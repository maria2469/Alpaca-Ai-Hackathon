# Take-profit rule: why a fraction of width

How the mechanical take-profit on an open debit vertical is defined, and the
study behind it. The exit code lives in `pos_and_risk.exit_decision`; the two
thresholds are `exits.take_profit_mult` (3.0) and `exits.take_profit_width_frac`
(0.65) in `settings.yaml`. Rule approved 2026-09-03 after the study below;
history: 2.0× debit (2026-08-31) → 3.5× → 3.0× (both 2026-09-02, after the
NVDA winner).

## The rule

Every cycle, for every paired spread with a known entry debit and fresh
two-sided leg quotes, the position manager computes the **net mid mark**
(long mid − short mid) and exits with reason `take_profit` when

```
mark ≥ min( take_profit_mult × entry_debit ,  take_profit_width_frac × width )
```

`width` is the strike distance of the paired legs (set in `pair_spreads`);
if it is unknown the debit rule applies alone. The stop (`stop_fraction`,
mark ≤ 0.5 × debit), the DTE exit and the reversal exit are unchanged, and
precedence is still expiry → reversal → stop → take-profit.

With the shipped screener band (debit between 25% and 45% of width) the
width rule is the one that binds: 3× debit is lower than 0.65× width only
when the fill came in under ~22% of width, which needs a favorable fill
below the screener's floor. The multiple is kept as a ceiling, not as the
working trigger.

## Why the debit multiple was the wrong yardstick

