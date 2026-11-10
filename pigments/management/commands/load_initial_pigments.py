import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

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


class _DryRunRollback(Exception):
    """Raised inside the transaction to undo a --dry-run."""


# Every kind of row the loader can create and lists in its report, so a typo
# that would add a stray family, country or brand shows up in the dry run.
REPORTED_KINDS = (
    'pigments', 'manuscripts', 'sources',
    'color families', 'pigment families', 'countries', 'brands', 'paints',
)


class Command(BaseCommand):
    help = (
        'Load pigment data from one or more JSON files. Only adds rows, never '
        'deletes or overwrites, so it is safe to re-run. All files load in one '
        'transaction: if anything fails, nothing is written.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--data-file',
            type=Path,
            nargs='+',
            default=[DEFAULT_DATA_FILE],
            help='One or more pigment JSON files, loaded in the order given '
                 '(default: pigments/data/initial_pigments.json)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created, then roll everything back.',
        )

    def handle(self, *args, **options):
        data_files = options['data_file']
        if isinstance(data_files, (str, Path)):  # call_command(data_file=path)
            data_files = [data_files]
        data_files = [Path(f) for f in data_files]
        missing = [str(f) for f in data_files if not f.exists()]
        if missing:
            raise CommandError(f'Data file not found: {", ".join(missing)}')

        dry_run = options['dry_run']
        self.stdout.write(f'Target database: {self._describe_database()}')
        self.created = {kind: [] for kind in REPORTED_KINDS}
        self.counts = {'links': 0, 'backfilled': 0, 'formulas': 0}
        self.warnings = []

        try:
            with transaction.atomic():
                for data_file in data_files:
                    data = self._read(data_file)
                    self.sources = self._load_sources(data.get('sources', {}))
                    for entry in data['pigments']:
                        self._load_pigment(entry)
                if dry_run:
                    raise _DryRunRollback
        except _DryRunRollback:
            pass

        self._report(dry_run)

    def _read(self, data_file):
        """Parse one data file, failing with its name if it isn't loader JSON."""
        try:
            with data_file.open() as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise CommandError(f'{data_file} is not valid JSON: {e}')
        if not isinstance(data, dict) or not isinstance(data.get('pigments'), list):
            raise CommandError(
                f'{data_file} has no top-level "pigments" list, so it is not a '
                'load_initial_pigments data file.'
            )
        return data

    def _get_or_create(self, model, kind, **lookup):
        """get_or_create a reference row, recording it for the report if new."""
        obj, created = model.objects.get_or_create(**lookup)
        if created:
            self.created[kind].append(str(obj))
        return obj

    def _describe_database(self):
        settings = connection.settings_dict
        host = settings.get('HOST') or 'local'
        port = f":{settings['PORT']}" if settings.get('PORT') else ''
        return f"{connection.vendor} {settings.get('NAME')} on {host}{port}"

    def _report(self, dry_run):
        verb = 'Would create' if dry_run else 'Created'
        for kind in REPORTED_KINDS:
            names = self.created[kind]
            self.stdout.write(f'{verb} {len(names)} {kind}' + (':' if names else '.'))
            for name in names:
                self.stdout.write(f'  + {name}')
        self.stdout.write(f"{verb} {self.counts['links']} pigment–manuscript links.")
        self.stdout.write(f"{verb} {self.counts['formulas']} formulas.")
        if self.counts['backfilled']:
            self.stdout.write(f"Filled in a missing source on {self.counts['backfilled']} existing links.")
        for warning in self.warnings:
            self.stdout.write(self.style.WARNING(f'Warning: {warning}'))
        if dry_run:
            self.stdout.write(self.style.WARNING('Dry run: nothing was saved.'))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'Pigments loaded. {Pigment.objects.count()} pigments in database.'
            ))

    def _warn_if_near_duplicate(self, model, name, label):
        """A new name that differs only in case usually means a duplicate."""
        twin = model.objects.filter(name__iexact=name).exclude(name=name).first()
        if twin:
            self.warnings.append(
                f'new {label} "{name}" differs only in case from existing "{twin.name}".'
            )

    def _load_sources(self, sources_data):
        """Create Source rows from the top-level 'sources' map; return {key: Source}."""
        sources = {}
        for key, src in sources_data.items():
            source, created = Source.objects.get_or_create(
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
            if created:
                self.created['sources'].append(source.title)
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
        """Load one pigment entry."""
        color_fam = self._get_or_create(ColorFamily, 'color families', name=entry['color_family'])
        pigment_fam = self._get_or_create(
            PigmentFamily, 'pigment families', name=entry['pigment_family'])

        pigment, created = Pigment.objects.get_or_create(
            name=entry['name'],
            defaults={
                'color_family': color_fam,
                'pigment_family': pigment_fam,
                'description': entry.get('description', ''),
            },
        )
        if created:
            self._warn_if_near_duplicate(Pigment, pigment.name, 'pigment')
            self.created['pigments'].append(pigment.name)
            if not pigment.description:
                self.warnings.append(
                    f'new pigment "{pigment.name}" has no description '
                    '(was a file that defines it skipped?).'
                )
        elif (pigment.color_family_id, pigment.pigment_family_id) != (color_fam.pk, pigment_fam.pk):
            self.warnings.append(
                f'existing pigment "{pigment.name}" is {pigment.color_family} / '
                f'{pigment.pigment_family} in the database but {color_fam} / {pigment_fam} '
                'in the file; the database value is kept.'
            )

        pigment_sources = [self._source(k) for k in entry.get('sources', [])]
        if pigment_sources:
            # ParentalManyToManyField: changes are only written on save().
            pigment.sources.add(*pigment_sources)
            pigment.save()

        for formula_data in entry.get('formulas', []):
            brand = self._get_or_create(Brand, 'brands', name=formula_data['brand'])
            formula, formula_created = Formula.objects.get_or_create(
                pigment=pigment,
                brand=brand,
                defaults={'notes': formula_data.get('notes', '')},
            )
            if formula_created:
                self.counts['formulas'] += 1
            if not formula.parts.exists():
                for part_data in formula_data.get('parts', []):
                    paint_brand = self._get_or_create(
                        Brand, 'brands', name=part_data['paint_brand'])
                    paint = self._get_or_create(
                        Paint, 'paints',
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
            country = self._get_or_create(Country, 'countries', name=ms_data['country'])
            manuscript, ms_created = Manuscript.objects.get_or_create(
                name=ms_data['name'],
                defaults={
                    'country': country,
                    'date_start': ms_data.get('date_start'),
                    'date_end': ms_data.get('date_end'),
                },
            )
            if ms_created:
                self._warn_if_near_duplicate(Manuscript, manuscript.name, 'manuscript')
                self.created['manuscripts'].append(manuscript.name)
            elif (manuscript.country_id, manuscript.date_start, manuscript.date_end) != (
                    country.pk, ms_data.get('date_start'), ms_data.get('date_end')):
                self.warnings.append(
                    f'existing manuscript "{manuscript.name}" is {manuscript.country}, '
                    f'{manuscript.date_start}–{manuscript.date_end} in the database but '
                    f"{country}, {ms_data.get('date_start')}–{ms_data.get('date_end')} "
                    'in the file; the database value is kept.'
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
                self.counts['links'] += 1
            elif link.source is None and source is not None:
                # Backfill a citation on a link loaded before sources existed;
                # never overwrite one set by hand in the admin.
                link.source = source
                link.source_detail = ms_data.get('source_detail', '')
                link.save(update_fields=['source', 'source_detail'])
                self.counts['backfilled'] += 1
