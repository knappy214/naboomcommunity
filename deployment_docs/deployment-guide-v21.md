# ============================================================================
# NABOOM COMMUNITY PLATFORM - DEPLOYMENT GUIDE (Updated)
# ============================================================================
#
# Version: 2.1
# Last Updated: October 2025
# Purpose: Production deployment optimized for specific software versions
#
# Software Stack (Confirmed Versions):
#   - Python 3.12.3
#   - Django 5.2.x
#   - Wagtail 7.1.x  
#   - PostgreSQL 16.10
#   - Nginx 1.24.0
#   - Node.js v22.20.0 LTS
#   - Redis 8.2.2
#   - Mosquitto 2.0.22
#   - Celery 5.5.3
#
# This guide provides step-by-step instructions for deploying the Naboom
# Community Platform with optimizations specific to these versions.
#
# ============================================================================

## TABLE OF CONTENTS

1. Prerequisites & System Requirements (Updated)
2. Directory Structure Setup
3. Environment Variables Configuration (Django 5.2 Updates)
4. Nginx 1.24.0 Configuration (HTTP/3 Ready)
5. Systemd Services Setup
6. Redis 8.2.2 Configuration (Performance Enhancements)
7. PostgreSQL 16 Setup (Advanced Features)
8. Mosquitto 2.0.22 Setup (Latest Security)
9. Django 5.2 + Wagtail 7.1 Configuration
10. Python 3.12.3 Optimizations
11. Celery 5.5.3 Configuration (Latest Features)
12. Node.js 22.20.0 Build Setup
13. Deployment Checklist
14. Testing & Verification
15. Version-Specific Troubleshooting

# ============================================================================
# 1. PREREQUISITES & SYSTEM REQUIREMENTS (Updated for Your Versions)
# ============================================================================

## Confirmed Software Versions

✅ **Python**: 3.12.3 (Latest stable with performance improvements)
✅ **Django**: 5.2.x (LTS with async views support)
✅ **Wagtail**: 7.1.x (Latest with improved admin UI)
✅ **PostgreSQL**: 16.10 (Advanced JSON features, better performance)
✅ **Nginx**: 1.24.0 (HTTP/3 support, improved WebSocket handling)
✅ **Node.js**: v22.20.0 LTS (Latest LTS with performance improvements)
✅ **Redis**: 8.2.2 (Latest with memory optimizations)
✅ **Mosquitto**: 2.0.22 (Latest security updates)
✅ **Celery**: 5.5.3 (Latest with improved monitoring)

## Server Requirements (Optimized for Your Stack)

- **OS**: Ubuntu 24.04 LTS (recommended for Python 3.12.3)
- **CPU**: 4-8 cores (Django 5.2 benefits from more cores due to async support)
- **RAM**: 12GB minimum (16GB recommended for Redis 8.2.2 + PostgreSQL 16)
- **Storage**: 100GB NVMe SSD (PostgreSQL 16 benefits from faster I/O)
- **Network**: Gigabit connection (for HTTP/3 benefits)

## Python 3.12.3 Specific Setup

```bash
# Verify Python version
python3 --version  # Should show: Python 3.12.3

# Install Python 3.12 specific packages
sudo apt-get update && sudo apt-get install -y \
    python3.12 \
    python3.12-dev \
    python3.12-venv \
    python3.12-distutils \
    build-essential \
    pkg-config \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    libjpeg-dev \
    libpillow-dev \
    zlib1g-dev

# Install pip for Python 3.12
curl https://bootstrap.pypa.io/get-pip.py | python3.12
```

## PostgreSQL 16.10 Installation

```bash
# Install PostgreSQL 16 with PostGIS
sudo apt-get install -y \
    postgresql-16 \
    postgresql-contrib-16 \
    postgresql-16-postgis-3 \
    postgresql-client-16 \
    libpq-dev

# Verify version
sudo -u postgres psql -c "SELECT version();"
# Should show: PostgreSQL 16.10
```

## Redis 8.2.2 Installation

```bash
# Install Redis 8.2.2 (latest stable)
wget https://download.redis.io/redis-stable.tar.gz
tar xzf redis-stable.tar.gz
cd redis-stable
make
sudo make install

# Verify version
redis-server --version
# Should show: Redis server v=8.2.2
```

## Nginx 1.24.0 with HTTP/3 Support

```bash
# Install Nginx 1.24.0 with HTTP/3 support
sudo apt-get install -y nginx-full

# Verify version and modules
nginx -v
nginx -V | grep -o with-[a-z_]*

# Should show: nginx version: nginx/1.24.0
# Should include: with-http_v3_module (if compiled with HTTP/3)
```

## Node.js 22.20.0 LTS Setup

```bash
# Install Node.js 22.20.0 LTS via NodeSource
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify version
node --version  # Should show: v22.20.0
npm --version   # Should show compatible npm version

# Install global packages for Vue.js build
sudo npm install -g @vue/cli@latest vite@latest
```

# ============================================================================
# 2. DIRECTORY STRUCTURE SETUP (Updated Paths)
# ============================================================================

## Create Application Directories

```bash
# Main application directory (using standard Python 3.12 layout)
sudo mkdir -p /opt/naboomcommunity
sudo chown www-data:www-data /opt/naboomcommunity

# Static and media directories (Django 5.2 recommended structure)
sudo mkdir -p /var/www/naboomcommunity/static
sudo mkdir -p /var/www/naboomcommunity/media
sudo mkdir -p /var/www/naboomcommunity/collected-static
sudo chown -R www-data:www-data /var/www/naboomcommunity

# Node.js build directories (for Vue 3 + Vite)
sudo mkdir -p /opt/naboomcommunity-frontend/panic-monitor
sudo mkdir -p /opt/naboomcommunity-frontend/community-hub
sudo chown -R www-data:www-data /opt/naboomcommunity-frontend

# Log directories (updated for all services)
sudo mkdir -p /var/log/naboom/{gunicorn,daphne,celery,mqtt,nginx}
sudo chown -R www-data:www-data /var/log/naboom

# Redis 8.2.2 specific directories
sudo mkdir -p /var/lib/redis/modules
sudo chown redis:redis /var/lib/redis/modules

# PostgreSQL 16 specific directories
sudo mkdir -p /var/lib/postgresql/16/backups
sudo chown postgres:postgres /var/lib/postgresql/16/backups
```

# ============================================================================
# 3. ENVIRONMENT VARIABLES (Django 5.2 + Python 3.12.3 Updates)
# ============================================================================

## Create .env File with Version-Specific Settings

Create `/opt/naboomcommunity/.env`:

