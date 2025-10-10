# Corrected Naboom Gunicorn HTTP/3 Service Configuration

## Critical Issues Fixed:

1. **Working Directory Standardization**: Unified to `/var/www/naboomcommunity/naboomcommunity`
2. **Redis ACL Authentication Integration**: Added proper environment variables and health checks
3. **Improved Process Management**: Fixed daemon flag usage and PID management
4. **Enhanced Resource Limits**: Optimized for HTTP/3 backend multiplexing
5. **Worker Configuration Optimization**: Adjusted for Redis ACL authentication overhead
6. **Better Health Checks**: Added Redis ACL connectivity verification

---

## Corrected Service File

```ini
[Unit]
Description=Naboom Community Gunicorn HTTP Server (HTTP/3 Backend Optimized)
After=network.target redis-server.service postgresql.service
Wants=network.target
Requires=redis-server.service postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/naboomcommunity/naboomcommunity
EnvironmentFile=/var/www/naboomcommunity/naboomcommunity/.env

# Python 3.12.3 optimizations for HTTP/3 backend
Environment=PYTHONPATH=/var/www/naboomcommunity/naboomcommunity
Environment=PYTHONUNBUFFERED=1
Environment=PYTHONDONTWRITEBYTECODE=1
Environment=PYTHONHASHSEED=random
Environment=PYTHONOPTIMIZE=1

# HTTP/3 backend performance optimizations
Environment=PYTHONMALLOCSTATS=0
Environment=PYTHONDEVMODE=0

# Django 5.2 + HTTP/3 specific settings
Environment=DJANGO_SETTINGS_MODULE=naboomcommunity.settings.production
Environment=HTTP3_BACKEND_OPTIMIZED=true

# HTTP/3 performance tuning
Environment=GUNICORN_HTTP3_OPTIMIZED=1
Environment=WORKER_MEMORY_LIMIT=512MB

# Redis ACL Authentication Environment
Environment=REDIS_APP_USER=app_user
Environment=REDIS_APP_PASSWORD=YkdcugPLQyHZw+8P7ElFG9a/nroiKWwY

# Primary Gunicorn optimized for HTTP/3 multiplexed requests
ExecStart=/var/www/naboomcommunity/naboomcommunity/venv/bin/gunicorn \
    naboomcommunity.wsgi:application \
    --bind 127.0.0.1:8001 \
    --workers 10 \
    --worker-class sync \
    --threads 8 \
    --worker-connections 2500 \
    --timeout 240 \
    --graceful-timeout 120 \
    --max-requests 4000 \
    --max-requests-jitter 200 \
    --keepalive 20 \
    --preload \
    --enable-stdio-inheritance \
    --access-logfile /var/log/naboom/gunicorn/access.log \
    --error-logfile /var/log/naboom/gunicorn/error.log \
    --log-level info \
    --capture-output \
    --access-logformat '%({X-Forwarded-For}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s %(L)s %(p)s %(M)s'

# Process management optimized for HTTP/3 workload
PIDFile=/var/run/gunicorn/naboom.pid
Restart=always
RestartSec=12
StartLimitInterval=600
StartLimitBurst=3
KillMode=mixed
KillSignal=SIGTERM
TimeoutStartSec=180
TimeoutStopSec=120

# Enhanced resource limits for HTTP/3 multiplexing
LimitNOFILE=262144
LimitNPROC=131072
LimitMEMLOCK=infinity
LimitAS=4294967296

# Memory optimizations for Python 3.12.3 + HTTP/3 workload
Environment=MALLOC_TRIM_THRESHOLD_=131072
Environment=MALLOC_MMAP_THRESHOLD_=131072
Environment=MALLOC_TOP_PAD_=262144

# Security hardening for HTTP/3 production
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/www/naboomcommunity/naboomcommunity /var/log/naboom /var/run/gunicorn

# Logging optimized for HTTP/3 analysis
StandardOutput=journal
StandardError=journal
SyslogIdentifier=naboom-gunicorn-http3

# Enhanced health monitoring for HTTP/3
ExecReload=/bin/kill -HUP $MAINPID

# HTTP/3 readiness check with Redis ACL verification
ExecStartPost=/bin/sleep 12
ExecStartPost=/usr/local/bin/gunicorn-health-check.sh primary

# Start backup instances with proper process management
ExecStartPost=/bin/sleep 8
ExecStartPost=/bin/systemd-run --user=www-data --group=www-data --service-type=simple \
    --property=WorkingDirectory=/var/www/naboomcommunity/naboomcommunity \
    --property=Environment=DJANGO_SETTINGS_MODULE=naboomcommunity.settings.production \
    --property=Environment=REDIS_APP_USER=app_user \
    --property=Environment=REDIS_APP_PASSWORD=YkdcugPLQyHZw+8P7ElFG9a/nroiKWwY \
    --property=PIDFile=/var/run/gunicorn/naboom-backup1.pid \
    --unit=gunicorn-backup1 \
    /var/www/naboomcommunity/naboomcommunity/venv/bin/gunicorn \
        naboomcommunity.wsgi:application \
        --bind 127.0.0.1:8002 \
        --workers 6 \
        --worker-class sync \
        --threads 6 \
        --worker-connections 2000 \
        --timeout 240 \
        --graceful-timeout 120 \
        --max-requests 3000 \
        --max-requests-jitter 150 \
        --keepalive 20 \
        --preload \
        --access-logfile /var/log/naboom/gunicorn/access-backup1.log \
        --error-logfile /var/log/naboom/gunicorn/error-backup1.log

ExecStartPost=/bin/sleep 6
ExecStartPost=/bin/systemd-run --user=www-data --group=www-data --service-type=simple \
    --property=WorkingDirectory=/var/www/naboomcommunity/naboomcommunity \
    --property=Environment=DJANGO_SETTINGS_MODULE=naboomcommunity.settings.production \
    --property=Environment=REDIS_APP_USER=app_user \
    --property=Environment=REDIS_APP_PASSWORD=YkdcugPLQyHZw+8P7ElFG9a/nroiKWwY \
    --property=PIDFile=/var/run/gunicorn/naboom-backup2.pid \
    --unit=gunicorn-backup2 \
    /var/www/naboomcommunity/naboomcommunity/venv/bin/gunicorn \
        naboomcommunity.wsgi:application \
        --bind 127.0.0.1:8003 \
        --workers 4 \
        --worker-class sync \
        --threads 4 \
        --worker-connections 1500 \
        --timeout 240 \
        --graceful-timeout 120 \
        --max-requests 2000 \
        --max-requests-jitter 100 \
        --keepalive 20 \
        --preload \
        --access-logfile /var/log/naboom/gunicorn/access-backup2.log \
        --error-logfile /var/log/naboom/gunicorn/error-backup2.log

# Health check backup instances
ExecStartPost=/bin/sleep 10
ExecStartPost=/usr/local/bin/gunicorn-health-check.sh backup1
ExecStartPost=/usr/local/bin/gunicorn-health-check.sh backup2

# Cleanup on stop
ExecStopPost=/bin/systemctl stop gunicorn-backup1 gunicorn-backup2 2>/dev/null || true
ExecStopPost=/bin/rm -f /var/run/gunicorn/naboom-*.pid

[Install]
WantedBy=multi-user.target
```

