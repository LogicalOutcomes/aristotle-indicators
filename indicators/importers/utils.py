from aristotle_mdr import models
from aristotle_mdr.contrib.identifiers import models as MDR_ID
from aristotle_mdr.contrib.slots.models import Slot


class BaseImporter(object):

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
        """Aristotle MDR regiter
        """
        models.Status.objects.get_or_create(
            concept=thing,
            registrationAuthority=self.authority,
            registrationDate=self.DEFAULT_REGISTRATION_DATE,
            state=models.STATES.recorded
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
        obj, c = MDR_ID.ScopedIdentifier.objects.get_or_create(
            namespace=self.authority_namespace,
            identifier=ident,
            concept=item
        )
        return obj

    def text_to_slots(self, item, col, slot_name, slot_type='', clean=False):
        if not col:
            return
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


def has_required_cols(row, *args):
    if not row or len(row) < len(args):
        return False
    coords = [c.coordinate for c in row if c.value]
    required = []
    for col in args:
        required += [col for c in coords if c.startswith(col)]
    return len(required) == len(args)


def get_col(row, col):
    for cell in row:
        if cell.value is not None:
            if cell.coordinate.startswith(col):
                return cell


def get_vcol(row, col):
    cell = get_col(row, col)
    if cell:
        return cell.value
    return None


def lb_2_p(txt, sep="\n\n"):
    if sep in txt:
        return "<p>" + "</p><p>".join([lb for lb in txt.split(sep) if lb != ""]) + "</p>"
    else:
        return txt
