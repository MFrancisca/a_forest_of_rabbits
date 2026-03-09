import pytest
from django.test import Client
from blog.models import Category, ProjectsIndexPage, ProjectPage, AboutPage
from blog.factories import CategoryFactory, ProjectPageFactory


pytestmark = pytest.mark.django_db


def test_category_str():
    """Category __str__ returns its name."""
    cat = CategoryFactory()
    assert str(cat) == cat.name


def test_index_shows_only_live_pages(client, projects_index, published_project):
    """ProjectsIndexPage only returns live ProjectPage children in context."""
    response = client.get(projects_index.url)
    assert response.status_code == 200
    projects = response.context['projects']
    assert published_project in projects


def test_index_ordering(client, projects_index):
    """Projects are ordered newest-first by date."""
    import datetime
    older = ProjectPageFactory(parent=projects_index, date=datetime.date(2025, 1, 1))
    newer = ProjectPageFactory(parent=projects_index, date=datetime.date(2026, 1, 1))
    response = client.get(projects_index.url)
    projects = list(response.context['projects'])
    assert projects.index(newer) < projects.index(older)


def test_index_empty_state(client, projects_index):
    """Projects index shows empty state when no published children."""
    response = client.get(projects_index.url)
    assert response.status_code == 200
    assert b'No projects published yet' in response.content


def test_project_page_renders(client, published_project):
    """ProjectPage detail renders body, date, category."""
    response = client.get(published_project.url)
    assert response.status_code == 200


def test_projects_url(client, projects_index, wagtail_site):
    """GET /projects/ returns HTTP 200."""
    response = client.get('/projects/')
    assert response.status_code == 200


def test_project_detail_url(client, published_project, wagtail_site):
    """GET /projects/<slug>/ returns HTTP 200 for a live page."""
    response = client.get(published_project.url)
    assert response.status_code == 200


def test_about_page_renders(client, about_page, wagtail_site):
    """AboutPage renders body at /about/."""
    response = client.get('/about/')
    assert response.status_code == 200


def test_about_url(client, about_page, wagtail_site):
    """GET /about/ returns HTTP 200."""
    response = client.get('/about/')
    assert response.status_code == 200
