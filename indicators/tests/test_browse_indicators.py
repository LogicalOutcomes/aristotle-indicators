from django.test import TestCase
from django.core.urlresolvers import reverse
from comet.models import Indicator


class BrowseIndicatorsTestCase(TestCase):

    def test_browse_indicators_view(self):
        # GIVEN an indicator on the DB
        Indicator.objects.create(short_name='example', name='example', definition='example')

        # WHEN browse indicator page is visited
        response = self.client.get(reverse('lo_home'))

        # THEN the user can access the page
        self.assertTrue(response.status_code, 200)
        # AND the indicator is displayed
        self.assertContains(response, 'example')
