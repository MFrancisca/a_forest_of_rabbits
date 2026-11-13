"""Tests for the staging -> production content sync.

The real command reads from a second Postgres. Here the 'staging' alias is
pointed at the *same* connection object as 'default' (so it sees this test's
uncommitted rows), which exercises the full dump -> remap -> loaddata path
against the test database. Remapping is then an identity mapping; the
mismatched-pk and missing-row cases are covered with stub models below.
"""
import json
from io import StringIO
from types import SimpleNamespace
from unittest import mock

import pytest
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connections
import wagtail_factories
from wagtail.models import Collection, Page

from blog.factories import CategoryFactory, ProjectPageFactory, ProjectsIndexPageFactory
from blog.image_collections import projects_collection
from blog.models import ProjectCollection, ProjectPage, ProjectsIndexColumn
from core.management.commands.sync_staging_to_production import Command
from pigments.factories import FormulaPartFactory, ManuscriptFactory

MODULE = 'core.management.commands.sync_staging_to_production'


@pytest.fixture
def staging_is_default(db):
    """Make the 'staging' alias resolve to the current default connection."""
    default_settings = dict(connections['default'].settings_dict)
    setattr(connections._connections, 'staging', connections['default'])
    # The command closes 'staging' when done; since that's the default
    # connection here, a real close (Postgres) would break the test transaction.
    with mock.patch(f'{MODULE}.dj_database_url.parse', return_value=default_settings), \
            mock.patch.object(connections['default'], 'close'):
        yield
    delattr(connections._connections, 'staging')
    connections.databases.pop('staging', None)
    settings.DATABASES.pop('staging', None)


@pytest.fixture
def content(db):
    projects_index = ProjectsIndexPageFactory(parent=Page.objects.get(depth=1))
    category = CategoryFactory(name='Armor')
    page = ProjectPageFactory(parent=projects_index, categories=[category])
    ProjectsIndexColumn.objects.create(page=projects_index, category=category)
    part = FormulaPartFactory()
    return SimpleNamespace(page=page, category=category, part=part, index=projects_index)


def _run(tmp_path, **options):
    out = StringIO()
    fixture = tmp_path / 'dump.json'
    call_command(
        'sync_staging_to_production',
        staging_url='postgres://ignored/ignored',
        fixture_path=fixture,
        stdout=out,
        stderr=StringIO(),
        **options,
    )
    return out.getvalue(), fixture


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def test_missing_staging_url_is_an_error(monkeypatch):
    monkeypatch.delenv('STAGING_DATABASE_PUBLIC_URL', raising=False)
    with pytest.raises(CommandError, match='--staging-url'):
        call_command('sync_staging_to_production', staging_url=None)


# ---------------------------------------------------------------------------
# End to end against the test database
# ---------------------------------------------------------------------------

def test_dry_run_dumps_content_and_writes_fixture(staging_is_default, content, tmp_path):
    out, fixture = _run(tmp_path, dry_run=True)

    records = json.loads(fixture.read_text())
    models = {r['model'] for r in records}
    assert {'wagtailcore.page', 'blog.projectpage', 'blog.category',
            'blog.projectsindexcolumn', 'pigments.formulapart', 'pigments.pigment'} <= models
    assert '[DRY RUN]' in out

    pages = [r for r in records if r['model'] == 'wagtailcore.page']
    assert pages and all(r['fields']['depth'] >= 2 for r in pages), 'root page must be excluded'
    for record in pages:
        for field in ('owner', 'locked_by', 'live_revision', 'latest_revision'):
            assert record['fields'][field] is None

    project = next(r for r in records if r['model'] == 'blog.projectpage' and r['pk'] == content.page.pk)
    assert project['fields']['categories'] == [content.category.pk]


def test_load_replaces_rows_in_target(staging_is_default, content, tmp_path):
    out, _ = _run(tmp_path, noinput=True)

    assert 'Loaded staging content' in out
    content.page.refresh_from_db()
    assert list(content.page.categories.all()) == [content.category]
    assert [c.category for c in content.index.columns.all()] == [content.category]


