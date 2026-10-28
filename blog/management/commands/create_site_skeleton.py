from django.core.management.base import BaseCommand
from wagtail.models import Page, Site


DEFAULT_WAGTAIL_PLACEHOLDER_TITLE = 'Welcome to your new Wagtail site!'


class Command(BaseCommand):
    help = 'Create HomePage, ProjectsIndexPage, and AboutPage if they do not exist (idempotent).'

    def handle(self, *args, **options):
        root = Page.objects.filter(depth=1).first()
        if not root:
            self.stderr.write('No root page found. Run wagtail migrations first.')
            return

        from blog.models import HomePage, ProjectsIndexPage, AboutPage, ProjectPage

        # HomePage must be the Wagtail site root (not a sibling of Projects/About) —
        # Wagtail only resolves "/" to Site.root_page itself, and only descendants
        # of root_page get their URLs resolved under that site. So Projects and
        # About are moved to become HomePage's children below; their public URLs
        # are unaffected since the site-root prefix is subtracted when computing
        # page.url (verified: /home/projects/ still resolves to /projects/).
        home = HomePage.objects.first()
        if not home:
            placeholder = root.get_children().filter(
                title=DEFAULT_WAGTAIL_PLACEHOLDER_TITLE,
            ).first()
            if placeholder:
                placeholder.delete()
                self.stdout.write('Removed default Wagtail placeholder page.')

            home = HomePage(
                title='A Forest of Rabbits',
                slug='home',
                intro='<p>Welcome to my forest, where all my rabbits live.</p>',
            )
            root.add_child(instance=home)
            home.save_revision().publish()
            self.stdout.write(self.style.SUCCESS('Created HomePage at /'))
        else:
            self.stdout.write('HomePage already exists — skipping.')

        site = Site.objects.filter(is_default_site=True).first()
        if site and site.root_page_id != home.id:
            site.root_page = home
            site.save()
            self.stdout.write(self.style.SUCCESS('Pointed default Site.root_page at HomePage'))

        index = ProjectsIndexPage.objects.first()
        if not index:
            index = ProjectsIndexPage(title='Projects', slug='projects')
            home.add_child(instance=index)
            index.save_revision().publish()
            self.stdout.write(self.style.SUCCESS('Created ProjectsIndexPage at /projects/'))
        elif index.get_parent().id != home.id:
            index.move(home, pos='last-child')
            self.stdout.write(self.style.SUCCESS('Moved ProjectsIndexPage under HomePage'))
        else:
            self.stdout.write('ProjectsIndexPage already exists — skipping.')

        about = AboutPage.objects.first()
        if not about:
            about = AboutPage(title='About', slug='about', body='<p>About page content — edit this in the Wagtail admin.</p>')
            home.add_child(instance=about)
            about.save_revision().publish()
            self.stdout.write(self.style.SUCCESS('Created AboutPage at /about/'))
        elif about.get_parent().id != home.id:
            about.move(home, pos='last-child')
            self.stdout.write(self.style.SUCCESS('Moved AboutPage under HomePage'))
        else:
            self.stdout.write('AboutPage already exists — skipping.')

        # Classes doesn't belong in the Projects index's category filtering —
        # pull it out to be a standalone top-level page at /classes/.
        classes = ProjectPage.objects.filter(slug='classes').first()
        if classes and classes.get_parent().id != home.id:
            classes.move(home, pos='last-child')
            if classes.categories.exists():
                classes.categories.clear()
                classes.save_revision().publish()
            self.stdout.write(self.style.SUCCESS('Moved Classes out of Projects to /classes/'))
