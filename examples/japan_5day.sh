#!/usr/bin/env bash
# Japan 5-day demo — zero API calls with --dry-run
set -euo pipefail
cd "$(dirname "$0")/.."

REQUEST='Plan a 5-day trip to Japan. Tokyo + Kyoto. $3,000 budget. Love food and temples, hate crowds.'

python3 -m src.main \
  --dry-run \
  --trace \
  --data-mode seed \
  -m output/japan_5day.md \
  -o output/japan_5day.json \
  "$REQUEST"

echo ""
echo "Done. Open output/japan_5day.md for the formatted itinerary."
