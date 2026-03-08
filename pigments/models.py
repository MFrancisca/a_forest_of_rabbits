from django.db import models
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.models import Orderable
from wagtail.snippets.models import register_snippet
from wagtail.admin.panels import FieldPanel, InlinePanel


# ---------------------------------------------------------------------------
# Simple taxonomy models — registered as Wagtail Snippets
# ---------------------------------------------------------------------------

@register_snippet
class ColorFamily(models.Model):
    """Broad colour category (e.g. 'Blue', 'Earth', 'Red')."""

    name = models.CharField(max_length=255, unique=True)

    panels = [
        FieldPanel('name'),
    ]

    class Meta:
        ordering = ['name']
        verbose_name = 'color family'
        verbose_name_plural = 'color families'

    def __str__(self):
        return self.name


@register_snippet
class PigmentFamily(models.Model):
    """Chemical / mineral family (e.g. 'Oxide', 'Ultramarine', 'Lead')."""

    name = models.CharField(max_length=255, unique=True)

    panels = [
        FieldPanel('name'),
    ]

    class Meta:
        ordering = ['name']
        verbose_name = 'pigment family'
        verbose_name_plural = 'pigment families'

    def __str__(self):
        return self.name


@register_snippet
class Country(models.Model):
    """Country of origin for manuscripts and pigment sources."""

    name = models.CharField(max_length=255, unique=True)

    panels = [
        FieldPanel('name'),
    ]

    class Meta:
        ordering = ['name']
        verbose_name = 'country'
        verbose_name_plural = 'countries'

    def __str__(self):
        return self.name


@register_snippet
class Brand(models.Model):
    """Paint manufacturer / supplier brand (e.g. 'Rublev', 'Williamsburg')."""

    name = models.CharField(max_length=255, unique=True)

    panels = [
        FieldPanel('name'),
    ]

    class Meta:
        ordering = ['name']
        verbose_name = 'brand'
        verbose_name_plural = 'brands'

    def __str__(self):
        return self.name


@register_snippet
class Paint(models.Model):
    """
    A specific paint product from a brand (e.g. Rublev 'Lead White').
    Used as ingredients in Formula parts.
    """

    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
        related_name='paints',
    )
    name = models.CharField(max_length=255)
    hex_color = models.CharField(
        max_length=7,
        blank=True,
        help_text='CSS hex e.g. #A3B2C1',
    )

    panels = [
        FieldPanel('brand'),
        FieldPanel('name'),
        FieldPanel('hex_color'),
    ]

    class Meta:
        ordering = ['brand', 'name']
        verbose_name = 'paint'
        verbose_name_plural = 'paints'

    def __str__(self):
        return f'{self.brand} — {self.name}'


@register_snippet
class Manuscript(models.Model):
    """
    A historical manuscript containing pigment recipes or references.
    e.g. 'Mappae Clavicula', 'Book of Kells'.
    """

    name = models.CharField(max_length=255)
    country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='manuscripts',
    )
    date_start = models.IntegerField(
        null=True,
        blank=True,
        help_text='Year CE',
    )
    date_end = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)

    panels = [
        FieldPanel('name'),
        FieldPanel('country'),
        FieldPanel('date_start'),
        FieldPanel('date_end'),
        FieldPanel('notes'),
    ]

    class Meta:
        ordering = ['name']
        verbose_name = 'manuscript'
        verbose_name_plural = 'manuscripts'

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Core pigment model — ClusterableModel for nested inline admin editing
# ---------------------------------------------------------------------------