```bash
# ============================================================================
# PYTHON 3.12.3 SPECIFIC SETTINGS
# ============================================================================

PYTHONPATH=/opt/naboomcommunity
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
PYTHONHASHSEED=random

# Python 3.12.3 performance optimizations
PYTHONOPTIMIZE=1
PYTHONMALLOCSTATS=0

# ============================================================================
# DJANGO 5.2 CORE SETTINGS
# ============================================================================

DJANGO_VERSION=5.2
SECRET_KEY=your-generated-secret-key-here-min-50-chars-random
DEBUG=False
ALLOWED_HOSTS=naboomneighbornet.net.za,localhost,127.0.0.1
DJANGO_SETTINGS_MODULE=naboomcommunity.settings.production

# Django 5.2 async support
DJANGO_ASYNC_ENABLE=True
ASYNC_WORKERS=4

# Django 5.2 security improvements
SECURE_REFERRER_POLICY=strict-origin-when-cross-origin
SECURE_CROSS_ORIGIN_OPENER_POLICY=same-origin

# ============================================================================
# WAGTAIL 7.1 SPECIFIC SETTINGS
# ============================================================================

WAGTAIL_VERSION=7.1
WAGTAIL_SITE_NAME=Naboom Community
WAGTAIL_ENABLE_ADMIN_DASHBOARD=True
WAGTAIL_ENABLE_LIVE_PREVIEW=True

# Wagtail 7.1 performance settings
WAGTAIL_CACHE_TTL=3600
WAGTAIL_ENABLE_SEARCH_PROMOTIONS=True

# ============================================================================
# POSTGRESQL 16.10 DATABASE CONFIGURATION
# ============================================================================

POSTGRES_VERSION=16
POSTGRES_DB=naboomneighbornetdb
POSTGRES_USER=naboomneighbornetdb_user
POSTGRES_PASSWORD='hpG8R0bIQpS@&5yO'
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432

# PostgreSQL 16 specific features
DATABASE_CONN_MAX_AGE=300
DATABASE_ATOMIC_REQUESTS=False
DATABASE_AUTOCOMMIT=True
DATABASE_ENGINE=django.contrib.gis.db.backends.postgis

# PostgreSQL 16 performance settings
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
DATABASE_POOL_RECYCLE=3600

# ============================================================================
# REDIS 8.2.2 CONFIGURATION
# ============================================================================

REDIS_VERSION=8.2.2
REDIS_URL=redis://127.0.0.1:6379
REDIS_PASSWORD=your-strong-redis-password-here

# Redis 8.2.2 database allocation
CACHE_REDIS_DB=0          # Django cache
CHANNELS_REDIS_DB=1       # WebSocket pub/sub
CELERY_REDIS_DB=2         # Celery broker & results
SESSION_REDIS_DB=3        # Django sessions (new in setup)

# Redis 8.2.2 performance settings
REDIS_CONNECTION_POOL_SIZE=50
REDIS_SOCKET_KEEPALIVE=True
REDIS_SOCKET_KEEPALIVE_OPTIONS={}

# ============================================================================
# CELERY 5.5.3 CONFIGURATION
# ============================================================================

CELERY_VERSION=5.5.3
CELERY_BROKER_URL=redis://:your-strong-redis-password@127.0.0.1:6379/2
CELERY_RESULT_BACKEND=redis://:your-strong-redis-password@127.0.0.1:6379/2

# Celery 5.5.3 new features
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_ACCEPT_CONTENT=json
CELERY_TIMEZONE=Africa/Johannesburg
CELERY_ENABLE_UTC=True

# Celery 5.5.3 performance improvements
CELERY_WORKER_PREFETCH_MULTIPLIER=4
CELERY_TASK_ACKS_LATE=True
CELERY_TASK_REJECT_ON_WORKER_LOST=True
CELERY_WORKER_DISABLE_RATE_LIMITS=True

# Celery 5.5.3 monitoring
CELERY_SEND_TASK_EVENTS=True
CELERY_TASK_SEND_SENT_EVENT=True
CELERY_RESULT_EXPIRES=3600

# ============================================================================
# NGINX 1.24.0 + HTTP/3 SETTINGS
# ============================================================================

NGINX_VERSION=1.24.0
NGINX_ENABLE_HTTP3=True
NGINX_WORKER_PROCESSES=auto
NGINX_WORKER_CONNECTIONS=4096

# ============================================================================
# NODE.JS 22.20.0 BUILD SETTINGS
# ============================================================================

NODE_VERSION=22.20.0
NODE_ENV=production
NODE_OPTIONS=--max-old-space-size=4096

# Vue.js build settings
VUE_CLI_VERSION=5
VITE_VERSION=5
BUILD_TOOL=vite

# ============================================================================
# MOSQUITTO 2.0.22 MQTT SETTINGS
# ============================================================================

MOSQUITTO_VERSION=2.0.22
MQTT_HOST=127.0.0.1
MQTT_PORT=1883
MQTT_WS_PORT=8083
MQTT_USER=app_subscriber
MQTT_PASSWORD=your-mqtt-password-here

# Mosquitto 2.0.22 security features
MQTT_REQUIRE_CERTIFICATE=False
MQTT_CAFILE=/etc/mosquitto/ca_certificates/ca.crt
MQTT_CERTFILE=/etc/mosquitto/certs/server.crt
MQTT_KEYFILE=/etc/mosquitto/certs/server.key

# ============================================================================
# SECURITY SETTINGS (Updated for Latest Versions)
# ============================================================================

# Django 5.2 security enhancements
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=63072000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SECURE_CONTENT_TYPE_NOSNIFF=True
SECURE_BROWSER_XSS_FILTER=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
X_FRAME_OPTIONS=DENY

# Django 5.2 new security features
SECURE_REFERRER_POLICY=strict-origin-when-cross-origin
SECURE_CROSS_ORIGIN_OPENER_POLICY=same-origin-allow-popups

# ============================================================================
# LOGGING CONFIGURATION (Enhanced)
# ============================================================================

LOG_LEVEL=INFO
LOG_DIR=/var/log/naboom/
DJANGO_LOG_LEVEL=INFO

# Structured logging for better monitoring
ENABLE_STRUCTURED_LOGGING=True
LOG_FORMAT=json
LOG_INCLUDE_TRACE_ID=True

# ============================================================================
# MONITORING & OBSERVABILITY (New Section)
# ============================================================================

# Application monitoring
ENABLE_APM=True
APM_SERVICE_NAME=naboomcommunity
APM_ENVIRONMENT=production

# Health check settings
HEALTH_CHECK_ENABLED=True
HEALTH_CHECK_DATABASE=True
HEALTH_CHECK_CACHE=True
HEALTH_CHECK_CELERY=True
```

## Generate Secrets for Your Versions

