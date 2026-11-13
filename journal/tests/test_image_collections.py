"""All blog post images are filed into one top-level "Blog" collection (journal/image_collections.py)."""
import pytest
import wagtail_factories
from wagtail.images.models import Image
from wagtail.models import Collection

from blog.factories import ProjectPageFactory
from blog.image_collections import page_image_ids
from journal.factories import BlogPostPageFactory
from journal.image_collections import BLOG_COLLECTION_NAME
from journal.models import BlogPostPage

pytestmark = pytest.mark.django_db


def _unfiled_image():
    """An image in the root collection, where the admin puts uploads by default.
    (wagtail_factories.ImageFactory otherwise files it in "Test collection".)"""
    return wagtail_factories.ImageFactory(collection=Collection.get_first_root_node())


def _body(image, carousel, embed):
    return [
        {'type': 'image', 'value': {'image': image.pk, 'caption': ''}},
        {'type': 'carousel', 'value': {'title': '', 'images': [{'image': carousel.pk, 'caption': ''}]}},
        {'type': 'rich_text', 'value': {'title': '', 'text':
            f'<p>Text</p><embed embedtype="image" id="{embed.pk}" format="fullwidth" alt="x"/>'}},
    ]


def _collection_name(image):
    return Image.objects.get(pk=image.pk).collection.name


def _save_in_admin(page, **fields):
    """What saving in the admin does: change the content, then save a revision."""
    page = BlogPostPage.objects.get(pk=page.pk)
    for name, value in fields.items():
        setattr(page, name, value)
    page.save_revision()
    return page


def test_unfiled_images_move_to_blog(blog_index):
    cover, image, carousel, embed = (_unfiled_image() for _ in range(4))
    post = BlogPostPageFactory(parent=blog_index)
    _save_in_admin(post, cover_image=cover, body=_body(image, carousel, embed))
    assert {_collection_name(i) for i in (cover, image, carousel, embed)} == {BLOG_COLLECTION_NAME}


def test_image_in_other_collection_stays(blog_index):
    elsewhere = Collection.get_first_root_node().add_child(name='Some project')
    image = wagtail_factories.ImageFactory(collection=elsewhere)
    post = BlogPostPageFactory(parent=blog_index)
    _save_in_admin(post, cover_image=image)
    assert _collection_name(image) == 'Some project'


def test_removed_image_stays_in_blog(blog_index):
    image = _unfiled_image()
    post = BlogPostPageFactory(parent=blog_index)
    post = _save_in_admin(post, cover_image=image)
    _save_in_admin(post, cover_image=None)
    assert _collection_name(image) == BLOG_COLLECTION_NAME


def test_blog_collection_created_once(blog_index):
    for _ in range(2):
        post = BlogPostPageFactory(parent=blog_index)
        _save_in_admin(post, cover_image=_unfiled_image())
    root = Collection.get_first_root_node()
    assert Collection.objects.filter(name=BLOG_COLLECTION_NAME, depth=root.depth + 1).count() == 1


def test_save_without_revision_moves_nothing(blog_index):
    image = _unfiled_image()
    post = BlogPostPageFactory(parent=blog_index, cover_image=image)
    post.save()
    assert _collection_name(image) == 'Root'


def test_page_image_ids_works_for_posts_and_projects(blog_index, projects_index):
    image = wagtail_factories.ImageFactory()
    post = BlogPostPageFactory(parent=blog_index, cover_image=image)
    project = ProjectPageFactory(parent=projects_index, cover_image=image)
    assert page_image_ids(post) == {image.pk}
    assert page_image_ids(project) == {image.pk}
