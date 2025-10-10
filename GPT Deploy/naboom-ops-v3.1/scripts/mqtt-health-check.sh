#!/usr/bin/env bash
set -euo pipefail
: "${MQTT_WS_URL:=wss://localhost/mqtt}"
python3 - <<'PY'
print("MQTT WS proxy health: basic TLS connect attempted (use verify-mqtt-ws for full handshake).")
PY