def test_project_collections_are_rebuilt_not_copied(staging_is_default, content, tmp_path):
    """Images in staging's project collections are loaded into the root collection
    (the target may not have those collections), then put back by page content."""
    on_page, taken_off = wagtail_factories.ImageFactory(), wagtail_factories.ImageFactory()
    page = ProjectPage.objects.get(pk=content.page.pk)
    page.body = [{'type': 'image', 'value': {'image': on_page.pk, 'caption': ''}},
                 {'type': 'image', 'value': {'image': taken_off.pk, 'caption': ''}}]
    page.save_revision()
    page.body = [{'type': 'image', 'value': {'image': on_page.pk, 'caption': ''}}]
    page.save()  # the live row the dump copies; no revisions are copied
    page.save_revision()
    collection = ProjectCollection.objects.get(page=page).collection

    out, fixture = _run(tmp_path, noinput=True)

    images = {r['pk']: r for r in json.loads(fixture.read_text()) if r['model'] == 'wagtailimages.image'}
    root = Collection.get_first_root_node()
    assert images[on_page.pk]['fields']['collection'] == root.pk
    assert images[taken_off.pk]['fields']['collection'] == root.pk
    assert not any(r['model'] == 'blog.projectcollection' for r in json.loads(fixture.read_text()))
    on_page.refresh_from_db()
    taken_off.refresh_from_db()
    assert on_page.collection == collection
    assert taken_off.collection == projects_collection()
    assert f'{page.title}: ' in out


def test_manuscripts_collection_is_recreated_not_required(staging_is_default, content, tmp_path):
    """An illumination filed in staging's "Manuscripts" collection loads into the root
    collection (the target may not have "Manuscripts"), then moves back into it."""
    image = wagtail_factories.ImageFactory(collection=Collection.get_first_root_node())
    ManuscriptFactory(illumination=image, illumination_credit='Library')
    image.refresh_from_db()
    assert image.collection.name == 'Manuscripts'

    out, fixture = _run(tmp_path, noinput=True)

    images = {r['pk']: r for r in json.loads(fixture.read_text()) if r['model'] == 'wagtailimages.image'}
    assert images[image.pk]['fields']['collection'] == Collection.get_first_root_node().pk
    image.refresh_from_db()
    assert image.collection.name == 'Manuscripts'
    assert 'Loaded staging content' in out


def test_blog_posts_are_copied_and_blog_collection_recreated(staging_is_default, content, tmp_path):
    """Blog posts, tags and their links to projects are copied; an image in staging's
    "Blog" collection loads into the root collection, then moves back into "Blog"."""
    from journal.factories import BlogIndexPageFactory, BlogPostPageFactory
    from journal.image_collections import blog_collection
    from journal.models import PIGMENTS_TAG_SLUG, Tag

    image = wagtail_factories.ImageFactory(collection=blog_collection())
    index = BlogIndexPageFactory(parent=Page.objects.get(depth=1))
    tag = Tag.objects.get(slug=PIGMENTS_TAG_SLUG)
    post = BlogPostPageFactory(parent=index, cover_image=image, tags=[tag],
                               related_projects=[content.page])

    out, fixture = _run(tmp_path, noinput=True)

    records = json.loads(fixture.read_text())
    models = {r['model'] for r in records}
    assert {'journal.tag', 'journal.blogindexpage', 'journal.blogpostpage'} <= models
    post_record = next(r for r in records if r['model'] == 'journal.blogpostpage')
    assert post_record['fields']['tags'] == [tag.pk]
    assert post_record['fields']['related_projects'] == [content.page.pk]
    images = {r['pk']: r for r in records if r['model'] == 'wagtailimages.image'}
    assert images[image.pk]['fields']['collection'] == Collection.get_first_root_node().pk
    image.refresh_from_db()
    assert image.collection.name == 'Blog'
    assert post.pk in [p.pk for p in content.page.journal_posts.all()]


