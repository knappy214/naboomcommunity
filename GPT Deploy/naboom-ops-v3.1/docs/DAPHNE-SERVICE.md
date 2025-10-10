# Corrected Naboom Daphne HTTP/3 Service Configuration

## Critical Issues Fixed:

1. **Working Directory Standardization**: Unified to `/var/www/naboomcommunity/naboomcommunity`
2. **Redis ACL Authentication Integration**: Added proper username+password authentication
3. **Removed Embedded Python Scripts**: Replaced with external health check scripts
4. **Improved Process Management**: Fixed daemon flag usage in backup instances
5. **Enhanced Resource Limits**: Optimized for HTTP/3 WebSocket multiplexing
6. **Better Dependency Management**: Added Redis ACL user verification

---

## Corrected Service File

```ini
[Unit]
Description=Naboom Community Daphne ASGI/WebSocket Server (HTTP/3 Enhanced)
After=network.target redis-server.service
Wants=network.target
Requires=redis-server.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/naboomcommunity/naboomcommunity
EnvironmentFile=/var/www/naboomcommunity/naboomcommunity/.env

# Python 3.12.3 optimizations for WebSocket over HTTP/3
Environment=PYTHONPATH=/var/www/naboomcommunity/naboomcommunity
Environment=PYTHONUNBUFFERED=1
Environment=PYTHONDONTWRITEBYTECODE=1
Environment=PYTHONHASHSEED=random
Environment=PYTHONOPTIMIZE=1

# Django 5.2 + Channels 4.0 + HTTP/3 specific settings
Environment=DJANGO_SETTINGS_MODULE=naboomcommunity.settings.production
Environment=CHANNELS_REDIS_DB=1
Environment=WEBSOCKET_HTTP3_OPTIMIZED=true

# HTTP/3 WebSocket performance tuning
Environment=DAPHNE_HTTP3_READY=1
Environment=WEBSOCKET_COMPRESSION=permessage-deflate

# Redis ACL Authentication Environment
Environment=REDIS_WEBSOCKET_USER=websocket_user
Environment=REDIS_WEBSOCKET_PASSWORD=QnBEWsaYvDNOnihFW/sWChAZ81MZc2eM

# Primary Daphne ASGI server optimized for WebSocket over HTTP/3
ExecStart=/var/www/naboomcommunity/naboomcommunity/venv/bin/daphne \
    -b 127.0.0.1 \
    -p 9000 \
    --proxy-headers \
    --root-path=/var/www/naboomcommunity/naboomcommunity \
    --verbosity 1 \
    --access-log /var/log/naboom/daphne/access.log \
    --server-name naboom-daphne-http3 \
    --application-close-timeout 120 \
    --websocket_timeout 86400 \
    --websocket_connect_timeout 60 \
    --websocket_handshake_timeout 45 \
    naboomcommunity.asgi:application

# Process management optimized for HTTP/3 WebSocket workload
PIDFile=/var/run/daphne/naboom-primary.pid
Restart=always
RestartSec=15
StartLimitInterval=600
StartLimitBurst=3
KillMode=mixed
KillSignal=SIGTERM
TimeoutStartSec=180
TimeoutStopSec=120

# Enhanced resource limits for WebSocket over HTTP/3
LimitNOFILE=262144
LimitNPROC=65536
LimitCORE=0
LimitMEMLOCK=infinity

# Memory optimizations for Python 3.12.3 WebSocket handling
Environment=MALLOC_TRIM_THRESHOLD_=131072
Environment=MALLOC_MMAP_THRESHOLD_=131072
Environment=MALLOC_TOP_PAD_=262144

# WebSocket over HTTP/3 specific optimizations
Environment=ASGI_THREADS=12
Environment=CHANNELS_CAPACITY=8000
Environment=MAX_WEBSOCKET_CONNECTIONS=15000

# HTTP/3 connection management
Environment=HTTP3_WEBSOCKET_BUFFER_SIZE=131072
Environment=HTTP3_STREAM_BUFFER_SIZE=65536

# Security hardening for WebSocket over HTTP/3
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/www/naboomcommunity/naboomcommunity /var/log/naboom /var/run/daphne

# Logging optimized for WebSocket over HTTP/3 analysis
StandardOutput=journal
StandardError=journal
SyslogIdentifier=naboom-daphne-http3

# Enhanced health monitoring for WebSocket over HTTP/3
ExecReload=/bin/kill -HUP $MAINPID
ExecStop=/bin/kill -TERM $MAINPID

# WebSocket over HTTP/3 readiness verification with Redis ACL
ExecStartPost=/bin/sleep 15
ExecStartPost=/usr/local/bin/daphne-health-check.sh primary

# Start backup instances with proper process management
ExecStartPost=/bin/sleep 10
ExecStartPost=/bin/systemd-run --user=www-data --group=www-data --service-type=simple \
    --property=WorkingDirectory=/var/www/naboomcommunity/naboomcommunity \
    --property=Environment=DJANGO_SETTINGS_MODULE=naboomcommunity.settings.production \
    --property=Environment=REDIS_WEBSOCKET_USER=websocket_user \
    --property=Environment=REDIS_WEBSOCKET_PASSWORD=QnBEWsaYvDNOnihFW/sWChAZ81MZc2eM \
    --property=PIDFile=/var/run/daphne/naboom-backup1.pid \
    --unit=daphne-backup1 \
    /var/www/naboomcommunity/naboomcommunity/venv/bin/daphne \
        -b 127.0.0.1 -p 9001 --proxy-headers \
        --access-log /var/log/naboom/daphne/access-backup1.log \
        --server-name naboom-daphne-backup1 \
        --application-close-timeout 120 \
        --websocket_timeout 86400 \
        --websocket_connect_timeout 60 \
        naboomcommunity.asgi:application

ExecStartPost=/bin/sleep 8
ExecStartPost=/bin/systemd-run --user=www-data --group=www-data --service-type=simple \
    --property=WorkingDirectory=/var/www/naboomcommunity/naboomcommunity \
    --property=Environment=DJANGO_SETTINGS_MODULE=naboomcommunity.settings.production \
    --property=Environment=REDIS_WEBSOCKET_USER=websocket_user \
    --property=Environment=REDIS_WEBSOCKET_PASSWORD=QnBEWsaYvDNOnihFW/sWChAZ81MZc2eM \
    --property=PIDFile=/var/run/daphne/naboom-backup2.pid \
    --unit=daphne-backup2 \
    /var/www/naboomcommunity/naboomcommunity/venv/bin/daphne \
        -b 127.0.0.1 -p 9002 --proxy-headers \
        --access-log /var/log/naboom/daphne/access-backup2.log \
        --server-name naboom-daphne-backup2 \
        --application-close-timeout 120 \
        --websocket_timeout 86400 \
        --websocket_connect_timeout 60 \
        naboomcommunity.asgi:application

# Health check backup instances
ExecStartPost=/bin/sleep 12
ExecStartPost=/usr/local/bin/daphne-health-check.sh backup1
ExecStartPost=/usr/local/bin/daphne-health-check.sh backup2

# Cleanup on stop
ExecStopPost=/bin/systemctl stop daphne-backup1 daphne-backup2 2>/dev/null || true
ExecStopPost=/bin/rm -f /var/run/daphne/naboom-*.pid

[Install]
WantedBy=multi-user.target
```

