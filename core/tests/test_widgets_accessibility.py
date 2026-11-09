"""Keyboard and screen-reader support for interactive widgets (issue #11):
lightbox, manuscript table notes, accordions, formula tabs, carousels."""
import re

import pytest
import wagtail_factories
from django.urls import reverse

from blog.factories import ProjectPageFactory
from pigments.factories import (
    FormulaFactory,
    PigmentFactory,
    PigmentImageFactory,
    PigmentManuscriptFactory,
)

pytestmark = pytest.mark.django_db


def _detail(client, pigment):
    response = client.get(reverse('pigments:detail', args=[pigment.pk]))
    assert response.status_code == 200
    return response.content.decode(), response.context


def _tags(html, pattern):
    """All opening tags matching `pattern` (e.g. r'<button[^>]*role="tab"')."""
    return re.findall(pattern + r'[^>]*>', html)


def _attr(tag, name):
    match = re.search(rf'\s{name}="([^"]*)"', tag)
    return match.group(1) if match else None


# --- lightbox -----------------------------------------------------------------

def test_enlargeable_images_are_buttons_opening_a_native_dialog(client):
    pigment = PigmentFactory(name='Azurite')
    PigmentImageFactory(pigment=pigment, image=wagtail_factories.ImageFactory(), alt_text='Azurite paint-out')
    FormulaFactory(pigment=pigment, image=wagtail_factories.ImageFactory())

    html, _ = _detail(client, pigment)

    openers = _tags(html, r'<button[^>]*@click="openLightbox\(\$el\)"')
    assert len(openers) == 2  # featured image + formula image
    for opener in openers:
        assert _attr(opener, 'aria-haspopup') == 'dialog'
        # The enlarged view uses a larger uncropped rendition, not the inline one.
        assert 'max-1600x1600' in _attr(opener, 'data-full')
    assert html.count('<span class="sr-only">Enlarge image: </span>') == 2
    # No click handlers left on bare images.
    assert not re.search(r'<img[^>]*@click', html)

    dialog = _tags(html, r'<dialog')
    assert len(dialog) == 1 and _attr(dialog[0], 'aria-label') == 'Enlarged image'
    # The enlarged image takes the opener's alt text instead of a generic one.
    assert ':alt="lightboxAlt"' in html
    assert re.search(r'<button[^>]*autofocus[^>]*>\s*Close\s*</button>', html)


def test_no_lightbox_triggers_without_images(client):
    html, _ = _detail(client, PigmentFactory())
    assert 'openLightbox($el)' not in html.split('<dialog')[0]


# --- missing pigment images -----------------------------------------------------

def test_pigment_images_whose_file_was_deleted_are_skipped(client):
    pigment = PigmentFactory()
    PigmentImageFactory(pigment=pigment, image=None, sort_order=0)
    real = PigmentImageFactory(pigment=pigment, image=wagtail_factories.ImageFactory(), sort_order=1)

    _, context = _detail(client, pigment)

    assert context['featured_image'] == real
    assert context['additional_images'] == []


# --- manuscript table notes ------------------------------------------------------

def test_manuscript_rows_with_notes_have_a_toggle_button(client):
    pigment = PigmentFactory()
    with_notes = PigmentManuscriptFactory(pigment=pigment, notes='Faded on folio 3.')
    PigmentManuscriptFactory(pigment=pigment)

    html, _ = _detail(client, pigment)

    [toggle] = _tags(html, r'<button[^>]*aria-controls="manuscript-notes-')
    assert _attr(toggle, 'aria-controls') == f'manuscript-notes-{with_notes.pk}'
    assert _attr(toggle, 'aria-expanded') == 'false'
    assert f'id="manuscript-notes-{with_notes.pk}"' in html
    assert '<span class="sr-only"> (details)</span>' in html


# --- accordions -----------------------------------------------------------------

def test_formula_notes_are_a_native_disclosure(client):
    pigment = PigmentFactory()
    FormulaFactory(pigment=pigment, notes='Grind with gum arabic.')

    html, _ = _detail(client, pigment)

    details = html.split('<details', 1)[1].split('</details>', 1)[0]
    assert re.search(r'<summary[^>]*>.*Notes', details, re.S)
    assert 'Grind with gum arabic.' in details
    assert 'notesOpen' not in html


def test_technical_information_is_a_native_disclosure(client, projects_index):
    project = ProjectPageFactory(
        parent=projects_index,
        technical_info=[{'type': 'freeform', 'value': '<p>Hand-forged.</p>'}],
    )
    html = client.get(project.url).content.decode()

    details = html.split('<details', 1)[1].split('</details>', 1)[0]
    assert re.search(r'<summary[^>]*>.*Technical Information', details, re.S)
    assert 'Hand-forged.' in details
    assert 'techOpen' not in html


# --- formula tabs ----------------------------------------------------------------

