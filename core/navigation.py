"""The site's main sections, shared by the nav and the 404 page's "Go to <section>" link."""

NAV_LINKS = [
    ('/', 'Home'),
    ('/pigments/', 'Pigments'),
    ('/projects/', 'Projects'),
    ('/blog/', 'Blog'),
    ('/classes/', 'Classes'),
    ('/about/', 'About'),
]

# What one item in a section is called, for "This pigment doesn't exist" on the
# 404 page. Sections not listed here say "page".
SECTION_ITEMS = {
    '/pigments/': 'pigment',
    '/projects/': 'project',
    '/classes/': 'class',
    '/blog/': 'post',
}


def is_under(path, href):
    """Whether `path` is `href` or inside it. "/" never counts, or it would match every path."""
    return href != '/' and path.startswith(href)


def section_for(path):
    """The nav section `path` is inside, as {"href", "label", "item"}, or None.

    The section's own page doesn't count: if /classes/ itself is missing there is
    nothing to point back to. "/" is never a section (see `is_under`).
    """
    for href, label in NAV_LINKS:
        if is_under(path, href) and path != href:
            return {'href': href, 'label': label, 'item': SECTION_ITEMS.get(href, 'page')}
    return None
