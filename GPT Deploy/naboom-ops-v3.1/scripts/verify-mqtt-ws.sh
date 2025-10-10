#!/usr/bin/env bash
set -euo pipefail
HOST="${1:-naboomneighbornet.net.za}"; PATH_WS="${2:-/mqtt}"; PORT="${3:-443}"
WSKEY="$(openssl rand -base64 16)"
REQ=$'GET '"${PATH_WS}"' HTTP/1.1\r\nHost: '"${HOST}"'\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: '"${WSKEY}"'\r\nSec-WebSocket-Version: 13\r\nOrigin: https://'"${HOST}"'\r\n\r\n'
printf "%s" "$REQ" | timeout 8 openssl s_client -connect "${HOST}:${PORT}" -servername "${HOST}" -quiet 2>/dev/null | sed -n '1,30p' | sed $'s/\r$//'
status_line="$(printf "%s" "$REQ" | timeout 8 openssl s_client -connect "${HOST}:${PORT}" -servername "${HOST}" -quiet 2>/dev/null | head -n 1 | sed $'s/\r$//')"
if echo "$status_line" | grep -q "101"; then
  echo "MQTT-WS VERIFY: SUCCESS (101)"; else echo "MQTT-WS VERIFY: FAILED"; exit 1; fi
