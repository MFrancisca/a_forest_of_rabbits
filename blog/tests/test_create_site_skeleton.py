import pytest
from django.core.management import call_command
from django.test import Client
from wagtail.models import Page, Site

from blog.management.commands.create_site_skeleton import DEFAULT_WAGTAIL_PLACEHOLDER_TITLE
from blog.models import AboutPage, HomePage, ProjectsIndexPage


@pytest.mark.django_db
def test_fresh_database_ends_with_routable_site():
    """On a freshly migrated DB (placeholder page + default Site pointing at it),
    the skeleton must leave a default Site rooted at HomePage. Site.root_page is
    on_delete=CASCADE, so deleting the placeholder first used to delete the Site."""
    assert Page.objects.filter(title=DEFAULT_WAGTAIL_PLACEHOLDER_TITLE).exists()

    call_command('create_site_skeleton')

    home = HomePage.objects.get()
    site = Site.objects.get(is_default_site=True)
    assert site.root_page_id == home.id
    assert home.slug == 'home'
    assert not Page.objects.filter(title=DEFAULT_WAGTAIL_PLACEHOLDER_TITLE).exists()
    assert ProjectsIndexPage.objects.get().get_parent().id == home.id
    assert AboutPage.objects.get().get_parent().id == home.id

    client = Client()
    assert client.get('/').status_code == 200
    assert client.get('/projects/').status_code == 200
    assert client.get('/about/').status_code == 200


@pytest.mark.django_db
def test_recreates_missing_default_site():
    """Recovers a DB already broken by the old behaviour: HomePage exists but no Site."""
    call_command('create_site_skeleton')
    Site.objects.all().delete()

    call_command('create_site_skeleton')

    site = Site.objects.get(is_default_site=True)
    assert site.root_page_id == HomePage.objects.get().id
    assert Client().get('/').status_code == 200


@pytest.mark.django_db
def test_is_idempotent():
    call_command('create_site_skeleton')
    call_command('create_site_skeleton')

    assert HomePage.objects.count() == 1
    assert Site.objects.filter(is_default_site=True).count() == 1
