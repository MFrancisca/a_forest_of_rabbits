# Data migration: wrap existing body_legacy RichText HTML into a single
# 'rich_text' StreamField block (empty title) so no existing content is lost.

from django.db import migrations


def copy_body_legacy_to_body(apps, schema_editor):
    ProjectPage = apps.get_model('blog', 'ProjectPage')
    for page in ProjectPage.objects.exclude(body_legacy=''):
        page.body = [{'type': 'rich_text', 'value': {'title': '', 'text': page.body_legacy}}]
        page.save(update_fields=['body'])


def reverse_copy(apps, schema_editor):
    ProjectPage = apps.get_model('blog', 'ProjectPage')
    ProjectPage.objects.update(body=[])


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0006_projectpage_body'),
    ]

    operations = [
        migrations.RunPython(copy_body_legacy_to_body, reverse_copy),
    ]
