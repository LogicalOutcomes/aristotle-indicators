import logging
from django.core.cache import cache
from django.core.management import call_command

from aristotle_mdr import models
from aristotle_mdr.contrib.identifiers import models as MDR_ID
from aristotle_mdr.contrib.identifiers.models import ScopedIdentifier
from aristotle_mdr.contrib.slots.models import Slot
from comet import models as comet

from ..models import (
    Instrument, Goal, CategoryOption, CategoryCombination,
    Category
)

logger = logging.getLogger(__name__)


class BaseImporter(object):
    results = {
        'errors': [],
        'warnings': [],
        'info': {
            'indicators': [],
            'data_elements': [],
        },
    }

    def process_authorities(self):
        self.authority, created = models.RegistrationAuthority.objects.get_or_create(
            name=self.DEFAULT_AUTHORITY_NAME
        )
        self.authority_org = models.Organization.objects.get(
            pk=self.authority.pk
        )
        self.authority_namespace, c = MDR_ID.Namespace.objects.get_or_create(
            naming_authority=self.authority_org,
            shorthand_prefix=self.DEFAULT_AUTHORITY_PREFIX
        )

    # Importer Helpers
    def define_data_type(self, name):
        name = name.capitalize()
        dt, c = models.DataType.objects.get_or_create(name=name)
        if c:
            self.register(dt)
        return dt

    def register(self, thing):
        """
        Aristotle MDR regiter
        this will create or update the status of an element
        """
        models.Status.objects.update_or_create(
            concept=thing,
            registrationAuthority=self.authority,
            registrationDate=self.DEFAULT_REGISTRATION_DATE,
            defaults={
                'state': self.status
            }
        )

    def get_from_identifier(self, ident):
        obj = MDR_ID.ScopedIdentifier.objects.filter(
            namespace=self.authority_namespace,
            identifier=ident
        ).first()
        if obj is None:
            return None
        else:
            return obj.concept.item

    def make_identifier(self, ident, item):
        if not ident:
            return None
        obj, c = MDR_ID.ScopedIdentifier.objects.get_or_create(
            namespace=self.authority_namespace,
            identifier=ident,
            defaults={
                'concept': item
            }
        )
        return obj

    def text_to_slots(self, item, col, slot_name, slot_type='', clean=False):
        if not col:
            return
        if type(col) is not str:
            col = unicode(col)

        for val in col.split(';'):
            val = val.strip()
            if clean:
                val = lb_2_p(val, sep="\n")
            if val:
                obj, created = Slot.objects.get_or_create(
                    name=slot_name,
                    type=slot_type,
                    concept=item,
                    value=val
                )

    def get_elements(self, col):
        if not col:
            return []
        elements = []
        for code in [code.strip() for code in col.split(';')]:
            elem = self.get_from_identifier(code)
            if elem:
                elements.append(elem)
        return elements

    def log_row(self, method, row):
        cells = [c for c in row if hasattr(c, 'row')]
        if row and cells:
            cell = cells[0]
            self.results['process'] = u'Procesing Method: {}. Row: {} - {}'.format(
                method, cell.row, [c.value if c else '' for c in row]
            )
            logger.info(self.results['process'])

    def log_error(self, msg):
        self.results['errors'].append(msg)

    def clear_cache(self):
        cache.clear()
        logger.info('Cache cleared')

    def rebuild_index(self):
        logger.info('Rebuilding index')
        # TODO: only use 'update_index --remove'
        call_command('rebuild_index', '--noinput')
        logger.info('Finish building index')



def has_required_cols(row, *args):
    if not row or len(row) < len(args):
        return False
    return all([get_vcol(row, col) for col in args])


def get_col(row, col):
    for cell in row:
        if cell.value is not None:
            if cell.coordinate.startswith(col):
                return cell


def get_vcol(row, col, default=None):
    cell = get_col(row, col)
    if cell:
        return cell.value
    return default


def lb_2_p(txt, sep="\n\n"):
    if sep in txt:
        return "<p>" + "</p><p>".join([lb for lb in txt.split(sep) if lb != ""]) + "</p>"
    else:
        return txt


class DBManager(object):

    @classmethod
    def clean_db(cls):
        # local models
        Instrument.objects.all().delete()
        Goal.objects.all().delete()
        CategoryOption.objects.all().delete()
        Category.objects.all().delete()
        CategoryCombination.objects.all().delete()
        # Indicators
        models.PermissibleValue.objects.all().delete()
        ScopedIdentifier.objects.all().delete()
        models.ValueDomain.objects.all().delete()
        Slot.objects.all().delete()
        models.DataElement.objects.all().delete()
        comet.Indicator.objects.all().delete()

    @classmethod
    def clean_collection(cls, collection):
        CategoryOption.objects.filter(collection=collection).delete()
        Category.objects.filter(collection=collection).delete()
        CategoryCombination.objects.filter(collection=collection).delete()

        cls.clean_model_collection(models.ValueDomain, collection)
        cls.clean_model_collection(models.DataElement, collection)
        cls.clean_model_collection(comet.Indicator, collection)
        Slot.objects.filter(name='Collection',
                            value=collection).delete()

    @classmethod
    def clean_model_collection(cls, model, collection):
        elements = model.objects.filter(slots__name='Collection',
                                        slots__value=collection)
        for element in elements:
            # only remove elements with no other collections
            if not element.slots.filter(name='Collection').exclude(value=collection):
                element.delete()