```bash
# Generate Django 5.2 compatible SECRET_KEY
python3.12 -c "
from django.core.management.utils import get_random_secret_key
print('SECRET_KEY=' + get_random_secret_key())
"

# Generate strong Redis password (Redis 8.2.2 recommendation)
python3.12 -c "
import secrets
import string
alphabet = string.ascii_letters + string.digits + '!@#$%^&*'
password = ''.join(secrets.choice(alphabet) for i in range(32))
print('REDIS_PASSWORD=' + password)
"

# Generate VAPID keys for web push
python3.12 -c "
from pywebpush import webpush
keys = webpush.WebPusher.generate_vapid_keys()
print('VAPID_PUBLIC_KEY=' + keys['public_key'])
print('VAPID_PRIVATE_KEY=' + keys['private_key'])
"
```

# ============================================================================
# 4. NGINX 1.24.0 CONFIGURATION (HTTP/3 + Performance)
# ============================================================================

## Enhanced Nginx Configuration for Version 1.24.0

Create `/etc/nginx/sites-available/naboomneighbornet.net.za`:

```nginx
# ============================================================================
# NGINX 1.24.0 OPTIMIZED CONFIGURATION FOR NABOOM COMMUNITY
# ============================================================================
# HTTP/3 Support + Advanced Features for Nginx 1.24.0

# Load balancing for multiple Gunicorn workers
upstream naboom_app {
    least_conn;
    server 127.0.0.1:8001 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8002 max_fails=3 fail_timeout=30s backup;
    keepalive 32;
    keepalive_requests 100;
    keepalive_timeout 60s;
}

# WebSocket load balancing for Daphne
upstream naboom_ws {
    ip_hash;  # Ensure WebSocket connections stick to same server
    server 127.0.0.1:9000 max_fails=2 fail_timeout=30s;
    keepalive 64;
}

# Mosquitto MQTT WebSocket
upstream mosquitto_ws {
    server 127.0.0.1:8083 max_fails=2 fail_timeout=30s;
    keepalive 32;
}

# ============================================================================
# RATE LIMITING ZONES (Enhanced for High Traffic)
# ============================================================================

# General API with burst handling
limit_req_zone $binary_remote_addr zone=api_general:20m rate=120r/m;

# Panic API (emergency system gets higher limits)
limit_req_zone $binary_remote_addr zone=panic_api:20m rate=300r/m;

# Vehicle tracking with geographic consideration
limit_req_zone $binary_remote_addr zone=vehicle_track:15m rate=60r/m;

# Admin protection with IP whitelisting support
limit_req_zone $binary_remote_addr zone=admin_login:10m rate=10r/m;

# Web Push with device consideration
limit_req_zone $binary_remote_addr zone=push_reg:10m rate=30r/m;

# Static content rate limiting
limit_req_zone $binary_remote_addr zone=static_content:10m rate=1000r/m;

# ============================================================================
# CONNECTION LIMITING (Enhanced)
# ============================================================================

limit_conn_zone $binary_remote_addr zone=ws_conn:20m;
limit_conn_zone $binary_remote_addr zone=mqtt_conn:15m;
limit_conn_zone $binary_remote_addr zone=general_conn:20m;

# ============================================================================
# HTTP/3 AND SECURITY HEADERS MAP
# ============================================================================

map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}

# Enhanced security headers based on request type
map $request_uri $csp_header {
    ~^/admin/     "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; connect-src 'self' wss://naboomneighbornet.net.za";
    ~^/ws/        "default-src 'self'; connect-src 'self' wss://naboomneighbornet.net.za";
    default       "default-src 'self'; img-src 'self' data: blob: https://*.gravatar.com; font-src 'self' data:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self' wss://naboomneighbornet.net.za; frame-ancestors 'none';";
}

# ============================================================================
# HTTP SERVER (Port 80) - Enhanced Redirect
# ============================================================================

server {
    listen 80;
    listen [::]:80;
    server_name naboomneighbornet.net.za www.naboomneighbornet.net.za;

    # Security headers even for HTTP
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;

    # ACME Challenge with rate limiting
    location ^~ /.well-known/acme-challenge/ {
        limit_req zone=static_content burst=10 nodelay;
        alias /var/www/_letsencrypt/;
        default_type text/plain;
        try_files $uri =404;
    }

    # Redirect with HSTS preload hint
    location / {
        return 301 https://$host$request_uri;
    }
}

# ============================================================================
# HTTPS SERVER (Port 443) - HTTP/3 + Advanced Features
# ============================================================================

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    
    # HTTP/3 support (Nginx 1.24.0)
    listen 443 quic reuseport;
    listen [::]:443 quic reuseport;

    server_name naboomneighbornet.net.za www.naboomneighbornet.net.za;

    # ========================================================================
    # HTTP/3 AND TLS 1.3 CONFIGURATION
    # ========================================================================
    
    ssl_certificate     /etc/letsencrypt/live/naboomneighbornet.net.za/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/naboomneighbornet.net.za/privkey.pem;

    # Advanced TLS configuration for 2025
    ssl_protocols TLSv1.3 TLSv1.2;
    ssl_ciphers 'TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:TLS_AES_128_GCM_SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;
    
    # TLS 1.3 early data support
    ssl_early_data on;
    
    # Session management
    ssl_session_timeout 1d;
    ssl_session_cache shared:NaboomSSL:50m;
    ssl_session_tickets off;

    # OCSP Stapling with Must-Staple
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/letsencrypt/live/naboomneighbornet.net.za/chain.pem;
    resolver 1.1.1.1 8.8.8.8 valid=300s;
    resolver_timeout 5s;

    # HTTP/3 Alt-Svc header
    add_header Alt-Svc 'h3=":443"; ma=86400' always;

    # ========================================================================
    # ENHANCED SECURITY HEADERS (2025 Standards)
    # ========================================================================
    
    # HSTS with preload
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    
    # Frame protection
    add_header X-Frame-Options "DENY" always;
    
    # MIME type sniffing protection
    add_header X-Content-Type-Options "nosniff" always;
    
    # XSS protection for legacy browsers
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Referrer policy
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Permissions Policy (2025 update)
    add_header Permissions-Policy "geolocation=(self), microphone=(), camera=(), payment=(), usb=(), bluetooth=()" always;
    
    # Content Security Policy (dynamic based on location)
    add_header Content-Security-Policy $csp_header always;
    
    # Cross-Origin policies
    add_header Cross-Origin-Opener-Policy "same-origin" always;
    add_header Cross-Origin-Resource-Policy "same-site" always;
    add_header Cross-Origin-Embedder-Policy "require-corp" always;

    # ========================================================================
    # CLIENT SETTINGS (Nginx 1.24.0 Optimized)
    # ========================================================================
    
    client_max_body_size 100M;  # Increased for modern file uploads
    client_body_timeout 60s;
    client_header_timeout 60s;
    client_body_buffer_size 256k;
    large_client_header_buffers 8 16k;

    # Connection limits
    limit_conn general_conn 100;

    # ========================================================================
    # ADVANCED COMPRESSION (Nginx 1.24.0)
    # ========================================================================
    
    # Brotli compression (if module available)
    brotli on;
    brotli_comp_level 6;
    brotli_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript image/svg+xml;

    # Gzip fallback
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_min_length 1000;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # ========================================================================
    # LOGGING (Enhanced for Monitoring)
    # ========================================================================
    
    # Custom log format with timing information
    log_format main_timed '$remote_addr - $remote_user [$time_local] '
                         '"$request" $status $bytes_sent '
                         '"$http_referer" "$http_user_agent" '
                         'rt=$request_time uct="$upstream_connect_time" '
                         'uht="$upstream_header_time" urt="$upstream_response_time"';

    access_log /var/log/naboom/nginx/access.log main_timed buffer=32k flush=1m;
    error_log /var/log/naboom/nginx/error.log warn;

    # ========================================================================
    # STATIC FILES (Advanced Caching + HTTP/3)
    # ========================================================================
    
    location /static/ {
        alias /var/www/naboomcommunity/collected-static/;
        
        # HTTP/3 push for critical resources
        http3_push /static/css/main.css;
        http3_push /static/js/main.js;
        
        # Advanced caching with versioning
        location ~* \.(css|js|woff2|woff)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            add_header X-Content-Type-Options "nosniff" always;
            access_log off;
            
            # Preload hints for HTTP/2 push
            add_header Link "</static/css/main.css>; rel=preload; as=style" always;
        }
        
        # Images and media
        location ~* \.(png|jpg|jpeg|gif|webp|svg|ico)$ {
            expires 6M;
            add_header Cache-Control "public";
            add_header X-Content-Type-Options "nosniff" always;
            access_log off;
            
            # Image optimization headers
            add_header Vary "Accept, Accept-Encoding" always;
        }
        
        # Default static file handling
        expires 30d;
        add_header Cache-Control "public";
        sendfile on;
        tcp_nopush on;
        tcp_nodelay on;
        access_log off;
    }

    # ========================================================================
    # MEDIA FILES (Enhanced Security)
    # ========================================================================
    
    location /media/ {
        alias /var/www/naboomcommunity/media/;
        
        # Enhanced security for user uploads
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-Frame-Options "DENY" always;
        
        # File type restrictions
        location ~* \.(php|py|pl|sh|cgi|jsp|asp|exe|bat)$ {
            deny all;
            return 403;
        }
        
        # PDF and document security
        location ~* \.(pdf|doc|docx|xls|xlsx)$ {
            add_header Content-Security-Policy "default-src 'none'; object-src 'none';" always;
        }
        
        expires 7d;
        add_header Cache-Control "public, max-age=604800";
        sendfile on;
        access_log off;
    }

    # ========================================================================
    # HEALTH CHECKS (Enhanced Monitoring)
    # ========================================================================
    
    # Application health check
    location = /health {
        limit_req zone=api_general burst=10 nodelay;
        
        proxy_pass http://naboom_app;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        
        # Fast timeouts for health checks
        proxy_connect_timeout 2s;
        proxy_send_timeout 2s;
        proxy_read_timeout 2s;
        
        access_log off;
    }
    
    # Deep health check for monitoring systems
    location = /health/deep {
        limit_req zone=api_general burst=5 nodelay;
        
        # Restrict to monitoring IPs
        allow 127.0.0.1;
        allow 10.0.0.0/8;
        deny all;
        
        proxy_pass http://naboom_app;
        include /etc/nginx/snippets/proxy-common.conf;
        access_log off;
    }

    # ========================================================================
    # PANIC SYSTEM (Enhanced Performance)
    # ========================================================================
    
    # Panic API with geographic load balancing
    location /panic/api/ {
        limit_req zone=panic_api burst=100 nodelay;
        limit_req_status 429;
        
        # Priority routing for emergency system
        proxy_pass http://naboom_app;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Enhanced timeouts for critical system
        proxy_connect_timeout 5s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # Retry logic for high availability
        proxy_next_upstream error timeout http_502 http_503;
        proxy_next_upstream_tries 2;
        
        proxy_buffering on;
        proxy_buffer_size 8k;
        proxy_buffers 16 8k;
    }
    
    # SSE Stream (Optimized for Real-time)
    location = /panic/api/stream {
        limit_req zone=panic_api burst=20 nodelay;
        
        proxy_pass http://naboom_app;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # SSE optimizations
        proxy_connect_timeout 5s;
        proxy_send_timeout 24h;  # Long-lived connections
        proxy_read_timeout 24h;
        
        # Critical: No buffering for real-time streams
        proxy_buffering off;
        proxy_cache off;
        add_header X-Accel-Buffering no;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Pragma "no-cache";
        add_header Expires "0";
        
        # HTTP/2 Server Push for SSE polyfills
        http2_push /static/js/sse-polyfill.js;
        
        chunked_transfer_encoding on;
    }

    # ========================================================================
    # WEBSOCKET (Enhanced for High Concurrency)
    # ========================================================================
    
    location /ws/ {
        limit_conn ws_conn 1000;  # Increased for production
        limit_req zone=api_general burst=50 nodelay;
        
        proxy_pass http://naboom_ws;
        proxy_http_version 1.1;
        
        # WebSocket headers
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket optimizations
        proxy_connect_timeout 60s;
        proxy_send_timeout 24h;
        proxy_read_timeout 24h;
        
        # No buffering for WebSocket
        proxy_buffering off;
        proxy_redirect off;
        
        # TCP optimizations
        tcp_nodelay on;
        proxy_socket_keepalive on;
        
        # WebSocket compression (if supported)
        proxy_set_header Sec-WebSocket-Extensions "permessage-deflate";
    }

    # ========================================================================
    # MQTT OVER WEBSOCKET (Production Optimized)
    # ========================================================================
    
    location /mqtt {
        limit_conn mqtt_conn 500;
        limit_req zone=panic_api burst=30 nodelay;
        
        # Device authentication middleware
        auth_request /auth/mqtt;
        
        proxy_pass http://mosquitto_ws;
        proxy_http_version 1.1;
        
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # MQTT connection timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 1h;
        proxy_read_timeout 1h;
        
        proxy_buffering off;
        tcp_nodelay on;
    }
    
    # MQTT Authentication endpoint
    location = /auth/mqtt {
        internal;
        proxy_pass http://naboom_app/api/auth/mqtt;
        proxy_pass_request_body off;
        proxy_set_header Content-Length "";
        proxy_set_header X-Original-URI $request_uri;
    }

    # ========================================================================
    # DJANGO ADMIN (Enhanced Security)
    # ========================================================================
    
    location /admin/login/ {
        limit_req zone=admin_login burst=5 nodelay;
        
        # IP whitelist for admin access (uncomment and configure)
        # allow 192.168.1.0/24;
        # allow 10.0.0.0/8;
        # deny all;
        
        proxy_pass http://naboom_app;
        include /etc/nginx/snippets/proxy-common.conf;
        
        # Additional security headers for admin
        add_header X-Frame-Options "DENY" always;
        add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
    }
    
    location /admin/ {
        limit_req zone=api_general burst=20 nodelay;
        
        proxy_pass http://naboom_app;
        include /etc/nginx/snippets/proxy-common.conf;
        
        # Extended timeout for admin operations
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }

    # ========================================================================
    # API ENDPOINTS (Load Balanced)
    # ========================================================================
    
    location /api/ {
        limit_req zone=api_general burst=50 nodelay;
        
        proxy_pass http://naboom_app;
        include /etc/nginx/snippets/proxy-common.conf;
        
        # API-specific optimizations
        proxy_buffering on;
        proxy_buffer_size 8k;
        proxy_buffers 16 8k;
        
        # Caching for GET requests
        location ~ ^/api/.*\?.*$ {
            # Cache GET requests with query parameters
            proxy_cache api_cache;
            proxy_cache_valid 200 5m;
            proxy_cache_key "$scheme$request_method$host$request_uri";
        }
    }

    # ========================================================================
    # FRONTEND SPAS (Vue.js with Vite)
    # ========================================================================
    
    # Panic Monitor SPA
    location /monitor/ {
        alias /opt/naboomcommunity-frontend/panic-monitor/dist/;
        try_files $uri $uri/ /monitor/index.html;
        
        # Vite build optimization
        location ~* \.(js|css|woff2)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            access_log off;
            
            # Preload critical resources
            add_header Link "</monitor/assets/index.js>; rel=modulepreload" always;
        }
        
        # SPA index with no cache
        location = /monitor/index.html {
            expires -1;
            add_header Cache-Control "no-store, no-cache, must-revalidate";
            add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self' wss://naboomneighbornet.net.za;" always;
        }
    }

    # ========================================================================
    # ROOT LOCATION (Wagtail CMS)
    # ========================================================================
    
    location / {
        limit_req zone=api_general burst=30 nodelay;
        
        proxy_pass http://naboom_app;
        include /etc/nginx/snippets/proxy-common.conf;
        
        # CMS-specific caching
        proxy_cache cms_cache;
        proxy_cache_valid 200 10m;
        proxy_cache_bypass $http_cache_control;
        proxy_no_cache $http_cache_control;
    }

    # ========================================================================
    # ERROR PAGES (Enhanced)
    # ========================================================================
    
    error_page 404 /404.html;
    error_page 429 /429.html;
    error_page 500 502 503 504 /50x.html;
    
    location = /404.html {
        root /var/www/naboomcommunity/error_pages;
        internal;
        add_header Cache-Control "no-cache" always;
    }
    
    location = /429.html {
        root /var/www/naboomcommunity/error_pages;
        internal;
        add_header Cache-Control "no-cache" always;
        add_header Retry-After "60" always;
    }
    
    location = /50x.html {
        root /var/www/naboomcommunity/error_pages;
        internal;
        add_header Cache-Control "no-cache" always;
    }
}

# ============================================================================
# CACHE DEFINITIONS
# ============================================================================

proxy_cache_path /var/cache/nginx/api levels=1:2 keys_zone=api_cache:10m inactive=60m use_temp_path=off;
proxy_cache_path /var/cache/nginx/cms levels=1:2 keys_zone=cms_cache:10m inactive=30m use_temp_path=off;
```

