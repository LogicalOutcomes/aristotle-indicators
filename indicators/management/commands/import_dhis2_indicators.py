from __future__ import unicode_literals
from indicators.importers.dhis2_indicators import IndicatorImporter
from ._base_import import BaseImportCommand


class Command(BaseImportCommand):
    importer_class = IndicatorImporter
