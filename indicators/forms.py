from aristotle_mdr.contrib.autocomplete import widgets
from aristotle_mdr.forms.bulk_actions import BulkActionForm, DownloadActionForm
from aristotle_mdr.models import (STATES, DataElementConcept, ObjectClass,
                                  Property)
from ckeditor.widgets import CKEditorWidget
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


class QuickCreateDataElementConcept(forms.Form):

    data_element_concept_name = forms.CharField(
        required=False, help_text=_('Search and select an existing Data Element Concept')
    )
    data_element_concept_definition = forms.CharField(required=False, widget=CKEditorWidget())

    object_class_name = forms.CharField(
        required=False, help_text=_('Search and select an existing Object Class')
    )
    object_class_definition = forms.CharField(required=False, widget=CKEditorWidget())

    property_name = forms.CharField(
        required=False, help_text=_('Search and select an existing Property')
    )
    property_definition = forms.CharField(required=False, widget=CKEditorWidget())
    copy_data_element_state = forms.BooleanField(
        initial=True, required=False,
        help_text=_('Appy the same state of the Data Element to concepts to be created')
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        self.data_element_concepts = DataElementConcept.objects.visible(self.user)
        self.objects_class = ObjectClass.objects.visible(self.user)
        self.properties = Property.objects.visible(self.user)

        super(QuickCreateDataElementConcept, self).__init__(*args, **kwargs)
        self.fields['data_element_concept'] = forms.ModelChoiceField(
            queryset=self.data_element_concepts,
            empty_label="None",
            label=_("Data Element Concept"),
            required=False,
            widget=widgets.ConceptAutocompleteSelect(model=DataElementConcept)
        )
        self.fields['object_class'] = forms.ModelChoiceField(
            queryset=self.objects_class,
            empty_label="None",
            label=_("Object Class"),
            required=False,
            widget=widgets.ConceptAutocompleteSelect(model=ObjectClass)
        )
        self.fields['property'] = forms.ModelChoiceField(
            queryset=self.properties,
            empty_label="None",
            label=_("Property"),
            required=False,
            widget=widgets.ConceptAutocompleteSelect(model=Property)
        )

    def clean(self):
        cleaned_data = super(QuickCreateDataElementConcept, self).clean()

        data_element_concept = cleaned_data.get('data_element_concept')
        data_element_concept_name = cleaned_data.get('data_element_concept_name')
        data_element_concept_definition = cleaned_data.get('data_element_concept_definition')

        object_class = cleaned_data.get('object_class')
        object_class_name = cleaned_data.get('object_class_name')
        object_class_definition = cleaned_data.get('object_class_definition')

        property = cleaned_data.get('property')
        property_name = cleaned_data.get('property_name')
        property_definition = cleaned_data.get('property_definition')

        if data_element_concept and (data_element_concept_name or data_element_concept_definition or
                                     object_class or object_class_name or object_class_definition or
                                     property or property_name or property_definition):
            # CASE: existing Data Element Concept
            raise forms.ValidationError(
                "If you select a Data Element Concept all other fields should be blank. "
                "Please expand the forms and remove the content of Object Class and Property fields"
            )
        elif not data_element_concept:
            # CASE: new Data Element Concept
            if not data_element_concept_name:
                self.add_error('data_element_concept_name', 'This field is required')
            if not data_element_concept_definition:
                self.add_error('data_element_concept_definition', 'This field is required')

            if object_class and (object_class_name or object_class_definition):
                # CASE: existing Object Class
                raise forms.ValidationError(
                    "If you select an Object Class all fields should be blank. "
                    "Please expand the Object Class forms and remove the content on the fields"
                )
            elif not object_class:
                # CASE: new Object Class
                if not object_class_name:
                    self.add_error('object_class_name', 'This field is required')
                if not object_class_definition:
                    self.add_error('object_class_definition', 'This field is required')

            if property and (property_name or property_definition):
                # CASE: existing Object Class
                raise forms.ValidationError(
                    "If you select a Property all other fields should be blank. "
                    "Please expand the Property forms and remove the content on the fields"
                )
            elif not property:
                # CASE: new Object Class
                if not property_name:
                    self.add_error('property_name', 'This field is required')
                if not property_definition:
                    self.add_error('property_definition', 'This field is required')


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
        ('DHIS2', 'DHIS2 type'),
        ('financial', 'Financial type'),
    )

    spreadsheet = forms.FileField(help_text='xlsx format is expected')
    spreadsheet_type = forms.ChoiceField(
        choices=IMPORT_OPTIONS,
        help_text='Select the spreadsheet type that you are about to import.'
    )
    collection = forms.CharField(
        required=True, max_length=64,
        help_text='Collection name will be assigned to the imported indicators'
    )
    clean_collection = forms.BooleanField(
        initial=False, required=False,
        help_text=_('First remove all elements of collection and then import')
    )
    status = forms.ChoiceField(
        choices=STATES, initial=STATES.recorded,
        help_text=_('Initial status for the metadata to be imported')
    )


class CleanDBForm(forms.Form):
    confirm = forms.BooleanField(
        initial=False, required=True,
        help_text=_('Check to confirm that you do want to remove all DB indicators and related data')
    )


class CleanCollectionForm(forms.Form):
    collection = forms.CharField(
        required=True, max_length=64,
        help_text='Collection name of elements to remove'
    )
