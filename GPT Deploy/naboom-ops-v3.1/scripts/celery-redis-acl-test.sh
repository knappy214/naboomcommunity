#!/usr/bin/env bash
set -euo pipefail
: "${REDIS_URL:=}"
[[ -z "$REDIS_URL" ]] && { echo "Set REDIS_URL"; exit 1; }
python3 - <<'PY'
import os, redis
r=redis.Redis.from_url(os.environ['REDIS_URL'], socket_connect_timeout=2)
r.set('celery:acl:probe','1',ex=10)
assert r.get('celery:acl:probe')=='1'
print("Redis ACL OK")
PY
