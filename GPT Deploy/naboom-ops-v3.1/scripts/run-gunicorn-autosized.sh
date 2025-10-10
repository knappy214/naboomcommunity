#!/usr/bin/env bash
set -euo pipefail
: "${APP_DIR:=/var/www/naboomcommunity/naboomcommunity}"
: "${APP_MODULE:=naboomcommunity.wsgi:application}"
: "${BIND_ADDR:=127.0.0.1}"
: "${BIND_PORT:=8001}"
: "${GUNICORN_PROFILE:=io}"
: "${GUNICORN_WORKERS:=auto}"
: "${GUNICORN_THREADS:=auto}"
: "${GUNICORN_MAX_REQUESTS:=1000}"
: "${GUNICORN_MAX_REQUESTS_JITTER:=100}"
: "${GUNICORN_TIMEOUT:=60}"
: "${GUNICORN_GRACEFUL_TIMEOUT:=30}"
: "${GUNICORN_LOG_LEVEL:=info}"
: "${GUNICORN_EXTRA_ARGS:=}"
cd "$APP_DIR"
CPU="$(nproc || echo 2)"
if [[ "$GUNICORN_WORKERS" == "auto" ]]; then
  if [[ "$GUNICORN_PROFILE" == "cpu" ]]; then GUNICORN_WORKERS=$(( CPU<2?2:CPU )); else
    calc=$((2*CPU+1)); GUNICORN_WORKERS=$(( calc>16?16:calc )); fi
fi
if [[ "$GUNICORN_THREADS" == "auto" ]]; then
  if [[ "$GUNICORN_PROFILE" == "cpu" ]]; then GUNICORN_THREADS=1; else GUNICORN_THREADS=2; fi
fi
exec /usr/bin/env gunicorn "$APP_MODULE"   --bind "${BIND_ADDR}:${BIND_PORT}"   --workers "${GUNICORN_WORKERS}"   --threads "${GUNICORN_THREADS}"   --worker-class gthread   --max-requests "${GUNICORN_MAX_REQUESTS}"   --max-requests-jitter "${GUNICORN_MAX_REQUESTS_JITTER}"   --timeout "${GUNICORN_TIMEOUT}"   --graceful-timeout "${GUNICORN_GRACEFUL_TIMEOUT}"   --log-level "${GUNICORN_LOG_LEVEL}"   ${GUNICORN_EXTRA_ARGS}
