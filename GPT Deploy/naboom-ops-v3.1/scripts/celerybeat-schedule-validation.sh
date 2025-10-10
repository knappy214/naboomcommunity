#!/usr/bin/env bash
set -euo pipefail
: "${SCHEDULE_FILE:=/var/lib/celery/celerybeat-schedule}"
[[ -f "$SCHEDULE_FILE" ]] || { echo "Missing $SCHEDULE_FILE"; exit 1; }
echo "Found $SCHEDULE_FILE"
