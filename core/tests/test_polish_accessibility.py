"""Accessibility polish (issue #13): formula notation, citation links,
new-tab warnings, and machine-readable dates."""
import datetime
import re

import pytest
from django.urls import reverse

from blog.factories import ProjectPageFactory
from pigments.factories import (
    FormulaFactory,
    FormulaPartFactory,
    PaintFactory,
    PigmentFactory,
    PigmentManuscriptFactory,
    SourceFactory,
)

pytestmark = pytest.mark.django_db


def _detail(client, pigment):
    response = client.get(reverse('pigments:detail', args=[pigment.pk]))
    assert response.status_code == 200
    return response.content.decode()


def _notation(html):
    return re.search(r'<p class="text-2xl font-mono[^"]*">(.*?)</p>', html, re.S).group(1)


def _spoken(fragment):
    """Roughly what a screen reader says: drop aria-hidden elements, then all tags."""
    fragment = re.sub(r'<(\w+)[^>]*aria-hidden="true"[^>]*>.*?</\1>', '', fragment, flags=re.S)
    return ' '.join(re.sub(r'<[^>]+>', ' ', fragment).split())


def _visible(fragment):
    """Roughly what is seen: drop sr-only spans, then all tags."""
    fragment = re.sub(r'<span class="sr-only">.*?</span>', '', fragment, flags=re.S)
    return re.sub(r'\s+', '', re.sub(r'<[^>]+>', '', fragment))


# --- formula notation -----------------------------------------------------------

def test_formula_notation_reads_paint_names_and_trace(client):
    pigment = PigmentFactory()
    formula = FormulaFactory(pigment=pigment)
    FormulaPartFactory(formula=formula, parts=2, paint=PaintFactory(name='Ultramarine', abbreviation='U'))
    FormulaPartFactory(formula=formula, parts=None, is_trace=True,
                       paint=PaintFactory(name='Lead White', abbreviation='W'))

    notation = _notation(_detail(client, pigment))

    assert _spoken(notation) == '2 Ultramarine + trace of Lead White'
    assert _visible(notation) == '2U+ΔW'  # compact notation unchanged on screen
    assert '<abbr title="Ultramarine" aria-hidden="true">U</abbr>' in notation
    assert '<abbr title="Lead White" aria-hidden="true">W</abbr>' in notation


# --- citations ----------------------------------------------------------------------

def test_table_source_links_to_its_reference_entry_without_tooltips(client):
    pigment = PigmentFactory()
    with_url = SourceFactory(authors='Bicchieri, M.', year=2014, doi='', url='https://arxiv.org/abs/1404.6414')
    no_link = SourceFactory(authors='Smith, J.', year=2001, doi='', url='')
    PigmentManuscriptFactory(pigment=pigment, source=with_url)
    PigmentManuscriptFactory(pigment=pigment, source=no_link)

    html = _detail(client, pigment)
    table = html.split('<table', 1)[1].split('</table>', 1)[0]

    for source in (with_url, no_link):
        assert re.search(rf'<a id="cite-\d+" href="#ref-{source.pk}"[^>]*>{re.escape(source.short_label)}</a>', table)
        assert re.search(rf'<li id="ref-{source.pk}"', html)
    assert 'title=' not in table
    assert 'target="_blank"' not in table  # the external link lives in References


def test_reference_entries_are_valid_jump_targets(client):
    pigment = PigmentFactory()
    source = SourceFactory()
    pigment.sources.add(source)
    pigment.save()  # ParentalManyToMany: add() is in-memory until save

    html = _detail(client, pigment)
    entry = re.search(rf'<li id="ref-{source.pk}"[^>]*>', html).group(0)
    assert 'tabindex="-1"' in entry and 'target:bg-stone-100' in entry


# --- new-tab links -------------------------------------------------------------------

def test_new_tab_links_warn_screen_reader_users(client):
    pigment = PigmentFactory()
    pigment.sources.add(SourceFactory(doi='10.1000/x', url=''))
    pigment.save()

    html = _detail(client, pigment)
    links = re.findall(r'<a [^>]*target="_blank"[^>]*>.*?</a>', html, re.S)
    assert links
    for link in links:
        assert '<span class="sr-only"> (opens in new tab)</span>' in link
        assert re.search(r'<svg[^>]*aria-hidden="true"', link)


# --- dates ------------------------------------------------------------------------------

def test_project_dates_are_machine_readable(client, projects_index):
    project = ProjectPageFactory(parent=projects_index, date=datetime.date(2025, 3, 7))

    page_html = client.get(project.url).content.decode()
    assert '<time datetime="2025-03-07" class="text-sm text-gray-500">7 Mar 2025</time>' in page_html

    index_html = client.get(projects_index.url).content.decode()
    assert '<time datetime="2025-03" class="text-sm text-gray-500">Mar 2025</time>' in index_html


# --- back to table ------------------------------------------------------------------------

def _reference(html, source):
    return html.split(f'<li id="ref-{source.pk}"', 1)[1].split('</li>', 1)[0]


def test_reference_cited_once_links_back_to_its_table_row(client):
    pigment = PigmentFactory()
    source = SourceFactory()
    row = PigmentManuscriptFactory(pigment=pigment, source=source)

    html = _detail(client, pigment)

    assert re.search(rf'<a id="cite-{row.pk}" href="#ref-{source.pk}"', html)
    entry = _reference(html, source)
    back = re.search(r'<a href="#cite-(\d+)"[^>]*>(.*?)</a>', entry, re.S)
    assert back.group(1) == str(row.pk)
    assert _spoken(back.group(2)) == f'Back to table ({row.manuscript.name})'


def test_reference_cited_by_several_rows_links_back_to_each(client):
    pigment = PigmentFactory()
    source = SourceFactory()
    first = PigmentManuscriptFactory(pigment=pigment, source=source, sort_order=0)
    second = PigmentManuscriptFactory(pigment=pigment, source=source, sort_order=1)

    html = _detail(client, pigment)
    entry = _reference(html, source)

    backs = re.findall(r'<a href="#cite-(\d+)"[^>]*>(.*?)</a>', entry, re.S)
    assert backs == [(str(first.pk), first.manuscript.name), (str(second.pk), second.manuscript.name)]
    assert 'Back to table:' in entry
    for row in (first, second):
        assert f'id="cite-{row.pk}"' in html


def test_back_links_show_page_reference_to_tell_same_manuscript_apart(client):
    pigment = PigmentFactory()
    source = SourceFactory()
    first = PigmentManuscriptFactory(pigment=pigment, source=source, page_reference='f. 3r', sort_order=0)
    PigmentManuscriptFactory(pigment=pigment, source=source, manuscript=first.manuscript,
                             page_reference='f. 9v', sort_order=1)

    entry = _reference(_detail(client, pigment), source)
    names = [text for _, text in re.findall(r'<a href="#cite-(\d+)"[^>]*>(.*?)</a>', entry, re.S)]
    assert names == [f'{first.manuscript.name} (f. 3r)', f'{first.manuscript.name} (f. 9v)']


def test_general_reference_has_no_back_link(client):
    pigment = PigmentFactory()
    source = SourceFactory()
    pigment.sources.add(source)
    pigment.save()

    entry = _reference(_detail(client, pigment), source)
    assert '#cite-' not in entry and 'Back to table' not in entry
