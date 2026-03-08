import pytest
from pigments.factories import ColorFamilyFactory, PigmentFactory, FormulaFactory


@pytest.fixture
def color_family(db):
    return ColorFamilyFactory()


@pytest.fixture
def pigment(db):
    return PigmentFactory()


@pytest.fixture
def formula(db):
    return FormulaFactory()
