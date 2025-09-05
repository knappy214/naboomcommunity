# User Profile API Implementation

This document summarizes the implementation of user profile pages for viewing and editing using Wagtail API v2, as requested.

## Overview

The implementation provides a comprehensive user profile management system with the following features:

- **Profile Viewing**: Complete user profile information retrieval
- **Profile Editing**: Update personal, medical, and preference information
- **Basic Info Management**: Update name and email
- **Password Management**: Secure password change functionality
- **Group Management**: Join/leave community groups with role assignments
- **Statistics**: Profile completion and activity statistics
- **Security**: Proper authentication and authorization

## Files Created/Modified

### 1. API Serializers (`api/user_profile_serializers.py`)
- `UserProfileSerializer`: Complete profile data with user info and group memberships
- `UserProfileUpdateSerializer`: Profile update (excludes sensitive fields)
- `UserBasicInfoUpdateSerializer`: Basic user information updates
- `UserPasswordChangeSerializer`: Password change with validation
- `UserGroupSerializer`, `UserRoleSerializer`, `UserGroupMembershipSerializer`: Group management

### 2. API Views (`api/user_profile_views.py`)
- `UserProfileDetailView`: GET current user's profile
- `UserProfileUpdateView`: PATCH profile information
- `UserBasicInfoUpdateView`: PATCH basic user info
- `UserPasswordChangeView`: POST password change
- `UserGroupListView`, `UserRoleListView`: List available groups/roles
- `UserGroupMembershipListView`: Manage group memberships
- `user_profile_stats`: Profile statistics endpoint
- `join_group`, `leave_group`: Group management functions

### 3. Permissions (`api/permissions.py`)
- `IsProfileOwner`: Users can only access their own profiles
- `CanManageGroupMemberships`: Users can manage their own group memberships
- `IsAdminOrReadOnly`: Admin-only write access for groups/roles
- `IsOwnerOrReadOnly`: Object-level ownership permissions

### 4. URL Configuration (`api/urls.py`)
Added comprehensive URL patterns for all user profile endpoints:
- `/api/user-profile/` - Profile management
- `/api/user-groups/` - Group listing
- `/api/user-roles/` - Role listing
- `/api/user-profile/group-memberships/` - Membership management

### 5. Tests (`api/tests_user_profile.py`)
Comprehensive test suite covering:
- Profile retrieval and updates
- Password changes
- Group management
- Permission enforcement
- Input validation
- Error handling

### 6. Documentation (`api/USER_PROFILE_API.md`)
Complete API documentation with:
- Endpoint descriptions
- Request/response examples
- Authentication requirements
- Error handling
- Usage examples in JavaScript and Python

### 7. Management Command (`home/management/commands/setup_sample_data.py`)
Command to create sample groups and roles for testing:
```bash
python manage.py setup_sample_data
```

### 8. Example Usage (`api/example_usage.py`)
Python client example demonstrating API usage with the `UserProfileAPIClient` class.

## API Endpoints Summary

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| GET | `/api/user-profile/` | Get current user's profile | JWT Required |
| PATCH | `/api/user-profile/update/` | Update profile information | JWT Required |
| PATCH | `/api/user-profile/basic-info/` | Update basic user info | JWT Required |
| POST | `/api/user-profile/change-password/` | Change password | JWT Required |
| GET | `/api/user-profile/stats/` | Get profile statistics | JWT Required |
| GET | `/api/user-groups/` | List available groups | JWT Required |
| GET | `/api/user-roles/` | List available roles | JWT Required |
| GET | `/api/user-profile/group-memberships/` | List user's memberships | JWT Required |
| POST | `/api/user-profile/join-group/` | Join a group | JWT Required |
| POST | `/api/user-profile/leave-group/` | Leave a group | JWT Required |

## Key Features

### 1. **Comprehensive Profile Data**
- Personal information (phone, address, etc.)
- Medical information (allergies, conditions, medications)
- Emergency contacts
- Preferences (language, notifications, MFA)
- Group memberships with roles

### 2. **Security & Permissions**
- JWT authentication required for all endpoints
- Users can only access their own profiles
- Proper input validation and sanitization
- Password strength validation
- Email uniqueness validation

### 3. **Group Management**
- Join/leave community groups
- Role-based permissions within groups
- Membership tracking with timestamps
- Admin-controlled group and role creation

### 4. **Profile Statistics**
- Completion percentage calculation
- Field completion tracking
- Group membership counts
- Activity timestamps

### 5. **Error Handling**
- Comprehensive error responses
- Validation error details
- Proper HTTP status codes
- User-friendly error messages

## Usage Examples

### Get User Profile
```bash
curl -H "Authorization: Bearer <token>" \
     https://your-domain.com/api/user-profile/
```

### Update Profile
```bash
curl -X PATCH \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"phone": "+1234567890", "city": "New City"}' \
     https://your-domain.com/api/user-profile/update/
```

### Join Group
```bash
curl -X POST \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"group_id": 1, "role_id": 1}' \
     https://your-domain.com/api/user-profile/join-group/
```

## Testing

Run the test suite:
```bash
python manage.py test api.tests_user_profile
```

Set up sample data:
```bash
python manage.py setup_sample_data
```

## Integration with Wagtail API v2

The implementation follows Wagtail API v2 patterns and integrates seamlessly with the existing Wagtail content management system. The user profile API complements the content API by providing user-specific functionality while maintaining the same authentication and permission patterns.

## Next Steps

1. **Frontend Integration**: Create frontend components to consume these APIs
2. **Admin Interface**: Enhance Wagtail admin for group/role management
3. **Email Notifications**: Add email notifications for group activities
4. **Advanced Permissions**: Implement more granular permission systems
5. **Profile Pictures**: Add profile picture upload functionality
6. **Data Export**: Implement GDPR-compliant data export features

## Conclusion

The user profile API implementation provides a robust, secure, and feature-rich system for managing user profiles and community memberships. It follows Django REST Framework and Wagtail API v2 best practices while providing comprehensive functionality for community management.

All endpoints are properly documented, tested, and ready for production use. The implementation includes proper error handling, security measures, and follows the existing codebase patterns and conventions.