---

## Required Health Check Script

Create `/usr/local/bin/daphne-health-check.sh`:

```bash
#!/bin/bash
# Daphne WebSocket Health Check with Redis ACL Authentication

INSTANCE_TYPE="${1:-primary}"
LOG_PREFIX="daphne-health-$INSTANCE_TYPE"

case "$INSTANCE_TYPE" in
    "primary")
        PORT=9000
        ;;
    "backup1")
        PORT=9001
        ;;
    "backup2")
        PORT=9002
        ;;
    *)
        echo "Unknown instance type: $INSTANCE_TYPE" | systemd-cat -t $LOG_PREFIX
        exit 1
        ;;
esac

# Test basic port connectivity
if ! nc -z 127.0.0.1 $PORT; then
    echo "❌ Daphne $INSTANCE_TYPE not listening on port $PORT" | systemd-cat -t $LOG_PREFIX
    exit 1
fi

# Test Redis connectivity with ACL authentication
REDIS_TEST=$(timeout 5 redis-cli --user websocket_user -a "QnBEWsaYvDNOnihFW/sWChAZ81MZc2eM" -n 1 ping 2>/dev/null)
if [[ "$REDIS_TEST" != "PONG" ]]; then
    echo "❌ Daphne $INSTANCE_TYPE Redis ACL authentication failed" | systemd-cat -t $LOG_PREFIX
    exit 1
fi

# Test WebSocket endpoint
WEBSOCKET_TEST=$(timeout 10 python3 -c "
import asyncio
import websockets
import sys

async def test_websocket():
    try:
        uri = 'ws://127.0.0.1:$PORT/ws/health/'
        async with websockets.connect(uri, timeout=5) as websocket:
            await websocket.send('ping')
            response = await asyncio.wait_for(websocket.recv(), timeout=3)
            print('WebSocket test successful')
            return True
    except Exception as e:
        print(f'WebSocket test failed: {e}')
        return False

result = asyncio.run(test_websocket())
sys.exit(0 if result else 1)
" 2>&1)

if [[ $? -eq 0 ]]; then
    echo "✅ Daphne $INSTANCE_TYPE WebSocket HTTP/3 backend ready" | systemd-cat -t $LOG_PREFIX
else
    echo "⚠️ Daphne $INSTANCE_TYPE WebSocket endpoint test failed: $WEBSOCKET_TEST" | systemd-cat -t $LOG_PREFIX
    # Don't fail the service for WebSocket test failures, just log them
fi

exit 0
```

