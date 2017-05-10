from aristotle_mdr.contrib.browse.views import BrowseConcepts
from aristotle_mdr.contrib.slots.models import Slot
from comet import models
from django.db.models import Count
from django.shortcuts import render
from .forms import CompareIndicatorsForm
from .models import Goal


class BrowseIndicatorsAsHome(BrowseConcepts):
    _model = models.Indicator

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        self.kwargs['app'] = 'comet'
        context = super(BrowseIndicatorsAsHome, self).get_context_data(**kwargs)

        # Collections
        context['collections'] = Slot.objects.filter(
            name='Collection'
        ).values('value').annotate(count=Count('value')).order_by('-count')
        context['selected_collections'] = self.request.GET.getlist('collections')

        # SDGs
        context['sdgs'] = Goal.objects.all().annotate(count=Count('indicators')).exclude(count=0)
        context['selected_sdgs'] = self.request.GET.getlist('sdgs')

        # No Poverty
        context['no_poverty'] = Slot.objects.filter(
            name='No Poverty'
        ).values('value').annotate(count=Count('value')).order_by('-count')
        context['selected_no_poverty'] = self.request.GET.getlist('no_poverty')

        # Theory of Change
        context['theory_of_change'] = Slot.objects.filter(
            name='Theory of Change'
        ).values('value').annotate(count=Count('value')).order_by('-count')
        context['selected_theory_of_change'] = self.request.GET.getlist('toc')

        return context

    def get_queryset(self, *args, **kwargs):
        queryset = super(BrowseIndicatorsAsHome, self).get_queryset(*args, **kwargs)

        # filter collections
        collections = self.request.GET.getlist('collections')
        if collections:
            queryset = queryset.filter(slots__name='Collection',
                                       slots__value__in=collections)

        # filter SDGs
        sdgs = self.request.GET.getlist('sdgs')
        if sdgs:
            queryset = queryset.filter(related_goals__short_name__in=sdgs)

        # Filter No Poverty
        no_poverty = self.request.GET.getlist('no_poverty')
        if no_poverty:
            queryset = queryset.filter(slots__name='No Poverty',
                                       slots__value__in=no_poverty)

        # Filter Theory of Change
        theory_of_change = self.request.GET.getlist('toc')
        if theory_of_change:
            queryset = queryset.filter(slots__name='Theory of Change',
                                       slots__value__in=theory_of_change)

        return queryset


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
