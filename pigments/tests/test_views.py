"""
Failing test stubs for the pigment list view — RED phase (02-01).

All 11 tests are collected with no import errors.
They fail with assertion errors (not ImportError/ModuleNotFoundError).
Plan 02-02 (GREEN) will implement the view to make these pass.
"""
import re

import pytest
from django.test import Client
from django.urls import reverse

from pigments.factories import (
    ColorFamilyFactory,
    CountryFactory,
    FormulaFactory,
    ManuscriptFactory,
    PigmentFactory,
    PigmentManuscriptFactory,
)


# ---------------------------------------------------------------------------
# 1. Basic status check
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_pigment_list_returns_200():
    client = Client()
    url = reverse("pigments:list")
    response = client.get(url)
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# 2. Unfiltered list shows all pigments
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_unfiltered_list_shows_all():
    PigmentFactory(with_formula=True)
    PigmentFactory(with_formula=True)
    PigmentFactory(with_formula=True)
    client = Client()
    url = reverse("pigments:list")
    response = client.get(url)
    assert response.context["filtered_count"] == 3


# ---------------------------------------------------------------------------
# 3. Single color family filter
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_color_family_filter():
    color_a = ColorFamilyFactory()
    color_b = ColorFamilyFactory()
    pigment_a = PigmentFactory(with_formula=True, color_family=color_a)
    PigmentFactory(with_formula=True, color_family=color_b)
    client = Client()
    url = reverse("pigments:list")
    response = client.get(url, {"color": color_a.pk})
    pigments = list(response.context["pigments"])
    assert pigment_a in pigments
    assert len(pigments) == 1


# ---------------------------------------------------------------------------
# 4. Multi-value OR within a single dimension
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_multivalue_or_within_dimension():
    color_a = ColorFamilyFactory()
    color_b = ColorFamilyFactory()
    color_c = ColorFamilyFactory()
    p_a = PigmentFactory(with_formula=True, color_family=color_a)
    p_b = PigmentFactory(with_formula=True, color_family=color_b)
    PigmentFactory(with_formula=True, color_family=color_c)
    client = Client()
    url = reverse("pigments:list")
    response = client.get(url, {"color": [color_a.pk, color_b.pk]})
    pigments = list(response.context["pigments"])
    assert p_a in pigments
    assert p_b in pigments
    assert len(pigments) == 2


# ---------------------------------------------------------------------------
# 5. AND across dimensions (color AND country)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_and_across_dimensions():
    color_x = ColorFamilyFactory()
    color_y = ColorFamilyFactory()
    country_a = CountryFactory()
    country_b = CountryFactory()

    manuscript_a = ManuscriptFactory(country=country_a)
    manuscript_b = ManuscriptFactory(country=country_b)

    # Only this pigment matches both color_x AND country_a
    p_match = PigmentFactory(with_formula=True, color_family=color_x)
    PigmentManuscriptFactory(pigment=p_match, manuscript=manuscript_a)

    # Matches color_x but not country_a
    p_color_only = PigmentFactory(with_formula=True, color_family=color_x)
    PigmentManuscriptFactory(pigment=p_color_only, manuscript=manuscript_b)

    # Matches country_a but not color_x
    p_country_only = PigmentFactory(with_formula=True, color_family=color_y)
    PigmentManuscriptFactory(pigment=p_country_only, manuscript=manuscript_a)

    client = Client()
    url = reverse("pigments:list")
    response = client.get(url, {"color": color_x.pk, "country": country_a.pk})
    pigments = list(response.context["pigments"])
    assert p_match in pigments
    assert len(pigments) == 1


# ---------------------------------------------------------------------------
# 6. Century overlap filter
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_century_overlap_filter():
    manuscript = ManuscriptFactory(date_start=820, date_end=870)
    pigment = PigmentFactory(with_formula=True)
    PigmentManuscriptFactory(pigment=pigment, manuscript=manuscript)

    # Pigment in a manuscript outside the century range — should not appear
    outside_manuscript = ManuscriptFactory(date_start=1000, date_end=1100)
    other_pigment = PigmentFactory(with_formula=True)
    PigmentManuscriptFactory(pigment=other_pigment, manuscript=outside_manuscript)

    client = Client()
    url = reverse("pigments:list")
    response = client.get(url, {"century": 800})
    pigments = list(response.context["pigments"])
    assert pigment in pigments
    assert other_pigment not in pigments


# ---------------------------------------------------------------------------
# 7. Empty results filter
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_empty_results_filter():
    PigmentFactory(with_formula=True)
    client = Client()
    url = reverse("pigments:list")
    response = client.get(url, {"color": 99999})
    assert response.status_code == 200
    assert response.context["filtered_count"] == 0