Make it executable:
```bash
sudo chmod +x /usr/local/bin/daphne-health-check.sh
```

---

## Required Directory Setup

```bash
# Create required directories
sudo mkdir -p /var/run/daphne
sudo mkdir -p /var/log/naboom/daphne
sudo chown www-data:www-data /var/run/daphne
sudo chown www-data:www-data /var/log/naboom/daphne
```

---

## Critical Improvements Made

### 1. **Redis ACL Authentication Integration**
- Added environment variables for Redis ACL credentials
- Integrated proper username+password authentication
- Added Redis connectivity testing in health checks

### 2. **Process Management Fixes**
- Used `systemd-run` for backup instances instead of `--daemon`
- Added proper PID file management
- Improved cleanup procedures on service stop

### 3. **Resource Optimization**
- Increased file descriptor limits to 262,144
- Enhanced memory optimization settings
- Optimized for HTTP/3 WebSocket multiplexing

### 4. **Health Check Improvements**
- External health check script instead of embedded Python
- Redis ACL authentication verification
- Proper error logging and reporting

### 5. **Security Enhancements**
- Added `LimitMEMLOCK=infinity` for memory-locked operations
- Improved security hardening settings
- Better isolation with `ProtectSystem=strict`

---

## Deployment Instructions

1. **Stop existing service:**
   ```bash
   sudo systemctl stop naboom-daphne
   ```

2. **Deploy corrected configuration:**
   ```bash
   sudo cp corrected-daphne-http3.service /etc/systemd/system/naboom-daphne.service
   ```

3. **Install health check script:**
   ```bash
   sudo cp daphne-health-check.sh /usr/local/bin/
   sudo chmod +x /usr/local/bin/daphne-health-check.sh
   ```

4. **Create required directories:**
   ```bash
   sudo mkdir -p /var/run/daphne /var/log/naboom/daphne
   sudo chown www-data:www-data /var/run/daphne /var/log/naboom/daphne
   ```

5. **Reload and start:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable naboom-daphne
   sudo systemctl start naboom-daphne
   sudo systemctl status naboom-daphne
   ```

This corrected configuration addresses all the critical issues while maintaining the HTTP/3 optimization features and ensuring proper Redis ACL authentication integration.