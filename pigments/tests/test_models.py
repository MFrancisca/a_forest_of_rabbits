"""
Tests for all 11 pigment models using factory_boy.

TDD RED phase: imports from pigments.factories which does not exist yet.
Running this file before factories are written will fail with ImportError.
"""
import pytest
from django.core.exceptions import ValidationError

from pigments.factories import (
    ColorFamilyFactory,
    PigmentFamilyFactory,
    CountryFactory,
    BrandFactory,
    PaintFactory,
    ManuscriptFactory,
    PigmentFactory,
    FormulaFactory,
    FormulaPartFactory,
    PigmentManuscriptFactory,
    PigmentImageFactory,
)


@pytest.mark.django_db
def test_color_family_creates():
    """ColorFamilyFactory creates a valid instance with str returning name."""
    cf = ColorFamilyFactory()
    assert cf.pk is not None
    assert str(cf) == cf.name


@pytest.mark.django_db
def test_pigment_family_creates():
    """PigmentFamilyFactory creates instance with unique name."""
    pf = PigmentFamilyFactory()
    assert pf.pk is not None
    assert str(pf) == pf.name


@pytest.mark.django_db
def test_country_creates():
    """CountryFactory creates a valid country instance."""
    country = CountryFactory()
    assert country.pk is not None
    assert str(country) == country.name


@pytest.mark.django_db
def test_brand_creates():
    """BrandFactory creates a valid brand instance."""
    brand = BrandFactory()
    assert brand.pk is not None
    assert str(brand) == brand.name


@pytest.mark.django_db
def test_paint_creates():
    """PaintFactory creates instance with brand FK populated via SubFactory."""
    paint = PaintFactory()
    assert paint.pk is not None
    assert paint.brand is not None
    assert paint.brand.pk is not None
    assert isinstance(str(paint), str)
    assert len(str(paint)) > 0


@pytest.mark.django_db
def test_manuscript_creates():
    """ManuscriptFactory creates instance with country FK."""
    manuscript = ManuscriptFactory()
    assert manuscript.pk is not None
    assert manuscript.country is not None
    assert str(manuscript) == manuscript.name


@pytest.mark.django_db
def test_pigment_creates():
    """PigmentFactory creates instance with color_family and pigment_family FKs."""
    pigment = PigmentFactory()
    assert pigment.pk is not None
    assert pigment.color_family is not None
    assert pigment.pigment_family is not None


@pytest.mark.django_db
def test_pigment_str():
    """str(PigmentFactory()) returns a non-empty string."""
    pigment = PigmentFactory()
    result = str(pigment)
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.django_db
def test_formula_creates():
    """FormulaFactory creates instance linked to a Pigment."""
    formula = FormulaFactory()
    assert formula.pk is not None
    assert formula.pigment is not None
    assert formula.pigment.pk is not None


@pytest.mark.django_db
def test_formula_part_creates():
    """FormulaPartFactory creates instance with paint FK."""
    part = FormulaPartFactory()
    assert part.pk is not None
    assert part.paint is not None
    assert part.paint.pk is not None


@pytest.mark.django_db
def test_pigment_with_formula():
    """PigmentFactory + FormulaFactory(pigment=pigment) — formula in pigment.formulas.all()."""
    pigment = PigmentFactory()
    formula = FormulaFactory(pigment=pigment)
    assert formula in pigment.formulas.all()


@pytest.mark.django_db
def test_formula_with_parts():
    """FormulaFactory + FormulaPartFactory(formula=formula) — part in formula.parts.all()."""
    formula = FormulaFactory()
    part = FormulaPartFactory(formula=formula)
    assert part in formula.parts.all()


@pytest.mark.django_db
def test_formula_part_trace_amount():
    """A trace (Δ) part has parts=None, is_trace=True, and renders with the Δ symbol."""
    part = FormulaPartFactory(parts=None, is_trace=True)
    assert part.pk is not None
    assert part.parts is None
    assert str(part) == f'{part.paint} × Δ'


@pytest.mark.django_db
def test_formula_part_requires_parts_or_trace():
    """clean() rejects a part with neither a parts quantity nor trace ticked."""
    part = FormulaPartFactory.build(parts=None, is_trace=False)
    with pytest.raises(ValidationError):
        part.clean()


@pytest.mark.django_db
def test_formula_part_rejects_parts_and_trace_together():
    """clean() rejects a part with both a parts quantity and trace ticked."""
    part = FormulaPartFactory.build(parts=3, is_trace=True)
    with pytest.raises(ValidationError):
        part.clean()


