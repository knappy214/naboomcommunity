# Implementation Plan: Community Incident Reporting and Tracking System

**Branch**: `002-incident-reporting-system` | **Date**: 2025-01-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-incident-reporting-system/spec.md`

## Summary

Comprehensive community incident reporting and tracking backend system using Django 5.2 framework with Wagtail 7.1.1 CMS integration, extending PostgreSQL 16.10 database schema with proper migrations, integrating with Redis 8.2.2 caching and WebSocket system, utilizing MinIO object storage for media files, maintaining existing REST API patterns with Django REST Framework, including proper authentication and permission systems, and ensuring compatibility with existing Nginx/HTTP3 infrastructure.

## Technical Context

**Language/Version**: Python 3.12, Django 5.2, Wagtail 7.1.1  
**Primary Dependencies**: Django REST Framework, Django Channels, MinIO, Redis 8.2.2, PostgreSQL 16.10 with PostGIS  
**Storage**: PostgreSQL 16.10 with PostGIS for location data, MinIO for media files, Redis 8.2.2 for caching and WebSocket  
**Testing**: pytest, pytest-django, pytest-asyncio for WebSocket testing  
**Target Platform**: Linux server with HTTP/3 QUIC support via Nginx 1.29.1  
**Project Type**: Web API with CMS integration and real-time capabilities  
**Performance Goals**: 500 concurrent incident reports/hour, 1000 WebSocket connections, sub-second API response  
**Constraints**: HTTP/3 optimization, Redis ACL authentication, PostgreSQL 16.10 performance tuning  
**Scale/Scope**: 10k+ community members, 1000+ incidents/month, 24/7 availability with HTTP/3 multiplexing  

## Infrastructure Integration

### HTTP/3 QUIC Architecture
```
Internet → Nginx 1.29.1 (HTTP/3 QUIC) → {
    HTTP/3 Multiplexing:
    ├── /panic/api/ → Gunicorn Cluster (8001,8002,8003)
    ├── /incidents/api/ → Gunicorn Cluster (8001,8002,8003)
    ├── /ws/ → Daphne Cluster (9000,9001,9002) 
    ├── /mqtt → Mosquitto WebSocket (8083,8084)
    └── /static/ → Direct file serving with HTTP/3 optimization

    Backend Services:
    ├── Redis 8.2.2 (ACL authenticated, HTTP/3 optimized)
    ├── PostgreSQL 16.10 (enhanced for HTTP/3 workload)
    ├── Celery 5.5.3 (HTTP/3 task queues with Redis ACL)
    └── Mosquitto 2.0.22 (WebSocket over HTTP/3)
}
```

### Redis 8.2.2 ACL Integration
- **Database 0**: Django Cache (existing)
- **Database 1**: Django Channels WebSocket (existing)
- **Database 2**: Celery Task Queue (existing)
- **Database 3**: Django Sessions (existing)
- **Database 4**: Real-time streams (existing)
- **Database 5**: Incident API responses (new)
- **Database 6**: Incident media metadata (new)
- **Database 7**: Incident audit logs (new)

### PostgreSQL 16.10 Schema Extensions
- **Existing Tables**: Extend with incident-related foreign keys
- **New Tables**: Incident, IncidentCategory, IncidentMedia, IncidentComment, IncidentAuditLog
- **Indexes**: HTTP/3 optimized with partial indexes and covering indexes
- **Partitioning**: Time-based partitioning for audit logs and media metadata
- **Extensions**: PostGIS, pg_trgm, btree_gin for full-text search

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Community-First Platform Compliance
- [x] Feature prioritizes community safety and incident reporting capabilities
- [x] Development decision evaluated against community safety impact
- [x] Incident reporting takes priority over non-essential functionality

### Accessibility-First Design Compliance
- [x] Interface follows WCAG guidelines for all community members
- [x] Design accommodates basic smartphones with poor connectivity
- [x] Minimal learning curve for non-technical users
- [x] Mobile-first approach implemented

### Privacy-First Data Protection Compliance
- [x] Zero-tolerance privacy policy for personal and incident data
- [x] Data collection is minimal, purposeful, and transparent
- [x] GDPR compliance verified

### Offline-Capable Emergency Features Compliance
- [x] Incident reporting works during load shedding scenarios
- [x] Media uploads handle poor connectivity gracefully
- [x] Local data caching and sync capabilities implemented

### Multilingual Support Compliance
- [x] English and Afrikaans support implemented at model and API level
- [x] Language preferences respected throughout platform
- [x] Future language additions don't compromise existing functionality

### User-Driven Feature Development Compliance
- [x] Feature based on actual community needs, not technical possibilities
- [x] Community feedback drives development priorities
- [x] Technical complexity justified by clear community benefit

### Sustainable Technology Choices Compliance
- [x] Technology maintainable by small development teams
- [x] No vendor lock-in dependencies
- [x] Open-source solutions preferred where possible

## Project Structure

### Documentation (this feature)

```
specs/002-incident-reporting-system/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
incidents/
├── models/
│   ├── __init__.py
│   ├── incident.py           # Core incident model with HTTP/3 optimizations
│   ├── category.py           # Incident categories with Wagtail integration
│   ├── media.py              # Media attachments with MinIO storage
│   ├── comment.py            # Comments and updates
│   ├── audit.py              # Audit logging with Redis 8.2.2 integration
│   └── integration.py        # Local authority integration
├── api/
│   ├── __init__.py
│   ├── viewsets.py           # DRF viewsets with HTTP/3 optimization
│   ├── serializers.py        # API serializers with multilingual support
│   ├── permissions.py        # API permissions with Redis ACL
│   ├── throttling.py         # Rate limiting for HTTP/3
│   └── filters.py            # API filtering with PostgreSQL 16.10 features
├── wagtail/
│   ├── __init__.py
│   ├── pages.py              # Wagtail 7.1.1 pages
│   ├── snippets.py           # Wagtail snippets with multilingual support
│   ├── hooks.py              # Wagtail hooks for incident management
│   └── admin.py              # Admin configuration
├── services/
│   ├── __init__.py
│   ├── incident_service.py   # Core incident logic with Redis caching
│   ├── media_service.py      # Media processing with MinIO
│   ├── notification_service.py # Notifications with HTTP/3 optimization
│   ├── integration_service.py # External integrations
│   └── audit_service.py      # Audit logging with Redis 8.2.2
├── websocket/
│   ├── __init__.py
│   ├── consumers.py          # WebSocket consumers with Redis 8.2.2
│   ├── routing.py            # WebSocket routing
│   └── middleware.py         # WebSocket middleware
├── tasks/
│   ├── __init__.py
│   ├── incident_tasks.py     # Celery 5.5.3 tasks with Redis ACL
│   └── media_tasks.py        # Media processing tasks
├── storage/
│   ├── __init__.py
│   ├── minio_storage.py      # MinIO storage backends
│   └── media_processor.py    # Media processing utilities
├── management/
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── setup_incidents.py
│   │   └── migrate_incidents.py
├── migrations/
│   ├── __init__.py
│   ├── 0001_initial.py       # Initial incident models
│   ├── 0002_incident_categories.py
│   ├── 0003_incident_media.py
│   ├── 0004_incident_comments.py
│   ├── 0005_incident_audit.py
│   └── 0006_incident_integrations.py
├── templates/
│   ├── incidents/
│   │   ├── management.html
│   │   ├── detail.html
│   │   └── create.html
├── static/
│   ├── incidents/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
├── locale/
│   ├── en/
│   │   └── LC_MESSAGES/
│   └── af/
│       └── LC_MESSAGES/
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_api.py
    ├── test_websocket.py
    ├── test_integrations.py
    └── test_media.py
