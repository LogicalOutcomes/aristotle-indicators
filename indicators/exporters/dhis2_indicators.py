import requests


class DHIS2Client(object):
    params = {
        'strategy': 'CREATE_AND_UPDATE',
        'mergeMode': 'REPLACE',
        'paging': 'false',
    }

    endpoints = {
        'categoryOptions': '/api/categoryOptions',
    }

    def __init__(self, server_url, user, password):
        self.server_url = server_url.rstrip('/')
        self.user = user
        self.password = password

    def get(self, endpoint, obj_id=None, params=None):
        url = self.server_url + self.endpoints[endpoint]
        if obj_id:
            url += '/{}'.format(obj_id)
        response = requests.get(
            url, params=params,
            auth=(self.user, self.password),
        )
        return response.json()

    def post(self, endpoint, data):
        response = requests.post(
            self.server_url + self.endpoints[endpoint],
            json=data, params=self.params,
            auth=(self.user, self.password)
        )
        return response.json()

    def get_element(self, element_type, name, lookup_field='displayName'):
        cat_options = self.get(element_type, params={'query': name})
        for opt in cat_options[element_type]:
            if name.lower() == opt[lookup_field].lower():
                return self.get(element_type, obj_id=opt['id'])
        return None

    def create_element(self, element_type, data):
        return self.post(element_type, data)

    def get_or_create_element(self, element_type, data, lookup_field='name'):
        created = False
        element = self.get_element(element_type, data[lookup_field])
        if not element:
            self.create_element(element_type, data)
            element = self.get_element(element_type, data[lookup_field])
            created = True
        return element, created


dhis2 = DHIS2Client(
    'http://dev.ocasi.sis.ngo',
    'rafael@logicaloutcomes.net', '0s6dH9ZM'
)
