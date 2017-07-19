import logging
import requests
from django.utils.text import slugify
from ..models import CategoryCombination

logger = logging.getLogger(__name__)


class DHIS2ClientException(Exception):
    pass


class DHIS2Client(object):
    params = {
        'strategy': 'CREATE_AND_UPDATE',
        'mergeMode': 'REPLACE',
        'paging': 'false',
    }

    def __init__(self, server_url, user, password, version=25):
        self.server_url = server_url.rstrip('/')
        self.version = version
        self.user = user
        self.password = password
        self.api_url = '{}/api/{}/'.format(self.server_url, self.version)

    # Basic calls
    def _get(self, url, params=None):
        params = self.params.update(params) if params else self.params
        return requests.get(
            url, params=params,
            auth=(self.user, self.password),
        )

    def _post(self, url, json=None, params=None):
        params = self.params.update(params) if params else self.params
        return requests.post(
            url, json=json, params=params,
            auth=(self.user, self.password),
        )

    # Schemas
    def get(self, endpoint, obj_id=None, params=None):
        url = self.api_url + endpoint
        if obj_id:
            url += '/{}'.format(obj_id)
        response = self._get(url, params=params)
        return response.json()

    def post(self, endpoint, data, obj_id=None):
        url = self.api_url + endpoint
        if obj_id:
            url += '/{}'.format(obj_id)
        response = self._post(url, json=data, params=self.params)
        return response.json()

    def get_element(self, collection_name, name, lookup_field='displayName'):
        cat_options = self.get(collection_name, params={'query': name})
        for opt in cat_options[collection_name]:
            if name.lower() == opt[lookup_field].lower():
                return self.get(collection_name, obj_id=opt['id'])
        return None

    def create_element(self, collection_name, data):
        res = self.post(collection_name, data)
        # raise if any error was found
        if res['status'] in ['WARNING', 'ERROR']:
            raise DHIS2ClientException('Error: {}'.format(res))
        return res

    def get_or_create_element(self, collection_name, data, lookup_field='name'):
        created = False
        element = self.get_element(collection_name, data[lookup_field])
        if not element:
            self.create_element(collection_name, data)
            element = self.get_element(collection_name, data[lookup_field])
            created = True
        return element, created

    # Collections
    def add_to_collection(self, collection_object, col_object_id, collection_name, object_id):
        url = self.server_url + '/api/{}/{}/{}/{}'.format(
            collection_object, col_object_id, collection_name, object_id
        )
        return self._post(url)


