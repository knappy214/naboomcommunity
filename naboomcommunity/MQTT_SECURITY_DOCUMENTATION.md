# MQTT Security Implementation Documentation

## Overview

This document describes the complete MQTT authentication and security implementation for the Naboom Community platform. The implementation provides secure, authenticated MQTT communication with optional SSL/TLS encryption.

## Security Features Implemented

### ✅ Authentication
- **Password-based authentication** using Mosquitto's password file
- **User credentials**: `naboom-mqtt` with secure password
- **Anonymous access disabled** across all listeners
- **Required authentication** for all MQTT connections

### ✅ Authorization (ACL)
- **Topic-based access control** using Access Control Lists
- **Granular permissions** for read/write operations
- **User-specific access** to `naboom/#` topic hierarchy
- **Anonymous users denied** access to all topics

### ✅ Encryption
- **SSL/TLS support** for secure MQTT connections
- **Self-signed certificates** for development (production should use CA-signed)
- **Secure WebSocket support** for web applications
- **Certificate management** with proper file permissions

### ✅ Django Integration
- **Settings configuration** with environment variable support
- **Secure MQTT service** using aiomqtt for async operations
- **Automatic credential handling** from Django settings
- **Error handling and retry logic** for robust connections

## Configuration Files

### Mosquitto Configuration (`/etc/mosquitto/mosquitto.conf`)

```ini
# Global settings
persistence true
persistence_location /var/lib/mosquitto/
log_dest file /var/log/mosquitto/mosquitto.log
per_listener_settings true

# Disable anonymous access globally
allow_anonymous false

# Regular MQTT listener (port 1883)
listener 1883 127.0.0.1
protocol mqtt
password_file /etc/mosquitto/passwd
acl_file /etc/mosquitto/acl

# WebSockets listener (port 8083)
listener 8083 127.0.0.1
protocol websockets
password_file /etc/mosquitto/passwd
acl_file /etc/mosquitto/acl
http_dir /usr/share/mosquitto/www

# SSL/TLS MQTT listener (port 8883)
listener 8883 127.0.0.1
protocol mqtt
cafile /etc/mosquitto/certs/server.crt
certfile /etc/mosquitto/certs/server.crt
keyfile /etc/mosquitto/certs/server.key
password_file /etc/mosquitto/passwd
acl_file /etc/mosquitto/acl

# Secure WebSockets listener (port 8884)
listener 8884 127.0.0.1
protocol websockets
cafile /etc/mosquitto/certs/server.crt
certfile /etc/mosquitto/certs/server.crt
keyfile /etc/mosquitto/certs/server.key
password_file /etc/mosquitto/passwd
acl_file /etc/mosquitto/acl
http_dir /usr/share/mosquitto/www
```

### Password File (`/etc/mosquitto/passwd`)

```
naboom-mqtt:$7$101$bLFQ29a0yGGy3HgK$HgVuC2WYqWBqJ2w8by3mOl61v8YHiiiiHmugcYUG0ELFwnmPb8/6dHwSCLrz1M6n13KlotZzJ+VNNOWLu/l3Rw==
```

**File Permissions**: `640` (readable by mosquitto user only)

### Access Control List (`/etc/mosquitto/acl`)

```
user naboom-mqtt
topic read naboom/#
topic write naboom/#
```

**File Permissions**: `640` (readable by mosquitto user only)

### SSL Certificates (`/etc/mosquitto/certs/`)

- **Server Certificate**: `server.crt` (644 permissions)
- **Private Key**: `server.key` (600 permissions)
- **CA Certificate**: `server.crt` (self-signed for development)

## Django Settings

### Base Settings (`naboomcommunity/settings/base.py`)

```python
# ============================================================================
# MQTT CONFIGURATION
# ============================================================================

# MQTT Broker Settings (with authentication)
MQTT_HOST = os.getenv('MQTT_HOST', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
MQTT_SSL_PORT = int(os.getenv('MQTT_SSL_PORT', '8883'))
MQTT_USERNAME = os.getenv('MQTT_USERNAME', 'naboom-mqtt')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', 'NaboomMQTT2024!')
MQTT_CLIENT_ID = os.getenv('MQTT_CLIENT_ID', 'naboom-community')
MQTT_KEEPALIVE = int(os.getenv('MQTT_KEEPALIVE', '60'))
MQTT_USE_SSL = os.getenv('MQTT_USE_SSL', 'false').lower() in ('true', '1', 'yes')

# MQTT Topic Configuration
MQTT_TOPIC_PREFIX = 'naboom'
MQTT_COMMUNITY_TOPIC = f'{MQTT_TOPIC_PREFIX}/community'
MQTT_SYSTEM_TOPIC = f'{MQTT_TOPIC_PREFIX}/system'
MQTT_NOTIFICATION_TOPIC = f'{MQTT_TOPIC_PREFIX}/notifications'
MQTT_ALERT_TOPIC = f'{MQTT_TOPIC_PREFIX}/alerts'
```

### Environment Variables

```bash
# MQTT Configuration
MQTT_HOST=localhost
MQTT_PORT=1883
MQTT_SSL_PORT=8883
MQTT_USERNAME=naboom-mqtt
MQTT_PASSWORD=NaboomMQTT2024!
MQTT_CLIENT_ID=naboom-community
MQTT_USE_SSL=false
```

