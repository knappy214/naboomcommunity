Runbook — Realtime, VAPID, Performance, Security, Redis, Celery, ASGI (EN/AF)

This document complements the three SPEC canvases (Backend, Web, Expo). It provides step‑by‑step setup and production‑grade configs for:

Nginx WebSocket reverse proxy (Realtime/WS)

Web Push VAPID configuration & implications

Performance optimisations (Expo + Web + Nginx)

Security hardening (JWT, sanitisation, admin guards)

Redis (Channels + Celery)

Celery (workers + beat)

ASGI server (Uvicorn) + WS verification

Multilingual: Push texts and UI copy must be available in English/Afrikaans (EN/AF). Examples below include a localisation note where relevant.

1) Realtime (WebSocket) via Nginx — fully optimised

Goals

Terminate TLS at Nginx, proxy HTTP/1.1 Upgrade to the Django ASGI app.

Low latency, long‑lived connections, sane timeouts, and safe logging.

Nginx upstream

upstream asgi_app {
    server 127.0.0.1:8000;   # uvicorn/daphne
    keepalive 64;
}

WS proxy (HTTPS vhost)

server {
    listen 443 ssl http2;
    server_name naboomneighbornet.net.za;

    # TLS config (example)
    ssl_certificate     /etc/letsencrypt/live/naboomneighbornet.net.za/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/naboomneighbornet.net.za/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_protocols TLSv1.3 TLSv1.2;
    ssl_ciphers "TLS_AES_256_GCM_SHA384:TLS_AES_128_GCM_SHA256:TLS_CHACHA20_POLY1305_SHA256:...";

    # --- Optimised proxy defaults ---
    proxy_http_version 1.1;           # required for WS upgrade
    proxy_read_timeout  3600s;        # long‑lived WS
    proxy_send_timeout  3600s;
    proxy_connect_timeout 60s;
    proxy_buffering off;              # reduce latency
    tcp_nodelay on;

    # Avoid leaking JWT if you ever use ?token=... (prefer subprotocol; see Security)
    log_format ws '$remote_addr - [$time_local] "$request_method $uri HTTP/$http_version" $status $body_bytes_sent';
    access_log /var/log/nginx/ws.access.log ws;

    # --- Static files (optional) ---
    location /static/ { root /srv/app/current; expires 30d; add_header Cache-Control "public"; }

    # --- WebSocket endpoint (Channels) ---
    location /ws/ {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Upgrade
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;

        proxy_pass http://asgi_app;
    }

    # --- REST API ---
    location /api/ {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://asgi_app;
    }

    # --- Wagtail API v2 ---
    location /api/v2/ { proxy_pass http://asgi_app; }
}

# Upgrade helper so Connection: upgrade is set only when needed
map $http_upgrade $connection_upgrade { default upgrade; '' close; }

Notes

Keep WS on HTTP/1.1 upstream (proxy_http_version 1.1). Nginx will serve HTTP/2 to browsers for normal requests; WS will negotiate upgrade on 1.1.

Use a separate access log format for /ws/ to avoid logging query strings (and therefore tokens) — see Security §4.

If you deploy Gunicorn + Uvicorn workers instead of bare Uvicorn, upstream remains the same (port changes via systemd).

Health check (optional)

Expose /healthz in Django and add an Nginx location /healthz { proxy_pass http://asgi_app; } used by monitoring.

2) Web Push VAPID — configuration & implications

What is VAPID?

VAPID (Voluntary Application Server Identification) is a public/private key pair that identifies your server to push services (e.g., Google FCM, Mozilla Push). It signs Web Push requests so browsers accept your payloads.

Keys & claims

Generate one long‑lived ECDSA P‑256 key pair.

Store private key server‑side only; publish the public key in the client (safe).

Include a sub claim (e.g., mailto:ops@...) and optionally aud/exp as the library dictates.

Backend settings

# settings.py
VAPID_PUBLIC_KEY  = env("VAPID_PUBLIC_KEY")     # safe to expose
VAPID_PRIVATE_KEY = env("VAPID_PRIVATE_KEY")    # keep secret
VAPID_CLAIMS = {"sub": "mailto:ops@naboomneighbornet.net.za"}

Client subscription (Web)

Register a Service Worker (/sw.js).

Call pushManager.subscribe({ applicationServerKey: VAPID_PUBLIC_KEY, userVisibleOnly: true }).

POST the subscription (endpoint + keys) to /api/devices/.

Sending pushes (server)

Use pywebpush with your private key and claims.

Payload should be small (< 4 KB). For larger content, send a teaser and deep link.

Implications & best practices

Consent: Ask for notification permission after a user gesture, not on page load.

Localisation (EN/AF): Push titles/bodies should be generated in the user’s preferred language (persisted in profile/prefs).

Privacy: Subscriptions include a push service endpoint (often FCM). Treat as PII; store minimally; delete on 410/404 responses.

Reliability: Browsers may throttle background delivery. Use concise payloads and set appropriate TTL if your library exposes it.

Revocation handling: On WebPushException 404/410, disable the device in DB.

Security: Never embed sensitive data in payloads; use deep links with server‑side auth.

3) Performance Optimisations (Expo + Web + Nginx)

