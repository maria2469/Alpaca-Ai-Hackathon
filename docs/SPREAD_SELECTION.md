# Spread selection & ranking

How one debit vertical spread is chosen per entry. All code lives in
`options_screener.py` (pure functions); every threshold is a key in
`settings.yaml` (screener section) — the numbers below are the shipped
defaults. Rules approved 2026-08-31, width/moneyness/ranking revised
2026-09-01.

## Pipeline

The screener runs once per entry attempt, on the single `(symbol, direction)`
the decision layer picked:

1. **Expiries** — the nearest `expiries_to_screen` (3) listed expiries
   (weeklies included) at least `min_dte` (5) days out, ignoring anything
   past `max_expiry_lookahead_days` (45). An expiry only counts if at least
   `min_liquid_legs_per_expiry` (3) strikes within `max_width_pct` (5%) of
   spot have open interest ≥ `min_open_interest` (`liquid_expirations`) — GLD, USO and XLE list
   Mon/Tue/Wed dailies with a full strike grid and ~zero OI that would
   otherwise fill all three slots. Steps 2–5 run per expiry; the
   ranking pools the survivors from all of them. `pick_expirations`
2. **Strike universe** — strikes within ±`strike_band_pct` (10%) of spot.
   With `otm_only: true`: out-of-the-money strikes only (calls above spot,
   puts below), **plus the one at-the-money strike bracketing spot** on the
   ITM side (calls: highest strike ≤ spot; puts: lowest ≥ spot) — typically
   the tightest-quoted strike in the chain. `enumerate_spreads`
3. **Per-leg filter** — each strike's contract must have:
   open interest ≥ `min_open_interest` (100); a two-sided quote with
   `bid ≤ ask`, both positive; a timestamp within `max_quote_age_seconds`
   (10 s) of Alpaca's server clock *in either direction* (snapshots are
   fetched after the clock read, so fresh quotes may postdate it slightly);
   bid-ask spread ≤ `max_leg_spread_bps` (500) of the mid; implied
   volatility present. `check_leg`
4. **Pairing** — every surviving strike pair whose width falls between
   `min_width_pct` (2%) and `max_width_pct` (5%) of spot. Bull call: long
   the lower strike, short the higher; bear put reversed.
5. **Debit sanity** — the marketable debit `ask(long) − bid(short)` must
   satisfy `min_net_debit` (0.05) ≤ debit < width.
6. **Ranking** — see below; the top-ranked spread is the pick.

Every rejection in steps 2–5 is tallied and journaled per cycle in
`logs/cycles.jsonl` under `entry.screen_rejections` (e.g. `low_open_interest`,
`wide_spread`, `too_narrow`, `bad_debit`) — the first place to look when a
cycle reports `no_spread`.

The same `check_leg` filter runs a second time immediately before submission
(the pre-submit re-check in `cli._attempt_entry`): both legs are re-quoted
against a fresh clock, and the debit is re-sized, so a spread that decayed
between screening and submission is refused rather than sent.

## What each filter protects against

Every knob exists to keep a specific bad trade out. Journal labels in
parentheses.

- **`min_dte` (5) / `max_expiry_lookahead_days` (45)** (`no_expiration`) —
  the floor keeps the spread out of the final-week gamma/theta zone, where a
  small adverse move destroys the debit before the momentum thesis can play
  out (a separate exit rule closes anything that reaches DTE ≤ 2); the cap
  stops the screener from drifting into far-dated expiries whose premium is
  mostly time value unrelated to a bar-scale momentum signal.
- **`min_liquid_legs_per_expiry` (3)** — an expiry is skipped unless this
  many strikes within `max_width_pct` of spot have OI ≥ `min_open_interest`.
  Measured near spot on purpose: GLD's dailies carry a handful of liquid
  far-out strikes that a 2–5%-wide vertical can never use. Harmless for
  SPY/QQQ (every daily qualifies); essential for ETFs whose dailies are empty.
