import re

from django import forms
from django.db import models
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from wagtail.models import Orderable, Page
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.forms import WagtailAdminPageForm
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.blocks import CharBlock, ChoiceBlock, ListBlock, RichTextBlock, StructBlock
from wagtail.images.blocks import ImageChooserBlock
from wagtail.snippets.models import register_snippet
from wagtail.search import index

LEGACY_EMBED_RE = re.compile(r'<embed[^>]*>')
LEGACY_EMBED_ID_RE = re.compile(r'id="(\d+)"')

# Pre-selected on new project pages, and the catch-all group on the Projects
# index for projects that aren't in any configured column. Seeded by
# the blog migrations; matched by name, so renaming it in the admin turns both off.
DEFAULT_CATEGORY_NAME = 'Other'


class RichTextWithTitleBlock(StructBlock):
    """A prose chunk with an optional heading, rendered as a section header."""

    title = CharBlock(required=False, label='Block title', help_text='Optional — rendered as a section header')
    text = RichTextBlock(features=['h2', 'h3', 'bold', 'italic', 'ol', 'ul', 'link', 'image'])

    class Meta:
        icon = 'doc-full'
        label = 'Rich text'


class ImageWithCaptionBlock(StructBlock):
    """A standalone image, centered or set to one side of a text column.

    `alignment` and `text` were added after content existed; StructBlock fills
    missing keys with defaults, so older blocks render centered with no text.
    """

    title = CharBlock(required=False, label='Block title', help_text='Optional — rendered as a section header')
    image = ImageChooserBlock()
    caption = CharBlock(required=False)
    alignment = ChoiceBlock(
        choices=[('center', 'Centered'), ('left', 'Left'), ('right', 'Right')],
        default='center',
        help_text='Left/Right place the image beside the Side text.',
    )
    text = RichTextBlock(
        required=False,
        features=['h2', 'h3', 'bold', 'italic', 'ol', 'ul', 'link'],
        label='Side text',
        help_text='Optional — shown beside a Left/Right image (below a centered one).',
    )

    class Meta:
        icon = 'image'
        label = 'Image'


class CarouselImageBlock(StructBlock):
    """A single carousel slide — no title; the carousel itself carries one."""

    image = ImageChooserBlock()
    caption = CharBlock(required=False)

    class Meta:
        icon = 'image'
        label = 'Slide'


class CarouselBlock(StructBlock):
    title = CharBlock(required=False, label='Block title', help_text='Optional — rendered as a section header')
    images = ListBlock(CarouselImageBlock())

    class Meta:
        icon = 'image'
        label = 'Carousel'


class ScribalDetailsBlock(StructBlock):
    """Fixed fields shared by every scribal (scroll/calligraphy) project."""

    size = CharBlock(required=True)
    reference = CharBlock(required=True, help_text='Source manuscript referenced')
    surface = CharBlock(required=True, help_text='e.g. vellum, stonehenge paper')
    colors = CharBlock(required=True)
    nib = CharBlock(required=False)
    ink = CharBlock(required=False)
    hand = CharBlock(required=False, help_text='Calligraphy script/hand used, e.g. Insular Minuscule')
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
    """Index page listing published ProjectPage children, grouped into one
    column per configured category, with an optional collapsed archive."""

    archive_category = models.ForeignKey(
        'blog.Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        help_text='Projects in this category are listed only in a collapsed '
                  'section at the bottom of the page.',
    )

    subpage_types = ['blog.ProjectPage']
    parent_page_types = ['wagtailcore.Page']

    content_panels = Page.content_panels + [
        InlinePanel(
            'columns',
            heading='Columns',
            label='Column',
            help_text='One column per category, in this order. Projects in none '
                      'of these categories are listed under "Other" below them.',
        ),
        FieldPanel('archive_category'),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context.update(self.grouped_projects())
        return context

    def grouped_projects(self):
        """Live child projects split into columns, "Other" and the archive.

        A project shows in every column whose category it has; one in no
        column goes to the default-category column if that is one, otherwise
        to the "Other" list. Archived projects show only in the archive.
        """
        projects = (
            ProjectPage.objects.child_of(self).live()
            .order_by('-date')
            .select_related('cover_image')
            .prefetch_related('categories')
        )
        archive_id = self.archive_category_id

        # Deduplicate and drop the archive category: a project can only be
        # listed once per column, and archived projects never show in one.
        column_categories = []
        for column in self.columns.select_related('category'):
            if column.category_id != archive_id and column.category not in column_categories:
                column_categories.append(column.category)
        groups = {category.id: [] for category in column_categories}
        default = next(
            (c for c in column_categories if c.name == DEFAULT_CATEGORY_NAME), None
        )
        column_ids = set(groups)

        archive, other = [], []
        for project in projects:
            categories = list(project.categories.all())
            category_ids = [c.id for c in categories]
            archived = archive_id in category_ids
            # The column (or the archive heading) already says which category
            # a project is in, so the card only tags the others (e.g.
            # Collaborations). Archived cards sit under no column, so they
            # keep their column categories as tags.
            hidden_tag_ids = {archive_id} if archived else column_ids
            project.tag_categories = [
                c for c in categories
                if c.id not in hidden_tag_ids and c.name != DEFAULT_CATEGORY_NAME
            ]
            if archived:
                archive.append(project)
                continue
            matched = [cid for cid in groups if cid in category_ids]
            for cid in matched:
                groups[cid].append(project)
            if not matched:
                (groups[default.id] if default else other).append(project)

        return {
            'columns': [
                (category, groups[category.id])
                for category in column_categories
                if groups[category.id]
            ],
            'other_projects': other,
            'archive_category': self.archive_category if archive else None,
            'archive_projects': archive,
        }


class ProjectsIndexColumn(Orderable):
    """One category shown as a column on the Projects index."""

    page = ParentalKey(
        'blog.ProjectsIndexPage', on_delete=models.CASCADE, related_name='columns'
    )
    category = models.ForeignKey(
        'blog.Category', on_delete=models.CASCADE, related_name='+'
    )

    panels = [FieldPanel('category')]


class ProjectPageForm(WagtailAdminPageForm):
    """Pre-selects the default category on a new project page."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk is None and not self.initial.get('categories'):
            default = Category.objects.filter(name=DEFAULT_CATEGORY_NAME).first()
            if default:
                self.initial['categories'] = [default.pk]


class ProjectPage(Page):
    """Individual project / tutorial article."""

    date = models.DateField()
    # ParentalManyToManyField (not models.ManyToManyField) so the selection is
    # stored in page revisions — Wagtail publishes from the revision, and a
    # plain M2M there silently reverts edits made in the admin.
    categories = ParentalManyToManyField(
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
            ('carousel', CarouselBlock()),
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

    base_form_class = ProjectPageForm

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
    def display_categories(self):
        """Categories worth showing as tags: the default one says nothing."""
        return [c for c in self.categories.all() if c.name != DEFAULT_CATEGORY_NAME]

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

        # A chooser block whose image was since deleted holds None — skip it
        # and keep looking rather than ending the search with no thumbnail.
        for block in self.body:
            if block.block_type == 'image':
                if block.value['image']:
                    return block.value['image']
            elif block.block_type == 'carousel':
                for item in block.value['images']:
                    if item['image']:
                        return item['image']
            elif block.block_type == 'rich_text':
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
        projects_index = ProjectsIndexPage.objects.live().first()
        context['projects_index'] = projects_index
        # Quick links jump to the index's columns, so only those that are
        # actually shown (configured and non-empty) get one.
        context['categories'] = (
            [category for category, _ in projects_index.grouped_projects()['columns']]
            if projects_index else []
        )
        return context
