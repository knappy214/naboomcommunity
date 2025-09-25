from .base import *
import os

# Use in-memory SQLite database for tests to avoid external dependencies
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

INSTALLED_APPS = [
    app for app in INSTALLED_APPS if app not in {"django.contrib.gis", "panic"}
]

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]
