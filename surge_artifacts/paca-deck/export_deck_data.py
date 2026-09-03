"""Build deck-data.json for the PACA judges' deck.

Read-only, no network, stdlib only. Reads the journal, the cycle dashboard's
exported JSON (realized trades, account, config) and the candles dashboard's
data.json, and writes one small file the deck renders every number from.

    uv run python surge_artifacts/paca-deck/export_deck_data.py

Nothing here talks to Alpaca; run the two dashboard deploy scripts first (or
deploy.sh, which does) so the inputs are fresh.
"""
from __future__ import annotations

import json
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
ET = ZoneInfo("America/New_York")

JOURNAL = REPO / "logs" / "cycles.jsonl"
ACCOUNT = REPO / "logs" / "account.json"
REALIZED = REPO / "surge_artifacts" / "paca-cycles" / "realized.json"
CONFIG = REPO / "surge_artifacts" / "paca-cycles" / "config.json"
CANDLES = REPO / "surge_artifacts" / "paca-candles" / "data.json"
OUT = HERE / "deck-data.json"


def parse_ts(s: str) -> datetime:
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def et_date(dt: datetime) -> str:
    return dt.astimezone(ET).strftime("%Y-%m-%d")


def load_journal() -> list[dict]:
    recs = []
    for line in JOURNAL.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            recs.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    # Live-schema cycles only: the 8/31 evidence-only rows and dry runs are excluded.
    return [r for r in recs if "candidates" in r and not r.get("dry_run")]


def entries_of(rec: dict) -> list[dict]:
    if isinstance(rec.get("entries"), list):
        return rec["entries"]
    if isinstance(rec.get("entry"), dict):
        return [rec["entry"]]
    return []


