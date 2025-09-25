"""Celery application for Naboom Community."""
from __future__ import annotations

import os

try:
    from celery import Celery  # type: ignore
except ImportError:  # pragma: no cover - allow local development without Celery
    Celery = None


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "naboomcommunity.settings.dev")


if Celery is not None:
    app = Celery("naboomcommunity")
    app.config_from_object("django.conf:settings", namespace="CELERY")
    app.autodiscover_tasks()

    @app.task(bind=True)
    def debug_task(self):  # pragma: no cover - helper for debugging
        print(f"Request: {self.request!r}")
else:

    class _CeleryStub:
        def config_from_object(self, *args, **kwargs):  # pragma: no cover - stub behaviour
            return None

        def autodiscover_tasks(self):  # pragma: no cover - stub behaviour
            return None

        def task(self, *decorator_args, **decorator_kwargs):  # pragma: no cover - stub behaviour
            def decorator(func):
                func.delay = lambda *args, **kwargs: func(*args, **kwargs)
                return func

            return decorator

    app = _CeleryStub()

    def debug_task(*args, **kwargs):  # pragma: no cover - stub behaviour
        return None
