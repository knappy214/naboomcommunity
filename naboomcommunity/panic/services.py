from __future__ import annotations

from datetime import timedelta
from typing import List

from django.db.models import Prefetch
from django.utils import timezone

from .models import (
    EscalationRule,
    EscalationTarget,
    Incident,
    IncidentEvent,
    OutboundMessage,
)


def process_incident_escalations(now: timezone.datetime | None = None) -> List[int]:
    """Process incidents awaiting escalation notifications.

    Returns a list of incident IDs that were escalated during this run.
    """

    now = now or timezone.now()
    triggered: List[int] = []

    rules = (
        EscalationRule.objects.filter(active=True)
        .prefetch_related(
            Prefetch("targets", queryset=EscalationTarget.objects.filter(active=True))
        )
        .order_by("delay_seconds")
    )

    for rule in rules:
        cutoff = now - timedelta(seconds=rule.delay_seconds)
        incidents = Incident.objects.filter(
            status=Incident.Status.OPEN,
            province=rule.province,
            created_at__lte=cutoff,
        )
        if rule.only_for_priority:
            incidents = incidents.filter(priority__gte=rule.only_for_priority)

        for incident in incidents:
            if incident.events.filter(
                kind=IncidentEvent.Kind.ESCALATED, metadata__rule_id=rule.id
            ).exists():
                continue

            for target in rule.targets.all():
                destination = target.resolve_destination()
                if not destination:
                    continue

                OutboundMessage.objects.create(
                    incident=incident,
                    to_number=destination,
                    body=(
                        f"Incident {incident.reference} requires attention. "
                        f"Priority: {incident.get_priority_display()}"
                    ),
                    metadata={
                        "rule_id": rule.id,
                        "channel": target.channel,
                        "target_type": target.target_type,
                    },
                )

            IncidentEvent.objects.create(
                incident=incident,
                kind=IncidentEvent.Kind.ESCALATED,
                description=f"Escalation rule '{rule.name}' triggered",
                metadata={"rule_id": rule.id},
            )
            triggered.append(incident.id)

    return triggered
