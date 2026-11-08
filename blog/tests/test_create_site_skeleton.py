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


@pytest.mark.django_db
def test_no_root_page_reports_error_and_creates_nothing():
    from io import StringIO

    Site.objects.all().delete()
    Page.objects.filter(depth=1).delete()
    err = StringIO()

    call_command('create_site_skeleton', stderr=err)

    assert 'No root page found' in err.getvalue()
    assert not HomePage.objects.exists()


@pytest.mark.django_db
def test_moves_index_and_about_under_homepage():
    """Pages created as siblings of HomePage (the old layout) get re-parented."""
    from blog.factories import AboutPageFactory, ProjectsIndexPageFactory

    root = Page.objects.get(depth=1)
    index = ProjectsIndexPageFactory(parent=root, slug='projects')
    about = AboutPageFactory(parent=root, slug='about')

    call_command('create_site_skeleton')

    home = HomePage.objects.get()
    assert ProjectsIndexPage.objects.get(pk=index.pk).get_parent().id == home.id
    assert AboutPage.objects.get(pk=about.pk).get_parent().id == home.id
    assert ProjectsIndexPage.objects.count() == 1
    assert AboutPage.objects.count() == 1


@pytest.mark.django_db
def test_moves_classes_out_of_projects_and_clears_categories():
    from blog.factories import CategoryFactory, ProjectPageFactory
    from blog.models import ProjectPage

    call_command('create_site_skeleton')
    index = ProjectsIndexPage.objects.get()
    classes = ProjectPageFactory(parent=index, slug='classes', categories=[CategoryFactory()])
    classes.save_revision().publish()

    call_command('create_site_skeleton')

    classes = ProjectPage.objects.get(pk=classes.pk)
    assert classes.get_parent().id == HomePage.objects.get().id
    assert not classes.categories.exists()
    # Published from a revision — the cleared categories must survive that.
    assert not classes.get_latest_revision_as_object().categories.exists()
    assert Client().get('/classes/').status_code == 200