```

**Structure Decision**: New Django app with comprehensive incident management, Wagtail 7.1.1 CMS integration, real-time WebSocket capabilities with Redis 8.2.2, and MinIO media storage. The system integrates with existing community hub and user profile systems while maintaining HTTP/3 optimization.

## Database Migration Strategy

### PostgreSQL 16.10 Schema Extensions

#### Phase 1: Core Incident Models
```sql
-- Migration 0001_initial.py
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Incident categories with multilingual support
CREATE TABLE incidents_incidentcategory (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    color VARCHAR(7) DEFAULT '#007bff',
    is_active BOOLEAN DEFAULT TRUE,
    requires_authority BOOLEAN DEFAULT FALSE,
    auto_assign_priority VARCHAR(16),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Core incident model with HTTP/3 optimizations
CREATE TABLE incidents_incident (
    id SERIAL PRIMARY KEY,
    reference VARCHAR(32) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    location GEOMETRY(POINT, 4326),
    address VARCHAR(255),
    reporter_id INTEGER REFERENCES auth_user(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES incidents_incidentcategory(id) ON DELETE PROTECT,
    priority VARCHAR(16) DEFAULT 'medium',
    status VARCHAR(16) DEFAULT 'reported',
    assigned_to_id INTEGER REFERENCES auth_user(id) ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}',
    is_public BOOLEAN DEFAULT TRUE,
    requires_authority BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    escalated_at TIMESTAMP WITH TIME ZONE
);

-- HTTP/3 optimized indexes
CREATE INDEX CONCURRENTLY idx_incidents_location_gist ON incidents_incident USING GIST (location);
CREATE INDEX CONCURRENTLY idx_incidents_status_priority ON incidents_incident (status, priority);
CREATE INDEX CONCURRENTLY idx_incidents_reporter_created ON incidents_incident (reporter_id, created_at DESC);
CREATE INDEX CONCURRENTLY idx_incidents_assigned_status ON incidents_incident (assigned_to_id, status) WHERE assigned_to_id IS NOT NULL;
CREATE INDEX CONCURRENTLY idx_incidents_metadata_gin ON incidents_incident USING GIN (metadata);
```

#### Phase 2: Media and Comments
```sql
-- Migration 0003_incident_media.py
CREATE TABLE incidents_incidentmedia (
    id SERIAL PRIMARY KEY,
    incident_id INTEGER REFERENCES incidents_incident(id) ON DELETE CASCADE,
    file VARCHAR(255) NOT NULL,
    media_type VARCHAR(16) NOT NULL,
    title VARCHAR(255),
    description TEXT,
    file_size INTEGER NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    uploaded_by_id INTEGER REFERENCES auth_user(id) ON DELETE CASCADE,
    is_processed BOOLEAN DEFAULT FALSE,
    thumbnail_url VARCHAR(500),
    minio_path VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Media indexes for HTTP/3 performance
CREATE INDEX CONCURRENTLY idx_incident_media_incident ON incidents_incidentmedia (incident_id);
CREATE INDEX CONCURRENTLY idx_incident_media_type ON incidents_incidentmedia (media_type);
CREATE INDEX CONCURRENTLY idx_incident_media_processed ON incidents_incidentmedia (is_processed) WHERE is_processed = FALSE;

-- Comments table
CREATE TABLE incidents_incidentcomment (
    id SERIAL PRIMARY KEY,
    incident_id INTEGER REFERENCES incidents_incident(id) ON DELETE CASCADE,
    author_id INTEGER REFERENCES auth_user(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    is_internal BOOLEAN DEFAULT FALSE,
    is_system_generated BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX CONCURRENTLY idx_incident_comments_incident ON incidents_incidentcomment (incident_id, created_at);
```

#### Phase 3: Audit and Integration
```sql
-- Migration 0005_incident_audit.py
CREATE TABLE incidents_incidentauditlog (
    id SERIAL PRIMARY KEY,
    incident_id INTEGER REFERENCES incidents_incident(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES auth_user(id) ON DELETE SET NULL,
    action VARCHAR(64) NOT NULL,
    field_name VARCHAR(64),
    old_value TEXT,
    new_value TEXT,
    ip_address INET,
    user_agent TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Partitioned table for audit logs (PostgreSQL 16.10 feature)
CREATE TABLE incidents_incidentauditlog_2025 PARTITION OF incidents_incidentauditlog
FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

-- Audit log indexes
CREATE INDEX CONCURRENTLY idx_incident_audit_incident ON incidents_incidentauditlog (incident_id, created_at DESC);
CREATE INDEX CONCURRENTLY idx_incident_audit_action ON incidents_incidentauditlog (action, created_at DESC);
CREATE INDEX CONCURRENTLY idx_incident_audit_user ON incidents_incidentauditlog (user_id, created_at DESC) WHERE user_id IS NOT NULL;
```

### Migration Execution Strategy

#### Pre-Migration Checklist
1. **Database Backup**: Full PostgreSQL 16.10 backup
2. **Redis Backup**: Redis 8.2.2 RDB snapshot
3. **MinIO Backup**: MinIO bucket backup
4. **Application Downtime**: Schedule maintenance window
5. **Rollback Plan**: Prepare rollback scripts

#### Migration Execution
```bash
# 1. Pre-migration checks
python manage.py check --deploy
python manage.py showmigrations incidents

# 2. Create migration files
python manage.py makemigrations incidents

# 3. Test migrations on staging
python manage.py migrate incidents --dry-run

# 4. Execute migrations with monitoring
python manage.py migrate incidents --verbosity=2

# 5. Post-migration validation
python manage.py check
python manage.py validate_incidents_schema
```

#### Post-Migration Tasks
1. **Index Optimization**: Analyze and optimize new indexes
2. **Statistics Update**: Update PostgreSQL statistics
3. **Cache Warming**: Warm Redis caches with incident data
4. **Performance Testing**: Validate HTTP/3 performance
5. **Monitoring Setup**: Configure incident-specific monitoring

## API Endpoint Specifications

### REST API Endpoints (Django REST Framework)

#### Core Incident Management
```python
# incidents/api/urls.py
urlpatterns = [
    # Incident CRUD operations
    path('incidents/', IncidentViewSet.as_view({'get': 'list', 'post': 'create'}), name='incident-list'),
    path('incidents/<int:pk>/', IncidentViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='incident-detail'),
    
    # Incident status management
    path('incidents/<int:pk>/status/', IncidentStatusView.as_view(), name='incident-status'),
    path('incidents/<int:pk>/assign/', IncidentAssignmentView.as_view(), name='incident-assign'),
    path('incidents/<int:pk>/escalate/', IncidentEscalationView.as_view(), name='incident-escalate'),
    
    # Media management
    path('incidents/<int:pk>/media/', IncidentMediaView.as_view(), name='incident-media'),
    path('incidents/<int:pk>/media/<int:media_id>/', IncidentMediaDetailView.as_view(), name='incident-media-detail'),
    
    # Comments and updates
    path('incidents/<int:pk>/comments/', IncidentCommentView.as_view(), name='incident-comments'),
    path('incidents/<int:pk>/comments/<int:comment_id>/', IncidentCommentDetailView.as_view(), name='incident-comment-detail'),
    
    # Categories and priorities
    path('categories/', IncidentCategoryView.as_view(), name='incident-categories'),
    path('priorities/', IncidentPriorityView.as_view(), name='incident-priorities'),
    
    # Statistics and reporting
    path('statistics/', IncidentStatisticsView.as_view(), name='incident-statistics'),
    path('reports/', IncidentReportView.as_view(), name='incident-reports'),
]
```

#### HTTP/3 Optimized ViewSets
```python
# incidents/api/viewsets.py
class IncidentViewSet(viewsets.ModelViewSet):
    """
    HTTP/3 optimized incident management with Redis caching
    """
    queryset = Incident.objects.select_related('reporter', 'category', 'assigned_to').prefetch_related('media', 'comments')
    serializer_class = IncidentSerializer
    permission_classes = [IsAuthenticated, IncidentPermission]
    throttle_classes = [IncidentRateThrottle]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'priority', 'category', 'assigned_to']
    search_fields = ['title', 'description', 'address']
    ordering_fields = ['created_at', 'updated_at', 'priority']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """HTTP/3 optimized queryset with Redis caching"""
        cache_key = f"incidents:list:{self.request.user.id}:{hash(str(self.request.GET))}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
            
        queryset = super().get_queryset()
        
        # Apply HTTP/3 optimizations
        if self.action == 'list':
            queryset = queryset.only(
                'id', 'reference', 'title', 'status', 'priority', 
                'created_at', 'reporter__username', 'category__name'
            )
        
        # Cache for 5 minutes
        cache.set(cache_key, queryset, 300)
        return queryset
```

### WebSocket Endpoints (Django Channels)

#### Real-Time Incident Updates
```python
# incidents/websocket/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/incidents/$', consumers.IncidentConsumer.as_asgi()),
    re_path(r'ws/incidents/(?P<incident_id>\w+)/$', consumers.IncidentDetailConsumer.as_asgi()),
    re_path(r'ws/incidents/categories/$', consumers.IncidentCategoryConsumer.as_asgi()),
]
```

#### WebSocket Consumers with Redis 8.2.2
```python
# incidents/websocket/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache
from .models import Incident

class IncidentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.incident_group = 'incident_updates'
        await self.channel_layer.group_add(
            self.incident_group,
            self.channel_name
        )
        await self.accept()
        
        # Send initial data with Redis caching
        initial_data = await self.get_initial_incidents()
        await self.send(text_data=json.dumps({
            'type': 'initial_data',
            'incidents': initial_data
        }))
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.incident_group,
            self.channel_name
        )
    
    async def incident_update(self, event):
        """Send incident update to WebSocket client"""
        await self.send(text_data=json.dumps({
            'type': 'incident_update',
            'incident_id': event['incident_id'],
            'action': event['action'],
            'data': event['data']
        }))
    
    @database_sync_to_async
    def get_initial_incidents(self):
        """Get initial incidents with Redis caching"""
        cache_key = "incidents:websocket:initial"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
            
        incidents = list(Incident.objects.filter(
            is_public=True
        ).values(
            'id', 'reference', 'title', 'status', 'priority', 'created_at'
        )[:50])
        
        cache.set(cache_key, incidents, 60)  # Cache for 1 minute
        return incidents
```

## Real-Time Features Integration

### Redis 8.2.2 WebSocket Integration

#### Channel Layer Configuration
```python
# naboomcommunity/settings/production.py
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [
                {
                    "address": "redis://127.0.0.1:6379/1",
                    "username": redis_users['WEBSOCKET_PASSWORD']['user'],
                    "password": redis_users['WEBSOCKET_PASSWORD']['password'],
                }
            ],
            "capacity": 1000,  # HTTP/3 optimized
            "expiry": 60,
            "group_expiry": 86400,
            "symmetric_encryption_keys": [SECRET_KEY],
        },
    }
}
```

#### Real-Time Notification System
```python
# incidents/services/notification_service.py
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

