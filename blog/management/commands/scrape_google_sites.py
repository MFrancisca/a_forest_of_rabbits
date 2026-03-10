"""Management command to scrape Google Sites pages and import them as Wagtail pages."""
import datetime
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand


def extract_title(html: str) -> str:
    """Extract the page title from HTML.

    Returns H1 text if present; otherwise parses the <title> tag and strips
    the site-name prefix (e.g. "Site - Classes" -> "Classes").
    """
    soup = BeautifulSoup(html, 'lxml')
    h1 = soup.find('h1')
    if h1:
        return h1.get_text(strip=True)
    title_tag = soup.find('title')
    if title_tag:
        # "Forest of Rabbits - Classes" -> "Classes"
        parts = title_tag.get_text().split(' - ')
        return parts[-1].strip() if len(parts) > 1 else parts[0].strip()
    return ''


def extract_body_html(html: str, slug: str) -> str:
    """Extract body HTML from a Google Sites page.

    Converts paragraphs to <p> tags, h2/h3 headings to <h2>/<h3> tags, and
    replaces each <img> element with an image-placeholder paragraph using the
    slug and an incrementing counter.
    """
    soup = BeautifulSoup(html, 'lxml')

    body_parts = []
    img_counter = 1

    for tag in soup.find_all(['h2', 'h3', 'p', 'img']):
        if tag.name in ('h2', 'h3'):
            body_parts.append(f'<{tag.name}>{tag.get_text(strip=True)}</{tag.name}>')
        elif tag.name == 'p':
            text = tag.get_text(strip=True)
            if text:
                body_parts.append(f'<p>{text}</p>')
        elif tag.name == 'img':
            placeholder = f'<p>\U0001f5bc\ufe0f [IMAGE: {slug}-{img_counter}]</p>'
            body_parts.append(placeholder)
            img_counter += 1

    return '\n'.join(body_parts)


def slug_from_url(url: str) -> str:
    """Derive a URL slug from the last path segment of a Google Sites URL."""
    path = urlparse(url).path.rstrip('/')
    return path.split('/')[-1]


def create_project_page(title, slug, body_html, date=None, category_name=None):
    """Create and publish a ProjectPage under ProjectsIndexPage.

    Returns 'skipped' if a page with the given slug already exists.
    Returns 'created' after successfully creating and publishing the page.
    """
    from blog.models import Category, ProjectPage, ProjectsIndexPage

    if ProjectPage.objects.filter(slug=slug).exists():
        return 'skipped'

    if date is None:
        date = datetime.date.today()

    category = None
    if category_name:
        category, _ = Category.objects.get_or_create(name=category_name)

    index = ProjectsIndexPage.objects.first()

    page = ProjectPage(
        title=title,
        slug=slug,
        date=date,
        category=category,
        body=body_html,
    )
    index.add_child(instance=page)
    page.save_revision().publish()
    return 'created'


def update_about_page(html: str) -> None:
    """Overwrite AboutPage.body with extracted body HTML and publish the revision."""
    from blog.models import AboutPage

    body_html = extract_body_html(html, slug='about')
    about = AboutPage.objects.first()
    about.body = body_html
    about.save_revision().publish()


class Command(BaseCommand):
    help = "Scrape pages from Google Sites and import them as Wagtail pages."

    def handle(self, *args, **options):
        pass
