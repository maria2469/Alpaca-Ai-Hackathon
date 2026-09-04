"""Read-only digest of logs/cycles.jsonl for one trading day (ET).

Usage: python .claude/skills/trading-review/analyze.py [YYYY-MM-DD]
Default date: today in America/New_York. Reads the journal only — no network,
no Alpaca credentials needed. P&L is deliberately NOT computed here; use
`pnl.py realized` / `pnl.py positions` for that.
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
JOURNAL = Path("logs/cycles.jsonl")


def parse_ts(raw: str) -> datetime:
    return datetime.fromisoformat(raw.replace(" ", "T").replace("Z", "+00:00"))


def entries_of(record: dict) -> list[dict]:
    """Entry attempts of one row: `entries` list (since 2026-09-02) or the older single `entry`."""
    if record.get("entries") is not None:
        return list(record["entries"])
    return [record["entry"]] if record.get("entry") else []


def fmt(value, digits=2, width=0):
    text = "-" if value is None else f"{value:.{digits}f}"
    return text.rjust(width) if width else text


def load_day(day: date) -> list[dict]:
    if not JOURNAL.exists():
        sys.exit(f"{JOURNAL} not found — run from the repo root")
    records = []
    for line in JOURNAL.read_text(encoding="utf-8").splitlines():
        rec = json.loads(line)
        if "candidates" not in rec:
            continue  # pre-rewrite schema
        if parse_ts(rec["started_at"]).astimezone(ET).date() == day:
            records.append(rec)
    return records


def main() -> None:
    day = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else datetime.now(ET).date()
    records = load_day(day)
    print(f"=== PACA session digest — {day} (ET) ===")
    if not records:
        print("no journal records for this date")
        return

    times = [parse_ts(r["started_at"]).astimezone(ET) for r in records]
    print(f"cycles: {len(records)}  ({times[0]:%H:%M}–{times[-1]:%H:%M} ET)")
    print(f"outcomes: {dict(Counter(r['outcome'] for r in records))}")
    dry = sum(1 for r in records if r.get("dry_run"))
    if dry:
        print(f"dry-run cycles: {dry}")
    equities = [r["equity"] for r in records if r.get("equity") is not None]
    if equities:
        print(f"equity: {equities[0]:,.2f} -> {equities[-1]:,.2f}  ({equities[-1] - equities[0]:+,.2f} over the session)")
    warnings = Counter(w for r in records for w in r.get("warnings") or [])
    if warnings:
        print("warnings:")
        for text, n in warnings.most_common():
            print(f"  {n:3d}x {text}")

    # --- gates and events ---
    gates = Counter()
    # count distinct event bars: consecutive identical (events, macd_hist) per symbol = one bar
    event_bars: Counter = Counter()
    last_sig: dict[str, tuple] = {}
    for r in records:
        for c in r.get("candidates") or []:
            gates[c.get("gate_block") or "PASS"] += 1
            sig = (tuple(c.get("events") or []), c.get("macd_hist"))
            if c.get("events") and sig != last_sig.get(c["symbol"]):
                for kind in c["events"]:
                    event_bars[(c["symbol"], kind)] += 1
            last_sig[c["symbol"]] = sig
    print(f"\ngate tally (symbol-cycles): {dict(gates.most_common())}")
    if event_bars:
        print("events fired (distinct bars):")
        for (sym, kind), n in sorted(event_bars.items()):
            print(f"  {sym:5s} {kind:18s} {n}")

    # --- entries ---
    entries = [(r, e) for r in records for e in entries_of(r)]
    print(f"\nentry attempts: {len(entries)}")
    rejections_by_symbol: dict[str, Counter] = defaultdict(Counter)
    for r, e in entries:
        stamp = parse_ts(r["started_at"]).astimezone(ET)
        spread = e.get("spread") or {}
        if e.get("rejected"):
            result = f"REJECTED {e['rejected']}"
        elif (e.get("receipt") or {}).get("submitted"):
            result = f"SUBMITTED debit={spread.get('net_debit')} qty={e.get('qty')} {spread.get('long', '')}/{spread.get('short', '')}"
        else:
            result = "planned (dry run)" if r.get("dry_run") else "no receipt"
        print(f"  {stamp:%H:%M} {e['symbol']:5s} {e['direction']:4s} [{e.get('model', '?')}] {result}")
        for reason, n in (e.get("screen_rejections") or {}).items():
            rejections_by_symbol[e["symbol"]][reason] += n
    if rejections_by_symbol:
        print("screen rejections (summed over the day's attempts):")
        for sym, tally in sorted(rejections_by_symbol.items()):
            print(f"  {sym:5s} {dict(tally.most_common())}")

    # --- exits ---
    exits = [(r, x) for r in records for x in r.get("exits") or []]
    print(f"\nexits: {len(exits)}")
    for r, x in exits:
        stamp = parse_ts(r["started_at"]).astimezone(ET)
        ok = (x.get("receipt") or {}).get("submitted")
        print(f"  {stamp:%H:%M} {x['spread']:24s} reason={x['reason']:10s} "
              f"net_mark={fmt(x.get('net_mark'), 3)} submitted={ok}")

    # --- decision-quality table ---
    # Per-symbol series of (time, mid, macd_hist, rsi) to look up what happened after each event.
    series: dict[str, list[tuple[datetime, dict]]] = defaultdict(list)
    for r, stamp in zip(records, times):
        for c in r.get("candidates") or []:
            series[c["symbol"]].append((stamp, c))

    def later(sym: str, stamp: datetime, minutes: int) -> dict | None:
        for t, c in series[sym]:
            if t >= stamp + timedelta(minutes=minutes):
                return c
        return None

    print("\ndecision-quality table (gate-PASS events; what the journal shows afterwards):")
    print("  time  sym   event(s)             |hist|/ATR  RSI   mid@t    +30m     +60m     EOD")
    seen: set[tuple] = set()
    for r, stamp in zip(records, times):
        for c in r.get("candidates") or []:
            if c.get("gate_block") is not None or not c.get("events"):
                continue
            key = (c["symbol"], tuple(c["events"]), c.get("macd_hist"))
            if key in seen:
                continue  # same event bar re-listed by a later cycle
            seen.add(key)
            atr, hist = c.get("atr"), c.get("macd_hist")
            ratio = abs(hist) / atr if atr and hist is not None else None
            eod = series[c["symbol"]][-1][1] if series[c["symbol"]] else None

            def col(point: dict | None) -> str:
                if point is None:
                    return fmt(None, width=8)
                if point.get("mid") is not None:
                    return fmt(point["mid"], width=8)
                return f"h{fmt(point.get('macd_hist'), 3)}".rjust(8)  # old records lack mid: histogram fallback

            print(f"  {stamp:%H:%M} {c['symbol']:5s} {','.join(c['events']):20s} "
                  f"{fmt(ratio, 3, 9)}  {fmt(c.get('rsi'), 1, 4)} {col(c)} "
                  f"{col(later(c['symbol'], stamp, 30))} {col(later(c['symbol'], stamp, 60))} {col(eod)}")
    if not seen:
        print("  (no gate-PASS events this session)")
    print("\nNote: columns show journaled mid prices; 'h±x.xxx' means the record predates")
    print("mid journaling and shows the MACD histogram instead. Mids are cycle snapshots,")
    print("not fills — use them for direction, not for exact P&L.")


if __name__ == "__main__":
    main()
