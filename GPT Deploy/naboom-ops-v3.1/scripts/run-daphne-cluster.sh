#!/usr/bin/env bash
set -euo pipefail
: "${APP_DIR:=/var/www/naboomcommunity/naboomcommunity}"
: "${ASGI_MODULE:=naboomcommunity.asgi:application}"
: "${DAPHNE_BASE_PORT:=9000}"
: "${DAPHNE_INSTANCES:=auto}"
: "${DAPHNE_WS_TIMEOUT:=86400}"
: "${DAPHNE_EXTRA_ARGS:=}"
cd "$APP_DIR"
CPU="$(nproc || echo 2)"
if [[ "$DAPHNE_INSTANCES" == "auto" ]]; then inst=$(( CPU<2?2:CPU )); DAPHNE_INSTANCES=$(( inst>8?8:inst )); fi
pids=()
for i in $(seq 0 $(( DAPHNE_INSTANCES-1 ))); do
  PORT=$(( DAPHNE_BASE_PORT + i ))
  /usr/bin/env daphne -b 127.0.0.1 -p "${PORT}"     --http_timeout 60 --ping_interval 20 --ping_timeout 30     --websocket_timeout "${DAPHNE_WS_TIMEOUT}"     ${DAPHNE_EXTRA_ARGS} "$ASGI_MODULE" &
  pids+=($!)
done
trap 'kill "${pids[@]}" 2>/dev/null || true; wait "${pids[@]}" 2>/dev/null || true' TERM INT
wait -n "${pids[@]}"