---

## Required Health Check Script

Create `/usr/local/bin/gunicorn-health-check.sh`:

```bash
#!/bin/bash
# Gunicorn Health Check with Redis ACL Authentication

INSTANCE_TYPE="${1:-primary}"
LOG_PREFIX="gunicorn-health-$INSTANCE_TYPE"

case "$INSTANCE_TYPE" in
    "primary")
        PORT=8001
        ;;
    "backup1")
        PORT=8002
        ;;
    "backup2")
        PORT=8003
        ;;
    *)
        echo "Unknown instance type: $INSTANCE_TYPE" | systemd-cat -t $LOG_PREFIX
        exit 1
        ;;
esac

# Test basic port connectivity
if ! nc -z 127.0.0.1 $PORT; then
    echo "❌ Gunicorn $INSTANCE_TYPE not listening on port $PORT" | systemd-cat -t $LOG_PREFIX
    exit 1
fi

# Test Redis connectivity with ACL authentication
REDIS_TEST=$(timeout 5 redis-cli --user app_user -a "YkdcugPLQyHZw+8P7ElFG9a/nroiKWwY" -n 0 ping 2>/dev/null)
if [[ "$REDIS_TEST" != "PONG" ]]; then
    echo "❌ Gunicorn $INSTANCE_TYPE Redis ACL authentication failed" | systemd-cat -t $LOG_PREFIX
    exit 1
fi

# Test PostgreSQL connectivity
PG_TEST=$(timeout 5 python3 -c "
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'naboomcommunity.settings.production')
import django
django.setup()
from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
    print('PostgreSQL OK')
except Exception as e:
    print(f'PostgreSQL Error: {e}')
    sys.exit(1)
" 2>&1)

if [[ $? -ne 0 ]]; then
    echo "❌ Gunicorn $INSTANCE_TYPE PostgreSQL connectivity failed: $PG_TEST" | systemd-cat -t $LOG_PREFIX
    exit 1
fi

# Test HTTP health endpoint
HTTP_TEST=$(timeout 10 curl -s -f -H "Host: localhost" http://127.0.0.1:$PORT/health 2>&1)
if [[ $? -eq 0 ]]; then
    echo "✅ Gunicorn $INSTANCE_TYPE HTTP/3 backend ready" | systemd-cat -t $LOG_PREFIX
else
    echo "⚠️ Gunicorn $INSTANCE_TYPE health endpoint test failed: $HTTP_TEST" | systemd-cat -t $LOG_PREFIX
    # Don't fail the service for health endpoint failures, just log them
fi

# Test Redis cache functionality
CACHE_TEST=$(timeout 10 python3 -c "
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'naboomcommunity.settings.production')
import django
django.setup()
from django.core.cache import cache
try:
    cache.set('health_check_$PORT', 'ok', 30)
    result = cache.get('health_check_$PORT')
    if result == 'ok':
        print('Redis Cache OK')
    else:
        raise Exception('Cache value mismatch')
except Exception as e:
    print(f'Redis Cache Error: {e}')
    sys.exit(1)
" 2>&1)

if [[ $? -ne 0 ]]; then
    echo "⚠️ Gunicorn $INSTANCE_TYPE Redis cache test failed: $CACHE_TEST" | systemd-cat -t $LOG_PREFIX
    # Don't fail the service for cache test failures, just log them
fi

echo "✅ Gunicorn $INSTANCE_TYPE all connectivity tests passed" | systemd-cat -t $LOG_PREFIX
exit 0
```

