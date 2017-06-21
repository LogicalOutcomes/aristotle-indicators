import sys
from celery.task import task
from celery.utils.log import get_task_logger
from django.core.files.storage import default_storage
from .importers.dhis2_indicators import IndicatorImporter as DHIS2Importer
from .importers.financial_indicators import IndicatorImporter as FinancialImporter
from .importers.utils import DBManager

logger = get_task_logger(__name__)


@task(
    time_limit=(60 * 60) * 3 + 5,     # 3h 5min
    soft_time_limit=(60 * 60) * 3,    # 3h
)
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


@task()
def clean_collection(collection):
    DBManager.clean_collection(collection)
    return {'status': 'OK', 'message': 'Collection "{}" elements removed'.format(collection)}


@task()
def clean_data_base():
    DBManager.clean_db()
    return {'status': 'OK', 'message': 'DB elements removed'}