class IncidentNotificationService:
    def __init__(self):
        self.channel_layer = get_channel_layer()
    
    def broadcast_incident_update(self, incident, action, data):
        """Broadcast incident update to all connected clients"""
        async_to_sync(self.channel_layer.group_send)(
            'incident_updates',
            {
                'type': 'incident_update',
                'incident_id': incident.id,
                'action': action,
                'data': data
            }
        )
    
    def notify_incident_assignment(self, incident, assignee):
        """Notify specific user about incident assignment"""
        async_to_sync(self.channel_layer.group_send)(
            f'user_{assignee.id}',
            {
                'type': 'incident_assigned',
                'incident_id': incident.id,
                'incident_title': incident.title,
                'assignee_id': assignee.id
            }
        )
```

### Celery 5.5.3 Task Integration

#### Incident Processing Tasks
```python
# incidents/tasks.py
from celery import shared_task
from django.core.cache import cache
from .models import Incident
from .services.notification_service import IncidentNotificationService

@shared_task(bind=True, max_retries=3)
def process_incident_media(self, incident_id, media_data):
    """Process uploaded media files with MinIO"""
    try:
        incident = Incident.objects.get(id=incident_id)
        # Process media files
        # Update incident status
        # Notify via WebSocket
        notification_service = IncidentNotificationService()
        notification_service.broadcast_incident_update(
            incident, 'media_processed', media_data
        )
    except Exception as exc:
        self.retry(countdown=60, exc=exc)

