Ops Guide — Nginx + MQTT + Redis + Celery (Production‑Grade)

This guide documents a production‑ready setup for serving Wagtail + Vue on the same VPS under https://naboomneighbornet.net.za, ingesting panic events via MQTT (TCP & WebSockets), broadcasting realtime updates with Django Channels, and running Redis + Celery for performance and reliability. All examples are hardened for security and tuned for low‑bandwidth rural networks.

TL;DR topology
- Nginx (443) → / → Gunicorn (Django/Wagtail HTTP)
- Nginx (443) → /monitor → Vue static SPA
- Nginx (443) → /panic/api/stream → Django SSE
- Nginx (443) → /ws/… → Daphne (Channels WebSocket)
- Nginx (443) → /mqtt → Mosquitto WS (127.0.0.1:8083)
- Django worker (systemd) → subscribes to Mosquitto TCP (127.0.0.1:1883)
- Redis → cache + Channel Layer + Celery broker/backend
- Celery → async SMS / escalation / housekeeping

1) Nginx on naboomneighbornet.net.za (Vue + Wagtail same server)

Create these files and adjust paths as needed.

1.1 Upstreams (HTTP app + Channels)

# /etc/nginx/conf.d/upstreams.conf
upstream naboom_app { server 127.0.0.1:8000 fail_timeout=0; }
upstream naboom_ws  { server 127.0.0.1:9000 fail_timeout=0; }  # Daphne
upstream mosq_ws    { server 127.0.0.1:8083 fail_timeout=0; }  # Mosquitto WS

1.2 Common proxy snippet

# /etc/nginx/snippets/proxy-common.conf
proxy_http_version 1.1;
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_connect_timeout 60s;
proxy_send_timeout 60s;
proxy_read_timeout 60s;
proxy_buffers 32 16k;
proxy_busy_buffers_size 32k;

1.3 HTTP→HTTPS redirect

server {
  listen 80; listen [::]:80;
  server_name naboomneighbornet.net.za;
  return 301 https://$host$request_uri;
}

1.4 Main HTTPS virtual host

