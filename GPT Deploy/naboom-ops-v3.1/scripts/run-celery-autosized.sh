#!/usr/bin/env bash
set -euo pipefail
: "${APP_DIR:=/var/www/naboomcommunity/naboomcommunity}"
: "${CELERY_APP:=naboomcommunity}"
: "${CELERY_PROFILE:=io}"
: "${CELERY_CONCURRENCY:=auto}"
: "${CELERY_PREFETCH_MULTIPLIER:=auto}"
: "${CELERY_MAX_TASKS_PER_CHILD:=1000}"
: "${CELERY_QUEUES:=default}"
: "${CELERY_LOGLEVEL:=INFO}"
: "${CELERY_EXTRA_ARGS:=}"
cd "$APP_DIR"
CPU="$(nproc || echo 2)"
if [[ "$CELERY_CONCURRENCY" == "auto" ]]; then
  if [[ "$CELERY_PROFILE" == "cpu" ]]; then CELERY_CONCURRENCY=$(( CPU<2?2:CPU )); else
    calc=$((2*CPU)); CELERY_CONCURRENCY=$(( calc>32?32:calc )); fi
fi
if [[ "$CELERY_PREFETCH_MULTIPLIER" == "auto" ]]; then
  if [[ "$CELERY_PROFILE" == "cpu" ]]; then CELERY_PREFETCH_MULTIPLIER=1; else CELERY_PREFETCH_MULTIPLIER=4; fi
fi
exec /usr/bin/env celery -A "$CELERY_APP" worker   --loglevel "$CELERY_LOGLEVEL"   --concurrency "$CELERY_CONCURRENCY"   --prefetch-multiplier "$CELERY_PREFETCH_MULTIPLIER"   --max-tasks-per-child "$CELERY_MAX_TASKS_PER_CHILD"   -Q "$CELERY_QUEUES"   ${CELERY_EXTRA_ARGS}
