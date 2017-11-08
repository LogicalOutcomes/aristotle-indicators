import time

import reversion
import unicodecsv as csv
from aristotle_mdr.contrib.browse.views import BrowseConcepts
from aristotle_mdr.contrib.generic.views import GenericWithItemURLView
from aristotle_mdr.contrib.slots.models import Slot
from aristotle_mdr.models import (DataElement, DataElementConcept, ObjectClass,
                                  Property, Status, SupplementaryValue,
                                  ValueDomain)
from celery.result import AsyncResult
from comet import models as comet
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Count
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.utils.encoding import force_text
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView, View
from django.views.generic.edit import FormView
from django_celery_results.models import TaskResult
from indicators.templatetags.logicaltags import get_single_slot

from .forms import (CleanCollectionForm, CleanDBForm, CompareIndicatorsForm,
                    DHIS2ExportForm, ImportForm, QuickCreateDataElementConcept)
from .tasks import (clean_collection, clean_data_base, dhis2_export,
                    import_indicators)


class SuperUserRequiredMixin(object):
    """
    View mixin which requires that the authenticated user is a super user
    (i.e. `is_superuser` is True).
    """
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect(settings.LOGIN_URL)
        return super(SuperUserRequiredMixin, self).dispatch(
            request,
            *args, **kwargs)


class BrowseIndicatorsAsHome(BrowseConcepts):
    _model = comet.Indicator

    def get_slot_context(self, context, name, slug_name, param_name, concepts):
        context[slug_name] = Slot.objects.filter(
            name=name, concept__in=concepts
        ).values('value').annotate(count=Count('value')).order_by('-count')
        context[param_name] = self.request.GET.getlist(param_name)
        return context

    def get_status_context(self, context, concepts, slug_name='statuses', param_name='st'):
        context[slug_name] = Status.objects.filter(
            concept__in=concepts
        ).values('state').annotate(count=Count('state')).order_by('-count')

        # Force Preferred and Standard status first
        preferred = [c for c in context[slug_name] if c['state'] == 6]
        preferred = preferred[0] if preferred else {'state': 6, 'count': 0}
        standard = [c for c in context[slug_name] if c['state'] == 5]
        standard = standard[0] if standard else {'state': 5, 'count': 0}
        context[slug_name] = [preferred, standard] + [c for c in context[slug_name] if c['state'] not in [6, 5]]

        context[param_name] = self.request.GET.getlist(param_name)
        return context

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        self.kwargs['app'] = 'comet'
        context = super(BrowseIndicatorsAsHome, self).get_context_data(**kwargs)
        indicators = comet.Indicator.objects.visible(self.request.user)

        # Collections
        context = self.get_slot_context(context, 'Collection',
                                        'collections', 'col', indicators)

        # Outcomes (SubDomain)
        context = self.get_slot_context(context, 'Outcomes',
                                        'sub_domain', 'sdom', indicators)

        # Inputs and outputs
        context = self.get_slot_context(context, 'Inputs and outputs',
                                        'inputs_and_outputs', 'io', indicators)

        # Data collection method
        context = self.get_slot_context(context, 'Data collection',
                                        'data_collection_method', 'dcm', indicators)

        # Statuses
        context = self.get_status_context(context, indicators)

        return context

    def filter_queryset_by_slot(self, queryset, name, param_name):
        params = self.request.GET.getlist(param_name)
        if params:
            queryset = queryset.filter(slots__name=name,
                                       slots__value__in=params)
        return queryset

    def filter_queryset_by_status(self, queryset, param_name='st'):
        params = self.request.GET.getlist(param_name)
        if params:
            queryset = queryset.filter(statuses__state__in=params)
        return queryset

    def get_queryset(self, *args, **kwargs):
        queryset = super(BrowseIndicatorsAsHome, self).get_queryset(*args, **kwargs)

        # filter collections
        queryset = self.filter_queryset_by_slot(queryset,
                                                'Collection', 'col')

        # Filter Outcomes
        queryset = self.filter_queryset_by_slot(queryset,
                                                'Outcomes', 'sdom')

        # Filter Inputs and outputs
        queryset = self.filter_queryset_by_slot(queryset,
                                                'Inputs and outputs', 'io')

        # Data collection method
        queryset = self.filter_queryset_by_slot(queryset,
                                                'Data collection', 'dcm')

        # Statuses
        queryset = self.filter_queryset_by_status(queryset)

        return queryset.visible(self.request.user).distinct()


