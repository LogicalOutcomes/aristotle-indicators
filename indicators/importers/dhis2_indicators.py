from __future__ import unicode_literals
import datetime
from openpyxl import load_workbook


class IndicatorImporter(object):
    """Import indicators from spreadsheet
    """
    DEFAULT_AUTHORITY_NAME = 'Logical Outcomes'
    DEFAULT_AUTHORITY_PREFIX = 'lo'
    DEFAULT_REGISTRATION_DATE = datetime.date(2017, 2, 28)
    DEFAULT_DEFINITION = 'Imported from the Indicator Reference Sheet'
    # data file sheets
    SHEET_DOMAINS = 'Domains and Subdomains'
    SHEET_INSTRUMENTS = 'Instruments'
    SHEET_VALUE_DOMAIN = 'Value Domain'
    SHEET_INDICATORS = 'Indicators'
    SHEET_DATA_ELEMENTS = 'Data Elements'
    SHEET_DOMAINS_SUBDOMAINS = 'Domains and Subdomains'

    def __init__(self, data_file):
        self.wb = load_workbook(data_file, read_only=True)

    def process(self):
        # TODO: implement import
        pass
