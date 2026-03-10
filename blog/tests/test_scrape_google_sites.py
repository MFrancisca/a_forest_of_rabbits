"""RED-state test stubs for the scrape_google_sites management command.

All tests here are expected to FAIL with NotImplementedError until Plan 02
implements the helper functions.
"""
import pytest
from blog.management.commands.scrape_google_sites import (
    extract_title,
    extract_body_html,
    slug_from_url,
    create_project_page,
    update_about_page,
)

# ---------------------------------------------------------------------------
# Fixture HTML strings used by pure-function tests
# ---------------------------------------------------------------------------

TITLE_HTML = '<html><body><h1>Queens Champion for Sonja III</h1><p>body</p></body></html>'
FALLBACK_HTML = '<html><head><title>Site - Classes</title></head><body><p>no h1</p></body></html>'
BODY_PARA_HTML = '<html><body><p>First paragraph.</p><p>Second paragraph.</p></body></html>'
BODY_HEADING_HTML = '<html><body><h2>Section One</h2><p>content</p></body></html>'
BODY_IMG_HTML = (
    '<html><body>'
    '<p>before</p>'
    '<img src="image1.jpg" />'
    '<p>between</p>'
    '<img src="image2.jpg" />'
    '</body></html>'
)


# ---------------------------------------------------------------------------
# Pure-function tests (no DB)
# ---------------------------------------------------------------------------


def test_extract_title_from_h1():
    """extract_title returns H1 text when an H1 element is present."""
    result = extract_title(TITLE_HTML)
    assert result == "Queens Champion for Sonja III"


def test_extract_title_fallback_to_title_tag():
    """extract_title parses <title> 'Site - Classes' -> 'Classes' when no H1."""
    result = extract_title(FALLBACK_HTML)
    assert result == "Classes"


def test_extract_body_paragraphs():
    """extract_body_html wraps body paragraphs in <p> tags."""
    result = extract_body_html(BODY_PARA_HTML, "my-slug")
    assert "<p>First paragraph.</p>" in result
    assert "<p>Second paragraph.</p>" in result


def test_extract_body_headings():
    """extract_body_html converts h2 text to <h2>text</h2>."""
    result = extract_body_html(BODY_HEADING_HTML, "my-slug")
    assert "<h2>Section One</h2>" in result


def test_extract_body_image_placeholders():
    """extract_body_html inserts <p>image placeholder</p> for each img, counter increments."""
    result = extract_body_html(BODY_IMG_HTML, "my-slug")
    assert "<p>\U0001f5bc\ufe0f [IMAGE: my-slug-1]</p>" in result
    assert "<p>\U0001f5bc\ufe0f [IMAGE: my-slug-2]</p>" in result


def test_slug_from_url_basic():
    """slug_from_url returns the last path segment of a Google Sites URL."""
    result = slug_from_url(
        "https://www.unanuovasperanza.art/projects/scrolls/qc-sonja-iii"
    )
    assert result == "qc-sonja-iii"


# ---------------------------------------------------------------------------
# DB tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_create_project_page_creates_page(projects_index):
    """create_project_page() creates a published ProjectPage under ProjectsIndexPage."""
    from blog.models import ProjectPage

    create_project_page(
        title="Queens Champion for Sonja III",
        slug="qc-sonja-iii",
        body_html="<p>Body text.</p>",
    )
    assert ProjectPage.objects.filter(slug="qc-sonja-iii").exists()


@pytest.mark.django_db
def test_create_project_page_skips_existing(projects_index):
    """create_project_page() returns 'skipped' when slug already exists and does not duplicate."""
    from blog.models import ProjectPage

    # Create once
    create_project_page(
        title="Queens Champion for Sonja III",
        slug="qc-sonja-iii",
        body_html="<p>Body text.</p>",
    )
    # Attempt duplicate
    result = create_project_page(
        title="Queens Champion for Sonja III",
        slug="qc-sonja-iii",
        body_html="<p>Different body.</p>",
    )
    assert result == "skipped"
    assert ProjectPage.objects.filter(slug="qc-sonja-iii").count() == 1


@pytest.mark.django_db
def test_update_about_page(about_page):
    """update_about_page overwrites AboutPage.body and publishes the revision."""
    from blog.models import AboutPage

    html = '<html><body><h1>About</h1><p>We are an art collective.</p></body></html>'
    update_about_page(html)

    page = AboutPage.objects.get(pk=about_page.pk)
    page.refresh_from_db()
    assert "We are an art collective." in page.body