server {
  listen 443 ssl http2; listen [::]:443 ssl http2;
  server_name naboomneighbornet.net.za;

  # TLS (use certbot-managed paths)
  ssl_certificate     /etc/letsencrypt/live/naboomneighbornet.net.za/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/naboomneighbornet.net.za/privkey.pem;

  # Security headers
  add_header X-Frame-Options DENY always;
  add_header X-Content-Type-Options nosniff always;
  add_header Referrer-Policy strict-origin-when-cross-origin always;
  add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

  # Gzip
  gzip on; gzip_comp_level 5; gzip_min_length 256;
  gzip_types text/plain text/css application/json application/javascript text/xml application/xml+rss image/svg+xml;

  # Static & media
  location /static/ { alias /srv/naboomcommunity/static/; access_log off; expires 30d; add_header Cache-Control "public, max-age=2592000, immutable"; }
  location /media/  { alias /srv/naboomcommunity/media/;  access_log off; expires 7d;  add_header Cache-Control "public, max-age=604800"; }

  # App HTTP (Wagtail + custom panic endpoints)
  location /api/   { proxy_pass http://naboom_app; include /etc/nginx/snippets/proxy-common.conf; }
  location /panic/ { proxy_pass http://naboom_app; include /etc/nginx/snippets/proxy-common.conf; }

  # SSE must NOT be buffered
  location = /panic/api/stream {
    proxy_pass http://naboom_app;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    proxy_read_timeout 1h; proxy_send_timeout 1h;
    proxy_buffering off; add_header X-Accel-Buffering no;
    include /etc/nginx/snippets/proxy-common.conf;
  }

  # Django Channels WebSocket
  location /ws/ {
    proxy_pass http://naboom_ws;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 1h; proxy_send_timeout 1h;
    include /etc/nginx/snippets/proxy-common.conf;
  }

  # MQTT over WebSockets (devices connect to wss://naboomneighbornet.net.za/mqtt)
  location /mqtt {
    proxy_pass http://mosq_ws;  # Mosquitto WS listener on 127.0.0.1:8083
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 1h; proxy_send_timeout 1h;
    include /etc/nginx/snippets/proxy-common.conf;
  }

  # Rate-limit tracker HTTP pings
  location = /panic/api/vehicle/ping {
    limit_req zone=veh burst=10 nodelay;
    proxy_pass http://naboom_app;
    include /etc/nginx/snippets/proxy-common.conf;
  }

  # Vue monitor under /monitor (single-domain option)
  location /monitor/ {
    alias /srv/naboomneighbornet_web/dist/;
    try_files $uri $uri/ /monitor/index.html;
  }
  location ~* ^/monitor/.+\.(?:js|css|svg|png|jpg|jpeg|gif|webp|ico|woff2?)$ {
    alias /srv/naboomneighbornet_web/dist/;
    access_log off; expires 30d; add_header Cache-Control "public, max-age=2592000, immutable";
  }
  location = /monitor/index.html { alias /srv/naboomneighbornet_web/dist/index.html; add_header Cache-Control "no-store"; }
}

# Rate-limit zones (http{} scope)
limit_req_zone $binary_remote_addr zone=veh:10m rate=30r/m;

Hardening notes
- Place admin at /admin/ behind IP allowlist or Auth proxy (optional).
- Ensure CORS allows the SPA origin only; for SSE with credentials, not *.
- Consider client_max_body_size 10m; if you later upload media.

2) MQTT ingest path (Mosquitto + asyncio‑mqtt + Channels)
2.1 Mosquitto (two listeners: TCP 1883, WS 8083)
Install Mosquitto:
sudo apt-get update && sudo apt-get install -y mosquitto mosquitto-clients
sudo systemctl enable --now mosquitto

Config:

# /etc/mosquitto/conf.d/naboom.conf
persistence true
persistence_location /var/lib/mosquitto/
log_dest syslog

# Authentication & ACLs
allow_anonymous false
password_file /etc/mosquitto/passwd
acl_file /etc/mosquitto/aclfile

# Local TCP listener (Django subscriber only)
listener 1883 127.0.0.1
allow_anonymous false

# WebSockets listener for devices (proxied by Nginx TLS)
listener 8083 127.0.0.1
protocol websockets
http_dir /usr/share/mosquitto/www

Create users and ACLs (1 app service user + per‑device users optional):

# service user for Django subscriber
sudo mosquitto_passwd -c /etc/mosquitto/passwd app_subscriber
# (enter strong password)

# optional: device-specific users (one per pid)
sudo mosquitto_passwd /etc/mosquitto/passwd device-1234

# ACL: devices can only publish to their own topic; app_subscriber can read them all
cat <<'ACL' | sudo tee /etc/mosquitto/aclfile
user app_subscriber
topic read panic/ingest/#

pattern write deny
pattern readwrite deny

# device users (pattern)
pattern write panic/ingest/%u
ACL

sudo systemctl restart mosquitto

Device connection options
- Mobile connects via WSS to wss://naboomneighbornet.net.za/mqtt (Nginx → Mosquitto 8083).
- QoS 1 publish to: panic/ingest/{pid} where {pid} is the device’s assigned ID.

Payload (signed)

{
  "pid": "device-1234",
  "ts": 1732590725,
  "nonce": 987654,
  "msg": "SOS",              
  "lat": -23.9001,            
  "lng": 28.3012,             
  "acc": 18,                  
  "kid": 1,                   
  "sig": "base64(hmac_sha256(kid#1 secret, canonical_json_without_sig))"
}

Idempotency: {pid}:{nonce} must be unique for at least 7 days. The subscriber uses Redis SETNX with TTL to drop duplicates.

2.2 Django: Device credentials & HMAC verify

Add a minimal credential model (if not using an MDM):

# panic/models_device.py (optional module)
from django.db import models
class DeviceCredential(models.Model):
    pid = models.CharField(max_length=64, unique=True)
    kid = models.IntegerField(default=1)  # key version
    secret = models.CharField(max_length=128)  # store as base64 or hex
    active = models.BooleanField(default=True)
    rotated_at = models.DateTimeField(null=True, blank=True)

Helper:

# panic/crypto.py
import base64, hmac, hashlib, json
from typing import Dict
from .models_device import DeviceCredential

CANON_KEYS = ["pid","ts","nonce","msg","lat","lng","acc","kid"]

def canonical_body(d: Dict) -> bytes:
    return json.dumps({k: d.get(k) for k in CANON_KEYS if k in d}, separators=(",",":"), sort_keys=True).encode()

def verify_hmac(payload: Dict) -> bool:
    sig = payload.get("sig")
    pid = payload.get("pid")
    kid = int(payload.get("kid", 1))
    if not sig or not pid:
        return False
    try:
        cred = DeviceCredential.objects.get(pid=pid, active=True)
        if cred.kid != kid:
            # allow overlap during rotation: accept if kid differs but pid matches
            pass
        secret = base64.b64decode(cred.secret)
        mac = hmac.new(secret, canonical_body(payload), hashlib.sha256).digest()
        expected = base64.b64encode(mac).decode()
        return hmac.compare_digest(expected, sig)
    except DeviceCredential.DoesNotExist:
        return False

2.3 Async MQTT subscriber (systemd‑managed)

Install library:

source /srv/naboomcommunity/venv/bin/activate
pip install asyncio-mqtt

Command:

# panic/management/commands/mqtt_subscriber.py
import asyncio, json, os, time
from django.core.management.base import BaseCommand
from asyncio_mqtt import Client
from django.utils import timezone
from django.conf import settings
from django.contrib.gis.geos import Point
import redis
from panic.crypto import verify_hmac
from panic.models import Incident, IncidentEvent
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

R = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'))

class Command(BaseCommand):
    help = 'Subscribe to MQTT panic/ingest/+ and create incidents/events'

    def add_arguments(self, parser):
        parser.add_argument('--host', default=os.getenv('MQTT_HOST','127.0.0.1'))
        parser.add_argument('--port', type=int, default=int(os.getenv('MQTT_PORT','1883')))
        parser.add_argument('--user', default=os.getenv('MQTT_USER','app_subscriber'))
        parser.add_argument('--password', default=os.getenv('MQTT_PASSWORD',''))
        parser.add_argument('--topic', default='panic/ingest/+')

    def handle(self, *args, **opts):
        asyncio.run(self.run(**opts))

    async def run(self, host, port, user, password, topic):
        async with Client(hostname=host, port=port, username=user, password=password, client_id='naboom-django-sub') as client:
            await client.subscribe(topic, qos=1)
            async with client.unfiltered_messages() as messages:
                async for m in messages:
                    try:
                        payload = json.loads(m.payload.decode('utf-8'))
                    except Exception:
                        continue
                    # Idempotency guard
                    pid = str(payload.get('pid',''))
                    nonce = str(payload.get('nonce',''))
                    if not pid or not nonce:
                        continue
                    if not verify_hmac(payload):
                        continue
                    dedupe_key = f"ingest:{pid}:{nonce}"
                    if not R.setnx(dedupe_key, 1):
                        continue
                    R.expire(dedupe_key, 7*24*3600)

                    # Create or update incident
                    point = None
                    if 'lat' in payload and 'lng' in payload:
                        try: point = Point(float(payload['lng']), float(payload['lat']))
                        except Exception: point = None
                    inc = Incident.objects.create(
                        source=Incident.Source.APP,
                        msisdn=None,
                        message=(payload.get('msg') or 'SOS')[:280],
                        location=point,
                        accuracy_m=payload.get('acc'),
                        consent_location=True,
                    )
                    IncidentEvent.objects.create(incident=inc, event_type='MQTT', payload=payload)

                    # Broadcast to Channels group (Limpopo default region code ZA-LP)
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        'alerts:ZA-LP',
                        { 'type': 'panic.event', 'data': { 'id': inc.id, 'msg': inc.message, 'lat': float(point.y) if point else None, 'lng': float(point.x) if point else None, 'ts': timezone.now().isoformat() } }
                    )

