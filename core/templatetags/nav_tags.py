from django import template
from django.utils.safestring import mark_safe

from core.navigation import NAV_LINKS, is_under

register = template.Library()


@register.simple_tag(takes_context=True)
def aria_current(context, href):
    """Mark a nav link as the current location for assistive technology.

    The exact page gets aria-current="page"; a section the visitor is inside
    (e.g. a pigment detail page under /pigments/) gets aria-current="true".
    "/" only ever matches exactly, or it would be current on every page.
    Nothing is current on the 404 page (context flag `not_found`), even under a section.
    """
    request = context.get('request')
    if request is None or context.get('not_found'):
        return ''
    if request.path == href:
        return mark_safe(' aria-current="page"')
    if is_under(request.path, href):
        return mark_safe(' aria-current="true"')
    return ''


@register.simple_tag(takes_context=True)
def nav_links(context):
    """The main nav items, each with its aria-current attribute (desktop and mobile menus share these)."""
    return [
        {'href': href, 'label': label, 'current': aria_current(context, href)}
        for href, label in NAV_LINKS
    ]
