"""Each project page keeps its images in a collection of its own (blog/image_collections.py)."""
from io import StringIO

import pytest
import wagtail_factories
from django.core.management import call_command
from wagtail.images.models import Image
from wagtail.models import Collection

from blog.factories import ProjectPageFactory
from blog.image_collections import PROJECTS_COLLECTION_NAME, project_image_ids, projects_collection
from blog.models import ProjectCollection, ProjectPage

pytestmark = pytest.mark.django_db


def _image():
    return wagtail_factories.ImageFactory()


def _body(*images, embed=None):
    """A body with one image block and a carousel of the rest, plus an optional rich text embed."""
    body = []
    if images:
        body.append({'type': 'image', 'value': {'image': images[0].pk, 'caption': ''}})
    if len(images) > 1:
        body.append({'type': 'carousel', 'value': {'title': '', 'images': [
            {'image': image.pk, 'caption': ''} for image in images[1:]]}})
    if embed:
        body.append({'type': 'rich_text', 'value': {'title': '', 'text':
            f'<p>Text</p><embed embedtype="image" id="{embed.pk}" format="fullwidth" alt="x"/>'}})
    return body


def _collection(page):
    return ProjectCollection.objects.get(page=page).collection


def _ids(collection):
    return set(Image.objects.filter(collection=collection).values_list('pk', flat=True))


def _edit(page, **fields):
    """What saving in the admin does: change the content, then save a revision."""
    page = ProjectPage.objects.get(pk=page.pk)
    for name, value in fields.items():
        setattr(page, name, value)
    page.save_revision()
    return page


# --- first save ------------------------------------------------------------------

def test_first_save_creates_a_collection_under_projects_with_the_page_images(projects_index):
    cover, single, slide_a, slide_b, embedded, tech = (_image() for _ in range(6))
    page = ProjectPageFactory(
        parent=projects_index, title='Sable Swap', cover_image=cover,
        body=_body(single, slide_a, slide_b, embed=embedded),
        technical_info=[{'type': 'freeform', 'value':
            f'<embed embedtype="image" id="{tech.pk}" format="left" alt="t"/>'}],
    )
    page.save_revision()

    collection = _collection(page)
    assert collection.name == 'Sable Swap'
    assert collection.get_parent().name == PROJECTS_COLLECTION_NAME
    assert collection.get_parent().get_parent().is_root()
    assert _ids(collection) == {cover.pk, single.pk, slide_a.pk, slide_b.pk, embedded.pk, tech.pk}


def test_reuses_an_existing_projects_collection(projects_index):
    """Production already has a "Projects" collection, made by hand."""
    existing = Collection.get_first_root_node().add_child(name=PROJECTS_COLLECTION_NAME)
    page = ProjectPageFactory(parent=projects_index, body=_body(_image()))
    page.save_revision()

    assert _collection(page).get_parent() == existing
    assert Collection.objects.filter(name=PROJECTS_COLLECTION_NAME).count() == 1


def test_adopts_a_same_named_collection_no_page_owns(projects_index):
    made_by_hand = projects_collection().add_child(name='Fan')
    page = ProjectPageFactory(parent=projects_index, title='Fan', body=_body(_image()))
    page.save_revision()

    assert _collection(page) == made_by_hand


def test_page_without_images_still_gets_an_empty_collection(projects_index):
    page = ProjectPageFactory(parent=projects_index)
    page.save_revision()

    assert _ids(_collection(page)) == set()


# --- later saves -------------------------------------------------------------------

def test_later_saves_add_new_images_and_move_removed_ones_up_to_projects(projects_index):
    kept, dropped, added = _image(), _image(), _image()
    page = ProjectPageFactory(parent=projects_index, body=_body(kept, dropped))
    page.save_revision()

    _edit(page, body=_body(kept, added))

    assert _ids(_collection(page)) == {kept.pk, added.pk}
    dropped.refresh_from_db()
    assert dropped.collection == projects_collection()
    assert Image.objects.count() == 3  # never deleted


def test_draft_saves_sync_the_draft_not_the_live_page(projects_index):
    live_image, draft_image = _image(), _image()
    page = ProjectPageFactory(parent=projects_index, body=_body(live_image))
    page.save_revision().publish()

    _edit(page, body=_body(draft_image))  # draft only, not published

    assert ProjectPage.objects.get(pk=page.pk).body[0].value['image'] == live_image
    assert _ids(_collection(page)) == {draft_image.pk}


