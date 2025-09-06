# User Profile API Documentation

This document describes the user profile API endpoints for the Naboom Community application, built using Wagtail API v2 and Django REST Framework.

## Authentication

All user profile endpoints require JWT authentication. Include the JWT token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/jwt/create/` | Obtain access and refresh tokens using email and password |
| POST | `/api/auth/jwt/refresh/` | Refresh an existing access token |
| POST | `/api/auth/jwt/verify/` | Verify token validity |
| POST | `/api/auth/register/` | Register a new user account |
| POST | `/api/auth/password-reset/` | Request a password reset link |
| POST | `/api/auth/password-reset/confirm/` | Confirm password reset with UID and token |

## Base URL

All endpoints are prefixed with `/api/`. The same endpoints are also available under `/api/v2/` for Wagtail API consumers.

## Endpoints Overview

### User Profile Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/user-profile/` | Get current user's profile |
| PATCH | `/api/user-profile/update/` | Update current user's profile |
| PATCH | `/api/user-profile/basic-info/` | Update basic user information |
| POST | `/api/user-profile/change-password/` | Change user password |
| GET | `/api/user-profile/stats/` | Get profile statistics |

### Group Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/user-groups/` | List available user groups |
| GET | `/api/user-roles/` | List available user roles |
| GET | `/api/user-profile/group-memberships/` | List user's group memberships |
| POST | `/api/user-profile/group-memberships/` | Create new group membership |
| GET | `/api/user-profile/group-memberships/{id}/` | Get specific group membership |
| PATCH | `/api/user-profile/group-memberships/{id}/` | Update group membership |
| DELETE | `/api/user-profile/group-memberships/{id}/` | Delete group membership |
| POST | `/api/user-profile/join-group/` | Join a user group |
| POST | `/api/user-profile/leave-group/` | Leave a user group |

### Avatar Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/user-profile/avatar/upload/` | Upload new avatar |
| DELETE | `/api/user-profile/avatar/delete/` | Delete current avatar |
| GET | `/api/user-profile/avatar/info/` | Get avatar information |
| POST | `/api/user-profile/avatar/set-existing/` | Set avatar from existing image |

## Detailed Endpoint Documentation

### 1. Get User Profile

**GET** `/api/user-profile/`

Retrieves the current user's complete profile information.

**Response:**
```json
{
    "user_id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "is_active": true,
    "date_joined": "2024-01-01T00:00:00Z",
    "last_login": "2024-01-15T10:30:00Z",
    "phone": "+1234567890",
    "date_of_birth": "1990-01-01",
    "gender": "Other",
    "address": "123 Main Street",
    "city": "Test City",
    "province": "Test Province",
    "postal_code": "12345",
    "allergies": "None",
    "medical_conditions": "None",
    "current_medications": "None",
    "emergency_contact_name": "Jane Doe",
    "emergency_contact_phone": "+0987654321",
    "emergency_contact_relationship": "Spouse",
    "preferred_language": "en",
    "timezone": "UTC",
    "email_notifications": true,
    "sms_notifications": false,
    "mfa_enabled": false,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "avatar": {
        "id": 1,
        "title": "User Avatar",
        "url": "https://example.com/media/images/avatar.jpg",
        "width": 300,
        "height": 300
    },
    "avatar_url": "https://example.com/media/images/avatar.jpg",
    "avatar_small": "https://example.com/media/images/avatar_50x50.webp",
    "avatar_medium": "https://example.com/media/images/avatar_150x150.webp",
    "avatar_large": "https://example.com/media/images/avatar_300x300.webp",
    "group_memberships": [
        {
            "id": 1,
            "group": {
                "id": 1,
                "name": "Members",
                "description": "General community members"
            },
            "role": {
                "id": 1,
                "name": "Member",
                "description": "Basic member role"
            },
            "joined_at": "2024-01-01T00:00:00Z",
            "is_active": true,
            "notes": ""
        }
    ]
}
```

### 2. Update User Profile

**PATCH** `/api/user-profile/update/`

Updates the current user's profile information (excluding basic user info and sensitive fields).

**Request Body:**
```json
{
    "phone": "+1234567890",
    "date_of_birth": "1990-01-01",
    "gender": "Other",
    "address": "123 Main Street",
    "city": "Test City",
    "province": "Test Province",
    "postal_code": "12345",
    "allergies": "None",
    "medical_conditions": "None",
    "current_medications": "None",
    "emergency_contact_name": "Jane Doe",
    "emergency_contact_phone": "+0987654321",
    "emergency_contact_relationship": "Spouse",
    "preferred_language": "en",
    "timezone": "UTC",
    "email_notifications": true,
    "sms_notifications": false,
    "mfa_enabled": false
}
```

**Response:** Same as GET profile endpoint

### 3. Update Basic User Information

**PATCH** `/api/user-profile/basic-info/`

Updates the current user's basic information (name and email).

**Request Body:**
```json
{
    "first_name": "Updated",
    "last_name": "Name",
    "email": "updated@example.com"
}
```

**Response:**
```json
{
    "first_name": "Updated",
    "last_name": "Name",
    "email": "updated@example.com"
}
```

### 4. Change Password

**POST** `/api/user-profile/change-password/`

Changes the current user's password.

**Request Body:**
```json
{
    "current_password": "oldpassword123",
    "new_password": "newpassword123",
    "confirm_password": "newpassword123"
}
```

**Response:**
```json
{
    "detail": "Password changed successfully"
}
```

### 5. Get Profile Statistics

**GET** `/api/user-profile/stats/`

Retrieves statistics about the current user's profile.

