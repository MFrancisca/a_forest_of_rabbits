"""The admin "Paint" filter's Select2 dropdown, in headless Chromium.

Opt-in like the axe checks (it needs a browser):

    .venv/bin/pytest -m a11y --no-cov pigments/tests/test_admin_filters_browser.py
"""
import os

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from pigments.factories import (
    BrandFactory, FormulaFactory, FormulaPartFactory, PaintFactory, PigmentFactory,
)

pytestmark = [pytest.mark.a11y, pytest.mark.django_db(transaction=True, serialized_rollback=True)]

playwright_sync = pytest.importorskip('playwright.sync_api')

LIST_PATH = reverse('wagtailsnippets_pigments_pigment:list')


@pytest.fixture
def page(live_server, request):
    # Playwright's sync API runs an event loop; Django's ORM guard would refuse
    # queries from it while the browser is up.
    previous = os.environ.get('DJANGO_ALLOW_ASYNC_UNSAFE')
    os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
    client = Client()
    client.force_login(get_user_model().objects.create_superuser('admin', 'admin@example.com', 'pw'))
    try:
        with playwright_sync.sync_playwright() as p:
            try:
                browser = p.chromium.launch()
            except playwright_sync.Error as exc:
                if "Executable doesn't exist" not in str(exc):
                    raise
                pytest.skip('Chromium not installed; run .venv/bin/playwright install chromium')
            context = browser.new_context(color_scheme=request.param, viewport={'width': 1280, 'height': 900})
            context.add_cookies([{
                'name': settings.SESSION_COOKIE_NAME,
                'value': client.cookies[settings.SESSION_COOKIE_NAME].value,
                'url': live_server.url,
            }])
            page = context.new_page()
            page.js_errors = []
            page.on('pageerror', lambda e: page.js_errors.append(str(e)))
            yield page
            browser.close()
    finally:
        if previous is None:
            os.environ.pop('DJANGO_ALLOW_ASYNC_UNSAFE', None)
        else:
            os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = previous


@pytest.mark.parametrize('page', ['light', 'dark'], indirect=True)
def test_paint_filter_search_pick_and_remove(page, live_server):
    ultramarine = PaintFactory(brand=BrandFactory(name='Winsor & Newton'), name='Ultramarine')
    for i in range(20):
        PaintFactory(name=f'Colour {i}')
    FormulaPartFactory(paint=ultramarine, formula=FormulaFactory(pigment=PigmentFactory(name='Bohemian Green')))
    PigmentFactory(name='Plain pigment')

    page.goto(live_server.url + LIST_PATH)
    page.wait_for_load_state('networkidle')
    page.get_by_role('button', name='Show filters').click()
    page.get_by_role('button', name='Paint').click()

    # Typing goes straight into the search box, and the list isn't clipped.
    page.locator('.select2-selection').click()
    playwright_sync.expect(page.locator('.select2-container--open .select2-search__field')).to_be_focused()
    page.keyboard.type('ultra')
    options = page.locator('.select2-results__option')
    assert options.all_inner_texts() == ['Winsor & Newton — Ultramarine']
    assert options.first.is_visible()
    page.keyboard.press('Enter')

    results = page.locator('#listing-results')
    results.get_by_text('1 pigment', exact=True).wait_for()
    assert f'paint={ultramarine.pk}' in page.url
    assert 'Bohemian Green' in results.inner_text()
    assert 'Plain pigment' not in results.inner_text()
    assert page.locator('#drilldown-id_paint').is_visible(), 'picking a paint must not close the filter panel'

    # Removing the active-filter pill resets the dropdown and the list.
    results.get_by_role('button', name='Clear').click()
    results.get_by_text('2 pigments', exact=True).wait_for()
    assert 'paint=' not in page.url
    # (The panel closes when the pill is clicked, so the dropdown is hidden.)
    page.locator('.select2-selection__rendered').get_by_text('Any paint').wait_for(state='attached')

    assert page.js_errors == []
