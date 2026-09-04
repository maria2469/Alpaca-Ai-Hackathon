#!/bin/sh
# Refresh the PACA candles page: export bars + spreads, then redeploy.
set -e
cd "$(dirname "$0")"
REPO=../..

# Best effort: a failed export keeps the previous data.json (the exporter writes
# to a .tmp and renames only on success).
(cd "$REPO" && uv run --env-file .env export_candles.py --days 20 --out surge_artifacts/paca-candles/data.json) \
  || echo "WARN: candle export failed; deploying previous data.json if present"

echo "alpaca-hackathon-2026-artifacts-paca-candles.surge.sh" > CNAME
surge . alpaca-hackathon-2026-artifacts-paca-candles.surge.sh
