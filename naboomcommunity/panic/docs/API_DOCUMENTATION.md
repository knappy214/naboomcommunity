# Emergency Response System API Documentation

## Overview

The Emergency Response System provides a comprehensive API for emergency management, including panic button activation, location tracking, medical data management, family notifications, and external service integration.

## Base URL

```
https://naboomneighbornet.net.za/api/
```

## Authentication

All API endpoints require authentication using JWT tokens. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Panic Button**: 5 requests per minute per user
- **Location Updates**: 10 requests per minute per user
- **Medical Data**: 3 requests per minute per user
- **Notifications**: 20 requests per minute per user
- **External Dispatch**: 3 requests per minute per user

## Error Handling

All API responses follow a consistent error format:

```json
{
    "error": "Error message",
    "details": {
        "field_name": ["Specific error message"]
    },
    "timestamp": "2024-01-01T12:00:00Z"
}
```

## Enhanced Panic Button API

### Activate Enhanced Panic Button

**POST** `/api/enhanced/panic/`

Activates the enhanced panic button with location accuracy validation and medical data integration.

#### Request Body

```json
{
    "emergency_type": "panic|medical|fire|crime|accident",
    "location": {
        "latitude": -26.2041,
        "longitude": 28.0473,
        "accuracy": 10.5,
        "altitude": 1500.0,
        "heading": 45.0,
        "speed": 0.0
    },
    "device_info": {
        "device_id": "device-123",
        "platform": "android|ios|web",
        "app_version": "1.0.0",
        "os_version": "11.0"
    },
    "context": {
        "description": "Emergency description",
        "severity": "low|medium|high|critical",
        "timestamp": "2024-01-01T12:00:00Z"
    }
}
```

#### Response

```json
{
    "emergency_id": "uuid",
    "status": "activated",
    "location_accuracy": "very_high",
    "medical_summary": {
        "blood_type": "O+",
        "critical_allergies": ["Penicillin"],
        "emergency_contact": "John Doe (+27123456789)"
    },
    "timestamp": "2024-01-01T12:00:00Z"
}
```

### Validate Location Accuracy

**POST** `/api/enhanced/location/validate/`

Validates GPS location accuracy and returns accuracy level.

#### Request Body

```json
{
    "latitude": -26.2041,
    "longitude": 28.0473,
    "accuracy": 10.5,
    "altitude": 1500.0,
    "heading": 45.0,
    "speed": 0.0
}
```

#### Response

```json
{
    "is_valid": true,
    "accuracy_level": "very_high|high|medium|low|very_low|unacceptable",
    "confidence_score": 0.95,
    "recommendations": ["Enable high accuracy mode"]
}
```

### Batch Location Accuracy

**POST** `/api/enhanced/location/batch/`

Validates multiple location points for accuracy.

#### Request Body

```json
{
    "locations": [
        {
            "latitude": -26.2041,
            "longitude": 28.0473,
            "accuracy": 10.5,
            "timestamp": "2024-01-01T12:00:00Z"
        }
    ]
}
```

#### Response

```json
{
    "results": [
        {
            "is_valid": true,
            "accuracy_level": "very_high",
            "confidence_score": 0.95
        }
    ],
    "overall_accuracy": "high"
}
```

## Medical Data API

### Get Medical Data

**GET** `/api/enhanced/medical/`

Retrieves user's medical data based on consent level.

#### Response

```json
{
    "medical_data": {
        "blood_type": "O+",
        "allergies": [
            {
                "name": "Penicillin",
                "severity": "severe",
                "requires_immediate_attention": true
            }
        ],
        "medical_conditions": [
            {
                "name": "Diabetes",
                "type": "Type 1",
                "requires_immediate_attention": true
            }
        ],
        "medications": [
            {
                "name": "Insulin",
                "dosage": "10 units",
                "is_emergency_medication": true
            }
        ],
        "emergency_contact": {
            "name": "John Doe",
            "phone": "+27123456789",
            "relationship": "spouse"
        }
    },
    "consent_level": "emergency_only",
    "timestamp": "2024-01-01T12:00:00Z"
}
```