A debit vertical's value is capped at its width, and the mark divided by the
width is approximately the market's (risk-neutral) probability that the
spread finishes fully in the money — see [Where that comes
from](#where-markwidth--probability-comes-from) below. That single ratio
tells you what odds you are still holding:

| mark as % of width | remaining reward : risk | = this multiple of a 25%-of-width debit | of a 45% debit |
|---|---|---|---|
| 50% | 1.0 : 1 | 2.0× | 1.1× |
| 60% | 0.67 : 1 | 2.4× | 1.3× |
| **65%** | **0.54 : 1** | **2.6×** | **1.4×** |
| 70% | 0.43 : 1 | 2.8× | 1.6× |
| 75% | 0.33 : 1 | 3.0× | 1.7× |

Three problems with "mark ≥ N × debit":

1. **It measures the wrong thing.** Two spreads at the same fraction of width
   have identical prospects from here on, but very different multiples
   depending on what they cost. The multiple mixes the entry price into an
   exit decision that should only depend on the current odds.
2. **Reachability depends on the entry price.** 3× is reachable only when the
   debit is under 33% of width. A 45%-debit spread would need 135% of width;
   a 33%-debit spread needs the full width, which the `exit_dte: 2` exit
   forecloses. Those trades could only ever leave via DTE, reversal or stop.
3. **Slippage eats the tail.** Exit orders are marketable (`build_exit_plan`
   uses long bid − short ask), so the realized credit sits below the
   triggering mid — about 6% of width on the TSLA example below. Past ~70% of
   width the remaining 30% barely covers that cost at the odds being run.

Why 0.65 and not another number: it is a judgment call inside the 0.60–0.70
band, not a fitted value. Entries are taken at 25–45% implied probability
on a short-horizon event signal; by 65% the market has moved 20–40 points
the trade's way and the entry edge is spent. Below 0.60 the rule sells
coin-flips with the momentum still running; above 0.70 it starts to need a
real run past the short strike and rarely fires, which is exactly the
problem 3× had.

## Worked example (TSLA 375/380 call spread, 2026-09-03 10:40 ET)

The spread that prompted the study. Entered 2026-09-02 10:28 ET on a
`macd_cross_up` event (manual mode), expiry 2026-09-18, quoted debit 1.26,
filled at **1.20**, 3 contracts ($360 at risk). At the time of the snapshot
TSLA had just reached the short strike.

- **Spot** 379.05. Leg snapshots from Alpaca (OPRA feed):

  | Leg | Bid | Ask | Mid | Delta | IV |
  |---|---|---|---|---|---|
  | long 375 C | 15.79 | 16.10 | 15.945 | 0.563 | 45.7% |
  | short 380 C | 13.36 | 13.67 | 13.515 | 0.506 | 45.9% |

- **Spread**: mid mark **2.43** = 2.03× debit = **49% of the $5 width**;
  marketable exit credit 15.79 − 13.67 = **2.12** (0.31 of slippage, 6% of
  width). Greeks of the spread: delta **0.057** per share ($5.70 per
  contract per $1 in TSLA), gamma ≈ 0, theta ≈ 0 (slightly positive above
  380), vega ≈ 0. One-sigma move for the 15 days left at 46% IV ≈ **$35**,
  against a $5 width.
- **Thresholds**: old rule 3 × 1.20 = **3.60** (72% of width); new rule
  0.65 × 5 = **3.25** (65%); stop 0.60. Decision on this snapshot: hold.

The question was whether more reward waits past the short strike, or whether
it fades because of the deltas. Black-Scholes at 45.7% IV, which reproduces
the live mark within a few cents:

| TSLA | 15 DTE | 10 DTE | 7 DTE | 5 DTE | 2 DTE (forced exit) |
|---|---|---|---|---|---|
| 370 | 2.01 | 1.93 | 1.84 | 1.74 | 1.37 |
| 375 | 2.30 | 2.28 | 2.25 | 2.22 | 2.09 |
| **380** | 2.58 | 2.62 | 2.67 | 2.71 | 2.86 |
| 385 | 2.86 | 2.96 | 3.07 | 3.18 | 3.57 |
| 390 | 3.13 | 3.29 | 3.44 | 3.61 | 4.14 |
| 400 | 3.62 | 3.85 | 4.07 | 4.28 | 4.77 |
| 410 | 4.02 | 4.28 | 4.50 | 4.68 | 4.96 |

Spot needed to reach each trigger:

| DTE | 3.60 (3× debit) | 3.25 (0.65× width) |
|---|---|---|
| 15 | ≈ 400 (+5.5%) | ≈ 393 (+3.7%) |
| 10 | ≈ 395 | ≈ 390 |
| 5 | ≈ 390 | ≈ 386 |
| 2 | ≈ 385 | ≈ 383 |

Spread delta by spot at 15 DTE: 0.056 at 370, **0.057 at 375–380**, 0.052 at
390, 0.045 at 400, 0.027 at 420.

What this says:

- **Delta is not what fades first.** The spread's delta peaks with spot
  between the strikes and stays flat until ~390. It only decays well past
  the short strike. At ~$5.70 per contract per $1, even a $20 rally to 400
  adds ~1.20 per share ($360 on three contracts) with 15 days left.
- **The remaining reward comes from time, not price.** A spread parked at
  the short strike is worth 2.58 today and 2.86 at the 2-day forced exit —
  the mark converges to the width only as expiry nears and only while TSLA
  stays above 380. That is why a trade "at the short strike" is still only
  worth ~half the width with two weeks to go.
- **The diminishing part is the odds.** At 49% of width the position is a
  1:1 bet on where TSLA lands in a $5 window two weeks out, when a one-sigma
  move is $35. At the old 72% trigger it would be risking 0.72 to make 0.28.
  The width rule exits at 0.54:1 instead, and fires only once TSLA has
  actually cleared the short strike (≈ $3 above it at 2 DTE, ≈ $6 at 5 DTE).

## Why the stop stays relative to the debit

Mirroring the width logic on the stop was considered and rejected. The
take-profit is an odds rule; the stop cannot be one, because the odds of
holding a *losing* vertical improve as it loses (at 15% of width the
remaining reward:risk is 5.7:1). A stop exists to admit the thesis failed
and to free the risk budget:

- Thesis failure is already handled by the **reversal exit**, which fires on
  an opposing event regardless of mark.
- The risk budget is in **debit** terms (per-entry cap = 0.5% of equity on
  the debit). "Exit at half the debit" means "never lose more than half the
  allocated risk" on every spread. A width-based stop at 15% would stop a
  45%-debit spread after a 67% loss and a 25%-debit spread after 40% —
  muddier, not cleaner.

If a width-based stop is ever wanted, slippage sets the floor: below ~2× the
combined leg bid-ask (12–15% of width on TSLA) the spread is worth about
what it costs to exit, and holding to the DTE exit is cheaper. The ceiling
is the 25% minimum debit fraction, or a spread could be stopped at entry.

For these expiries the stop rarely matters anyway. TSLA needs to fall to
≈ 339 today (−10.5%), ≈ 355 at 5 DTE or ≈ 363 at 2 DTE for the 0.60 stop to
fire — and at 2 DTE the forced exit fires first. With 5–16 DTE spreads at
~45% IV the stop is mostly a near-expiry rule that overlaps `exit_dte`.

## Where "mark/width ≈ probability" comes from

This is textbook option theory, not a PACA heuristic. Three results chain
together:

1. **A cash-or-nothing digital call that pays $1 if `S_T > K` is worth
   `e^{-rT} · N(d2)`**, and `N(d2)` is the risk-neutral probability of
   finishing in the money. Standard Black–Scholes result; see the
   [Black–Scholes valuation of a binary option](https://en.wikipedia.org/wiki/Binary_option#Black%E2%80%93Scholes_valuation)
   or the [Bionic Turtle (FRM) explainer](https://forum.bionicturtle.com/threads/cash-or-nothing-and-asset-or-nothing-why-n-d1-and-n-d2.5650/)
   on why `N(d1)` and `N(d2)` appear where they do.
2. **The digital is minus the derivative of the vanilla call price with
   respect to strike, `−∂C/∂K`**, so a tight vertical call spread
   `(C(K₁) − C(K₂)) / (K₂ − K₁)` is a finite-difference approximation of it:
   the spread's value per dollar of width converges to the discounted
   probability of finishing above the strikes as the width shrinks. Same
   Wikipedia section states both facts ("the value of a binary call is the
   negative of the derivative of the price of a vanilla call with respect to
   strike price"; "a binary call option is … similar to a tight call spread").
   The general version — the whole risk-neutral distribution can be read off
   the strike-derivatives of call prices — is
   [Breeden & Litzenberger (1978), *Prices of State-Contingent Claims Implicit in Option Prices*, Journal of Business 51(4)](https://ideas.repec.org/a/ucp/jnlbus/v51y1978i4p621-51.html).
3. **Delta is `N(d1)`, not `N(d2)`, and `N(d1) > N(d2)` for calls** by a gap
   that grows with `σ·√T` — delta also prices *how far* in the money the
   option finishes, not just whether. So "delta ≈ probability ITM" is the
   loose trader shorthand; the exact statement is `mark/width ≈ e^{-rT}·N(d2)`
   at the spread's midpoint, and delta overstates it. See
   [GlobalCapital, *Option Delta Versus Probability To Exercise*](https://www.globalcapital.com/article/28mwtvkodfvd0968sq6m8/derivatives/option-delta-versus-probability-to-exercise)
   and [Option Alpha's probability documentation](https://docs.optionalpha.com/technical-documentation/calculations/probability)
   ("N(d2) represents the risk-neutral probability that the option will be
   exercised").

Check against the TSLA snapshot above (spot 379.05, midpoint strike 377.5,
IV 45.7%, 15 DTE, r 4%):

| quantity | value |
|---|---|
| mark / width (live quotes) | 2.43 / 5 = **0.486** |
| `e^{-rT}·N(d2)` at 377.5 (Black–Scholes) | **0.505** |
| delta `N(d1)` at 377.5 (Black–Scholes) | 0.543 |
| delta at 377.5 (average of Alpaca's 375 C and 380 C deltas) | 0.535 |

The ordering is the textbook one: mark/width ≈ N(d2) < delta. The 2-point gap
between the live ratio and the model probability is the $5 finite difference
plus the market's smile; the 5-point gap to delta is `σ·√T`. For PACA's
purposes the ratio is the number to use — it needs no greeks, it is exactly
what the exit code already computes, and it is the more conservative of the
two.

Caveat: "probability" here is the risk-neutral one implied by prices, not a
forecast. It is the right yardstick for *what odds the market is offering*
on the remaining payoff, which is what a take-profit rule should read.

## Alternatives considered (not implemented)

Any of these is a small change to the take-profit branch in
`exit_decision` plus tests, and each is a **methodology change** per
CLAUDE.md — decide first, then implement.

| Rule | Trigger | Pro | Con |
|---|---|---|---|
| Debit multiple only *(the rule before 2026-09-03)* | `mark ≥ N × debit` | Simplest; reads as "+200%" | Reachability depends on entry price; unreachable above a 33% debit at N = 3 |
| Width fraction only | `mark ≥ f × width` | Same odds at the trigger for every spread | Drops the familiar "×" reading; the shipped rule keeps both, the multiple as a ceiling |
| Short-strike delta | exit when short-leg delta ≥ ~0.65–0.70 | Reads a probability-like number straight off the snapshot | Needs greeks plumbed into `LegQuote`; delta is N(d1), which overstates the ITM probability N(d2) that mark/width already measures (see below) |
| Trailing take-profit | exit when mark falls X% from its cycle-to-cycle high | Lets winners run past a fixed level | Needs persisted per-spread highs; interacts with 5-minute mark noise on wide leg quotes |
| Time-scaled fraction | `f` rising as DTE falls (e.g. 0.6 at 15 DTE → 0.8 at 3 DTE) | Matches the value-converges-with-time picture above | Two knobs and a schedule to justify; the DTE exit already caps the tail |

Data point against every version that holds longer than 2.0×: the NVDA
227.5/235 winner (debit 0.86, width 7.5) was sold at 2.06 on the 2.0× rule
within 1% of the day's high; that mark was 27% of width, so neither 3×
debit nor 0.65× width would have fired. That spread's 11%-of-width debit is
no longer allowed by the screener's 25% floor, so it is not representative
of current entries, but it is the one realized exit on record.
