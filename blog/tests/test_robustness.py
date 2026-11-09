"""Regression tests for malformed input and dangling image references."""
import pytest
import wagtail_factories

from blog.factories import ProjectPageFactory
from blog.models import ProjectPage


# ---------------------------------------------------------------------------
# Images deleted after being chosen in a StreamField block
# ---------------------------------------------------------------------------

def _reload(page):
    return ProjectPage.objects.get(pk=page.pk)


@pytest.mark.django_db
def test_thumbnail_skips_deleted_image_block(projects_index):
    gone = wagtail_factories.ImageFactory()
    kept = wagtail_factories.ImageFactory()
    page = ProjectPageFactory(parent=projects_index, body=[
        {'type': 'image', 'value': {'title': '', 'image': gone.pk, 'caption': ''}},
        {'type': 'image', 'value': {'title': '', 'image': kept.pk, 'caption': ''}},
    ])
    gone.delete()

    assert _reload(page).thumbnail == kept


@pytest.mark.django_db
def test_thumbnail_skips_deleted_carousel_slide(projects_index):
    gone = wagtail_factories.ImageFactory()
    kept = wagtail_factories.ImageFactory()
    page = ProjectPageFactory(parent=projects_index, body=[
        {'type': 'carousel', 'value': {'title': '', 'images': [
            {'image': gone.pk, 'caption': ''},
            {'image': kept.pk, 'caption': ''},
        ]}},
    ])
    gone.delete()

    assert _reload(page).thumbnail == kept


@pytest.mark.django_db
def test_thumbnail_none_when_only_image_was_deleted(projects_index):
    gone = wagtail_factories.ImageFactory()
    page = ProjectPageFactory(parent=projects_index, body=[
        {'type': 'image', 'value': {'title': '', 'image': gone.pk, 'caption': ''}},
    ])
    gone.delete()

    assert _reload(page).thumbnail is None


@pytest.mark.django_db
def test_deleted_image_block_does_not_repeat_previous_image(client, projects_index):
    """{% image None ... as img %} leaves `img` untouched, so an unguarded block
    re-rendered the previous block's rendition."""
    shown = wagtail_factories.ImageFactory()
    gone = wagtail_factories.ImageFactory()
    page = ProjectPageFactory(parent=projects_index, body=[
        {'type': 'image', 'value': {'title': '', 'image': shown.pk, 'caption': 'kept'}},
        {'type': 'image', 'value': {'title': '', 'image': gone.pk, 'caption': 'orphan caption'}},
        {'type': 'carousel', 'value': {'title': '', 'images': [
            {'image': gone.pk, 'caption': 'orphan slide'},
            {'image': shown.pk, 'caption': ''},
        ]}},
    ])
    gone.delete()

    html = client.get(page.url).content.decode()

    assert 'orphan caption' not in html
    assert 'orphan slide' not in html
    # One <img> for the standalone block + one for the surviving slide.
    assert html.count('object-cover rounded-lg shadow-sm') == 1
    assert html.count('class="w-full rounded-lg"') == 1
