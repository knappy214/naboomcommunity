# Feature Specification: Community Incident Reporting and Tracking System

**Feature Branch**: `002-incident-reporting-system`  
**Created**: 2025-01-27  
**Status**: Draft  
**Input**: User description: "Develop a comprehensive community incident reporting and tracking backend system using Django models and Wagtail CMS integration. The system should support incident categorization, priority assignment, photo/video upload via MinIO, status tracking workflows, automatic notification triggers, integration with local authority systems, and comprehensive audit trails. Include proper multilingual support (English/Afrikaans) at the model and API level, GDPR-compliant data handling, and real-time update capabilities through WebSocket connections."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Community Member Reports Incident (Priority: P1)

A community member witnesses a safety issue, infrastructure problem, or community concern and reports it through the mobile app or web interface. They can attach photos/videos, provide location details, select appropriate categories, and set priority levels. The system automatically notifies relevant community leaders and local authorities.

**Why this priority**: This is the core functionality that enables community members to report issues and ensures they are properly tracked and addressed.

**Independent Test**: Can be fully tested by creating an incident report with photos, verifying categorization, and confirming notifications are sent to appropriate stakeholders.

**Acceptance Scenarios**:

1. **Given** a community member is logged in, **When** they create an incident report with photos and location, **Then** the incident is saved with proper categorization and priority assignment
2. **Given** an incident is reported, **When** the system processes the report, **Then** appropriate community leaders and local authorities are automatically notified
3. **Given** a user reports an incident in Afrikaans, **When** the system processes the report, **Then** all notifications and communications are sent in Afrikaans
4. **Given** an incident is reported with photos, **When** the system saves the report, **Then** photos are uploaded to MinIO and properly linked to the incident

---

### User Story 2 - Community Leader Manages Incidents (Priority: P1)

Community leaders and moderators can view, categorize, prioritize, and track incident reports. They can assign incidents to specific responders, update status, add comments, and escalate to local authorities when necessary.

**Why this priority**: Community leaders need effective tools to manage and coordinate incident response to ensure community safety and proper issue resolution.

**Independent Test**: Can be fully tested by logging in as a community leader and performing incident management actions including status updates and assignments.

**Acceptance Scenarios**:

1. **Given** a community leader is logged in, **When** they view the incident dashboard, **Then** they see all incidents with proper filtering and categorization options
2. **Given** an incident needs attention, **When** a leader updates its status and assigns it to a responder, **Then** the assigned responder receives real-time notification
3. **Given** an incident requires escalation, **When** a leader escalates to local authorities, **Then** the appropriate external systems are notified with incident details
4. **Given** a leader adds comments to an incident, **When** they save the comments, **Then** all stakeholders receive real-time updates via WebSocket

---

### User Story 3 - Real-Time Status Updates (Priority: P1)

All stakeholders (reporters, community leaders, responders, local authorities) receive real-time updates about incident status changes, assignments, and resolution progress through WebSocket connections and push notifications.

**Why this priority**: Real-time communication is essential for effective incident coordination and keeping all parties informed of progress.

**Independent Test**: Can be fully tested by creating an incident and verifying that all connected clients receive real-time updates when the incident status changes.

**Acceptance Scenarios**:

1. **Given** an incident status is updated, **When** the change is saved, **Then** all connected stakeholders receive real-time WebSocket updates within 1 second
2. **Given** a responder is assigned to an incident, **When** the assignment is made, **Then** the responder receives immediate push notification
3. **Given** an incident is resolved, **When** the resolution is marked, **Then** the original reporter receives notification in their preferred language
4. **Given** multiple users are monitoring an incident, **When** updates occur, **Then** all users receive updates in their preferred language (English/Afrikaans)

---

### User Story 4 - Local Authority Integration (Priority: P2)

The system integrates with local authority systems to automatically forward appropriate incidents, receive status updates, and maintain synchronization between community and official incident tracking systems.

**Why this priority**: Integration with local authorities ensures proper escalation and coordination for incidents that require official response.

**Independent Test**: Can be fully tested by creating incidents that require local authority involvement and verifying proper integration and data synchronization.

**Acceptance Scenarios**:

1. **Given** an incident requires local authority involvement, **When** it is escalated, **Then** the incident data is automatically forwarded to the appropriate authority system
2. **Given** local authorities update incident status, **When** the update is received, **Then** the community system reflects the updated status in real-time
3. **Given** an incident is closed by local authorities, **When** the closure is received, **Then** all community stakeholders are notified of the resolution
4. **Given** local authority systems are unavailable, **When** incidents are escalated, **Then** the system queues the integration requests for retry

---