class DHIS2Exporter(object):

    def __init__(self, url, username, password, api_version=25):
        self.dhis2 = DHIS2Client(url, username, password, version=api_version)

    def export_category_options(self, obj):
        opt, c = self.dhis2.get_or_create_element('categoryOptions', {
            'name': obj.name, 'shortName': obj.short_name, 'code': obj.code
        })
        return opt

    def export_category(self, obj):
        cat, c = self.dhis2.get_or_create_element('categories', {
            'name': obj.name, 'shortName': obj.short_name, 'code': obj.code,
            'dataDimensionType': 'DISAGGREGATION'
        })
        for option in obj.options.all():
            res_opt = self.export_category_options(option)
            self.dhis2.add_to_collection('categories', cat['id'], 'categoryOptions', res_opt['id'])
        return cat

    def export_category_combination(self, obj):
        comb, c = self.dhis2.get_or_create_element('categoryCombos', {
            'name': obj.name, 'shortName': obj.short_name, 'code': obj.code,
            'dataDimensionType': 'DISAGGREGATION'
        })
        for cat in obj.categories.all():
            res_cat = self.export_category(cat)
            self.dhis2.add_to_collection('categoryCombos', comb['id'], 'categories', res_cat['id'])
        return comb

    def export_option_set_value(self, obj):
        val, c = self.dhis2.get_or_create_element('options', {
            'name': obj.meaning, 'code': obj.value
        })
        return val

    def export_option_set(self, obj):
        opt, c = self.dhis2.get_or_create_element('optionSets', {
            'name': obj.name, 'code': self.get_code_from_identifier(obj),
            'valueType': "TEXT"
        })
        for val in obj.permissiblevalue_set.all():
            res_val = self.export_option_set_value(val)
            self.dhis2.add_to_collection('optionSets', opt['id'], 'options', res_val['id'])
        return opt

    def export_data_element(self, obj):
        logger.info(u'Export data element: {}'.format(obj))

        # Add category combination
        category_combo = None
        cat_combo_code = self.get_single_value_from_slot(obj, 'Category combination Code')
        if cat_combo_code:
            cat_combo_obj = CategoryCombination.objects.filter(code=cat_combo_code).first()
            if cat_combo_obj:
                category_combo = self.export_category_combination(cat_combo_obj)
        # Default None category combo
        if not category_combo:
            category_combo = self.dhis2.get_element('categoryCombos', 'default')

        # Add option set
        option_set = None
        if obj.valueDomain:
            option_set = self.export_option_set(obj.valueDomain)

        # Add Data Element
        dt, c = self.dhis2.get_or_create_element('dataElements', {
            'name': obj.name, 'shortName': obj.short_name,
            'code': self.get_code_from_identifier(obj),
            'description': obj.definition,
            'formName': self.get_single_value_from_slot(obj, 'Form name', default=obj.name),
            'domainType': self.get_single_value_from_slot(obj, 'Domain type'),
            'valueType': self.get_single_value_from_slot(obj, 'Value type'),
            'aggregationType': self.get_single_value_from_slot(obj, 'Aggregation operator'),
            'categoryCombo': self.get_simple_repr(category_combo),
            'optionSet': self.get_simple_repr(option_set, keys=['displayName', 'name', 'id', 'valueType']),
        })
        return dt

    def export_indicator(self, obj):
        # Generate numerators
        numerator = obj.numerator_computation
        numerators = {}
        for num in obj.numerators.all():
            res_num = self.export_data_element(num)
            code = self.get_code_from_identifier(num)
            numerators[code] = res_num
            numerator = numerator.replace(code, '#{{{}}}'.format(res_num['id']))

        # Generate denominators
        denominator = obj.denominator_computation
        denominators = {}
        for den in obj.denominators.all():
            res_den = self.export_data_element(den)
            code = self.get_code_from_identifier(den)
            denominators[code] = res_den
            denominator = denominator.replace(code, '#{{{}}}'.format(res_den['id']))

        # Indicator Type
        if obj.indicatorType:
            ind_type, c = self.dhis2.get_or_create_element('indicatorTypes', {
                'name': obj.indicatorType.short_name,
                'factor': self.get_single_value_from_slot(obj.indicatorType, 'Factor')
            })
        else:
            # if not type use Number as default
            ind_type = self.dhis2.get_element('indicatorTypes', 'Number')

        # Generate Indicator
        ind, c = self.dhis2.get_or_create_element('indicators', {
            'name': obj.name, 'shortName': obj.short_name,
            'code': self.get_code_from_identifier(obj),
            'description': obj.definition,
            'indicatorType': self.get_simple_repr(ind_type),
            'numeratorDescription': obj.numerator_description,
            'denominatorDescription': obj.denominator_description,
            'numerator': numerator,
            'denominator': denominator,
        })
        return ind

    # Helpers
    def get_code_from_identifier(self, obj):
        ident = obj.identifiers.first()
        if ident:
            return ident.identifier
        else:
            return slugify(obj.name)

    def get_single_value_from_slot(self, obj, slot_name, default=''):
        slot = obj.slots.filter(name=slot_name).first()
        return slot.value if slot else default

    def get_simple_repr(self, data, keys=['displayName', 'name', 'id']):
        if not data:
            return None
        return {k: v for k, v in data.items() if k in keys}