def test_renaming_the_page_renames_its_collection(projects_index):
    page = ProjectPageFactory(parent=projects_index, title='Old name')
    page.save_revision()
    collection = _collection(page)

    _edit(page, title='New name')

    collection.refresh_from_db()
    assert collection.name == 'New name'
    assert Collection.objects.filter(name='Old name').count() == 0


def test_image_already_in_another_projects_collection_stays_there(projects_index):
    shared = _image()
    first = ProjectPageFactory(parent=projects_index, body=_body(shared))
    first.save_revision()
    second = ProjectPageFactory(parent=projects_index, body=_body(shared))
    second.save_revision()

    assert _ids(_collection(first)) == {shared.pk}
    assert _ids(_collection(second)) == set()


def test_deleted_and_missing_images_are_ignored(projects_index):
    gone, embedded_then_deleted = _image(), _image()
    page = ProjectPageFactory(parent=projects_index, body=_body(gone, embed=embedded_then_deleted))
    gone.delete()
    embedded_then_deleted.delete()  # rich text keeps the dangling <embed id="...">

    assert project_image_ids(ProjectPage.objects.get(pk=page.pk)) == set()


def test_deleting_a_page_keeps_its_collection_and_images(projects_index):
    image = _image()
    page = ProjectPageFactory(parent=projects_index, body=_body(image))
    page.save_revision()
    collection = _collection(page)

    page.delete()

    assert Collection.objects.filter(pk=collection.pk).exists()
    assert _ids(collection) == {image.pk}


# --- backfill command ----------------------------------------------------------------

def _command(*args):
    out = StringIO()
    call_command('sync_project_collections', *args, stdout=out)
    return out.getvalue()


def test_command_creates_collections_for_existing_pages(projects_index):
    """Pages loaded without saving (like the existing ones) have no collection yet."""
    image = _image()
    page = ProjectPageFactory(parent=projects_index, title='Old project', body=_body(image))
    assert not ProjectCollection.objects.exists()

    out = _command()

    assert _ids(_collection(page)) == {image.pk}
    assert 'Old project: created, +1 images, -0 images' in out
    # Re-running changes nothing.
    assert '0 collections changed' in _command()


def test_command_dry_run_changes_nothing(projects_index):
    ProjectPageFactory(parent=projects_index, body=_body(_image()))

    out = _command('--dry-run')

    assert 'created, +1 images' in out
    assert '[DRY RUN]' in out
    assert not ProjectCollection.objects.exists()
    assert not Collection.objects.filter(name=PROJECTS_COLLECTION_NAME).exists()


def test_copying_a_page_only_syncs_its_final_content(projects_index):
    """Copying re-saves every old revision of the original. Only the copy's final
    content may sync, or images from old drafts get moved around."""
    elsewhere = Collection.get_first_root_node().add_child(name='Pigments')
    old_draft_image = _image()
    old_draft_image.collection = elsewhere
    old_draft_image.save()
    original = ProjectPageFactory(parent=projects_index, title='Original')
    original = _edit(original, body=_body(old_draft_image))  # synced: moved in
    old_draft_image.collection = elsewhere  # put it back by hand
    old_draft_image.save()
    with_new = _image()
    original = _edit(original, body=_body(with_new))
    old_draft_image.refresh_from_db()
    assert old_draft_image.collection == elsewhere

    copy = original.copy(update_attrs={'title': 'Copy', 'slug': 'copy'})

    old_draft_image.refresh_from_db()
    assert old_draft_image.collection == elsewhere
    assert _collection(copy).name == 'Copy'
    # with_new already belongs to the original's collection, so it stays there.
    assert _ids(_collection(copy)) == set()
    assert _ids(_collection(original)) == {with_new.pk}


# --- admin ---------------------------------------------------------------------------

def test_admin_refuses_to_delete_a_project_collection_or_projects(client, admin_user, projects_index):
    page = ProjectPageFactory(parent=projects_index)
    page.save_revision()
    client.force_login(admin_user)

    for collection in (_collection(page), projects_collection()):
        url = f'/cms/collections/{collection.pk}/delete/'
        response = client.get(url)
        assert response.status_code == 200
        assert '1 project page' in response.content.decode()
        assert client.post(url).status_code == 403
        assert Collection.objects.filter(pk=collection.pk).exists()


def test_admin_can_still_delete_an_unlinked_empty_collection(client, admin_user):
    spare = projects_collection().add_child(name='Spare')
    client.force_login(admin_user)

    client.post(f'/cms/collections/{spare.pk}/delete/')

    assert not Collection.objects.filter(pk=spare.pk).exists()