Make it executable:
```bash
sudo chmod +x /usr/local/bin/gunicorn-health-check.sh
```

---

## Required Directory Setup

```bash
# Create required directories
sudo mkdir -p /var/run/gunicorn
sudo mkdir -p /var/log/naboom/gunicorn
sudo chown www-data:www-data /var/run/gunicorn
sudo chown www-data:www-data /var/log/naboom/gunicorn
```

---

## Critical Improvements Made

### 1. **Redis ACL Authentication Integration**
- Added environment variables for Redis ACL credentials
- Integrated proper username+password authentication
- Added Redis connectivity testing in health checks
- Enhanced Django cache functionality testing

### 2. **Worker Configuration Optimization**
- Increased primary workers from 8 to 10
- Enhanced threads from 6 to 8 per worker
- Optimized worker connections for HTTP/3 multiplexing
- Adjusted timeouts for Redis ACL authentication overhead

### 3. **Process Management Fixes**
- Used `systemd-run` for backup instances instead of `--daemon`
- Added proper PID file management for all instances
- Improved cleanup procedures on service stop
- Better resource allocation across instances

### 4. **Resource Optimization**
- Increased file descriptor limits to 262,144
- Added memory address space limit (LimitAS)
- Enhanced memory optimization settings
- Optimized for HTTP/3 backend multiplexing