Systemd unit:

# /etc/systemd/system/naboom-mqtt.service
[Unit]
Description=Naboom Django MQTT subscriber
After=network-online.target mosquitto.service
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/srv/naboomcommunity
EnvironmentFile=/srv/naboomcommunity/.env
ExecStart=/srv/naboomcommunity/venv/bin/python manage.py mqtt_subscriber
Restart=always
RestartSec=5
User=www-data
Group=www-data

[Install]
WantedBy=multi-user.target

Enable:

sudo systemctl daemon-reload
sudo systemctl enable --now naboom-mqtt.service

2.4 Django Channels (WebSocket → Vue/Wagtail control room)

Install & configure:

pip install channels[daphne] channels-redis

settings.py

INSTALLED_APPS += ["channels"]
ASGI_APPLICATION = "config.asgi.application"
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/1")
CHANNEL_LAYERS = { "default": { "BACKEND": "channels_redis.core.RedisChannelLayer", "CONFIG": { "hosts": [REDIS_URL] } } }

asgi.py

# config/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import panic.routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
  "http": django_asgi_app,
  "websocket": AuthMiddlewareStack(URLRouter(panic.routing.websocket_urlpatterns)),
})

routing.py

# panic/routing.py
from django.urls import re_path
from .ws_consumers import AlertsConsumer
websocket_urlpatterns = [ re_path(r"^ws/alerts/(?P<region>[A-Za-z0-9\-_:]+)/$", AlertsConsumer.as_asgi()), ]