### User Story 5 - Comprehensive Audit Trail (Priority: P2)

All incident-related activities are logged with comprehensive audit trails including user actions, system changes, external integrations, and data access for compliance and accountability.

**Why this priority**: Audit trails are essential for compliance, accountability, and ensuring proper incident handling procedures are followed.

**Independent Test**: Can be fully tested by performing various incident management actions and verifying that all activities are properly logged with appropriate detail.

**Acceptance Scenarios**:

1. **Given** any incident management action is performed, **When** the action is completed, **Then** a detailed audit log entry is created with user, timestamp, and action details
2. **Given** external system integration occurs, **When** data is exchanged, **Then** the integration activity is logged with request/response details
3. **Given** incident data is accessed, **When** the access occurs, **Then** the access is logged with user identification and purpose
4. **Given** audit logs are queried, **When** a search is performed, **Then** results are returned with proper filtering and GDPR-compliant data handling

---

### User Story 6 - Mobile Photo/Video Upload (Priority: P2)

Community members can easily upload photos and videos as evidence for incident reports, with automatic optimization, compression, and secure storage in MinIO.

**Why this priority**: Visual evidence is crucial for incident assessment and resolution, and mobile uploads must work reliably on basic smartphones.

**Independent Test**: Can be fully tested by uploading various photo and video formats from mobile devices and verifying proper storage and retrieval.

**Acceptance Scenarios**:

1. **Given** a user selects photos/videos for an incident report, **When** they upload the media, **Then** files are automatically optimized and stored in MinIO
2. **Given** large video files are uploaded, **When** the upload occurs, **Then** files are compressed appropriately for mobile viewing
3. **Given** media files are uploaded, **When** they are stored, **Then** proper metadata and incident associations are maintained
4. **Given** poor connectivity exists, **When** media uploads are attempted, **Then** the system handles uploads gracefully with retry mechanisms

---

### Edge Cases

- What happens when MinIO storage is unavailable during media upload?
- How does the system handle duplicate incident reports for the same issue?
- What occurs when local authority systems are down or unreachable?
- How does the system handle incidents reported in languages other than English/Afrikaans?
- What happens when WebSocket connections drop during critical updates?
- How does the system handle incidents that span multiple categories or priorities?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support incident creation with photos, videos, location, and categorization
- **FR-002**: System MUST provide incident management dashboard for community leaders
- **FR-003**: System MUST support real-time status updates via WebSocket connections
- **FR-004**: System MUST integrate with local authority systems for incident escalation
- **FR-005**: System MUST maintain comprehensive audit trails for all incident activities

### Community Safety Requirements

- **CSR-001**: System MUST prioritize incident reporting and tracking for community safety
- **CSR-002**: Incident categorization MUST support safety, infrastructure, and community concerns
- **CSR-003**: System MUST support priority assignment (low, medium, high, critical)
- **CSR-004**: System MUST provide real-time notifications to appropriate stakeholders
- **CSR-005**: System MUST support incident escalation to local authorities

### Accessibility Requirements

- **AR-001**: Interface MUST comply with WCAG 2.1 AA guidelines
- **AR-002**: System MUST support mobile-first incident reporting
- **AR-003**: Design MUST accommodate elderly and disabled community members
- **AR-004**: Interface MUST have minimal learning curve for non-technical users
- **AR-005**: System MUST support voice-to-text for incident descriptions

### Multilingual Requirements

- **MLR-001**: System MUST support English and Afrikaans at model and API level
- **MLR-002**: Incident categories and priorities MUST be translatable
- **MLR-003**: All notifications MUST be sent in user's preferred language
- **MLR-004**: Wagtail CMS integration MUST support multilingual content
- **MLR-005**: API responses MUST include language-specific field values

### Privacy Requirements

- **PR-001**: System MUST implement GDPR-compliant data handling
- **PR-002**: Personal data in incidents MUST be properly protected
- **PR-003**: Media uploads MUST be stored securely with access controls
- **PR-004**: Users MUST have control over their data sharing preferences
- **PR-005**: System MUST support data anonymization for analytics

### Technical Requirements

- **TR-001**: System MUST use Django models with proper relationships
- **TR-002**: System MUST integrate with Wagtail CMS for content management
- **TR-003**: Media uploads MUST use MinIO for storage
- **TR-004**: System MUST support WebSocket connections for real-time updates
- **TR-005**: System MUST provide RESTful API endpoints for all functionality

### Integration Requirements

- **IR-001**: System MUST integrate with existing community hub models
- **IR-002**: System MUST support local authority system integration
- **IR-003**: System MUST integrate with notification systems (SMS, email, push)
- **IR-004**: System MUST support external webhook callbacks
- **IR-005**: System MUST integrate with existing user profile system

