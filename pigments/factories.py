"""
factory_boy DjangoModelFactory classes for all 11 pigment models.

Every factory is callable with zero arguments and produces a valid saved instance.
Uses factory.Sequence for unique fields and factory.SubFactory for FK relationships.
No Django fixtures or loaddata calls anywhere.
"""
import factory
from factory.django import DjangoModelFactory

from pigments.models import (
    ColorFamily,
    PigmentFamily,
    Country,
    Brand,
    Paint,
    Manuscript,
    Pigment,
    Formula,
    FormulaPart,
    PigmentManuscript,
    PigmentImage,
)


class ColorFamilyFactory(DjangoModelFactory):
    class Meta:
        model = ColorFamily

    name = factory.Sequence(lambda n: f'Color Family {n}')


class PigmentFamilyFactory(DjangoModelFactory):
    class Meta:
        model = PigmentFamily

    name = factory.Sequence(lambda n: f'Pigment Family {n}')


class CountryFactory(DjangoModelFactory):
    class Meta:
        model = Country

    name = factory.Sequence(lambda n: f'Country {n}')


class BrandFactory(DjangoModelFactory):
    class Meta:
        model = Brand

    name = factory.Sequence(lambda n: f'Brand {n}')


class PaintFactory(DjangoModelFactory):
    class Meta:
        model = Paint

    brand = factory.SubFactory(BrandFactory)
    name = factory.Sequence(lambda n: f'Paint {n}')
    hex_color = factory.Sequence(lambda n: f'#{n:06x}')


class ManuscriptFactory(DjangoModelFactory):
    class Meta:
        model = Manuscript

    name = factory.Sequence(lambda n: f'Manuscript {n}')
    country = factory.SubFactory(CountryFactory)


class PigmentFactory(DjangoModelFactory):
    class Meta:
        model = Pigment

    name = factory.Sequence(lambda n: f'Pigment {n}')
    color_family = factory.SubFactory(ColorFamilyFactory)
    pigment_family = factory.SubFactory(PigmentFamilyFactory)


class FormulaFactory(DjangoModelFactory):
    class Meta:
        model = Formula

    pigment = factory.SubFactory(PigmentFactory)
    brand = factory.SubFactory(BrandFactory)


class FormulaPartFactory(DjangoModelFactory):
    class Meta:
        model = FormulaPart

    formula = factory.SubFactory(FormulaFactory)
    paint = factory.SubFactory(PaintFactory)
    parts = factory.Sequence(lambda n: round(1.0 + n * 0.5, 2))


class PigmentManuscriptFactory(DjangoModelFactory):
    class Meta:
        model = PigmentManuscript

    pigment = factory.SubFactory(PigmentFactory)
    manuscript = factory.SubFactory(ManuscriptFactory)


class PigmentImageFactory(DjangoModelFactory):
    class Meta:
        model = PigmentImage

    pigment = factory.SubFactory(PigmentFactory)
    image = None  # null=True — no file fixture needed in Phase 1
