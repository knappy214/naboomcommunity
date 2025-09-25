from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CommunityHubConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "communityhub"
    verbose_name = _("Community Hub")

    def ready(self) -> None:  # pragma: no cover - import signals lazily
        try:
            from . import signals  # noqa: F401
        except ImportError:
            # Signals are optional and only required when they exist.
            pass
