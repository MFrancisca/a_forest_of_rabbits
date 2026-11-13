import pytest
from django.db import IntegrityError

from journal.models import PIGMENTS_TAG_SLUG, Tag

pytestmark = pytest.mark.django_db


def test_tag_slug_filled_from_name():
    assert Tag.objects.create(name='Work in Progress').slug == 'work-in-progress'


def test_tag_slug_kept_on_rename():
    tag = Tag.objects.create(name='Techniques')
    tag.name = 'Painting techniques'
    tag.save()
    tag.refresh_from_db()
    assert tag.slug == 'techniques'


def test_pigments_tag_seeded():
    assert Tag.objects.get(slug=PIGMENTS_TAG_SLUG).name == 'Pigments'


def test_tag_name_unique():
    with pytest.raises(IntegrityError):
        Tag.objects.create(name='Pigments', slug='pigments-2')


# --- Pages ---------------------------------------------------------------

from blog.factories import HomePageFactory, ProjectPageFactory  # noqa: E402
from journal.factories import BlogPostPageFactory  # noqa: E402
from journal.models import SUMMARY_LENGTH, BlogIndexPage, BlogPostPage  # noqa: E402


def _text(html):
    return {'type': 'rich_text', 'value': {'title': '', 'text': html}}


def _image_block():
    import wagtail_factories
    return {'type': 'image', 'value': {'image': wagtail_factories.ImageFactory().pk, 'caption': ''}}


def test_display_summary_uses_summary(blog_index):
    post = BlogPostPageFactory(parent=blog_index, summary='Short.')
    assert post.display_summary == 'Short.'


def test_display_summary_falls_back_to_body(blog_index):
    post = BlogPostPageFactory(parent=blog_index, body=[_image_block(), _text('<p>Hello <b>world</b> &amp; more</p>')])
    assert post.display_summary == 'Hello world & more'


def test_display_summary_skips_empty_text_blocks(blog_index):
    post = BlogPostPageFactory(parent=blog_index, body=[_text('<p></p>'), _text('<p>Second</p>')])
    assert post.display_summary == 'Second'


def test_display_summary_truncates_at_word(blog_index):
    source = 'pigment ' * 80
    post = BlogPostPageFactory(parent=blog_index, body=[_text(f'<p>{source}</p>')])
    summary = post.display_summary
    assert summary.endswith('…')
    assert len(summary) <= SUMMARY_LENGTH + 1
    kept = summary[:-1]
    assert kept.endswith('pigment')
    assert source.startswith(kept + ' ')


def test_display_summary_not_cut_has_no_ellipsis(blog_index):
    post = BlogPostPageFactory(parent=blog_index, body=[_text('<p>A short note.</p>')])
    assert post.display_summary == 'A short note.'


def test_display_summary_empty_without_text(blog_index):
    post = BlogPostPageFactory(parent=blog_index, body=[_image_block()])
    assert post.display_summary == ''


def test_tags_and_projects_survive_publish(blog_index, projects_index, pigments_tag):
    project = ProjectPageFactory(parent=projects_index, live=True)
    post = BlogPostPageFactory(parent=blog_index)
    post.tags.set([pigments_tag])
    post.related_projects.set([project])
    post.save_revision().publish()
    post = BlogPostPage.objects.get(pk=post.pk)
    assert list(post.tags.all()) == [pigments_tag]
    assert [p.pk for p in post.related_projects.all()] == [project.pk]
    assert [p.pk for p in project.journal_posts.all()] == [post.pk]


def test_page_tree_rules(root_page, wagtail_site, blog_index):
    home = HomePageFactory(parent=root_page)
    assert BlogIndexPage.can_create_at(home) is False  # max_count reached by blog_index
    assert BlogPostPage.can_create_at(blog_index)
    assert not BlogPostPage.can_create_at(home)
    assert BlogIndexPage.max_count == 1
    assert 'journal.BlogIndexPage' in [f'{m._meta.app_label}.{m.__name__}' for m in home.specific_class.allowed_subpage_models()]


def test_tag_clean_fills_slug_so_unique_check_catches_collision():
    from django.core.exceptions import ValidationError
    Tag.objects.create(name='Work in progress')
    tag = Tag(name='Work-in-progress')
    with pytest.raises(ValidationError) as exc:
        tag.full_clean()
    assert 'slug' in exc.value.message_dict


def test_tag_clean_rejects_name_without_slug():
    from django.core.exceptions import ValidationError
    with pytest.raises(ValidationError):
        Tag(name='!!!').full_clean()


def test_unsaved_project_preview_has_no_updates(rf):
    from blog.models import ProjectPage
    context = ProjectPage(title='New').get_context(rf.get('/'))
    assert list(context['journal_updates']) == []
