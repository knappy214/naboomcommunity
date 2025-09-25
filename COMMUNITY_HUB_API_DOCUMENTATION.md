# Community Hub API Documentation

This document provides comprehensive API documentation for the Community Hub system, designed for both Vue.js and Expo/React Native frontends.

## Table of Contents

1. [Authentication](#authentication)
2. [Base URL and Headers](#base-url-and-headers)
3. [API Endpoints](#api-endpoints)
4. [Data Models](#data-models)
5. [Error Handling](#error-handling)
6. [Rate Limiting](#rate-limiting)
7. [WebSocket Events](#websocket-events)
8. [Frontend Implementation Examples](#frontend-implementation-examples)

---

## Authentication

### JWT Token Authentication

All API endpoints require JWT authentication. Include the access token in the Authorization header:

```http
Authorization: Bearer <your_access_token>
```

### Login Endpoints

#### Get JWT Token
```http
POST /api/auth/jwt/create/
Content-Type: application/json

{
  "username": "your_username",  // OR
  "email": "your_email@example.com",
  "password": "your_password"
}
```

**Response:**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Refresh Token
```http
POST /api/auth/jwt/refresh/
Content-Type: application/json

{
  "refresh": "your_refresh_token"
}
```

#### Verify Token
```http
POST /api/auth/jwt/verify/
Content-Type: application/json

{
  "token": "your_access_token"
}
```

---

## Base URL and Headers

### Base URL
```
http://localhost:8000/api/community/
```

### Required Headers
```http
Content-Type: application/json
Authorization: Bearer <access_token>
```

---

## API Endpoints

### 1. Channels

#### List Channels
```http
GET /api/community/channels/
```

**Response:**
```json
[
  {
    "id": 1,
    "slug": "general",
    "name": "General Discussion",
    "name_translations": {
      "en": "General Discussion",
      "af": "Algemene Bespreking"
    },
    "description": "General community discussions",
    "description_translations": {
      "en": "General community discussions",
      "af": "Algemene gemeenskapsbesprekings"
    },
    "kind": "discussion",
    "posting_policy": "members",
    "is_private": false,
    "is_active": true,
    "allow_alerts": true,
    "broadcast_scope": "members",
    "allow_join_requests": true,
    "default_alerts_enabled": true,
    "default_posts_enabled": true,
    "teaser_character_limit": 200,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "is_member": true,
    "membership_role": "member"
  }
]
```

#### Join Channel
```http
POST /api/community/channels/{id}/join/
```

**Response:**
```json
{
  "id": 1,
  "user": 1,
  "channel": 1,
  "role": "member",
  "is_active": true,
  "joined_at": "2024-01-01T00:00:00Z"
}
```

#### Leave Channel
```http
POST /api/community/channels/{id}/leave/
```

**Response:** `204 No Content`

### 2. Threads

#### List Threads
```http
GET /api/community/threads/
```

**Query Parameters:**
- `channel` (optional): Filter by channel ID
- `page` (optional): Page number for pagination
- `page_size` (optional): Number of items per page

**Response:**
```json
[
  {
    "id": 1,
    "title": "Welcome to the Community",
    "title_translations": {
      "en": "Welcome to the Community",
      "af": "Welkom by die Gemeenskap"
    },
    "channel": 1,
    "author": {
      "id": 1,
      "username": "admin",
      "first_name": "Admin",
      "last_name": "User"
    },
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "posts": [
      {
        "id": 1,
        "content": "Welcome everyone!",
        "author": {
          "id": 1,
          "username": "admin"
        },
        "created_at": "2024-01-01T00:00:00Z"
      }
    ]
  }
]
```

#### Create Thread
```http
POST /api/community/threads/
Content-Type: application/json

{
  "title": "New Discussion Thread",
  "channel": 1,
  "posts": [
    {
      "content": "This is the first post in the thread"
    }
  ]
}
```

#### Get Thread Details
```http
GET /api/community/threads/{id}/
```

#### Update Thread
```http
PUT /api/community/threads/{id}/
PATCH /api/community/threads/{id}/
```

#### Delete Thread
```http
DELETE /api/community/threads/{id}/
```

### 3. Posts

#### List Posts
```http
GET /api/community/posts/
```

**Query Parameters:**
- `thread` (optional): Filter by thread ID
- `channel` (optional): Filter by channel ID

#### Create Post
```http
POST /api/community/posts/
Content-Type: application/json

{
  "content": "This is a new post",
  "thread": 1,
  "channel": 1
}
```

#### Update Post
```http
PUT /api/community/posts/{id}/
PATCH /api/community/posts/{id}/
```

#### Soft Delete Post (Moderators Only)
```http
POST /api/community/posts/{id}/soft_delete/
```

#### Restore Post (Moderators Only)
```http
POST /api/community/posts/{id}/restore/
```

### 4. Alerts

#### List Alerts
```http
GET /api/community/alerts/
```

#### Create Alert
```http
POST /api/community/alerts/
Content-Type: application/json

{
  "content": "URGENT: Community meeting tomorrow at 2 PM",
  "thread": 1,
  "channel": 1
}
```

### 5. Events

#### List Events
```http
GET /api/community/events/
```

#### Create Event
```http
POST /api/community/events/
Content-Type: application/json

{
  "thread": 1,
  "event_date": "2024-01-15T14:00:00Z",
  "location": "Community Center",
  "max_attendees": 50
}
```

#### RSVP to Event
```http
POST /api/community/event-rsvps/
Content-Type: application/json

{
  "event": 1,
  "status": "attending"  // attending, maybe, not_attending
}
```

### 6. Channel Invites

#### List Invites (Moderators Only)
```http
GET /api/community/invites/
```

#### Create Invite (Moderators Only)
```http
POST /api/community/invites/
Content-Type: application/json

{
  "channel": 1,
  "email": "newuser@example.com",
  "role": "member"
}
```

### 7. Join Requests

#### List Join Requests
```http
GET /api/community/join-requests/
```

#### Create Join Request
```http
POST /api/community/join-requests/
Content-Type: application/json

{
  "channel": 1,
  "message": "I would like to join this community"
}
```

#### Approve Join Request (Moderators Only)
```http
POST /api/community/join-requests/{id}/approve/
```

#### Decline Join Request (Moderators Only)
```http
POST /api/community/join-requests/{id}/decline/
```

### 8. Reports

#### List Reports
```http
GET /api/community/reports/
```

#### Create Report
```http
POST /api/community/reports/
Content-Type: application/json

{
  "channel": 1,
  "thread": 1,
  "post": 1,
  "reason": "inappropriate_content",
  "description": "This post contains offensive language"
}
```

### 9. Search

#### Search Threads
```http
GET /api/community/search/threads/?q=search_term&channel=1
```

**Query Parameters:**
- `q`: Search query
- `channel` (optional): Filter by channel ID

### 10. Devices (Push Notifications)

#### List Devices
```http
GET /api/community/devices/
```

#### Register Device
```http
POST /api/community/devices/
Content-Type: application/json

{
  "device_id": "unique_device_identifier",
  "platform": "ios",  // ios, android, web
  "push_token": "device_push_token",
  "is_active": true
}
```

#### Get VAPID Public Key
```http
GET /api/community/vapid-key/
```

**Response:**
```json
{
  "publicKey": "BEl62iUYgUivxIkv69yViEuiBIa40HI..."
}
```

---

## Data Models

### Channel
```typescript
interface Channel {
  id: number;
  slug: string;
  name: string;
  name_translations: Record<string, string>;
  description: string;
  description_translations: Record<string, string>;
  kind: 'discussion' | 'announcement' | 'event';
  posting_policy: 'members' | 'moderators' | 'managers';
  is_private: boolean;
  is_active: boolean;
  allow_alerts: boolean;
  broadcast_scope: 'members' | 'all';
  allow_join_requests: boolean;
  default_alerts_enabled: boolean;
  default_posts_enabled: boolean;
  teaser_character_limit: number;
  created_at: string;
  updated_at: string;
  is_member: boolean;
  membership_role: 'member' | 'moderator' | 'manager' | null;
}
```

### Thread
```typescript
interface Thread {
  id: number;
  title: string;
  title_translations: Record<string, string>;
  channel: number;
  author: {
    id: number;
    username: string;
    first_name: string;
    last_name: string;
  };
  created_at: string;
  updated_at: string;
  posts: Post[];
}
```

### Post
```typescript
interface Post {
  id: number;
  content: string;
  content_translations: Record<string, string>;
  thread: number;
  channel: number;
  author: {
    id: number;
    username: string;
    first_name: string;
    last_name: string;
  };
  kind: 'post' | 'alert';
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
}
```

### Event
```typescript
interface Event {
  id: number;
  thread: number;
  event_date: string;
  location: string;
  max_attendees: number | null;
  created_at: string;
  updated_at: string;
}
```

### Event RSVP
```typescript
interface EventRSVP {
  id: number;
  event: number;
  user: number;
  status: 'attending' | 'maybe' | 'not_attending';
  created_at: string;
  updated_at: string;
}
```

---

## Error Handling

### Standard Error Response
```json
{
  "detail": "Error message",
  "code": "error_code",
  "field_errors": {
    "field_name": ["Error message for this field"]
  }
}
```

### Common HTTP Status Codes
- `200` - Success
- `201` - Created
- `204` - No Content
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Too Many Requests
- `500` - Internal Server Error

---

## Rate Limiting

- **Post Creation**: 10 posts per minute
- **Alert Creation**: 3 alerts per hour
- **General API**: 1000 requests per hour

Rate limit headers are included in responses:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

---

## WebSocket Events

### Connection
```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/community-hub/');

// Send authentication
ws.send(JSON.stringify({
  type: 'auth',
  token: 'your_access_token'
}));
```

### Event Types

#### New Thread
```json
{
  "type": "thread.created",
  "data": {
    "thread": { /* Thread object */ },
    "channel": { /* Channel object */ }
  }
}
```

#### New Post
```json
{
  "type": "post.created",
  "data": {
    "post": { /* Post object */ },
    "thread": { /* Thread object */ },
    "channel": { /* Channel object */ }
  }
}
```

#### New Alert
```json
{
  "type": "alert.created",
  "data": {
    "alert": { /* Alert object */ },
    "thread": { /* Thread object */ },
    "channel": { /* Channel object */ }
  }
}
```

---

## Frontend Implementation Examples

### Vue.js Implementation

#### API Service
```javascript
// api/communityHub.js
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/community/';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  }
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post('/api/auth/jwt/refresh/', {
          refresh: refreshToken
        });
        localStorage.setItem('access_token', response.data.access);
        return api.request(error.config);
      } catch (refreshError) {
        // Redirect to login
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const communityHubAPI = {
  // Channels
  getChannels: () => api.get('/channels/'),
  joinChannel: (channelId) => api.post(`/channels/${channelId}/join/`),
  leaveChannel: (channelId) => api.post(`/channels/${channelId}/leave/`),

  // Threads
  getThreads: (params = {}) => api.get('/threads/', { params }),
  getThread: (threadId) => api.get(`/threads/${threadId}/`),
  createThread: (data) => api.post('/threads/', data),
  updateThread: (threadId, data) => api.put(`/threads/${threadId}/`, data),
  deleteThread: (threadId) => api.delete(`/threads/${threadId}/`),

  // Posts
  getPosts: (params = {}) => api.get('/posts/', { params }),
  createPost: (data) => api.post('/posts/', data),
  updatePost: (postId, data) => api.put(`/posts/${postId}/`, data),
  deletePost: (postId) => api.post(`/posts/${postId}/soft_delete/`),

  // Alerts
  getAlerts: () => api.get('/alerts/'),
  createAlert: (data) => api.post('/alerts/', data),

  // Events
  getEvents: () => api.get('/events/'),
  createEvent: (data) => api.post('/events/', data),
  rsvpEvent: (data) => api.post('/event-rsvps/', data),

  // Search
  searchThreads: (query, channelId = null) => {
    const params = { q: query };
    if (channelId) params.channel = channelId;
    return api.get('/search/threads/', { params });
  },

  // Reports
  createReport: (data) => api.post('/reports/', data),

  // Devices
  getDevices: () => api.get('/devices/'),
  registerDevice: (data) => api.post('/devices/', data),
  getVapidKey: () => api.get('/vapid-key/'),
};
```

#### Vue Component Example
```vue
<template>
  <div class="community-hub">
    <div class="channels">
      <h2>Channels</h2>
      <div v-for="channel in channels" :key="channel.id" class="channel">
        <h3>{{ channel.name }}</h3>
        <p>{{ channel.description }}</p>
        <button @click="joinChannel(channel.id)" v-if="!channel.is_member">
          Join Channel
        </button>
        <button @click="leaveChannel(channel.id)" v-else>
          Leave Channel
        </button>
      </div>
    </div>

    <div class="threads">
      <h2>Threads</h2>
      <div v-for="thread in threads" :key="thread.id" class="thread">
        <h3>{{ thread.title }}</h3>
        <p>By {{ thread.author.username }}</p>
        <div v-for="post in thread.posts" :key="post.id" class="post">
          <p>{{ post.content }}</p>
          <small>{{ post.author.username }} - {{ formatDate(post.created_at) }}</small>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { communityHubAPI } from '@/api/communityHub';

export default {
  data() {
    return {
      channels: [],
      threads: [],
      loading: false,
      error: null
    };
  },
  async mounted() {
    await this.loadData();
  },
  methods: {
    async loadData() {
      this.loading = true;
      try {
        const [channelsResponse, threadsResponse] = await Promise.all([
          communityHubAPI.getChannels(),
          communityHubAPI.getThreads()
        ]);
        this.channels = channelsResponse.data;
        this.threads = threadsResponse.data;
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to load data';
      } finally {
        this.loading = false;
      }
    },
    async joinChannel(channelId) {
      try {
        await communityHubAPI.joinChannel(channelId);
        await this.loadData(); // Refresh data
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to join channel';
      }
    },
    async leaveChannel(channelId) {
      try {
        await communityHubAPI.leaveChannel(channelId);
        await this.loadData(); // Refresh data
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to leave channel';
      }
    },
    formatDate(dateString) {
      return new Date(dateString).toLocaleDateString();
    }
  }
};
</script>
```

### Expo/React Native Implementation

#### API Service
```javascript
// services/communityHubAPI.js
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = 'http://localhost:8000/api/community/';

class CommunityHubAPI {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  async getAuthHeaders() {
    const token = await AsyncStorage.getItem('access_token');
    return {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    };
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const headers = await this.getAuthHeaders();

    const response = await fetch(url, {
      ...options,
      headers: {
        ...headers,
        ...options.headers,
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        // Handle token refresh
        await this.refreshToken();
        // Retry request
        return this.request(endpoint, options);
      }
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  async refreshToken() {
    const refreshToken = await AsyncStorage.getItem('refresh_token');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await fetch('http://localhost:8000/api/auth/jwt/refresh/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: refreshToken }),
    });

    if (!response.ok) {
      throw new Error('Token refresh failed');
    }

    const data = await response.json();
    await AsyncStorage.setItem('access_token', data.access);
  }

  // Channels
  async getChannels() {
    return this.request('channels/');
  }

  async joinChannel(channelId) {
    return this.request(`channels/${channelId}/join/`, { method: 'POST' });
  }

  async leaveChannel(channelId) {
    return this.request(`channels/${channelId}/leave/`, { method: 'POST' });
  }

  // Threads
  async getThreads(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request(`threads/${queryString ? `?${queryString}` : ''}`);
  }

  async getThread(threadId) {
    return this.request(`threads/${threadId}/`);
  }

  async createThread(data) {
    return this.request('threads/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Posts
  async getPosts(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request(`posts/${queryString ? `?${queryString}` : ''}`);
  }

  async createPost(data) {
    return this.request('posts/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Alerts
  async getAlerts() {
    return this.request('alerts/');
  }

  async createAlert(data) {
    return this.request('alerts/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Search
  async searchThreads(query, channelId = null) {
    const params = { q: query };
    if (channelId) params.channel = channelId;
    const queryString = new URLSearchParams(params).toString();
    return this.request(`search/threads/?${queryString}`);
  }

  // Reports
  async createReport(data) {
    return this.request('reports/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Devices
  async registerDevice(data) {
    return this.request('devices/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getVapidKey() {
    return this.request('vapid-key/');
  }
}

export default new CommunityHubAPI();
```

#### React Native Component Example
```jsx
import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, TouchableOpacity, Alert } from 'react-native';
import CommunityHubAPI from '../services/communityHubAPI';

const CommunityHubScreen = () => {
  const [channels, setChannels] = useState([]);
  const [threads, setThreads] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [channelsData, threadsData] = await Promise.all([
        CommunityHubAPI.getChannels(),
        CommunityHubAPI.getThreads()
      ]);
      setChannels(channelsData);
      setThreads(threadsData);
    } catch (error) {
      Alert.alert('Error', 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const joinChannel = async (channelId) => {
    try {
      await CommunityHubAPI.joinChannel(channelId);
      loadData(); // Refresh data
    } catch (error) {
      Alert.alert('Error', 'Failed to join channel');
    }
  };

  const renderChannel = ({ item }) => (
    <View style={styles.channelItem}>
      <Text style={styles.channelTitle}>{item.name}</Text>
      <Text style={styles.channelDescription}>{item.description}</Text>
      <TouchableOpacity
        style={styles.button}
        onPress={() => joinChannel(item.id)}
        disabled={item.is_member}
      >
        <Text style={styles.buttonText}>
          {item.is_member ? 'Joined' : 'Join Channel'}
        </Text>
      </TouchableOpacity>
    </View>
  );

  const renderThread = ({ item }) => (
    <View style={styles.threadItem}>
      <Text style={styles.threadTitle}>{item.title}</Text>
      <Text style={styles.threadAuthor}>By {item.author.username}</Text>
      {item.posts.map(post => (
        <View key={post.id} style={styles.postItem}>
          <Text style={styles.postContent}>{post.content}</Text>
          <Text style={styles.postAuthor}>
            {post.author.username} - {new Date(post.created_at).toLocaleDateString()}
          </Text>
        </View>
      ))}
    </View>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Community Hub</Text>
      
      <Text style={styles.sectionTitle}>Channels</Text>
      <FlatList
        data={channels}
        renderItem={renderChannel}
        keyExtractor={item => item.id.toString()}
        refreshing={loading}
        onRefresh={loadData}
      />

      <Text style={styles.sectionTitle}>Threads</Text>
      <FlatList
        data={threads}
        renderItem={renderThread}
        keyExtractor={item => item.id.toString()}
        refreshing={loading}
        onRefresh={loadData}
      />
    </View>
  );
};

const styles = {
  container: {
    flex: 1,
    padding: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginTop: 16,
    marginBottom: 8,
  },
  channelItem: {
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  channelTitle: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  channelDescription: {
    fontSize: 14,
    color: '#666',
    marginVertical: 4,
  },
  button: {
    backgroundColor: '#007bff',
    padding: 8,
    borderRadius: 4,
    marginTop: 8,
  },
  buttonText: {
    color: 'white',
    textAlign: 'center',
  },
  threadItem: {
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  threadTitle: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  threadAuthor: {
    fontSize: 12,
    color: '#666',
    marginBottom: 8,
  },
  postItem: {
    marginLeft: 16,
    marginBottom: 8,
  },
  postContent: {
    fontSize: 14,
  },
  postAuthor: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
};

export default CommunityHubScreen;
```

---

## Push Notifications (Expo)

### Setup
```bash
npm install expo-notifications expo-device expo-constants
```

### Implementation
```javascript
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import Constants from 'expo-constants';

// Register for push notifications
const registerForPushNotifications = async () => {
  if (!Device.isDevice) {
    console.log('Must use physical device for push notifications');
    return;
  }

  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;

  if (existingStatus !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== 'granted') {
    console.log('Failed to get push token for push notification!');
    return;
  }

  const token = (await Notifications.getExpoPushTokenAsync()).data;
  
  // Register device with backend
  await CommunityHubAPI.registerDevice({
    device_id: Constants.deviceId,
    platform: Platform.OS,
    push_token: token,
    is_active: true
  });

  return token;
};
```

---

This documentation provides everything needed to integrate the Community Hub API with both Vue.js and Expo/React Native frontends. The API supports real-time features, multilingual content, and comprehensive community management functionality.
