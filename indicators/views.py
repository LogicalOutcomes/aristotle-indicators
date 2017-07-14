import time
from aristotle_mdr.contrib.browse.views import BrowseConcepts
from aristotle_mdr.contrib.slots.models import Slot
from aristotle_mdr.models import Status
from celery.result import AsyncResult
from comet import models as comet
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django_celery_results.models import TaskResult
from .forms import (
    CompareIndicatorsForm, DHIS2ExportForm, ImportForm, CleanDBForm,
    CleanCollectionForm
)
from .tasks import (
    import_indicators, clean_data_base, clean_collection,
    dhis2_export
)


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
        indicators = comet.Indicator.objects.all()

        # Collections
        context = self.get_slot_context(context, 'Collection',
                                        'collections', 'col', indicators)

        # Outcomes (SubDomain)
        context = self.get_slot_context(context, 'Outcomes',
                                        'sub_domain', 'sdom', indicators)

        # Theory of Change
        context = self.get_slot_context(context, 'Theory of change',
                                        'theory_of_change', 'toc', indicators)

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

        # Filter Theory of Change
        queryset = self.filter_queryset_by_slot(queryset,
                                                'Theory of change', 'toc')

        # Data collection method
        queryset = self.filter_queryset_by_slot(queryset,
                                                'Data collection', 'dcm')

        # Statuses
        queryset = self.filter_queryset_by_status(queryset)

        return queryset.distinct()


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
                clean=form.cleaned_data.get('clean_collection')
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
