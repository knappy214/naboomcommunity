from django.apps import AppConfig


class PanicConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "panic"
    verbose_name = "Panic Response"

    def ready(self) -> None:
        # Import signal handlers or services that need startup registration.
        from . import signals  # noqa: F401
        return super().ready()
