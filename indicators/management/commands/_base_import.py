from __future__ import unicode_literals
import datetime
import argparse
from django.core.management.base import BaseCommand


class BaseImportCommand(BaseCommand):
    args = 'spreadsheet.xlsx'
    help = 'Import indicators from `file`.xlsx'
    REGISTRATION_DATE = datetime.date(2009, 4, 28)

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('data_file', type=argparse.FileType('rb'))
        parser.add_argument('-c', '--collection', dest="collection", help="Set collection name for indicators")

    def handle(self, *args, **options):
        self.stdout.write('Importing data...')
        importer_class = self.get_importer_class()
        importer = importer_class(options.get('data_file'), collection=options.get('collection'))
        importer.process()
        self.stdout.write('Import complete')
        self.stdout.write('Results:')
        self.stdout.write('''
            Indicators = {}
        '''.format(
            len(importer.results['info']['indicators']),
        ))

    def get_importer_class(self):
        importer_class = getattr(self, 'importer_class', None)
        if not importer_class:
            raise NotImplementedError('You need to specify an importer_class')
        return importer_class
