"""Robustness of the pigment views against malformed / hand-edited query strings.

Filter values go straight from the URL into integer lookups, so anything that
isn't an integer used to raise ValueError inside the ORM and return a 500.
"""
import re

import pytest
from django.http import QueryDict
from django.urls import reverse

from pigments.factories import (
    ColorFamilyFactory,
    ManuscriptFactory,
    PigmentFactory,
    PigmentManuscriptFactory,
)
from pigments.views import build_active_pills, int_values


def test_int_values_keeps_integers_and_drops_the_rest():
    params = QueryDict('color=1&color=abc&color=&color=007&color=1.5&color=-3&color=' + '9' * 30)
    assert int_values(params, 'color') == ['1', '7', '-3']


def test_int_values_missing_key_is_empty():
    assert int_values(QueryDict(''), 'color') == []


@pytest.mark.django_db
@pytest.mark.parametrize('query', [
    'color=abc',
    'color=',
    'pfam=x',
    'country=1.5',
    "manuscript='",
    'century=abc',
    'century=',
    'color=' + '9' * 30,
    'century=' + '9' * 30,
])
def test_malformed_filter_value_is_ignored_not_500(client, query):
    PigmentFactory(with_formula=True)
    PigmentFactory(with_formula=True)

    response = client.get(reverse('pigments:list') + '?' + query)

    assert response.status_code == 200
    assert response.context['filtered_count'] == 2
    assert response.context['is_filtered'] is False
    assert response.context['active_pills'] == []


@pytest.mark.django_db
def test_malformed_value_alongside_valid_one_still_filters_by_valid(client):
    color = ColorFamilyFactory()
    match = PigmentFactory(with_formula=True, color_family=color)
    PigmentFactory(with_formula=True)

    response = client.get(reverse('pigments:list'), {'color': [str(color.pk), 'abc']})

    assert response.status_code == 200
    assert list(response.context['pigments']) == [match]
    assert response.context['is_filtered'] is True
    assert response.context['selected']['color'] == [str(color.pk)]


@pytest.mark.django_db
def test_malformed_filter_htmx_partial_is_ignored_not_500(client):
    PigmentFactory(with_formula=True)
    response = client.get(
        reverse('pigments:list'), {'century': 'nope'}, HTTP_HX_REQUEST='true',
    )
    assert response.status_code == 200
    assert 'pigments/pigment_list_partial.html' in [t.name for t in response.templates]


@pytest.mark.django_db
def test_selected_checkbox_ticked_for_zero_padded_id(client):
    """'?color=007' filters by pk 7 *and* ticks that checkbox — the selected
    values are canonicalised so they compare equal to the rendered ids."""
    color = ColorFamilyFactory()
    PigmentFactory(with_formula=True, color_family=color)

    response = client.get(reverse('pigments:list'), {'color': f'00{color.pk}'})

    assert response.context['selected']['color'] == [str(color.pk)]
    assert re.search(
        rf'name="color"\s+value="{color.pk}"\s+class="filter-select"\s+checked',
        response.content.decode(),
    )


@pytest.mark.django_db
def test_century_pills_merge_consecutive_and_dedupe():
    pills = build_active_pills(QueryDict('century=900&century=800&century=800&century=1100'))
    assert [(p['label'], p['values']) for p in pills] == [
        ('9th century–10th century', ['800', '900']),
        ('12th century', ['1100']),
    ]


@pytest.mark.django_db
def test_pill_for_unknown_id_is_skipped():
    color = ColorFamilyFactory(name='Blue')
    pills = build_active_pills(QueryDict(f'color={color.pk}&color=999999'))
    assert pills == [{'label': 'Blue', 'param': 'color', 'value': str(color.pk)}]


@pytest.mark.django_db
@pytest.mark.parametrize('dates', [
    {'date_start': 800},
    {'date_start': 850},
    {'date_start': 899},
    {'date_end': 850},
])
def test_century_filter_includes_single_date_manuscript(client, dates):
    """'c.800' (only one date known) is treated as that year: it gets a
    9th-century bucket and matches that filter, and no other century."""
    pigment = PigmentFactory(with_formula=True)
    PigmentManuscriptFactory(pigment=pigment, manuscript=ManuscriptFactory(**dates))

    response = client.get(reverse('pigments:list'), {'century': 800})

    assert list(response.context['pigments']) == [pigment]
    assert response.context['century_buckets'] == [{'start': 800, 'label': '9th century'}]
    assert response.context['active_pills'][0]['label'] == '9th century'

    for other in (700, 900):
        response = client.get(reverse('pigments:list'), {'century': other})
        assert response.context['filtered_count'] == 0


@pytest.mark.django_db
def test_century_filter_still_matches_ranges_and_skips_undated(client):
    ranged = PigmentFactory(with_formula=True)
    PigmentManuscriptFactory(pigment=ranged, manuscript=ManuscriptFactory(date_start=750, date_end=820))
    undated = PigmentFactory(with_formula=True)
    PigmentManuscriptFactory(pigment=undated, manuscript=ManuscriptFactory(date_start=None, date_end=None))

    response = client.get(reverse('pigments:list'), {'century': 800})

    assert list(response.context['pigments']) == [ranged]
    assert [b['start'] for b in response.context['century_buckets']] == [700, 800]


@pytest.mark.django_db
def test_century_at_int_limit_does_not_overflow(client):
    PigmentFactory(with_formula=True)
    response = client.get(reverse('pigments:list'), {'century': 2**63 - 1})
    assert response.status_code == 200
    assert response.context['filtered_count'] == 0


@pytest.mark.django_db
def test_pigment_detail_404_for_unknown_pk(client):
    assert client.get(reverse('pigments:detail', args=[999999])).status_code == 404
