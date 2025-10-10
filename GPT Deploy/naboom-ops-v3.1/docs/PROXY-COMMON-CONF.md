# Corrected Proxy Common Configuration - HTTP/3 Optimized

## Critical Issues Fixed:

1. **HTTP/3 Variable Safety**: Removed unverified nginx variables
2. **Conditional Header Setting**: Context-aware header configuration  
3. **Buffer Optimization**: Right-sized buffers for different request types
4. **Timeout Standardization**: Consistent timeout values across contexts
5. **Performance Header Reduction**: Removed unnecessary monitoring headers
6. **WebSocket Header Separation**: Proper conditional WebSocket support

---

## Corrected Proxy Configuration File

**Deploy to:** `/etc/nginx/snippets/proxy-common.conf`

```nginx
# ============================================================================
# ENHANCED PROXY CONFIGURATION SNIPPET - HTTP/3 OPTIMIZED & CORRECTED
# ============================================================================
# File: /etc/nginx/snippets/proxy-common.conf
# 
# Corrected for production reliability:
#   ✅ Verified HTTP/3 variables only
#   ✅ Context-aware header setting
#   ✅ Right-sized buffers for HTTP/3 multiplexing
#   ✅ Standardized timeout settings
#   ✅ Reduced header overhead
# 
# Usage in location blocks:
#   location /api/ {
#       proxy_pass http://upstream_name;
#       include /etc/nginx/snippets/proxy-common.conf;
#   }
# ============================================================================

# ============================================================================
# PROTOCOL AND CONNECTION SETTINGS (HTTP/3 Enhanced)
# ============================================================================

# Use HTTP/1.1 for upstream connections (backend compatibility)
proxy_http_version 1.1;

# Enhanced connection management for HTTP/3 multiplexing
proxy_set_header Connection "";

# Enable keep-alive with extended settings for HTTP/3 backend pools
proxy_socket_keepalive on;

# ============================================================================
# CORE PROXY HEADERS (Essential Only)
# ============================================================================

# Standard proxy headers - verified and essential
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;

# Enhanced headers for HTTP/3 context
proxy_set_header X-Forwarded-Host $host;
proxy_set_header X-Forwarded-Port $server_port;
proxy_set_header X-Forwarded-Server $host;

# HTTP/3 protocol information for backend processing - SAFE VARIABLES ONLY
proxy_set_header X-HTTP-Version $server_protocol;
proxy_set_header X-Original-URI $request_uri;
proxy_set_header X-Original-Method $request_method;

# Request tracing (essential for debugging)
proxy_set_header X-Request-ID $request_id;

# SSL context information
proxy_set_header X-SSL-Protocol $ssl_protocol;
proxy_set_header X-SSL-Cipher $ssl_cipher;

# ============================================================================
# TIMEOUT SETTINGS (Standardized for HTTP/3)
# ============================================================================

# Standardized timeouts for HTTP/3 workloads
proxy_connect_timeout 10s;        # Connection establishment
proxy_send_timeout 120s;          # Request sending
proxy_read_timeout 120s;          # Response reading

# ============================================================================
# BUFFER SETTINGS (Optimized for HTTP/3)
# ============================================================================

# Enhanced buffering for HTTP/3 multiplexed streams
proxy_buffering on;

# Right-sized buffer configuration for HTTP/3
proxy_buffer_size 16k;            # Response header buffer
proxy_buffers 16 16k;            # Response body buffers
proxy_busy_buffers_size 32k;     # Busy buffer for HTTP/3

# ============================================================================
# ADVANCED PROXY SETTINGS (Production Optimized)
# ============================================================================

# Disable proxy redirect modification (maintain HTTP/3 context)
proxy_redirect off;

# Request body handling optimized for HTTP/3
proxy_request_buffering on;

# HTTP/3 stream management
proxy_max_temp_file_size 1024m;   # Reasonable limit for temp files

# ============================================================================
# SECURITY HEADERS (Backend Communication)
# ============================================================================

# Remove sensitive server information from backend responses
proxy_hide_header Server;
proxy_hide_header X-Powered-By;
proxy_hide_header X-AspNet-Version;

# Add security context for backend processing
proxy_set_header X-Secure-Transport "HTTPS";
proxy_set_header X-TLS-Version $ssl_protocol;

# ============================================================================
# ERROR HANDLING (HTTP/3 Optimized)
# ============================================================================

# Enhanced upstream failure handling for HTTP/3 high availability
proxy_next_upstream error timeout http_502 http_503 http_504;
proxy_next_upstream_tries 3;
proxy_next_upstream_timeout 30s;

# ============================================================================
# COMPRESSION HANDLING (HTTP/3 Compatible)
# ============================================================================

# Pass through compression headers
proxy_set_header Accept-Encoding $http_accept_encoding;

# ============================================================================
# DJANGO 5.2 SPECIFIC OPTIMIZATIONS
# ============================================================================

# Django CSRF and session handling with secure cookies
proxy_cookie_path / "/; Secure; HttpOnly; SameSite=Strict";

# Django internationalization support
proxy_set_header Accept-Language $http_accept_language;

# ============================================================================
# CONDITIONAL SETTINGS FOR SPECIFIC USE CASES
# ============================================================================

# Note: These settings should be applied in specific location blocks as needed:

# FOR WEBSOCKET CONNECTIONS (add these in WebSocket locations):
#   proxy_set_header Upgrade $http_upgrade;
#   proxy_set_header Connection $connection_upgrade;
#   proxy_read_timeout 24h;
#   proxy_send_timeout 24h;
#   proxy_buffering off;

# FOR SERVER-SENT EVENTS (add these in SSE locations):
#   proxy_buffering off;
#   proxy_cache off;
#   proxy_read_timeout 24h;
#   proxy_send_timeout 24h;
#   add_header X-Accel-Buffering no;
#   add_header Cache-Control "no-cache, no-store, must-revalidate" always;

# FOR API ENDPOINTS WITH CACHING (add these in API locations):
#   proxy_cache api_cache;
#   proxy_cache_valid 200 10m;
#   proxy_cache_key "$scheme$request_method$host$request_uri";
#   add_header X-Cache-Status $upstream_cache_status always;

# FOR HEALTH CHECKS (add these in health check locations):
#   proxy_connect_timeout 2s;
#   proxy_read_timeout 5s;
#   proxy_send_timeout 5s;
#   add_header Cache-Control "no-cache, no-store, must-revalidate" always;

# FOR FILE UPLOADS (add these in upload locations):
#   proxy_connect_timeout 30s;
#   proxy_read_timeout 300s;
#   proxy_send_timeout 300s;
#   proxy_request_buffering off;
#   client_max_body_size 500M;

# ============================================================================
# EMERGENCY SYSTEM OPTIMIZATION (Panic Platform)
# ============================================================================

# Emergency response headers (add in panic system locations):
#   proxy_set_header X-Emergency-Priority "HIGH";
#   proxy_set_header X-Network-Reliability "HTTP3-ENHANCED";

# ============================================================================
# MOBILE OPTIMIZATION HEADERS
# ============================================================================

# Mobile device optimization headers
proxy_set_header X-Mobile-Optimized "true";
proxy_set_header X-Network-Type "HTTP3-QUIC";

# ============================================================================
# USAGE EXAMPLES FOR HTTP/3 OPTIMIZATION
# ============================================================================

# Example 1: Standard API endpoint
#   location /api/ {
#       proxy_pass http://naboom_app;
#       include /etc/nginx/snippets/proxy-common.conf;
#       # Additional API-specific settings here
#   }

# Example 2: Emergency panic API
#   location /panic/api/ {
#       proxy_pass http://naboom_app;
#       include /etc/nginx/snippets/proxy-common.conf;
#       # Override timeouts for emergency response
#       proxy_connect_timeout 2s;
#       proxy_read_timeout 45s;
#       proxy_set_header X-Emergency-Priority "CRITICAL";
#   }

# Example 3: WebSocket endpoint  
#   location /ws/ {
#       proxy_pass http://naboom_ws;
#       include /etc/nginx/snippets/proxy-common.conf;
#       # WebSocket specific overrides
#       proxy_set_header Upgrade $http_upgrade;
#       proxy_set_header Connection $connection_upgrade;
#       proxy_buffering off;
#       proxy_read_timeout 24h;
#       proxy_send_timeout 24h;
#   }

# Example 4: Server-Sent Events
#   location /stream/ {
#       proxy_pass http://naboom_app;
#       include /etc/nginx/snippets/proxy-common.conf;
#       # SSE specific overrides
#       proxy_buffering off;
#       proxy_cache off;
#       add_header X-Accel-Buffering no;
#       add_header Cache-Control "no-cache, no-store, must-revalidate" always;
#   }

# ============================================================================
# PERFORMANCE BENEFITS OF THIS CORRECTED CONFIGURATION
# ============================================================================

# This HTTP/3 optimized and corrected proxy configuration provides:
# ✓ Verified nginx variables only - prevents configuration errors
# ✓ Right-sized buffers for HTTP/3 multiplexing performance
# ✓ Standardized timeouts for consistent behavior
# ✓ Reduced header overhead for better performance
# ✓ Context-aware configuration for different endpoint types
# ✓ Production-ready error handling
# ✓ Security-focused header management
# ✓ Mobile and emergency system optimization
# ✓ Future-proof settings for HTTP/3 evolution

# ============================================================================
# DEPLOYMENT VERIFICATION
# ============================================================================

# After deploying this configuration:
# 1. Test nginx configuration: sudo nginx -t
# 2. Check proxy headers: curl -I https://your-domain/api/health
# 3. Monitor error logs: tail -f /var/log/nginx/error.log
# 4. Verify HTTP/3 functionality: check Alt-Svc headers
# 5. Test different endpoint types (API, WebSocket, SSE)

# ============================================================================
# END OF CORRECTED HTTP/3 OPTIMIZED PROXY CONFIGURATION
# ============================================================================
```

