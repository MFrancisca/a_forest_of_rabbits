import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from pigments.models import (
    Brand, ColorFamily, Country, Formula, FormulaPart,
    Manuscript, Paint, Pigment, PigmentFamily, PigmentManuscript, Source,
)

DEFAULT_DATA_FILE = (
    Path(__file__).resolve().parent.parent.parent / 'data' / 'initial_pigments.json'
)

# Values in a part's "parts" field that mean "a trace amount — too small to measure"
# rather than a numeric quantity. Compared case-insensitively.
TRACE_MARKERS = {'Δ', 'delta', 'trace'}


def _parse_parts_quantity(value):
    """Return (parts, is_trace) for a FormulaPart's raw "parts" value."""
    if isinstance(value, str) and value.strip().lower() in {m.lower() for m in TRACE_MARKERS}:
        return None, True
    return value, False


class Command(BaseCommand):
    help = 'Load pigment data from a JSON file (idempotent — safe to re-run)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--data-file',
            type=Path,
            default=DEFAULT_DATA_FILE,
            help='Path to pigments JSON file (default: pigments/data/initial_pigments.json)',
        )

    def handle(self, *args, **options):
        data_file = options['data_file']
        if not data_file.exists():
            self.stderr.write(f'Data file not found: {data_file}')
            return

        with data_file.open() as f:
            data = json.load(f)

        self.sources = self._load_sources(data.get('sources', {}))

        created_count = 0
        for entry in data['pigments']:
            if self._load_pigment(entry):
                created_count += 1

        total = Pigment.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'Initial pigments loaded. {created_count} new, {total} total in database.'
        ))

    def _load_sources(self, sources_data):
        """Create Source rows from the top-level 'sources' map; return {key: Source}."""
        sources = {}
        for key, src in sources_data.items():
            source, _ = Source.objects.get_or_create(
                title=src['title'],
                defaults={
                    'kind': src.get('kind', Source.KIND_PAPER),
                    'authors': src.get('authors', ''),
                    'publication': src.get('publication', ''),
                    'year': src.get('year'),
                    'doi': src.get('doi', ''),
                    'url': src.get('url', ''),
                },
            )
            sources[key] = source
        return sources

    def _source(self, key):
        """Resolve a source key from the data file, failing loudly on typos."""
        if not key:
            return None
        try:
            return self.sources[key]
        except KeyError:
            raise CommandError(f'Unknown source key "{key}": add it to the top-level "sources" map.')

    def _load_pigment(self, entry):
        """Load one pigment entry; returns True if it was newly created."""
        color_fam, _ = ColorFamily.objects.get_or_create(name=entry['color_family'])
        pigment_fam, _ = PigmentFamily.objects.get_or_create(name=entry['pigment_family'])

        pigment, created = Pigment.objects.get_or_create(
            name=entry['name'],
            defaults={
                'color_family': color_fam,
                'pigment_family': pigment_fam,
                'description': entry.get('description', ''),
            },
        )

        pigment_sources = [self._source(k) for k in entry.get('sources', [])]
        if pigment_sources:
            # ParentalManyToManyField: changes are only written on save().
            pigment.sources.add(*pigment_sources)
            pigment.save()

        for formula_data in entry.get('formulas', []):
            brand, _ = Brand.objects.get_or_create(name=formula_data['brand'])
            formula, _ = Formula.objects.get_or_create(
                pigment=pigment,
                brand=brand,
                defaults={'notes': formula_data.get('notes', '')},
            )
            if not formula.parts.exists():
                for part_data in formula_data.get('parts', []):
                    paint_brand, _ = Brand.objects.get_or_create(name=part_data['paint_brand'])
                    paint, _ = Paint.objects.get_or_create(
                        name=part_data['paint_name'],
                        brand=paint_brand,
                        defaults={
                            'abbreviation': part_data.get('abbreviation', ''),
                            'hex_color': part_data.get('hex_color', ''),
                        },
                    )
                    parts_qty, is_trace = _parse_parts_quantity(part_data['parts'])
                    FormulaPart.objects.create(
                        formula=formula,
                        paint=paint,
                        parts=parts_qty,
                        is_trace=is_trace,
                    )

        for ms_data in entry.get('manuscripts', []):
            country, _ = Country.objects.get_or_create(name=ms_data['country'])
            manuscript, _ = Manuscript.objects.get_or_create(
                name=ms_data['name'],
                defaults={
                    'country': country,
                    'date_start': ms_data.get('date_start'),
                    'date_end': ms_data.get('date_end'),
                },
            )
            source = self._source(ms_data.get('source'))
            link = pigment.manuscript_links.filter(manuscript=manuscript).first()
            if link is None:
                PigmentManuscript.objects.create(
                    pigment=pigment,
                    manuscript=manuscript,
                    page_reference=ms_data.get('page_reference', ''),
                    notes=ms_data.get('notes', ''),
                    source=source,
                    source_detail=ms_data.get('source_detail', ''),
                )
            elif link.source is None and source is not None:
                # Backfill a citation on a link loaded before sources existed;
                # never overwrite one set by hand in the admin.
                link.source = source
                link.source_detail = ms_data.get('source_detail', '')
                link.save(update_fields=['source', 'source_detail'])

        return created