3.1 Expo — FlashList for 1k+ items

import { FlashList } from "@shopify/flash-list";

export function PostsList({ data, onEndReached }) {
  return (
    <FlashList
      data={data}
      renderItem={({ item }) => <PostItem post={item} />}
      estimatedItemSize={72}           // tune: typical item height
      onEndReached={onEndReached}
      onEndReachedThreshold={0.5}
      keyExtractor={(p) => String(p.id)}
      removeClippedSubviews
    />
  );
}

Tips: Set estimatedItemSize close to reality (e.g., 64–88). Avoid dynamic heights if possible; use getItemType when mixing sizes.

3.2 Expo — Batch WS updates before state writes

import { unstable_batchedUpdates } from "react-native"; // RN exposes this

// Buffer WS messages and flush at most every 16ms
const buffer: any[] = [];
let scheduled = false;

export function onWsMessage(msg: any, push: (items:any[]) => void) {
  buffer.push(msg);
  if (scheduled) return;
  scheduled = true;
  setTimeout(() => {
    const chunk = buffer.splice(0, buffer.length);
    unstable_batchedUpdates(() => push(chunk)); // single render pass
    scheduled = false;
  }, 16);
}

If you use Zustand, do a single set((s)=>{ /* apply all changes */ }) per flush.

3.3 Network: HTTP/2, gzip/brotli, coalesce rapid posts

Nginx: enable http2 on listen 443 ssl http2;, gzip on; and (optionally) brotli on; (if the module is available). Serve JSON with gzip_types application/json.

Client coalescing: when a user sends multiple replies quickly, queue them locally and send as a single HTTP request where acceptable, or at least debounce the POSTs by 200–300ms to avoid flooding.

// naive coalescer for replies
const queue: {thread:number, body:string}[] = [];
let timer: any;
export function queueReply(item:{thread:number, body:string}){
  queue.push(item);
  clearTimeout(timer);
  timer = setTimeout(flush, 250);
}
async function flush(){
  const items = queue.splice(0);
  await Promise.all(items.map(i => api.post("/posts/", i)));
}

3.4 Images: expo-image caching + thumbnails

import { Image } from "expo-image";

<Image
  source={{ uri: thumbUrl }}            // small rendition for lists
  contentFit="cover"
  placeholder={blurhash}
  cachePolicy="disk"                   // cache on device
  transition={200}
  style={{ width: 80, height: 80, borderRadius: 8 }}
/>

Server side: generate thumbnails/renditions (Wagtail Images) and include blurhash/placeholder if available. Load full image on detail screens only.

3.5 Web lists (optional)

Use Vue Virtual Scroller or similar for long lists; avoid reactivity on large arrays by shallowRef and targeted updates.

4) Security

4.1 JWT storage (Expo)

Use expo-secure-store for tokens. Never store JWT in AsyncStorage.

Do not log tokens; redact in error logs; interceptors must avoid dumping headers.

import * as SecureStore from "expo-secure-store";

