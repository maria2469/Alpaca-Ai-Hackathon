---
name: paca-agent
description: Run one full PACA trading cycle with Claude acting as the momentum-trader entry decider (instead of the OpenRouter LLM), then redeploy the surge cycle dashboard. Use this whenever the user asks to "run a cycle", "run the agent", "run paca", "run the system", "make a trade decision", or wants the dashboard refreshed after a cycle — even if they don't say "paca-agent" explicitly.
---

# PACA Agent Cycle

Run one cycle of PACA end-to-end: gather signals, decide the entry yourself as a disciplined momentum trader, execute via `cli.py run --manual-mode --execute`, then redeploy the dashboard with `surge_artifacts/paca-cycles/deploy.sh`.

You are the decision layer here. The OpenRouter LLM is never called — manual mode reads the pick from stdin, and you supply it. Everything else (screening, sizing, risk caps, exits, order placement) stays deterministic code; you never bypass it.

## Guardrails

- **Never edit `settings.yaml`** or any Python module. This skill only runs commands.
- Paper account only; `--execute` submits real paper orders, including mechanical exits the cycle decides on its own.
- When uncertain, **pass** (blank stdin). No order beats a guessed order. Manual mode treats any unparseable input as a pass, so passing is always safe.
- Show the user everything: the full logger output of each command, verbatim, and your complete decision reasoning. The user must be able to see the same information you saw and follow how the decision was made.

## Step 1 — Gather context (read-only)

Run these and include their output in your reply:

```bash
uv run --env-file .env cli.py candidates 2>&1     # indicators, events, gate results per symbol
uv run --env-file .env cli.py account 2>&1        # equity, open spreads, premium at risk, warnings
tail -n 10 logs/cycles.jsonl                      # recent cycle history
```

From the journal tail, note: recent outcomes, screen rejections (an underlying that repeatedly finds no acceptable spread will likely reject again), which underlyings are already held or pending (a pending order gates out as `pending_order`, a same-cycle exit as `exiting`, an event against the held direction as `opposing_held`; with `allow_stacking: false` anything held gates as `already_held`) — a held underlying can still be a candidate for a same-direction add, and its `held` field names that direction — and open-risk warnings.

If the market is closed or no candidate passes its gate, skip to Step 3 and run the cycle anyway (it journals the state and runs exits when relevant), then deploy.

## Step 2 — Decide like a momentum trader

Evaluate every gate-passing candidate with fired events. For each, reason explicitly about:

- **Event quality**: a gap or breakout beyond 2 ATR is a strong impulse; a bare MACD zero-cross is weaker confirmation-only evidence.
- **Bare MACD crosses need a second leg to stand on.** On 2026-09-02 every losing or vetoed pick was a `macd_cross_*` with no other event, taken on a "trend resumption" or "broad rollover" story, while the passes that cited whipsaw or trend disagreement were right 22 times out of 22. Do not take a cross alone. It qualifies only with at least one of: a same-bar gap/breakout; price on the event's side of **both** EMAs (`ema25`/`ema50` columns) with |hist|/ATR ≥ 0.10; or a clearly stated higher-timeframe reason. Never take a second cross in the same direction on the same symbol within a session — the first one already told you the name is oscillating.
- **Trend confirmation**: does the MACD histogram's sign and magnitude agree with the event direction?
- **Exhaustion risk**: extreme RSI *against* the move (e.g. RSI > 70 on a gap_up) argues the move is spent — momentum traders chase strength, not tops. Conflicting events on the same bar are a reason to pass.
- **Volatility context**: ATR relative to price — enough range to pay for a debit spread, not so wild that the spread quotes will be junk.
- **History**: what the journal says about this underlying's recent screen rejections and holdings.

Pick **at most one** candidate and direction (CALL = expect rise, PUT = expect fall) per prompt, or pass. After an entry is placed the run asks again with the **remaining** candidates (re-numbered from 1), up to `per_cycle_fraction / per_entry_fraction` entries per cycle (2 with the shipped settings). Taking a second entry is the exception, not the norm — it needs its own momentum thesis, not a correlated echo of the first (SPY then QQQ is one bet twice). Write the reasoning out in your reply before executing — that is the point of this skill.

## Step 3 — Run the cycle

Manual mode lists tradeable candidates (gate PASS **and** at least one event) **sorted alphabetically by symbol**, numbered from 1, then asks for a number and a direction. Derive your index from that ordering.

```bash
# entering candidate N with an explicit direction (end of input = pass on the second prompt):
printf "N\nCALL\n" | uv run --env-file .env cli.py run --manual-mode --execute 2>&1

# entering two: N from the first list, then M from the re-numbered list WITHOUT the first symbol:
printf "N\nCALL\nM\nPUT\n" | uv run --env-file .env cli.py run --manual-mode --execute 2>&1

# passing (no entry; exits and journaling still run):
printf "\n" | uv run --env-file .env cli.py run --manual-mode --execute 2>&1
```

Always pipe the direction explicitly — never rely on the default. Show the complete output verbatim.

## Step 4 — Verify the order matched your intent

The candidate list is recomputed inside the run, so the index can drift if a gate flipped between Step 1 and Step 3. Check the run output:

- The numbered candidate list printed by manual mode — confirm your index pointed at the symbol you intended.
- The `entry choice: SYMBOL DIRECTION (manual)` log line — must match your stated pick.
- The order receipt (`order <id>: submitted=... status=...`) and any fill-polling lines.

**If the entered symbol does not match your intent and an order was submitted**, say so prominently and immediately offer to cancel: `uv run --env-file .env cli.py cancel` (lists open orders and confirms before cancelling).

## Step 5 — Deploy the dashboard

```bash
sh surge_artifacts/paca-cycles/deploy.sh
curl -sI https://alpaca-hackathon-2026-artifacts-paca-cycles.surge.sh | head -1   # expect HTTP 200
sh surge_artifacts/paca-candles/deploy.sh
curl -sI https://alpaca-hackathon-2026-artifacts-paca-candles.surge.sh | head -1  # expect HTTP 200
```

Run this even when the market was closed or you passed — the dashboard should always reflect the latest cycle.

## Step 6 — Report

End with: the candidate table and your reasoning, the cycle outcome (entry/pass/market_closed, any exits), order receipts and fill status, anything that went wrong or was skipped, and the live dashboard URL.
