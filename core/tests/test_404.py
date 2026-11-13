"""Custom 404 page with a section-aware variant (issue #16)."""
import re

import pytest
from django.test import override_settings

from core.navigation import section_for

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures('wagtail_site')]


@pytest.fixture(autouse=True)
def production_404s():
    """handler404 only runs with DEBUG off; test settings turn it on."""
    with override_settings(DEBUG=False):
        yield


def _get_404(client, path):
    response = client.get(path)
    assert response.status_code == 404
    assert [t.name for t in response.templates][0] == '404.html'
    return response.content.decode(), response.context


# --- section_for --------------------------------------------------------------------

@pytest.mark.parametrize('path, expected', [
    ('/pigments/9999/', ('/pigments/', 'Pigments', 'pigment')),
    ('/projects/old-slug/', ('/projects/', 'Projects', 'project')),
    ('/classes/x/', ('/classes/', 'Classes', 'class')),
    ('/about/team/', ('/about/', 'About', 'page')),   # no item name → "page"
])
def test_section_for_paths_under_a_section(path, expected):
    section = section_for(path)
    assert (section['href'], section['label'], section['item']) == expected


@pytest.mark.parametrize('path', ['/', '/does-not-exist/', '/classes/', '/pigmentsx/'])
def test_section_for_other_paths_is_none(path):
    """Top-level paths, a section's own page, and look-alike prefixes have no section."""
    assert section_for(path) is None


# --- site-wide page -------------------------------------------------------------------

def test_unknown_top_level_url_gets_the_site_404(client):
    html, context = _get_404(client, '/does-not-exist/')

    assert re.search(r'<title>\s*Page not found — A Forest of Rabbits\s*</title>', html)
    assert re.search(r'<h1[^>]*>Page not found</h1>', html)
    assert context['section'] is None
    assert "There's nothing at this address" in html
    for href in ('/', '/pigments/', '/projects/'):
        assert f'<a href="{href}" class="block h-full' in html
    # Full layout, so visitors can still get around.
    assert '<nav aria-label="Main"' in html and 'Skip to content' in html


# --- section-aware variant --------------------------------------------------------------

@pytest.mark.parametrize('path, item, label, href', [
    ('/pigments/9999/', 'pigment', 'Pigments', '/pigments/'),   # get_object_or_404 miss
    ('/pigments/abc/', 'pigment', 'Pigments', '/pigments/'),    # no URL pattern matches
    ('/projects/old-slug/', 'project', 'Projects', '/projects/'),  # Wagtail page miss
    ('/classes/old-handout/', 'class', 'Classes', '/classes/'),
    ('/about/team/', 'page', 'About', '/about/'),
    ('/blog/old-post/', 'post', 'Blog', '/blog/'),
])
def test_missing_page_under_a_section_points_back_to_it(client, path, item, label, href):
    html, context = _get_404(client, path)

    assert context['section']['href'] == href
    assert f"This {item} doesn't exist." in html
    assert re.search(rf'<a href="{href}"\s+class="inline-flex[^"]*">\s*Go to {label}', html)


def test_no_nav_link_is_marked_current_on_a_404(client):
    """A 404 isn't a real page in the section, so nothing is announced as current."""
    html, _ = _get_404(client, '/pigments/9999/')
    assert 'aria-current' not in html.split('<main', 1)[0]


def test_real_pages_still_mark_their_section(client):
    from pigments.factories import PigmentFactory
    pigment = PigmentFactory()
    html = client.get(f'/pigments/{pigment.pk}/').content.decode()
    assert 'href="/pigments/" aria-current="true"' in html
