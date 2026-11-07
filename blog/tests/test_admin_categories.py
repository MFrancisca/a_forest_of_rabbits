import pytest
from django.contrib.auth import get_user_model
from wagtail.test.utils.form_data import nested_form_data, rich_text, streamfield

from blog.factories import CategoryFactory, ProjectPageFactory
from blog.models import ProjectPage


def _edit_form_data(page, categories):
    data = nested_form_data({
        'title': page.title,
        'slug': page.slug,
        'date': page.date.isoformat(),
        'excerpt': page.excerpt,
        'body': streamfield([
            ('rich_text', {'title': '', 'text': rich_text('<p>Body</p>')}),
        ]),
        'technical_info': streamfield([]),
        'action-publish': 'action-publish',
    })
    # Added after flattening — nested_form_data would turn a list into
    # categories-0, categories-1, ... instead of a multi-value field.
    data['categories'] = [c.pk for c in categories]
    return data


@pytest.mark.django_db
def test_changing_categories_in_admin_is_preserved_on_publish(client, projects_index):
    """Regression: a plain ManyToManyField isn't stored in Wagtail revisions,
    so publishing from the admin silently reverted category changes."""
    scrolls = CategoryFactory(name='Scrolls')
    calligraphy = CategoryFactory(name='Calligraphy and Illumination')
    page = ProjectPageFactory(parent=projects_index, categories=[scrolls])
    page.save_revision().publish()

    admin = get_user_model().objects.create_superuser('admin', 'admin@example.com', 'pw')
    client.force_login(admin)
    response = client.post(f'/cms/pages/{page.pk}/edit/', _edit_form_data(page, [calligraphy]))
    assert response.status_code == 302, response.context['form'].errors if response.context else response

    page = ProjectPage.objects.get(pk=page.pk)
    assert list(page.categories.all()) == [calligraphy]
    assert list(page.get_latest_revision_as_object().categories.all()) == [calligraphy]


@pytest.mark.django_db
def test_revisions_saved_before_the_fix_still_show_db_categories(projects_index):
    """Revisions created while categories was a plain M2M have no 'categories'
    key; loading them (as the admin edit view does) must fall back to the DB."""
    scrolls = CategoryFactory(name='Scrolls')
    page = ProjectPageFactory(parent=projects_index, categories=[scrolls])
    revision = page.save_revision()
    revision.content.pop('categories', None)
    revision.save()

    assert list(revision.as_object().categories.all()) == [scrolls]
