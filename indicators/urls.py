from django.conf.urls import url
from django.views.generic import TemplateView

from .views import (BrowseIndicatorsAsHome, CleanCollectionCompleteView,
                    CleanCollectionView, CleanDBCompleteView, CleanDBView,
                    CreateDataElementConcept, DHIS2ExportCompleteView,
                    DHIS2ExportView, ExportDataElements, ExportValueDomains,
                    ImportCompleteView, ImportDashboardView, ImportView,
                    comparer)

urlpatterns = [
    url(r'^/?$', BrowseIndicatorsAsHome.as_view(), name='lo_home'),

    url(r'^export/?$', TemplateView.as_view(template_name='indicators/static/export.html'), name="exporter"),
    url(r'^comparer/?$', comparer, name='comparer'),

    url(r'^item/(?P<iid>\d+)?/new-quick/data-element-concept/$', CreateDataElementConcept.as_view(), name='indicators_create_data_element_concept'),
    url(r'^import-export/dashboard/$', ImportDashboardView.as_view(), name='indicators_import_dashboard'),
    url(r'^import-export/clean-db/$', CleanDBView.as_view(), name='indicators_clean_db_form'),
    url(r'^import-export/clean-db/complete/$', CleanDBCompleteView.as_view(), name='indicators_clean_db_complete'),
    url(r'^import-export/clean-collection/$', CleanCollectionView.as_view(), name='indicators_clean_collection_form'),
    url(r'^import-export/clean-collection/complete/$', CleanCollectionCompleteView.as_view(), name='indicators_clean_collection_complete'),
    url(r'^import-export/indicators/$', ImportView.as_view(), name='indicators_import_form'),
    url(r'^import-export/indicators/complete/$', ImportCompleteView.as_view(), name='indicators_import_complete'),
    url(r'^import-export/export/data-elements/$', ExportDataElements.as_view(), name='indicators_export_data_elements'),
    url(r'^import-export/export/value-domains/$', ExportValueDomains.as_view(), name='indicators_export_value_domains'),


    url(r'^dhis2/export/indicator/(?P<pk>\d+)/$', DHIS2ExportView.as_view(), name='indicators_dhis2_export_form'),
    url(r'^dhis2/export/complete/$', DHIS2ExportCompleteView.as_view(), name='indicators_dhis2_export_complete'),
]
