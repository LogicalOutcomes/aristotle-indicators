from __future__ import unicode_literals
from aristotle_mdr import models
from aristotle_mdr.contrib.identifiers import models as MDR_ID
from datetime import date
from openpyxl import load_workbook
from .utils import BaseImporter, get_col
from ..models import CategoryOption, Category, CategoryCombination


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
        self.process_category_options()
        self.process_categories()
        self.process_category_combitation()

    def process_category_options(self):
        sheet = self.wb.get_sheet_by_name(self.SHEET_CATEGORY_OPTIONS)
        for row in sheet.iter_rows(row_offset=1):
            if row[0].value is None:
                continue

            option, c = CategoryOption.objects.get_or_create(
                code=get_col(row, 'C').value,
                name=get_col(row, 'A').value,
                short_name=get_col(row, 'D').value,
            )

    def process_categories(self):
        sheet = self.wb.get_sheet_by_name(self.SHEET_CATEGORIES)

        categories = []

        for row in sheet.iter_rows(row_offset=1):
            if row[0].value is None:
                continue

            category, c = Category.objects.get_or_create(
                code=get_col(row, 'C').value,
                name=get_col(row, 'A').value,
                short_name=get_col(row, 'D').value,
            )

            if category not in categories:
                # remove all options from categories the first time we import it
                categories.append(category)
                category.options.clear()

            option = CategoryOption.objects.get(code=get_col(row, 'E').value)
            category.options.add(option)

    def process_category_combitation(self):
        sheet = self.wb.get_sheet_by_name(self.SHEET_CATEGORY_COMBOS)

        category_combinations = []

        for row in sheet.iter_rows(row_offset=1):
            if row[0].value is None:
                continue

            category_combination, c = CategoryCombination.objects.get_or_create(
                code=get_col(row, 'C').value,
                name=get_col(row, 'A').value,
                short_name=get_col(row, 'D').value,
            )

            if category_combination not in category_combinations:
                # remove all categories from category_combination the first time we import it
                category_combinations.append(category_combination)
                category_combination.categories.clear()

            category = Category.objects.get(code=get_col(row, 'E').value)
            category_combination.categories.add(category)
