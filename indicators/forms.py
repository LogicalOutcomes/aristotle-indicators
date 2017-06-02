from aristotle_mdr.contrib.autocomplete import widgets
from aristotle_mdr.forms.bulk_actions import BulkActionForm, DownloadActionForm
from django import forms
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _


class CompareIndicatorsForm(forms.Form):

    def __init__(self, *args, **kwargs):
        from comet.models import Indicator
        self.user = kwargs.pop('user')
        self.qs = Indicator.objects.visible(self.user)
        super(CompareIndicatorsForm, self).__init__(*args, **kwargs)

        self.fields['indicator_1'] = forms.ModelChoiceField(
            queryset=self.qs,
            empty_label="None",
            label=_("First item"),
            required=True,
            widget=widgets.ConceptAutocompleteSelect(model=Indicator)
        )

        self.fields['indicator_2'] = forms.ModelChoiceField(
            queryset=self.qs,
            empty_label="None",
            label=_("Second item"),
            required=True,
            widget=widgets.ConceptAutocompleteSelect(model=Indicator)
        )

        self.fields['indicator_3'] = forms.ModelChoiceField(
            queryset=self.qs,
            empty_label="None",
            label=_("Third item"),
            required=True,
            widget=widgets.ConceptAutocompleteSelect(model=Indicator)
        )


class CompareRedirectBulkActionForm(BulkActionForm):
    classes = "fa-exchange"
    action_text = _('Compare')
    items_label = "Items that will be removed from your favourites list"

    def make_changes(self):
        items = self.items_to_change
        from aristotle_mdr.contrib.redirect.exceptions import Redirect
        raise Redirect(
            url=reverse('comparer') + "?" + "&".join(['items=%s' % i.id for i in items])
        )


class QuickPDFExportDownloadForm(DownloadActionForm):
    classes = "fa-file-pdf-o"
    action_text = _('Export')
    items_label = "Items to export"
    download_type = 'pdf'
    title = "Exported Indicators"


class DHIS2ExportForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput())
    server_url = forms.URLField(help_text=_('DHIS2 base url'))
    api_version = forms.IntegerField(initial=25)


class ImportForm(forms.Form):
    IMPORT_OPTIONS = (
        ('financial', 'Financial type'),
        ('DHIS2', 'DHIS2 type'),
    )

    spreadsheet = forms.FileField(help_text='xlsx format is expected')
    spreadsheet_type = forms.ChoiceField(
        choices=IMPORT_OPTIONS,
        help_text='Select the spreadsheet type that you are about to import.'
    )
    collection = forms.CharField(
        required=False, max_length=64,
        help_text='Collection name will be assigned to the imported indicators'
    )


class CleanDBForm(forms.Form):
    confirm = forms.BooleanField(
        initial=False, required=True,
        help_text=_('Check to confirm that you do want to remove all DB indicators and related data')
    )
