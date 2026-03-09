import pytest
from django.core.management import call_command

from pigments.models import Pigment


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