### Update Medical Data

**PUT** `/api/enhanced/medical/`

Updates user's medical data.

#### Request Body

```json
{
    "blood_type": "O+",
    "allergies": [
        {
            "name": "Penicillin",
            "severity": "severe",
            "requires_immediate_attention": true
        }
    ],
    "medical_conditions": [
        {
            "name": "Diabetes",
            "type": "Type 1",
            "requires_immediate_attention": true
        }
    ],
    "medications": [
        {
            "name": "Insulin",
            "dosage": "10 units",
            "is_emergency_medication": true
        }
    ],
    "emergency_contact_name": "John Doe",
    "emergency_contact_phone": "+27123456789",
    "emergency_contact_relationship": "spouse",
    "consent_level": "emergency_only|full"
}
```

#### Response

```json
{
    "success": true,
    "consent_level": "emergency_only",
    "encrypted_fields": ["allergies", "medical_conditions"],
    "timestamp": "2024-01-01T12:00:00Z"
}
```

## Family Notification API

### Send Family Notification

**POST** `/api/family/notify/`

Sends emergency notification to family and contacts.

#### Request Body

```json
{
    "emergency_id": "uuid",
    "emergency_type": "panic|medical|fire|crime|accident",
    "channels": ["sms", "email", "push", "whatsapp"],
    "recipients": [
        {
            "name": "John Doe",
            "phone": "+27123456789",
            "email": "john@example.com",
            "relationship": "spouse",
            "priority": "high"
        }
    ],
    "message": "Custom emergency message",
    "priority": "high|critical",
    "location": {
        "latitude": -26.2041,
        "longitude": 28.0473,
        "accuracy": 10.5,
        "address": "123 Main St, Johannesburg"
    },
    "medical_data": {
        "blood_type": "O+",
        "allergies": [],
        "medical_conditions": []
    }
}
```

#### Response

```json
{
    "notification_id": "uuid",
    "channels_sent": ["sms", "email"],
    "total_sent": 5,
    "total_failed": 0,
    "results": {
        "sms": {
            "success": true,
            "sent_count": 3,
            "failed_count": 0
        },
        "email": {
            "success": true,
            "sent_count": 2,
            "failed_count": 0
        }
    },
    "timestamp": "2024-01-01T12:00:00Z"
}
```

### Get Emergency Contacts

**GET** `/api/family/contacts/`

Retrieves user's emergency contacts.

#### Query Parameters

- `include_medical` (boolean): Include medical emergency contacts (default: true)
- `include_family` (boolean): Include family contacts (default: true)
- `include_friends` (boolean): Include friend contacts (default: true)

#### Response

```json
{
    "contacts": [
        {
            "id": "uuid",
            "name": "John Doe",
            "phone": "+27123456789",
            "email": "john@example.com",
            "relationship": "spouse",
            "priority": "high",
            "contact_type": "family",
            "is_primary": true,
            "notifications_enabled": true
        }
    ],
    "total_contacts": 5,
    "timestamp": "2024-01-01T12:00:00Z"
}
```

### Add Emergency Contact

**POST** `/api/family/contacts/add/`

Adds new emergency contact.

#### Request Body

```json
{
    "name": "John Doe",
    "phone": "+27123456789",
    "email": "john@example.com",
    "relationship": "spouse|parent|sibling|friend|colleague",
    "priority": "low|medium|high|critical",
    "contact_type": "family|medical|friend",
    "is_primary": false,
    "notifications_enabled": true
}
```

#### Response

```json
{
    "contact_id": "uuid",
    "message": "Emergency contact added successfully",
    "timestamp": "2024-01-01T12:00:00Z"
}
```

## External Service Integration API

### Dispatch Emergency Service

**POST** `/api/integration/dispatch/`

Dispatches emergency to external service.

#### Request Body