export async function saveToken(t: string){ await SecureStore.setItemAsync("jwt", t); }
export async function loadToken(){ return SecureStore.getItemAsync("jwt"); }

4.2 Sanitise rich text (Web + Mobile)

Default rendering is plain text. If you ever render HTML (e.g., from CMS), sanitise:

Web: dompurify (strict config);

Mobile: react-native-render-html with a whitelist of tags/attributes; never allow on* handlers.

4.3 Guard admin actions (client) & enforce (server)

Client: derive role from profile/JWT claim (e.g., role in /me or a short‑lived signed claim). Hide admin UI and prompt a confirm dialog for destructive actions (pin/unpin, lock, delete/restore, remove member).

if (!user.roles.includes("moderator")) return toast.error(t("errors.not_authorised"));
const ok = await confirm(t("confirm.pin_thread"));
if (ok) await api.post(`/threads/${id}/pin`, {});

Server: Always enforce with DRF permissions; never trust the client.

4.4 WebSocket auth best‑practice

Prefer a short‑lived WS token obtained from REST and passed via Sec-WebSocket-Protocol (subprotocol), not a query string. Browsers don’t let you set Authorization headers in WS, but you can set a subprotocol.

Client: new WebSocket(url, ["Bearer", wsToken])

Server: read scope['subprotocols'] and validate.

If you must use ?token=..., remove query strings from WS access logs (see Nginx log_format above) and set short expiry.

5) Redis — config & deployment

Roles

Channels layer (pub/sub groups for WS broadcasts).

Celery broker (and optionally result backend).

redis.conf highlights

bind 127.0.0.1 ::1
port 6379
protected-mode yes
save ""                 # disable RDB if ephemeral (Channels)
appendonly no            # for pure ephemeral; set yes if you also want Celery results persisted
maxmemory 512mb
maxmemory-policy allkeys-lru
tcp-keepalive 300

(If you need persistent Celery results, enable AOF or use Postgres as result backend.)

Systemd service

[Unit]
Description=Redis In-Memory Data Store
After=network.target

[Service]
Type=notify
ExecStart=/usr/bin/redis-server /etc/redis/redis.conf
User=redis
Group=redis
RuntimeDirectory=redis
LimitNOFILE=10032

[Install]
WantedBy=multi-user.target

Django settings

CHANNEL_LAYERS = {
  "default": {
    "BACKEND": "channels_redis.core.RedisChannelLayer",
    "CONFIG": {"hosts": [env("REDIS_URL", default="redis://127.0.0.1:6379/0")]},
  }
}

CELERY_BROKER_URL  = env("REDIS_URL", default="redis://127.0.0.1:6379/1")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://127.0.0.1:6379/2")

6) Celery — config & deployment

Install & settings

pip install celery

# settings.py (snippets)
CELERY_TASK_ACKS_LATE = True             # retry on worker crash
CELERY_WORKER_PREFETCH_MULTIPLIER = 2
CELERY_TASK_TIME_LIMIT = 30
CELERY_TASK_SOFT_TIME_LIMIT = 25
CELERY_BROKER_CONNECTION_MAX_RETRIES = 100
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = CELERY_RESULT_SERIALIZER = "json"
CELERY_BEAT_SCHEDULE = {
  "unpin-expired": {"task": "communityhub.tasks.unpin_expired", "schedule": 300},
  "archive-logs": {"task": "communityhub.tasks.archive_old_logs", "schedule": 86400},
}

App bootstrap

# naboomcommunity/celery.py
import os
from celery import Celery
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "naboomcommunity.settings")
app = Celery("naboomcommunity")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# naboomcommunity/__init__.py
from .celery import app as celery_app  # noqa: F401

Tasks (examples)

# communityhub/tasks.py
from celery import shared_task

@shared_task(bind=True, max_retries=3)
def fanout_alert(self, thread_id: int):
    # fetch devices, batch Expo, send Web Push, handle receipts
    ...

@shared_task
def unpin_expired():
    ...

@shared_task
def archive_old_logs():
    ...

systemd units

