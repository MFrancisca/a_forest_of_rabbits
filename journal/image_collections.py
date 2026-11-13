"""File blog post images into one top-level "Blog" collection.

Saving a post (draft or publish) moves the images it uses that are still unfiled
(in the root collection) into "Blog". Images already in another collection, such
as a project's, stay where they are, and images removed from a post stay in
"Blog". Images are never deleted, only moved. There are no per-post collections,
so the admin's collection filter stays short.
"""
from wagtail.images import get_image_model
from wagtail.models import Collection

from blog.image_collections import page_image_ids
from core.collections import top_level_collection

BLOG_COLLECTION_NAME = 'Blog'


def blog_collection():
    return top_level_collection(BLOG_COLLECTION_NAME)


def file_post_images(page):
    """Move the unfiled images `page` uses into "Blog". Returns the pks moved."""
    root = Collection.get_first_root_node()
    unfiled = get_image_model().objects.filter(pk__in=page_image_ids(page), collection=root)
    moved = list(unfiled.values_list('pk', flat=True))
    if moved:
        get_image_model().objects.filter(pk__in=moved).update(collection=blog_collection())
    return moved