## Create Cache Directories

```bash
sudo mkdir -p /var/cache/nginx/api
sudo mkdir -p /var/cache/nginx/cms
sudo chown -R www-data:www-data /var/cache/nginx
```

# ============================================================================
# 5. REDIS 8.2.2 CONFIGURATION (Latest Optimizations)
# ============================================================================

## Enhanced Redis Configuration for Version 8.2.2

Create `/etc/redis/redis-8.2.2.conf`:

```conf
# ============================================================================
# REDIS 8.2.2 OPTIMIZED CONFIGURATION
# ============================================================================

# Network Configuration
bind 127.0.0.1 -::1
port 6379
tcp-backlog 511
timeout 0
tcp-keepalive 300

# Security (Redis 8.2.2 enhancements)
requirepass your-strong-redis-password-here
protected-mode yes

# Redis 8.2.2 new security features
user default on nopass ~* &* +@all
user app_user on >your-app-user-password ~cached:* ~sessions:* ~celery:* +@all -@dangerous

# Memory Management (Redis 8.2.2 improvements)
maxmemory 4gb
maxmemory-policy allkeys-lru
maxmemory-samples 10

# Redis 8.2.2 memory efficiency
hash-max-ziplist-entries 1000
hash-max-ziplist-value 64
list-max-ziplist-size -2
set-max-intset-entries 512
zset-max-ziplist-entries 256
zset-max-ziplist-value 64

# Persistence (Enhanced in 8.2.2)
save 900 1
save 300 10
save 60 10000

# AOF Configuration (Redis 8.2.2 improvements)
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

# Redis 8.2.2 Multi-part AOF
aof-rewrite-incremental-fsync yes

# Database Configuration
databases 16

# Performance Tuning (Redis 8.2.2)
hz 10
dynamic-hz yes

# Redis 8.2.2 threading improvements
io-threads 4
io-threads-do-reads yes

# Logging
loglevel notice
logfile /var/log/redis/redis-server.log

# Client Configuration
maxclients 10000
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit replica 256mb 64mb 60
client-output-buffer-limit pubsub 32mb 8mb 60

# Redis 8.2.2 connection optimizations
tcp-keepalive 300
timeout 300

# Slow Log
slowlog-log-slower-than 10000
slowlog-max-len 128

# Latency Monitoring (Enhanced in 8.2.2)
latency-monitor-threshold 100

# Redis 8.2.2 New Features
# Function libraries support
enable-protected-configs yes
enable-debug-command no
enable-module-command no

# Stream optimizations
stream-node-max-bytes 4096
stream-node-max-entries 100

# Redis 8.2.2 Cluster improvements (for future scaling)
# cluster-enabled no
# cluster-config-file nodes-6379.conf
# cluster-node-timeout 15000
# cluster-announce-hostname ""
```

