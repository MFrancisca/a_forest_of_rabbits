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
