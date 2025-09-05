# Avatar Implementation for User Profiles

This document summarizes the avatar functionality added to the user profile system, designed to support forum creation and community features.

## Overview

The avatar system provides comprehensive image management for user profiles, including upload, display in multiple sizes, and integration with Wagtail's image management system.

## Features Implemented

### 🖼️ **Avatar Management**
- **Upload**: Direct image upload with validation
- **Display**: Multiple size variants (small, medium, large)
- **Deletion**: Remove current avatar
- **Existing Images**: Set avatar from existing Wagtail images
- **Information**: Detailed avatar metadata and URLs

### 🔧 **Technical Features**
- **Wagtail Integration**: Uses Wagtail's Image model for storage
- **Automatic Resizing**: WebP format with fallbacks
- **Validation**: File type and size validation (max 5MB)
- **Security**: Proper authentication and authorization
- **API Integration**: RESTful endpoints for all operations

## Files Modified/Created

### 1. Model Updates (`home/models.py`)
- Added `avatar` field to `UserProfile` model
- Added helper methods for avatar URL generation
- Integrated with Wagtail's Image model

### 2. Serializers (`api/user_profile_serializers.py`)
- Updated `UserProfileSerializer` with avatar fields
- Added `AvatarUploadSerializer` for file uploads
- Enhanced `UserProfileUpdateSerializer` with avatar support

### 3. Views (`api/user_profile_views.py`)
- `AvatarUploadView`: Handle image uploads
- `AvatarDeleteView`: Remove current avatar
- `avatar_info`: Get detailed avatar information
- `set_avatar_from_existing`: Use existing images

### 4. URL Configuration (`api/urls.py`)
Added avatar endpoints:
- `/api/user-profile/avatar/upload/`
- `/api/user-profile/avatar/delete/`
- `/api/user-profile/avatar/info/`
- `/api/user-profile/avatar/set-existing/`

### 5. Tests (`api/tests_user_profile.py`)
Comprehensive test coverage for all avatar functionality

### 6. Documentation (`api/USER_PROFILE_API.md`)
Complete API documentation with examples

## Avatar Sizes and Use Cases

| Size | Dimensions | Use Case | Method |
|------|------------|----------|---------|
| Small | 50x50px | Forum posts, comments | `get_avatar_small()` |
| Medium | 150x150px | Profile pages, user cards | `get_avatar_medium()` |
| Large | 300x300px | Profile headers, detailed views | `get_avatar_large()` |
| Original | Full size | High-resolution displays | `avatar_url` |

## API Endpoints

### Upload Avatar
```bash
POST /api/user-profile/avatar/upload/
Content-Type: multipart/form-data

image: <file>
```

### Delete Avatar
```bash
DELETE /api/user-profile/avatar/delete/
```

### Get Avatar Info
```bash
GET /api/user-profile/avatar/info/
```

### Set from Existing Image
```bash
POST /api/user-profile/avatar/set-existing/
Content-Type: application/json

{
    "image_id": 1
}
```

## Profile Data Structure

The user profile now includes comprehensive avatar information:

```json
{
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
    "avatar_id": 1
}
```

## Usage Examples

### JavaScript/Fetch
```javascript
// Upload avatar
const formData = new FormData();
formData.append('image', fileInput.files[0]);

const response = await fetch('/api/user-profile/avatar/upload/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`
    },
    body: formData
});

// Get avatar info
const avatarInfo = await fetch('/api/user-profile/avatar/info/', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
}).then(r => r.json());
```

### Python/Requests
```python
# Upload avatar
with open('avatar.jpg', 'rb') as f:
    files = {'image': f}
    response = requests.post(
        f'{base_url}/user-profile/avatar/upload/',
        headers={'Authorization': f'Bearer {token}'},
        files=files
    )

# Set from existing image
response = requests.post(
    f'{base_url}/user-profile/avatar/set-existing/',
    headers={'Authorization': f'Bearer {token}'},
    json={'image_id': 1}
)
```

## Forum Integration

The avatar system is designed to seamlessly integrate with forum features:

### Forum Posts
- Use `avatar_small` (50x50px) for post headers
- Consistent display across all forum interactions
- Fallback to default avatar when none set

### User Profiles
- Use `avatar_medium` (150x150px) for profile pages
- `avatar_large` (300x300px) for profile headers
- Full avatar information available via API

### Community Features
- Avatar display in member directories
- Group membership displays
- Activity feeds and notifications

## Security Considerations

1. **File Validation**: Only image files (JPEG, PNG, WebP, GIF) allowed
2. **Size Limits**: Maximum 5MB file size
3. **Authentication**: All endpoints require valid JWT tokens
4. **User Isolation**: Users can only manage their own avatars
5. **Image Processing**: Automatic format conversion and resizing

## Performance Optimizations

1. **WebP Format**: Automatic conversion to WebP for better compression
2. **Multiple Sizes**: Pre-generated thumbnails for common use cases
3. **Lazy Loading**: Support for lazy loading in frontend implementations
4. **CDN Ready**: URLs are CDN-compatible for global distribution

## Database Schema

The avatar field is stored as a foreign key to Wagtail's Image model:

```sql
ALTER TABLE home_userprofile 
ADD COLUMN avatar_id INTEGER REFERENCES wagtailimages_image(id) 
ON DELETE SET NULL;
```

## Migration Status

- ✅ Model field added
- ✅ Database migration applied
- ✅ API endpoints implemented
- ✅ Tests written
- ✅ Documentation updated
- ✅ Example code provided

## Next Steps for Forum Integration

1. **Frontend Components**: Create avatar display components
2. **Default Avatars**: Implement fallback avatar system
3. **Avatar Gallery**: Allow users to choose from preset avatars
4. **Moderation**: Add avatar moderation for inappropriate content
5. **Caching**: Implement avatar URL caching for performance
6. **Analytics**: Track avatar usage and engagement

## Testing

Run the avatar tests:
```bash
python manage.py test api.tests_user_profile.AvatarAPITestCase
```

## Conclusion

The avatar system provides a robust foundation for user identity in the community platform. It integrates seamlessly with Wagtail's image management while providing the flexibility needed for forum and community features. The implementation follows best practices for security, performance, and user experience.

All avatar functionality is production-ready and fully documented, with comprehensive test coverage ensuring reliability and maintainability.
