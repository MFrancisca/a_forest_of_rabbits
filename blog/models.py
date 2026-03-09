from django.db import models
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.search import index


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
        context['projects'] = (
            ProjectPage.objects.child_of(self)
            .live()
            .order_by('-date')
        )
        return context


class ProjectPage(Page):
    """Individual project / tutorial article."""

    date = models.DateField()
    category = models.ForeignKey(
        'blog.Category',
        on_delete=models.PROTECT,
        null=True,
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
    body = RichTextField(features=['h2', 'h3', 'bold', 'italic', 'ol', 'ul', 'link', 'image'])

    parent_page_types = ['blog.ProjectsIndexPage']
    subpage_types = []

    content_panels = Page.content_panels + [
        FieldPanel('date'),
        FieldPanel('category'),
        FieldPanel('excerpt'),
        FieldPanel('cover_image'),
        FieldPanel('body'),
    ]

    search_fields = Page.search_fields + [
        index.SearchField('body'),
        index.SearchField('excerpt'),
    ]


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