def test_formula_brands_are_aria_tabs_linked_to_panels(client):
    pigment = PigmentFactory()
    FormulaFactory(pigment=pigment)
    FormulaFactory(pigment=pigment)

    html, _ = _detail(client, pigment)

    assert _tags(html, r'<div[^>]*role="tablist"')
    tabs = _tags(html, r'<button[^>]*role="tab"')
    panels = _tags(html, r'<div[^>]*role="tabpanel"')
    assert len(tabs) == len(panels) == 2

    assert [_attr(t, 'aria-selected') for t in tabs] == ['true', 'false']
    assert [_attr(t, 'tabindex') for t in tabs] == ['0', '-1']
    for tab, panel in zip(tabs, panels):
        assert _attr(tab, 'aria-controls') == _attr(panel, 'id')
        assert _attr(panel, 'aria-labelledby') == _attr(tab, 'id')
    # Only the first panel is visible before Alpine runs.
    assert ['x-cloak' in p for p in panels] == [False, True]
    # Arrow / Home / End keys move between tabs.
    for key in ('right', 'left', 'home', 'end'):
        assert f'@keydown.{key}.prevent' in html


# --- carousels -------------------------------------------------------------------

def _carousel_page(projects_index, images, title='Angles'):
    return ProjectPageFactory(parent=projects_index, body=[{
        'type': 'carousel',
        'value': {'title': title, 'images': [{'image': i.pk, 'caption': ''} for i in images]},
    }])


def _assert_carousel_controls(html, count):
    assert 'aria-label="Previous image"' in html
    assert 'aria-label="Next image"' in html
    dots = _tags(html, r'<button[^>]*aria-label="Show image')
    assert len(dots) == count
    assert [_attr(d, 'aria-current') for d in dots] == ['true'] + [None] * (count - 1)
    assert all('p-2' in _attr(d, 'class').split() for d in dots)  # 24px+ target
    assert re.search(rf'aria-live="polite"[^>]*>Image 1 of {count}</p>', html)


def test_project_carousel_is_a_labelled_region_with_full_controls(client, projects_index):
    page = _carousel_page(projects_index, [wagtail_factories.ImageFactory() for _ in range(3)])
    html = client.get(page.url).content.decode()

    [region] = _tags(html, r'<section[^>]*aria-roledescription="carousel"')
    # A titled carousel is named by its visible heading, not a duplicate label.
    heading_id = _attr(region, 'aria-labelledby')
    assert heading_id and _attr(region, 'aria-label') is None
    assert re.search(rf'<h2 id="{heading_id}"[^>]*>Angles</h2>', html)
    slides = _tags(html, r'<div[^>]*aria-roledescription="slide"')
    assert [_attr(s, 'aria-label') for s in slides] == ['1 of 3', '2 of 3', '3 of 3']
    assert ['x-cloak' in s for s in slides] == [False, True, True]
    _assert_carousel_controls(html, 3)


def test_untitled_project_carousel_gets_a_generic_label(client, projects_index):
    page = _carousel_page(projects_index, [wagtail_factories.ImageFactory() for _ in range(2)], title='')
    html = client.get(page.url).content.decode()

    [region] = _tags(html, r'<section[^>]*aria-roledescription="carousel"')
    assert _attr(region, 'aria-label') == 'Image carousel'
    assert _attr(region, 'aria-labelledby') is None


def test_carousel_controls_are_hidden_until_javascript_runs(client, projects_index):
    page = _carousel_page(projects_index, [wagtail_factories.ImageFactory() for _ in range(2)])
    html = client.get(page.url).content.decode()

    [controls] = _tags(html, r'<div x-cloak class="flex items-center justify-center')
    assert html.index(controls) < html.index('aria-label="Previous image"')


def test_project_carousel_skips_slides_with_deleted_images(client, projects_index):
    """Deleted images used to keep their slide index, so the first visible slide
    could be blank and the dots counted slides that weren't there."""
    gone, a, b = (wagtail_factories.ImageFactory() for _ in range(3))
    page = _carousel_page(projects_index, [gone, a, b])
    gone.delete()

    html = client.get(page.url).content.decode()

    slides = _tags(html, r'<div[^>]*aria-roledescription="slide"')
    assert [_attr(s, 'aria-label') for s in slides] == ['1 of 2', '2 of 2']
    _assert_carousel_controls(html, 2)


def test_project_carousel_with_only_deleted_images_renders_nothing(client, projects_index):
    gone = wagtail_factories.ImageFactory()
    page = _carousel_page(projects_index, [gone], title='Vanished')
    gone.delete()

    html = client.get(page.url).content.decode()
    assert 'Vanished' not in html.split('<main', 1)[1]
    assert 'aria-roledescription="carousel"' not in html


def test_pigment_carousel_has_full_controls(client):
    pigment = PigmentFactory(name='Malachite')
    for order in range(3):
        PigmentImageFactory(pigment=pigment, image=wagtail_factories.ImageFactory(), sort_order=order)

    html, _ = _detail(client, pigment)

    [region] = _tags(html, r'<section[^>]*aria-roledescription="carousel"')
    assert _attr(region, 'aria-label') == 'More images of Malachite'
    _assert_carousel_controls(html, 2)  # the first image is featured above
