#!/usr/bin/env python3
"""Debug ACL permissions for MQTT."""
import asyncio
import aiomqtt

async def test_acl_debug():
    """Debug ACL permissions."""
    print("Testing ACL permissions...")
    
    try:
        async with aiomqtt.Client(
            hostname='localhost',
            port=1883,
            username='naboom-mqtt',
            password='NaboomMQTT2024!',
            identifier='acl-debug-test'
        ) as client:
            print("Connected successfully")
            
            # Try to publish to unauthorized topic
            try:
                await client.publish("unauthorized/topic", payload="test", qos=1)
                print("❌ FAIL: Published to unauthorized topic")
            except Exception as e:
                print(f"✅ PASS: ACL denied - {e}")
                
            # Try to publish to authorized topic
            try:
                await client.publish("naboom/test/acl", payload="test", qos=1)
                print("✅ PASS: Published to authorized topic")
            except Exception as e:
                print(f"❌ FAIL: Could not publish to authorized topic - {e}")
                
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_acl_debug())
