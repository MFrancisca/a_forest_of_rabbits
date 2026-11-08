from io import StringIO

import pytest
import wagtail_factories
from django.core.management import call_command

from blog.factories import ProjectPageFactory
from blog.management.commands.split_project_body_streamfield import group_nodes, parse_nodes
from blog.models import ProjectPage


def _embed(image_id, alt=''):
    return f'<embed embedtype="image" format="fullwidth" id="{image_id}" alt="{alt}"/>'


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------

def test_parse_nodes_splits_text_and_images_and_drops_spacers():
    html = (
        '<h2>Heading</h2>\n'
        '<p>First</p>'
        '<p>   </p>'          # spacer — dropped
        f'{_embed(7, "seven")}'
        '<embed embedtype="image" id="not-a-number"/>'  # unusable id — dropped
        '<p><b></b></p>'      # empty — dropped
        '<ul><li>Item</li></ul>'
    )
    assert parse_nodes(html) == [
        ('text', '<h2>Heading</h2>'),
        ('text', '<p>First</p>'),
        ('image', 7, 'seven'),
        ('text', '<ul><li>Item</li></ul>'),
    ]


def test_parse_nodes_keeps_paragraph_that_only_wraps_an_image():
    """Only top-level embeds become image nodes; one nested in a <p> stays
    inside that paragraph's rich text (it isn't an empty spacer)."""
    [(kind, html)] = parse_nodes(f'<p>{_embed(3)}</p>')
    assert kind == 'text'
    assert html.startswith('<p><embed') and 'id="3"' in html


def test_group_nodes_single_image_vs_carousel_runs():
    nodes = [
        ('text', '<p>a</p>'),
        ('image', 1, 'one'),
        ('text', '<p>b</p>'),
        ('image', 2, 'two'),
        ('image', 3, ''),
    ]
    assert group_nodes(nodes) == [
        ('rich_text', {'title': '', 'text': '<p>a</p>'}),
        ('image', {'image': 1, 'caption': 'one'}),
        ('rich_text', {'title': '', 'text': '<p>b</p>'}),
        ('carousel', [{'image': 2, 'caption': 'two'}, {'image': 3, 'caption': ''}]),
    ]


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------

def _unsplit_page(index, html):
    return ProjectPageFactory(
        parent=index,
        body=[{'type': 'rich_text', 'value': {'title': '', 'text': html}}],
    )


def _block_types(page):
    return [b.block_type for b in ProjectPage.objects.get(pk=page.pk).body]


@pytest.mark.django_db
def test_command_splits_unsplit_page(projects_index):
    a, b, c = (wagtail_factories.ImageFactory() for _ in range(3))
    page = _unsplit_page(
        projects_index,
        f'<p>Intro</p>{_embed(a.pk, "solo")}<p>Middle</p>{_embed(b.pk)}{_embed(c.pk)}',
    )
    out = StringIO()

    call_command('split_project_body_streamfield', stdout=out)

    body = ProjectPage.objects.get(pk=page.pk).body
    assert [blk.block_type for blk in body] == ['rich_text', 'image', 'rich_text', 'carousel']
    assert body[1].value['image'] == a
    assert body[1].value['caption'] == 'solo'
    assert [item['image'] for item in body[3].value['images']] == [b, c]
    assert 'Processed 1 page(s); skipped 0' in out.getvalue()


@pytest.mark.django_db
def test_command_dry_run_saves_nothing(projects_index):
    image = wagtail_factories.ImageFactory()
    page = _unsplit_page(projects_index, f'<p>Intro</p>{_embed(image.pk)}')
    out = StringIO()

    call_command('split_project_body_streamfield', dry_run=True, stdout=out)

    assert _block_types(page) == ['rich_text']
    assert '[DRY RUN]' in out.getvalue()
    assert 'Would process 1 page(s)' in out.getvalue()


@pytest.mark.django_db
def test_command_skips_already_split_pages_and_is_rerunnable(projects_index):
    image = wagtail_factories.ImageFactory()
    page = _unsplit_page(projects_index, f'<p>Intro</p>{_embed(image.pk)}')

    call_command('split_project_body_streamfield', stdout=StringIO())
    out = StringIO()
    call_command('split_project_body_streamfield', stdout=out)

    assert _block_types(page) == ['rich_text', 'image']
    assert 'Processed 0 page(s); skipped 1' in out.getvalue()


@pytest.mark.django_db
def test_command_drops_missing_images_and_degrades_carousel(projects_index):
    kept = wagtail_factories.ImageFactory()
    page = _unsplit_page(
        projects_index,
        # standalone missing image, then a 2-image run with one missing
        f'<p>Intro</p>{_embed(999001)}<p>Mid</p>{_embed(kept.pk)}{_embed(999002)}',
    )
    out = StringIO()

    call_command('split_project_body_streamfield', stdout=out)

    body = ProjectPage.objects.get(pk=page.pk).body
    assert [blk.block_type for blk in body] == ['rich_text', 'rich_text', 'image']
    assert body[2].value['image'] == kept
    assert '999001' in out.getvalue() and '999002' in out.getvalue()


@pytest.mark.django_db
def test_command_drops_carousel_with_no_surviving_images(projects_index):
    page = _unsplit_page(projects_index, f'<p>Intro</p>{_embed(999001)}{_embed(999002)}')

    call_command('split_project_body_streamfield', stdout=StringIO())

    assert _block_types(page) == ['rich_text']
