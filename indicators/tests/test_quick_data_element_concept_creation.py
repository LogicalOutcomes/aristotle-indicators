from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from aristotle_mdr.models import DataElement, DataElementConcept, ObjectClass, Property


class QuickDataElementConceptCreationTestCase(TestCase):

    def setUp(self):
        # GIVEN a logged in superuser
        self.user = User.objects.create_superuser(
            'jacob', 'jacob@example.com', 'top_secret'
        )
        self.client.login(username='jacob', password='top_secret')
        # AND a data element
        self.de = DataElement.objects.create(
            name='Data Element Example',
            definition='Definition example'
        )

    def test_quick_data_element_concept_creation_access(self):
        # WHEN the view is called
        response = self.client.get(
            reverse('indicators_create_data_element_concept', args=[self.de.pk])
        )

        # THEN the view is displayed
        self.assertEqual(response.status_code, 200)

    def test_quick_data_element_concept_creation_view(self):
        # WHEN the form is filled
        data = {
            'data_element_concept_name': 'dec name',
            'data_element_concept_definition': 'dec definition',
            'object_class_name': 'obj class name',
            'object_class_definition': 'obj class definition',
            'property_name': 'prop name',
            'property_definition': 'prop definition',
        }
        self.client.post(
            reverse('indicators_create_data_element_concept', args=[self.de.pk]),
            data
        )

        # THEN the concept are created
        dec = DataElementConcept.objects.get()
        self.assertEqual(dec.name, data['data_element_concept_name'])
        self.assertEqual(dec.definition, data['data_element_concept_definition'])
        obj_class = ObjectClass.objects.get()
        self.assertEqual(obj_class.name, data['object_class_name'])
        self.assertEqual(obj_class.definition, data['object_class_definition'])
        prop = Property.objects.get()
        self.assertEqual(prop.name, data['property_name'])
        self.assertEqual(prop.definition, data['property_definition'])
