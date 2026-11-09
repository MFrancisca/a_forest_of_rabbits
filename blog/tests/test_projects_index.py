"""Projects index layout: category columns, the "Other" group, the archive,
and the default category on new project pages."""
import datetime

import pytest
from django.contrib.auth import get_user_model

from blog.factories import CategoryFactory, ProjectPageFactory
from blog.models import DEFAULT_CATEGORY_NAME, Category, ProjectsIndexColumn


pytestmark = pytest.mark.django_db


@pytest.fixture
def other():
    """The default category, seeded by the blog migrations."""
    return Category.objects.get(name=DEFAULT_CATEGORY_NAME)


def _set_columns(index, *categories):
    for order, category in enumerate(categories):
        ProjectsIndexColumn.objects.create(page=index, category=category, sort_order=order)


def _get(client, index):
    response = client.get(index.url)
    assert response.status_code == 200
    return response.context


def _columns(context):
    return [(category.name, list(projects)) for category, projects in context['columns']]


def test_migration_creates_default_category(other):
    assert other.name == 'Other'


def test_projects_are_grouped_into_configured_columns_in_order(client, projects_index):
    armor, clothing = CategoryFactory(name='Armor'), CategoryFactory(name='Clothing')
    _set_columns(projects_index, clothing, armor)
    helmet = ProjectPageFactory(parent=projects_index, categories=[armor])
    cotte = ProjectPageFactory(parent=projects_index, categories=[clothing])

    context = _get(client, projects_index)

    assert _columns(context) == [('Clothing', [cotte]), ('Armor', [helmet])]
    assert context['other_projects'] == []


def test_columns_are_newest_first(client, projects_index):
    armor = CategoryFactory(name='Armor')
    _set_columns(projects_index, armor)
    older = ProjectPageFactory(parent=projects_index, categories=[armor], date=datetime.date(2025, 1, 1))
    newer = ProjectPageFactory(parent=projects_index, categories=[armor], date=datetime.date(2026, 1, 1))

    assert _columns(_get(client, projects_index)) == [('Armor', [newer, older])]


def test_project_in_two_columns_shows_in_both(client, projects_index):
    armor, clothing = CategoryFactory(name='Armor'), CategoryFactory(name='Clothing')
    _set_columns(projects_index, armor, clothing)
    both = ProjectPageFactory(parent=projects_index, categories=[armor, clothing])

    assert _columns(_get(client, projects_index)) == [('Armor', [both]), ('Clothing', [both])]


def test_project_in_no_column_goes_to_other(client, projects_index, other):
    armor, collab = CategoryFactory(name='Armor'), CategoryFactory(name='Collaborations')
    _set_columns(projects_index, armor)
    ProjectPageFactory(parent=projects_index, categories=[armor])
    collab_only = ProjectPageFactory(parent=projects_index, categories=[collab])
    defaulted = ProjectPageFactory(parent=projects_index, categories=[other])
    untagged = ProjectPageFactory(parent=projects_index)

    context = _get(client, projects_index)

    assert set(context['other_projects']) == {collab_only, defaulted, untagged}
    assert b'>Other</h2>' in client.get(projects_index.url).content


def test_other_is_used_as_a_column_when_configured(client, projects_index, other):
    armor = CategoryFactory(name='Armor')
    _set_columns(projects_index, armor, other)
    defaulted = ProjectPageFactory(
        parent=projects_index, categories=[other], date=datetime.date(2026, 1, 1)
    )
    untagged = ProjectPageFactory(parent=projects_index, date=datetime.date(2000, 1, 1))

    context = _get(client, projects_index)

    assert ('Other', [defaulted, untagged]) in _columns(context)
    assert context['other_projects'] == []


def test_empty_columns_are_hidden(client, projects_index):
    armor, clothing = CategoryFactory(name='Armor'), CategoryFactory(name='Clothing')
    _set_columns(projects_index, armor, clothing)
    ProjectPageFactory(parent=projects_index, categories=[armor])

    assert [name for name, _ in _columns(_get(client, projects_index))] == ['Armor']


def test_duplicate_column_is_listed_once(client, projects_index):
    armor = CategoryFactory(name='Armor')
    _set_columns(projects_index, armor, armor)
    ProjectPageFactory(parent=projects_index, categories=[armor])

    assert len(_columns(_get(client, projects_index))) == 1


def test_archived_projects_only_show_in_collapsed_archive(client, projects_index):
    armor, archive = CategoryFactory(name='Armor'), CategoryFactory(name='Archive')
    _set_columns(projects_index, armor, archive)  # archive as a column is ignored
    projects_index.archive_category = archive
    projects_index.save_revision().publish()
    current = ProjectPageFactory(parent=projects_index, categories=[armor])
    old = ProjectPageFactory(parent=projects_index, categories=[armor, archive])

    context = _get(client, projects_index)

    assert _columns(context) == [('Armor', [current])]
    assert context['archive_projects'] == [old]
    assert context['archive_category'] == archive
    content = client.get(projects_index.url).content.decode()
    assert '<details' in content and '<details open' not in content


