#!/usr/bin/env bash
set -euo pipefail
pgrep -f "celery.*worker" >/dev/null || { echo "celery worker not running"; exit 1; }
echo "celery health OK"
