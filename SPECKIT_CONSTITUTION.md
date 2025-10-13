# SPECKIT Constitution: Backend Development Principles
## Naboom Community Platform - Django/Wagtail CMS Architecture

**Version:** 1.0  
**Effective Date:** 2024-12-19  
**Platform:** Django 5.2 + Wagtail 7.1.1 + PostgreSQL 16 + Redis 7 + MinIO  
**Target:** South African Community Emergency Response Systems

---

## 1. ARCHITECTURAL FOUNDATION

### 1.1 Core Technology Stack
- **Framework:** Django 5.2 with Wagtail 7.1.1 CMS
- **Database:** PostgreSQL 16 with PostGIS for geospatial data
- **Cache Layer:** Redis 7 with multi-database architecture
- **Object Storage:** MinIO for media and static assets
- **Message Broker:** Redis for Celery task queue
- **Real-time Communication:** Django Channels with Redis backend
- **Authentication:** JWT with SimpleJWT
- **API Framework:** Django REST Framework with Spectacular OpenAPI

### 1.2 HTTP/3 Performance Optimization
All components MUST be optimized for HTTP/3 performance:
- Connection multiplexing and reuse
- Efficient compression (zlib level 6)
- Optimized caching strategies
- Reduced latency for rural connectivity

---

## 2. DATABASE INTEGRITY PRINCIPLES

### 2.1 PostgreSQL Configuration Standards
```python
# Required database settings for all environments
DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "CONN_MAX_AGE": 600,  # 10 minutes for HTTP/3 connection reuse
        "CONN_HEALTH_CHECKS": True,
        "ATOMIC_REQUESTS": False,  # Better for HTTP/3 concurrency
        "OPTIONS": {
            "sslmode": "prefer",
            "connect_timeout": 10,
            "application_name": "naboom_http3",
            "keepalives_idle": "600",
            "keepalives_interval": "30",
            "keepalives_count": "3",
        }
    }
}
```

### 2.2 Database Migration Governance
- **Zero-downtime migrations:** All migrations MUST be backward compatible
- **Data integrity checks:** Pre and post-migration validation required
- **Rollback procedures:** Every migration MUST have a rollback plan
- **Performance impact:** Migrations affecting >1M records require approval
- **Testing:** All migrations MUST be tested in staging environment

### 2.3 Geospatial Data Standards
- Use PostGIS for all location-based data
- Implement proper spatial indexing
- Validate coordinate systems (WGS84 for GPS, local projections for mapping)
- Maintain data accuracy for emergency response scenarios

---

## 3. REST API CONSISTENCY STANDARDS

### 3.1 API Versioning Protocol
```python
# URL Pattern: /api/v{version}/{endpoint}/
# Example: /api/v1/community/posts/
# Example: /api/v2/emergency/incidents/

# Version deprecation timeline:
# - v1: Current stable (6 months support after v2 release)
# - v2: Latest stable (18 months support)
# - v3: Development (no production support)
```

### 3.2 Response Format Standards
```json
{
    "status": "success|error|warning",
    "code": 200,
    "message": "Human readable message",
    "data": {
        // Actual response data
    },
    "meta": {
        "pagination": {
            "page": 1,
            "per_page": 20,
            "total": 150,
            "pages": 8
        },
        "timestamp": "2024-12-19T10:30:00Z",
        "version": "v1"
    }
}
```

### 3.3 Error Handling Standards
```json
{
    "status": "error",
    "code": 400,
    "message": "Validation failed",
    "errors": [
        {
            "field": "email",
            "code": "invalid",
            "message": "Enter a valid email address"
        }
    ],
    "meta": {
        "timestamp": "2024-12-19T10:30:00Z",
        "request_id": "req_123456789"
    }
}
```

### 3.4 Rate Limiting Configuration
```python
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_RATES": {
        "community_post_burst": "30/min",
        "community_alert": "2/30min",
        "api_general": "1000/hour",
        "panic_incident": "10/min",
        "emergency_broadcast": "5/min",  # Critical for emergency response
    }
}
```

---

## 4. EMERGENCY RESPONSE SYSTEM RELIABILITY

### 4.1 Critical System Requirements
- **Uptime:** 99.9% availability (8.76 hours downtime/year maximum)
- **Response Time:** <200ms for emergency endpoints
- **Data Persistence:** All emergency data MUST be immediately persisted
- **Backup Strategy:** Real-time replication with 15-minute RPO

