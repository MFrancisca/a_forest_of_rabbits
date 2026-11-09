# conftest.py — root conftest
# pytest-django reads DJANGO_SETTINGS_MODULE from pyproject.toml [tool.pytest.ini_options]
"""Fixtures shared across apps: a routable Wagtail site and a Projects index."""
import pytest
from wagtail.models import Page, Site

from blog.factories import ProjectsIndexPageFactory


@pytest.fixture
def root_page(db):
    """Return the Wagtail root page created by initial migration."""
    return Page.objects.filter(depth=1).first()


@pytest.fixture
def wagtail_site(db, root_page):
    """Return or create the default Wagtail site pointing to root.

    Wagtail's initial migration creates a default site pointing to a depth=2
    homepage.  We need it to point to root_page (depth=1) so that pages added
    as children of root_page are reachable at their slug URLs.
    """
    site, created = Site.objects.get_or_create(
        is_default_site=True,
        defaults={'hostname': 'localhost', 'port': 80, 'root_page': root_page},
    )
    if not created and site.root_page_id != root_page.pk:
        # The initial migration already created a default site with a different
        # root_page — update it so our test pages are routable.
        site.root_page = root_page
        site.save()
    return site


@pytest.fixture
def projects_index(db, root_page, wagtail_site):
    return ProjectsIndexPageFactory(parent=root_page, slug='projects')