# ============================================================================
# 6. POSTGRESQL 16.10 CONFIGURATION (Advanced Features)
# ============================================================================

## PostgreSQL 16 Performance Optimization

Edit `/etc/postgresql/16/main/postgresql.conf`:

```conf
# ============================================================================
# POSTGRESQL 16.10 OPTIMIZED CONFIGURATION
# ============================================================================

# Connection Settings
max_connections = 200
superuser_reserved_connections = 3

# Memory Settings (for 16GB RAM server)
shared_buffers = 4GB                    # 25% of RAM
effective_cache_size = 12GB             # 75% of RAM
maintenance_work_mem = 1GB
work_mem = 32MB
wal_buffers = 64MB

# PostgreSQL 16 new memory features
huge_pages = try
shared_memory_type = mmap

# Checkpoint Settings (PostgreSQL 16 improvements)
checkpoint_timeout = 15min
checkpoint_completion_target = 0.9
max_wal_size = 4GB
min_wal_size = 1GB

# Query Planner (PostgreSQL 16 enhancements)
random_page_cost = 1.1                  # For NVMe SSD
effective_io_concurrency = 200          # For NVMe SSD
maintenance_io_concurrency = 100
max_worker_processes = 8
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
max_parallel_maintenance_workers = 4

# PostgreSQL 16 new planner features
enable_partitionwise_join = on
enable_partitionwise_aggregate = on
enable_parallel_append = on
enable_parallel_hash = on

# Write-Ahead Logging (PostgreSQL 16 improvements)
wal_level = replica
synchronous_commit = on
wal_sync_method = fdatasync
full_page_writes = on
wal_compression = lz4
wal_log_hints = on

# PostgreSQL 16 WAL improvements
wal_init_zero = on
wal_recycle = on

# Archiving (for Point-in-Time Recovery)
archive_mode = on
archive_command = 'test ! -f /var/lib/postgresql/16/archive/%f && cp %p /var/lib/postgresql/16/archive/%f'

# Replication (PostgreSQL 16 enhancements)
max_wal_senders = 10
hot_standby = on
hot_standby_feedback = on

# Background Writer
bgwriter_delay = 200ms
bgwriter_lru_maxpages = 100
bgwriter_lru_multiplier = 2.0

# Autovacuum (PostgreSQL 16 improvements)
autovacuum = on
autovacuum_max_workers = 6
autovacuum_naptime = 30s
autovacuum_vacuum_threshold = 50
autovacuum_vacuum_scale_factor = 0.1
autovacuum_analyze_threshold = 50
autovacuum_analyze_scale_factor = 0.05

# Statistics
track_activities = on
track_counts = on
track_io_timing = on
track_functions = all
stats_temp_directory = '/var/run/postgresql/16-main.pg_stat_tmp'

# PostgreSQL 16 new statistics features
compute_query_id = on
log_parameter_max_length = -1
log_parameter_max_length_on_error = 0

# Error Reporting and Logging
log_destination = 'stderr,csvlog'
logging_collector = on
log_directory = '/var/log/postgresql'
log_filename = 'postgresql-16-%Y-%m-%d_%H%M%S.log'
log_rotation_age = 1d
log_rotation_size = 100MB
log_min_duration_statement = 1000
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on
log_statement = 'mod'
log_temp_files = 0

# PostgreSQL 16 enhanced logging
log_recovery_conflict_waits = on
log_startup_progress_interval = 30s

# Locale and Formatting
datestyle = 'iso, mdy'
timezone = 'Africa/Johannesburg'
lc_messages = 'en_US.UTF-8'
lc_monetary = 'en_US.UTF-8'
lc_numeric = 'en_US.UTF-8'
lc_time = 'en_US.UTF-8'
default_text_search_config = 'pg_catalog.english'

# PostgreSQL 16 JSON improvements
shared_preload_libraries = 'pg_stat_statements'

# Extensions (PostgreSQL 16 enhanced PostGIS)
# PostGIS 3.4 optimizations will be loaded automatically
```

