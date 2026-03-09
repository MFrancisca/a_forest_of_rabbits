from django.core.management.base import BaseCommand
from wagtail.models import Page


class Command(BaseCommand):
    help = 'Create ProjectsIndexPage and AboutPage if they do not exist (idempotent).'

    def handle(self, *args, **options):
        root = Page.objects.filter(depth=1).first()
        if not root:
            self.stderr.write('No root page found. Run wagtail migrations first.')
            return

        from blog.models import ProjectsIndexPage, AboutPage

        if not root.get_children().filter(slug='projects').exists():
            index = ProjectsIndexPage(title='Projects', slug='projects')
            root.add_child(instance=index)
            index.save_revision().publish()
            self.stdout.write(self.style.SUCCESS('Created ProjectsIndexPage at /projects/'))
        else:
            self.stdout.write('ProjectsIndexPage already exists — skipping.')

        if not root.get_children().filter(slug='about').exists():
            about = AboutPage(title='About', slug='about')
            root.add_child(instance=about)
            about.save_revision().publish()
            self.stdout.write(self.style.SUCCESS('Created AboutPage at /about/'))
        else:
            self.stdout.write('AboutPage already exists — skipping.')
