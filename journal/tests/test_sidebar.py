"""The "Latest pigment notes" sidebar on the pigment list and detail pages."""
import datetime

import pytest
from django.urls import reverse

from journal.factories import BlogPostPageFactory, TagFactory
from pigments.factories import PigmentFactory

pytestmark = pytest.mark.django_db

HEADING = 'Latest pigment notes'


@pytest.fixture
def pigment():
    return PigmentFactory(with_formula=True)


def _post(blog_index, title, tags, day=1, live=True):
    return BlogPostPageFactory(parent=blog_index, title=title, tags=tags, live=live,
                               date=datetime.date(2026, 1, day))


def _list(client, **headers):
    return client.get(reverse('pigments:list'), **headers).content.decode()


def _detail(client, pigment):
    return client.get(reverse('pigments:detail', kwargs={'pk': pigment.pk})).content.decode()


def test_sidebar_on_list_and_detail(client, blog_index, pigments_tag, pigment):
    _post(blog_index, 'Grinding lapis', [pigments_tag])
    for html in (_list(client), _detail(client, pigment)):
        assert HEADING in html
        assert 'Grinding lapis' in html


def test_sidebar_only_pigments_posts_max_three(client, blog_index, pigments_tag):
    for day in range(1, 5):
        _post(blog_index, f'Pigment note {day}', [pigments_tag], day=day)
    _post(blog_index, 'Bookbinding note', [TagFactory()], day=9)
    _post(blog_index, 'Draft pigment note', [pigments_tag], day=10, live=False)
    html = _list(client)
    assert html.index('Pigment note 4') < html.index('Pigment note 3') < html.index('Pigment note 2')
    assert 'Pigment note 1' not in html
    assert 'Bookbinding note' not in html
    assert 'Draft pigment note' not in html


def test_sidebar_absent_without_posts(client, blog_index, pigment):
    assert HEADING not in _list(client)
    assert HEADING not in _detail(client, pigment)


def test_sidebar_absent_when_tag_deleted(client, blog_index, pigments_tag):
    _post(blog_index, 'Orphaned note', [pigments_tag])
    pigments_tag.delete()
    assert HEADING not in _list(client)


def test_sidebar_survives_tag_rename(client, blog_index, pigments_tag):
    _post(blog_index, 'Renamed-tag note', [pigments_tag])
    pigments_tag.name = 'Pigment research'
    pigments_tag.save()
    assert 'Renamed-tag note' in _list(client)


def test_hide_control_only_on_detail(client, blog_index, pigments_tag, pigment):
    _post(blog_index, 'A note', [pigments_tag])
    detail = _detail(client, pigment)
    assert 'pigmentNotesHidden' in detail
    assert 'aria-controls="pigment-notes-list"' in detail
    assert 'pigmentNotesHidden' not in _list(client)


def test_htmx_partial_has_no_sidebar(client, blog_index, pigments_tag):
    _post(blog_index, 'A note', [pigments_tag])
    assert HEADING not in _list(client, HTTP_HX_REQUEST='true')


def test_see_all_link(client, blog_index, pigments_tag):
    _post(blog_index, 'A note', [pigments_tag])
    assert 'href="/blog/?tag=pigments"' in _list(client)