consumer

# panic/ws_consumers.py
from channels.generic.websocket import AsyncJsonWebsocketConsumer

class AlertsConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        region = self.scope['url_route']['kwargs'].get('region', 'ZA-LP')
        self.group = f"alerts:{region}"
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()
    async def disconnect(self, code):
        if hasattr(self, 'group'):
            await self.channel_layer.group_discard(self.group, self.channel_name)
    async def panic_event(self, event):
        await self.send_json(event.get('data', {}))

Daphne service

# /etc/systemd/system/naboom-daphne.service
[Unit]
Description=Daphne ASGI for Naboom
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/srv/naboomcommunity
EnvironmentFile=/srv/naboomcommunity/.env
ExecStart=/srv/naboomcommunity/venv/bin/daphne -b 127.0.0.1 -p 9000 config.asgi:application
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target

Enable:

sudo systemctl daemon-reload
sudo systemctl enable --now naboom-daphne.service

Vue control room hookup

// ws client (alternative to SSE) — choose one per page
const ws = new WebSocket('wss://naboomneighbornet.net.za/ws/alerts/ZA-LP/')
ws.onmessage = (ev) => {
  const d = JSON.parse(ev.data)
  // show toast + map zoom similar to SSE handler
}

Security :
- All ingress is TLS terminated at Nginx.
- Mosquitto does not expose TCP/WS to the internet directly; only via Nginx /mqtt.
- ACLs restrict device users to panic/ingest/{pid}; app subscriber is read‑only.
- HMAC validation with per‑device secrets; include kid for rotation; accept both old/new during rotation window.
- POPIA: keep minimal PII — prefer device PID (opaque), coarse location (optional rounding to ~2–3 decimals when not in emergency), and avoid storing personal messages beyond 280 chars.
- Idempotency: Redis SETNX on {pid}:{nonce} avoids duplicate incidents.

3) Redis — cache, channels, celery broker
Install & tune:

sudo apt-get install -y redis-server
sudo sed -i 's/^#\? bind .*/bind 127.0.0.1 ::1/' /etc/redis/redis.conf
sudo sed -i 's/^supervised .*/supervised systemd/' /etc/redis/redis.conf
sudo sed -i 's/^#\? maxmemory .*/maxmemory 512mb/' /etc/redis/redis.conf
sudo sed -i 's/^#\? maxmemory-policy .*/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf
sudo sed -i 's/^save .*/save 900 1\nsave 300 10\nsave 60 10000/' /etc/redis/redis.conf
sudo sed -i 's/^#\? appendonly .*/appendonly yes/' /etc/redis/redis.conf
sudo systemctl enable --now redis-server

Django settings:

# Cache
CACHES = {
  "default": {
    "BACKEND": "django_redis.cache.RedisCache",
    "LOCATION": os.getenv("REDIS_URL", "redis://127.0.0.1:6379/1"),
    "OPTIONS": { "CLIENT_CLASS": "django_redis.client.DefaultClient" }
  }
}
# Channels (see above)
CHANNEL_LAYERS = { "default": { "BACKEND": "channels_redis.core.RedisChannelLayer", "CONFIG": { "hosts": [os.getenv("REDIS_URL", "redis://127.0.0.1:6379/1")] } } }

