import json

import pytest
from django.core.management import call_command

from pigments.models import FormulaPart, Pigment


@pytest.mark.django_db
def test_load_initial_pigments_creates_pigments():
    call_command('load_initial_pigments')
    assert Pigment.objects.count() >= 3


@pytest.mark.django_db
def test_load_initial_pigments_idempotent():
    call_command('load_initial_pigments')
    count_after_first = Pigment.objects.count()
    call_command('load_initial_pigments')
    assert Pigment.objects.count() == count_after_first


@pytest.mark.django_db
def test_load_initial_pigments_parses_trace_amount(tmp_path):
    """A "Δ" (or "delta"/"trace") parts value loads as a trace FormulaPart, not a number."""
    data_file = tmp_path / 'trace_pigments.json'
    data_file.write_text(json.dumps({
        'pigments': [
            {
                'name': 'Test Trace Pigment',
                'color_family': 'Yellow',
                'pigment_family': 'Ochres',
                'description': '',
                'formulas': [
                    {
                        'brand': 'Test Brand',
                        'notes': '',
                        'parts': [
                            {'paint_name': 'Base Paint', 'paint_brand': 'Test Brand',
                             'abbreviation': 'B', 'hex_color': '', 'parts': 3},
                            {'paint_name': 'Trace Paint', 'paint_brand': 'Test Brand',
                             'abbreviation': 'T', 'hex_color': '', 'parts': 'Δ'},
                        ],
                    },
                ],
                'manuscripts': [],
            },
        ],
    }))

    call_command('load_initial_pigments', data_file=data_file)

    part = FormulaPart.objects.get(paint__name='Trace Paint')
    assert part.is_trace is True
    assert part.parts is None


def _write(tmp_path, data):
    data_file = tmp_path / 'sourced.json'
    data_file.write_text(json.dumps(data))
    return str(data_file)


SOURCED_DATA = {
    'sources': {
        'kells': {'kind': 'paper', 'authors': 'Bioletti, S.', 'title': 'Kells Raman',
                  'publication': 'JRS', 'year': 2009, 'doi': '10.1002/jrs.2231', 'url': ''},
        'web': {'kind': 'website', 'title': 'Pigment page', 'url': 'https://example.org/pigment'},
    },
    'pigments': [{
        'name': 'Sourced Orpiment',
        'color_family': 'Yellow',
        'pigment_family': 'Arsenic Pigments',
        'sources': ['web'],
        'manuscripts': [{
            'name': 'Book of Kells', 'country': 'Ireland', 'date_start': 800, 'date_end': 1100,
            'page_reference': '', 'notes': 'Yellow.', 'source': 'kells', 'source_detail': 'Table 1',
        }],
    }],
}


@pytest.mark.django_db
def test_loader_creates_sources_and_cites_them(tmp_path):
    from pigments.models import Source
    path = _write(tmp_path, SOURCED_DATA)
    call_command('load_initial_pigments', '--data-file', path)
    call_command('load_initial_pigments', '--data-file', path)

    assert Source.objects.count() == 2
    pigment = Pigment.objects.get(name='Sourced Orpiment')
    assert [s.title for s in pigment.sources.all()] == ['Pigment page']
    link = pigment.manuscript_links.get()
    assert link.source.doi == '10.1002/jrs.2231'
    assert link.source_detail == 'Table 1'


@pytest.mark.django_db
def test_loader_backfills_missing_source_but_keeps_manual_one(tmp_path):
    from pigments.factories import SourceFactory
    data = json.loads(json.dumps(SOURCED_DATA))
    del data['pigments'][0]['manuscripts'][0]['source']
    call_command('load_initial_pigments', '--data-file', _write(tmp_path, data))
    link = Pigment.objects.get(name='Sourced Orpiment').manuscript_links.get()
    assert link.source is None

    call_command('load_initial_pigments', '--data-file', _write(tmp_path, SOURCED_DATA))
    link.refresh_from_db()
    assert link.source.title == 'Kells Raman'

    manual = SourceFactory()
    link.source = manual
    link.save()
    call_command('load_initial_pigments', '--data-file', _write(tmp_path, SOURCED_DATA))
    link.refresh_from_db()
    assert link.source == manual


@pytest.mark.django_db
def test_loader_rejects_unknown_source_key(tmp_path):
    from django.core.management.base import CommandError
    data = json.loads(json.dumps(SOURCED_DATA))
    data['pigments'][0]['manuscripts'][0]['source'] = 'typo'
    with pytest.raises(CommandError, match='typo'):
        call_command('load_initial_pigments', '--data-file', _write(tmp_path, data))


@pytest.mark.django_db
def test_manuscript_pigments_data_file_loads():
    from pigments.models import PigmentManuscript
    call_command('load_initial_pigments', '--data-file', 'pigments/data/manuscript_pigments.json')
    assert PigmentManuscript.objects.count() == 47
    assert not PigmentManuscript.objects.filter(source__isnull=True).exists()