### Audit Requirements

- **AUR-001**: System MUST log all incident creation and modification activities
- **AUR-002**: System MUST log all user access to incident data
- **AUR-003**: System MUST log all external system integrations
- **AUR-004**: System MUST maintain immutable audit log entries
- **AUR-005**: System MUST support audit log querying and reporting

### Key Entities *(include if feature involves data)*

- **Incident**: Core incident model with categorization, priority, status, and metadata
- **IncidentCategory**: Translatable categories for incident classification
- **IncidentPriority**: Priority levels with multilingual support
- **IncidentStatus**: Status tracking with workflow management
- **IncidentMedia**: Photo/video attachments with MinIO storage integration
- **IncidentComment**: Comments and updates with user tracking
- **IncidentAssignment**: Assignment tracking for responders and authorities
- **IncidentAuditLog**: Comprehensive audit trail for all activities
- **LocalAuthorityIntegration**: External system integration configuration
- **IncidentNotification**: Notification tracking and delivery status

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Incident creation to notification delivery within 5 seconds
- **SC-002**: Real-time WebSocket updates delivered within 1 second for 95% of changes
- **SC-003**: Media upload success rate of 99% for photos and 95% for videos
- **SC-004**: Local authority integration response time under 10 seconds
- **SC-005**: Audit log completeness of 100% for all incident activities
- **SC-006**: Multilingual support accuracy of 100% for English and Afrikaans
- **SC-007**: Mobile incident reporting success rate of 95% on basic smartphones
- **SC-008**: Community leader incident management efficiency improvement of 50%
- **SC-009**: GDPR compliance verification for 100% of data handling
- **SC-010**: System availability of 99.5% during business hours

### Performance Metrics

- **PM-001**: Support 500 concurrent incident reports per hour
- **PM-002**: Process media uploads up to 50MB per file
- **PM-003**: Maintain sub-second response times for incident API endpoints
- **PM-004**: Support 1000 concurrent WebSocket connections
- **PM-005**: Handle 10,000 incident records with efficient querying

### User Experience Metrics

- **UX-001**: 90% of users can create incident reports successfully on first attempt
- **UX-002**: 95% of community leaders report satisfaction with management tools
- **UX-003**: 85% of users prefer the mobile interface over web interface
- **UX-004**: 90% of notifications are delivered in user's preferred language
- **UX-005**: 95% of media uploads complete successfully on first attempt

## Technical Architecture

### Django Models

#### Core Incident Model
```python
class Incident(TranslatableMixin, TimeStampedModel):
    """Core incident model with multilingual support."""
    
    class Status(models.TextChoices):
        REPORTED = "reported", _("Reported")
        ACKNOWLEDGED = "acknowledged", _("Acknowledged")
        IN_PROGRESS = "in_progress", _("In Progress")
        RESOLVED = "resolved", _("Resolved")
        CLOSED = "closed", _("Closed")
        ESCALATED = "escalated", _("Escalated")
    
    class Priority(models.TextChoices):
        LOW = "low", _("Low")
        MEDIUM = "medium", _("Medium")
        HIGH = "high", _("High")
        CRITICAL = "critical", _("Critical")
    
    # Core fields
    reference = models.CharField(max_length=32, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.PointField(geography=True, srid=4326)
    address = models.CharField(max_length=255, blank=True)
    
    # Relationships
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_incidents')
    category = models.ForeignKey('IncidentCategory', on_delete=models.PROTECT)
    priority = models.CharField(max_length=16, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.REPORTED)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_incidents')
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    is_public = models.BooleanField(default=True)
    requires_authority = models.BooleanField(default=False)
    
    # Timestamps
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    escalated_at = models.DateTimeField(null=True, blank=True)
```

#### Incident Category Model
```python
class IncidentCategory(TranslatableMixin, TimeStampedModel):
    """Translatable incident categories."""
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=7, default='#007bff')  # Hex color
    is_active = models.BooleanField(default=True)
    requires_authority = models.BooleanField(default=False)
    auto_assign_priority = models.CharField(max_length=16, choices=Incident.Priority.choices, blank=True)
    
    class Meta(TranslatableMixin.Meta):
        verbose_name = _("Incident Category")
        verbose_name_plural = _("Incident Categories")
```

