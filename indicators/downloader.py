from django.http import HttpResponse
from django.shortcuts import redirect
from django.core.urlresolvers import reverse


item_register = {
    'dhis2': {'comet': ['indicator']},
}


def download(request, download_type, item):
    return redirect(reverse('dhis2_export_form', args=[item.pk]))


def bulk_download(request, download_type, items, title=None, subtitle=None):
    res = "Not implemented yet: "
    for item in items:
        res += ', {}'.format(item)
    return HttpResponse(res, content_type="text/plain")
