import re

from django.core.exceptions import ValidationError
from django.db import models
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.models import ClusterableModel
from wagtail.models import Collection, Orderable

from core.collections import top_level_collection
from wagtail.snippets.models import register_snippet
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel


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
    abbreviation = models.CharField(
        max_length=10,
        blank=True,
        help_text='Short label used in compact formula notation (e.g. "W" for white)',
    )

    panels = [
        FieldPanel('brand'),
        FieldPanel('name'),
        FieldPanel('hex_color'),
        FieldPanel('abbreviation'),
    ]

    class Meta:
        ordering = ['brand', 'name']
        verbose_name = 'paint'
        verbose_name_plural = 'paints'

    def __str__(self):
        return f'{self.brand} — {self.name}'


MANUSCRIPTS_COLLECTION_NAME = 'Manuscripts'


def manuscripts_collection():
    """The "Manuscripts" collection (a child of Root) for illuminations, created if missing."""
    return top_level_collection(MANUSCRIPTS_COLLECTION_NAME)


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

    # Shown in the expanded manuscript row on pigment pages, so visitors can see
    # the colours in the manuscript itself, with the holding library's credit.
    illumination = models.ForeignKey(
        'wagtailimages.Image',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        help_text='An illumination from the manuscript that shows its colours.',
    )
    illumination_caption = models.CharField(
        max_length=255, blank=True,
        help_text='What the image shows, e.g. "Chi Rho page, fol. 34r".',
    )
    illumination_credit = models.CharField(
        max_length=500, blank=True,
        help_text='Required with an image: the credit line and licence the holding library asks for.',
    )
    illumination_credit_url = models.URLField(
        max_length=500, blank=True,
        help_text="The library's page for this image, or its licence.",
    )
    digitized_url = models.URLField(
        max_length=500, blank=True,
        help_text='Where the digitized manuscript can be viewed online.',
    )

    @property
    def date_display(self):
        if self.date_start and self.date_end:
            return f'c.{self.date_start}\u2013{self.date_end}'
        elif self.date_start:
            return f'c.{self.date_start}'
        return '\u2014'

    panels = [
        FieldPanel('name'),
        FieldPanel('country'),
        FieldPanel('date_start'),
        FieldPanel('date_end'),
        FieldPanel('notes'),
        MultiFieldPanel([
            FieldPanel('illumination'),
            FieldPanel('illumination_caption'),
            FieldPanel('illumination_credit'),
            FieldPanel('illumination_credit_url'),
            FieldPanel('digitized_url'),
        ], heading='Illumination & digitized copy'),
    ]

    @property
    def illumination_alt_text(self):
        # The image's description if it has one; titles are often just file names.
        description = getattr(self.illumination, 'description', '')
        return description or f'Illumination from {self.name}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._file_illumination()

    def _file_illumination(self):
        """Move an unfiled illumination (in the root collection, where uploads land
        by default) into a "Manuscripts" collection. One already filed elsewhere,
        e.g. in a project's collection, stays where it is."""
        image = self.illumination
        if image is None:
            return
        if image.collection_id != Collection.get_first_root_node().pk:
            return
        collection = manuscripts_collection()
        type(image).objects.filter(pk=image.pk).update(collection=collection)
        image.collection = collection

    def clean(self):
        super().clean()
        if self.illumination_id and not self.illumination_credit.strip():
            raise ValidationError({
                'illumination_credit': 'Add the credit line the holding library asks for.',
            })

    class Meta:
        ordering = ['name']
        verbose_name = 'manuscript'
        verbose_name_plural = 'manuscripts'

    def __str__(self):
        return self.name


