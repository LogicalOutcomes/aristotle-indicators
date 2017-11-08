from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase


class ExportDataElementsTestCase(TestCase):

    def test_export_view(self):
        # GIVEN a logged in superuser
        self.user = User.objects.create_superuser(
            'jacob', 'jacob@example.com', 'top_secret'
        )
        self.client.login(username='jacob', password='top_secret')

        # WHEN the export view is called
        response = self.client.get(
            reverse('indicators_export_data_elements')
        )

        # THEN the view returns a streaming content
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.streaming_content)
