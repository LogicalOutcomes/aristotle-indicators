from os.path import join as path_join, dirname
from django.test import TestCase
from comet import models as comet
from ..importers.dhis2_indicators import IndicatorImporter


class ImporterTestCase(TestCase):

    def setUp(self):
        # GIVEN a spreadsheet and an importer instance
        self.spreadsheet = open(path_join(dirname(__file__), 'data/dhis2-indicators.xlsx'), 'r')
        self.importer = IndicatorImporter(self.spreadsheet)

    def test_process(self):
        # WHEN process indicators is called
        self.importer.process()

        # THEN we have indicators imported
        self.assertGreater(comet.Indicator.objects.count(), 1)