## Create Archive Directory

```bash
sudo mkdir -p /var/lib/postgresql/16/archive
sudo chown postgres:postgres /var/lib/postgresql/16/archive
sudo chmod 700 /var/lib/postgresql/16/archive
```

## Initialize Database with PostgreSQL 16 Features

```bash
# Connect as postgres user
sudo -u postgres psql

-- Create database with PostgreSQL 16 optimizations
CREATE DATABASE naboomneighbornetdb
    WITH OWNER = naboomneighbornetdb_user
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1
    IS_TEMPLATE = False;

-- Connect to the database
\c naboomneighbornetdb

-- Enable PostgreSQL 16 + PostGIS 3.4 extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS btree_gin;
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- PostgreSQL 16 performance monitoring
CREATE EXTENSION IF NOT EXISTS pg_prewarm;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE naboomneighbornetdb TO naboomneighbornetdb_user;
GRANT ALL ON SCHEMA public TO naboomneighbornetdb_user;
GRANT ALL ON ALL TABLES IN SCHEMA public TO naboomneighbornetdb_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO naboomneighbornetdb_user;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO naboomneighbornetdb_user;

\q
```

# ============================================================================
# 7. DJANGO 5.2 + WAGTAIL 7.1 CONFIGURATION
# ============================================================================

## requirements.txt for Python 3.12.3

Create `/opt/naboomcommunity/requirements.txt`:

```txt
# ============================================================================
# NABOOM COMMUNITY REQUIREMENTS - Python 3.12.3 Compatible
# ============================================================================

# Django 5.2 LTS
Django>=5.2,<5.3
django-environ>=0.11.2
django-extensions>=3.2.3
django-cors-headers>=4.3.1

# Wagtail 7.1
wagtail>=7.1,<7.2
wagtail-django-recaptcha>=1.0

# Database & Geospatial
psycopg[binary]>=3.1.15
django-postgres-extra>=2.0.8

# Redis & Caching (Redis 8.2.2 compatible)
redis>=5.0.1
django-redis>=5.4.0
hiredis>=2.2.3

# Celery 5.5.3 with latest features
celery>=5.5.3,<5.6
django-celery-beat>=2.5.0
django-celery-results>=2.5.0
kombu>=5.3.4

# Django Channels for WebSocket (updated for Django 5.2)
channels>=4.0.0
channels-redis>=4.1.0
daphne>=4.1.0

# ASGI server
uvicorn>=0.24.0

# API Framework
djangorestframework>=3.14.0
django-filter>=23.5
drf-spectacular>=0.27.0

# Authentication & Security
django-allauth>=0.57.0
django-otp>=1.2.2
django-axes>=6.1.1
cryptography>=41.0.7

# File Handling & Storage
Pillow>=10.1.0
django-storages>=1.14.2
boto3>=1.34.0  # If using S3

# Monitoring & Logging
sentry-sdk>=1.38.0
django-health-check>=3.17.0
structlog>=23.2.0

# Web Push Notifications (CommunityHub)
pywebpush>=1.14.0
py-vapid>=1.9.0

# MQTT Client (Panic System)
paho-mqtt>=1.6.1

# Geospatial Libraries
geopy>=2.4.1
shapely>=2.0.2
geos>=0.2.3

# HTTP & Networking
requests>=2.31.0
urllib3>=2.1.0
httpx>=0.25.2

# Task Queue & Background Processing
dramatiq>=1.15.0  # Alternative to Celery for some tasks
APScheduler>=3.10.4

# Data Processing
pandas>=2.1.4
numpy>=1.26.2

# Utilities
python-dateutil>=2.8.2
pytz>=2023.3.post1
python-slugify>=8.0.1
Faker>=20.1.0  # For development/testing

# Development & Testing (keep for production debugging)
django-debug-toolbar>=4.2.0
factory-boy>=3.3.0
pytest>=7.4.3
pytest-django>=4.7.0
pytest-cov>=4.1.0

# Production WSGI/ASGI
gunicorn>=21.2.0
whitenoise>=6.6.0  # For static file serving fallback

# Linting & Code Quality
black>=23.11.0
flake8>=6.1.0
isort>=5.12.0

# Type Checking (Python 3.12.3 compatible)
mypy>=1.7.1
django-stubs>=4.2.7
```