# /etc/systemd/system/celery.service
[Unit]
Description=Celery Worker
After=network.target redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/srv/app/current
Environment="DJANGO_SETTINGS_MODULE=naboomcommunity.settings"
ExecStart=/srv/app/venv/bin/celery -A naboomcommunity worker -l INFO --concurrency=4
Restart=always

[Install]
WantedBy=multi-user.target

# /etc/systemd/system/celery-beat.service
[Unit]
Description=Celery Beat
After=network.target redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/srv/app/current
Environment="DJANGO_SETTINGS_MODULE=naboomcommunity.settings"
ExecStart=/srv/app/venv/bin/celery -A naboomcommunity beat -l INFO
Restart=always

[Install]
WantedBy=multi-user.target

7) ASGI (Uvicorn) — run & verify WS endpoint

Run Uvicorn (behind Nginx)

/srv/app/venv/bin/uvicorn naboomcommunity.asgi:application \
  --host 127.0.0.1 --port 8000 \
  --workers 4 --loop uvloop --http httptools \
  --proxy-headers --forwarded-allow-ips="*"

Notes: start with workers = CPU cores (or cores*2 for IO‑heavy), adjust after profiling. Use --proxy-headers when behind Nginx.

systemd unit (Uvicorn)

# /etc/systemd/system/uvicorn.service
[Unit]
Description=Uvicorn ASGI Server
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/srv/app/current
ExecStart=/srv/app/venv/bin/uvicorn naboomcommunity.asgi:application --host 127.0.0.1 --port 8000 --workers 4 --loop uvloop --http httptools --proxy-headers --forwarded-allow-ips="*"
Restart=always

[Install]
WantedBy=multi-user.target

Verify WS endpoint

Smoke via CLI:

# Install wscat: npm i -g wscat
wscat -c wss://naboomneighbornet.net.za/ws/channels/1/
# If using subprotocol token
echo "Subprotocol auth only supported from custom clients; for browsers, your app will supply the token."

Programmatic (Web):

const ws = new WebSocket("wss://naboomneighbornet.net.za/ws/channels/1/");
ws.onopen = () => console.log("WS open");
ws.onmessage = (e) => console.log("WS", e.data);

Expected: On creating a new post in channel 1, a new_post message arrives within ~1–2s.

PlantUML — App Flow (as in EXP spec)

@startuml
start
:Launch -> read token & locale (MMKV);
if (logged in?) then (yes)
  :Fetch channels; connect WS;
  :Open channel -> list threads;
  :Open thread -> posts; reply;
else (no)
  :Login screen;
endif
:Notification tap -> deep link to thread;
stop
@enduml

EN/AF localisation checklist (push & UI)

Maintain per‑user language preference (Profile/Prefs).

Web Push/Expo push payloads generated in EN or AF strings:

EN: "New alert in {channel}"

AF: "Nuwe waarskuwing in {channel}"

Wagtail/Wagtail Admin snippet labels translated via .po files.

Vue & Expo bundles (en.json / af.json) kept in sync.

Quick runbooks

Deploy order (first time)

Provision Redis (db0=Channels, db1=broker, db2=results).

Start Uvicorn systemd unit.

Configure Nginx WS reverse proxy & TLS; reload.

Run DB migrations + seeds.

Start Celery worker + beat services.

Verify REST, WS, Web Push, Expo push.

Rollback plan

Keep last two app releases on disk (/srv/app/releases).

systemctl stop celery/uvicorn; symlink rollback; systemctl start.

Nginx config kept side‑by‑side with nginx -t before reload.

Appendix — Nginx gzip/brotli (optional)

gzip on;
gzip_comp_level 5;
gzip_min_length 1024;
gzip_types application/json text/plain text/css application/javascript;
# If ngx_brotli is available
#brotli on; brotli_comp_level 5; brotli_types application/json text/plain text/css application/javascript;

Appendix — Web SW (minimal)

self.addEventListener("push", (event) => {
  const data = event.data?.json() || {};
  const { title = "New alert", body = "", url = "/" } = data;
  event.waitUntil(self.registration.showNotification(title, { body, data: { url } }));
});
self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = event.notification.data?.url || "/";
  event.waitUntil(clients.openWindow(url));
});

