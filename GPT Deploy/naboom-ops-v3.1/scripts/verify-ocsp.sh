#!/usr/bin/env bash
set -euo pipefail
HOST="${1:-naboomneighbornet.net.za}"; PORT="${2:-443}"
curl -sS --http3 -I "https://${HOST}" | grep -i 'alt-svc' || echo "No Alt-Svc header detected"
echo "---- OCSP status (openssl s_client) ----"
timeout 8 openssl s_client -connect "${HOST}:${PORT}" -servername "${HOST}" -status </dev/null 2>/dev/null | sed -n '/OCSP response:/,/---/p' || {
  echo "openssl check failed (timeout or connectivity issue)"; exit 1; }
echo "----------------------------------------"
