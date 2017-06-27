from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from comet.models import Indicator
from mock import patch, MagicMock


class ExportToDHIS2TestCase(TestCase):

    @patch('indicators.exporters.dhis2_indicators.DHIS2Client._post', MagicMock())
    @patch('indicators.exporters.dhis2_indicators.DHIS2Client._get')
    def test_export_view(self, mocked_get):
        # TODO: improve this test with a complete Indicator with Data elements, and more

        # GIVEN a logged in superuser
        self.user = User.objects.create_superuser(
            'jacob', 'jacob@example.com', 'top_secret'
        )
        self.client.login(username='jacob', password='top_secret')
        # and some data on the DB (one Indicator)
        ind = Indicator.objects.create(short_name='example', name='example', definition='example')

        # WHEN export to DHIS2 is called
        response = self.client.post(
            reverse('indicators_dhis2_export_form', args=[ind.pk]),
            {
                'collection': 'LO',
                'username': 'jacob',
                'password': 'top_secret',
                'server_url': 'http://example.com/api/',
                'api_version': 25,
            }
        )

        # THEN the user is redirect to the confirm view
        self.assertTrue(response.status_code, 302)
        # AND the exporter was used
        mocked_get.assert_called()
