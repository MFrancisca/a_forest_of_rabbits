"""Blog-only fixtures. root_page, wagtail_site and projects_index live in the root conftest.py."""
import pytest
from blog.factories import (
    ProjectPageFactory,
    AboutPageFactory,
    CategoryFactory,
    HomePageFactory,
)


@pytest.fixture
def about_page(db, root_page, wagtail_site):
    return AboutPageFactory(parent=root_page, slug='about')


@pytest.fixture
def published_project(db, projects_index):
    return ProjectPageFactory(parent=projects_index, live=True)


@pytest.fixture
def home_page(db, root_page, wagtail_site):
    # Wagtail's own initial migration seeds a default page at slug='home' under
    # root — don't collide with it; let the factory assign a unique slug.
    return HomePageFactory(parent=root_page)
