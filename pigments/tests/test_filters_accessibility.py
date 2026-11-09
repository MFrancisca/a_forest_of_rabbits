"""Accessible pigment filters (issue #12): dropdown state, fieldset grouping,
announced results, specific pill labels, and a no-JavaScript fallback."""
import re

import pytest
from django.urls import reverse

from pigments.factories import (
    ColorFamilyFactory,
    ManuscriptFactory,
    PigmentFactory,
    PigmentManuscriptFactory,
)
from pigments.views import filter_groups

pytestmark = pytest.mark.django_db

HTMX = {'HTTP_HX_REQUEST': 'true'}


def _get(client, query='', **headers):
    response = client.get(reverse('pigments:list') + ('?' + query if query else ''), **headers)
    assert response.status_code == 200
    return response.content.decode(), response.context


def _attr(tag, name):
    match = re.search(rf'\s{name}="([^"]*)"', tag)
    return match.group(1) if match else None


@pytest.fixture
def blue():
    color = ColorFamilyFactory(name='Blue')
    PigmentFactory(with_formula=True, color_family=color)
    return color


# --- filter_groups ---------------------------------------------------------------

def test_filter_groups_list_every_dimension_in_order_with_checked_state(client, blue):
    _, context = _get(client, f'color={blue.pk}')
    groups = context['filter_groups']

    assert [(g['name'], g['label']) for g in groups] == [
        ('color', 'Color Family'),
        ('pfam', 'Pigment Family'),
        ('country', 'Country'),
        ('manuscript', 'Manuscript'),
        ('century', 'Time Period'),
    ]
    [color_group] = [g for g in groups if g['name'] == 'color']
    assert color_group['options'] == [{'value': blue.pk, 'label': 'Blue', 'checked': True}]


def test_filter_groups_century_options_use_bucket_start_and_label():
    groups = filter_groups(
        {'color_families': [], 'pigment_families': [], 'countries': [], 'manuscripts': [],
         'century_buckets': [{'start': 800, 'label': '9th century'}]},
        {'color': [], 'pfam': [], 'country': [], 'manuscript': [], 'century': ['800']},
    )
    assert groups[-1]['options'] == [{'value': 800, 'label': '9th century', 'checked': True}]


# --- dropdown markup ----------------------------------------------------------------

def test_each_filter_is_a_labelled_fieldset_controlled_by_its_button(client, blue):
    html, _ = _get(client)

    form = re.search(r'<form[^>]*id="filter-form"[^>]*>', html).group(0)
    assert _attr(form, 'role') == 'search' and _attr(form, 'aria-label') == 'Filter pigments'

    for name, label in [('color', 'Color Family'), ('pfam', 'Pigment Family'), ('country', 'Country'),
                        ('manuscript', 'Manuscript'), ('century', 'Time Period')]:
        button = re.search(rf'<button[^>]*aria-controls="filter-{name}"[^>]*>', html).group(0)
        assert _attr(button, 'aria-expanded') == 'false'
        assert ':aria-expanded="open.toString()"' in button
        fieldset = html.split(f'<fieldset id="filter-{name}"', 1)[1].split('</fieldset>', 1)[0]
        assert re.search(rf'<legend class="filter-legend sr-only">{label}</legend>', fieldset)


def test_dropdown_closes_on_escape_outside_click_and_focus_leaving(client, blue):
    html, _ = _get(client)
    assert html.count('@keydown.escape="if (open) { open = false; $refs.button.focus() }"') == 5
    assert html.count('@click.outside="open = false"') == 5
    assert html.count('@focusout="if ($event.relatedTarget && !$el.contains($event.relatedTarget)) open = false"') == 5


def test_no_js_fallback_has_apply_button_and_visible_panels(client, blue):
    html, _ = _get(client)
    head = html.split('</head>', 1)[0]
    assert '.filter-panel { display: block !important; position: static !important; }' in head
    noscripts = re.findall(r'<noscript>(.*?)</noscript>', html, re.S)
    assert any('<button type="submit"' in n and 'Apply filters' in n for n in noscripts)


def test_plain_get_submission_filters_results(client, blue):
    PigmentFactory(with_formula=True)  # another colour
    _, context = _get(client, f'color={blue.pk}')
    assert context['filtered_count'] == 1 and context['total_count'] == 2


# --- announcing results ---------------------------------------------------------------

def test_live_region_sits_outside_the_htmx_swap_target(client, blue):
    html, _ = _get(client)
    live = html.index('<p id="result-status" class="sr-only" aria-live="polite"></p>')
    assert live < html.index('<div id="pigment-results">')

    fragment, _ = _get(client, f'color={blue.pk}', **HTMX)
    assert 'result-status' not in fragment  # swapping never replaces the live region
    assert re.search(r'<p id="result-count" tabindex="-1"[^>]*>\s*1 of 1 pigment\s*</p>', fragment)


# --- filter pills ----------------------------------------------------------------------

def test_pill_remove_buttons_name_the_filter_and_carry_their_values(client, blue):
    early = ManuscriptFactory(date_start=850, date_end=850)
    late = ManuscriptFactory(date_start=950, date_end=950)
    pigment = PigmentFactory(with_formula=True)
    PigmentManuscriptFactory(pigment=pigment, manuscript=early)
    PigmentManuscriptFactory(pigment=pigment, manuscript=late)

    html, _ = _get(client, f'color={blue.pk}&century=800&century=900', **HTMX)

    buttons = re.findall(r'<button[^>]*data-remove-filter[^>]*>.*?</button>', html, re.S)
    assert len(buttons) == 2
    color_button, century_button = buttons
    assert _attr(color_button, 'aria-label') == 'Remove filter: Blue'
    assert (_attr(color_button, 'data-param'), _attr(color_button, 'data-values')) == ('color', str(blue.pk))
    assert _attr(century_button, 'aria-label') == 'Remove filter: 9th century–10th century'
    assert (_attr(century_button, 'data-param'), _attr(century_button, 'data-values')) == ('century', '800 900')
    assert '<span aria-hidden="true">&#x00D7;</span>' in color_button
    assert 'onclick' not in html
