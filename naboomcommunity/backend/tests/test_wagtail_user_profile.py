from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


def test_wagtail_user_profile_requires_jwt(db):
    user = User.objects.create_user(
        username="carol",
        email="carol@example.com",
        password="pass12345",
    )
    client = APIClient()
    token_resp = client.post(
        '/api/auth/jwt/create/',
        {'username': 'carol', 'password': 'pass12345'},
        format='json'
    )
    assert token_resp.status_code == 200
    token = token_resp.json()['access']
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    resp = client.get('/api/v2/user-profiles/')
    assert resp.status_code == 200
    data = resp.json()
    assert data['meta']['total_count'] == 1
    assert data['items'][0]['username'] == 'carol'
