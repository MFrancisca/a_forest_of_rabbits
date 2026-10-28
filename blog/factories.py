import factory
import factory.fuzzy
from factory.django import DjangoModelFactory
import wagtail_factories
from blog.models import Category, ProjectsIndexPage, ProjectPage, AboutPage, HomePage


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
    body = factory.LazyAttribute(lambda o: [
        {'type': 'rich_text', 'value': {'title': '', 'text': f'<p>Body content for {o.title}</p>'}},
    ])

    class Meta:
        model = ProjectPage

    @factory.post_generation
    def categories(self, create, extracted, **kwargs):
        if create and extracted:
            self.categories.set(extracted)


class AboutPageFactory(wagtail_factories.PageFactory):
    title = 'About'
    slug = factory.Sequence(lambda n: f'about-{n}')
    body = '<p>About this site.</p>'

    class Meta:
        model = AboutPage


class HomePageFactory(wagtail_factories.PageFactory):
    title = 'A Forest of Rabbits'
    slug = factory.Sequence(lambda n: f'home-{n}')
    intro = '<p>Welcome to my forest.</p>'

    class Meta:
        model = HomePage