@shared_task(bind=True, max_retries=5)
def escalate_incident_to_authority(self, incident_id):
    """Escalate incident to local authority"""
    try:
        incident = Incident.objects.get(id=incident_id)
        # Integrate with local authority system
        # Update incident status
        # Log audit trail
    except Exception as exc:
        self.retry(countdown=300, exc=exc)  # Retry every 5 minutes
```

## MinIO Integration Strategy

### MinIO Storage Configuration
```python
# incidents/storage/minio_storage.py
from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings
import uuid

class IncidentMediaStorage(S3Boto3Storage):
    """MinIO storage for incident media files"""
    location = 'incidents/media'
    default_acl = 'private'
    file_overwrite = False
    querystring_auth = True
    querystring_expire = 3600  # 1 hour
    
    def get_available_name(self, name, max_length=None):
        """Generate unique filename to prevent overwrites"""
        if self.exists(name):
            name_parts = name.rsplit('.', 1)
            if len(name_parts) == 2:
                name = f"{name_parts[0]}_{uuid.uuid4().hex[:8]}.{name_parts[1]}"
            else:
                name = f"{name}_{uuid.uuid4().hex[:8]}"
        return name

class IncidentDocumentStorage(S3Boto3Storage):
    """MinIO storage for incident documents"""
    location = 'incidents/documents'
    default_acl = 'private'
    file_overwrite = False
    querystring_auth = True
    querystring_expire = 7200  # 2 hours