### 4.2 Emergency Data Handling
```python
# Emergency data models MUST include:
class EmergencyIncident(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    priority = models.CharField(max_length=20, choices=EMERGENCY_PRIORITIES)
    status = models.CharField(max_length=20, choices=INCIDENT_STATUSES)
    location = models.PointField(srid=4326)  # GPS coordinates
    verified = models.BooleanField(default=False)
    escalation_level = models.IntegerField(default=0)
    
    class Meta:
        indexes = [
            models.Index(fields=['priority', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['location']),  # Spatial index
        ]
```

### 4.3 Real-time Communication Standards
- WebSocket connections for emergency broadcasts
- MQTT integration for IoT emergency devices
- Push notification fallback for offline users
- Message queuing with Redis for guaranteed delivery

---

## 5. GDPR COMPLIANCE FOR COMMUNITY DATA

### 5.1 Data Classification
- **Personal Data:** Names, emails, phone numbers, addresses
- **Sensitive Data:** Emergency contacts, medical information, location history
- **Community Data:** Posts, comments, community membership
- **System Data:** Logs, analytics, performance metrics

### 5.2 Data Processing Principles
```python
# All data models MUST include GDPR compliance fields
class BaseCommunityModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    data_retention_until = models.DateTimeField(null=True, blank=True)
    gdpr_consent_given = models.BooleanField(default=False)
    gdpr_consent_date = models.DateTimeField(null=True, blank=True)
    data_processing_purpose = models.TextField()
    
    class Meta:
        abstract = True
```

### 5.3 Data Retention Policies
- **Personal Data:** 7 years after last activity
- **Emergency Data:** 10 years (legal requirement)
- **Community Posts:** 5 years after deletion request
- **System Logs:** 1 year (anonymized after 6 months)

### 5.4 User Rights Implementation
- **Right to Access:** API endpoint for data export
- **Right to Rectification:** User profile editing capabilities
- **Right to Erasure:** Secure data deletion with audit trail
- **Right to Portability:** JSON export of user data

---

## 6. SCALABLE ARCHITECTURE FOR SOUTH AFRICAN COMMUNITIES

### 6.1 Rural Connectivity Optimization
```python
# Optimized for low-bandwidth scenarios
CACHE_MIDDLEWARE_SECONDS = 300  # 5 minutes
WAGTAILIMAGES_JPEG_QUALITY = 85
WAGTAILIMAGES_WEBP_QUALITY = 85
WAGTAILIMAGES_FORMAT_CONVERSIONS = {
    'bmp': 'jpeg',
    'webp': 'webp',
    'png': 'webp',  # Convert PNG to WebP for efficiency
}
```

### 6.2 Multi-Community Architecture
- **Community Isolation:** Each community has isolated data namespace
- **Cross-Community Communication:** Controlled via API permissions
- **Resource Sharing:** Emergency resources can be shared between communities
- **Scalability:** Horizontal scaling via Redis clustering

### 6.3 Offline-First Design
- **Progressive Web App:** Service workers for offline functionality
- **Data Synchronization:** Conflict resolution for offline edits
- **Caching Strategy:** Aggressive caching for offline access
- **Queue Management:** Background sync when connectivity restored

---

## 7. REDIS CACHING STRATEGIES

### 7.1 Multi-Database Architecture
```python
CACHES = {
    'default': {
        'LOCATION': 'redis://user:pass@127.0.0.1:6379/0',  # Django Cache
        'TIMEOUT': 300,
    },
    'sessions': {
        'LOCATION': 'redis://user:pass@127.0.0.1:6379/3',  # Django Sessions
        'TIMEOUT': 86400,
    },
    'realtime': {
        'LOCATION': 'redis://user:pass@127.0.0.1:6379/4',  # Real-time streams
        'TIMEOUT': 60,
    },
    'api_responses': {
        'LOCATION': 'redis://user:pass@127.0.0.1:6379/5',  # API Response Cache
        'TIMEOUT': 1800,
    },
    'renditions': {
        'LOCATION': 'redis://user:pass@127.0.0.1:6379/6',  # Wagtail Image Renditions
        'TIMEOUT': 86400,
    },
}
```

