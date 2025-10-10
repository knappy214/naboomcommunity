#!/usr/bin/env bash
set -euo pipefail
pgrep -f "celery.*beat" >/dev/null || { echo "celery beat not running"; exit 1; }
echo "celerybeat health OK"