def test_no_archive_section_without_archived_projects(client, projects_index):
    projects_index.archive_category = CategoryFactory(name='Archive')
    projects_index.save_revision().publish()
    ProjectPageFactory(parent=projects_index)

    context = _get(client, projects_index)
    assert context['archive_category'] is None
    assert b'<details' not in client.get(projects_index.url).content


def test_unconfigured_index_lists_everything_without_headings(client, projects_index, published_project):
    """Before columns are set up in the admin, the page still lists every project."""
    context = _get(client, projects_index)

    assert context['columns'] == []
    assert context['other_projects'] == [published_project]
    assert b'>Other</h2>' not in client.get(projects_index.url).content


def test_draft_and_outside_projects_are_not_listed(client, root_page, projects_index):
    armor = CategoryFactory(name='Armor')
    _set_columns(projects_index, armor)
    ProjectPageFactory(parent=projects_index, categories=[armor], live=False)
    ProjectPageFactory(parent=root_page, slug='classes', categories=[armor])

    context = _get(client, projects_index)
    assert context['columns'] == [] and context['other_projects'] == []


def test_cards_tag_only_non_column_categories(client, projects_index, other):
    armor, collab = CategoryFactory(name='Armor'), CategoryFactory(name='Collaborations')
    _set_columns(projects_index, armor)
    ProjectPageFactory(parent=projects_index, categories=[armor, collab, other])

    (_, [project]), = _get(client, projects_index)['columns']
    assert project.tag_categories == [collab]


def test_archived_cards_keep_their_column_tags(client, projects_index):
    armor, archive = CategoryFactory(name='Armor'), CategoryFactory(name='Archive')
    _set_columns(projects_index, armor)
    projects_index.archive_category = archive
    projects_index.save_revision().publish()
    ProjectPageFactory(parent=projects_index, categories=[armor, archive])

    [project] = _get(client, projects_index)['archive_projects']
    assert project.tag_categories == [armor]


def test_stale_category_query_param_is_ignored(client, projects_index, published_project):
    """Old ?category= links (bookmarks, crawlers) still get the full page."""
    response = client.get(projects_index.url, {'category': 'abc'})
    assert response.status_code == 200
    assert response.context['other_projects'] == [published_project]


def test_column_anchor_ids_match_homepage_links(client, home_page, projects_index):
    armor, unused = CategoryFactory(name='Armor'), CategoryFactory(name='Unused')
    _set_columns(projects_index, armor, unused)
    ProjectPageFactory(parent=projects_index, categories=[armor])

    home = client.get(home_page.url)
    assert home.context['categories'] == [armor]
    assert f'{projects_index.url}#category-{armor.id}' in home.content.decode()
    assert f'id="category-{armor.id}"' in client.get(projects_index.url).content.decode()


def test_homepage_without_projects_index_has_no_quick_links(client, home_page):
    assert client.get(home_page.url).context['categories'] == []


def test_detail_page_hides_default_category_tag(client, projects_index, other):
    armor = CategoryFactory(name='Armor')
    project = ProjectPageFactory(parent=projects_index, categories=[armor, other])

    pills = client.get(project.url).content.decode().count('rounded-full bg-amber-100')
    assert pills == 1
    assert project.display_categories == [armor]


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------

@pytest.fixture
def admin_client(client):
    admin = get_user_model().objects.create_superuser('admin', 'admin@example.com', 'pw')
    client.force_login(admin)
    return client


def _categories_field(response):
    return response.context['form']['categories']


def test_new_project_page_preselects_default_category(admin_client, projects_index, other):
    response = admin_client.get(f'/cms/pages/add/blog/projectpage/{projects_index.pk}/')
    assert response.status_code == 200
    assert [int(v) for v in _categories_field(response).value()] == [other.pk]


def test_existing_project_page_keeps_its_own_categories(admin_client, projects_index, other):
    armor = CategoryFactory(name='Armor')
    page = ProjectPageFactory(parent=projects_index, categories=[armor])
    page.save_revision().publish()

    response = admin_client.get(f'/cms/pages/{page.pk}/edit/')
    assert [int(v) for v in _categories_field(response).value()] == [armor.pk]


def test_no_preselection_when_default_category_was_removed(admin_client, projects_index, other):
    other.delete()
    response = admin_client.get(f'/cms/pages/add/blog/projectpage/{projects_index.pk}/')
    assert not _categories_field(response).value()


def test_index_layout_is_editable_in_admin(admin_client, projects_index):
    from wagtail.test.utils.form_data import inline_formset, nested_form_data
    armor, clothing, archive = (CategoryFactory(name=n) for n in ('Armor', 'Clothing', 'Archive'))
    data = nested_form_data({
        'title': projects_index.title,
        'slug': projects_index.slug,
        'columns': inline_formset([
            {'category': clothing.pk, 'ORDER': 1},
            {'category': armor.pk, 'ORDER': 2},
        ]),
        'archive_category': archive.pk,
        'action-publish': 'action-publish',
    })

    response = admin_client.post(f'/cms/pages/{projects_index.pk}/edit/', data)
    assert response.status_code == 302, response.context['form'].errors if response.context else response

    projects_index.refresh_from_db()
    assert [c.category for c in projects_index.columns.all()] == [clothing, armor]
    assert projects_index.archive_category == archive