### 7.2 Cache Invalidation Strategy
- **Time-based:** TTL for non-critical data
- **Event-based:** Invalidation on data updates
- **Version-based:** Cache keys include data version
- **Pattern-based:** Wildcard invalidation for related data

### 7.3 Performance Optimization
- **Compression:** zlib compression for all cached data
- **Connection Pooling:** 500 max connections for default cache
- **Serialization:** JSON for simple data, Pickle for complex objects
- **Health Checks:** 30-second health check intervals

---

## 8. MINIO OBJECT STORAGE INTEGRATION

### 8.1 Storage Configuration
```python
# Custom storage backend for MinIO
class MediaStorage(S3Boto3Storage):
    bucket_name = 'naboom-media'
    custom_domain = 's3.naboomneighbornet.net.za'
    file_overwrite = False
    default_acl = 'private'
    
    def get_object_parameters(self, name):
        params = super().get_object_parameters(name)
        params['ContentType'] = self._get_content_type(name)
        return params
```

### 8.2 File Organization Standards
```
/media/
├── avatars/
│   ├── {user_id}/
│   └── thumbnails/
├── community/
│   ├── {community_id}/
│   └── posts/
├── emergency/
│   ├── incidents/
│   └── evidence/
└── static/
    ├── css/
    ├── js/
    └── images/
```

### 8.3 Security and Access Control
- **Private by default:** All uploads are private unless explicitly public
- **Signed URLs:** Time-limited access for sensitive files
- **Virus Scanning:** Integration with ClamAV for uploaded files
- **Backup Strategy:** Cross-region replication for critical files

---

## 9. WEBSOCKET REAL-TIME COMMUNICATION STANDARDS

### 9.1 Channel Layer Configuration
```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [{
                'address': ('127.0.0.1', 6379),
                'db': 1,  # DB 1: Channels Layer
                'username': 'websocket_user',
                'password': 'password',
            }],
            'capacity': 16000,  # High capacity for HTTP/3
            'expiry': 300,
            'group_expiry': 86400,
            'symmetric_encryption_keys': [SECRET_KEY],
        },
    },
}
```

### 9.2 Real-time Event Standards
```python
# Event naming convention: {module}.{action}.{entity}
# Examples:
# - community.post.created
# - emergency.incident.updated
# - user.location.changed
# - system.maintenance.scheduled

class RealTimeEvent:
    def __init__(self, event_type, data, user_id=None, community_id=None):
        self.event_type = event_type
        self.data = data
        self.user_id = user_id
        self.community_id = community_id
        self.timestamp = timezone.now()
        self.id = str(uuid.uuid4())
```

### 9.3 Connection Management
- **Authentication:** JWT token validation for WebSocket connections
- **Rate Limiting:** 100 messages per minute per connection
- **Heartbeat:** 30-second ping/pong for connection health
- **Reconnection:** Exponential backoff for failed connections

---

## 10. SECURITY PROTOCOLS FOR EMERGENCY DATA

### 10.1 Data Encryption Standards
- **At Rest:** AES-256 encryption for sensitive data
- **In Transit:** TLS 1.3 for all communications
- **Database:** Transparent Data Encryption (TDE) for PostgreSQL
- **Backups:** Encrypted backups with separate key management

### 10.2 Access Control Matrix
```python
# Emergency data access levels
EMERGENCY_ACCESS_LEVELS = {
    'PUBLIC': 0,           # General community information
    'COMMUNITY': 1,        # Community members only
    'VERIFIED': 2,         # Verified community members
    'EMERGENCY': 3,        # Emergency responders
    'ADMIN': 4,            # System administrators
    'SUPERUSER': 5,        # Platform superusers
}
```

### 10.3 Audit Logging
```python
# All emergency data access MUST be logged
class EmergencyAuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=50)
    resource = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    success = models.BooleanField()
    details = models.JSONField()
```

---

## 11. PERFORMANCE REQUIREMENTS FOR RURAL CONNECTIVITY

### 11.1 Response Time Targets
- **API Endpoints:** <200ms for 95th percentile
- **Emergency Endpoints:** <100ms for 95th percentile
- **Static Assets:** <500ms for 95th percentile
- **Database Queries:** <50ms for 95th percentile