#### Incident Media Model
```python
class IncidentMedia(TimeStampedModel):
    """Media attachments for incidents."""
    
    class MediaType(models.TextChoices):
        IMAGE = "image", _("Image")
        VIDEO = "video", _("Video")
        AUDIO = "audio", _("Audio")
        DOCUMENT = "document", _("Document")
    
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name='media')
    file = models.FileField(upload_to='incidents/media/')
    media_type = models.CharField(max_length=16, choices=MediaType.choices)
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    file_size = models.PositiveIntegerField()
    mime_type = models.CharField(max_length=100)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    is_processed = models.BooleanField(default=False)
    thumbnail_url = models.URLField(blank=True)
```

#### Incident Comment Model
```python
class IncidentComment(TimeStampedModel):
    """Comments and updates on incidents."""
    
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    is_internal = models.BooleanField(default=False)
    is_system_generated = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['created_at']
```

#### Incident Audit Log Model
```python
class IncidentAuditLog(TimeStampedModel):
    """Comprehensive audit trail for incidents."""
    
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name='audit_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=64)
    field_name = models.CharField(max_length=64, blank=True)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-created_at']
```

### Wagtail CMS Integration

#### Incident Management Pages
```python
class IncidentManagementPage(Page):
    """Wagtail page for incident management interface."""
    
    template = "incidents/incident_management.html"
    
    content_panels = Page.content_panels + [
        FieldPanel('description'),
    ]
    
    def get_context(self, request):
        context = super().get_context(request)
        context['incidents'] = Incident.objects.filter(is_public=True).order_by('-created_at')[:50]
        return context
```

#### Incident Category Snippets
```python
class IncidentCategorySnippet(TranslatableMixin, ClusterableModel):
    """Wagtail snippet for incident categories."""
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=7, default='#007bff')
    
    panels = [
        FieldPanel('name'),
        FieldPanel('description'),
        FieldPanel('icon'),
        FieldPanel('color'),
    ]
```

### API Endpoints

#### Incident Management API
- `GET /api/v2/incidents/` - List incidents with filtering and pagination
- `POST /api/v2/incidents/` - Create new incident report
- `GET /api/v2/incidents/{id}/` - Get incident details
- `PUT /api/v2/incidents/{id}/` - Update incident
- `PATCH /api/v2/incidents/{id}/status/` - Update incident status
- `POST /api/v2/incidents/{id}/assign/` - Assign incident to responder
- `POST /api/v2/incidents/{id}/escalate/` - Escalate to local authorities

#### Media Management API
- `POST /api/v2/incidents/{id}/media/` - Upload media files
- `GET /api/v2/incidents/{id}/media/` - List incident media
- `DELETE /api/v2/incidents/{id}/media/{media_id}/` - Delete media file

#### Real-Time Updates API
- `WS /ws/incidents/` - WebSocket connection for real-time updates
- `POST /api/v2/incidents/broadcast/` - Broadcast updates to connected clients

#### Local Authority Integration API
- `POST /api/v2/incidents/{id}/forward/` - Forward incident to local authority
- `GET /api/v2/incidents/{id}/authority-status/` - Get local authority status
- `POST /api/v2/incidents/authority-callback/` - Receive authority updates

### MinIO Integration

#### Media Storage Configuration
```python
class IncidentMediaStorage(S3Boto3Storage):
    """Custom storage for incident media files."""
    
    location = 'incidents/media'
    default_acl = 'private'
    file_overwrite = False
    querystring_auth = True
    querystring_expire = 3600  # 1 hour
    
    def get_available_name(self, name, max_length=None):
        """Generate unique filename to prevent overwrites."""
        if self.exists(name):
            name_parts = name.rsplit('.', 1)
            if len(name_parts) == 2:
                name = f"{name_parts[0]}_{uuid.uuid4().hex[:8]}.{name_parts[1]}"
            else:
                name = f"{name}_{uuid.uuid4().hex[:8]}"
        return name
```

#### Media Processing
```python
class MediaProcessor:
    """Process and optimize uploaded media files."""
    
    @staticmethod
    def process_image(file_path, incident_id):
        """Process and optimize image files."""
        # Resize, compress, generate thumbnails
        pass
    
    @staticmethod
    def process_video(file_path, incident_id):
        """Process and optimize video files."""
        # Compress, generate preview frames
        pass
```

### WebSocket Implementation

#### Real-Time Updates
```python
class IncidentConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time incident updates."""
    
    async def connect(self):
        self.incident_group = f"incident_updates"
        await self.channel_layer.group_add(
            self.incident_group,
            self.channel_name
        )
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.incident_group,
            self.channel_name
        )
    
    async def incident_update(self, event):
        """Send incident update to WebSocket client."""
        await self.send(text_data=json.dumps({
            'type': 'incident_update',
            'incident_id': event['incident_id'],
            'action': event['action'],
            'data': event['data']
        }))
```

