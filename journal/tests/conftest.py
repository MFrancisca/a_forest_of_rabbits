"""Journal fixtures. root_page, wagtail_site and projects_index live in the root conftest.py."""
import pytest

from journal.factories import BlogIndexPageFactory
from journal.models import PIGMENTS_TAG_SLUG, Tag


@pytest.fixture
def blog_index(db, root_page, wagtail_site):
    # Under the test site's root, so it's served at /blog/ (in production it sits under HomePage).
    return BlogIndexPageFactory(parent=root_page)


@pytest.fixture
def pigments_tag(db):
    return Tag.objects.get(slug=PIGMENTS_TAG_SLUG)
