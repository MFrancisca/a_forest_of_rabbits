"""Keep each project page's images in an image collection of its own.

Every project page gets a collection named after its title, under a parent
"Projects" collection. Saving the page (draft or publish) syncs it:
- images on the page move into the page's collection;
- images in that collection that are no longer on the page move up to "Projects".
Images are never deleted, only moved between collections.

A Wagtail image lives in exactly one collection. If an image is already in
another project's collection, it stays there: the first project to collect it
keeps it, so two pages sharing an image don't keep pulling it back and forth.

The page <-> collection link is a ProjectCollection row, not a field on the page,
so it isn't stored in page revisions and reverting a revision can't lose it.
"""
from dataclasses import dataclass, field

from wagtail.images import get_image_model
from wagtail.models import Collection

from blog.models import ProjectCollection, embedded_image_ids
from core.collections import top_level_collection

PROJECTS_COLLECTION_NAME = 'Projects'


@dataclass
class SyncResult:
    collection: Collection
    created: bool = False
    renamed_from: str = ''
    added: list = field(default_factory=list)      # image pks moved into the collection
    removed: list = field(default_factory=list)    # image pks moved up to "Projects"
    kept_elsewhere: list = field(default_factory=list)  # in another project's collection

    @property
    def changed(self):
        return self.created or bool(self.renamed_from or self.added or self.removed)


def projects_collection():
    """The parent "Projects" collection (a child of Root), created if missing."""
    return top_level_collection(PROJECTS_COLLECTION_NAME)


def page_image_ids(page):
    """Pks of every image used on a project or blog post page: cover image, image
    blocks, carousel slides, and images embedded in rich text (including a
    project's technical info). Deleted images are skipped."""
    ids = set()
    if page.cover_image_id:
        ids.add(page.cover_image_id)

    rich_texts = []
    for block in page.body:
        if block.block_type == 'image':
            if block.value['image']:
                ids.add(block.value['image'].pk)
        elif block.block_type == 'carousel':
            ids.update(item['image'].pk for item in block.value['images'] if item['image'])
        elif block.block_type == 'rich_text':
            rich_texts.append(block.value['text'].source)
    # Only projects have technical info.
    rich_texts += [block.value.source for block in getattr(page, 'technical_info', ())
                   if block.block_type == 'freeform']

    for source in rich_texts:
        ids.update(embedded_image_ids(source))

    # Drop ids of images that no longer exist (rich text embeds aren't checked by Wagtail).
    return set(get_image_model().objects.filter(pk__in=ids).values_list('pk', flat=True))


def _collection_for(page, parent):
    """The page's collection, creating or renaming it to match the page title.
    Returns (collection, created, renamed_from)."""
    title = page.title
    link = ProjectCollection.objects.filter(page_id=page.pk).select_related('collection').first()
    if link:
        collection = link.collection
        if collection.name != title:
            old = collection.name
            collection.name = title
            collection.save(update_fields=['name'])
            return collection, False, old
        return collection, False, ''

    # Adopt a same-named collection under "Projects" that no page owns yet: one made
    # by hand in the admin, or rebuilt after content was copied between databases.
    owned = ProjectCollection.objects.values('collection_id')
    collection = parent.get_children().filter(name=title).exclude(pk__in=owned).first()
    created = collection is None
    if created:
        collection = parent.add_child(name=title)
    ProjectCollection.objects.create(page_id=page.pk, collection=collection)
    return collection, created, ''


def sync_project_collection(page):
    """Create or update `page`'s collection so it holds exactly the page's images.

    `page` is the content to sync from, which for a draft is the latest revision
    (revision.as_object()), not the live Page row.
    """
    Image = get_image_model()
    parent = projects_collection()
    collection, created, renamed_from = _collection_for(page, parent)
    result = SyncResult(collection=collection, created=created, renamed_from=renamed_from)

    wanted = page_image_ids(page)
    other_projects = ProjectCollection.objects.exclude(page_id=page.pk).values('collection_id')

    to_add = Image.objects.filter(pk__in=wanted).exclude(collection=collection)
    result.kept_elsewhere = sorted(to_add.filter(collection__in=other_projects).values_list('pk', flat=True))
    to_add = to_add.exclude(collection__in=other_projects)
    result.added = sorted(to_add.values_list('pk', flat=True))
    to_add.update(collection=collection)

    to_remove = Image.objects.filter(collection=collection).exclude(pk__in=wanted)
    result.removed = sorted(to_remove.values_list('pk', flat=True))
    to_remove.update(collection=parent)

    return result


def latest_content(page):
    """The page as it was last saved: its latest revision, or the Page row if it
    has none (e.g. content loaded from a fixture)."""
    revision = page.get_latest_revision()
    return revision.as_object() if revision else page
