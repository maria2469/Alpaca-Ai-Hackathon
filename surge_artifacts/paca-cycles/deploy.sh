#!/bin/sh
# Refresh the PACA cycle dashboard: export fresh data and redeploy.
set -e
cd "$(dirname "$0")"
REPO=../..

# Fresh account snapshot (best effort: keep the previous one if the export fails)
(cd "$REPO" && uv run --env-file .env cli.py account --export) \
  || echo "WARN: account export failed; deploying previous snapshot if present"
if [ -f "$REPO/logs/account.json" ]; then
  cp "$REPO/logs/account.json" ./account.json
fi

# PnL snapshots from pnl.py (best effort). Write to a temp file and move only on
# success so a failed export keeps the previous copy instead of an empty file.
# stderr (loguru warnings) is deliberately not redirected into the JSON.
export_json() {
  out="$1"; shift
  if (cd "$REPO" && uv run --env-file .env pnl.py "$@") > "./$out.tmp"; then
    mv "./$out.tmp" "./$out"
  else
    rm -f "./$out.tmp"
    echo "WARN: $out export failed; deploying previous copy if present"
  fi
}
export_json positions.json positions --json
export_json realized.json realized --json --days 30

# Trading config, minus the llm section (model names stay private)
(cd "$REPO" && uv run python -c "
import json, yaml
d = yaml.safe_load(open('settings.yaml'))
d.pop('llm', None)
print(json.dumps(d))
") > ./config.json

cp "$REPO/logs/cycles.jsonl" ./cycles.jsonl
surge . alpaca-hackathon-2026-artifacts-paca-cycles.surge.sh