### Local Authority Integration

#### Integration Service
```python
class LocalAuthorityIntegrationService:
    """Service for integrating with local authority systems."""
    
    def __init__(self, authority_config):
        self.config = authority_config
        self.client = self._create_client()
    
    def forward_incident(self, incident):
        """Forward incident to local authority system."""
        payload = self._prepare_incident_payload(incident)
        response = self.client.post('/api/incidents/', json=payload)
        return self._handle_response(response)
    
    def get_incident_status(self, external_id):
        """Get incident status from local authority."""
        response = self.client.get(f'/api/incidents/{external_id}/')
        return self._parse_status_response(response)
    
    def handle_authority_callback(self, data):
        """Handle callback from local authority system."""
        incident = Incident.objects.get(external_id=data['incident_id'])
        incident.status = data['status']
        incident.save()
        
        # Broadcast update to WebSocket clients
        self._broadcast_update(incident, 'status_changed')
```

### Multilingual Support

#### Translation Configuration
```python
# settings.py
LANGUAGES = [
    ('en', 'English'),
    ('af', 'Afrikaans'),
]

WAGTAIL_I18N_ENABLED = True
WAGTAIL_CONTENT_LANGUAGES = LANGUAGES

# Model translation
class IncidentTranslation(TranslatableMixin):
    title = models.CharField(max_length=255)
    description = models.TextField()
    
    class Meta(TranslatableMixin.Meta):
        pass
```

#### API Localization
```python
class LocalizedIncidentSerializer(serializers.ModelSerializer):
    """Serializer with automatic localization."""
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        language = self.context.get('language', 'en')
        
        # Get localized category name
        if hasattr(instance.category, 'get_translation'):
            category_translation = instance.category.get_translation(language)
            data['category_name'] = category_translation.name if category_translation else instance.category.name
        
        return data
```

### GDPR Compliance

#### Data Protection Implementation
```python
class GDPRCompliantIncidentManager(models.Manager):
    """Manager with GDPR compliance features."""
    
    def anonymize_user_data(self, user):
        """Anonymize user data in incidents."""
        incidents = self.filter(reporter=user)
        for incident in incidents:
            incident.reporter = None
            incident.metadata['anonymized'] = True
            incident.metadata['anonymized_at'] = timezone.now().isoformat()
            incident.save()
    
    def export_user_data(self, user):
        """Export user's incident data for portability."""
        incidents = self.filter(reporter=user)
        return {
            'incidents': [
                {
                    'id': incident.id,
                    'title': incident.title,
                    'description': incident.description,
                    'created_at': incident.created_at.isoformat(),
                    'status': incident.status,
                    'category': incident.category.name,
                }
                for incident in incidents
            ]
        }
```

### Audit Trail Implementation

#### Audit Logging
```python
class IncidentAuditLogger:
    """Comprehensive audit logging for incidents."""
    
    @staticmethod
    def log_incident_creation(incident, user, request):
        """Log incident creation."""
        IncidentAuditLog.objects.create(
            incident=incident,
            user=user,
            action='incident_created',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            metadata={
                'title': incident.title,
                'category': incident.category.name,
                'priority': incident.priority,
            }
        )
    
    @staticmethod
    def log_status_change(incident, old_status, new_status, user, request):
        """Log status change."""
        IncidentAuditLog.objects.create(
            incident=incident,
            user=user,
            action='status_changed',
            field_name='status',
            old_value=old_status,
            new_value=new_status,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
        )
```

## Implementation Notes

### Technology Stack
- **Backend**: Django 4.2+ with Django REST Framework
- **CMS**: Wagtail 5.0+ with multilingual support
- **Storage**: MinIO for media files with S3-compatible API
- **Real-time**: Django Channels with Redis for WebSocket
- **Database**: PostgreSQL with PostGIS for location data
- **Translation**: Django i18n with Wagtail translation support

### Performance Considerations
- Database indexing on frequently queried fields
- Redis caching for category and priority lookups
- Media file optimization and CDN integration
- WebSocket connection pooling and management
- Asynchronous task processing for heavy operations

### Security Considerations
- File upload validation and virus scanning
- Access control for sensitive incident data
- API rate limiting and authentication
- Secure media file storage with signed URLs
- Audit log integrity and tamper protection

### Compliance Requirements
- GDPR compliance for personal data handling
- South African data protection regulations
- Accessibility compliance (WCAG 2.1 AA)
- Audit trail requirements for accountability
- Multilingual support for community inclusion

This comprehensive incident reporting and tracking system provides a robust foundation for community safety and issue management while maintaining the highest standards of privacy, accessibility, and multilingual support.
