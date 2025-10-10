#!/usr/bin/env bash
set -euo pipefail
sleep 3
pgrep -f "celery.*worker" >/dev/null || { echo "Worker not up"; exit 1; }
echo "Worker ready"
