import sys
from celery.utils.log import get_task_logger
from django.core.files.storage import default_storage
from .importers.dhis2_indicators import IndicatorImporter as DHIS2Importer
from .importers.financial_indicators import IndicatorImporter as FinancialImporter
from .importers.utils import DBManager

# TODO: import the app using settings
from logicaloutcomes.celery import app

logger = get_task_logger(__name__)


@app.task()
def import_indicators(spreadsheet_path, spreadsheet_type, collection):
    spreadsheet = default_storage.open(spreadsheet_path)

    if spreadsheet_type == 'DHIS2':
        importer_class = DHIS2Importer
    elif spreadsheet_type == 'financial':
        importer_class = FinancialImporter

    importer = importer_class(
        spreadsheet,
        collection=collection
    )
    try:
        importer.process()
    except Exception as e:
        msg = u'{} \n {}'.format(e.message, importer.results.get('process', ''))
        # TODO: add compatibility for Python 3
        raise type(e), type(e)(msg), sys.exc_info()[2]
    # display results
    indicator_cnt = len(importer.results['info']['indicators'])
    return {'status': 'complete', 'indicators': indicator_cnt}


@app.task()
def clean_data_base():
    DBManager.clean_db()
    return {'status': 'OK'}
