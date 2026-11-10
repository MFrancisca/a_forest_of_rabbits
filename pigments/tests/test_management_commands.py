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


def _run(*args):
    from io import StringIO
    out = StringIO()
    call_command('load_initial_pigments', *args, stdout=out)
    return out.getvalue()


@pytest.mark.django_db
def test_dry_run_reports_but_saves_nothing(tmp_path):
    from pigments.models import Manuscript, Source
    output = _run('--data-file', _write(tmp_path, SOURCED_DATA), '--dry-run')

    assert 'Target database:' in output
    assert 'Would create 1 pigments:' in output
    assert '+ Sourced Orpiment' in output
    assert '+ Book of Kells' in output
    assert 'Would create 1 pigment–manuscript links.' in output
    assert 'Dry run: nothing was saved.' in output
    assert not Pigment.objects.exists()
    assert not Manuscript.objects.exists()
    assert not Source.objects.exists()


@pytest.mark.django_db
def test_dry_run_after_load_reports_nothing_new(tmp_path):
    path = _write(tmp_path, SOURCED_DATA)
    _run('--data-file', path)
    output = _run('--data-file', path, '--dry-run')
    assert 'Would create 0 pigments.' in output
    assert 'Would create 0 pigment–manuscript links.' in output


@pytest.mark.django_db
def test_several_files_load_in_order(tmp_path):
    first = tmp_path / 'first.json'
    first.write_text(json.dumps(SOURCED_DATA))
    second_data = {'pigments': [{
        'name': 'Sourced Orpiment', 'color_family': 'Yellow', 'pigment_family': 'Arsenic Pigments',
        'description': '',
        'manuscripts': [{'name': 'Book of Durrow', 'country': 'Ireland',
                         'date_start': 650, 'date_end': 700}],
    }]}
    second = tmp_path / 'second.json'
    second.write_text(json.dumps(second_data))

    output = _run('--data-file', str(first), str(second))

    pigment = Pigment.objects.get(name='Sourced Orpiment')
    assert sorted(pigment.manuscript_links.values_list('manuscript__name', flat=True)) == [
        'Book of Durrow', 'Book of Kells']
    assert 'Created 2 pigment–manuscript links.' in output


@pytest.mark.django_db
def test_failure_in_a_later_file_rolls_back_earlier_files(tmp_path):
    from django.core.management.base import CommandError
    good = tmp_path / 'good.json'
    good.write_text(json.dumps(SOURCED_DATA))
    bad_data = json.loads(json.dumps(SOURCED_DATA))
    bad_data['pigments'][0]['name'] = 'Other'
    bad_data['pigments'][0]['manuscripts'][0]['source'] = 'typo'
    bad = tmp_path / 'bad.json'
    bad.write_text(json.dumps(bad_data))

    with pytest.raises(CommandError, match='typo'):
        _run('--data-file', str(good), str(bad))
    assert not Pigment.objects.exists()


@pytest.mark.django_db
def test_missing_file_is_an_error(tmp_path):
    from django.core.management.base import CommandError
    with pytest.raises(CommandError, match='not found'):
        _run('--data-file', str(tmp_path / 'nope.json'))


@pytest.mark.django_db
def test_warns_about_case_only_duplicates_and_bare_pigments(tmp_path):
    from pigments.factories import PigmentFactory
    PigmentFactory(name='sourced orpiment')
    data = json.loads(json.dumps(SOURCED_DATA))
    output = _run('--data-file', _write(tmp_path, data), '--dry-run')
    assert 'differs only in case from existing "sourced orpiment"' in output
    assert 'new pigment "Sourced Orpiment" has no description' in output


@pytest.mark.django_db
def test_supplemental_data_file_loads_after_manuscript_pigments():
    from pigments.models import PigmentManuscript
    output = _run('--data-file', 'pigments/data/manuscript_pigments.json',
                  'pigments/data/supplemental_manuscript_pigments.json')
    assert 'Warning' not in output
    assert not PigmentManuscript.objects.filter(source__isnull=True).exists()
    assert Pigment.objects.get(name='Indigo').description.startswith('Plant-derived')
    assert PigmentManuscript.objects.filter(
        manuscript__name='Gondär Homiliary (Walters W.835)', pigment__name='Smalt').exists()


@pytest.mark.django_db
def test_dry_run_lists_new_reference_rows(tmp_path):
    output = _run('--data-file', _write(tmp_path, SOURCED_DATA), '--dry-run')
    assert 'Would create 1 color families:' in output
    assert '+ Arsenic Pigments' in output
    assert 'Would create 1 countries:' in output
    assert '+ Ireland' in output


@pytest.mark.django_db
def test_file_without_pigments_list_is_an_error(tmp_path):
    from django.core.management.base import CommandError
    path = tmp_path / 'other.json'
    path.write_text(json.dumps({'manuscripts': []}))
    with pytest.raises(CommandError, match='no top-level "pigments" list'):
        _run('--data-file', str(path))
    path.write_text('{not json')
    with pytest.raises(CommandError, match='not valid JSON'):
        _run('--data-file', str(path))


@pytest.mark.django_db
def test_warns_when_existing_rows_differ_from_file(tmp_path):
    path = _write(tmp_path, SOURCED_DATA)
    _run('--data-file', path)
    data = json.loads(json.dumps(SOURCED_DATA))
    data['pigments'][0]['color_family'] = 'Orange'
    data['pigments'][0]['manuscripts'][0]['date_start'] = 750
    output = _run('--data-file', _write(tmp_path, data), '--dry-run')
    assert 'existing pigment "Sourced Orpiment" is Yellow / Arsenic Pigments' in output
    assert 'existing manuscript "Book of Kells" is Ireland, 800–1100' in output
