"""Management command to scrape Google Sites pages and import them as Wagtail pages."""
from django.core.management.base import BaseCommand


def extract_title(html):
    """Extract the page title from HTML.

    Returns H1 text if present; otherwise parses the <title> tag and strips
    the site-name prefix (e.g. "Site - Classes" -> "Classes").
    """
    raise NotImplementedError


def extract_body_html(html, slug):
    """Extract body HTML from a Google Sites page.

    Converts paragraphs to <p> tags, h2 headings to <h2> tags, and replaces
    each <img> element with an image-placeholder paragraph using the slug and
    an incrementing counter.
    """
    raise NotImplementedError


def slug_from_url(url):
    """Derive a URL slug from the last path segment of a Google Sites URL."""
    raise NotImplementedError


def create_project_page(title, slug, body_html, date=None, category_name=None):
    """Create and publish a ProjectPage under ProjectsIndexPage.

    Returns 'skipped' if a page with the given slug already exists.
    """
    raise NotImplementedError


def update_about_page(html):
    """Overwrite AboutPage.body with extracted body HTML and publish the revision."""
    raise NotImplementedError


class Command(BaseCommand):
    help = "Scrape pages from Google Sites and import them as Wagtail pages."

    def handle(self, *args, **options):
        pass
