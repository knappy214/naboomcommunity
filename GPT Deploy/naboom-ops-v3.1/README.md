# Naboom Ops (v3.1)

## Structure
- docs/ — Reference guides you supplied (corrected)
- nginx/ — HTTP/3 site + common proxy snippet + conf.d core include
- mosquitto/ — Broker config + ACL/passwd placeholders
- redis/ — Redis ACL helper (`utils/redis_connections.py`) and guide (see docs)
- systemd/ — Hardened unit files for gunicorn, daphne, celery, celerybeat, mqtt
- scripts/ — Health checks, dependency checks, MQTT subscriber, monitoring, rollback, verifiers (WS, MQTT WS, MQTT flow), autosizing launchers
- logrotate/ — Rotation policy for Mosquitto
- .env.sample — Centralized env for service credentials & autosizing
- Makefile — install, deploy, verify, verify-ws, verify-mqtt-ws, verify-mqtt-flow, verify-h3-ocsp, rollback, status, logs, tune

## Quick start
1) Copy `.env.sample` to `/etc/default/naboom` and fill secrets.
2) `sudo make install`
3) `sudo make deploy`
4) `sudo make verify-h3-ocsp && sudo make verify-ws && sudo make verify-mqtt-ws && sudo make verify-mqtt-flow`