# ---------------------------------------------------------------------------
# 8. No duplicates when pigment linked to multiple manuscripts in same country
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_combined_filter_m2m_no_duplicates():
    country = CountryFactory()
    manuscript_1 = ManuscriptFactory(country=country)
    manuscript_2 = ManuscriptFactory(country=country)
    pigment = PigmentFactory(with_formula=True)
    PigmentManuscriptFactory(pigment=pigment, manuscript=manuscript_1)
    PigmentManuscriptFactory(pigment=pigment, manuscript=manuscript_2)

    client = Client()
    url = reverse("pigments:list")
    response = client.get(url, {"country": country.pk})
    assert response.context["filtered_count"] == 1


# ---------------------------------------------------------------------------
# 9. HTMX request returns partial template
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_htmx_request_returns_partial():
    client = Client()
    url = reverse("pigments:list")
    response = client.get(url, HTTP_HX_REQUEST="true")
    template_names = [t.name for t in response.templates]
    assert "pigments/pigment_list_partial.html" in template_names
    assert "pigments/pigment_list.html" not in template_names


# ---------------------------------------------------------------------------
# 10. HTMX history restore returns full page
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_history_restore_returns_full_page():
    client = Client()
    url = reverse("pigments:list")
    response = client.get(
        url,
        HTTP_HX_REQUEST="true",
        HTTP_HX_HISTORY_RESTORE_REQUEST="true",
    )
    template_names = [t.name for t in response.templates]
    assert "pigments/pigment_list.html" in template_names


# ---------------------------------------------------------------------------
# 11. Direct GET (no HTMX) returns full page
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_direct_get_returns_full_page():
    client = Client()
    url = reverse("pigments:list")
    response = client.get(url)
    template_names = [t.name for t in response.templates]
    assert "pigments/pigment_list.html" in template_names