@register_snippet
class Pigment(ClusterableModel):
    """
    The central entity. Represents a historical pigment (e.g. 'Ultramarine Blue').
    Has nested formulas, manuscript references, and images via InlinePanel.
    """

    name = models.CharField(max_length=255)
    color_family = models.ForeignKey(
        ColorFamily,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='pigments',
    )
    pigment_family = models.ForeignKey(
        PigmentFamily,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='pigments',
    )
    description = models.TextField(blank=True)

    panels = [
        FieldPanel('name'),
        FieldPanel('color_family'),
        FieldPanel('pigment_family'),
        FieldPanel('description'),
        InlinePanel('formulas', label='Formulas'),
        InlinePanel('manuscript_links', label='Manuscript Links'),
        InlinePanel('images', label='Images'),
    ]

    class Meta:
        ordering = ['name']
        verbose_name = 'pigment'
        verbose_name_plural = 'pigments'

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Formula — TWO-level nesting: Pigment → Formula → FormulaPart
# Must be BOTH ClusterableModel (has its own InlinePanel) and Orderable
# ---------------------------------------------------------------------------

class Formula(ClusterableModel, Orderable):
    """
    A recipe formula for a pigment using a particular brand's paints.
    One Pigment may have multiple Formulas (one per brand comparison).
    """

    pigment = ParentalKey(
        Pigment,
        on_delete=models.CASCADE,
        related_name='formulas',
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
        related_name='formulas',
    )
    notes = models.TextField(blank=True)

    panels = [
        FieldPanel('brand'),
        FieldPanel('notes'),
        InlinePanel('parts', label='Formula Parts'),
    ]

    class Meta(Orderable.Meta):
        verbose_name = 'formula'
        verbose_name_plural = 'formulas'

    def __str__(self):
        return f'{self.pigment} — {self.brand}'


# ---------------------------------------------------------------------------
# Leaf inline children — Orderable only (no further nesting)
# ---------------------------------------------------------------------------

class FormulaPart(Orderable):
    """
    One ingredient in a Formula: a specific Paint with a quantity in parts.
    e.g. Lead White 3 parts + Smalt 1 part.
    """

    formula = ParentalKey(
        Formula,
        on_delete=models.CASCADE,
        related_name='parts',
    )
    paint = models.ForeignKey(
        Paint,
        on_delete=models.PROTECT,
        related_name='formula_parts',
    )
    parts = models.DecimalField(max_digits=5, decimal_places=2)

    panels = [
        FieldPanel('paint'),
        FieldPanel('parts'),
    ]

    class Meta(Orderable.Meta):
        verbose_name = 'formula part'
        verbose_name_plural = 'formula parts'

    def __str__(self):
        return f'{self.paint} × {self.parts}'


class PigmentManuscript(Orderable):
    """
    A link from a Pigment to a Manuscript with page reference and notes.
    Allows many manuscript citations per pigment.
    """

    pigment = ParentalKey(
        Pigment,
        on_delete=models.CASCADE,
        related_name='manuscript_links',
    )
    manuscript = models.ForeignKey(
        Manuscript,
        on_delete=models.PROTECT,
        related_name='pigment_links',
    )
    page_reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    panels = [
        FieldPanel('manuscript'),
        FieldPanel('page_reference'),
        FieldPanel('notes'),
    ]

    class Meta(Orderable.Meta):
        verbose_name = 'pigment manuscript link'
        verbose_name_plural = 'pigment manuscript links'

    def __str__(self):
        return f'{self.pigment} → {self.manuscript}'


class PigmentImage(Orderable):
    """
    An image associated with a pigment (photo of dry pigment, paint-out, etc.).
    image is nullable so Phase 1 tests/factories work without file fixtures.
    """

    pigment = ParentalKey(
        Pigment,
        on_delete=models.CASCADE,
        related_name='images',
    )
    image = models.ForeignKey(
        'wagtailimages.Image',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )
    caption = models.CharField(max_length=255, blank=True)
    alt_text = models.CharField(max_length=255, blank=True)

    panels = [
        FieldPanel('image'),
        FieldPanel('caption'),
        FieldPanel('alt_text'),
    ]

    class Meta(Orderable.Meta):
        verbose_name = 'pigment image'
        verbose_name_plural = 'pigment images'

    def __str__(self):
        return f'{self.pigment} — {self.caption or self.alt_text or "image"}'