- **`expiries_to_screen` (3)** — how many of the nearest eligible expiries
  compete in one ranked pool. More expiries = more candidates and a real
  choice between near/cheap-theta and far/more-time spreads, at the cost of
  one snapshot fetch covering more contracts. Note the ranking has no time
  preference: equal reward-to-risk at 7 and 21 DTE ties, and further
  expiries often price *better* rr for the same strikes — expect the pick
  to lean later. Keep the contract fetch in mind before raising it: SPY/QQQ
  list daily expirations, and `broker.fetch_contracts` caps out at 5 000
  contracts.
- **`strike_band_pct` (0.10)** (`too_few_strikes_in_band`) — bounds both the
  API fetch and the universe: strikes beyond ±10% of spot are either deep ITM
  (all intrinsic, wide quotes) or lottery tickets, and neither belongs in a
  3–5%-wide vertical. It is applied twice: in the Alpaca contracts request
  (`broker.fetch_contracts`) and again locally.
- **`otm_only` (true)** — ITM legs price mostly intrinsic value, so they
  inflate the debit without adding payoff leverage, and they usually quote
  wide. The one **ATM bracketing strike** (calls: highest ≤ spot; puts:
  lowest ≥ spot) is deliberately kept because it is typically the
  tightest-quoted, highest-OI strike in the chain — observed repeatedly on
  AAPL, where the just-ITM strike quoted ~34–320 bps while its OTM neighbors
  sat at 400–700.
- **`min_width_pct` (2%) / `max_width_pct` (5%)** (`too_narrow` / `too_wide`)
  — the floor keeps the max payoff large enough to matter after slippage and
  the stop/TP exits; the cap bounds risk per spread and also limits how far
  the reward-to-risk ranking can chase cheap, low-probability wide spreads.
- **`min_open_interest` (100, per leg)** (`low_open_interest`) — open
  interest is the proxy for "someone will be on the other side when the exit
  order goes out". Entries are marketable limits, but every spread must also
  be *closed*; a leg with no open interest can strand the position. In
  practice this is the dominant rejection on single-name chains (AAPL band
  strikes routinely tally 5–20), which is expected — most of a chain is dead.
  Raising it much above ~500 effectively restricts trading to index products
  (SPY/QQQ/IWM).
- **`max_quote_age_seconds` (10, both directions)** (`stale_quote` /
  `future_quote`) — a quote older than 10 s vs Alpaca's server clock may not
  reflect the market the order will meet. The same tolerance applies in the
  *future* direction because snapshots are fetched after the clock read, so
  the freshest quotes legitimately postdate it by the fetch latency
  (2026-09-01 fix); only a timestamp more than 10 s ahead — genuine clock
  garbage — is rejected.
- **`max_leg_spread_bps` (500)** (`wide_spread`) — bounds slippage: the plan
  prices the entry at `ask(long) − bid(short)`, so wide legs both worsen the
  price and make the mid-based mark used by the stop/TP exits unreliable. In
  practice this is the *binding* filter: observed ATM option legs oscillate
  roughly 200–700 bps intraday, so small changes to this cap decide whether a
  cycle finds any spread at all. Too tight → `wide_spread` dominates the
  tallies and every cycle ends `no_spread`; too loose → fills land far from
  the screened debit and stop/TP levels drift from reality.
- **Two-sided quote sanity** (`no_quote` / `crossed_quote` / `missing_iv`) —
  data-quality guards, not tunables: a missing side, a non-positive price, a
  bid above the ask (typically a zero-bid far-OTM strike), or absent implied
  volatility all mean the feed cannot support a sane price for that leg.
- **`min_net_debit` (0.05)** (`bad_debit`, shared with `debit ≥ width`) —
  floors out junk spreads whose entire debit is inside quote noise; the
  upper sanity bound `debit < width` rejects pairs whose quotes imply a
  guaranteed loss at expiry.

## Ranking rule (current)

`rank_spreads` sorts by **reward-to-risk, highest first**:

```
reward_to_risk = (width − net_debit) / net_debit
```

That is the payoff multiple if the spread finishes fully in the money: risk
the debit, collect `width − debit`. Ties go to the **tighter combined leg
quotes** (summed bid-ask bps of both legs), i.e. the more fillable spread.

