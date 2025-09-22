from __future__ import annotations

from django.core.management.base import BaseCommand

from ...services import process_incident_escalations


class Command(BaseCommand):
    help = "Process pending panic incident escalations."

    def handle(self, *args, **options):  # pragma: no cover - management command
        triggered = process_incident_escalations()
        self.stdout.write(self.style.SUCCESS(f"Escalated {len(triggered)} incidents"))
