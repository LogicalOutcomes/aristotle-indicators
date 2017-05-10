from django.contrib import admin
from aristotle_mdr.register import register_concept
from .models import (
    Category,
    CategoryCombination,
    CategoryOption,
    Goal,
    Instrument,
)

register_concept(Instrument)
register_concept(Goal)


@admin.register(CategoryOption)
class CategoryOptionAdmin(admin.ModelAdmin):
    list_display = ['code', 'short_name', 'name']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['code', 'short_name', 'name']


@admin.register(CategoryCombination)
class CategoryCombinationAdmin(admin.ModelAdmin):
    list_display = ['code', 'short_name', 'name']