```json
{
    "emergency_id": "uuid",
    "emergency_type": "panic|medical|fire|crime|accident|rescue|disaster|security",
    "priority": "low|medium|high|critical",
    "description": "Emergency description",
    "location": {
        "latitude": -26.2041,
        "longitude": 28.0473,
        "accuracy": 10.5,
        "altitude": 1500.0,
        "address": "123 Main St, Johannesburg"
    },
    "medical_data": {
        "blood_type": "O+",
        "allergies": [],
        "medical_conditions": [],
        "consent_level": "emergency_only|full"
    },
    "service_preference": "police|ambulance|fire|rescue|disaster|security|auto"
}
```

#### Response

```json
{
    "dispatch_id": "uuid",
    "service_type": "police",
    "service_name": "South African Police Service",
    "external_id": "ext-123",
    "status": "dispatched",
    "message": "Emergency dispatched successfully",
    "timestamp": "2024-01-01T12:00:00Z"
}
```

### Get Available Services

**GET** `/api/integration/services/`

Retrieves list of available external emergency services.

#### Query Parameters

- `service_type` (string): Filter by service type (optional)
- `status` (string): Filter by service status (optional)

#### Response

```json
{
    "services": [
        {
            "id": "police_10111",
            "name": "South African Police Service",
            "type": "police",
            "protocol": "rest_api",
            "endpoint": "https://api.saps.gov.za/emergency",
            "timeout": 30,
            "retry_attempts": 3,
            "health": {
                "status": "healthy",
                "response_time": 0.5,
                "last_check": "2024-01-01T12:00:00Z"
            }
        }
    ],
    "total_services": 5,
    "timestamp": "2024-01-01T12:00:00Z"
}
```

### Get Service Status

**GET** `/api/integration/services/{service_type}/status/`

Gets status of specific external service.

#### Response

```json
{
    "service_type": "police",
    "service_name": "South African Police Service",
    "protocol": "rest_api",
    "status": "healthy",
    "response_time": 0.5,
    "last_check": "2024-01-01T12:00:00Z",
    "error": null
}
```

## Offline Sync API

### Create Sync Session

**POST** `/api/offline/session/create/`

Creates new offline sync session.

#### Request Body

```json
{
    "device_id": "device-123",
    "sync_type": "full|incremental|emergency_only"
}
```

#### Response

```json
{
    "session_id": "uuid",
    "sync_type": "full",
    "timestamp": "2024-01-01T12:00:00Z"
}
```

### Sync Offline Data

**POST** `/api/offline/sync/`

Syncs offline data with server.

#### Request Body

```json
{
    "session_id": "uuid",
    "device_id": "device-123",
    "sync_type": "full|incremental|emergency_only",
    "offline_data": {
        "emergency_location": [
            {
                "id": "uuid",
                "operation": "create|update|delete",
                "timestamp": "2024-01-01T12:00:00Z",
                "latitude": -26.2041,
                "longitude": 28.0473,
                "accuracy": 10.5,
                "emergency_type": "panic"
            }
        ],
        "emergency_medical": [
            {
                "id": "uuid",
                "operation": "create|update|delete",
                "timestamp": "2024-01-01T12:00:00Z",
                "blood_type": "O+",
                "allergies": [],
                "medications": []
            }
        ]
    },
    "checksum": "md5_checksum"
}
```

#### Response

```json
{
    "session_id": "uuid",
    "status": "synced",
    "synced_items": 5,
    "conflicts": 1,
    "errors": 0,
    "conflict_resolutions": [],
    "timestamp": "2024-01-01T12:00:00Z"
}
```

## WebSocket API

### WebSocket Status

**GET** `/api/websocket/status/`

Gets WebSocket connection status.

#### Response

```json
{
    "connections": 15,
    "active_channels": ["emergency_updates", "location_updates"],
    "server_status": "healthy",
    "timestamp": "2024-01-01T12:00:00Z"
}
```

### Subscribe to WebSocket

**POST** `/api/websocket/subscribe/`

Subscribes to WebSocket channels.

#### Request Body

```json
{
    "channels": ["emergency_updates", "location_updates", "medical_updates"],
    "emergency_id": "uuid"
}
```

#### Response

```json
{
    "status": "subscribed",
    "channels": ["emergency_updates", "location_updates"],
    "subscription_id": "uuid",
    "timestamp": "2024-01-01T12:00:00Z"
}
```