### 11.2 Bandwidth Optimization
- **Image Compression:** WebP format with 85% quality
- **API Compression:** Gzip compression for all responses
- **Caching:** Aggressive caching with 5-minute TTL
- **CDN Integration:** MinIO with CloudFront for static assets

### 11.3 Offline Capabilities
- **Service Workers:** Cache critical resources for offline use
- **Data Sync:** Background synchronization when online
- **Conflict Resolution:** Last-write-wins with user notification
- **Emergency Mode:** Critical functions available offline

---

## 12. DEVELOPMENT WORKFLOW STANDARDS

### 12.1 Code Quality Requirements
- **Type Hints:** All functions MUST have type hints
- **Documentation:** Docstrings for all public methods
- **Testing:** 90% code coverage minimum
- **Linting:** Black, isort, flake8 compliance required

### 12.2 Git Workflow
```bash
# Branch naming convention
feature/emergency-response-system
bugfix/websocket-connection-issue
hotfix/critical-security-patch
release/v2.1.0

# Commit message format
type(scope): description

# Examples:
feat(emergency): add panic button functionality
fix(api): resolve CORS issue with mobile app
docs(readme): update installation instructions
```

### 12.3 Deployment Standards
- **Staging Environment:** All changes tested in staging first
- **Database Migrations:** Zero-downtime migrations only
- **Feature Flags:** Use feature flags for gradual rollouts
- **Monitoring:** Comprehensive logging and alerting

---

## 13. MONITORING AND OBSERVABILITY

### 13.1 Logging Standards
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/http3.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'naboomcommunity': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### 13.2 Performance Monitoring
- **APM Integration:** New Relic or DataDog for application monitoring
- **Database Monitoring:** PostgreSQL query performance tracking
- **Cache Monitoring:** Redis performance and hit rates
- **Error Tracking:** Sentry for error monitoring and alerting

---

## 14. COMPLIANCE AND GOVERNANCE

### 14.1 Data Protection Compliance
- **POPIA Compliance:** South African Protection of Personal Information Act
- **GDPR Compliance:** European General Data Protection Regulation
- **Data Minimization:** Collect only necessary data
- **Purpose Limitation:** Use data only for stated purposes

### 14.2 Emergency Response Compliance
- **SAPS Integration:** South African Police Service API integration
- **Emergency Services:** Integration with local emergency services
- **Legal Requirements:** Compliance with South African emergency response laws
- **Audit Trail:** Complete audit trail for all emergency incidents

---

## 15. MAINTENANCE AND UPDATES

### 15.1 Security Updates
- **Critical Updates:** Applied within 24 hours
- **High Priority:** Applied within 7 days
- **Medium Priority:** Applied within 30 days
- **Low Priority:** Applied within 90 days

### 15.2 Feature Updates
- **Major Releases:** Quarterly with 30-day notice
- **Minor Releases:** Monthly with 7-day notice
- **Patch Releases:** As needed with 24-hour notice
- **Emergency Fixes:** Immediate deployment with post-deployment review

---

## 16. DOCUMENTATION REQUIREMENTS

### 16.1 API Documentation
- **OpenAPI Specification:** Complete API documentation
- **Code Examples:** Working examples for all endpoints
- **Error Codes:** Comprehensive error code documentation
- **Rate Limits:** Clear rate limiting documentation

### 16.2 System Documentation
- **Architecture Diagrams:** System architecture documentation
- **Deployment Guides:** Step-by-step deployment instructions
- **Troubleshooting:** Common issues and solutions
- **Performance Tuning:** Optimization guidelines

---

## CONCLUSION

This constitution serves as the foundational document for all backend development on the Naboom Community Platform. All developers, contributors, and maintainers MUST adhere to these principles to ensure:

1. **System Reliability:** Robust emergency response capabilities
2. **Data Security:** Protection of community and personal data
3. **Performance:** Optimal performance for rural South African communities
4. **Scalability:** Growth-ready architecture for expanding communities
5. **Compliance:** Full adherence to South African and international regulations

**Document Maintenance:** This constitution MUST be reviewed and updated quarterly or when significant architectural changes are made.

**Approval Authority:** Changes to this constitution require approval from the Technical Lead and Community Safety Officer.

---

*Last Updated: 2024-12-19*  
*Next Review: 2025-03-19*  
*Version: 1.0*
