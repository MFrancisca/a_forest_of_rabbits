"""Management command to scrape Google Sites pages and import them as Wagtail pages."""
import datetime
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand

SCRAPE_CONFIG = [
    ('https://www.unanuovasperanza.art/home', None, 'about'),
    ('https://www.unanuovasperanza.art/projects/scrolls/qc-sonja-iii', 'Calligraphy & Illumination', 'project'),
    ('https://www.unanuovasperanza.art/projects/scrolls/court-baronies-for-elfseas-founding-bb', 'Calligraphy & Illumination', 'project'),
    ('https://www.unanuovasperanza.art/projects/scrolls/rainbow-triskele-sable-swap-2024', 'Calligraphy & Illumination', 'project'),
    ('https://www.unanuovasperanza.art/projects/scrolls/collaborations/queens-champion-for-hrm-gilyan-iii', 'Calligraphy & Illumination', 'project'),
    ('https://www.unanuovasperanza.art/projects/scrolls/collaborations/bjornsborg-champions-spring-2025', 'Calligraphy & Illumination', 'project'),
    ('https://www.unanuovasperanza.art/projects/garb/handsewn-camicia', 'Clothing', 'project'),
    ('https://www.unanuovasperanza.art/projects/armor/leather-fencing-doublet', 'Armor', 'project'),
    ('https://www.unanuovasperanza.art/projects/armor/rotella', 'Armor', 'project'),
    ('https://www.unanuovasperanza.art/research/classes', 'Classes', 'project'),
    ('https://www.unanuovasperanza.art/archive/scribal', 'Archive', 'project'),
    ('https://www.unanuovasperanza.art/archive/weaving', 'Archive', 'project'),
]


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

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would be created without touching the database.',
        )

    def handle(self, *args, **options):
        from playwright.sync_api import sync_playwright

        dry_run = options.get('dry_run', False)
        created = 0
        skipped = 0
        failed = 0

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            for url, category, page_type in SCRAPE_CONFIG:
                self.stdout.write(f'\u2192 Scraping: {url}')
                try:
                    pw_page = browser.new_page()
                    pw_page.goto(url, wait_until='networkidle')
                    html = pw_page.content()
                    pw_page.close()

                    title = extract_title(html)
                    slug = slug_from_url(url)
                    body_html = extract_body_html(html, slug)

                    if page_type == 'about':
                        if dry_run:
                            self.stdout.write(f'[dry-run] Would update AboutPage with {len(body_html)} chars')
                        else:
                            update_about_page(html)
                            self.stdout.write('\u2713 Updated: AboutPage')
                    elif page_type == 'project':
                        if dry_run:
                            self.stdout.write(f'[dry-run] Would create ProjectPage: {title} ({category})')
                        else:
                            result = create_project_page(
                                title=title,
                                slug=slug,
                                body_html=body_html,
                                category_name=category,
                            )
                            if result == 'created':
                                created += 1
                            else:
                                skipped += 1
                except Exception as e:
                    self.stdout.write(f'\u2717 Failed: {url} \u2014 {e}')
                    failed += 1
            browser.close()

        self.stdout.write('\u2500' * 33)
        self.stdout.write('Scrape complete')
        self.stdout.write(f'Created:  {created}')
        self.stdout.write(f'Skipped:  {skipped} (existing)')
        self.stdout.write(f'Failed:   {failed}')
        self.stdout.write('\u2500' * 33)
