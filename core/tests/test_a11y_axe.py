"""Automated accessibility checks (issue #14): axe-core in headless Chromium.

Every key page, plus the interactive states a static load can't show (open filter
dropdown, open lightbox, expanded disclosures, mobile menu), in both themes, against
WCAG 2.0/2.1/2.2 A and AA.

Opt-in because it needs a browser: skipped by the default run (addopts has
`-m "not a11y"`). Run it with

    .venv/bin/pytest -m a11y --no-cov

(first time only: `.venv/bin/playwright install chromium`).

Known exceptions go in KNOWN_EXCEPTIONS with a reason, instead of turning rules off.
"""
import os

import pytest
import wagtail_factories
from django.test import override_settings
from wagtail.models import Page, Site

from blog.factories import (
    AboutPageFactory,
    CategoryFactory,
    HomePageFactory,
    ProjectPageFactory,
    ProjectsIndexPageFactory,
)
from blog.models import ProjectsIndexColumn
from pigments.factories import (
    FormulaFactory,
    FormulaPartFactory,
    ManuscriptFactory,
    PaintFactory,
    PigmentFactory,
    PigmentImageFactory,
    PigmentManuscriptFactory,
    SourceFactory,
)

pytestmark = [pytest.mark.a11y, pytest.mark.django_db(transaction=True, serialized_rollback=True)]

playwright_sync = pytest.importorskip('playwright.sync_api')
axe_sync = pytest.importorskip('axe_playwright_python.sync_playwright')

# wcag22a has no rules in axe 4.12 (WCAG 2.2's only new automatable check, target-size, is AA);
# listed so a future axe version that adds one is picked up.
WCAG_TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22a', 'wcag22aa']

# {rule id: reason}. Empty on purpose: add an entry only with a written justification.
KNOWN_EXCEPTIONS = {}

THEMES = ['light', 'dark']


# --- browser and content ------------------------------------------------------------------

@pytest.fixture(scope='module')
def browser():
    # Playwright's sync API runs an event loop; Django's ORM guard would refuse queries
    # from it. Lift the guard only while the browser is up, not for the whole session.
    previous = os.environ.get('DJANGO_ALLOW_ASYNC_UNSAFE')
    os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
    try:
        with playwright_sync.sync_playwright() as p:
            try:
                chromium = p.chromium.launch()
            except playwright_sync.Error as exc:
                if "Executable doesn't exist" not in str(exc):
                    raise
                pytest.skip('Chromium not installed; run .venv/bin/playwright install chromium')
            yield chromium
            chromium.close()
    finally:
        if previous is None:
            os.environ.pop('DJANGO_ALLOW_ASYNC_UNSAFE', None)
        else:
            os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = previous


@pytest.fixture
def site(live_server):
    """A small but complete site: every widget the templates have, with real content."""
    home = HomePageFactory(parent=Page.objects.get(depth=1), title='A Forest of Rabbits')
    Site.objects.update_or_create(
        is_default_site=True, defaults={'hostname': 'localhost', 'port': 80, 'root_page': home},
    )
    AboutPageFactory(parent=home, slug='about', body='<p>About this <a href="/pigments/">site</a>.</p>')

    index = ProjectsIndexPageFactory(parent=home, slug='projects')
    calligraphy, armor, archive = (CategoryFactory(name=n) for n in ('Calligraphy', 'Armor', 'Archive'))
    for order, category in enumerate((calligraphy, armor)):
        ProjectsIndexColumn.objects.create(page=index, category=category, sort_order=order)
    index.archive_category = archive
    index.save()
    images = [wagtail_factories.ImageFactory(title=f'Photo {n}') for n in range(3)]
    project = ProjectPageFactory(
        parent=index, slug='gilded-scroll', title='Gilded Scroll', categories=[calligraphy],
        technical_info=[{'type': 'freeform', 'value': '<p>Gouache on vellum.</p>'}],
        body=[
            {'type': 'rich_text', 'value': {'title': 'Process', 'text': '<p>Sketch, ink, gild.</p>'}},
            {'type': 'image', 'value': {'title': '', 'image': images[0].pk, 'caption': 'Detail', 'alignment': 'right',
                                        'text': '<p>The gilding up close.</p>'}},
            {'type': 'carousel', 'value': {'title': 'Angles', 'images': [
                {'image': image.pk, 'caption': f'Angle {n}'} for n, image in enumerate(images)]}},
        ],
    )
    ProjectPageFactory(parent=index, title='Old Helmet', categories=[armor, archive])
    ProjectPageFactory(parent=index, title='Brigandine', categories=[armor])

    source = SourceFactory(authors='Bicchieri, M.', year=2014, url='https://example.org/study', doi='')
    pigment = PigmentFactory(with_formula=False, name='Azurite')
    for _ in range(2):
        formula = FormulaFactory(pigment=pigment, notes='Grind with gum arabic.')
        FormulaPartFactory(formula=formula, parts=2, paint=PaintFactory(name='Ultramarine', abbreviation='U'))
        FormulaPartFactory(formula=formula, parts=None, is_trace=True, paint=PaintFactory(name='Lead White', abbreviation='W'))
    for order in range(3):
        PigmentImageFactory(pigment=pigment, image=wagtail_factories.ImageFactory(), sort_order=order,
                            alt_text=f'Azurite sample {order}')
    PigmentManuscriptFactory(pigment=pigment, manuscript=ManuscriptFactory(name='Book of Hours', date_start=1400, date_end=1450),
                             source=source, page_reference='f. 3r', notes='Faded on the margins.')
    pigment.sources.add(SourceFactory(title='General pigment reference'))
    pigment.save()
    PigmentFactory(with_formula=True, name='Vermilion')

    return {'url': live_server.url, 'project': project.url, 'pigment': f'/pigments/{pigment.pk}/',
            'color': pigment.color_family_id}


