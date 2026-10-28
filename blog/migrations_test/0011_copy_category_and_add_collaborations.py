# Data migration: copy each ProjectPage's single category_legacy into the new
# categories M2M (as its one member), and create the new "Collaborations"
# category requested alongside this change.

from django.db import migrations


def copy_category_and_add_collaborations(apps, schema_editor):
    ProjectPage = apps.get_model('blog', 'ProjectPage')
    Category = apps.get_model('blog', 'Category')

    for page in ProjectPage.objects.exclude(category_legacy__isnull=True):
        page.categories.add(page.category_legacy_id)

    Category.objects.get_or_create(name='Collaborations')


def reverse(apps, schema_editor):
    Category = apps.get_model('blog', 'Category')
    ProjectPage = apps.get_model('blog', 'ProjectPage')
    for page in ProjectPage.objects.all():
        page.categories.clear()
    Category.objects.filter(name='Collaborations').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0010_projectpage_categories'),
    ]

    operations = [
        migrations.RunPython(copy_category_and_add_collaborations, reverse),
    ]
