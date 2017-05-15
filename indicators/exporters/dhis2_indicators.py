import requests
from aristotle_mdr.models import ValueDomain
from django.utils.text import slugify
from ..models import Category, CategoryOption, CategoryCombination


class DHIS2Client(object):
    params = {
        'strategy': 'CREATE_AND_UPDATE',
        'mergeMode': 'REPLACE',
        'paging': 'false',
    }

    endpoints = {
        'categoryOptions': '/api/categoryOptions',
        'categories': '/api/categories',
        'categoryCombos': '/api/categoryCombos',
        'optionSets': '/api/optionSets',
        'options': '/api/options',
    }

    def __init__(self, server_url, user, password):
        self.server_url = server_url.rstrip('/')
        self.user = user
        self.password = password

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
        url = self.server_url + self.endpoints[endpoint]
        if obj_id:
            url += '/{}'.format(obj_id)
        response = self._get(url, params=params)
        return response.json()

    def post(self, endpoint, data, obj_id=None):
        url = self.server_url + self.endpoints[endpoint]
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
        return self.post(collection_name, data)

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

    def __init__(self):
        self.dhis2 = DHIS2Client(
            'http://dev.ocasi.sis.ngo',
            'rafael@logicaloutcomes.net', '0s6dH9ZM'
        )

    def export(self):
        val_dom = ValueDomain.objects.get(pk=2)
        self.export_option_set(val_dom)
        # comb = CategoryCombination.objects.get(id=2)
        # self.export_category_combination(comb)

    def export_category_options(self, obj):
        opt, c = self.dhis2.get_or_create_element('categoryOptions', {
            'name': obj.name, 'shortName': obj.short_name, 'code': obj.code
        })
        return opt['id']

    def export_category(self, obj):
        cat, c = self.dhis2.get_or_create_element('categories', {
            'name': obj.name, 'shortName': obj.short_name, 'code': obj.code,
            'dataDimensionType': 'DISAGGREGATION'
        })
        for option in obj.options.all():
            opt_id = self.export_category_options(option)
            self.dhis2.add_to_collection('categories', cat['id'], 'categoryOptions', opt_id)
        return cat['id']

    def export_category_combination(self, obj):
        comb, c = self.dhis2.get_or_create_element('categoryCombos', {
            'name': obj.name, 'shortName': obj.short_name, 'code': obj.code,
            'dataDimensionType': 'DISAGGREGATION'
        })
        for cat in obj.categories.all():
            cat_id = self.export_category(cat)
            self.dhis2.add_to_collection('categoryCombos', comb['id'], 'categories', cat_id)
        return comb['id']

    def export_option_set_value(self, obj):
        val, c = self.dhis2.get_or_create_element('options', {
            'name': obj.meaning, 'code': obj.value
        })
        return val['id']

    def export_option_set(self, obj):
        opt, c = self.dhis2.get_or_create_element('optionSets', {
            'name': obj.name, 'code': self.get_code_from_identifier(obj),
            'valueType': "TEXT"
        })
        for val in obj.permissiblevalue_set.all():
            val_id = self.export_option_set_value(val)
            self.dhis2.add_to_collection('optionSets', opt['id'], 'options', val_id)
        return opt['id']

    def get_code_from_identifier(self, obj):
        ident = obj.identifiers.first()
        if ident:
            return ident.identifier
        else:
            return slugify(obj.name)

exporter = DHIS2Exporter()
