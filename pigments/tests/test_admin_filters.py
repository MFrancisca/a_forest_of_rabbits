"""Filters on the admin Pigments listing (Snippets → Pigments)."""
import pytest
from django.urls import reverse

from pigments.factories import (
    BrandFactory, FormulaFactory, FormulaPartFactory, PaintFactory, PigmentFactory,
)

pytestmark = pytest.mark.django_db

LIST_URL = reverse('wagtailsnippets_pigments_pigment:list')


def _listed(admin_client, **params):
    response = admin_client.get(LIST_URL, params)
    assert response.status_code == 200
    return sorted(p.name for p in response.context['object_list'])


@pytest.fixture
def pigments():
    with_formula = PigmentFactory(name='With formula')
    FormulaFactory(pigment=with_formula)
    PigmentFactory(name='Without formula')


def test_has_formula_yes(admin_client, pigments):
    assert _listed(admin_client, has_formula='true') == ['With formula']


def test_has_formula_no(admin_client, pigments):
    assert _listed(admin_client, has_formula='false') == ['Without formula']


def test_has_formula_any_lists_all(admin_client, pigments):
    assert _listed(admin_client) == ['With formula', 'Without formula']


def test_paint_filter(admin_client):
    paint = PaintFactory()
    FormulaPartFactory(paint=paint, formula=FormulaFactory(pigment=PigmentFactory(name='Uses it')))
    FormulaPartFactory(formula=FormulaFactory(pigment=PigmentFactory(name='Other paint')))
    PigmentFactory(name='No formula')
    assert _listed(admin_client, paint=paint.pk) == ['Uses it']


def test_paint_filter_lists_a_pigment_once(admin_client):
    paint = PaintFactory()
    pigment = PigmentFactory(name='Twice')
    FormulaPartFactory(paint=paint, formula=FormulaFactory(pigment=pigment))
    FormulaPartFactory(paint=paint, formula=FormulaFactory(pigment=pigment))
    assert _listed(admin_client, paint=paint.pk) == ['Twice']


def test_paint_filter_unused_paint_lists_nothing(admin_client, pigments):
    assert _listed(admin_client, paint=PaintFactory().pk) == []


def test_filters_combine(admin_client):
    paint = PaintFactory()
    FormulaPartFactory(paint=paint, formula=FormulaFactory(pigment=PigmentFactory(name='Uses it')))
    assert _listed(admin_client, paint=paint.pk, has_formula='false') == []


def test_paint_options_are_labelled_brand_then_paint(admin_client):
    PaintFactory(brand=BrandFactory(name='Rublev'), name='Lead White')
    PaintFactory(brand=BrandFactory(name='Daniel Smith'), name='Smalt')
    response = admin_client.get(LIST_URL)
    choices = [label for _, label in response.context['filters'].form.fields['paint'].choices][1:]
    assert choices == ['Daniel Smith — Smalt', 'Rublev — Lead White']


def test_listing_loads_select2_for_the_paint_filter(admin_client):
    html = admin_client.get(LIST_URL).content.decode()
    assert 'select2.min.js' in html
    assert 'pigment-paint-filter.js' in html
    assert 'data-pigment-paint-filter' in html


def test_other_listings_do_not_load_select2(admin_client):
    html = admin_client.get(reverse('wagtailsnippets_pigments_paint:list')).content.decode()
    assert 'select2' not in html

