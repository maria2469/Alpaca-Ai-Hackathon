#!/bin/sh
# Refresh the PACA judges' deck: rebuild deck-data.json from the other two
# pages' exports and the journal, then redeploy.
set -e
cd "$(dirname "$0")"
REPO=../..

# The deck reads realized.json / config.json (cycle monitor) and data.json
# (candles). Refresh them first when asked; otherwise reuse what is there.
if [ "$1" = "--refresh" ]; then
  sh ../paca-cycles/deploy.sh
  sh ../paca-candles/deploy.sh
fi

# Best effort: the exporter writes to a .tmp and renames on success, so a
# failure keeps the previous deck-data.json.
(cd "$REPO" && uv run python surge_artifacts/paca-deck/export_deck_data.py) \
  || echo "WARN: deck data export failed; deploying previous deck-data.json if present"

echo "alpaca-hackathon-2026-artifacts-paca-deck.surge.sh" > CNAME
surge . alpaca-hackathon-2026-artifacts-paca-deck.surge.sh
