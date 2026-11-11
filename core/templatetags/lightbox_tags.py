"""Renditions for images that open the lightbox, skipping images that can't be shown.

    {% load lightbox_tags %}
    {% lightbox_renditions page.cover_image "fill-800x600" as r %}
    {% if r %}{% include "includes/lightbox_opener.html" with src=r.thumb.url full=r.full.url ... %}{% endif %}

    {% for slide in block.value.slides|lightbox_slides:"fill-800x600" %}
      {{ slide.thumb.url }} {{ slide.full.url }} {{ slide.caption }} {{ slide.image }}
    {% endfor %}

An image is skipped when it was deleted (None) or its original file is missing
from storage. Wagtail's {% image %} renders the latter as a broken "not-found"
placeholder, which would show a broken thumbnail and open an empty lightbox.
"""
from django import template
from wagtail.images.models import SourceImageIOError

register = template.Library()

FULL_SPEC = 'max-1600x1600'


@register.simple_tag
def lightbox_renditions(image, thumb_spec):
    """{'thumb': rendition, 'full': rendition}, or None if the image can't be shown."""
    if not image:
        return None
    try:
        # One call: existing renditions are looked up together, not one query each.
        renditions = image.get_renditions(thumb_spec, FULL_SPEC)
    except SourceImageIOError:
        return None
    return {'thumb': renditions[thumb_spec], 'full': renditions[FULL_SPEC]}


@register.filter
def lightbox_slides(slides, thumb_spec):
    """Carousel slides that can be shown, each with its renditions attached.
    Filtering before rendering keeps slide indexes, dots and "N of M" in sync."""
    shown = []
    for item in slides:
        renditions = lightbox_renditions(item['image'], thumb_spec)
        if renditions:
            shown.append({'image': item['image'], 'caption': item['caption'], **renditions})
    return shown