Rationale: entries fire on momentum events, so the bet is directional — pay
as little as possible per dollar of maximum payout, and among equals prefer
the spread whose quotes suggest a fill near mid.

Known bias worth watching: reward-to-risk favors the widest allowed spread
with the furthest-OTM short leg (cheap debit, but lower probability of
reaching max payout). The width band bounds how far this can stretch.

## Worked example (AAPL CALL, 2026-09-01 ~11:35 ET)

A real screen from the morning the current rules went live (run under the
3% width floor, before it was lowered to 2%; leg cap 500 bps). The decision
layer had picked AAPL CALL on a `breakout_up` event.

- **Spot** 324.80 → expiry 2026-09-09 (8 DTE, nearest ≥ 5); strike band
  292.50–357.50; with `otm_only` the universe starts at **322.50** (the ATM
  bracketing strike, the last one below spot) and runs up through 355.
- **Per-leg filter** knocked out 9 of the 13 strikes:
  `low_open_interest: 5` (e.g. 327.50 at OI 89, 342.50 at OI 18 — under the
  100 floor) and `wide_spread: 4` (far-OTM legs quoting 1 000–2 400 bps).
- **Pairing** the surviving legs inside the width band (then $9.74–$16.24)
  left two spreads; `too_narrow: 3` and `too_wide: 1` tallied the pairs that
  didn't fit.
- **Ranking**:

  | Spread | Width | Debit | Max win | Reward-to-risk | Legs bps |
  |---|---|---|---|---|---|
  | **330 / 340** ← picked | 10.0 | 2.15 | 7.85 | **3.65** | 702 |
  | 322.5 / 335 | 12.5 | 4.99 | 7.51 | 1.51 | 806 |

  Both spreads offer a similar dollar payoff at max profit (~$7.5–7.9 per
  share), but the 330/340 risks $215 per contract to the 322.5/335's $499 —
  3.65× vs 1.51× — so it wins on the primary key and the quote tiebreak
  never comes into play. This is the documented bias in action: the pick is
  the cheaper, further-OTM spread, which needs AAPL above $340 by expiry for
  the full payout, while the runner-up starts paying above ~$327.50.

The same screen ten minutes earlier had returned **no spread at all**
(every surviving leg pair fell below the width floor) — ATM leg quotes were
observed swinging between ~200 and ~700 bps within minutes, so the set of
acceptable spreads genuinely flickers cycle to cycle. That volatility of the
*filter inputs*, not the ranking, is usually why one cycle plans an entry
and the next reports `no_spread`.

## Alternatives considered (not implemented)

Each of these is a one-line change to the sort key in `rank_spreads`
(plus tests). Switching is a **methodology change** per CLAUDE.md — decide
first, then implement.

| Rule | Sorts by | Pro | Con |
|---|---|---|---|
| Flattest IV skew *(the rule before 2026-09-01)* | `abs(IV_short − IV_long)` ascending, ties → higher combined OI | Avoids overpaying for the long leg's volatility | Ignores payoff shape entirely |
| Probability-weighted EV | `P·(width − debit) − (1 − P)·debit`, P ≈ short-strike delta | Balances payoff against likelihood — the most principled | Needs greeks plumbed from Alpaca snapshots into `LegQuote`; delta is only a proxy for P(max payoff) |
| Debit-to-width target band | Prefer `debit / width` in ~0.25–0.40 | Classic vertical heuristic; balances probability vs payoff without greeks | A band, not a total order — still needs a tiebreak inside the band |
| Highest delta / ATM-first | Long strike closest to spot | Maximizes the chance the momentum move pays at all | Most expensive per dollar of payout (lowest reward-to-risk) |
| Execution quality | Combined leg bid-ask bps ascending | Best fills, least slippage | Ignores payoff; already serves as the current tiebreak |
| Composite score | Weighted blend (e.g. normalized reward-to-risk + liquidity) | Most expressive | Most knobs to tune and justify — against the keep-it-small rule unless clearly needed |

The pragmatic middle ground, if reward-to-risk proves too aggressive in
paper trading: the debit-to-width band, or probability-weighted EV once
greeks are worth the plumbing.
