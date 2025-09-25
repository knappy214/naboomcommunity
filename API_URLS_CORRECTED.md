# API URLs - Corrected Information

## ✅ **Community Hub API URLs**

The Community Hub API is correctly configured and working at:

### **Base URL:**
```
http://localhost:8000/api/community/
```

### **Available Endpoints:**
- `GET /api/community/channels/` - List channels
- `GET /api/community/threads/` - List threads  
- `GET /api/community/posts/` - List posts
- `GET /api/community/alerts/` - List alerts
- `GET /api/community/events/` - List events
- `GET /api/community/join-requests/` - List join requests
- `GET /api/community/reports/` - List reports
- `GET /api/community/devices/` - List devices
- `GET /api/community/vapid-key/` - Get VAPID key
- `GET /api/community/search/threads/` - Search threads

## ❌ **Incorrect URL (404 Error):**
```
http://localhost:8000/api/community-hub/
```
This URL does not exist and will return a 404 error.

## ✅ **Other Working API URLs:**

### **Authentication:**
- `POST /api/auth/jwt/create/` - Get JWT token
- `POST /api/auth/jwt/refresh/` - Refresh JWT token
- `POST /api/auth/jwt/verify/` - Verify JWT token

### **User Profile:**
- `GET /api/user-profile/` - Get user profile
- `GET /api/user-profile/avatar/info/` - Get avatar info
- `POST /api/user-profile/avatar/upload/` - Upload avatar

### **Wagtail API v2:**
- `GET /api/v2/user-profiles/` - Wagtail user profiles API

## **Testing Results:**

✅ **Community Hub API**: All endpoints return 200 with proper JWT authentication
✅ **Authentication**: JWT token creation and refresh working
✅ **User Profile**: Avatar URLs optimized for performance
✅ **Image Serving**: Custom image serving from S3/MinIO working

## **For Frontend Development:**

Use the correct base URL in your Vue.js and Expo applications:

```javascript
// Vue.js / Expo
const API_BASE_URL = 'http://localhost:8000/api/community/';
```

The Community Hub API documentation has been updated with the correct URLs! 🚀
