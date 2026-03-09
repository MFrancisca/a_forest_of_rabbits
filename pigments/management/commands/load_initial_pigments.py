from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Load initial pigment data (idempotent — stub)'

    def handle(self, *args, **options):
        pass  # Stub — implementation in plan 03
