import factory
import factory.fuzzy
from factory.django import DjangoModelFactory
import wagtail_factories
from blog.models import Category, ProjectsIndexPage, ProjectPage, AboutPage


class CategoryFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: f'Category {n}')

    class Meta:
        model = Category


class ProjectsIndexPageFactory(wagtail_factories.PageFactory):
    title = 'Projects'
    slug = factory.Sequence(lambda n: f'projects-{n}')

    class Meta:
        model = ProjectsIndexPage


class ProjectPageFactory(wagtail_factories.PageFactory):
    title = factory.Sequence(lambda n: f'Project {n}')
    date = factory.Faker('date_object')
    excerpt = factory.Sequence(lambda n: f'Excerpt for project {n}')
    body = factory.Sequence(lambda n: f'<p>Body content for project {n}</p>')
    category = factory.SubFactory(CategoryFactory)

    class Meta:
        model = ProjectPage


class AboutPageFactory(wagtail_factories.PageFactory):
    title = 'About'
    slug = factory.Sequence(lambda n: f'about-{n}')
    body = '<p>About this site.</p>'

    class Meta:
        model = AboutPage