---

## Critical Improvements Made

### 1. **HTTP/3 Variable Safety**
- **Removed unverified variables** like `$quic_version`, `$http3`
- **Kept only confirmed variables** that exist in Nginx 1.29.1
- **Added safe protocol detection** using `$server_protocol`

### 2. **Buffer Right-Sizing**
- **Reduced buffer sizes** from 32k to 16k for better memory efficiency
- **Optimized buffer count** for HTTP/3 multiplexing
- **Balanced performance vs memory usage**

### 3. **Timeout Standardization**
- **Consistent timeout values** across all contexts
- **Reasonable defaults** that work for most use cases
- **Context-specific overrides** documented for special cases

### 4. **Header Optimization**
- **Removed performance monitoring headers** that create overhead
- **Kept essential headers only** for functionality
- **Added proper SSL context information**

### 5. **Context-Aware Configuration**
- **Conditional settings documentation** for different endpoint types
- **Clear separation** between WebSocket and regular proxy usage
- **Specific examples** for each use case

### 6. **Production Reliability**
- **Error handling optimization** for HTTP/3 high availability
- **Security header management** for backend communication
- **Mobile optimization** without excessive overhead

---

## Usage Examples

### Emergency API Endpoint
```nginx
location /panic/api/ {
    proxy_pass http://naboom_app;
    include /etc/nginx/snippets/proxy-common.conf;
    
    # Emergency-specific overrides
    proxy_connect_timeout 2s;
    proxy_read_timeout 45s;
    proxy_set_header X-Emergency-Priority "CRITICAL";
}
```

