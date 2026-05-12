#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

python3 scripts/export_dashboard_data.py

cd dashboard/public
echo "SAMBA React Material UI dashboard:"
echo "http://127.0.0.1:8088/standalone/"
python3 -m http.server 8088 --bind 127.0.0.1