@pytest.mark.django_db
def test_pigment_manuscript_link():
    """PigmentManuscriptFactory creates instance with pigment and manuscript FKs."""
    link = PigmentManuscriptFactory()
    assert link.pk is not None
    assert link.pigment is not None
    assert link.manuscript is not None


@pytest.mark.django_db
def test_pigment_image_creates():
    """PigmentImageFactory creates instance with image=None (null allowed)."""
    img = PigmentImageFactory()
    assert img.pk is not None
    assert img.image is None


@pytest.mark.django_db
def test_factory_sequences_unique():
    """Two ColorFamilyFactory() calls produce distinct names."""
    cf1 = ColorFamilyFactory()
    cf2 = ColorFamilyFactory()
    assert cf1.name != cf2.name


# ---------------------------------------------------------------------------
# Phase 03-01 tests: Paint.abbreviation and Manuscript.date_display
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_paint_abbreviation_field():
    """Paint.abbreviation exists, max_length=10, blank=True, default is ''."""
    paint = PaintFactory()
    assert hasattr(paint, 'abbreviation')
    assert len(paint.abbreviation) == 1  # PaintFactory Sequence produces single letter A-Z


@pytest.mark.django_db
def test_paint_factory_abbreviation():
    """PaintFactory() produces a non-empty abbreviation string."""
    paint = PaintFactory()
    assert isinstance(paint.abbreviation, str)
    assert len(paint.abbreviation) > 0


@pytest.mark.django_db
def test_manuscript_date_display_both():
    """Manuscript with start and end renders 'c.800\u2013900'."""
    manuscript = ManuscriptFactory(date_start=800, date_end=900)
    assert manuscript.date_display == 'c.800\u2013900'


@pytest.mark.django_db
def test_manuscript_date_display_start_only():
    """Manuscript with only start renders 'c.800'."""
    manuscript = ManuscriptFactory(date_start=800, date_end=None)
    assert manuscript.date_display == 'c.800'


@pytest.mark.django_db
def test_manuscript_date_display_neither():
    """Manuscript with no dates renders em-dash."""
    manuscript = ManuscriptFactory(date_start=None, date_end=None)
    assert manuscript.date_display == '\u2014'


# ---------------------------------------------------------------------------
# Source
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_source_link_prefers_url_then_doi():
    from pigments.factories import SourceFactory
    assert SourceFactory(doi='10.1002/jrs.2231', url='').link == 'https://doi.org/10.1002/jrs.2231'
    assert SourceFactory(doi='10.1002/jrs.2231', url='https://example.org/p').link == 'https://example.org/p'
    assert SourceFactory(doi='', url='').link == ''


@pytest.mark.parametrize('authors,expected', [
    ('Bicchieri, M.', 'Bicchieri 2014'),
    ('Brown, K. L. & Clark, R. J. H.', 'Brown & Clark 2014'),
    ('Bioletti, S., Leahy, R., Fields, J., Meehan, B. & Blau, W.', 'Bioletti et al. 2014'),
    ('McCrone Associates', 'McCrone Associates 2014'),
])
def test_source_short_label(authors, expected):
    from pigments.models import Source
    assert Source(authors=authors, title='T', year=2014).short_label == expected


def test_source_short_label_without_authors_uses_publication():
    from pigments.models import Source
    assert Source(title='What colour is that?', publication='Trinity College Dublin Library').short_label \
        == 'Trinity College Dublin Library'


def test_source_citation():
    from pigments.models import Source
    s = Source(authors='Brown, K. L. & Clark, R. J. H.', year=2004, title='The Lindisfarne Gospels',
               publication='Journal of Raman Spectroscopy 35(1), 4–12')
    assert s.citation == ('Brown, K. L. & Clark, R. J. H. (2004). The Lindisfarne Gospels. '
                          'Journal of Raman Spectroscopy 35(1), 4–12.')


@pytest.mark.django_db
def test_pigment_general_sources():
    from pigments.factories import SourceFactory
    pigment = PigmentFactory()
    source = SourceFactory()
    pigment.sources.add(source)
    pigment.save()
    assert list(source.pigments.all()) == [pigment]


def test_source_citation_no_double_punctuation():
    from pigments.models import Source
    assert Source(title='What colour is that?', publication='Trinity College Dublin Library').citation \
        == 'What colour is that? Trinity College Dublin Library.'