@register_snippet
class Source(models.Model):
    """
    A citable reference: a paper, book, technical report or website.
    Shared between pigments, so one paper is entered once and cited many times.
    """

    KIND_PAPER = 'paper'
    KIND_BOOK = 'book'
    KIND_REPORT = 'report'
    KIND_WEBSITE = 'website'
    KIND_CHOICES = [
        (KIND_PAPER, 'Paper'),
        (KIND_BOOK, 'Book'),
        (KIND_REPORT, 'Report'),
        (KIND_WEBSITE, 'Website'),
    ]

    kind = models.CharField(max_length=10, choices=KIND_CHOICES, default=KIND_PAPER)
    authors = models.CharField(
        max_length=500,
        blank=True,
        help_text='e.g. "Bioletti, S., Leahy, R., Fields, J."',
    )
    title = models.CharField(max_length=500)
    publication = models.CharField(
        max_length=255,
        blank=True,
        help_text='Journal, publisher, institution or website name, with volume/pages if any',
    )
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    doi = models.CharField(
        max_length=255,
        blank=True,
        help_text='Bare DOI, e.g. 10.1002/jrs.2231 (no https://doi.org/)',
    )
    url = models.URLField(
        max_length=500,
        blank=True,
        help_text='Link to the paper or page. Leave blank to link via the DOI.',
    )

    panels = [
        FieldPanel('kind'),
        FieldPanel('authors'),
        FieldPanel('title'),
        FieldPanel('publication'),
        FieldPanel('year'),
        FieldPanel('doi'),
        FieldPanel('url'),
    ]

    class Meta:
        ordering = ['authors', 'year', 'title']
        verbose_name = 'source'
        verbose_name_plural = 'sources'

    @property
    def link(self):
        """Best URL for this source: explicit URL first, else the DOI resolver."""
        if self.url:
            return self.url
        if self.doi:
            return f'https://doi.org/{self.doi}'
        return ''

    @property
    def short_label(self):
        """Compact in-table label, e.g. 'Bioletti et al. 2009' or 'Trinity College Dublin Library'."""
        if self.authors:
            # "Surname, I. J." pairs; an organisation name with no initials is used whole.
            surnames = [
                m.strip() for m in re.findall(r'([^,&]+?),\s*[A-Z]\.', self.authors)
            ] or [self.authors.strip()]
            if len(surnames) == 1:
                lead = surnames[0]
            elif len(surnames) == 2:
                lead = f'{surnames[0]} & {surnames[1]}'
            else:
                lead = f'{surnames[0]} et al.'
        else:
            lead = self.publication or self.title
        return f'{lead} {self.year}' if self.year else lead

    @property
    def citation(self):
        """Plain-text citation, e.g. 'Bioletti, S. et al. (2009). Title. Journal.'"""
        parts = []
        if self.authors:
            parts.append(self.authors.rstrip('.') + '.')
        if self.year:
            parts.append(f'({self.year}).')
        for text in (self.title, self.publication):
            if text:
                # Don't add a full stop after a title ending in ? or !
                parts.append(text if text[-1] in '.?!' else text + '.')
        return ' '.join(parts)

    def __str__(self):
        lead = self.authors.split(',')[0].strip() if self.authors else self.publication
        bits = [b for b in (lead, str(self.year) if self.year else '') if b]
        prefix = f'{", ".join(bits)}: ' if bits else ''
        return f'{prefix}{self.title}'[:120]


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
    sources = ParentalManyToManyField(
        'Source',
        blank=True,
        related_name='pigments',
        help_text='General references for this pigment (not tied to a manuscript).',
    )

    panels = [
        FieldPanel('name'),
        FieldPanel('color_family'),
        FieldPanel('pigment_family'),
        FieldPanel('description'),
        FieldPanel('sources'),
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
    image = models.ForeignKey(
        'wagtailimages.Image',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        help_text='Optional — e.g. a paint-out of this formula. Shown to the left of the formula.',
    )
    notes = models.TextField(blank=True)

    panels = [
        FieldPanel('brand'),
        FieldPanel('image'),
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
    parts = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Quantity in parts. Leave blank and tick "trace amount" instead for a '
                   'quantity too small to measure.',
    )
    is_trace = models.BooleanField(
        default=False,
        help_text='Trace amount (Δ) — used instead of "parts" when the quantity is too '
                   'small to measure.',
    )

    panels = [
        FieldPanel('paint'),
        FieldPanel('parts'),
        FieldPanel('is_trace'),
    ]

    class Meta(Orderable.Meta):
        verbose_name = 'formula part'
        verbose_name_plural = 'formula parts'

    def clean(self):
        super().clean()
        if self.is_trace and self.parts is not None:
            raise ValidationError('A formula part cannot have both a parts quantity and be marked as trace.')
        if not self.is_trace and self.parts is None:
            raise ValidationError('A formula part needs either a parts quantity or "trace amount" ticked.')

    def __str__(self):
        return f'{self.paint} × {"Δ" if self.is_trace else self.parts}'


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
    source = models.ForeignKey(
        Source,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='manuscript_links',
        help_text='The publication that identified this pigment in this manuscript.',
    )
    source_detail = models.CharField(
        max_length=255,
        blank=True,
        help_text='Where in the source, e.g. "Table 1" or "p. 1046".',
    )

    panels = [
        FieldPanel('manuscript'),
        FieldPanel('page_reference'),
        FieldPanel('notes'),
        FieldPanel('source'),
        FieldPanel('source_detail'),
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
