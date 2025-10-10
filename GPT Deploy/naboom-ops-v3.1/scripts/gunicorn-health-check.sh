#!/usr/bin/env bash
set -euo pipefail
: "${PORTS:=8001 8002 8003}"
: "${REDIS_URL:=}"
: "${DB_CHECK:=1}"
for p in $PORTS; do
  timeout 2 bash -c "</dev/tcp/127.0.0.1/$p" 2>/dev/null || { echo "gunicorn port $p not open"; exit 1; }
done
if [[ -n "$REDIS_URL" ]]; then
python3 - <<'PY' || { echo "Redis ACL check failed"; exit 1; }
import os, redis; r=redis.Redis.from_url(os.environ['REDIS_URL'], socket_connect_timeout=2); r.ping(); print("Redis OK")
PY
fi
if [[ "$DB_CHECK" == "1" ]]; then
python3 - <<'PY' || { echo "DB check failed"; exit 1; }
import os, psycopg2; dsn=os.getenv('DATABASE_URL'); 
if dsn: 
  conn=psycopg2.connect(dsn, connect_timeout=2); conn.close(); print("DB OK")
else: print("DB check skipped")
PY
fi
echo "gunicorn health OK"
