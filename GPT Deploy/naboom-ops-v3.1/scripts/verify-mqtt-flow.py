#!/usr/bin/env python3
import os, ssl, time, sys, uuid
import paho.mqtt.client as mqtt
HOST = os.getenv("MQTT_FLOW_HOST", "naboomneighbornet.net.za")
PORT = int(os.getenv("MQTT_FLOW_PORT", "443"))
PATH = os.getenv("MQTT_FLOW_PATH", "/mqtt")
USER = os.getenv("MQTT_USER", "")
PASS = os.getenv("MQTT_PASSWORD", "")
TOPIC_BASE = os.getenv("MQTT_FLOW_TOPIC_BASE", "ops/smoke")
TIMEOUT = int(os.getenv("MQTT_FLOW_TIMEOUT", "10"))
topic = f"{TOPIC_BASE}/{uuid.uuid4().hex}"; payload = uuid.uuid4().hex
state = {"sub": False, "msg": False}
def on_connect(c,u,f,rc,props=None):
    if rc != 0: print("Connect failed rc", rc); sys.exit(2)
    c.subscribe(topic, qos=1)
def on_subscribe(c,u,mid,granted_qos,props=None):
    state["sub"] = True; c.publish(topic, payload, qos=1)
def on_message(c,u,msg):
    if msg.topic == topic and msg.payload.decode() == payload:
        state["msg"] = True; c.disconnect()
client = mqtt.Client(transport="websockets", protocol=mqtt.MQTTv311)
client.username_pw_set(USER, PASS)
client.tls_set()  # system CAs
client.ws_set_options(path=PATH)
client.on_connect = on_connect; client.on_subscribe = on_subscribe; client.on_message = on_message
client.connect(HOST, PORT, keepalive=20)
t0 = time.time(); client.loop_start()
try:
    while time.time() - t0 < TIMEOUT and not state["msg"]:
        time.sleep(0.2)
finally:
    client.loop_stop()
if state["sub"] and state["msg"]:
    print("MQTT FLOW: SUCCESS topic=", topic); sys.exit(0)
else:
    print("MQTT FLOW: FAILED (subscribed=%s, got=%s, timeout=%ss)" % (state["sub"], state["msg"], TIMEOUT)); sys.exit(1)
