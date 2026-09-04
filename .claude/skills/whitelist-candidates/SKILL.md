---
name: whitelist-candidates
description: Evaluate underlyings for the PACA whitelist (symbols in settings.yaml) with a read-only Alpaca liquidity probe plus the real screener, recommend which to add, and after the user picks, apply the edit and commit. Use whenever the user asks to "add X to the whitelist", "find more underlyings/candidates", "evaluate SYM for the whitelist", "diversify the whitelist", or wonders whether a symbol's options are liquid enough for the system.
---

# Whitelist candidates

Find and vet new underlyings for `symbols` in `settings.yaml`. The whitelist is part of the
approved trading methodology, so nothing is edited until the user picks from your
recommendation. Until then every step is read-only.

## Guardrails

- Paper account only; the probe and `cli.py screen` only read data. No orders are ever placed.
- **Never change screener thresholds** (`min_open_interest`, `max_leg_spread_bps`, width band,
  `min_liquid_legs_per_expiry`, ...) to make a symbol pass. Report the mismatch instead; loosening
  a threshold is a separate methodology decision for the user.
- **Never reorder or remove existing symbols.** Append only — `tests/test_settings.py` pins SPY
  at index 0.
- Show the user the full output of every command you run, verbatim.
- If the market is closed, the probe still reports open interest and expiry selection, but the
  quote filter cannot be verified. Say so plainly and recommend re-running `cli.py screen`
  during hours before the first live cycle; do not present after-hours results as "strong".

## Step 1 — Collect candidates

Take symbols from the user's message. If none were given, propose a set that fills sector gaps
against the current list (`grep '^symbols' settings.yaml`). Categories probed so far and what
was learned on 2026-09-01 (quotes change; re-probe, don't assume):

| category | names | 2026-09-01 result |
|---|---|---|
| bitcoin | IBIT, MSTR, COIN, MARA, BITO | IBIT/MSTR added; COIN quotes too wide; MARA/BITO too cheap |
| metals | GLD, SLV, GDX | GLD/SLV added (GLD needed the liquid-expiry filter); GDX quotes wide |
| energy | USO, XLE, XOM, CVX | USO/XLE added; XOM/CVX quotes wide |
| rates / credit | TLT, HYG | TLT low IV, wide quotes; HYG no IV on many legs |
| financials | JPM, GS, XLF, KRE | wide quotes relative to premium |
| staples / health | WMT, UNH, LLY | WMT added; UNH/LLY wide |
| broad | DIA, IWM, EEM, EFA, XBI, ARKK | DIA works but overlaps SPY; EEM/EFA thin |

Always include two current whitelist names (SPY and NVDA) as a baseline so the user can compare.

## Step 2 — Probe (read-only)

```bash
uv run --env-file .env python .claude/skills/whitelist-candidates/probe.py SPY NVDA <CANDIDATES...> 2>&1
```

Per symbol it prints spot, bar count at the configured timeframe, strike step, whether the
strike grid can form a spread in the width band, which expiries the screener would pick after
the liquid-expiry filter with the number of liquid strikes near spot in each, and (market hours
only) how many of those legs also clear the quote filter. The verdict line is the summary:

- `strong` — several legs on both sides clear every filter right now.
- `marginal` — open interest is there but few legs clear the quote filter; the screener will
  find a spread only sometimes. Fine to add if the user wants the exposure.
- `thin: ...` — the reason is spelled out. Do **not** add. Typical causes: too few bars on the
  IEX feed, a strike grid too coarse for the width band (very low-priced ETFs), no expiry with
  enough liquid strikes near spot, or quotes wider than `max_leg_spread_bps`.

Paste the whole output.

## Step 3 — Confirm with the real screener (market hours)

For every `strong` or `marginal` symbol, and for any `thin` one the user specifically asked
about, run both directions and paste the last three lines of each:

```bash
uv run --env-file .env cli.py screen SYM --direction CALL 2>&1 | tail -3
uv run --env-file .env cli.py screen SYM --direction PUT  2>&1 | tail -3
```

A found spread (`CALL SYM 2026-..: long ... / short ...`) is the strongest evidence. "no
acceptable spread" with mostly `wide_spread` rejections means marginal; mostly
`low_open_interest` means thin. If the market is closed, skip this step and say so.

## Step 4 — Recommend and ask

Rank the candidates, one line each with the exposure it adds and the evidence. Then use
AskUserQuestion to let the user pick which to add; "none" is a valid answer. Flag separately
anything that would only work with a methodology change (a threshold or the expiry rule), and
leave it out unless the user explicitly approves that change.

## Step 5 — Apply (only after the user has picked)

1. Append the chosen symbols to `symbols` in `settings.yaml`, keeping the existing order.
2. Update the whitelist line in `README.md` (section "Methodology", the `**Whitelist**` bullet).
3. Update the whitelist bullet in the memory file
   `~/.claude/projects/-Users-jho-Documents-Git--seekingvega-Alpaca-Ai-Hackathon/memory/spread-methodology.md`
   with the date and the reason each symbol was added or rejected.
4. Verify:

   ```bash
   uv run pytest -q 2>&1 | tail -3
   uv run --env-file .env cli.py preflight 2>&1 | grep -E "SYMBOLS|preflight"
   ```

5. Commit only `settings.yaml` and `README.md` with a message naming the symbols added and the
   probe evidence (liquid legs, screener result). Do not push.

## Step 6 — Report

End with: symbols added, symbols rejected and the one-line reason for each, whether the quote
filter was verified live or not, tests run, and anything skipped.
