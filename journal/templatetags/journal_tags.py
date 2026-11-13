from django import template
from django.utils.http import urlencode

from journal.models import PIGMENTS_TAG_SLUG, BlogIndexPage, BlogPostPage

register = template.Library()

PIGMENT_NOTES_COUNT = 3


@register.simple_tag
def pigment_notes():
    """The newest live posts tagged Pigments, for the pigment pages' sidebar, as
    {'posts': [...], 'see_all_url': str}, or None when there are none (or the
    tag was deleted), so the page can drop the sidebar and its column."""
    posts = list(
        BlogPostPage.objects.live()
        .filter(tags__slug=PIGMENTS_TAG_SLUG)
        .order_by('-date', '-first_published_at')[:PIGMENT_NOTES_COUNT]
    )
    if not posts:
        return None
    index = BlogIndexPage.objects.live().first()
    see_all = f"{index.url}?{urlencode({'tag': PIGMENTS_TAG_SLUG})}" if index else ''
    return {'posts': posts, 'see_all_url': see_all}