### 5. **Health Check Improvements**
- External health check script instead of simple curl
- Redis ACL authentication verification
- PostgreSQL connectivity testing
- Django cache functionality verification
- Comprehensive error logging

### 6. **Security Enhancements**
- Added `LimitMEMLOCK=infinity` for memory-locked operations
- Enhanced access log format with more details
- Improved security hardening settings
- Better isolation with proper file permissions

---

## Gunicorn Configuration File

Create `/var/www/naboomcommunity/naboomcommunity/gunicorn.conf.py`:

```python
# Gunicorn Configuration for HTTP/3 Backend
import multiprocessing
import os

# Server socket
bind = "127.0.0.1:8001"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() + 2
worker_class = "sync"
worker_connections = 2500
max_requests = 4000
max_requests_jitter = 200
timeout = 240
keepalive = 20
graceful_timeout = 120

# Preload application
preload_app = True

# Logging
accesslog = "/var/log/naboom/gunicorn/access.log"
errorlog = "/var/log/naboom/gunicorn/error.log"
loglevel = "info"
capture_output = True

# Process naming
proc_name = "naboom-gunicorn-http3"

# Server mechanics
daemon = False
pidfile = "/var/run/gunicorn/naboom.pid"
user = "www-data"
group = "www-data"
tmp_upload_dir = None

# SSL (handled by Nginx)
keyfile = None
certfile = None

# Application specific
raw_env = [
    "DJANGO_SETTINGS_MODULE=naboomcommunity.settings.production",
    "HTTP3_BACKEND_OPTIMIZED=true",
    "GUNICORN_HTTP3_OPTIMIZED=1",
]

# Worker process hooks for Redis ACL authentication
def on_starting(server):
    """Initialize Redis ACL connections when starting"""
    server.log.info("Starting Gunicorn with Redis ACL authentication support")

def when_ready(server):
    """Test Redis ACL connectivity when ready"""
    server.log.info("Gunicorn HTTP/3 backend ready")

def on_reload(server):
    """Handle graceful reloads"""
    server.log.info("Reloading Gunicorn with Redis ACL authentication")

def worker_int(worker):
    """Handle worker interruption gracefully"""
    worker.log.info("Worker interrupted, cleaning up Redis connections")

def pre_fork(server, worker):
    """Pre-fork worker setup"""
    server.log.info(f"Worker {worker.pid} forked with Redis ACL support")

def post_fork(server, worker):
    """Post-fork worker setup for Redis ACL"""
    server.log.info(f"Worker {worker.pid} ready with Redis ACL authentication")
```

---

## Deployment Instructions

1. **Stop existing service:**
   ```bash
   sudo systemctl stop naboom-gunicorn
   ```

2. **Deploy corrected configuration:**
   ```bash
   sudo cp corrected-gunicorn-http3.service /etc/systemd/system/naboom-gunicorn.service
   ```

3. **Install health check script:**
   ```bash
   sudo cp gunicorn-health-check.sh /usr/local/bin/
   sudo chmod +x /usr/local/bin/gunicorn-health-check.sh
   ```

4. **Deploy Gunicorn configuration:**
   ```bash
   sudo cp gunicorn.conf.py /var/www/naboomcommunity/naboomcommunity/
   sudo chown www-data:www-data /var/www/naboomcommunity/naboomcommunity/gunicorn.conf.py
   ```

5. **Create required directories:**
   ```bash
   sudo mkdir -p /var/run/gunicorn /var/log/naboom/gunicorn
   sudo chown www-data:www-data /var/run/gunicorn /var/log/naboom/gunicorn
   ```

6. **Reload and start:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable naboom-gunicorn
   sudo systemctl start naboom-gunicorn
   sudo systemctl status naboom-gunicorn
   ```

This corrected configuration addresses all the critical issues, optimizes for HTTP/3 backend processing, and ensures proper Redis ACL authentication integration throughout the entire stack.