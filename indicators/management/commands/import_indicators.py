from __future__ import unicode_literals
import datetime
import argparse
from django.core.management.base import BaseCommand
from indicators.importer import IndicatorImporter


class Command(BaseCommand):
    args = 'spreadsheet.xlsx'
    help = 'Import indicators from `file`.xlsx'
    REGISTRATION_DATE = datetime.date(2009, 4, 28)

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('data_file', type=argparse.FileType('rb'))

    def handle(self, *args, **options):
        self.stdout.write('Importing data...')
        IndicatorImporter(options.get('data_file')).process()
        self.stdout.write('Import complete')
