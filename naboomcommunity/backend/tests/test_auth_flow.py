import re
from django.core import mail
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


def test_register_and_login(db):
    c = APIClient()
    r = c.post(
        '/api/v1/auth/register/',
        {'username': 'alice', 'email': 'alice@example.com', 'password': 'Str0ngP@ssw0rd!'},
        format='json',
    )
    assert r.status_code == 201
    r = c.post(
        '/api/v1/auth/jwt/create/',
        {'email': 'alice@example.com', 'password': 'Str0ngP@ssw0rd!'},
        format='json',
    )
    assert r.status_code == 200
    assert 'access' in r.json()


def test_password_reset(db, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    u = User.objects.create_user(
        username='bob', email='bob@example.com', password='Str0ngP@ssw0rd!'
    )
    c = APIClient()
    r = c.post('/api/v1/auth/password-reset/', {'email': 'bob@example.com'}, format='json')
    assert r.status_code == 200
    assert len(mail.outbox) == 1
    m = mail.outbox[0]
    assert 'Reset your password' in m.body
