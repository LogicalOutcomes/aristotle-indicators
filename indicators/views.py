import time
from aristotle_mdr.contrib.browse.views import BrowseConcepts
from aristotle_mdr.contrib.slots.models import Slot
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
from .exporters.dhis2_indicators import DHIS2Exporter
from .forms import CompareIndicatorsForm, DHIS2ExportForm, ImportForm, CleanDBForm
from .models import Goal
from .tasks import import_indicators, clean_data_base


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

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        self.kwargs['app'] = 'comet'
        context = super(BrowseIndicatorsAsHome, self).get_context_data(**kwargs)
        indicators = comet.Indicator.objects.all()

        # Collections
        context = self.get_slot_context(context, 'Collection',
                                        'collections', 'col', indicators)

        # SDGs
        context['sdgs'] = Goal.objects.all().annotate(count=Count('indicators')).exclude(count=0)
        context['selected_sdgs'] = self.request.GET.getlist('sdgs')

        # No Poverty
        context = self.get_slot_context(context, 'No Poverty',
                                        'no_poverty', 'no_pov', indicators)

        # Theory of Change
        context = self.get_slot_context(context, 'Theory of Change',
                                        'theory_of_change', 'toc', indicators)

        # Data collection method
        context = self.get_slot_context(context, 'Data collection method',
                                        'data_collection_method', 'dcm', indicators)

        return context

    def filter_queryset_by_slot(self, queryset, name, param_name):
        params = self.request.GET.getlist(param_name)
        if params:
            queryset = queryset.filter(slots__name=name,
                                       slots__value__in=params)
        return queryset

    def get_queryset(self, *args, **kwargs):
        queryset = super(BrowseIndicatorsAsHome, self).get_queryset(*args, **kwargs)

        # filter collections
        queryset = self.filter_queryset_by_slot(queryset,
                                                'Collection', 'col')

        # filter SDGs
        sdgs = self.request.GET.getlist('sdgs')
        if sdgs:
            queryset = queryset.filter(related_goals__short_name__in=sdgs)

        # Filter No Poverty
        queryset = self.filter_queryset_by_slot(queryset,
                                                'No Poverty', 'no_pov')

        # Filter Theory of Change
        queryset = self.filter_queryset_by_slot(queryset,
                                                'Theory of Change', 'toc')

        # Data collection method
        queryset = self.filter_queryset_by_slot(queryset,
                                                'Data collection method', 'dcm')

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
                form.cleaned_data['collection']
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


class CleanDBView(SuperUserRequiredMixin, FormView):
    template_name = 'indicators/import_clean_db_form.html'
    form_class = CleanDBForm

    def get_success_url(self):
        return reverse('indicators_clean_db_complete')

    def form_valid(self, form):
        try:
            task = clean_data_base.delay()
            self.request.session['clean_db_task_id'] = task.id
            messages.add_message(self.request, messages.INFO, 'Removing elements from database')
        except Exception as e:
            messages.add_message(self.request, messages.ERROR, 'Error: {}'.format(e))

        return super(CleanDBView, self).form_valid(form)


class CleanDBCompleteView(SuperUserRequiredMixin, TemplateView):
    template_name = 'indicators/import_clean_db_complete.html'

    def get_context_data(self, **kwargs):
        context = super(CleanDBCompleteView, self).get_context_data(**kwargs)
        context['task_id'] = self.request.session.get('clean_db_task_id')
        try:
            context['task'] = TaskResult.objects.get(task_id=context['task_id'])
        except TaskResult.DoesNotExist:
            context['task'] = AsyncResult(context['task_id'])
        return context


class DHIS2ExportView(FormView):
    template_name = 'indicators/dhis2_export_form.html'
    form_class = DHIS2ExportForm

    def get_success_url(self):
        return reverse('dhis2_export_complete')

    def get_context_data(self, **kwargs):
        context = super(DHIS2ExportView, self).get_context_data(**kwargs)
        context['indicator'] = get_object_or_404(comet.Indicator, pk=self.kwargs['pk'])
        return context

    def form_valid(self, form):
        DHIS2Exporter(
            form.cleaned_data['server_url'],
            form.cleaned_data['username'],
            form.cleaned_data['password'],
            form.cleaned_data['api_version']
        ).export_indicator(
            get_object_or_404(comet.Indicator, pk=self.kwargs['pk'])
        )
        return super(DHIS2ExportView, self).form_valid(form)


class DHIS2ExportCompleteView(TemplateView):
    template_name = 'indicators/dhis2_export_complete.html'
