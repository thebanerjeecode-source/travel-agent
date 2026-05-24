#!/usr/bin/env bash
# Jaipur 4-day demo — dry-run uses stub pipeline (LLM-only city in live mode)
set -euo pipefail
cd "$(dirname "$0")/.."

REQUEST='Plan a 4-day trip to Jaipur. $1,200 budget. Love forts and street food, hate crowds.'

python3 -m src.main \
  --dry-run \
  --trace \
  -m output/jaipur_4day.md \
  "$REQUEST"

echo ""
echo "Done. For live Jaipur planning, remove --dry-run (requires GROQ_API_KEY + GEMINI_API_KEY)."
