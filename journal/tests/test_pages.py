"""The blog index (/blog/), post pages, and "Updates on this project" on project pages."""
import datetime

import pytest
import wagtail_factories
from django.core.cache import cache

from blog.factories import ProjectPageFactory
from journal.factories import BlogPostPageFactory, TagFactory

pytestmark = pytest.mark.django_db


def _post(blog_index, **kwargs):
    kwargs.setdefault('live', True)
    return BlogPostPageFactory(parent=blog_index, **kwargs)


def _get(client, url):
    response = client.get(url)
    assert response.status_code == 200
    return response.content.decode()


# --- Blog index -----------------------------------------------------------

def test_index_newest_first(client, blog_index):
    for day, title in [(1, 'First'), (3, 'Third'), (2, 'Second')]:
        _post(blog_index, title=title, date=datetime.date(2026, 1, day))
    html = _get(client, '/blog/')
    assert html.index('Third') < html.index('Second') < html.index('First')


def test_index_excludes_drafts(client, blog_index):
    _post(blog_index, title='Published note')
    _post(blog_index, title='Unfinished draft', live=False)
    html = _get(client, '/blog/')
    assert 'Published note' in html
    assert 'Unfinished draft' not in html


def test_index_filters_by_tag(client, blog_index, pigments_tag):
    _post(blog_index, title='About vermilion', tags=[pigments_tag])
    _post(blog_index, title='About bookbinding')
    html = _get(client, '/blog/?tag=pigments')
    assert 'About vermilion' in html
    assert 'About bookbinding' not in html
    assert 'href="/blog/?tag=pigments" aria-current="page"' in html


def test_index_unknown_tag(client, blog_index):
    _post(blog_index, title='A note')
    html = _get(client, '/blog/?tag=nope')
    assert 'No posts tagged' in html
    assert 'A note' not in html


def test_index_tag_links_only_in_use(client, blog_index, pigments_tag):
    TagFactory(name='Never used')
    _post(blog_index, tags=[pigments_tag])
    html = _get(client, '/blog/')
    assert 'Never used' not in html
    assert 'href="/blog/?tag=pigments"' in html


def test_index_tag_links_ignore_draft_posts(client, blog_index):
    tag = TagFactory(name='Only on drafts')
    _post(blog_index, tags=[tag], live=False)
    assert 'Only on drafts' not in _get(client, '/blog/')


def test_index_paginates(client, blog_index):
    for day in range(1, 12):
        _post(blog_index, title=f'Note {day:02}', date=datetime.date(2026, 1, day))
    page1 = _get(client, '/blog/')
    page2 = _get(client, '/blog/?page=2')
    assert page1.count('data-post-item') == 10
    assert page2.count('data-post-item') == 1
    assert 'Note 01' in page2
    assert 'href="?page=2"' in page1


def test_index_pagination_keeps_tag(client, blog_index, pigments_tag):
    for day in range(1, 12):
        _post(blog_index, date=datetime.date(2026, 1, day), tags=[pigments_tag])
    assert 'href="?tag=pigments&amp;page=2"' in _get(client, '/blog/?tag=pigments')


@pytest.mark.parametrize('page', ['abc', '99', '0'])
def test_index_bad_page_numbers(client, blog_index, page):
    _post(blog_index, title='Only note')
    assert 'Only note' in _get(client, f'/blog/?page={page}')


def test_index_shows_display_summary(client, blog_index):
    _post(blog_index, body=[{'type': 'rich_text', 'value': {'title': '', 'text': '<p>Opening of the body</p>'}}])
    assert 'Opening of the body' in _get(client, '/blog/')


# --- Post page ------------------------------------------------------------

def test_post_page_shows_tags_and_live_projects(client, blog_index, projects_index, pigments_tag):
    live = ProjectPageFactory(parent=projects_index, live=True, title='Live project')
    draft = ProjectPageFactory(parent=projects_index, live=False, title='Hidden project')
    post = _post(blog_index, tags=[pigments_tag], related_projects=[live, draft],
                 body=[{'type': 'rich_text', 'value': {'title': 'Notes', 'text': '<p>Post text</p>'}}])
    html = _get(client, post.url)
    assert 'Post text' in html
    assert f'href="{live.url}"' in html
    assert 'Hidden project' not in html
    assert 'href="/blog/?tag=pigments"' in html


def test_post_page_without_projects_has_no_related_section(client, blog_index):
    post = _post(blog_index)
    assert 'Related project' not in _get(client, post.url)


def test_post_page_skips_missing_cover_file(client, blog_index):
    cache.clear()  # Wagtail caches renditions by image pk, and pks are reused between tests.
    image = wagtail_factories.ImageFactory()
    image.file.storage.delete(image.file.name)
    post = _post(blog_index, cover_image=image)
    html = _get(client, post.url)
    assert 'not-found' not in html
    assert 'lightbox' in html  # page rendered


# --- Project page ---------------------------------------------------------

def test_project_lists_linked_live_posts(client, blog_index, projects_index):
    project = ProjectPageFactory(parent=projects_index, live=True)
    _post(blog_index, title='Older update', date=datetime.date(2026, 1, 1), related_projects=[project])
    _post(blog_index, title='Newer update', date=datetime.date(2026, 2, 1), related_projects=[project])
    _post(blog_index, title='Draft update', live=False, related_projects=[project])
    _post(blog_index, title='Unrelated post')
    html = _get(client, project.url)
    assert 'Updates on this project' in html
    assert html.index('Newer update') < html.index('Older update')
    assert 'Draft update' not in html
    assert 'Unrelated post' not in html


def test_project_without_posts_has_no_updates_section(client, projects_index):
    project = ProjectPageFactory(parent=projects_index, live=True)
    assert 'Updates on this project' not in _get(client, project.url)


# --- Navigation -----------------------------------------------------------

def test_nav_has_blog_link_in_order():
    from core.navigation import NAV_LINKS
    assert [label for _, label in NAV_LINKS] == ['Home', 'Pigments', 'Projects', 'Blog', 'Classes', 'About']
    assert ('/blog/', 'Blog') in NAV_LINKS


def test_blog_nav_link_is_current(client, blog_index):
    post = _post(blog_index)
    assert _get(client, '/blog/').count('href="/blog/" aria-current="page"') == 2  # desktop + mobile
    assert 'href="/blog/" aria-current="true"' in _get(client, post.url)


def test_index_known_tag_without_live_posts(client, blog_index):
    tag = TagFactory(name='Only drafts')
    _post(blog_index, tags=[tag], live=False)
    html = _get(client, f'/blog/?tag={tag.slug}')
    assert 'No posts tagged “Only drafts”' in html
