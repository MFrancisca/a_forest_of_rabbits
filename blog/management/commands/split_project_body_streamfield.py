"""
Management command: split_project_body_streamfield

One-time: every ProjectPage.body currently holds its entire original content
as a single 'rich_text' block (a leftover of the data migration that moved
content out of the old body_legacy RichTextField — see
blog/migrations/0007_copy_body_legacy_to_body.py). This command re-parses
that block's HTML and splits it into multiple blocks:

- Every paragraph/heading/list becomes its own 'rich_text' block.
- A single standalone image embed becomes an 'image' block.
- Two or more consecutive image embeds become one 'carousel' block.

Usage
-----
    python manage.py split_project_body_streamfield --dry-run
    python manage.py split_project_body_streamfield

A page is only touched if its body is still in the single-block "unsplit"
shape, so this is safe to re-run — already-split pages are skipped.
"""

from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from wagtail.images import get_image_model

from blog.models import ProjectPage

Image = get_image_model()


def _is_image_embed(tag):
    return tag.name == 'embed' and tag.get('embedtype') == 'image'


def _has_meaningful_content(tag):
    return bool(tag.get_text(strip=True)) or bool(tag.find(['img', 'embed']))


def parse_nodes(html):
    """Flatten the body HTML into ('text', html) / ('image', id, alt) nodes,
    dropping empty spacer paragraphs."""
    soup = BeautifulSoup(f'<div>{html}</div>', 'html.parser')
    nodes = []
    for child in soup.div.children:
        if not getattr(child, 'name', None):
            continue  # stray whitespace between tags
        if _is_image_embed(child):
            image_id = child.get('id', '')
            if image_id.isdigit():
                nodes.append(('image', int(image_id), child.get('alt', '')))
            continue
        if _has_meaningful_content(child):
            nodes.append(('text', str(child)))
    return nodes


def group_nodes(nodes):
    """Each text node becomes its own rich_text block. Runs of consecutive
    image nodes become one carousel (2+) or one image block (exactly 1)."""
    blocks = []
    i = 0
    while i < len(nodes):
        if nodes[i][0] == 'text':
            blocks.append(('rich_text', {'title': '', 'text': nodes[i][1]}))
            i += 1
            continue

        run = []
        while i < len(nodes) and nodes[i][0] == 'image':
            run.append(nodes[i])
            i += 1

        if len(run) == 1:
            _, image_id, alt = run[0]
            blocks.append(('image', {'image': image_id, 'caption': alt}))
        else:
            blocks.append((
                'carousel',
                [{'image': image_id, 'caption': alt} for _, image_id, alt in run],
            ))
    return blocks


class Command(BaseCommand):
    help = (
        "One-time: split each ProjectPage.body's single rich_text block into "
        "multiple blocks (one rich_text per paragraph, image/carousel blocks "
        "for embedded images)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Report what would change without saving anything.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        if dry_run:
            self.stdout.write(self.style.WARNING('[DRY RUN] No pages will be saved.'))

        existing_image_ids = set(Image.objects.values_list('id', flat=True))

        processed = 0
        skipped = 0
        missing_images = []

        for page in ProjectPage.objects.all().order_by('pk'):
            if not self._is_unsplit(page.body):
                skipped += 1
                continue

            html = page.body[0].value['text'].source
            blocks = group_nodes(parse_nodes(html))

            new_body = []
            for block_type, value in blocks:
                if block_type == 'rich_text':
                    new_body.append({'type': 'rich_text', 'value': value})
                elif block_type == 'image':
                    if value['image'] not in existing_image_ids:
                        missing_images.append((page.title, value['image']))
                        continue
                    new_body.append({'type': 'image', 'value': value})
                else:  # carousel
                    present = []
                    for item in value:
                        if item['image'] not in existing_image_ids:
                            missing_images.append((page.title, item['image']))
                        else:
                            present.append(item)
                    if len(present) >= 2:
                        new_body.append({'type': 'carousel', 'value': present})
                    elif len(present) == 1:
                        new_body.append({'type': 'image', 'value': present[0]})

            counts = {t: sum(1 for b in new_body if b['type'] == t) for t in ('rich_text', 'image', 'carousel')}
            self.stdout.write(
                f"{page.title!r}: {len(new_body)} blocks "
                f"({counts['rich_text']} rich_text, {counts['image']} image, {counts['carousel']} carousel)"
            )

            if not dry_run:
                page.body = new_body
                page.save_revision().publish()

            processed += 1

        if missing_images:
            self.stdout.write(self.style.WARNING(
                'Image ids referenced but not found in wagtailimages.Image (dropped): '
                + ', '.join(f'{title!r}:{image_id}' for title, image_id in missing_images)
            ))

        verb = 'Would process' if dry_run else 'Processed'
        self.stdout.write(self.style.SUCCESS(
            f'{verb} {processed} page(s); skipped {skipped} (already split or empty).'
        ))

    @staticmethod
    def _is_unsplit(body):
        return len(body) == 1 and body[0].block_type == 'rich_text'
