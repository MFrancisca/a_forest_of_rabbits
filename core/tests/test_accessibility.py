"""Site-wide accessibility structure: skip link, nav state, heading outline (issue #10)."""
import re
from pathlib import Path

import pytest
from django.conf import settings
from django.template import Context, Template
from django.test import RequestFactory
from django.urls import reverse
from wagtail.models import Page, Site

from blog.factories import CategoryFactory, HomePageFactory, ProjectPageFactory, ProjectsIndexPageFactory
from pigments.factories import PigmentFactory


@pytest.fixture
def home(db):
    home = HomePageFactory(parent=Page.objects.get(depth=1), title='A Forest of Rabbits')
    Site.objects.update_or_create(
        is_default_site=True, defaults={'hostname': 'localhost', 'port': 80, 'root_page': home},
    )
    return home


@pytest.fixture
def index(home):
    return ProjectsIndexPageFactory(parent=home, title='Projects', slug='projects')


def _html(response):
    assert response.status_code == 200
    return response.content.decode()


def _current(html):
    """{href: aria-current value} for every nav link that has one."""
    return dict(re.findall(r'<a href="([^"]+)" aria-current="(page|true)"', html))


def _headings(html):
    """Heading levels in document order."""
    return [int(level) for level in re.findall(r'<h([1-6])\b', html)]


# --- skip link ---------------------------------------------------------------

def test_skip_link_is_first_focusable_and_targets_main(client, home):
    html = _html(client.get('/'))
    body = html.split('<body', 1)[1]
    first_link = re.search(r'<a\b[^>]*>', body).group(0)
    assert 'href="#content"' in first_link
    assert re.search(r'<main id="content" tabindex="-1"', html)


# --- nav ---------------------------------------------------------------------

def test_nav_is_labelled_and_menu_button_exposes_state(client, home):
    html = _html(client.get('/'))
    assert '<nav aria-label="Main"' in html
    assert 'aria-controls="mobile-menu"' in html
    assert 'aria-expanded="false"' in html
    assert ':aria-expanded="open.toString()"' in html
    assert 'id="mobile-menu"' in html


def test_home_link_is_current_only_on_home(client, home, index):
    assert _current(_html(client.get('/'))) == {'/': 'page'}
    assert '/' not in _current(_html(client.get(index.url)))


def test_section_page_is_current_page_in_both_menus(client, index):
    html = _html(client.get(index.url))
    assert _current(html) == {'/projects/': 'page'}
    assert html.count('href="/projects/" aria-current="page"') == 2  # desktop + mobile


def test_page_inside_section_marks_section_true(client, index):
    project = ProjectPageFactory(parent=index, title='Gilded Armor')
    assert _current(_html(client.get(project.url))) == {'/projects/': 'true'}


@pytest.mark.django_db
def test_pigment_pages_mark_pigments_link(client):
    pigment = PigmentFactory(with_formula=True)
    assert _current(_html(client.get(reverse('pigments:list')))) == {'/pigments/': 'page'}
    assert _current(_html(client.get(reverse('pigments:detail', args=[pigment.pk])))) == {'/pigments/': 'true'}


def test_aria_current_tag_without_request_renders_nothing():
    template = Template("{% load nav_tags %}{% aria_current '/' %}")
    assert template.render(Context({})) == ''


def test_aria_current_tag_ignores_unrelated_prefixes():
    request = RequestFactory().get('/pigmentsextra/')
    template = Template("{% load nav_tags %}{% aria_current '/pigments/' %}")
    assert template.render(Context({'request': request})) == ''


# --- heading outline ----------------------------------------------------------

def _assert_no_skips(levels):
    for previous, current in zip(levels, levels[1:]):
        assert current <= previous + 1, f'heading jumps from h{previous} to h{current}: {levels}'


def test_projects_without_columns_have_h2_above_cards(client, index):
    ProjectPageFactory(parent=index)
    html = _html(client.get(index.url))
    assert '<h2 class="sr-only">All projects</h2>' in html
    _assert_no_skips(_headings(html))


def test_archive_title_is_h2_above_archived_cards(client, index):
    archive = CategoryFactory(name='Archive')
    index.archive_category = archive
    index.save()
    ProjectPageFactory(parent=index, categories=[archive])

    html = _html(client.get(index.url))
    summary = html.split('<summary', 1)[1].split('</summary>', 1)[0]
    assert re.search(r'<h2\b[^>]*>Archive</h2>', summary)
    _assert_no_skips(_headings(html))


# --- contrast -----------------------------------------------------------------

@pytest.mark.django_db
def test_no_low_contrast_stone_400_text(client, home):
    pigment = PigmentFactory(with_formula=True)
    for url in ('/', reverse('pigments:list'), reverse('pigments:detail', args=[pigment.pk])):
        assert 'text-stone-400' not in _html(client.get(url)), url


def test_no_template_uses_low_contrast_stone_400_text():
    """Static check, so conditional branches the rendered pages above miss are covered too."""
    offenders = [
        str(path) for path in Path(settings.BASE_DIR).glob('*/templates/**/*.html')
        if 'text-stone-400' in path.read_text()
    ]
    assert offenders == []
