from django.utils.translation import ngettext
from wagtail import hooks
from wagtail.models import Collection

from blog.models import ProjectCollection


@hooks.register('describe_collection_contents')
def describe_project_pages(collection):
    """Count the project pages whose image collection is this one or below it, so
    Wagtail refuses to delete it (its "not empty" screen) instead of failing on the
    PROTECT link. Deleting a collection also deletes the collections under it, so
    "Projects" is protected while any project collection exists."""
    subtree = Collection.objects.filter(path__startswith=collection.path)
    count = ProjectCollection.objects.filter(collection__in=subtree).count()
    if count:
        return {
            'count': count,
            'count_text': ngettext('%(count)s project page', '%(count)s project pages', count)
            % {'count': count},
        }
