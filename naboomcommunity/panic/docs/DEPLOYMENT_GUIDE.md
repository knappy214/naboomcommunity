# Emergency Response System Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the Emergency Response System in production environments. The system is designed for high availability, scalability, and security.

## Prerequisites

### System Requirements

- **Operating System**: Ubuntu 20.04 LTS or later
- **Python**: 3.9 or later
- **PostgreSQL**: 16.10 or later
- **Redis**: 8.2.2 or later
- **Nginx**: 1.18 or later
- **MinIO**: Latest stable version
- **Docker**: 20.10 or later (optional)

### Hardware Requirements

#### Minimum Configuration
- **CPU**: 4 cores
- **RAM**: 8GB
- **Storage**: 100GB SSD
- **Network**: 1Gbps

#### Recommended Configuration
- **CPU**: 8 cores
- **RAM**: 16GB
- **Storage**: 500GB SSD
- **Network**: 10Gbps

#### High Availability Configuration
- **CPU**: 16 cores
- **RAM**: 32GB
- **Storage**: 1TB SSD (RAID 10)
- **Network**: 10Gbps
- **Load Balancer**: HAProxy or Nginx Plus

## Installation

### 1. System Setup

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3.9 python3.9-dev python3-pip postgresql-16 redis-server nginx minio

# Install additional dependencies
sudo apt install -y build-essential libpq-dev libffi-dev libssl-dev
```

### 2. PostgreSQL Setup

```bash
# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql
```

```sql
-- Create database
CREATE DATABASE naboom_emergency;

-- Create user
CREATE USER emergency_user WITH PASSWORD 'secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE naboom_emergency TO emergency_user;

-- Enable extensions
\c naboom_emergency;
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Exit PostgreSQL
\q
```

### 3. Redis Setup

```bash
# Configure Redis
sudo nano /etc/redis/redis.conf
```

Add the following configuration:

```conf
# Emergency Response System Redis Configuration
port 6379
bind 127.0.0.1
protected-mode yes
requirepass emergency_redis_password

# Memory configuration
maxmemory 2gb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000

# Emergency databases
databases 16

# ACL configuration
aclfile /etc/redis/emergency_users.acl
```

```bash
# Create ACL file
sudo nano /etc/redis/emergency_users.acl
```

Add emergency users:

```conf
# Emergency Response System ACL Users
user emergency_user on >emergency_password +@all ~* &* -@dangerous
user location_user on >location_password +@read +@write +@stream +pubsub +select +ping ~location:* &* -@dangerous
user medical_user on >medical_password +@read +@write +@stream +pubsub +select +ping ~medical:* &* -@dangerous
user notification_user on >notification_password +@read +@write +@stream +pubsub +select +ping ~notification:* &* -@dangerous
```

```bash
# Restart Redis
sudo systemctl restart redis-server
```

### 4. MinIO Setup

```bash
# Create MinIO user
sudo useradd -r minio-user -s /sbin/nologin

# Create MinIO directories
sudo mkdir -p /opt/minio/{bin,data,config}
sudo mkdir -p /etc/minio

# Download and install MinIO
wget https://dl.min.io/server/minio/release/linux-amd64/minio
sudo mv minio /opt/minio/bin/
sudo chmod +x /opt/minio/bin/minio
sudo chown -R minio-user:minio-user /opt/minio

# Create MinIO service
sudo nano /etc/systemd/system/minio.service
```

```ini
[Unit]
Description=MinIO Object Storage
After=network.target

[Service]
Type=simple
User=minio-user
Group=minio-user
ExecStart=/opt/minio/bin/minio server /opt/minio/data --console-address ":9001"
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# Start MinIO service
sudo systemctl start minio
sudo systemctl enable minio

# Create emergency media bucket
mc alias set emergency http://localhost:9000 minioadmin minioadmin
mc mb emergency/naboom-emergency-media
mc policy set public emergency/naboom-emergency-media
```

### 5. Application Setup

```bash
# Create application directory
sudo mkdir -p /var/www/naboomcommunity
sudo chown -R www-data:www-data /var/www/naboomcommunity

