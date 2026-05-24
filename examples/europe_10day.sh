#!/usr/bin/env bash
# Europe 10-day demo — dry-run for offline demo; live mode plans Paris + Rome
set -euo pipefail
cd "$(dirname "$0")/.."

REQUEST='10 days in Europe. Paris and Rome. $5,000. Art and history.'

python3 -m src.main \
  --dry-run \
  --trace \
  -m output/europe_10day.md \
  "$REQUEST"

echo ""
echo "Done. Live run: python3 -m src.main \"$REQUEST\" --trace"
