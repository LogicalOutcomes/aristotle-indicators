from celery.utils.log import get_task_logger
from django.core.files.storage import default_storage
from .importers.dhis2_indicators import IndicatorImporter as DHIS2Importer
from .importers.financial_indicators import IndicatorImporter as FinancialImporter

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

    try:
        importer = importer_class(
            spreadsheet,
            collection=collection
        )
        importer.process()
        # display results
        indicator_cnt = len(importer.results['info']['indicators'])
        return {'status': 'complete', 'indicators': indicator_cnt}
    except Exception as e:
        return {'status': 'Error: {}'.format(e)}
