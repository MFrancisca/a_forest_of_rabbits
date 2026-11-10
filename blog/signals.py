"""Sync a project page's image collection whenever the page is saved.

Every admin save, draft or publish, goes through Page.save_revision(), which
ends by saving the page with update_fields including "latest_revision". At that
point the in-memory page holds the content just saved (the draft, not the live
row), so that's what gets synced.

Syncing on Revision post_save instead would be wrong: copying a page re-saves
every old revision of the original, and each would sync (and move images) in
turn. The copy reaches save_revision() once, for its final revision.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from blog.models import ProjectPage


@receiver(post_save, sender=ProjectPage)
def sync_project_collection_on_save(sender, instance, raw=False, update_fields=None, **kwargs):
    if raw or not update_fields or 'latest_revision' not in update_fields:
        return
    from blog.image_collections import sync_project_collection

    sync_project_collection(instance)