class ExportIndicators(BrowseConcepts):
    _model = comet.Indicator

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        self.kwargs['app'] = 'comet'
        context = super(ExportIndicators, self).get_context_data(**kwargs)
        return context

    def get_template_names(self):
        return "indicators/export_indicators.html"


def comparer(request):
    if request.GET.getlist('items', None):
        i1, i2, i3 = (request.GET.getlist('items') + [None, None, None])[:3]
        data = {
            'indicator_1': i1,
            'indicator_2': i2,
            'indicator_3': i3,
        }
    else:
        i1 = request.GET.get('indicator_1', None)
        i2 = request.GET.get('indicator_2', None)
        i3 = request.GET.get('indicator_3', None)
        data = request.GET
    indicator1 = comet.Indicator.objects.filter(id=i1).first()  # visible(request.user)
    indicator2 = comet.Indicator.objects.filter(id=i2).first()  # visible(request.user)
    indicator3 = comet.Indicator.objects.filter(id=i3).first()  # visible(request.user)
    indicators = [indicator1, indicator2, indicator3]
    form = CompareIndicatorsForm(data=data, user=request.user)
    return render(request, 'indicators/comparer.html', {
        'indicators': indicators, "form": form
    })


class CreateDataElementConcept(SuperUserRequiredMixin, GenericWithItemURLView, FormView):
    template_name = 'indicators/new_data_element_concept.html'
    form_class = QuickCreateDataElementConcept
    model_base = DataElement

    def get_form_kwargs(self):
        kwargs = super(CreateDataElementConcept, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def save_reversion(self, reversion):
        reversion.revisions.set_user(self.request.user)
        reversion.revisions.set_comment(
            _(u'Altered relationship of dataElementConcept for {name} "{object}" with Quick Create Data Element Concept.'.format(
                name=force_text(self.item._meta.verbose_name),
                object=force_text(self.item)
            ))
        )

    def copy_data_element_state(self, concept):
        for st in self.item.current_statuses():
            Status.objects.update_or_create(
                concept=concept,
                registrationAuthority=st.registrationAuthority,
                registrationDate=st.registrationDate,
                state=st.state
            )

    def form_valid(self, form):
        res = super(CreateDataElementConcept, self).form_valid(form)
        # TODO: Create with self.item status

        # CASE: existing Data Element Concept
        if form.cleaned_data.get('data_element_concept'):
            with transaction.atomic(), reversion.revisions.create_revision():
                self.item.dataElementConcept = form.cleaned_data['data_element_concept']
                self.item.save()
                self.save_reversion(reversion)
            return res

        # CASE: existing Object Class
        if form.cleaned_data.get('object_class'):
            obj_class = form.cleaned_data['object_class']
        # CASE: new Object class
        else:
            obj_class = ObjectClass.objects.create(
                name=form.cleaned_data.get('object_class_name'),
                definition=form.cleaned_data.get('object_class_definition'),
                workgroup=self.item.workgroup
            )
            # Assign data element status base on user input
            if form.cleaned_data.get('copy_data_element_state'):
                self.copy_data_element_state(obj_class)

        # CASE: existing Property
        if form.cleaned_data.get('property'):
            prop = form.cleaned_data['property']
        # CASE: new Object class
        else:
            prop = Property.objects.create(
                name=form.cleaned_data.get('property_name'),
                definition=form.cleaned_data.get('property_definition'),
                workgroup=self.item.workgroup
            )
            # Assign data element status base on user input
            if form.cleaned_data.get('copy_data_element_state'):
                self.copy_data_element_state(prop)

        # CASE: new Data Element Concept
        with transaction.atomic(), reversion.revisions.create_revision():
            dec = DataElementConcept.objects.create(
                name=form.cleaned_data.get('data_element_concept_name'),
                definition=form.cleaned_data.get('data_element_concept_definition'),
                workgroup=self.item.workgroup,
                property=prop,
                objectClass=obj_class,
            )
            self.item.dataElementConcept = dec
            self.item.save()
            self.save_reversion(reversion)

        # Assign data element status base on user input
        if form.cleaned_data.get('copy_data_element_state'):
            self.copy_data_element_state(dec)

        return res


# Export views
class Echo(object):
    """An object that implements just the write method of the file-like
    interface.
    """
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


class BaseExport(SuperUserRequiredMixin, View):

    filename = 'export.csv'

    def get(self, request, *args, **kwargs):
        pseudo_buffer = Echo()
        writer = csv.writer(pseudo_buffer)
        rows = self.get_rows(writer)
        response = StreamingHttpResponse(rows, content_type="text/csv")
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(self.filename)
        return response

    def get_rows(self):
        raise NotImplementedError(
            'You need to implement a method that returns an '
            'iterator with the rows of the CSV file'
        )

    def get_slot(self, concept, slots):
        for slot in slots:
            slot = get_single_slot(concept, slot).first()
            if slot and slot.value:
                return slot.value
        return None

    def get_code(self, concept):
        res = []
        for ident in concept.identifiers.all():
            res.append(ident.identifier)
        if res:
            return u', '.join(res)
        else:
            return concept.id


class ExportDataElements(BaseExport):
    filename = 'data_elements.csv'

    def get_rows(self, writer):
        # header
        yield writer.writerow((
            'ID',
            'Code',
            'Short name',
            'Name',
            'Definition',
            'Value type',
            'Form name',
            'Terms of use',
            'Value domain',
        ))
        # rows
        for de in DataElement.objects.all():
            yield writer.writerow((
                de.id,
                self.get_code(de),
                de.short_name,
                de.name,
                de.definition,
                self.get_slot(de, ['Value type']),
                self.get_slot(de, ['Form name', 'Form name EN']),
                self.get_slot(de, ['Terms of use']),
                self.get_code(de.valueDomain) if de.valueDomain else None,
            ))


class ExportValueDomains(BaseExport):

    filename = 'value_domains.csv'

    def get_rows(self, writer):
        yield writer.writerow((
            'ID',
            'Code',
            'Short name',
            'Name',
            'Value',
            'Meaning',
        ))
        # rows
        for vd in ValueDomain.objects.all():
            # Permissible Values of the Value Domain
            for pv in vd.permissibleValues:
                yield writer.writerow((
                    vd.id,
                    self.get_code(vd),
                    vd.short_name,
                    vd.name,
                    pv.value,
                    pv.meaning,
                ))
            # Supplementary Values of the Value Domain
            for sv in vd.supplementaryValues:
                yield writer.writerow((
                    vd.id,
                    self.get_code(vd),
                    vd.short_name,
                    vd.name,
                    sv.value,
                    sv.meaning,
                ))
            # Empty Value Domain
            if not vd.permissibleValues and not vd.supplementaryValues:
                yield writer.writerow((
                    vd.id,
                    self.get_code(vd),
                    vd.short_name,
                    vd.name,
                    None,
                    None,
                ))


class ImportDashboardView(SuperUserRequiredMixin, TemplateView):
    template_name = 'indicators/import_dashboard.html'


class ImportView(SuperUserRequiredMixin, FormView):
    template_name = 'indicators/import_form.html'
    form_class = ImportForm

    def get_success_url(self):
        return reverse('indicators_import_complete')

    def form_valid(self, form):
        # save spreadsheet on a tmp file
        path = default_storage.save(
            'spreadsheet-{}.xlsx'.format(time.time()),
            form.cleaned_data['spreadsheet'],
        )

        try:
            task = import_indicators.delay(
                path,
                form.cleaned_data['spreadsheet_type'],
                form.cleaned_data['collection'],
                clean=form.cleaned_data.get('clean_collection'),
                status=form.cleaned_data.get('status'),
            )
            self.request.session['import_task_id'] = task.id
            messages.add_message(self.request, messages.INFO, 'Importing file')
        except Exception as e:
            messages.add_message(self.request, messages.ERROR, 'Error: {}'.format(e))

        return super(ImportView, self).form_valid(form)


class ImportCompleteView(SuperUserRequiredMixin, TemplateView):
    template_name = 'indicators/import_complete.html'

    def get_context_data(self, **kwargs):
        context = super(ImportCompleteView, self).get_context_data(**kwargs)
        context['task_id'] = self.request.session.get('import_task_id')
        try:
            context['task'] = TaskResult.objects.get(task_id=context['task_id'])
        except TaskResult.DoesNotExist:
            context['task'] = AsyncResult(context['task_id'])
        return context


class TaskBaseView(SuperUserRequiredMixin, FormView):

    def get_success_url(self):
        return reverse(self.task_complete_view_name)

    def run_task(self, form):
        raise NotImplementedError('this method should return a task')

    def form_valid(self, form):
        try:
            task = self.run_task(form)
            self.request.session['{}_task_id'.format(self.task_name)] = task.id
            messages.add_message(self.request, messages.INFO, 'Executing: {}'.format(self.task_description))
        except Exception as e:
            messages.add_message(self.request, messages.ERROR, 'Error: {}'.format(e))
        return super(TaskBaseView, self).form_valid(form)


class TaskCompleteBaseView(SuperUserRequiredMixin, TemplateView):

    def get_context_data(self, **kwargs):
        context = super(TaskCompleteBaseView, self).get_context_data(**kwargs)
        context['task_id'] = self.request.session.get('{}_task_id'.format(self.task_name))
        if not context['task_id']:
            return context
        # if there's a test add it to the context
        try:
            context['task'] = TaskResult.objects.get(task_id=context['task_id'])
        except TaskResult.DoesNotExist:
            context['task'] = AsyncResult(context['task_id'])
        return context


class CleanDBView(TaskBaseView):
    task_name = 'clean_db'
    task_description = 'Remove database elements'
    task_complete_view_name = 'indicators_clean_db_complete'
    template_name = 'indicators/import_clean_db_form.html'
    form_class = CleanDBForm

    def run_task(self, form):
        return clean_data_base.delay()


class CleanDBCompleteView(TaskCompleteBaseView):
    task_name = 'clean_db'
    template_name = 'indicators/import_clean_db_complete.html'


class CleanCollectionView(TaskBaseView):
    task_name = 'clean_collection'
    task_description = 'Remove collection elements'
    task_complete_view_name = 'indicators_clean_collection_complete'
    template_name = 'indicators/import_clean_collection_form.html'
    form_class = CleanCollectionForm

    def run_task(self, form):
        return clean_collection.delay(form.cleaned_data.get('collection'))


class CleanCollectionCompleteView(TaskCompleteBaseView):
    task_name = 'clean_collection'
    template_name = 'indicators/import_clean_collection_complete.html'


class DHIS2ExportView(TaskBaseView):
    task_name = 'dhis2_export'
    task_description = 'Export elements to DHIS2'
    task_complete_view_name = 'indicators_dhis2_export_complete'
    template_name = 'indicators/dhis2_export_form.html'
    form_class = DHIS2ExportForm

    def run_task(self, form):
        indicator = get_object_or_404(comet.Indicator, pk=self.kwargs['pk'])
        return dhis2_export.delay(
            form.cleaned_data['server_url'],
            form.cleaned_data['username'],
            form.cleaned_data['password'],
            form.cleaned_data['api_version'],
            indicator.pk
        )

    def get_context_data(self, **kwargs):
        context = super(DHIS2ExportView, self).get_context_data(**kwargs)
        context['indicator'] = get_object_or_404(comet.Indicator, pk=self.kwargs['pk'])
        return context


class DHIS2ExportCompleteView(TaskCompleteBaseView):
    task_name = 'dhis2_export'
    template_name = 'indicators/dhis2_export_complete.html'
