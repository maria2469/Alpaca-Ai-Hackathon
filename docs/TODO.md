# TODO — follow-ups from 2026-09-01 live loop session

Three issues observed while running the `/paca-agent` loop (32 cycles, 13:28–16:01 ET).
Details and evidence are in `logs/cycles.jsonl` for that afternoon.

## 1. Exit client_order_id collision for same-underlying/same-expiry spreads (bug, DEFER → fix)

- **What happened:** Cycle `20260901-185000` triggered reversal exits on both AMZN 2026-09-11 call
  spreads (x5 260/267.5 and x7 262.5/270). Both exits generated the identical client order id
  `sp-20260901-185000-exit-AMZN-260911C` (cycle + underlying + expiry + right). The first submitted
  and filled; the second was rejected with `APIError` and its spread stayed open.
- **Impact:** One exit delayed by one cycle. Self-healing — the next cycle (`20260901-185443`)
  retried under its new cycle id and filled. Confirmed in the journal.
- **Proposed fix:** Make the exit client_order_id unique per spread — include strikes or a sequence
  suffix. Should be a one-liner where the id is built.
- **Classification:** bug fix; small, low risk.

## 2. Manual-mode index drift can select the wrong symbol (safety edge)

- **What happened twice on 2026-09-01:**
  - 14:45 — intended MSFT PUT as `[1]`; a new bar arrived inside the run, MSFT's event expired,
    IWM+QQQ fired instead, and `1` selected **IWM PUT**. No harm (screen rejected it), but the wrong
    symbol was chosen.
  - 15:13 — intended TSLA as `[3]` (MSFT, NVDA, TSLA); NVDA gated out as `already_held` inside the
    run, list shrank to 2, and `3` fell out of range (safe: treated as pass).
- **Impact:** The dangerous case is a wrong-symbol selection that *passes* the screen and submits an
  order. Didn't happen, but nothing structurally prevents it.
- **Ideas (pick one, keep it simple):**
  - Let manual mode accept a symbol string (e.g. `TSLA PUT`) instead of / in addition to an index.
  - Or echo the selection and require a confirmation line (`SYMBOL DIRECTION` must match).
- **Classification:** methodology-adjacent safety improvement — discuss before implementing.

## 3. Wide-spread recheck rejected a screened entry at submission time (observation, likely fine)

- **What happened:** Cycle `20260901-184603` — QQQ PUT on `breakout_down`. The screener accepted a
  spread (QQQ 2026-09-08 P 686/671, net debit 1.06, qty 4) but the final pre-order recheck rejected
  it: `recheck: wide_spread`. Quotes widened between screening and submission; no order.
- **Impact:** Missed the day's strongest signal, but the QQQ move didn't follow through afterward,
  so the guard arguably saved a losing trade. Working as designed.
- **Follow-up:** Decide whether this is acceptable (probably yes) or whether the recheck should
  retry once with fresh quotes before giving up. Only act if it keeps blocking good entries.
- **Classification:** no change unless it recurs; any change is a methodology change needing approval.

## Deferred from the 2026-09-02 signal-quality review (post-hackathon)

Implemented on 2026-09-02: MACD cross magnitude threshold (`macd_min_hist_atr`),
RSI exhaustion entry gate (`rsi_overbought`/`rsi_oversold`), debit-fraction band
(`min_debit_frac`/`max_debit_frac`), `min_width_pct` 0.02 → 0.01, flat-bar RSI fix.
Still open, deliberately deferred:

- **Session filter** — indicators are computed on IEX bars including pre/post-market.
  Thin extended-hours bars shrink ATR (the event denominator) and the 09:30 "gap"
  event compares against the previous extended-hours bar, not the prior session
  close, so real overnight gaps are largely invisible. Filter to regular hours in
  `market_data.fetch_ohlcv`. Highest-value remaining item; riskier change.
- **Event cooldown / one-shot bookkeeping** — the same 5m bar persists as "latest"
  across cycles (median cycle gap on 9/1 was 4.2 min), so one event can be acted on
  twice. Record acted-on (symbol, bar timestamp) pairs.
- **Higher-timeframe trend alignment gate** — the pre-rewrite journal had
  `momentum_align`; restore a 1h/daily EMA (or similar) agreement check for entries.
  *Advisory step landed 2026-09-02*: 25/50-bar EMA distances are computed, journaled
  and shown to the decider (`trend_ema_fast`/`trend_ema_slow` in settings.yaml).
  Hardening into an `against_trend` gate stays deferred until `/trading-review`
  evidence supports it.
- **Exit-mark quality** — stop/take-profit marks bypass `options_screener.check_leg`
  (cli.py exit path), so a stale or absurdly wide quote can trigger them.
- ~~**Pre-existing test failures (not from this work)** — the `test_cancel_*` tests
  fail on unmodified HEAD.~~ **Resolved 2026-09-03:** root cause was the cancel loop
  in `cli.py cancel` being commented out, so the command listed orders but never
  called `broker.cancel_order`. Loop restored; all six cancel tests pass.

## Applied from the 2026-09-02 trading review (2026-09-03)

See `docs/trading_review.md` → "Review — 2026-09-02" for evidence. Applied:
cancel CLI restored; stock quote-age check in `broker.fetch_spot_mids` (frozen
IEX quotes now gate as `missing_quote`); pre-order vetoes logged via `_veto`;
`paca-agent` skill guidance tightened on bare MACD crosses. Still deferred from
that review: whitelist review of WMT and MSFT (both keep failing the liquidity
screen and generate the most event churn) — use `/whitelist-candidates`.

## Context from the session (for reference)

- MSFT's option chain failed the liquidity screen on all 6 signals that day (low OI / wide quotes) —
  it may effectively be untradeable under current screen settings.
- Overnight positions carried out of the session: NVDA 2026-09-09 227.5/235 C x11, TSLA 2026-09-11
  380/390 C x4 (~$1,386 premium at risk). Equity at close: $99,201.35.
