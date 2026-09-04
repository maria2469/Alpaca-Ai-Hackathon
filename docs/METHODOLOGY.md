# Trading methodology

What PACA trades, when, how big, and when it gets out. Every number below is
the shipped default in `settings.yaml`; change it there, not in code. Each
section names the keys it reads and the module that implements it.

Approved 2026-08-31; revised 2026-09-01 (spread geometry, liquidity, ranking),
2026-09-02 (MACD magnitude, RSI exhaustion gate, debit band, stacking) and
2026-09-03 (take-profit). Per `CLAUDE.md`, any change to a rule on this page
is a **methodology change** and needs explicit approval first. The evidence
behind the revisions is in [trading_review.md](trading_review.md).

Contents: [Whitelist](#whitelist) · [Signals](#signals) ·
[Decision](#decision) · [Spread selection](#spread-selection) ·
[Risk and sizing](#risk-and-sizing) · [Exits](#exits) · [Orders](#orders) ·
[One cycle, end to end](#one-cycle-end-to-end)

## Whitelist

`symbols` — the only underlyings the agent will ever screen or trade.

| Group | Symbols | Why |
|---|---|---|
| Index / tech core | SPY, QQQ, IWM, AAPL, NVDA, TSLA, MSFT, AMZN | deepest options books; SPY stays first (tests pin index 0) |
| Diversifiers | IBIT, MSTR, SLV, WMT, GLD, USO, XLE | bitcoin, metals, energy, staples — added 2026-09-01 after a live liquidity probe |

Candidates are vetted with the `/whitelist-candidates` skill before they touch
the file: enough IEX bars, a strike grid that can form a spread in the width
band, expiries that survive the liquid-expiry filter, and legs that clear the
quote filter during market hours. COIN, CVX, GDX, XOM and TLT were rejected
for leg quotes wider than 350 bps. A held underlying keeps getting signal
coverage even if it is later removed from the list, so its exits still run.

## Signals

Module: `market_data.py` (bars) and `signals.py` (pure indicator and event
logic). Keys: `bar_timeframe`, `loop_interval_seconds`, the `signals` section.

### Bars and indicators

- OHLCV bars at `bar_timeframe` (**5m**), fetched one symbol at a time as a
  pandas DataFrame. One cycle per completed bar: `loop_interval_seconds`
  (**300**) matches the bar length, and a tighter interval just re-reads the
  same bar.
- RSI(`rsi_period` **14**), ATR(`atr_period` **14**) and MACD(`macd_fast`
  **12** / `macd_slow` **26** / `macd_signal` **9**), standard definitions.
  Indicators count only after `min_bars` (**40**) completed bars.
- ATR is read **as of the prior bar**, so the bar being judged does not
  inflate its own yardstick.

### Entry events

A symbol is a candidate only when at least one event fired on the **latest
completed bar**:

| Event | Fires when | Direction |
|---|---|---|
| `gap_up` / `gap_down` | \|open − prior close\| > `atr_event_mult` (**2.0**) × ATR | sign of the gap |
| `breakout_up` / `breakout_down` | \|close − open\| > `atr_event_mult` × ATR | sign of the bar |
| `macd_cross_up` / `macd_cross_down` | MACD histogram crosses zero **and** \|histogram\| ≥ `macd_min_hist_atr` (**0.05**) × ATR | sign of the cross |

The MACD magnitude floor (2026-09-02) drops sub-threshold sign flips: they
are chop, not momentum. Events replaced the earlier 4/16-bar momentum returns
on 2026-08-31.

### Entry gates

Every gate is deterministic and checked before the decider sees a candidate.
A symbol that fails one is journaled with the reason:

| Gate | Journal tag | Rule |
|---|---|---|
| market open | `market_closed` | Alpaca clock says open |
| fresh bars | `stale_data` | last bar younger than `stale_bar_factor` (**2.0**) × bar duration |
| enough history | `insufficient_history` | RSI, ATR and MACD all computable (≥ `min_bars` completed bars) |
| quote present | `missing_quote` | a fresh, uncrossed two-sided stock quote (a quote older than the option quote limit is treated as missing — GLD's IEX quote once sat frozen for 2.5 h) |
| event fired | `no_event` | at least one event above |
| RSI exhaustion (entries only) | `rsi_exhausted` | CALL events dropped at RSI ≥ `rsi_overbought` (**70**), PUT events at RSI ≤ `rsi_oversold` (**30**) |
| not held / pending | `already_held`, `pending_order`, `exiting`, `opposing_held` | see [Stacking](#stacking) for what a held underlying may still do |
| data fetched | `data_error` | the bar or quote fetch for that symbol failed this cycle |

Trading near the open and near the close is allowed on purpose: there is no
time-of-day gate.

### Advisory trend context

Distances of the last close from a `trend_ema_fast` (**25**-bar, ~2 h on 5m)
and `trend_ema_slow` (**50**-bar, ~4 h) EMA are journaled and shown to the
decider. They are **not a gate**; the intent is to collect review evidence
before hardening an `against_trend` rule.

## Decision

Module: `decision_layer.py`. Keys: `llm.primary_model`, `llm.fallback_models`.

- The decider sees only the gate-passing candidates — their events and
  RSI/ATR/MACD readings plus the advisory trend distances — and returns one
  `{action, symbol, direction, thesis}`. Malformed output means no entry.
- It is asked **one entry at a time**: after an entry is placed the cycle
  re-asks with the remaining candidates until it has taken
  `floor(per_cycle_fraction / per_entry_fraction)` entries (**2** with the
  shipped settings), the decider passes, or candidates run out.
- Who decides is a run-time choice: the OpenRouter model (`z-ai/glm-5.3-flash`,
  falling back to `minimax/minimax-m3:free` then
  `nvidia/nemotron-3-super-120b-a12b:free`), a human at the prompt with
  `--manual-mode`, or Claude via the `/paca-agent` skill, which pipes its pick
  into manual mode. Manual-mode EOF counts as a pass.
- The decider picks **only** the symbol and direction. Expiry, strikes, size
  and every exit are deterministic code, and a pick that opposes a held
  spread's direction is rejected in code (`opposes_held_spread`).

## Spread selection

Module: `options_screener.py` (pure functions). Keys: the `screener` section.
Full pipeline, worked example and the alternatives considered:
[SPREAD_SELECTION.md](SPREAD_SELECTION.md).

Debit verticals only — a long leg near the money and a short leg further out
in the direction of the event, bought as one multi-leg order. In brief:

1. **Expiries** — the nearest `expiries_to_screen` (**3**) listed expiries
   (weeklies included) at least `min_dte` (**5**) days out and within
   `max_expiry_lookahead_days` (**45**). An expiry counts only if at least
   `min_liquid_legs_per_expiry` (**3**) strikes within `max_width_pct` of
   spot have open interest ≥ `min_open_interest`; this skips the empty
   Mon/Tue/Wed dailies that GLD, USO and XLE list. Survivors are ranked as
   one pool.
2. **Strikes** — within ±`strike_band_pct` (**10%**) of spot; with `otm_only`
   (**true**) out-of-the-money strikes plus the single at-the-money strike
   bracketing spot on the ITM side.
3. **Per-leg filter** — open interest ≥ `min_open_interest` (**100**); a
   two-sided uncrossed quote no older than `max_quote_age_seconds` (**10 s**)
   against Alpaca's server clock; bid-ask ≤ `max_leg_spread_bps` (**350**);
   implied volatility present.
4. **Pairs** — width between `min_width_pct` (**1%**) and `max_width_pct`
   (**5%**) of spot; `min_net_debit` (**0.05**) ≤ debit < width; and the
   debit between `min_debit_frac` (**25%**) and `max_debit_frac` (**45%**) of
   the width. The debit band is the moneyness control: it keeps the long leg
   near ATM with real delta (no deep-OTM lottery tickets) and the
   reward-to-risk at least ~1.2 (no overpriced spreads).
5. **Ranking** — highest reward-to-risk `(width − debit) / debit` first; ties
   go to the tighter combined leg quotes. The debit is priced marketable
   (long ask − short bid) at screen time and becomes the order's limit.

## Risk and sizing

Module: `pos_and_risk.py` (`size_entry`). Keys: the `risk` section. All caps
are fractions of **live equity read every cycle**; unknown equity or unknown
open risk refuses entries rather than guessing.

| Cap | Key | Default | On $100k |
|---|---|---|---|
| one entry's total debit | `per_entry_fraction` | **0.5%** | $500 |
| open premium on one underlying | `per_underlying_fraction` | **1.5%** | $1,500 |
| new premium per cycle | `per_cycle_fraction` | **1%** | $1,000 |
| total open premium | `total_fraction` | **10%** | $10,000 |

Quantity is the largest whole number of spreads that fits under every cap at
once; premium already spent this cycle is threaded into the next entry's
room. Validation enforces per-entry ≤ per-underlying ≤ total.

### Stacking

`allow_stacking` (**true**): an underlying already held may take a further
entry only in the **same direction** as the held spread; the per-underlying
cap sizes the add, and the add's chain excludes every held leg (Alpaca nets
per contract, so a shared leg would unpair the held spread). A pending order
on the underlying or an exit in the same cycle still blocks, and an event
against the held direction is gated as `opposing_held`. Set it to `false`
for one spread per underlying (`already_held`). Rationale: a per-underlying
cap of 3× the per-entry cap only makes sense if adds exist.

## Exits

Module: `pos_and_risk.py` (`pair_spreads`, `exit_decision`). Keys: the
`exits` section. Exits are **mechanical only**, run **before entries every
cycle**, and the LLM is never consulted. The mark is the net of the two legs'
quote mids from a fresh option snapshot.

Precedence, first match wins:

| # | Exit | Fires when | Needs marks? |
|---|---|---|---|
| 1 | **expiry** | DTE ≤ `exit_dte` (**2**) | no |
| 2 | **reversal** | `reversal_exit` (**true**) and an entry event fired *against* the spread's direction on its underlying (e.g. `gap_down` while holding a call spread) | no |
| 3 | **stop** | mark ≤ `stop_fraction` (**0.5**) × entry debit | yes |
| 4 | **take-profit** | mark ≥ the **lower** of `take_profit_mult` (**3.0**) × entry debit and `take_profit_width_frac` (**0.65**) × strike width | yes |

- Expiry and reversal are signal-based, so they work even when the entry
  debit or the marks are unknown. Stop and take-profit hold (and log the
  gap) when either is unknown rather than guess.
- **Entry debit** is recovered from Alpaca's per-leg `avg_entry_price`, so
  it survives restarts; **width** is the strike distance of the paired legs.
  Positions that do not pair into a known debit vertical are warned about
  and never touched.
- **Why take-profit is a fraction of width**: mark ÷ width is the market's
  implied probability of a full payoff, so a width fraction means the same
  remaining reward-to-risk at the trigger on every spread, whereas a debit
  multiple is unreachable for spreads that cost more than a third of their
  width. The stop deliberately stays debit-relative because it is a
  risk-budget rule, not an odds rule. The study, with a worked TSLA example
  and sources: [TAKE_PROFIT.md](TAKE_PROFIT.md).
- **Why a reversal exit**: with 5–16 DTE spreads and ~45% implied volatility
  the stop rarely fires before expiry; the reversal exit is what actually
  admits a failed thesis.

## Orders

Module: `broker.py`; plans built in `options_screener.py`
(`build_entry_plan`, `build_exit_plan`).

- One **multi-leg (MLEG) limit order** per action, time-in-force day. Entry
  at the fresh net debit (long ask − short bid); exit at the fresh net
  credit (long bid − short ask), sent as a negative limit per Alpaca's
  convention. Realized exits therefore land below the mid mark that
  triggered them.
- Deterministic `client_order_id` per cycle and spread; exit ids carry both
  strikes so two spreads on one underlying and expiry can close in the same
  cycle.
- `broker.submit_paper_order` is the only function that submits, runs only
  under `run --execute`, and the client is paper-only by construction. The
  safety rules are listed in the [README](../README.md#safety-rules-this-code-enforces).

## One cycle, end to end

1. Read the clock, equity, positions and open orders; pair legs into spreads.
2. Fetch bars and quotes for the whitelist plus any held underlying; compute
   indicators, events and gates.
3. Evaluate every held spread against the exit table; plan exits first.
4. Ask the decider for one entry from the gate-passing candidates; screen
   the spread; size it under the risk caps; repeat until the per-cycle cap,
   a pass, or no candidates.
5. Submit the plans (only with `--execute`); append one JSON line to
   `logs/cycles.jsonl`.