**Response:**
```json
{
    "profile_completion_percentage": 75.0,
    "completed_fields": 7,
    "total_fields": 10,
    "group_memberships_count": 2,
    "active_groups": ["Members", "Choir"],
    "profile_created_at": "2024-01-01T00:00:00Z",
    "profile_updated_at": "2024-01-15T10:30:00Z",
    "user_joined_at": "2024-01-01T00:00:00Z",
    "last_login": "2024-01-15T10:30:00Z"
}
```

### 6. Join User Group

**POST** `/api/user-profile/join-group/`

Joins a user group.

**Request Body:**
```json
{
    "group_id": 1,
    "role_id": 1
}
```

**Response:**
```json
{
    "id": 1,
    "group": {
        "id": 1,
        "name": "Choir",
        "description": "Community choir group"
    },
    "role": {
        "id": 1,
        "name": "Member",
        "description": "Basic member role"
    },
    "joined_at": "2024-01-15T10:30:00Z",
    "is_active": true,
    "notes": ""
}
```

### 7. Leave User Group

**POST** `/api/user-profile/leave-group/`

Leaves a user group.

**Request Body:**
```json
{
    "group_id": 1
}
```

**Response:**
```json
{
    "detail": "Successfully left the group"
}
```

### 8. List User Groups

**GET** `/api/user-groups/`

Lists all available user groups.

**Response:**
```json
[
    {
        "id": 1,
        "name": "Members",
        "description": "General community members",
        "is_active": true,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    },
    {
        "id": 2,
        "name": "Choir",
        "description": "Community choir group",
        "is_active": true,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }
]
```

### 9. List User Roles

**GET** `/api/user-roles/`

Lists all available user roles.

**Response:**
```json
[
    {
        "id": 1,
        "name": "Member",
        "description": "Basic member role",
        "permissions": {},
        "is_active": true,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    },
    {
        "id": 2,
        "name": "Leader",
        "description": "Group leader role",
        "permissions": {"can_manage_members": true},
        "is_active": true,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }
]
```

## Error Responses

### 400 Bad Request
```json
{
    "field_name": ["Error message"]
}
```

### 401 Unauthorized
```json
{
    "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
    "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
    "detail": "Not found."
}
```

## Usage Examples

### JavaScript/Fetch Example

```javascript
// Get user profile
const response = await fetch('/api/user-profile/', {
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    }
});
const profile = await response.json();

// Update profile
const updateResponse = await fetch('/api/user-profile/update/', {
    method: 'PATCH',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        phone: '+1234567890',
        city: 'New City'
    })
});
```

### Python/Requests Example

```python
import requests

# Get user profile
response = requests.get(
    'https://your-domain.com/api/user-profile/',
    headers={'Authorization': f'Bearer {token}'}
)
profile = response.json()

# Update profile
update_response = requests.patch(
    'https://your-domain.com/api/user-profile/update/',
    headers={'Authorization': f'Bearer {token}'},
    json={
        'phone': '+1234567890',
        'city': 'New City'
    }
)
```

### Avatar Management Endpoints

#### Upload Avatar

**POST** `/api/user-profile/avatar/upload/`

Upload a new avatar image for the current user.

**Request Body (multipart/form-data):**
```
image: <file>
```

**Response:**
```json
{
    "detail": "Avatar uploaded successfully",
    "avatar": {
        "id": 1,
        "url": "https://example.com/media/images/avatar.jpg",
        "title": "Avatar for testuser"
    },
    "profile": {
        // Complete profile data with updated avatar info
    }
}
```

#### Delete Avatar

**DELETE** `/api/user-profile/avatar/delete/`

Delete the current user's avatar.

**Response:**
```json
{
    "detail": "Avatar deleted successfully",
    "deleted_avatar": {
        "id": 1,
        "title": "Avatar for testuser"
    }
}
```

#### Get Avatar Information

**GET** `/api/user-profile/avatar/info/`

Get detailed information about the current user's avatar.

**Response (with avatar):**
```json
{
    "has_avatar": true,
    "avatar": {
        "id": 1,
        "title": "Avatar for testuser",
        "url": "https://example.com/media/images/avatar.jpg",
        "width": 300,
        "height": 300,
        "file_size": 45678,
        "created_at": "2024-01-15T10:30:00Z",
        "urls": {
            "original": "https://example.com/media/images/avatar.jpg",
            "small": "https://example.com/media/images/avatar_50x50.webp",
            "medium": "https://example.com/media/images/avatar_150x150.webp",
            "large": "https://example.com/media/images/avatar_300x300.webp"
        }
    }
}
```

**Response (no avatar):**
```json
{
    "has_avatar": false,
    "avatar": null
}
```

#### Set Avatar from Existing Image

**POST** `/api/user-profile/avatar/set-existing/`

Set the avatar from an existing image in the system.

**Request Body:**
```json
{
    "image_id": 1
}
```

**Response:**
```json
{
    "detail": "Avatar set successfully",
    "avatar": {
        "id": 1,
        "url": "https://example.com/media/images/avatar.jpg",
        "title": "Existing Image"
    },
    "profile": {
        // Complete profile data with updated avatar info
    }
}
```

## Security Considerations

1. **Authentication Required**: All endpoints require valid JWT authentication
2. **User Isolation**: Users can only access and modify their own profiles
3. **Password Security**: Password changes require current password verification
4. **Email Validation**: Email updates are validated for uniqueness and format
5. **Input Validation**: All input data is validated according to model constraints
6. **Avatar Security**: Image uploads are validated for file type and size (max 5MB)

## Rate Limiting

The API implements rate limiting to prevent abuse. Please respect the rate limits and implement appropriate retry logic in your client applications.

## Support

For technical support or questions about the API, please contact the development team or refer to the main project documentation.
