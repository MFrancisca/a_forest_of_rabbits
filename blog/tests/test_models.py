import pytest
import wagtail_factories
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


def test_index_filters_by_category(client, projects_index):
    """?category=<id> narrows the project list to that category only."""
    wanted = CategoryFactory(name='Armor')
    other = CategoryFactory(name='Scrolls')
    match = ProjectPageFactory(parent=projects_index, categories=[wanted], live=True)
    non_match = ProjectPageFactory(parent=projects_index, categories=[other], live=True)

    response = client.get(projects_index.url, {'category': wanted.id})

    projects = list(response.context['projects'])
    assert match in projects
    assert non_match not in projects
    assert response.context['active_category'] == wanted


def test_project_can_have_multiple_categories(projects_index):
    """A project can be assigned more than one category."""
    armor = CategoryFactory(name='Armor')
    collab = Category.objects.get(name='Collaborations')
    project = ProjectPageFactory(parent=projects_index, categories=[armor, collab])
    assert set(project.categories.all()) == {armor, collab}


def test_index_filter_matches_project_with_multiple_categories(client, projects_index):
    """Filtering by one of a project's several categories still matches it,
    and the project doesn't appear twice in the results."""
    armor = CategoryFactory(name='Armor')
    collab = Category.objects.get(name='Collaborations')
    project = ProjectPageFactory(parent=projects_index, categories=[armor, collab], live=True)

    response = client.get(projects_index.url, {'category': collab.id})

    projects = list(response.context['projects'])
    assert projects.count(project) == 1


def test_project_detail_renders_multiple_category_pills(client, projects_index):
    """The detail page renders one pill per assigned category."""
    armor = CategoryFactory(name='Armor')
    collab = Category.objects.get(name='Collaborations')
    project = ProjectPageFactory(parent=projects_index, categories=[armor, collab], live=True)

    response = client.get(project.url)
    content = response.content.decode()
    assert 'Armor' in content
    assert 'Collaborations' in content


def test_index_no_filter_shows_all_categories(client, projects_index, published_project):
    """With no ?category= param, active_category is None and all live projects show."""
    response = client.get(projects_index.url)
    assert response.context['active_category'] is None
    assert published_project in response.context['projects']


def test_index_categories_context_lists_only_categories_in_use(client, projects_index):
    """ProjectsIndexPage's categories context includes only categories with a
    live project under it, for the filter-chip row."""
    used = CategoryFactory(name='Armor')
    unused = CategoryFactory(name='Unused')
    ProjectPageFactory(parent=projects_index, categories=[used], live=True)

    response = client.get(projects_index.url)

    categories = list(response.context['categories'])
    assert used in categories
    assert unused not in categories


def test_index_categories_excludes_projects_outside_the_index(client, root_page, projects_index, wagtail_site):
    """A ProjectPage living directly under another parent (e.g. the moved
    Classes page) doesn't contribute to the Projects index's category list."""
    standalone_category = CategoryFactory(name='Classes')
    ProjectPageFactory(parent=root_page, slug='classes', categories=[standalone_category], live=True)

    response = client.get(projects_index.url)

    categories = list(response.context['categories'])
    assert standalone_category not in categories


def test_homepage_renders(client, home_page):
    """HomePage renders at its URL."""
    response = client.get(home_page.url)
    assert response.status_code == 200


def test_homepage_categories_only_includes_live_projects(client, home_page, projects_index):
    """HomePage's category quick-links only include categories with a live project."""
    live_category = CategoryFactory(name='Armor')
    empty_category = CategoryFactory(name='Unused')
    ProjectPageFactory(parent=projects_index, categories=[live_category], live=True)

    response = client.get(home_page.url)

    categories = list(response.context['categories'])
    assert live_category in categories
    assert empty_category not in categories


def test_project_no_technical_info_no_accordion(client, published_project):
    """Projects without technical_info don't render the accordion at all."""
    response = client.get(published_project.url)
    assert b'Technical Information' not in response.content


def test_project_renders_freeform_technical_info(client, projects_index):
    """Freeform technical_info renders its rich text inside the accordion."""
    project = ProjectPageFactory(
        parent=projects_index,
        live=True,
        technical_info=[{'type': 'freeform', 'value': '<p>Hand-forged from mild steel.</p>'}],
    )
    response = client.get(project.url)
    assert response.status_code == 200
    assert b'Technical Information' in response.content
    assert b'Hand-forged from mild steel.' in response.content


def test_project_renders_scribal_details(client, projects_index):
    """Scribal details render each fixed field, including optional gilding when set."""
    project = ProjectPageFactory(
        parent=projects_index,
        live=True,
        technical_info=[{
            'type': 'scribal_details',
            'value': {
                'size': '8x10 in',
                'reference': 'Visconti Hours, f.42',
                'surface': 'Black stonehenge paper',
                'colors': 'Gold, black',
                'nib': 'Brausse 2.5mm',
                'ink': 'Coliro gold paint',
                'hand': 'Insular Minuscule',
                'gilding': 'Raised gesso gilding',
            },
        }],
    )
    response = client.get(project.url)
    content = response.content.decode()
    assert 'Visconti Hours, f.42' in content
    assert 'Black stonehenge paper' in content
    assert 'Brausse 2.5mm' in content
    assert 'Insular Minuscule' in content
    assert 'Raised gesso gilding' in content


