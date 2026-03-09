from django.db import models  # noqa: F401
from wagtail.models import Page


class Category(models.Model):
    pass

    class Meta:
        app_label = 'blog'


class ProjectsIndexPage(Page):
    pass


class ProjectPage(Page):
    pass


class AboutPage(Page):
    pass