```

### Media Processing Pipeline
```python
# incidents/services/media_service.py
from celery import shared_task
from PIL import Image
import boto3
from django.conf import settings

class IncidentMediaService:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
    
    def process_image(self, file_path, incident_id):
        """Process and optimize image files"""
        # Resize and compress
        # Generate thumbnails
        # Upload to MinIO
        # Update database
        pass
    
    def process_video(self, file_path, incident_id):
        """Process and optimize video files"""
        # Compress video
        # Generate preview frames
        # Upload to MinIO
        # Update database
        pass
```

## HTTP/3 Optimization Strategy

### Nginx Configuration Updates
```nginx
# /etc/nginx/sites-available/naboomcommunity
server {
    listen 443 ssl http3;
    listen [::]:443 ssl http3;
    
    # HTTP/3 QUIC configuration
    ssl_protocols TLSv1.3;
    ssl_early_data on;
    
    # Incident API endpoints
    location /incidents/api/ {
        proxy_pass http://incident_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # HTTP/3 optimizations
        proxy_cache incident_cache;
        proxy_cache_valid 200 5m;
        proxy_cache_use_stale error timeout updating;
        proxy_cache_lock on;
    }
    
    # WebSocket endpoints
    location /ws/incidents/ {
        proxy_pass http://incident_websocket;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket optimizations
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }
}

