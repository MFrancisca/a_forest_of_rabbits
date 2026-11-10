"""Create or update every project page's image collection (blog/image_collections.py).

Saving a project page already syncs its collection; run this once per environment
to give existing projects theirs, or after copying content between databases.
Safe to re-run: it only moves images between collections and never deletes any.

    python manage.py sync_project_collections --dry-run
    python manage.py sync_project_collections
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from blog.image_collections import latest_content, sync_project_collection
from blog.models import ProjectPage


class _DryRunRollback(Exception):
    pass


class Command(BaseCommand):
    help = "Create or update each project page's image collection (never deletes images)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Report what would change, then roll everything back.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        try:
            with transaction.atomic():
                self._sync_all()
                if dry_run:
                    raise _DryRunRollback
        except _DryRunRollback:
            self.stdout.write(self.style.WARNING('[DRY RUN] Nothing was changed.'))

    def _sync_all(self):
        total = changed = 0
        for page in ProjectPage.objects.order_by('path'):
            total += 1
            result = sync_project_collection(latest_content(page))
            if result.changed:
                changed += 1
            self.stdout.write(self._describe(page, result))
            if result.kept_elsewhere:
                self.stdout.write(self.style.WARNING(
                    f'    already in another project\'s collection, left there: '
                    f'{", ".join(map(str, result.kept_elsewhere))}'
                ))
        self.stdout.write(self.style.SUCCESS(
            f'{total} project pages, {changed} collections changed.'
        ))

    @staticmethod
    def _describe(page, result):
        parts = []
        if result.created:
            parts.append('created')
        if result.renamed_from:
            parts.append(f'renamed from "{result.renamed_from}"')
        parts.append(f'+{len(result.added)} images')
        parts.append(f'-{len(result.removed)} images')
        return f'  {page.title}: ' + ', '.join(parts)
