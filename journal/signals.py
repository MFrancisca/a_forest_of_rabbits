"""File a blog post's images whenever the post is saved in the admin.

Same trigger as blog/signals.py: every admin save, draft or publish, goes through
Page.save_revision(), which ends by saving the page with update_fields including
"latest_revision", while the in-memory page holds the content just saved.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from journal.models import BlogPostPage


@receiver(post_save, sender=BlogPostPage)
def file_post_images_on_save(sender, instance, raw=False, update_fields=None, **kwargs):
    if raw or not update_fields or 'latest_revision' not in update_fields:
        return
    from journal.image_collections import file_post_images

    file_post_images(instance)
