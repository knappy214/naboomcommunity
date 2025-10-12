"""Minimal stub implementation of Django Channels for offline test environments."""
from __future__ import annotations

from . import auth, db, generic, layers, routing

__all__ = [
    "auth",
    "db",
    "generic",
    "layers",
    "routing",
]