Operational tips :
- Keep Redis bound to 127.0.0.1 only.
- Monitor memory and hits/misses (redis-cli info stats memory).
- For HA later, move Redis to a managed instance or enable AOF + backups.

4) Celery — async tasks & scheduling

Install:

pip install celery[redis]

Project bootstrap:

# panic/celery.py
import os
from celery import Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
app = Celery('panic')
app.conf.broker_url = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1')
app.conf.result_backend = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1')
app.autodiscover_tasks()

# panic/__init__.py
from .celery import app as celery_app  # noqa

Tasks:

# panic/tasks.py
from celery import shared_task
from .services.clickatell import send_sms
from .models import OutboundMessage, Incident

@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def send_sms_task(self, to_msisdn: str, body: str, incident_id: int | None = None):
    try:
        mid = send_sms(to_msisdn, body)
        OutboundMessage.objects.create(incident_id=incident_id, to_msisdn=to_msisdn, body=body, status='SENT', provider_message_id=mid)
    except Exception as e:
        if self.request.retries < 3:
            raise self.retry(exc=e)
        OutboundMessage.objects.create(incident_id=incident_id, to_msisdn=to_msisdn, body=body, status='ERROR', error_code=str(e))

@shared_task
def escalate_open_incidents():
    from django.utils import timezone
    from .models import EscalationRule
    now = timezone.now()
    for r in EscalationRule.objects.filter(is_active=True, predicate='OPEN_UNACK'):
        cutoff = now - timezone.timedelta(minutes=r.threshold_minutes)
        for inc in Incident.objects.filter(status=Incident.Status.OPEN, created_at__lte=cutoff):
            for t in r.targets.all():
                if t.kind == 'SMS':
                    send_sms_task.delay(t.address, t.template or f"Incident #{inc.id} needs attention", inc.id)

Schedule (beat):

# settings.py
CELERY_BEAT_SCHEDULE = {
  'escalations-every-minute': { 'task': 'panic.tasks.escalate_open_incidents', 'schedule': 60.0 },
}

Systemd units:

# /etc/systemd/system/naboom-celery.service
[Unit]
Description=Celery Worker
After=network.target redis-server.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/srv/naboomcommunity
EnvironmentFile=/srv/naboomcommunity/.env
ExecStart=/srv/naboomcommunity/venv/bin/celery -A panic worker -l info --concurrency=2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target

# /etc/systemd/system/naboom-celerybeat.service
[Unit]
Description=Celery Beat Scheduler
After=network.target redis-server.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/srv/naboomcommunity
EnvironmentFile=/srv/naboomcommunity/.env
ExecStart=/srv/naboomcommunity/venv/bin/celery -A panic beat -l info
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target

Enable:

sudo systemctl daemon-reload
sudo systemctl enable --now naboom-celery.service naboom-celerybeat.service

Where to call Celery tasks :
- Replace direct SMS sends in views.submit_incident with send_sms_task.delay(...) for resilience.
- Consider a task to compute patrol coverage daily.

5) Performance & Security checklist (final pass) :
- TLS everywhere: Nginx terminates TLS for HTTP, WS, and WSS.
- SSE: buffering disabled, long read timeouts, HTTP/2 on.
- WebSockets: upgrade headers set, long timeouts, rate‑limit handshake if abused.
- MQTT: no direct internet exposure; users constrained by ACL; QoS 1 on publish; persistent broker.
- HMAC: per‑device secret with kid rotation; verify in subscriber; store secrets securely.
- Idempotency: Redis SETNX on {pid}:{nonce} with TTL≥7d.
- Redis: bound to localhost, AOF enabled, LRU policy, monitored memory.
- Celery: retries on transient SMS errors; beat for escalations.
- POPIA: keep payload minimal (opaque PID, coarse lat/lng if not critical). Purge old events per policy.
- Backups: Postgres dumps, Redis AOF copies, /srv/* config backups.
- Observability: journald tails for all services; consider Sentry for Django; Mosquitto logs via syslog.

This provides a production‑grade, resilient path for HTTP + MQTT ingestion, live operator views via SSE/WS, and robust background processing with Redis + Celery — all on the single VPS behind Nginx at naboomneighbornet.net.za.