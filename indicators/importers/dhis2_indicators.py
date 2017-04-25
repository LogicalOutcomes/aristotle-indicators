from __future__ import unicode_literals
from aristotle_mdr import models
from aristotle_mdr.contrib.identifiers import models as MDR_ID
from datetime import date
from openpyxl import load_workbook
from .utils import BaseImporter


class IndicatorImporter(BaseImporter):
    """Import indicators from spreadsheet
    """
    DEFAULT_AUTHORITY_NAME = 'Logical Outcomes'
    DEFAULT_AUTHORITY_PREFIX = 'lo'
    DEFAULT_REGISTRATION_DATE = date.today()
    DEFAULT_DEFINITION = 'Imported from the Indicator Reference Sheet'
    # data file sheets
    SHEET_INDICATORS = 'Indicators'
    SHEET_DATA_ELEMENTS = 'Data Elements'
    SHEET_CATEGORY_OPTIONS = 'CategoryOptions'
    SHEET_CATEGORIES = 'Categories'
    SHEET_CATEGORY_COMBOS = 'CategoryCombos'
    SHEET_OPTIONS_SETS = 'OptionSets'

    def __init__(self, data_file):
        self.wb = load_workbook(data_file, read_only=True)

    def process(self):
        self.process_authorities()
        self.process_categories()

    def process_categories(self):
        sheet = self.wb.get_sheet_by_name(self.SHEET_CATEGORIES)
        dt = self.define_data_type('Number')
        value_domains = {}

        for i, row in enumerate(sheet.iter_rows(row_offset=1)):
            option_name = row[0].value
            category_name = row[1].value
            option_code = row[2].value

            val_dom, created = models.ValueDomain.objects.get_or_create(
                name=category_name,
                defaults={
                    # "workgroup": wg,
                    "definition": self.DEFAULT_DEFINITION,
                    "data_type": dt,
                }
            )
            if created:
                self.register(val_dom)

            if category_name not in value_domains:
                # clean all option when we process for the fist time a value domain
                val_dom.permissiblevalue_set.all().delete()
                value_domains[category_name] = [option_name]
            else:
                value_domains[category_name].append(option_name)

            models.PermissibleValue.objects.get_or_create(
                valueDomain=val_dom,
                value=len(value_domains[category_name]),
                meaning=option_name,
                order=len(value_domains[category_name])
            )
