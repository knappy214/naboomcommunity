#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
import sys
for m in ("paho.mqtt.client","redis","requests"):
    try:
        __import__(m)
    except Exception as e:
        print("Missing:", m, e); sys.exit(1)
print("deps OK")
PY