# ---------------------------------------------------------------------------
# Phase 03-01 tests: pigment detail view (RED stubs)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_pigment_detail_returns_200():
    pigment = PigmentFactory()
    client = Client()
    url = reverse('pigments:detail', kwargs={'pk': pigment.pk})
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_pigment_detail_404():
    client = Client()
    url = reverse('pigments:detail', kwargs={'pk': 99999})
    response = client.get(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_pigment_detail_shows_name():
    pigment = PigmentFactory()
    client = Client()
    url = reverse('pigments:detail', kwargs={'pk': pigment.pk})
    response = client.get(url)
    assert pigment.name.encode() in response.content


@pytest.mark.django_db
def test_pigment_detail_shows_description():
    pigment = PigmentFactory(description='A rare blue pigment from lapis lazuli.')
    client = Client()
    url = reverse('pigments:detail', kwargs={'pk': pigment.pk})
    response = client.get(url)
    assert b'A rare blue pigment from lapis lazuli.' in response.content


@pytest.mark.django_db
def test_detail_shows_manuscript_links():
    pigment = PigmentFactory()
    manuscript = ManuscriptFactory(name='Book of Kells')
    PigmentManuscriptFactory(pigment=pigment, manuscript=manuscript)
    client = Client()
    url = reverse('pigments:detail', kwargs={'pk': pigment.pk})
    response = client.get(url)
    assert b'Book of Kells' in response.content


@pytest.mark.django_db
def test_detail_no_manuscript_section_when_empty():
    pigment = PigmentFactory()
    client = Client()
    url = reverse('pigments:detail', kwargs={'pk': pigment.pk})
    response = client.get(url)
    assert b'Manuscript' not in response.content


@pytest.mark.django_db
def test_detail_context_has_formulas():
    pigment = PigmentFactory()
    FormulaFactory(pigment=pigment)
    client = Client()
    url = reverse('pigments:detail', kwargs={'pk': pigment.pk})
    response = client.get(url)
    assert 'formulas' in response.context


@pytest.mark.django_db
def test_manuscript_filter_shows_manuscript_names():
    PigmentManuscriptFactory(
        pigment=PigmentFactory(with_formula=True),
        manuscript=ManuscriptFactory(name='Lindisfarne Gospels'),
    )
    client = Client()
    response = client.get(reverse('pigments:list'))
    assert 'Lindisfarne Gospels' in response.content.decode()


@pytest.mark.django_db
def test_selected_filters_are_checked_on_full_page_load():
    import re
    picked = ManuscriptFactory(name='Book of Durrow')
    other = ManuscriptFactory(name='Voynich Manuscript')
    # Only manuscripts linked to a listed pigment appear as filter options.
    for ms in (picked, other):
        PigmentManuscriptFactory(pigment=PigmentFactory(with_formula=True), manuscript=ms)
    client = Client()
    response = client.get(reverse('pigments:list'), {'manuscript': picked.id})
    html = response.content.decode()

    def is_checked(name, value):
        tag = re.search(rf'<input[^>]*name="{name}"[^>]*value="{value}"[^>]*>', html)
        return tag is not None and 'checked' in tag.group(0)

    assert is_checked('manuscript', picked.id)
    assert not is_checked('manuscript', other.id)


@pytest.mark.django_db
def test_detail_shows_link_source_and_references():
    from pigments.factories import SourceFactory
    pigment = PigmentFactory()
    cited = SourceFactory(authors='Bicchieri, M.', year=2014, title='Codex Rossanensis study', doi='',
                          url='https://arxiv.org/abs/1404.6414')
    general = SourceFactory(title='General pigment reference')
    PigmentManuscriptFactory(pigment=pigment, source=cited, source_detail='Table 1')
    PigmentManuscriptFactory(pigment=pigment, source=cited)  # cited twice → listed once
    pigment.sources.add(general)
    pigment.save()

    response = Client().get(reverse('pigments:detail', kwargs={'pk': pigment.pk}))
    html = response.content.decode()

    assert response.context['references'] == [cited, general]
    assert 'Bicchieri 2014' in html
    assert 'https://arxiv.org/abs/1404.6414' in html
    assert 'Table 1' in html
    assert f'https://doi.org/{general.doi}' in html


# ---------------------------------------------------------------------------
# Only pigments with formulas are listed
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_list_hides_pigments_without_formulas():
    with_formula = PigmentFactory(with_formula=True)
    without_formula = PigmentFactory()
    response = Client().get(reverse("pigments:list"))
    pigments = list(response.context["pigments"])
    assert with_formula in pigments
    assert without_formula not in pigments
    assert response.context["filtered_count"] == 1
    assert response.context["total_count"] == 1


@pytest.mark.django_db
def test_list_shows_pigment_with_several_formulas_once():
    pigment = PigmentFactory(with_formula=True)
    FormulaFactory(pigment=pigment)
    response = Client().get(reverse("pigments:list"))
    assert list(response.context["pigments"]) == [pigment]


@pytest.mark.django_db
def test_filters_also_hide_pigments_without_formulas():
    color = ColorFamilyFactory()
    listed = PigmentFactory(with_formula=True, color_family=color)
    PigmentFactory(color_family=color)
    response = Client().get(reverse("pigments:list"), {"color": color.pk})
    assert list(response.context["pigments"]) == [listed]


@pytest.mark.django_db
def test_detail_still_works_for_pigment_without_formulas():
    pigment = PigmentFactory()
    response = Client().get(reverse("pigments:detail", args=[pigment.pk]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_filter_options_only_include_listed_pigments():
    color_listed, color_hidden = ColorFamilyFactory(), ColorFamilyFactory()
    country_listed, country_hidden = CountryFactory(), CountryFactory()
    ms_listed = ManuscriptFactory(country=country_listed, date_start=800, date_end=850)
    ms_hidden = ManuscriptFactory(country=country_hidden, date_start=1400, date_end=1450)

    listed = PigmentFactory(with_formula=True, color_family=color_listed)
    hidden = PigmentFactory(color_family=color_hidden)
    PigmentManuscriptFactory(pigment=listed, manuscript=ms_listed)
    PigmentManuscriptFactory(pigment=hidden, manuscript=ms_hidden)
    # A second link to the same manuscript must not duplicate options.
    PigmentManuscriptFactory(pigment=PigmentFactory(with_formula=True, color_family=color_listed), manuscript=ms_listed)

    ctx = Client().get(reverse("pigments:list")).context
    assert list(ctx["color_families"]) == [color_listed]
    assert listed.pigment_family in ctx["pigment_families"]
    assert hidden.pigment_family not in ctx["pigment_families"]
    assert list(ctx["countries"]) == [country_listed]
    assert list(ctx["manuscripts"]) == [ms_listed]
    assert [b["start"] for b in ctx["century_buckets"]] == [800]


@pytest.mark.django_db
def test_detail_shows_formula_image_when_set():
    import wagtail_factories
    pigment = PigmentFactory()
    FormulaFactory(pigment=pigment, image=wagtail_factories.ImageFactory())
    html = Client().get(reverse('pigments:detail', args=[pigment.pk])).content.decode()
    assert 'class="formula-image' in html


@pytest.mark.django_db
def test_detail_has_no_formula_image_when_unset():
    pigment = PigmentFactory()
    FormulaFactory(pigment=pigment)
    html = Client().get(reverse('pigments:detail', args=[pigment.pk])).content.decode()
    assert 'class="formula-image' not in html


@pytest.mark.django_db
def test_detail_links_back_to_the_pigment_list():
    """A plain link to the list; a script upgrades it to the filtered list the visitor came from."""
    pigment = PigmentFactory()
    html = Client().get(reverse('pigments:detail', kwargs={'pk': pigment.pk})).content.decode()
    link = re.search(r'<a href="([^"]+)" id="back-to-list"[^>]*>(.*?)</a>', html, re.S)
    assert link, 'back-to-list link not found'
    assert link.group(1) == reverse('pigments:list')
    assert 'Back to pigments' in link.group(2)
    assert html.index('id="back-to-list"') < html.index('<h1')
    assert "document.getElementById('back-to-list')" in html
