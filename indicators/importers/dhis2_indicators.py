from __future__ import unicode_literals
from aristotle_mdr import models
from aristotle_mdr.contrib.slots.models import Slot
from datetime import date
from openpyxl import load_workbook
from .utils import BaseImporter, get_col, get_vcol, has_required_cols
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
        self.process_options_sets()
        self.process_data_elements()

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

    def process_options_sets(self):
        sheet = self.wb.get_sheet_by_name(self.SHEET_OPTIONS_SETS)

        # Value domain as Text
        data_type = self.define_data_type('Text')

        value_domains = {}
        for i, row in enumerate(sheet.iter_rows(row_offset=1)):
            name = get_col(row, 'A').value
            code = get_col(row, 'C').value
            option_name = get_col(row, 'D').value
            option_code = get_col(row, 'F').value

            if name is None:
                continue

            if name not in value_domains:
                val_dom, created = models.ValueDomain.objects.update_or_create(
                    name=name,
                    defaults={
                        'definition': self.DEFAULT_DEFINITION,
                        'data_type': data_type,
                    }
                )
                self.register(val_dom)
                self.make_identifier(code, val_dom)
                val_dom.permissiblevalue_set.all().delete()
                value_domains[name] = {'val_dom': val_dom, 'options': []}

            pv = models.PermissibleValue.objects.create(
                valueDomain=value_domains[name]['val_dom'],
                value=option_code,
                meaning=option_name,
                order=len(value_domains[name]['options']) + 1
            )
            value_domains[name]['options'].append(pv)

    def process_data_elements(self):
        sheet = self.wb.get_sheet_by_name(self.SHEET_DATA_ELEMENTS)

        for row in sheet.iter_rows(row_offset=1):
            if not has_required_cols(row, 'A', 'C'):
                continue

            name = get_vcol(row, 'A')
            code = get_vcol(row, 'C')
            short_name = get_vcol(row, 'D')
            description = get_vcol(row, 'F')
            form_name = get_vcol(row, 'G')
            domain_type = get_vcol(row, 'H')
            value_type = get_vcol(row, 'I')
            aggregation_operator = get_vcol(row, 'J')
            category_combination = get_vcol(row, 'K')
            url = get_vcol(row, 'L')
            zero_is_significant = get_vcol(row, 'M')
            option_set = get_vcol(row, 'N')
            comment_option_set = get_vcol(row, 'O')

            de, c = models.DataElement.objects.update_or_create(
                name=name,
                defaults={
                    'short_name': short_name,
                    'definition': description or name,
                }
            )
            if c:
                self.register(de)
                self.make_identifier(code, de)
                Slot.objects.filter(concept=de).delete()

            # Add custom properties
            self.text_to_slots(de, form_name, 'Form name')
            self.text_to_slots(de, domain_type, 'Domain type')
            self.text_to_slots(de, value_type, 'Value type')
            self.text_to_slots(de, aggregation_operator, 'Aggregation operator')
            self.text_to_slots(de, category_combination, 'Category combination Code')
            self.text_to_slots(de, zero_is_significant, 'Zero is significant')
            self.text_to_slots(de, comment_option_set, 'Comment option set')
            self.text_to_slots(de, url, 'URL')

            # Add value domain
            if option_set:
                vd = self.get_from_identifier(option_set)
                if vd:
                    de.valueDomain = vd
                    de.save()
            # get value domain from data type
            # else:
