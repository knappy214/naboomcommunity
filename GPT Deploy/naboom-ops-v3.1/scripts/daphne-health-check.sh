#!/usr/bin/env bash
set -euo pipefail
: "${PORTS:=9000 9001 9002}"
for p in $PORTS; do
  timeout 2 bash -c "</dev/tcp/127.0.0.1/$p" 2>/dev/null || { echo "daphne port $p not open"; exit 1; }
done
echo "daphne health OK"
