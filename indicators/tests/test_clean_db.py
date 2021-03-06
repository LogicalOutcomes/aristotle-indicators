from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from comet.models import Indicator


class CleanDBTestCase(TestCase):

    def test_clean_data_base_view(self):
        # GIVEN a logged in superuser
        self.user = User.objects.create_superuser(
            'jacob', 'jacob@example.com', 'top_secret'
        )
        self.client.login(username='jacob', password='top_secret')
        # and some data on the DB (one Indicator)
        Indicator.objects.create(short_name='example', name='example', definition='example')

        # WHEN clean_data_base is called
        response = self.client.post(
            reverse('indicators_clean_db_form'),
            {'confirm': True}
        )

        # THEN the user is redirect to the confirm view
        self.assertTrue(response.status_code, 302)
        # AND no indicators are on the DB
        self.assertEqual(Indicator.objects.count(), 0)
