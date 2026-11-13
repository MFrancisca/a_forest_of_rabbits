import datetime
import html
import re

from django import forms
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import models
from django.utils.http import urlencode
from django.utils.html import strip_tags
from django.utils.text import slugify
from modelcluster.fields import ParentalManyToManyField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page
from wagtail.snippets.models import register_snippet

from blog.models import CarouselBlock, ImageWithCaptionBlock, RichTextWithTitleBlock

# The tag the pigment pages' "Latest pigment notes" sidebar shows. Matched by
# slug, which renaming the tag in the admin doesn't change. Seeded by migration.
PIGMENTS_TAG_SLUG = 'pigments'

# Longest summary, typed or taken from the body.
SUMMARY_LENGTH = 300

POSTS_PER_PAGE = 10


@register_snippet
class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(
        max_length=100, unique=True, blank=True,
        help_text='Used in the blog filter link (/blog/?tag=…). Filled from the name '
                  'if left blank; kept when the name changes.',
    )

    panels = [FieldPanel('name'), FieldPanel('slug')]

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def clean(self):
        # Fill the slug here, not only in save(), so the admin form's unique check
        # sees it: "Work in progress" and "Work-in-progress" both slugify the same.
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.slug:
            raise ValidationError({'slug': 'Enter a slug: the name has no letters or digits to make one from.'})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class BlogIndexPage(Page):
    """The blog: live posts, newest first, filterable by tag."""

    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel('intro')]

    parent_page_types = ['blog.HomePage']
    subpage_types = ['journal.BlogPostPage']
    max_count = 1

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        posts = (
            BlogPostPage.objects.live().child_of(self).order_by('-date', '-first_published_at')
            .select_related('cover_image').prefetch_related('tags', 'cover_image__renditions')
        )
        slug = request.GET.get('tag', '')
        current_tag = Tag.objects.filter(slug=slug).first() if slug else None
        if slug:
            # An unknown slug lists nothing (with a message) rather than 404ing.
            posts = posts.filter(tags=current_tag) if current_tag else posts.none()
        # get_page() clamps bad or out-of-range numbers to the first/last page.
        page = Paginator(posts, POSTS_PER_PAGE).get_page(request.GET.get('page'))
        context.update(
            posts=page,
            # Only tags with a live post here, so no filter link leads to an empty list.
            tags=Tag.objects.filter(posts__in=BlogPostPage.objects.live().child_of(self)).distinct(),
            current_tag=current_tag,
            unknown_tag=slug if slug and not current_tag else '',
            page_query=urlencode({'tag': slug}) + '&' if current_tag else '',
        )
        return context


class BlogPostPage(Page):
    """A work-in-progress update or an interesting find."""

    date = models.DateField(default=datetime.date.today)
    summary = models.TextField(
        max_length=SUMMARY_LENGTH, blank=True,
        help_text='Shown in the blog list, the pigment notes sidebar and on related '
                  'projects. Leave blank to use the beginning of the body.',
    )
    cover_image = models.ForeignKey(
        'wagtailimages.Image',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )
    # Parental M2Ms (not plain M2Ms) so the selection is stored in page
    # revisions, as with ProjectPage.categories.
    tags = ParentalManyToManyField('journal.Tag', blank=True, related_name='posts')
    related_projects = ParentalManyToManyField(
        'blog.ProjectPage', blank=True, related_name='journal_posts',
        help_text='This post is listed under "Updates on this project" on each of these.',
    )
    body = StreamField(
        [
            ('rich_text', RichTextWithTitleBlock()),
            ('carousel', CarouselBlock()),
            ('image', ImageWithCaptionBlock()),
        ],
        blank=True,
        use_json_field=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel('date'),
        FieldPanel('summary'),
        FieldPanel('cover_image'),
        MultiFieldPanel([
            FieldPanel('tags', widget=forms.CheckboxSelectMultiple),
            FieldPanel('related_projects'),
        ], heading='Tags & related projects'),
        FieldPanel('body'),
    ]

    parent_page_types = ['journal.BlogIndexPage']
    subpage_types = []

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        # A Python filter, not .live(): a preview holds an in-memory relation without PageQuerySet methods.
        context['live_projects'] = [p for p in self.related_projects.all() if p.live]
        context['index_url'] = self.get_parent().get_url(request)
        return context

    @property
    def display_summary(self):
        """The summary, or else the start of the body's first rich text with any text."""
        if self.summary:
            return self.summary
        for block in self.body:
            if block.block_type != 'rich_text':
                continue
            text = re.sub(r'\s+', ' ', html.unescape(strip_tags(block.value['text'].source))).strip()
            if text:
                return _truncate_at_word(text, SUMMARY_LENGTH)
        return ''


def _truncate_at_word(text, limit):
    """`text` cut to at most `limit` characters at a word boundary, plus "…" if cut."""
    if len(text) <= limit:
        return text
    cut = text[:limit + 1]
    space = cut.rfind(' ')
    return (cut[:space] if space > 0 else text[:limit]).rstrip() + '…'
