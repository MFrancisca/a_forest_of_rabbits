import factory
import wagtail_factories
from factory.django import DjangoModelFactory

from journal.models import BlogIndexPage, BlogPostPage, Tag


class TagFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: f'Tag {n}')

    class Meta:
        model = Tag


class BlogIndexPageFactory(wagtail_factories.PageFactory):
    title = 'Blog'
    slug = 'blog'

    class Meta:
        model = BlogIndexPage


class BlogPostPageFactory(wagtail_factories.PageFactory):
    title = factory.Sequence(lambda n: f'Post {n}')
    date = factory.Faker('date_object')
    body = factory.LazyAttribute(lambda o: [
        {'type': 'rich_text', 'value': {'title': '', 'text': f'<p>Body of {o.title}</p>'}},
    ])

    class Meta:
        model = BlogPostPage
        skip_postgeneration_save = True

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if create and extracted:
            # ParentalManyToManyField only writes the relation on save().
            self.tags.set(extracted)
            self.save()

    @factory.post_generation
    def related_projects(self, create, extracted, **kwargs):
        if create and extracted:
            self.related_projects.set(extracted)
            self.save()
