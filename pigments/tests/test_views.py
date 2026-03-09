"""
Failing test stubs for the pigment list view — RED phase (02-01).

All 11 tests are collected with no import errors.
They fail with assertion errors (not ImportError/ModuleNotFoundError).
Plan 02-02 (GREEN) will implement the view to make these pass.
"""
import pytest
from django.test import Client
from django.urls import reverse

from pigments.factories import (
    ColorFamilyFactory,
    CountryFactory,
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
    PigmentFactory()
    PigmentFactory()
    PigmentFactory()
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
    pigment_a = PigmentFactory(color_family=color_a)
    PigmentFactory(color_family=color_b)
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
    p_a = PigmentFactory(color_family=color_a)
    p_b = PigmentFactory(color_family=color_b)
    PigmentFactory(color_family=color_c)
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
    p_match = PigmentFactory(color_family=color_x)
    PigmentManuscriptFactory(pigment=p_match, manuscript=manuscript_a)

    # Matches color_x but not country_a
    p_color_only = PigmentFactory(color_family=color_x)
    PigmentManuscriptFactory(pigment=p_color_only, manuscript=manuscript_b)

    # Matches country_a but not color_x
    p_country_only = PigmentFactory(color_family=color_y)
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
    pigment = PigmentFactory()
    PigmentManuscriptFactory(pigment=pigment, manuscript=manuscript)

    # Pigment in a manuscript outside the century range — should not appear
    outside_manuscript = ManuscriptFactory(date_start=1000, date_end=1100)
    other_pigment = PigmentFactory()
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
    PigmentFactory()
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
    pigment = PigmentFactory()
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