def main() -> None:
    recs = load_journal()
    realized = json.loads(REALIZED.read_text())
    account = json.loads(ACCOUNT.read_text())
    config = json.loads(CONFIG.read_text())
    candles = json.loads(CANDLES.read_text())

    # ---- cycles / cadence -------------------------------------------------
    by_day: dict[str, list[dict]] = defaultdict(list)
    for r in recs:
        by_day[et_date(parse_ts(r["started_at"]))].append(r)
    days = []
    for day in sorted(by_day):
        rs = sorted(by_day[day], key=lambda r: r["started_at"])
        times = [parse_ts(r["started_at"]) for r in rs]
        gaps = [(b - a).total_seconds() / 60 for a, b in zip(times, times[1:])]
        eq = [r["equity"] for r in rs if r.get("equity") is not None]
        days.append({
            "date": day,
            "cycles": len(rs),
            "first_et": times[0].astimezone(ET).strftime("%H:%M"),
            "last_et": times[-1].astimezone(ET).strftime("%H:%M"),
            "median_gap_min": round(statistics.median(gaps), 2) if gaps else None,
            "outcomes": dict(Counter(r.get("outcome") for r in rs)),
            "equity_first": eq[0] if eq else None,
            "equity_last": eq[-1] if eq else None,
        })

    # ---- gates / events / funnel -----------------------------------------
    gate = Counter()
    symbol_cycles = 0
    with_event = 0
    for r in recs:
        for c in r.get("candidates", []):
            symbol_cycles += 1
            if c.get("events"):
                with_event += 1
            gate[c.get("gate_block") or "PASS"] += 1

    picks: list[dict] = []
    screen_rej = Counter()
    rejected = Counter()
    for r in recs:
        for e in entries_of(r):
            picks.append({**e, "cycle_id": r["cycle_id"], "started_at": r["started_at"]})
            for k, v in (e.get("screen_rejections") or {}).items():
                screen_rej[k] += v
            if e.get("rejected"):
                rejected[e["rejected"]] += 1
    screened = [p for p in picks if p.get("spread")]
    submitted = [p for p in picks if (p.get("receipt") or {}).get("submitted")]

    funnel = [
        {"stage": "symbol-cycles scanned", "n": symbol_cycles},
        {"stage": "fired an event", "n": with_event},
        {"stage": "passed every gate", "n": gate["PASS"]},
        {"stage": "picked by the decider", "n": len(picks)},
        {"stage": "screener found a spread", "n": len(screened)},
        {"stage": "orders submitted", "n": len(submitted)},
    ]

    # ---- exits (journal) joined to realized by client_order_id -----------
    exit_reason_by_order: dict[str, str] = {}
    exit_attempts = 0
    exit_failed = 0
    for r in recs:
        for x in r.get("exits", []):
            if x.get("skipped"):
                continue
            exit_attempts += 1
            rc = x.get("receipt") or {}
            if rc.get("client_order_id"):
                exit_reason_by_order[rc["client_order_id"]] = x.get("reason")
            if rc.get("submitted") is False:
                exit_failed += 1

    # quoted debit per submitted entry, by leg pair
    quoted_by_legs: dict[tuple[str, str], float] = {}
    for p in submitted:
        sp = p.get("spread") or {}
        if sp.get("long") and sp.get("short"):
            quoted_by_legs[(sp["long"], sp["short"])] = sp.get("net_debit")

    trades = []
    for t in sorted(realized, key=lambda t: t["entered_at"]):
        ent, ext = parse_ts(t["entered_at"]), parse_ts(t["exited_at"])
        long_strike = float(t["long_symbol"][-8:]) / 1000
        short_strike = float(t["short_symbol"][-8:]) / 1000
        trades.append({
            "underlying": t["underlying"],
            "type": t["type"],
            "direction": "bull call" if t["type"] == "C" else "bear put",
            "expiration": t["expiration"],
            "long_strike": long_strike,
            "short_strike": short_strike,
            "width": round(abs(short_strike - long_strike), 2),
            "qty": t["qty"],
            "entry_debit": t["entry_debit"],
            "quoted_debit": quoted_by_legs.get((t["long_symbol"], t["short_symbol"])),
            "exit_credit": t["exit_credit"],
            "premium": round(t["entry_debit"] * t["qty"] * 100, 2),
            "pnl": t["pnl"],
            "pnl_pct": t["pnl_pct"],
            "hold_min": t["hold_min"],
            "entered_at": t["entered_at"],
            "exited_at": t["exited_at"],
            "entered_et": ent.astimezone(ET).strftime("%m/%d %H:%M"),
            "exited_et": ext.astimezone(ET).strftime("%m/%d %H:%M"),
            "exit_day": et_date(ext),
            "exit_reason": exit_reason_by_order.get(t["exit_order"]),
            "exit_order": t["exit_order"],
        })

    wins = [t for t in trades if t["pnl"] > 0]
    losses = [t for t in trades if t["pnl"] <= 0]
    pnl_by_day = Counter()
    for t in trades:
        pnl_by_day[t["exit_day"]] += t["pnl"]
    for d in days:
        d["realized_pnl"] = round(pnl_by_day.get(d["date"], 0.0), 2)

    summary = {
        "trades": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "realized_pnl": round(sum(t["pnl"] for t in trades), 2),
        "premium_deployed": round(sum(t["premium"] for t in trades), 2),
        "contracts": sum(t["qty"] for t in trades),
        "avg_win": round(statistics.mean(t["pnl"] for t in wins), 2) if wins else None,
        "avg_loss": round(statistics.mean(t["pnl"] for t in losses), 2) if losses else None,
        "largest_win": max((t["pnl"] for t in trades), default=None),
        "largest_loss": min((t["pnl"] for t in trades), default=None),
        "median_hold_min": statistics.median(t["hold_min"] for t in trades) if trades else None,
        "mean_hold_min": round(statistics.mean(t["hold_min"] for t in trades), 1) if trades else None,
        "exit_reasons": dict(Counter(t["exit_reason"] or "unknown" for t in trades)),
        "exit_attempts": exit_attempts,
        "exit_failed": exit_failed,
    }

    # ---- candle slices for every closed trade (hero = best pnl) ----------
    cols = candles["columns"]
    slices = []
    for t in trades:
        sym = candles["symbols"].get(t["underlying"])
        if not sym:
            continue
        ent = parse_ts(t["entered_at"]).timestamp()
        ext = parse_ts(t["exited_at"]).timestamp()
        lo, hi = ent - 3 * 3600, ext + 5 * 3600
        bars = [b for b in sym["bars"] if lo <= b[0] <= hi]
        spread = next((s for s in sym["spreads"] if s.get("exit_order") == t["exit_order"]), None)
        slices.append({
            "exit_order": t["exit_order"],
            "underlying": t["underlying"],
            "bars": bars,
            "events": [e for e in sym["events"] if lo <= e[0] <= hi],
            "spread": spread,
        })

    equity_start = 100000.0
    for d in days:
        if d["equity_first"]:
            equity_start = d["equity_first"]
            break

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "candles_generated_at": candles.get("generated_at"),
        "account": {
            "equity": account.get("equity"),
            "equity_start": equity_start,
            "generated_at": account.get("generated_at"),
            "open_spreads": len(account.get("spreads") or []),
            "open_risk": account.get("open_risk"),
            "options_level": account.get("options_level"),
        },
        "config": config,
        "cycles": {
            "total": len(recs),
            "days": days,
            "first_day": days[0]["date"] if days else None,
            "last_day": days[-1]["date"] if days else None,
            "last_cycle_et": max(parse_ts(r["started_at"]) for r in recs).astimezone(ET).strftime("%Y-%m-%d %H:%M ET") if recs else None,
        },
        "gates": dict(gate),
        "funnel": funnel,
        "post_pick_rejections": dict(rejected),
        "screen_rejections": dict(screen_rej.most_common()),
        "picks_by_model": dict(Counter(p.get("model") for p in picks)),
        "trades": trades,
        "summary": summary,
        "candle_columns": cols,
        "slices": slices,
    }
    tmp = OUT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(out, separators=(",", ":")))
    tmp.replace(OUT)
    print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes): {len(recs)} cycles, {len(trades)} trades, {len(slices)} slices")
    print(json.dumps({k: out[k] for k in ("gates", "funnel", "post_pick_rejections", "screen_rejections", "picks_by_model", "summary")}, indent=1))
    print(json.dumps(out["cycles"]["days"], indent=1))
    print([ (t["underlying"], t["quoted_debit"], t["entry_debit"], t["exit_reason"]) for t in trades])


if __name__ == "__main__":
    main()