def _open(browser, site, path, theme, width=1280):
    page = browser.new_page(color_scheme=theme, viewport={'width': width, 'height': 900})
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(site['url'] + path)
    page.wait_for_load_state('networkidle')
    page.js_errors = errors
    return page


def _summary(node):
    lines = (node.get('failureSummary') or '').strip().splitlines()
    return lines[-1].strip() if lines else ''


def _check(page, label):
    """Run axe and fail with a readable list of violations. Always closes the page."""
    try:
        _assert_accessible(page, label)
    finally:
        page.close()


def _assert_accessible(page, label):
    results = axe_sync.Axe().run(page, options={'runOnly': {'type': 'tag', 'values': WCAG_TAGS},
                                               'resultTypes': ['violations']})
    violations = [v for v in results.response['violations'] if v['id'] not in KNOWN_EXCEPTIONS]
    report = '\n'.join(
        f"  [{v['impact']}] {v['id']}: {v['help']}\n"
        + '\n'.join(f"      {', '.join(map(str, n['target']))}: {_summary(n)}"
                    for n in v['nodes'][:5])
        for v in violations
    )
    assert not violations, f'{label}: {len(violations)} axe violation(s)\n{report}'
    assert not page.js_errors, f'{label}: JavaScript errors {page.js_errors}'


# --- pages ----------------------------------------------------------------------------------

PAGES = {
    'home': lambda s: '/',
    'about': lambda s: '/about/',
    'projects index': lambda s: '/projects/',
    'project page': lambda s: s['project'],
    'pigment list': lambda s: '/pigments/',
    'pigment list, filtered': lambda s: f"/pigments/?color={s['color']}",
    'pigment detail': lambda s: s['pigment'],
}


@pytest.mark.parametrize('theme', THEMES)
@pytest.mark.parametrize('name', PAGES)
def test_page(browser, site, name, theme):
    page = _open(browser, site, PAGES[name](site), theme)
    _check(page, f'{name} ({theme})')


@pytest.mark.parametrize('theme', THEMES)
def test_404_page(browser, site, theme):
    with override_settings(DEBUG=False):
        page = _open(browser, site, '/pigments/99999/', theme)
        _check(page, f'404 ({theme})')


# --- interactive states ------------------------------------------------------------------------

@pytest.mark.parametrize('theme', THEMES)
def test_filter_dropdown_open(browser, site, theme):
    # axe reports the result count as "incomplete" (not a violation) here: the open panel
    # covers it, so its background can't be measured. With the panel closed it passes.
    page = _open(browser, site, '/pigments/', theme)
    page.locator('button[aria-controls="filter-color"]').click()
    page.locator('#filter-color').wait_for(state='visible')
    _check(page, f'filter dropdown open ({theme})')


@pytest.mark.parametrize('theme', THEMES)
def test_lightbox_open(browser, site, theme):
    page = _open(browser, site, site['pigment'], theme)
    page.get_by_role('button', name='Enlarge image: Azurite sample 0').click()
    page.locator('dialog[open]').wait_for()
    _check(page, f'lightbox open ({theme})')


@pytest.mark.parametrize('theme', THEMES)
def test_disclosures_and_table_notes_open(browser, site, theme):
    page = _open(browser, site, site['pigment'], theme)
    page.locator('#formula-panel-0 summary').click()
    page.get_by_role('button', name='(notes)').click()
    page.get_by_text('Faded on the margins.').wait_for(state='visible')
    _check(page, f'pigment disclosures open ({theme})')

    page = _open(browser, site, site['project'], theme)
    page.get_by_text('Technical Information').click()
    page.get_by_text('Gouache on vellum.').wait_for(state='visible')
    _check(page, f'technical information open ({theme})')


@pytest.mark.parametrize('theme', THEMES)
def test_mobile_menu_open(browser, site, theme):
    page = _open(browser, site, '/', theme, width=390)
    page.get_by_role('button', name='Toggle navigation menu').click()
    page.locator('#mobile-menu').wait_for(state='visible')
    _check(page, f'mobile menu open ({theme})')