### WebSocket Endpoint
```nginx
location /ws/ {
    proxy_pass http://naboom_ws;
    include /etc/nginx/snippets/proxy-common.conf;
    
    # WebSocket-specific overrides
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;
    proxy_buffering off;
    proxy_read_timeout 24h;
    proxy_send_timeout 24h;
}
```

### Cached API Endpoint
```nginx
location /api/v1/ {
    proxy_pass http://naboom_app;
    include /etc/nginx/snippets/proxy-common.conf;
    
    # Caching-specific settings
    proxy_cache api_cache;
    proxy_cache_valid 200 10m;
    proxy_cache_key "$scheme$request_method$host$request_uri";
    add_header X-Cache-Status $upstream_cache_status always;
}
```

---

## Deployment Instructions

1. **Deploy corrected configuration:**
   ```bash
   sudo cp corrected-proxy-common.conf /etc/nginx/snippets/proxy-common.conf
   ```

2. **Test configuration:**
   ```bash
   sudo nginx -t
   ```

3. **Reload nginx:**
   ```bash
   sudo systemctl reload nginx
   ```

4. **Verify headers:**
   ```bash
   curl -I https://naboomneighbornet.net.za/api/health
   ```

This corrected proxy configuration eliminates all the **dangerous unverified variables**, provides **production-ready defaults**, and offers **context-aware optimization** for your HTTP/3 emergency response platform.