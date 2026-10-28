import re

from django import forms
from django.db import models
from wagtail.models import Page
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel
from wagtail.blocks import CharBlock, ListBlock, RichTextBlock, StructBlock
from wagtail.images.blocks import ImageChooserBlock
from wagtail.snippets.models import register_snippet
from wagtail.search import index

LEGACY_EMBED_RE = re.compile(r'<embed[^>]*>')
LEGACY_EMBED_ID_RE = re.compile(r'id="(\d+)"')


class RichTextWithTitleBlock(StructBlock):
    """A prose chunk with an optional heading, rendered as a section header."""

    title = CharBlock(required=False, label='Block title', help_text='Optional — rendered as a section header')
    text = RichTextBlock(features=['h2', 'h3', 'bold', 'italic', 'ol', 'ul', 'link', 'image'])

    class Meta:
        icon = 'doc-full'
        label = 'Rich text'


class ImageWithCaptionBlock(StructBlock):
    image = ImageChooserBlock()
    caption = CharBlock(required=False)

    class Meta:
        icon = 'image'
        label = 'Image'


class ScribalDetailsBlock(StructBlock):
    """Fixed fields shared by every scribal (scroll/calligraphy) project."""

    size = CharBlock(required=True)
    reference = CharBlock(required=True, help_text='Source manuscript referenced')
    surface = CharBlock(required=True, help_text='e.g. vellum, stonehenge paper')
    colors = CharBlock(required=True)
    nib = CharBlock(required=True)
    ink = CharBlock(required=True)
    hand = CharBlock(required=True, help_text='Calligraphy script/hand used, e.g. Insular Minuscule')
    gilding = CharBlock(required=False)

    class Meta:
        icon = 'edit'
        label = 'Scribal details'


@register_snippet
class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)

    panels = [FieldPanel('name')]

    class Meta:
        ordering = ['name']
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class ProjectsIndexPage(Page):
    """Index page listing all published ProjectPage children."""

    subpage_types = ['blog.ProjectPage']
    parent_page_types = ['wagtailcore.Page']

    content_panels = Page.content_panels

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        all_projects = ProjectPage.objects.child_of(self).live()
        projects = all_projects.order_by('-date')

        category_id = request.GET.get('category')
        active_category = None
        if category_id:
            projects = projects.filter(categories__id=category_id).distinct()
            active_category = Category.objects.filter(id=category_id).first()

        context['projects'] = projects
        context['active_category'] = active_category
        context['categories'] = (
            Category.objects.filter(project_pages__in=all_projects)
            .distinct()
            .order_by('name')
        )
        return context


class ProjectPage(Page):
    """Individual project / tutorial article."""

    date = models.DateField()
    categories = models.ManyToManyField(
        'blog.Category',
        blank=True,
        related_name='project_pages',
    )
    excerpt = models.TextField(blank=True)
    cover_image = models.ForeignKey(
        'wagtailimages.Image',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )
    body = StreamField(
        [
            ('rich_text', RichTextWithTitleBlock()),
            ('carousel', ListBlock(ImageWithCaptionBlock(), icon='image')),
            ('image', ImageWithCaptionBlock()),
        ],
        blank=True,
        use_json_field=True,
        help_text='Build the article from rich text, image carousels, and standalone '
                   'images, in any order.',
    )
    technical_info = StreamField(
        [
            ('freeform', RichTextBlock(icon='doc-full')),
            ('scribal_details', ScribalDetailsBlock()),
        ],
        blank=True,
        use_json_field=True,
        max_num=1,
        help_text='Optional "Technical Information" accordion. Use Freeform for '
                   'most projects, or Scribal details for scroll/calligraphy pieces.',
    )

    # 'wagtailcore.Page' allows a project to instead live as a standalone
    # top-level page (e.g. Classes) when it doesn't belong in the Projects
    # index's category filtering.
    parent_page_types = ['blog.ProjectsIndexPage', 'wagtailcore.Page']
    subpage_types = []

    content_panels = Page.content_panels + [
        FieldPanel('date'),
        FieldPanel('categories', widget=forms.CheckboxSelectMultiple),
        FieldPanel('excerpt'),
        FieldPanel('cover_image'),
        FieldPanel('body'),
        FieldPanel('technical_info'),
    ]

    search_fields = Page.search_fields + [
        index.SearchField('body'),
        index.SearchField('excerpt'),
    ]

    @property
    def thumbnail(self):
        """Best available image for list-view thumbnails.

        Falls back through: explicit cover_image, the first structured
        image/carousel block, then the first <embed> image inside legacy
        migrated rich text (older projects have their images inline in
        prose rather than as separate blocks).
        """
        if self.cover_image:
            return self.cover_image

        for block in self.body:
            if block.block_type == 'image':
                return block.value['image']
            if block.block_type == 'carousel' and len(block.value):
                return block.value[0]['image']
            if block.block_type == 'rich_text':
                from wagtail.images.models import Image
                for tag in LEGACY_EMBED_RE.findall(block.value['text'].source):
                    if 'embedtype="image"' not in tag:
                        continue
                    match = LEGACY_EMBED_ID_RE.search(tag)
                    if match:
                        image = Image.objects.filter(pk=match.group(1)).first()
                        if image:
                            return image
        return None


class AboutPage(Page):
    """Single about page describing the site and its author."""

    body = RichTextField()
    profile_photo = models.ForeignKey(
        'wagtailimages.Image',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )

    parent_page_types = ['wagtailcore.Page']
    subpage_types = []

    content_panels = Page.content_panels + [
        FieldPanel('profile_photo'),
        FieldPanel('body'),
    ]


class HomePage(Page):
    """Site homepage — bio intro plus quick links into the major sections."""

    intro = RichTextField(blank=True)
    profile_photo = models.ForeignKey(
        'wagtailimages.Image',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )

    parent_page_types = ['wagtailcore.Page']
    subpage_types = ['blog.ProjectsIndexPage', 'blog.AboutPage', 'blog.ProjectPage']

    content_panels = Page.content_panels + [
        FieldPanel('profile_photo'),
        FieldPanel('intro'),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        projects_index = ProjectsIndexPage.objects.first()
        if projects_index:
            live_projects = ProjectPage.objects.child_of(projects_index).live()
            context['categories'] = (
                Category.objects.filter(project_pages__in=live_projects)
                .distinct()
                .order_by('name')
            )
        else:
            context['categories'] = Category.objects.none()
        return context