# Clone repository
cd /var/www/naboomcommunity
git clone https://github.com/your-org/naboomcommunity.git .

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 6. Django Configuration

```bash
# Create production settings
cp naboomcommunity/settings/production.py.example naboomcommunity/settings/production.py
nano naboomcommunity/settings/production.py
```

Configure production settings:

```python
# Emergency Response System Production Settings
import os
from .base import *

DEBUG = False
ALLOWED_HOSTS = ['naboomneighbornet.net.za', 'www.naboomneighbornet.net.za']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'naboom_emergency',
        'USER': 'emergency_user',
        'PASSWORD': 'secure_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Redis Configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/0',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PASSWORD': 'emergency_redis_password',
        }
    },
    'emergency_db8': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/8',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PASSWORD': 'emergency_redis_password',
        }
    },
    'emergency_db9': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/9',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PASSWORD': 'emergency_redis_password',
        }
    },
    'emergency_db10': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/10',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PASSWORD': 'emergency_redis_password',
        }
    }
}

# MinIO Configuration
DEFAULT_FILE_STORAGE = 'panic.storage.emergency_storage.EmergencyMediaStorage'
AWS_ACCESS_KEY_ID = 'minioadmin'
AWS_SECRET_ACCESS_KEY = 'minioadmin'
AWS_STORAGE_BUCKET_NAME = 'naboom-emergency-media'
AWS_S3_ENDPOINT_URL = 'http://localhost:9000'
AWS_S3_USE_SSL = False

# Celery Configuration
CELERY_BROKER_URL = 'redis://:emergency_redis_password@localhost:6379/1'
CELERY_RESULT_BACKEND = 'redis://:emergency_redis_password@localhost:6379/2'

# Security
SECRET_KEY = 'your-secret-key-here'
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# External Service Configuration
EXTERNAL_EMERGENCY_SERVICES = {
    'police_10111': {
        'name': 'South African Police Service',
        'type': 'police',
        'protocol': 'rest_api',
        'endpoint': 'https://api.saps.gov.za/emergency',
        'api_key': 'your-saps-api-key',
        'timeout': 30,
        'retry_attempts': 3,
    },
    'ambulance_10177': {
        'name': 'Emergency Medical Services',
        'type': 'ambulance',
        'protocol': 'rest_api',
        'endpoint': 'https://api.ems.gov.za/emergency',
        'api_key': 'your-ems-api-key',
        'timeout': 30,
        'retry_attempts': 3,
    }
}

# Twilio Configuration
TWILIO_ACCOUNT_SID = 'your-twilio-account-sid'
TWILIO_AUTH_TOKEN = 'your-twilio-auth-token'
TWILIO_PHONE_NUMBER = 'your-twilio-phone-number'
```

### 7. Database Migration

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load initial data
python manage.py loaddata emergency_fixtures.json
```

### 8. Nginx Configuration

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/naboomneighbornet.net.za
```

