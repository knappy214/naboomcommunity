from __future__ import annotations

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from ...models import VehiclePosition


class Command(BaseCommand):
    help = "Prune historical vehicle positions to keep the database lean."

    def add_arguments(self, parser):  # pragma: no cover - management command
        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="Number of days of history to retain",
        )

    def handle(self, *args, **options):  # pragma: no cover - management command
        days = options["days"]
        cutoff = timezone.now() - timedelta(days=days)
        deleted, _ = VehiclePosition.objects.filter(recorded_at__lt=cutoff).delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted} vehicle positions"))
