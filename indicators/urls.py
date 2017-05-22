from django.conf.urls import url
from django.views.generic import TemplateView
from .views import BrowseIndicatorsAsHome, comparer, DHIS2ExportView, DHIS2ExportCompleteView

urlpatterns = [
    url(r'^/?$', BrowseIndicatorsAsHome.as_view(), name='lo_home'),

    url(r'^export/?$', TemplateView.as_view(template_name='indicators/static/export.html'), name="exporter"),
    url(r'^comparer/?$', comparer, name='comparer'),

    url(r'^dhis2/export/indicator/(?P<pk>\d+)/$', DHIS2ExportView.as_view(), name='dhis2_export_form'),
    url(r'^dhis2/export/complete/$', DHIS2ExportCompleteView.as_view(), name='dhis2_export_complete'),
]