```nginx
# Emergency Response System Nginx Configuration
server {
    listen 80;
    listen [::]:80;
    server_name naboomneighbornet.net.za www.naboomneighbornet.net.za;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name naboomneighbornet.net.za www.naboomneighbornet.net.za;

    # SSL Configuration
    ssl_certificate /etc/ssl/certs/naboomneighbornet.net.za.crt;
    ssl_certificate_key /etc/ssl/private/naboomneighbornet.net.za.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";

    # Emergency API endpoints
    location /api/enhanced/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Emergency-specific timeouts
        proxy_connect_timeout 5s;
        proxy_send_timeout 10s;
        proxy_read_timeout 30s;
        
        # Rate limiting
        limit_req zone=emergency_api burst=10 nodelay;
        
        # CORS headers
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "Authorization, Content-Type";
    }

    # WebSocket endpoints
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket timeouts
        proxy_connect_timeout 5s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Emergency media files
    location /emergency-media/ {
        proxy_pass http://127.0.0.1:9000/naboom-emergency-media/;
        proxy_set_header Host $host;
        
        # Cache settings
        expires 1h;
        add_header Cache-Control "public, no-transform";
        
        # Security
        add_header X-Content-Type-Options nosniff;
    }

    # Main application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Rate limiting zones
http {
    limit_req_zone $binary_remote_addr zone=emergency_api:10m rate=10r/m;
    limit_req_zone $binary_remote_addr zone=panic_button:10m rate=5r/m;
    limit_req_zone $binary_remote_addr zone=location_updates:10m rate=20r/m;
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/naboomneighbornet.net.za /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 9. Celery Configuration

```bash
# Create Celery service
sudo nano /etc/systemd/system/naboom-celery-emergency.service
```

```ini
[Unit]
Description=Naboom Emergency Celery Worker
After=network.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/var/www/naboomcommunity/naboomcommunity
Environment=DJANGO_SETTINGS_MODULE=naboomcommunity.settings.production
ExecStart=/var/www/naboomcommunity/venv/bin/celery -A naboomcommunity worker --loglevel=info --concurrency=4 --queues=emergency-high-priority,emergency-location,emergency-medical,emergency-notifications,emergency-sync
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# Start Celery service
sudo systemctl start naboom-celery-emergency
sudo systemctl enable naboom-celery-emergency
```

### 10. Gunicorn Configuration

```bash
# Create Gunicorn service
sudo nano /etc/systemd/system/naboom-gunicorn.service
```

```ini
[Unit]
Description=Naboom Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/naboomcommunity/naboomcommunity
Environment=DJANGO_SETTINGS_MODULE=naboomcommunity.settings.production
ExecStart=/var/www/naboomcommunity/venv/bin/gunicorn --access-logfile - --workers 4 --bind unix:/var/www/naboomcommunity/naboomcommunity.sock naboomcommunity.wsgi:application
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# Start Gunicorn service
sudo systemctl start naboom-gunicorn
sudo systemctl enable naboom-gunicorn
```

## Monitoring and Logging

### 1. Log Configuration

```bash
# Create log directories
sudo mkdir -p /var/log/naboom/emergency
sudo chown -R www-data:www-data /var/log/naboom

# Configure logrotate
sudo nano /etc/logrotate.d/naboom-emergency
```

```
/var/log/naboom/emergency/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload naboom-gunicorn
    endscript
}
```

### 2. Health Checks

```bash
# Create health check script
sudo nano /usr/local/bin/emergency-health-check.sh
```

```bash
#!/bin/bash

# Emergency Response System Health Check
LOG_FILE="/var/log/naboom/emergency/health-check.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# Check PostgreSQL
if ! pg_isready -h localhost -p 5432 -U emergency_user > /dev/null 2>&1; then
    echo "[$DATE] ERROR: PostgreSQL is not responding" >> $LOG_FILE
    exit 1
fi

# Check Redis
if ! redis-cli -a emergency_redis_password ping > /dev/null 2>&1; then
    echo "[$DATE] ERROR: Redis is not responding" >> $LOG_FILE
    exit 1
fi

# Check MinIO
if ! curl -s http://localhost:9000/minio/health/live > /dev/null 2>&1; then
    echo "[$DATE] ERROR: MinIO is not responding" >> $LOG_FILE
    exit 1
fi

# Check Django application
if ! curl -s http://localhost:8000/health/ > /dev/null 2>&1; then
    echo "[$DATE] ERROR: Django application is not responding" >> $LOG_FILE
    exit 1
fi

echo "[$DATE] INFO: All services are healthy" >> $LOG_FILE
exit 0
```

```bash
# Make executable
sudo chmod +x /usr/local/bin/emergency-health-check.sh

# Add to crontab
sudo crontab -e
```

Add:
```
# Emergency Response System Health Check
*/5 * * * * /usr/local/bin/emergency-health-check.sh
```

### 3. Performance Monitoring

```bash
# Install monitoring tools
sudo apt install -y htop iotop nethogs

# Create performance monitoring script
sudo nano /usr/local/bin/emergency-performance-monitor.sh
```

```bash
#!/bin/bash

# Emergency Response System Performance Monitor
LOG_FILE="/var/log/naboom/emergency/performance.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# CPU usage
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')

# Memory usage
MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.2f", $3/$2 * 100.0}')