## WebSocket Endpoints

### Emergency Updates

**WebSocket** `/ws/emergency/{room_name}/`

Real-time emergency status updates.

#### Message Format

```json
{
    "type": "emergency_update",
    "emergency_id": "uuid",
    "status": "activated|dispatched|acknowledged|completed",
    "message": "Emergency status update",
    "timestamp": "2024-01-01T12:00:00Z"
}
```

### Location Updates

**WebSocket** `/ws/location/{user_id}/`

Real-time location tracking updates.

#### Message Format

```json
{
    "type": "location_update",
    "user_id": "uuid",
    "location": {
        "latitude": -26.2041,
        "longitude": 28.0473,
        "accuracy": 10.5,
        "timestamp": "2024-01-01T12:00:00Z"
    }
}
```

### Medical Updates

**WebSocket** `/ws/medical/{user_id}/`

Real-time medical data updates.

#### Message Format

```json
{
    "type": "medical_update",
    "user_id": "uuid",
    "medical_data": {
        "blood_type": "O+",
        "allergies": [],
        "timestamp": "2024-01-01T12:00:00Z"
    }
}
```

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input data |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server error |

## Rate Limiting Headers

When rate limiting is applied, the following headers are included:

```
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 3
X-RateLimit-Reset: 1640995200
Retry-After: 60
```

## Webhook Integration

### Emergency Webhook

**POST** `/webhooks/emergency/`

Receives emergency notifications from external services.

#### Request Body

```json
{
    "emergency_id": "uuid",
    "service_type": "police|ambulance|fire",
    "status": "dispatched|acknowledged|in_progress|completed",
    "external_id": "ext-123",
    "message": "Emergency response update",
    "timestamp": "2024-01-01T12:00:00Z",
    "signature": "webhook_signature"
}
```

## SDK Examples

### JavaScript/Node.js

```javascript
const EmergencyAPI = require('@naboom/emergency-api');

const client = new EmergencyAPI({
    baseURL: 'https://naboomneighbornet.net.za/api',
    token: 'your-jwt-token'
});

// Activate panic button
const emergency = await client.activatePanicButton({
    emergency_type: 'panic',
    location: {
        latitude: -26.2041,
        longitude: 28.0473,
        accuracy: 10.5
    },
    device_info: {
        device_id: 'device-123',
        platform: 'android'
    },
    context: {
        description: 'Emergency situation',
        severity: 'high'
    }
});

console.log('Emergency activated:', emergency.emergency_id);
```

### Python

```python
from naboom_emergency_api import EmergencyAPI

client = EmergencyAPI(
    base_url='https://naboomneighbornet.net.za/api',
    token='your-jwt-token'
)

# Activate panic button
emergency = client.activate_panic_button(
    emergency_type='panic',
    location={
        'latitude': -26.2041,
        'longitude': 28.0473,
        'accuracy': 10.5
    },
    device_info={
        'device_id': 'device-123',
        'platform': 'android'
    },
    context={
        'description': 'Emergency situation',
        'severity': 'high'
    }
)

print(f'Emergency activated: {emergency.emergency_id}')
```

### Swift/iOS

```swift
import EmergencyAPI

let client = EmergencyAPI(
    baseURL: URL(string: "https://naboomneighbornet.net.za/api")!,
    token: "your-jwt-token"
)

// Activate panic button
let emergency = try await client.activatePanicButton(
    emergencyType: .panic,
    location: Location(
        latitude: -26.2041,
        longitude: 28.0473,
        accuracy: 10.5
    ),
    deviceInfo: DeviceInfo(
        deviceId: "device-123",
        platform: .android
    ),
    context: Context(
        description: "Emergency situation",
        severity: .high
    )
)

print("Emergency activated: \(emergency.emergencyId)")
```

## Support

For API support and questions:

- **Email**: api-support@naboomneighbornet.net.za
- **Documentation**: https://docs.naboomneighbornet.net.za
- **Status Page**: https://status.naboomneighbornet.net.za
