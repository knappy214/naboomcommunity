#!/usr/bin/env bash
set -euo pipefail
HOST="${1:-naboomneighbornet.net.za}"
curl -sS --http3 -I "https://$HOST" | grep -i 'alt-svc' || echo "No Alt-Svc found"
timeout 2 bash -c ">/dev/udp/127.0.0.1/443" && echo "UDP/443 reachable (localhost)" || echo "UDP/443 check skipped"
curl -sS --http3 "https://$HOST/health" || true
