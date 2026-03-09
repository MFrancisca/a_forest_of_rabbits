import pytest
from wagtail.models import Page, Site
from blog.factories import (
    ProjectsIndexPageFactory,
    ProjectPageFactory,
    AboutPageFactory,
    CategoryFactory,
)


@pytest.fixture
def root_page(db):
    """Return the Wagtail root page created by initial migration."""
    return Page.objects.filter(depth=1).first()


@pytest.fixture
def wagtail_site(db, root_page):
    """Return or create the default Wagtail site pointing to root."""
    site, _ = Site.objects.get_or_create(
        is_default_site=True,
        defaults={'hostname': 'localhost', 'port': 80, 'root_page': root_page},
    )
    return site


@pytest.fixture
def projects_index(db, root_page, wagtail_site):
    return ProjectsIndexPageFactory(parent=root_page, slug='projects')


@pytest.fixture
def about_page(db, root_page, wagtail_site):
    return AboutPageFactory(parent=root_page, slug='about')


@pytest.fixture
def published_project(db, projects_index):
    return ProjectPageFactory(parent=projects_index, live=True)