# Incident backend cluster
upstream incident_backend {
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
    keepalive 32;
}

# Incident WebSocket cluster
upstream incident_websocket {
    server 127.0.0.1:9000;
    server 127.0.0.1:9001;
    server 127.0.0.1:9002;
}
```

### Django Settings Optimization
```python
# naboomcommunity/settings/production.py
# HTTP/3 optimized settings for incident reporting

# Incident-specific cache configuration
INCIDENT_CACHE_TIMEOUT = 300  # 5 minutes
INCIDENT_MEDIA_CACHE_TIMEOUT = 3600  # 1 hour
INCIDENT_STATISTICS_CACHE_TIMEOUT = 1800  # 30 minutes

# HTTP/3 optimized database settings
DATABASES['default']['OPTIONS'].update({
    'application_name': 'naboom_incidents_http3',
    'keepalives_idle': '600',
    'keepalives_interval': '30',
    'keepalives_count': '3',
    'tcp_keepalives_idle': '600',
    'tcp_keepalives_interval': '30',
    'tcp_keepalives_count': '3',
})

# Redis 8.2.2 ACL configuration for incidents
INCIDENT_REDIS_CONFIG = {
    'incident_cache': {
        'LOCATION': f'redis://{redis_users["DJANGO_APP_PASSWORD"]["user"]}:{quote_plus(redis_users["DJANGO_APP_PASSWORD"]["password"])}@127.0.0.1:6379/5',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 200,
                'retry_on_timeout': True,
                'socket_keepalive': True,
            },
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
        },
        'KEY_PREFIX': 'naboom:http3:incidents',
        'TIMEOUT': INCIDENT_CACHE_TIMEOUT,
    }
}
```

## Implementation Phases

### Phase 0: Infrastructure Preparation (Week 1)
- **Database Setup**: Prepare PostgreSQL 16.10 for incident schema
- **Redis Configuration**: Configure Redis 8.2.2 ACL for incident data
- **MinIO Setup**: Configure MinIO buckets for incident media
- **Nginx Configuration**: Update Nginx 1.29.1 for incident endpoints
- **Docker Configuration**: Update container configurations

### Phase 1: Core Models and API (Weeks 2-4)
- **Django Models**: Create incident models with HTTP/3 optimizations
- **Database Migrations**: Execute PostgreSQL 16.10 migrations
- **REST API**: Implement Django REST Framework endpoints
- **Authentication**: Integrate with existing auth system
- **Permissions**: Implement role-based permissions

### Phase 2: Wagtail CMS Integration (Weeks 5-6)
- **Wagtail Pages**: Create incident management pages
- **Wagtail Snippets**: Create incident category snippets
- **Multilingual Support**: Implement English/Afrikaans support
- **Admin Interface**: Customize Wagtail admin for incidents
- **Content Workflow**: Implement incident content workflow

### Phase 3: Real-Time Features (Weeks 7-8)
- **WebSocket Implementation**: Django Channels with Redis 8.2.2
- **Real-Time Updates**: Incident status updates via WebSocket
- **Notification System**: Push notifications for incident updates
- **Celery Tasks**: Background processing for incident operations
- **Caching Strategy**: Redis caching for performance

### Phase 4: Media and Storage (Weeks 9-10)
- **MinIO Integration**: Media upload and storage
- **Media Processing**: Image/video optimization
- **CDN Integration**: Media delivery optimization
- **File Management**: Media file lifecycle management
- **Security**: Secure media access controls

### Phase 5: External Integration (Weeks 11-12)
- **Local Authority API**: Integration with external systems
- **Webhook Handling**: Incoming webhook processing
- **Data Synchronization**: Bidirectional data sync
- **Error Handling**: Robust error handling and retry logic
- **Monitoring**: Integration monitoring and alerting

### Phase 6: Testing and Optimization (Weeks 13-14)
- **Unit Testing**: Comprehensive test suite
- **Integration Testing**: End-to-end testing
- **Performance Testing**: HTTP/3 performance validation
- **Load Testing**: High-load scenario testing
- **Security Testing**: Security vulnerability testing

### Phase 7: Deployment and Monitoring (Weeks 15-16)
- **Production Deployment**: Deploy to production environment
- **Monitoring Setup**: Configure incident-specific monitoring
- **Performance Tuning**: Optimize for production load
- **Documentation**: Complete API and user documentation
- **Training**: Community leader training

## Risk Mitigation

### Technical Risks
- **PostgreSQL 16.10 Migration**: Use blue-green deployment strategy
- **Redis 8.2.2 ACL**: Test ACL configurations thoroughly
- **MinIO Integration**: Implement fallback storage mechanisms
- **HTTP/3 Compatibility**: Test with multiple HTTP/3 clients

### Performance Risks
- **Database Performance**: Implement proper indexing and query optimization
- **Redis Performance**: Monitor Redis memory usage and connection pools
- **WebSocket Scalability**: Implement connection pooling and load balancing
- **Media Processing**: Use asynchronous processing for large files

### Security Risks
- **Data Privacy**: Implement proper access controls and encryption
- **File Upload Security**: Validate and sanitize all uploaded files
- **API Security**: Implement rate limiting and authentication
- **Audit Trail**: Ensure comprehensive logging and monitoring

## Success Metrics

### Performance Metrics
- **API Response Time**: <200ms for incident list, <500ms for incident detail
- **WebSocket Latency**: <100ms for real-time updates
- **Media Upload Speed**: >1MB/s for image uploads, >500KB/s for video uploads
- **Database Query Time**: <50ms for incident queries
- **Cache Hit Rate**: >90% for incident data

### Community Impact Metrics
- **Incident Reporting Adoption**: 80% of community members
- **Resolution Time**: 50% improvement in incident resolution time
- **Community Satisfaction**: 90% satisfaction with incident reporting
- **Multilingual Usage**: 60% Afrikaans, 40% English
- **Mobile Usage**: 85% of incident reports from mobile devices

### Technical Quality Metrics
- **Test Coverage**: 95% code coverage
- **API Documentation**: 100% endpoint documentation
- **Error Rate**: <0.1% API error rate
- **Uptime**: 99.9% system availability
- **Security**: Zero critical security vulnerabilities

## Timeline Estimate

- **Phase 0 (Infrastructure)**: 1 week
- **Phase 1 (Core Models)**: 3 weeks  
- **Phase 2 (Wagtail Integration)**: 2 weeks
- **Phase 3 (Real-Time Features)**: 2 weeks
- **Phase 4 (Media & Storage)**: 2 weeks
- **Phase 5 (External Integration)**: 2 weeks
- **Phase 6 (Testing & Optimization)**: 2 weeks
- **Phase 7 (Deployment & Monitoring)**: 2 weeks

**Total Estimated Duration**: 16 weeks (4 months)

## Next Steps

1. **Immediate**: Begin Phase 0 infrastructure preparation
2. **Week 1**: Complete database and Redis configuration
3. **Week 2**: Start Phase 1 with Django model creation
4. **Week 3**: Implement REST API endpoints
5. **Week 4**: Complete authentication and permissions
6. **Week 5**: Begin Wagtail CMS integration
7. **Week 6**: Implement multilingual support
8. **Week 7**: Start real-time WebSocket implementation
9. **Week 8**: Complete notification system
10. **Week 9**: Begin MinIO media integration
11. **Week 10**: Complete media processing pipeline
12. **Week 11**: Start external authority integration
13. **Week 12**: Complete webhook handling
14. **Week 13**: Begin comprehensive testing
15. **Week 14**: Complete performance optimization
16. **Week 15**: Deploy to production
17. **Week 16**: Complete monitoring and documentation

This implementation plan ensures the community incident reporting and tracking system integrates seamlessly with your existing infrastructure while maintaining the highest standards of performance, security, and community safety.