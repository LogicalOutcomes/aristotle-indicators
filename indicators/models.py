from __future__ import unicode_literals
import aristotle_mdr as aristotle
from comet.models import Indicator
from django.db import models
from django.utils.encoding import python_2_unicode_compatible


class Instrument(aristotle.models.concept):
    template = "indicators/instrument.html"
    # population = models.ForeignKey(Population, null=True)
    population = aristotle.models.RichTextField()
    limitations = aristotle.models.RichTextField()
    where_to_get = aristotle.models.RichTextField()
    terms_of_use = aristotle.models.RichTextField()

    indicators = models.ManyToManyField(
        Indicator,
        related_name='instruments'
    )


class Goal(aristotle.models.concept):
    """
    On September 25th 2015, countries adopted a set of goals to end poverty,
    protect the planet, and ensure prosperity for all as part of a new sustainable development agenda.
    Each goal has specific targets to be achieved over the next 15 years. - http://www.un.org/sustainabledevelopment/sustainable-development-goals/
    """
    template = "indicators/goal.html"

    indicators = models.ManyToManyField(
        Indicator,
        related_name='related_goals'
    )


# DHIS2 Categories for Data Elements
@python_2_unicode_compatible
class DHIS2Category(models.Model):
    code = models.CharField(max_length=64)
    collection = models.CharField(max_length=64)
    short_name = models.CharField(max_length=64)
    name = models.CharField(max_length=128)

    class Meta:
        abstract = True
        ordering = ['short_name']

    def __str__(self):
        return '{}'.format(self.short_name)


class CategoryOption(DHIS2Category):
    pass


class Category(DHIS2Category):
    options = models.ManyToManyField(
        CategoryOption,
        related_name='categories'
    )


class CategoryCombination(DHIS2Category):

    categories = models.ManyToManyField(
        Category,
        related_name='category_combination'
    )