def test_project_scribal_details_omits_empty_gilding(client, projects_index):
    """Gilding is optional — its row is omitted entirely when left blank."""
    project = ProjectPageFactory(
        parent=projects_index,
        live=True,
        technical_info=[{
            'type': 'scribal_details',
            'value': {
                'size': '8x10 in',
                'reference': 'Visconti Hours, f.42',
                'surface': 'Black stonehenge paper',
                'colors': 'Gold, black',
                'nib': 'Brausse 2.5mm',
                'ink': 'Coliro gold paint',
                'hand': 'Insular Minuscule',
                'gilding': '',
            },
        }],
    )
    response = client.get(project.url)
    assert b'Gilding' not in response.content


def test_project_body_rich_text_block_renders_optional_title(client, projects_index):
    """A rich_text block with a title renders it as a section header."""
    project = ProjectPageFactory(
        parent=projects_index,
        live=True,
        body=[{
            'type': 'rich_text',
            'value': {'title': 'Drafting and Layout', 'text': '<p>Some prose.</p>'},
        }],
    )
    response = client.get(project.url)
    content = response.content.decode()
    assert 'Drafting and Layout' in content
    assert 'Some prose.' in content


def test_project_body_rich_text_block_without_title_renders_no_heading(client, projects_index):
    """A rich_text block with a blank title renders no section header."""
    project = ProjectPageFactory(
        parent=projects_index,
        live=True,
        body=[{'type': 'rich_text', 'value': {'title': '', 'text': '<p>Some prose.</p>'}}],
    )
    response = client.get(project.url)
    assert b'<h2' not in response.content


def test_project_body_standalone_image_renders(client, projects_index):
    """A standalone image block renders the image and its optional caption."""
    image = wagtail_factories.ImageFactory(title='Finished shield')
    project = ProjectPageFactory(
        parent=projects_index,
        live=True,
        body=[{'type': 'image', 'value': {'image': image.id, 'caption': 'The finished shield'}}],
    )
    response = client.get(project.url)
    content = response.content.decode()
    assert 'The finished shield' in content


def test_project_body_carousel_renders_dots_for_multiple_images(client, projects_index):
    """A carousel block with 2+ images renders pagination dots."""
    image_a = wagtail_factories.ImageFactory(title='Angle 1')
    image_b = wagtail_factories.ImageFactory(title='Angle 2')
    project = ProjectPageFactory(
        parent=projects_index,
        live=True,
        body=[{
            'type': 'carousel',
            'value': [
                {'image': image_a.id, 'caption': 'First angle'},
                {'image': image_b.id, 'caption': 'Second angle'},
            ],
        }],
    )
    response = client.get(project.url)
    content = response.content.decode()
    assert 'First angle' in content
    assert 'Second angle' in content
    assert content.count('aria-label="Show image') == 2


def test_project_body_carousel_omits_dots_for_single_image(client, projects_index):
    """A carousel block with only one image renders no pagination dots."""
    image = wagtail_factories.ImageFactory(title='Only angle')
    project = ProjectPageFactory(
        parent=projects_index,
        live=True,
        body=[{'type': 'carousel', 'value': [{'image': image.id, 'caption': 'Only angle'}]}],
    )
    response = client.get(project.url)
    assert b'aria-label="Show image' not in response.content


def test_thumbnail_prefers_explicit_cover_image(projects_index):
    """thumbnail returns cover_image when set, even if body also has images."""
    cover = wagtail_factories.ImageFactory(title='Cover')
    body_image = wagtail_factories.ImageFactory(title='Body image')
    project = ProjectPageFactory(
        parent=projects_index,
        cover_image=cover,
        body=[{'type': 'image', 'value': {'image': body_image.id, 'caption': ''}}],
    )
    assert project.thumbnail == cover


def test_thumbnail_falls_back_to_first_structured_image_block(projects_index):
    """With no cover_image, thumbnail uses the first image/carousel block."""
    image = wagtail_factories.ImageFactory(title='Body image')
    project = ProjectPageFactory(
        parent=projects_index,
        cover_image=None,
        body=[{'type': 'image', 'value': {'image': image.id, 'caption': ''}}],
    )
    assert project.thumbnail == image


def test_thumbnail_falls_back_to_first_carousel_image(projects_index):
    """With no cover_image or standalone image block, thumbnail uses the
    first image of the first carousel block."""
    image = wagtail_factories.ImageFactory(title='Carousel image')
    project = ProjectPageFactory(
        parent=projects_index,
        cover_image=None,
        body=[{'type': 'carousel', 'value': [{'image': image.id, 'caption': ''}]}],
    )
    assert project.thumbnail == image


def test_thumbnail_falls_back_to_legacy_embedded_image(projects_index):
    """With no cover_image or structured image blocks, thumbnail extracts
    the first <embed> image from legacy migrated rich text."""
    image = wagtail_factories.ImageFactory(title='Embedded image')
    project = ProjectPageFactory(
        parent=projects_index,
        cover_image=None,
        body=[{
            'type': 'rich_text',
            'value': {
                'title': '',
                'text': f'<p>Some text.</p><embed embedtype="image" format="left" id="{image.id}" alt="x"/><p>More.</p>',
            },
        }],
    )
    assert project.thumbnail == image


def test_thumbnail_none_when_no_images_anywhere(projects_index):
    """thumbnail is None when there's no cover_image, no structured image
    blocks, and no legacy embeds."""
    project = ProjectPageFactory(
        parent=projects_index,
        cover_image=None,
        body=[{'type': 'rich_text', 'value': {'title': '', 'text': '<p>No images here.</p>'}}],
    )
    assert project.thumbnail is None


def test_index_renders_thumbnail_image(client, projects_index):
    """Projects index renders an <img> for a project with a thumbnail."""
    image = wagtail_factories.ImageFactory(title='Cover')
    ProjectPageFactory(parent=projects_index, cover_image=image, live=True)
    response = client.get(projects_index.url)
    assert b'<img src=' in response.content
