import json
from pathlib import Path

from django.core.management.base import BaseCommand

from pigments.models import (
    Brand, ColorFamily, Country, Formula, FormulaPart,
    Manuscript, Paint, Pigment, PigmentFamily, PigmentManuscript,
)

DEFAULT_DATA_FILE = (
    Path(__file__).resolve().parent.parent.parent / 'data' / 'initial_pigments.json'
)


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

        for entry in data['pigments']:
            self._load_pigment(entry)

        count = Pigment.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'Initial pigments loaded. Total: {count} pigments.'
        ))

    def _load_pigment(self, entry):
        color_fam, _ = ColorFamily.objects.get_or_create(name=entry['color_family'])
        pigment_fam, _ = PigmentFamily.objects.get_or_create(name=entry['pigment_family'])

        pigment, _ = Pigment.objects.get_or_create(
            name=entry['name'],
            defaults={
                'color_family': color_fam,
                'pigment_family': pigment_fam,
                'description': entry.get('description', ''),
            },
        )

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
                    FormulaPart.objects.create(
                        formula=formula,
                        paint=paint,
                        parts=part_data['parts'],
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
            if not pigment.manuscript_links.filter(manuscript=manuscript).exists():
                PigmentManuscript.objects.create(
                    pigment=pigment,
                    manuscript=manuscript,
                    page_reference=ms_data.get('page_reference', ''),
                    notes=ms_data.get('notes', ''),
                )
