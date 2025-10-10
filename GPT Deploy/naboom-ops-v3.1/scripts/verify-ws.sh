#!/usr/bin/env bash
set -euo pipefail
HOST="${1:-naboomneighbornet.net.za}"; PATH_WS="${2:-/ws/}"; PORT="${3:-443}"
WSKEY="$(openssl rand -base64 16)"
REQ=$'GET '"${PATH_WS}"' HTTP/1.1\r\nHost: '"${HOST}"'\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: '"${WSKEY}"'\r\nSec-WebSocket-Version: 13\r\nOrigin: https://'"${HOST}"'\r\n\r\n'
printf "%s" "$REQ" | timeout 8 openssl s_client -connect "${HOST}:${PORT}" -servername "${HOST}" -quiet 2>/dev/null | sed -n '1,20p' | sed $'s/\r$//'
if printf "%s" "$REQ" | timeout 8 openssl s_client -connect "${HOST}:${PORT}" -servername "${HOST}" -quiet 2>/dev/null | head -n 1 | grep -q "101"; then
  echo "WS VERIFY: SUCCESS (101)"; else echo "WS VERIFY: FAILED"; exit 1; fi
