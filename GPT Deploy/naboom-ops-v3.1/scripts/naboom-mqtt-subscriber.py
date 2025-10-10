#!/usr/bin/env python3
import os, ssl, logging, uuid
import paho.mqtt.client as mqtt
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
HOST = os.getenv("MQTT_FLOW_HOST","naboomneighbornet.net.za")
WS_URL_PATH = os.getenv("MQTT_WS_PATH","/mqtt")
TCP_HOST = os.getenv("MQTT_TCP_HOST","127.0.0.1"); TCP_PORT = int(os.getenv("MQTT_TCP_PORT","1883"))
USER = os.getenv("MQTT_USER"); PASS = os.getenv("MQTT_PASSWORD")
TOPICS = [t.strip() for t in os.getenv("MQTT_TOPICS","events/#").split(",")]
def on_connect(c, u, f, rc, p=None):
    logging.info("Connected rc=%s", rc); [c.subscribe(t, qos=1) for t in TOPICS]
def on_message(c, u, m):
    logging.info("MQTT %s: %s", m.topic, m.payload[:200])
def try_ws_then_tcp():
    try:
        c = mqtt.Client(transport="websockets", protocol=mqtt.MQTTv311)
        c.username_pw_set(USER, PASS)
        c.tls_set()  # verify
        c.ws_set_options(path=WS_URL_PATH)
        c.on_connect = on_connect; c.on_message = on_message
        c.connect(HOST, 443, keepalive=60); c.loop_forever()
    except Exception as e:
        logging.warning("WS failed: %s; falling back to TCP %s:%s", e, TCP_HOST, TCP_PORT)
        c2 = mqtt.Client(protocol=mqtt.MQTTv311)
        c2.username_pw_set(USER, PASS)
        c2.on_connect = on_connect; c2.on_message = on_message
        c2.connect(TCP_HOST, TCP_PORT, keepalive=60); c2.loop_forever()
if __name__ == "__main__":
    try_ws_then_tcp()
