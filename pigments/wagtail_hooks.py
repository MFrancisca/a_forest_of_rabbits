# pigments/wagtail_hooks.py
"""Admin customisations for the pigments snippets.

The other pigments models are registered with @register_snippet in models.py.
Pigment is registered here, through a viewset, so its listing can have filters.
"""
import django_filters
from django import forms
from django.db.models import Exists, OuterRef
from wagtail.admin.filters import WagtailFilterSet
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from pigments.models import Formula, Paint, Pigment

# Select2 4.0.13, served from static (checked against cdnjs's SRI hashes) rather
# than a CDN, so nothing third-party runs in the admin.
SELECT2 = 'pigments/vendor/select2-4.0.13'


class PaintFilterSelect(forms.Select):
    """A <select> that pigment-paint-filter.js turns into a searchable Select2 dropdown.

    Every paint is in the page and searched in the browser, which stays quick up
    to a few thousand paints. Select2 needs jQuery, which the Wagtail admin
    already loads on every page.
    """

    def __init__(self, attrs=None, choices=()):
        super().__init__({'data-pigment-paint-filter': '', **(attrs or {})}, choices)

    class Media:
        css = {'all': [f'{SELECT2}/select2.min.css', 'pigments/css/pigment-paint-filter.css']}
        js = [f'{SELECT2}/select2.min.js', 'pigments/js/pigment-paint-filter.js']


class PigmentFilterSet(WagtailFilterSet):
    has_formula = django_filters.BooleanFilter(label='Has formula', method='filter_has_formula')
    paint = django_filters.ModelChoiceFilter(
        label='Paint',
        help_text='Pigments with a formula that uses this paint.',
        queryset=Paint.objects.select_related('brand').order_by('brand__name', 'name'),
        field_name='formulas__parts__paint',
        distinct=True,
        empty_label='Any paint',
        widget=PaintFilterSelect,
    )

    class Meta:
        model = Pigment
        fields = []

    def filter_has_formula(self, queryset, name, value):
        # Exists, not a join, so a pigment with several formulas is listed once.
        has_formula = Exists(Formula.objects.filter(pigment=OuterRef('pk')))
        return queryset.filter(has_formula if value else ~has_formula)


class PigmentViewSet(SnippetViewSet):
    model = Pigment
    filterset_class = PigmentFilterSet


register_snippet(PigmentViewSet)
