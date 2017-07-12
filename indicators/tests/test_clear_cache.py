from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase
from django.utils.six import StringIO


class ClearCacheCommandTestCase(TestCase):

    def test_clear_cache(self):
        # GIVEN a value on the cache
        cache.set('key', 'value')

        # WHEN clear cache command is called
        call_command('clear_cache', stdout=StringIO())

        # THEN the value is not on the cache
        self.assertFalse(cache.get('key', False))
