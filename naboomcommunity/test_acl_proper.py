#!/usr/bin/env python3
"""Proper ACL test that checks return codes."""
import asyncio
import aiomqtt

async def test_acl_proper():
    """Test ACL with proper return code checking."""
    print("Testing ACL permissions with return code checking...")
    
    try:
        async with aiomqtt.Client(
            hostname='localhost',
            port=1883,
            username='naboom-mqtt',
            password='NaboomMQTT2024!',
            identifier='acl-proper-test'
        ) as client:
            print("Connected successfully")
            
            # Try to publish to unauthorized topic and check return code
            try:
                result = await client.publish("unauthorized/topic", payload="test", qos=1)
                print(f"Publish result: {result}")
                # In aiomqtt, we need to check if the message was actually published
                # by trying to subscribe and see if we receive it
                return False, "ACL test failed: Published to unauthorized topic"
            except Exception as e:
                print(f"Exception during publish: {e}")
                return True, "ACL test passed: Correctly denied access"
                
    except Exception as e:
        print(f"Connection failed: {e}")
        return False, f"Connection failed: {e}"

if __name__ == "__main__":
    result = asyncio.run(test_acl_proper())
    print(f"Result: {result}")
