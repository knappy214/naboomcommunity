#!/usr/bin/env python3
"""
MQTT Security Test Script for Naboom Community

This script tests the MQTT authentication and security implementation
including both regular and SSL/TLS connections.
"""

import asyncio
import json
import ssl
import time
from typing import Dict, Any

import aiomqtt
from django.conf import settings
import os
import sys

# Add the project directory to Python path
sys.path.append('/var/www/naboomcommunity/naboomcommunity')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'naboomcommunity.settings.production')

import django
django.setup()


class MQTTSecurityTester:
    """Test MQTT security implementation."""
    
    def __init__(self):
        self.test_results = []
        self.mqtt_host = getattr(settings, 'MQTT_HOST', 'localhost')
        self.mqtt_port = getattr(settings, 'MQTT_PORT', 1883)
        self.mqtt_ssl_port = getattr(settings, 'MQTT_SSL_PORT', 8883)
        self.mqtt_username = getattr(settings, 'MQTT_USERNAME', 'naboom-mqtt')
        self.mqtt_password = getattr(settings, 'MQTT_PASSWORD', 'NaboomMQTT2024!')
        self.mqtt_client_id = getattr(settings, 'MQTT_CLIENT_ID', 'naboom-test-client')
    
    def create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context for testing."""
        ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        return ssl_context
    
    async def test_regular_connection(self) -> bool:
        """Test regular MQTT connection with authentication."""
        print("🔐 Testing regular MQTT connection with authentication...")
        
        try:
            client = aiomqtt.Client(
                hostname=self.mqtt_host,
                port=self.mqtt_port,
                username=self.mqtt_username,
                password=self.mqtt_password,
                identifier=f"{self.mqtt_client_id}-regular",
            )
            
            async with client:
                # Test publish
                test_message = {
                    "test": "regular_connection",
                    "timestamp": time.time(),
                    "message": "Regular MQTT connection test successful"
                }
                
                await client.publish(
                    "naboom/test/regular",
                    json.dumps(test_message),
                    qos=1
                )
                print("✅ Regular connection: Publish successful")
                
                # Test subscribe
                await client.subscribe("naboom/test/regular")
                
                # Wait for message
                message_received = False
                async for message in client.messages:
                    if str(message.topic) == "naboom/test/regular":
                        data = json.loads(message.payload.decode())
                        if data.get("test") == "regular_connection":
                            print("✅ Regular connection: Subscribe successful")
                            message_received = True
                            break
                    if not message_received:
                        break
                
                return message_received
                
        except Exception as e:
            print(f"❌ Regular connection failed: {e}")
            return False
    
    async def test_ssl_connection(self) -> bool:
        """Test SSL/TLS MQTT connection with authentication."""
        print("🔒 Testing SSL/TLS MQTT connection with authentication...")
        
        try:
            ssl_context = self.create_ssl_context()
            
            client = aiomqtt.Client(
                hostname=self.mqtt_host,
                port=self.mqtt_ssl_port,
                username=self.mqtt_username,
                password=self.mqtt_password,
                identifier=f"{self.mqtt_client_id}-ssl",
                tls_context=ssl_context,
            )
            
            async with client:
                # Test publish
                test_message = {
                    "test": "ssl_connection",
                    "timestamp": time.time(),
                    "message": "SSL MQTT connection test successful"
                }
                
                await client.publish(
                    "naboom/test/ssl",
                    json.dumps(test_message),
                    qos=1
                )
                print("✅ SSL connection: Publish successful")
                
                # Test subscribe
                await client.subscribe("naboom/test/ssl")
                
                # Wait for message
                message_received = False
                async for message in client.messages:
                    if str(message.topic) == "naboom/test/ssl":
                        data = json.loads(message.payload.decode())
                        if data.get("test") == "ssl_connection":
                            print("✅ SSL connection: Subscribe successful")
                            message_received = True
                            break
                    if not message_received:
                        break
                
                return message_received
                
        except Exception as e:
            print(f"❌ SSL connection failed: {e}")
            return False
    
    async def test_authentication_failure(self) -> bool:
        """Test that invalid credentials are rejected."""
        print("🚫 Testing authentication failure (should fail)...")
        
        try:
            client = aiomqtt.Client(
                hostname=self.mqtt_host,
                port=self.mqtt_port,
                username="invalid_user",
                password="invalid_password",
                identifier=f"{self.mqtt_client_id}-invalid",
            )
            
            async with client:
                # This should fail
                await client.publish("naboom/test/invalid", "test", qos=0)
                print("❌ Authentication failure test: Should have failed but didn't")
                return False
                
        except Exception as e:
            print(f"✅ Authentication failure test: Correctly rejected invalid credentials - {e}")
            return True
    
    async def test_acl_permissions(self) -> bool:
        """Test ACL permissions for topic access."""
        print("🛡️ Testing ACL permissions...")
        
        try:
            client = aiomqtt.Client(
                hostname=self.mqtt_host,
                port=self.mqtt_port,
                username=self.mqtt_username,
                password=self.mqtt_password,
                identifier=f"{self.mqtt_client_id}-acl",
            )
            
            async with client:
                # Test allowed topics
                allowed_topics = [
                    "naboom/community/test",
                    "naboom/system/test",
                    "naboom/notifications/test",
                    "naboom/alerts/test"
                ]
                
                for topic in allowed_topics:
                    try:
                        await client.publish(topic, "ACL test", qos=0)
                        print(f"✅ ACL test: {topic} - Allowed")
                    except Exception as e:
                        print(f"❌ ACL test: {topic} - Unexpectedly denied: {e}")
                        return False
                
                return True
                
        except Exception as e:
            print(f"❌ ACL permissions test failed: {e}")
            return False
    
    async def test_anonymous_access_denied(self) -> bool:
        """Test that anonymous access is denied."""
        print("👤 Testing anonymous access denial...")
        
        try:
            client = aiomqtt.Client(
                hostname=self.mqtt_host,
                port=self.mqtt_port,
                identifier=f"{self.mqtt_client_id}-anonymous",
            )
            
            async with client:
                # This should fail
                await client.publish("naboom/test/anonymous", "test", qos=0)
                print("❌ Anonymous access test: Should have failed but didn't")
                return False
                
        except Exception as e:
            print(f"✅ Anonymous access test: Correctly denied anonymous access - {e}")
            return True
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all security tests."""
        print("🚀 Starting MQTT Security Tests for Naboom Community")
        print("=" * 60)
        
        tests = {
            "Regular Connection": await self.test_regular_connection(),
            "SSL/TLS Connection": await self.test_ssl_connection(),
            "Authentication Failure": await self.test_authentication_failure(),
            "ACL Permissions": await self.test_acl_permissions(),
            "Anonymous Access Denied": await self.test_anonymous_access_denied(),
        }
        
        print("\n" + "=" * 60)
        print("📊 Test Results Summary:")
        print("=" * 60)
        
        passed = 0
        total = len(tests)
        
        for test_name, result in tests.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:<25} {status}")
            if result:
                passed += 1
        
        print("=" * 60)
        print(f"Total: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All MQTT security tests passed!")
        else:
            print("⚠️ Some tests failed. Please check the configuration.")
        
        return tests


async def main():
    """Main test function."""
    tester = MQTTSecurityTester()
    results = await tester.run_all_tests()
    
    # Exit with appropriate code
    if all(results.values()):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