## Usage

### Running the Secure MQTT Service

```bash
# Activate virtual environment
cd /var/www/naboomcommunity/naboomcommunity
source venv/bin/activate

# Run regular MQTT service
python manage.py run_mqtt_service_secure

# Run with SSL/TLS
python manage.py run_mqtt_service_secure --ssl
```

### Testing MQTT Connections

#### Regular MQTT (Port 1883)
```bash
# Publish message
mosquitto_pub -h localhost -u naboom-mqtt -P NaboomMQTT2024! -t "naboom/test" -m "Test message"

# Subscribe to messages
mosquitto_sub -h localhost -u naboom-mqtt -P NaboomMQTT2024! -t "naboom/#"
```

#### SSL/TLS MQTT (Port 8883)
```bash
# Publish message with SSL
mosquitto_pub -h localhost -p 8883 --cafile /etc/mosquitto/certs/server.crt -u naboom-mqtt -P NaboomMQTT2024! -t "naboom/test" -m "SSL test message"

# Subscribe with SSL
mosquitto_sub -h localhost -p 8883 --cafile /etc/mosquitto/certs/server.crt -u naboom-mqtt -P NaboomMQTT2024! -t "naboom/#"
```

### Python Client Usage

```python
import asyncio
import aiomqtt
from django.conf import settings

async def mqtt_client_example():
    """Example of using MQTT client with authentication."""
    
    # Create client with authentication
    client = aiomqtt.Client(
        hostname=settings.MQTT_HOST,
        port=settings.MQTT_PORT,
        username=settings.MQTT_USERNAME,
        password=settings.MQTT_PASSWORD,
        identifier=settings.MQTT_CLIENT_ID,
    )
    
    async with client:
        # Publish message
        await client.publish("naboom/test", "Hello from Python!")
        
        # Subscribe to topic
        await client.subscribe("naboom/#")
        
        # Process messages
        async for message in client.messages:
            print(f"Received: {message.topic} -> {message.payload}")
```

## Security Considerations

### Production Deployment

1. **Replace Self-Signed Certificates**
   - Use CA-signed certificates for production
   - Implement proper certificate rotation
   - Monitor certificate expiration

2. **Password Management**
   - Use strong, unique passwords
   - Implement password rotation policy
   - Store passwords securely (environment variables)

3. **Network Security**
   - Configure firewall rules for MQTT ports
   - Use VPN for remote access
   - Monitor network traffic

4. **Monitoring and Logging**
   - Set up MQTT broker monitoring
   - Log authentication attempts
   - Monitor for suspicious activity

### Security Best Practices

1. **Regular Updates**
   - Keep Mosquitto broker updated
   - Update certificates before expiration
   - Apply security patches promptly

2. **Access Control**
   - Review ACL permissions regularly
   - Remove unused user accounts
   - Implement least privilege principle

3. **Monitoring**
   - Monitor connection attempts
   - Log all MQTT operations
   - Set up alerts for security events

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Check password file permissions
   - Verify username/password combination
   - Ensure password file is readable by mosquitto user

2. **ACL Permission Denied**
   - Verify ACL file syntax
   - Check topic patterns in ACL file
   - Ensure user has proper permissions

3. **SSL Connection Issues**
   - Verify certificate file permissions
   - Check certificate validity
   - Ensure proper SSL context configuration

### Debug Commands

```bash
# Check Mosquitto status
sudo systemctl status mosquitto

# View Mosquitto logs
sudo tail -f /var/log/mosquitto/mosquitto.log

# Test configuration
sudo mosquitto -c /etc/mosquitto/mosquitto.conf -v

# Check file permissions
ls -la /etc/mosquitto/
```

## Maintenance

### Regular Tasks

1. **Certificate Management**
   - Monitor certificate expiration
   - Renew certificates before expiration
   - Update certificate files

2. **Password Rotation**
   - Change passwords regularly
   - Update password file
   - Update Django settings

3. **Log Rotation**
   - Configure log rotation for Mosquitto logs
   - Monitor log file sizes
   - Archive old logs

### Backup Procedures

1. **Configuration Backup**
   ```bash
   sudo cp /etc/mosquitto/mosquitto.conf /backup/mosquitto.conf.$(date +%Y%m%d)
   sudo cp /etc/mosquitto/passwd /backup/mosquitto.passwd.$(date +%Y%m%d)
   sudo cp /etc/mosquitto/acl /backup/mosquitto.acl.$(date +%Y%m%d)
   ```

2. **Certificate Backup**
   ```bash
   sudo cp -r /etc/mosquitto/certs /backup/mosquitto-certs.$(date +%Y%m%d)
   ```

## Support

For issues or questions regarding the MQTT security implementation:

1. Check the troubleshooting section above
2. Review Mosquitto logs for error messages
3. Verify configuration file syntax
4. Test with command-line tools first
5. Contact the development team for assistance

## References

- [Eclipse Mosquitto Documentation](https://mosquitto.org/documentation/)
- [aiomqtt Documentation](https://aiomqtt.readthedocs.io/)
- [Django Settings Documentation](https://docs.djangoproject.com/en/stable/topics/settings/)
- [MQTT Security Best Practices](https://mqtt.org/security/)
