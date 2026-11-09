from django.shortcuts import render

from core.navigation import section_for


def page_not_found(request, exception=None):
    """Site 404 (handler404). Used for unknown URLs, missing Wagtail pages and
    get_object_or_404 misses alike. Only active when DEBUG is False."""
    context = {
        'section': section_for(request.path),
        # Tells the nav not to mark any section as current: this isn't a real page.
        'not_found': True,
    }
    return render(request, '404.html', context, status=404)
