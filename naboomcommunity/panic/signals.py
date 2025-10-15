"""Signal hooks for the panic application.

Currently used to ensure Django loads escalation services when the app
is ready. The module intentionally keeps side effects light to avoid
expensive work during startup.
"""

from django.dispatch import receiver
from django.db.models.signals import post_save

# Import models if they exist
try:
    from .models import Incident, IncidentEvent
    
    @receiver(post_save, sender=Incident)
    def ensure_initial_event(sender, instance: Incident, created: bool, **_: object) -> None:
        """Ensure new incidents always have an audit event entry."""
        if not created:
            return

        if not instance.events.filter(kind=IncidentEvent.Kind.CREATED).exists():
            IncidentEvent.objects.create(
                incident=instance,
                kind=IncidentEvent.Kind.CREATED,
                description="Incident created",
                metadata={"auto": True},
            )
except ImportError:
    # Models don't exist yet, skip signal registration
    pass