def test_journal_models_follow_the_blog_models():
    from core.management.commands.sync_staging_to_production import FULL_MODEL_LABELS

    journal = [FULL_MODEL_LABELS.index(m) for m in ('journal.tag', 'journal.blogindexpage', 'journal.blogpostpage')]
    blog = [i for i, m in enumerate(FULL_MODEL_LABELS) if m.startswith('blog.')]
    assert min(journal) > max(blog)


def test_interactive_cancel_does_not_load(staging_is_default, content, tmp_path):
    with mock.patch('builtins.input', return_value='no'), \
            mock.patch(f'{MODULE}.call_command', wraps=call_command) as cc:
        out, _ = _run(tmp_path)

    assert 'Cancelled.' in out
    assert 'loaddata' not in [c.args[0] for c in cc.call_args_list]


def test_dump_failure_exits_nonzero(staging_is_default, tmp_path):
    with mock.patch.object(Command, '_dump_from_staging', side_effect=RuntimeError('boom')):
        with pytest.raises(SystemExit) as exc:
            _run(tmp_path, dry_run=True)
    assert exc.value.code == 1


# ---------------------------------------------------------------------------
# pk remapping of ContentType / Locale / Collection
# ---------------------------------------------------------------------------

def _stub_model(staging_rows, target_rows):
    """Minimal stand-in for model.objects.using('staging')... / model.objects.values()."""
    staging_qs = mock.Mock()
    staging_qs.filter.return_value.values.return_value = staging_rows
    manager = mock.Mock()
    manager.using.return_value = staging_qs
    manager.values.return_value = target_rows
    return SimpleNamespace(objects=manager)


def test_build_remap_maps_by_identity_not_pk():
    model = _stub_model(
        staging_rows=[{'pk': 10, 'app_label': 'blog', 'model': 'projectpage'}],
        target_rows=[
            {'pk': 3, 'app_label': 'blog', 'model': 'projectpage'},
            {'pk': 10, 'app_label': 'blog', 'model': 'homepage'},
        ],
    )
    assert Command._build_remap(model, {10}, ('app_label', 'model'), 'content type') == {10: 3}


def test_build_remap_aborts_when_target_lacks_a_row():
    model = _stub_model(
        staging_rows=[{'pk': 5, 'language_code': 'fr'}],
        target_rows=[{'pk': 1, 'language_code': 'en'}],
    )
    with pytest.raises(CommandError, match=r"locale \('fr',\)"):
        Command._build_remap(model, {5}, ('language_code',), 'locale')


def test_build_remap_no_ids_is_empty():
    assert Command._build_remap(None, set(), ('name',), 'collection') == {}


def test_remap_shared_references_rewrites_page_and_image_fields():
    records = [
        {'model': 'wagtailcore.page', 'fields': {'content_type': 10, 'locale': 5}},
        {'model': 'wagtailcore.page', 'fields': {'content_type': None, 'locale': None}},
        {'model': 'wagtailimages.image', 'fields': {'collection': 7}},
        {'model': 'blog.category', 'fields': {'name': 'x'}},
    ]
    maps = {'content type': {10: 3}, 'locale': {5: 1}, 'collection': {7: 2}}
    with mock.patch.object(Command, '_build_remap', side_effect=lambda m, ids, f, label: maps[label]), \
            mock.patch.object(Command, '_staging_collection_tree_ids', return_value=set()):
        Command()._remap_shared_references(records)

    assert records[0]['fields'] == {'content_type': 3, 'locale': 1}
    assert records[1]['fields'] == {'content_type': None, 'locale': None}
    assert records[2]['fields'] == {'collection': 2}
    assert records[3]['fields'] == {'name': 'x'}


def test_counts_by_model():
    records = [{'model': 'a'}, {'model': 'b'}, {'model': 'a'}]
    assert Command._counts_by_model(records) == {'a': 2, 'b': 1}