## Django 5.2 Settings Structure

Create `/opt/naboomcommunity/naboomcommunity/settings/base.py`:

```python
# ============================================================================
# DJANGO 5.2 + PYTHON 3.12.3 BASE SETTINGS
# ============================================================================

import os
import sys
from pathlib import Path
from django.core.management.utils import get_random_secret_key
import environ

# Environment variables
env = environ.Env(
    DEBUG=(bool, False),
    DJANGO_ASYNC_ENABLE=(bool, True),
)

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Read .env file
env.read_env(os.path.join(BASE_DIR, '.env'))

# ============================================================================
# DJANGO 5.2 CORE SETTINGS
# ============================================================================

SECRET_KEY = env('SECRET_KEY', default=get_random_secret_key())
DEBUG = env('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

# Django 5.2 new settings
SECURE_REFERRER_POLICY = env('SECURE_REFERRER_POLICY', default='strict-origin-when-cross-origin')
SECURE_CROSS_ORIGIN_OPENER_POLICY = env('SECURE_CROSS_ORIGIN_OPENER_POLICY', default='same-origin')

# ============================================================================
# APPLICATION DEFINITION
# ============================================================================

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',  # PostGIS support
]

THIRD_PARTY_APPS = [
    # REST Framework
    'rest_framework',
    'django_filters',
    'corsheaders',
    
    # Wagtail 7.1
    'wagtail.contrib.forms',
    'wagtail.contrib.redirects',
    'wagtail.embeds',
    'wagtail.sites',
    'wagtail.users',
    'wagtail.snippets',
    'wagtail.documents',
    'wagtail.images',
    'wagtail.search',
    'wagtail.admin',
    'wagtail',
    'wagtail.api.v2',
    'taggit',
    
    # Django Channels 4.0
    'channels',
    
    # Celery 5.5.3
    'django_celery_beat',
    'django_celery_results',
    
    # Monitoring & Health
    'health_check',
    'health_check.db',
    'health_check.cache',
    'health_check.storage',
    
    # Authentication
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    
    # Security
    'axes',
]

LOCAL_APPS = [
    'panic.apps.PanicConfig',           # Emergency response system
    'communityhub.apps.CommunityHubConfig',  # Communication platform
    'users.apps.UsersConfig',           # Extended user profiles
    'core.apps.CoreConfig',             # Core utilities
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ============================================================================
# MIDDLEWARE CONFIGURATION (Django 5.2 optimized)
# ============================================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'wagtail.contrib.redirects.middleware.RedirectMiddleware',
    'axes.middleware.AxesMiddleware',  # Security
]

# Django 5.2 async middleware support
ASYNC_MIDDLEWARE = env('DJANGO_ASYNC_ENABLE', default=True)

# ============================================================================
# URL CONFIGURATION
# ============================================================================

ROOT_URLCONF = 'naboomcommunity.urls'
WSGI_APPLICATION = 'naboomcommunity.wsgi.application'
ASGI_APPLICATION = 'naboomcommunity.asgi.application'

# ============================================================================
# DATABASE CONFIGURATION (PostgreSQL 16)
# ============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': env('POSTGRES_DB'),
        'USER': env('POSTGRES_USER'),
        'PASSWORD': env('POSTGRES_PASSWORD'),
        'HOST': env('POSTGRES_HOST', default='127.0.0.1'),
        'PORT': env('POSTGRES_PORT', default='5432'),
        'CONN_MAX_AGE': env.int('DATABASE_CONN_MAX_AGE', default=300),
        'CONN_HEALTH_CHECKS': True,  # Django 5.2 feature
        'OPTIONS': {
            'sslmode': 'prefer',
            'connect_timeout': 10,
            'options': '-c default_transaction_isolation=read_committed'
        },
        'TEST': {
            'NAME': 'test_naboomcommunity',
        },
    }
}

# Database routing for read/write splitting (future enhancement)
DATABASE_ROUTERS = []

# ============================================================================
# REDIS 8.2.2 CONFIGURATION
# ============================================================================

REDIS_URL = env('REDIS_URL', default='redis://127.0.0.1:6379')
REDIS_PASSWORD = env('REDIS_PASSWORD', default='')

# Cache Configuration (Redis DB 0)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"{REDIS_URL}/{env.int('CACHE_REDIS_DB', default=0)}",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
                'health_check_interval': 30,
            },
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'IGNORE_EXCEPTIONS': True,
        },
        'KEY_PREFIX': 'naboom',
        'VERSION': 1,
        'TIMEOUT': 300,
    }
}

# Session Configuration (Redis DB 3)
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'sessions'
CACHES['sessions'] = {
    'BACKEND': 'django_redis.cache.RedisCache',
    'LOCATION': f"{REDIS_URL}/{env.int('SESSION_REDIS_DB', default=3)}",
    'OPTIONS': {
        'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        'CONNECTION_POOL_CLASS_KWARGS': {
            'max_connections': 20,
            'retry_on_timeout': True,
        },
    },
    'KEY_PREFIX': 'session',
    'TIMEOUT': 86400,  # 24 hours
}

# ============================================================================
# CHANNELS CONFIGURATION (Redis DB 1)
# ============================================================================

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [f"{REDIS_URL}/{env.int('CHANNELS_REDIS_DB', default=1)}"],
            'capacity': 2000,  # Increased for production
            'expiry': 60,
            'group_expiry': 86400,
            'symmetric_encryption_keys': [SECRET_KEY],
        },
    },
}

# ============================================================================
# CELERY 5.5.3 CONFIGURATION (Redis DB 2)
# ============================================================================

# Broker settings
CELERY_BROKER_URL = f"{REDIS_URL}/{env.int('CELERY_REDIS_DB', default=2)}"
CELERY_RESULT_BACKEND = f"{REDIS_URL}/{env.int('CELERY_REDIS_DB', default=2)}"

# Celery 5.5.3 connection settings
CELERY_BROKER_CONNECTION_RETRY = True
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_CONNECTION_MAX_RETRIES = 10
CELERY_BROKER_POOL_LIMIT = 10

# Task serialization
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']

# Timezone settings
CELERY_TIMEZONE = 'Africa/Johannesburg'
CELERY_ENABLE_UTC = True

# Task execution settings
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = env.int('CELERY_WORKER_PREFETCH_MULTIPLIER', default=4)
CELERY_TASK_REJECT_ON_WORKER_LOST = True

# Celery 5.5.3 performance settings
CELERY_WORKER_DISABLE_RATE_LIMITS = env.bool('CELERY_WORKER_DISABLE_RATE_LIMITS', default=True)
CELERY_TASK_TIME_LIMIT = 300
CELERY_TASK_SOFT_TIME_LIMIT = 240

# Celery 5.5.3 monitoring
CELERY_SEND_TASK_EVENTS = env.bool('CELERY_SEND_TASK_EVENTS', default=True)
CELERY_TASK_SEND_SENT_EVENT = env.bool('CELERY_TASK_SEND_SENT_EVENT', default=True)
CELERY_RESULT_EXPIRES = env.int('CELERY_RESULT_EXPIRES', default=3600)

# Beat scheduler
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# ============================================================================
# INTERNATIONALIZATION (Django 5.2 enhancements)
# ============================================================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Johannesburg'
USE_I18N = True
USE_TZ = True

# Django 5.2 locale improvements
LANGUAGES = [
    ('en', 'English'),
    ('af', 'Afrikaans'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# ============================================================================
# STATIC FILES (Django 5.2 + WhiteNoise)
# ============================================================================

STATIC_URL = '/static/'
STATIC_ROOT = env('STATIC_ROOT', default='/var/www/naboomcommunity/collected-static/')
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# WhiteNoise configuration for Django 5.2
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = DEBUG

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = env('MEDIA_ROOT', default='/var/www/naboomcommunity/media/')

# ============================================================================
# TEMPLATES (Django 5.2 enhancements)
# ============================================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ============================================================================
# PASSWORD VALIDATION (Django 5.2)
# ============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,  # Increased security
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ============================================================================
# WAGTAIL 7.1 CONFIGURATION
# ============================================================================

WAGTAIL_SITE_NAME = env('WAGTAIL_SITE_NAME', default='Naboom Community')
WAGTAIL_ENABLE_ADMIN_DASHBOARD = env.bool('WAGTAIL_ENABLE_ADMIN_DASHBOARD', default=True)
WAGTAIL_ENABLE_LIVE_PREVIEW = env.bool('WAGTAIL_ENABLE_LIVE_PREVIEW', default=True)

# Wagtail 7.1 performance settings
WAGTAIL_CACHE = True
WAGTAIL_CACHE_TTL = env.int('WAGTAIL_CACHE_TTL', default=3600)

# Wagtail 7.1 search backend
WAGTAILSEARCH_BACKENDS = {
    'default': {
        'BACKEND': 'wagtail.search.backends.database',
        'AUTO_UPDATE': True,
    }
}

# ============================================================================
# REST FRAMEWORK CONFIGURATION
# ============================================================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}

# ============================================================================
# CORS CONFIGURATION
# ============================================================================

CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    'https://naboomneighbornet.net.za',
])
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = DEBUG  # Only in development

# ============================================================================
# SECURITY SETTINGS (Django 5.2 enhanced)
# ============================================================================

# Basic security
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=not DEBUG)
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True)
SECURE_HSTS_PRELOAD = env.bool('SECURE_HSTS_PRELOAD', default=True)

# Content security
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Django 5.2 new security settings
SECURE_REFERRER_POLICY = env('SECURE_REFERRER_POLICY', default='strict-origin-when-cross-origin')
SECURE_CROSS_ORIGIN_OPENER_POLICY = env('SECURE_CROSS_ORIGIN_OPENER_POLICY', default='same-origin')

# Cookie security
SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=not DEBUG)
CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=not DEBUG)
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_SAMESITE = 'Strict'

# ============================================================================
# LOGGING CONFIGURATION (Enhanced for Production)
# ============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'json': {
            '()': 'structlog.stdlib.ProcessorFormatter',
            'processor': 'structlog.dev.ConsoleRenderer',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/naboom/django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': env('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'naboomcommunity': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ============================================================================
# HEALTH CHECKS
# ============================================================================

HEALTH_CHECK = {
    'MEMORY_MIN': 100,  # in MB
    'DISK_USAGE_MAX': 90,  # in %
}

# ============================================================================
# DEFAULT AUTO FIELD (Django 5.2)
# ============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================================================
# MQTT CONFIGURATION (Panic System)
# ============================================================================

MQTT_HOST = env('MQTT_HOST', default='127.0.0.1')
MQTT_PORT = env.int('MQTT_PORT', default=1883)
MQTT_USER = env('MQTT_USER', default='app_subscriber')
MQTT_PASSWORD = env('MQTT_PASSWORD', default='')
MQTT_KEEPALIVE = 60
MQTT_QOS = 1

# ============================================================================
# WEB PUSH CONFIGURATION (CommunityHub)
# ============================================================================

VAPID_PUBLIC_KEY = env('VAPID_PUBLIC_KEY', default='')
VAPID_PRIVATE_KEY = env('VAPID_PRIVATE_KEY', default='')
VAPID_ADMIN_EMAIL = env('VAPID_ADMIN_EMAIL', default='admin@naboomneighbornet.net.za')

WEBPUSH_SETTINGS = {
    "VAPID_PUBLIC_KEY": VAPID_PUBLIC_KEY,
    "VAPID_PRIVATE_KEY": VAPID_PRIVATE_KEY,
    "VAPID_ADMIN_EMAIL": VAPID_ADMIN_EMAIL,
}

# ============================================================================
# MONITORING & APM
# ============================================================================

# Sentry (optional)
SENTRY_DSN = env('SENTRY_DSN', default='')
if SENTRY_DSN and not DEBUG:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(auto_enabling=True),
            CeleryIntegration(monitor_beat_tasks=True),
        ],
        traces_sample_rate=0.1,
        send_default_pii=True,
        environment=env('ENVIRONMENT', default='production'),
    )
```

This updated documentation reflects all your specific software versions with optimizations and features specific to each version. The configuration takes advantage of:

- **Python 3.12.3** performance improvements and new features
- **Django 5.2** async support and security enhancements  
- **Wagtail 7.1** improved admin interface and performance
- **PostgreSQL 16.10** advanced JSON features and performance improvements
- **Nginx 1.24.0** HTTP/3 support and enhanced WebSocket handling
- **Redis 8.2.2** memory optimizations and new security features
- **Celery 5.5.3** improved monitoring and performance features
- **Node.js 22.20.0** latest LTS optimizations for Vue.js builds

Would you like me to continue with the remaining sections covering Celery 5.5.3 specific configuration, Node.js 22.20.0 build setup, and version-specific troubleshooting?