# Disk usage
DISK_USAGE=$(df -h / | awk 'NR==2{print $5}' | sed 's/%//')

# Database connections
DB_CONNECTIONS=$(psql -h localhost -U emergency_user -d naboom_emergency -c "SELECT count(*) FROM pg_stat_activity;" | grep -o '[0-9]\+')

# Redis memory usage
REDIS_MEMORY=$(redis-cli -a emergency_redis_password info memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')

echo "[$DATE] CPU: ${CPU_USAGE}%, Memory: ${MEMORY_USAGE}%, Disk: ${DISK_USAGE}%, DB Connections: ${DB_CONNECTIONS}, Redis Memory: ${REDIS_MEMORY}" >> $LOG_FILE
```

## Security Hardening

### 1. Firewall Configuration

```bash
# Configure UFW firewall
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH
sudo ufw allow ssh

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow internal services
sudo ufw allow from 127.0.0.1 to any port 5432
sudo ufw allow from 127.0.0.1 to any port 6379
sudo ufw allow from 127.0.0.1 to any port 9000
```

### 2. SSL Certificate

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d naboomneighbornet.net.za -d www.naboomneighbornet.net.za

# Auto-renewal
sudo crontab -e
```

Add:
```
# SSL Certificate Auto-renewal
0 12 * * * /usr/bin/certbot renew --quiet
```

### 3. Database Security

```bash
# Configure PostgreSQL security
sudo nano /etc/postgresql/16/main/postgresql.conf
```

```conf
# Security settings
ssl = on
ssl_cert_file = '/etc/ssl/certs/server.crt'
ssl_key_file = '/etc/ssl/private/server.key'
password_encryption = scram-sha-256
```

```bash
# Configure pg_hba.conf
sudo nano /etc/postgresql/16/main/pg_hba.conf
```

```
# Emergency Response System Database Access
local   naboom_emergency    emergency_user    scram-sha-256
host    naboom_emergency    emergency_user    127.0.0.1/32    scram-sha-256
host    naboom_emergency    emergency_user    ::1/128         scram-sha-256
```

## Backup and Recovery

### 1. Database Backup

```bash
# Create backup script
sudo nano /usr/local/bin/emergency-db-backup.sh
```

```bash
#!/bin/bash

# Emergency Response System Database Backup
BACKUP_DIR="/var/backups/naboom/emergency"
DATE=$(date '+%Y-%m-%d_%H-%M-%S')
BACKUP_FILE="emergency_db_${DATE}.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create database backup
pg_dump -h localhost -U emergency_user -d naboom_emergency > $BACKUP_DIR/$BACKUP_FILE

# Compress backup
gzip $BACKUP_DIR/$BACKUP_FILE

# Remove backups older than 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Database backup completed: $BACKUP_FILE.gz"
```

```bash
# Make executable
sudo chmod +x /usr/local/bin/emergency-db-backup.sh

# Add to crontab
sudo crontab -e
```

Add:
```
# Emergency Response System Database Backup
0 2 * * * /usr/local/bin/emergency-db-backup.sh
```

### 2. Application Backup

```bash
# Create application backup script
sudo nano /usr/local/bin/emergency-app-backup.sh
```

```bash
#!/bin/bash

# Emergency Response System Application Backup
BACKUP_DIR="/var/backups/naboom/emergency"
DATE=$(date '+%Y-%m-%d_%H-%M-%S')
BACKUP_FILE="emergency_app_${DATE}.tar.gz"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create application backup
tar -czf $BACKUP_DIR/$BACKUP_FILE -C /var/www/naboomcommunity .

# Remove backups older than 30 days
find $BACKUP_DIR -name "emergency_app_*.tar.gz" -mtime +30 -delete

echo "Application backup completed: $BACKUP_FILE"
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Check PostgreSQL status
   sudo systemctl status postgresql
   
   # Check database connectivity
   psql -h localhost -U emergency_user -d naboom_emergency
   ```

2. **Redis Connection Errors**
   ```bash
   # Check Redis status
   sudo systemctl status redis-server
   
   # Test Redis connection
   redis-cli -a emergency_redis_password ping
   ```

3. **Celery Worker Issues**
   ```bash
   # Check Celery status
   sudo systemctl status naboom-celery-emergency
   
   # Check Celery logs
   sudo journalctl -u naboom-celery-emergency -f
   ```

4. **Nginx Configuration Issues**
   ```bash
   # Test Nginx configuration
   sudo nginx -t
   
   # Check Nginx status
   sudo systemctl status nginx
   ```

### Log Analysis

```bash
# View application logs
tail -f /var/log/naboom/emergency/application.log

# View error logs
tail -f /var/log/nginx/error.log

# View system logs
sudo journalctl -f
```

## Performance Optimization

### 1. Database Optimization

```sql
-- Create indexes for emergency tables
CREATE INDEX CONCURRENTLY idx_emergency_location_user_created 
ON emergency_locations (user_id, created_at);

CREATE INDEX CONCURRENTLY idx_emergency_medical_user 
ON emergency_medical (user_id);

CREATE INDEX CONCURRENTLY idx_emergency_audit_user_created 
ON emergency_audit_logs (user_id, created_at);

-- Analyze tables
ANALYZE emergency_locations;
ANALYZE emergency_medical;
ANALYZE emergency_audit_logs;
```

### 2. Redis Optimization

```bash
# Configure Redis for performance
sudo nano /etc/redis/redis.conf
```

```conf
# Performance settings
tcp-keepalive 60
timeout 0
tcp-backlog 511
maxmemory-policy allkeys-lru
```

### 3. Application Optimization

```python
# Django settings optimization
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/0',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PASSWORD': 'emergency_redis_password',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            }
        }
    }
}

# Database connection pooling
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'naboom_emergency',
        'USER': 'emergency_user',
        'PASSWORD': 'secure_password',
        'HOST': 'localhost',
        'PORT': '5432',
        'OPTIONS': {
            'MAX_CONNS': 20,
            'CONN_MAX_AGE': 600,
        }
    }
}
```

## Maintenance

### 1. Regular Maintenance Tasks

```bash
# Create maintenance script
sudo nano /usr/local/bin/emergency-maintenance.sh
```

```bash
#!/bin/bash

# Emergency Response System Maintenance
LOG_FILE="/var/log/naboom/emergency/maintenance.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$DATE] Starting maintenance tasks" >> $LOG_FILE

# Update system packages
apt update && apt upgrade -y >> $LOG_FILE 2>&1

# Clean up old logs
find /var/log/naboom/emergency -name "*.log" -mtime +30 -delete >> $LOG_FILE 2>&1

# Optimize database
psql -h localhost -U emergency_user -d naboom_emergency -c "VACUUM ANALYZE;" >> $LOG_FILE 2>&1

# Clear old cache entries
redis-cli -a emergency_redis_password --scan --pattern "emergency:*" | head -1000 | xargs redis-cli -a emergency_redis_password del >> $LOG_FILE 2>&1

echo "[$DATE] Maintenance tasks completed" >> $LOG_FILE
```

### 2. Monitoring Alerts

```bash
# Create alert script
sudo nano /usr/local/bin/emergency-alerts.sh
```

```bash
#!/bin/bash

# Emergency Response System Alerts
ALERT_EMAIL="admin@naboomneighbornet.net.za"

# Check disk space
DISK_USAGE=$(df -h / | awk 'NR==2{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "Disk usage is ${DISK_USAGE}%" | mail -s "Emergency System Alert: High Disk Usage" $ALERT_EMAIL
fi

# Check memory usage
MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
if [ $MEMORY_USAGE -gt 90 ]; then
    echo "Memory usage is ${MEMORY_USAGE}%" | mail -s "Emergency System Alert: High Memory Usage" $ALERT_EMAIL
fi

# Check service status
if ! systemctl is-active --quiet naboom-gunicorn; then
    echo "Gunicorn service is not running" | mail -s "Emergency System Alert: Service Down" $ALERT_EMAIL
fi
```

## Conclusion

This deployment guide provides comprehensive instructions for setting up the Emergency Response System in production. Follow these steps carefully and ensure all security measures are in place before going live.

For additional support, contact the development team at dev@naboomneighbornet.net.za.
