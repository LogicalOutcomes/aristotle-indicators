from aristotle_mdr.contrib.browse.views import BrowseConcepts
from aristotle_mdr.contrib.slots.models import Slot
from comet import models
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from .forms import CompareIndicatorsForm, DHIS2ExportForm
from .models import Goal
from .exporters.dhis2_indicators import DHIS2Exporter


class BrowseIndicatorsAsHome(BrowseConcepts):
    _model = models.Indicator

    def get_slot_context(self, context, name, slug_name, param_name):
        context[slug_name] = Slot.objects.filter(
            name=name
        ).values('value').annotate(count=Count('value')).order_by('-count')
        context[param_name] = self.request.GET.getlist(param_name)
        return context

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        self.kwargs['app'] = 'comet'
        context = super(BrowseIndicatorsAsHome, self).get_context_data(**kwargs)

        # Collections
        context = self.get_slot_context(context, 'Collection',
                                        'collections', 'col')

        # SDGs
        context['sdgs'] = Goal.objects.all().annotate(count=Count('indicators')).exclude(count=0)
        context['selected_sdgs'] = self.request.GET.getlist('sdgs')

        # No Poverty
        context = self.get_slot_context(context, 'No Poverty',
                                        'no_poverty', 'no_poverty')

        # Theory of Change
        context = self.get_slot_context(context, 'Theory of Change',
                                        'theory_of_change', 'toc')

        # Data collection method
        context = self.get_slot_context(context, 'Data collection method',
                                        'data_collection_method', 'dcm')

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
                                                'No Poverty', 'no_poverty')

        # Filter Theory of Change
        queryset = self.filter_queryset_by_slot(queryset,
                                                'Theory of Change', 'toc')

        # Data collection method
        queryset = self.filter_queryset_by_slot(queryset,
                                                'Data collection method', 'dcm')

        return queryset.distinct()


class ExportIndicators(BrowseConcepts):
    _model = models.Indicator

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        self.kwargs['app'] = 'comet'
        context = super(ExportIndicators, self).get_context_data(**kwargs)
        return context

    def get_template_names(self):
        return "indicators/export_indicators.html"


# def home(request, path=''):
#     indicators = models.Indicator.objects.all() #visible(request.user)
#     frameworks = models.Framework.objects.all() #visible(request.user)
#     outcome_areas = models.OutcomeArea.objects.all() #visible(request.user)
#     return render(request, 'aristotle_mdr/static/home.html',{
#         'indicators':indicators,
#         'frameworks':frameworks,
#         'outcome_areas':outcome_areas,
#     })


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
    indicator1 = models.Indicator.objects.filter(id=i1).first()  # visible(request.user)
    indicator2 = models.Indicator.objects.filter(id=i2).first()  # visible(request.user)
    indicator3 = models.Indicator.objects.filter(id=i3).first()  # visible(request.user)
    indicators = [indicator1, indicator2, indicator3]
    form = CompareIndicatorsForm(data=data, user=request.user)
    return render(request, 'indicators/comparer.html', {
        'indicators': indicators, "form": form
    })


class DHIS2ExportView(FormView):
    template_name = 'indicators/dhis2_export_form.html'
    form_class = DHIS2ExportForm

    def get_success_url(self):
        return reverse('dhis2_export_complete')

    def get_context_data(self, **kwargs):
        context = super(DHIS2ExportView, self).get_context_data(**kwargs)
        context['indicator'] = get_object_or_404(models.Indicator, pk=self.kwargs['pk'])
        return context

    def form_valid(self, form):
        DHIS2Exporter(
            form.cleaned_data['server_url'],
            form.cleaned_data['username'],
            form.cleaned_data['password'],
            form.cleaned_data['api_version']
        ).export_indicator(
            get_object_or_404(models.Indicator, pk=self.kwargs['pk'])
        )
        return super(DHIS2ExportView, self).form_valid(form)


class DHIS2ExportCompleteView(TemplateView):
    template_name = 'indicators/dhis2_export_complete.html'
