from rest_framework.test import APIClient


def test_health_ok(db):
    c = APIClient()
    r = c.get('/api/health/')
    assert r.status_code == 200
    assert r.json()['status'] == 'ok'
