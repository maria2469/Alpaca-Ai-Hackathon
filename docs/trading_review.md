# Trading reviews

Living post-close review log for PACA, newest first. Each section is one trading
day's review — session evidence, prior watch-item scorecard, decision grades,
findings, and what to watch next — produced by the `/trading-review` skill
(`.claude/skills/trading-review/`).

## Review — 2026-09-02

Written 2026-09-03 by Claude acting as the system's momentum-trader decision
layer, after running the `/paca-agent` loop for the full session on 2026-09-02
(81 cycles, 09:34–15:58 ET, five-minute cadence with three short pauses).
Evidence: `.claude/skills/trading-review/analyze.py 2026-09-02`, `pnl.py realized`
and `pnl.py positions`, `git log` for the day, and the 2026-09-01 review above.
The signal-quality changes from that review (`cbe1cff`) went live at 09:36, so
this is the first full day under the MACD threshold, RSI gate and debit band.

### Session stats

- **81 cycles**, outcomes 78 `hold` / 3 `submitted`. Equity 99,495 → 100,833
  (+1,338 over the session, of which +1,252 is realized round trips and the rest
  is overnight mark movement on positions carried in from 9/1).
- **Gate tally:** 1,153 `no_event`, 36 `PASS`, 15 `stale_data` (USO only),
  10 `rsi_exhausted`, 1 `already_held`. Roughly one gate-PASS candidate every
  other cycle; most cycles had nothing to decide.
- **Events:** 45 distinct-bar events across 14 symbols. WMT alone fired 9
  (three `breakout_down`, three `macd_cross_up`, two `macd_cross_down`, one
  `breakout_up`) inside a one-dollar range. SPY fired zero events all day.
- **Entry attempts:** 4 picks by the decision layer, 1 filled. WMT PUT (09:36)
  and MSFT PUT (11:38) died as `no_spread` on wide/stale quotes; QQQ PUT (11:53)
  screened a 708/695 put spread (13 wide, debit 3.26 = 25% of width, qty 1)
  and was vetoed at the pre-order recheck for `wide_spread`. TSLA CALL (10:28)
  filled: 2026-09-18 375/380, quoted 1.26, filled 1.20, qty 3.
- **Exits:** 2. TSLA 2026-09-11 380/390 C x4 `reversal` at 09:36 on a genuine
  2-ATR `breakout_down`; NVDA 2026-09-09 227.5/235 C x11 `take_profit` at 11:05
  (order took ~4 min to fill; the run's 35 s poll exited with it pending and the
  next cycle confirmed the fill).
- **Mid-day settings/code changes** (all by the user, all landed while the loop
  ran): take-profit 2.0x → 3.5x (11:17) → 3.0x (12:19); `allow_stacking: true`
  (12:13); up to 2 entries per cycle (12:34); advisory 25/50 EMA distances shown
  to the decider (10:41); exit client_order_id collision fix (10:17). The NVDA
  take-profit fired under the old 2.0x rule.

### P&L

Authoritative from `pnl.py realized` (round trips closed on 9/2):

| Spread | Qty | Debit → Credit | P&L | Held |
|---|---|---|---|---|
| TSLA 2026-09-11 C 380/390 | 4 | 1.10 → 0.93 | −$68 (−15%) | 18 h 22 m (overnight) |
| NVDA 2026-09-09 C 227.5/235 | 11 | 0.86 → 2.06 | **+$1,320 (+140%)** | 23 h (overnight) |

Realized on the day: **+$1,252**. Open at close: TSLA 2026-09-18 C 375/380 x3,
debit 1.20, mark 0.95, **−$75 unrealized (−21%)**. One winner paid for the
five small 9/1 losers (−$298) and yesterday's TSLA exit combined, which is what
a momentum book is supposed to look like — but it is one trade.

### Prior watch-item scorecard

Grading the 2026-09-01 "Watch next session" list against today's digest:

| Watch item | Verdict | Evidence |
|---|---|---|
| Mix of `rejected` reasons; loosen `min_debit_frac` toward 0.20 if `debit_out_of_band` dominates | **no action needed** | `debit_out_of_band` was the top reason for QQQ (102) and TSLA (58), but both still produced a candidate spread. WMT and MSFT died on `wide_spread`/`stale_quote`, which the debit band does not touch. |
| Whether SPY/QQQ now produce entries | **partially met** | QQQ screened a valid 13-wide put spread at 25% of width (the 0.01 width floor works); the recheck vetoed it on quotes. SPY fired no event all day, so untested. |
| Holding times lengthen toward multi-hour/overnight | **met** | Both closed round trips were overnight holds (18 h and 23 h). The new TSLA spread has been held 5.5 h and carried overnight. On 9/1 the longest hold was 2 h 46 m. |
| Stop/take-profit exits finally fire | **met** | NVDA `take_profit` fired at 11:05 at 2.4x debit. Stop-loss did not fire; the open TSLA spread sits at −21% against a −50% stop. |

Bonus check the review did not list but should have: **reversal-exit whipsaw
is gone.** One reversal exit today (on a real breakout), against four on 9/1. The
open TSLA spread survived three sub-threshold histogram sign flips (11:00 at
0.03 ATR, 13:44 at 0.015 ATR, 15:05 near zero) that would each have closed it
under the old rule. The `macd_min_hist_atr` fix did what it was designed to do.

### Decision grades

Mids below are journaled cycle snapshots, direction only. Rows before 09:54
predate mid journaling and are graded on histogram follow-through.

**Entries taken**

| Time | Pick | Path (entry → +30m → +60m → EOD) | Verdict |
|---|---|---|---|
| 10:28 | TSLA CALL 375/380 x3 | 357.65 → 353.80 → 353.81 → 353.6; mark 1.20 → 0.95 | **bad entry, outcome open.** A bare `macd_cross_up` at 0.098 ATR on a name that had just bounced 5 ATR. It gave back the whole bounce within 30 minutes. The threshold-protected exit kept it alive and TSLA rallied to 357 in the last hour, so it may yet work, but the entry was chasing a bounce, not a trend. |

**Exits (mechanical)**

| Time | Exit | Verdict |
|---|---|---|
| 09:36 | TSLA 380/390 reversal at 0.93 (−$68) | **good.** TSLA fell from 357 to 350.5 by 10:03. The 2-ATR breakout was real. |
| 11:05 | NVDA 227.5/235 take-profit at 2.06 (+$1,320) | **good.** NVDA peaked at 227.6 at 14:03 and closed 224.2, below the 225.3 exit spot. The 2.0x rule sold within 1% of the day's high. Under the 3.0x rule now in force this spread would still be open at a lower mark; that is one data point against the raise, not a verdict. |

**Screener / recheck blocks on the decider's picks**

| Time | Pick | Path | Verdict |
|---|---|---|---|
| 09:36 | WMT PUT | 105.73 → 106.06 → 106.09 → 106.07 (up) | **block saved money.** Pick was wrong; WMT reversed within one bar. |
| 11:38 | MSFT PUT | 495.69 → 494.65 → 496.12 → 496.66 | **block neutral.** Direction right for 30 min, then reversed. A 1/3-width put spread would not have cleared friction. |
| 11:53 | QQQ PUT | 708.61 → 708.69 → 708.59 → 709.10 | **block saved money.** Second day running the QQQ recheck vetoed a losing put. Pick was wrong. |

**Passes** (30 gate-PASS rows not acted on)

Twenty-two were clearly right: the move faded or reversed within 30–60 minutes
(all seven WMT flips, all three AAPL crosses, all three USO flips, MSTR 09:45 and
13:49, SLV 10:41, IBIT 09:45, MSFT 09:54 and 15:24, QQQ 14:46, GLD 14:23, TSLA
add 12:57, AMZN 09:36). Seven were inconclusive: small moves of 0.3–0.5% that a
debit spread would have struggled to monetize after four legs of friction
(WMT 13:11 +0.46, WMT 14:51 −0.42 then half back, SLV 13:49 and 14:23 +0.4%,
GLD 13:49 +0.14%, XLE 09:36 +0.6% at EOD only, MSTR 12:02 whose EOD print is a
suspect repeated quote). Zero passes were clear misses.

**Honest summary of the decision layer.** On a range-bound day the decider's four
picks went 0-for-4 (one open at −21%, three blocked, two of which would have
lost). All three losing or blocked picks were **bare MACD crosses** taken on a
"trend resumption" or "broad rollover" narrative. The passes, which leaned on
"whipsaw", "lower high", "price above EMAs on a bearish cross", were right 22
times and never clearly wrong. The mechanical filters and the pass discipline
carried the day; the discretionary entries did not.

### Findings

1. **The 9/1 fixes worked.** Reversal exits 4 → 1, holding times 1–3 h →
   overnight, take-profit fired, the debit band produced ATM-ish spreads (TSLA
   375/380 on a $357 stock, QQQ 708/695 on $708). No change.
2. **Bare MACD crosses are still the decider's weak spot.** Every losing pick
   was a `macd_cross_*` with no gap/breakout, and the winners in the 9/1
   calibration table were the 0.16 and 0.054 ATR crosses on trending names.
   Today's three bad crosses were 0.098, 0.061 and 0.052 ATR on range-bound
   names. The skill text already calls a bare cross "weaker confirmation-only
   evidence"; the decider did not act on that. **Proposed:** tighten the
   `paca-agent` skill guidance so a bare cross needs at least one of: a
   same-bar gap/breakout, EMA alignment on both EMAs with |hist|/ATR ≥ 0.10, or
   a higher-timeframe agreement — and is never taken as a *second* cross in the
   same direction within the session. Decision-layer text only, no code.
   Classification: methodology-adjacent (decision layer). **FIX NOW** (cheap;
   one session of evidence, so keep it as guidance, not a code gate).
3. **Frozen spot quotes pass the freshness gate.** `fetch_spot_mids` uses the
   latest IEX quote with no timestamp check; the only staleness gate is bar age.
   GLD's mid printed exactly 400.66 on 17 of 71 cycles (11:00–13:35), USO's
   140.855 on 29 of 71 (with isolated jumps to 143.4 and 138.8), MSTR's 125.695
   on 11. USO was gated `stale_data` only twice, GLD and MSTR never. The spot
   mid centers the strike band and feeds the screener, so a frozen quote can
   mis-center the chain fetch; on a stronger move it could produce a bad spread.
   **Proposed:** in `fetch_spot_mids`, read the quote timestamp and return
   `None` (→ `missing_quote` gate) when it is older than `max_quote_age_seconds`
   against the server clock, mirroring what `check_leg` already does for option
   quotes. Classification: bug fix (data validity). **FIX NOW** if it is the
   small change it looks like; otherwise DEFER.
4. **The `cancel` CLI cannot cancel.** The loop that calls `broker.cancel_order`
   in `cli.py cancel` is commented out; the command lists open orders, asks for
   confirmation, and exits. The `paca-agent` skill tells the operator to use it
   if a wrong-symbol order slips through. It was needed for real once today
   (NVDA exit pending ~4 min) and would have been a no-op. TODO.md notes the
   three `test_cancel_*` tests fail on unmodified HEAD, which is probably why the
   loop was disabled. Classification: bug fix (safety). **FIX NOW** — restore
   the loop and make the tests honest, or delete the command so the skill stops
   advertising it.
5. **Pre-order recheck rejections are journal-only.** The 11:53 QQQ recheck veto
   logged nothing but `outcome: hold`; the reason lived only in
   `entries[].rejected`. Classification: refactor (logging). **FIX NOW** if a
   one-line `logger.info` — it is the operator's only live view of the safety
   layer working.
6. **Take-profit multiple changed twice mid-day on one trade.** 2.0x → 3.5x →
   3.0x, motivated by NVDA's move. In hindsight the 2.0x exit sold NVDA within
   1% of its high. With 4–7 DTE spreads, 3.0x means the mark must reach ~35–40%
   of width for a 0.25-of-width debit; achievable but rarer, and every extra
   hour in a winner is also exposure to the reversal exit. No change proposed;
   **watch** whether any 3.0x exit fires and whether a spread that passed 2.0x
   gives it back.
7. **WMT and MSFT chains keep failing the liquidity screen.** MSFT 0-for-7 on
   9/1 and 0-for-1 today; WMT 0-for-1 with 15 stale quotes at the open. Both
   also generate the most event churn. Candidates for `whitelist-candidates`
   review. Classification: methodology (universe). **DEFER** to the whitelist
   skill; not a code change.
8. **Event churn on flat names is the remaining noise source.** WMT's nine
   events in a $1 range are exactly the case the deferred event-cooldown item
   describes. Evidence supports it; still **DEFER** (tracked in docs/TODO.md).

### Recommendations

Prioritized. The user picked all four on 2026-09-03 and they were applied in
the working tree (uncommitted at the time of writing):

1. **Restore `cli.py cancel`** (bug fix) — applied. The cancel loop is back; the
   six `test_cancel_*` tests that failed on HEAD now pass, which confirms they
   were failing *because* the loop was disabled, not the other way round.
2. **Quote-age check in `fetch_spot_mids`** (bug fix) — applied. Stock quotes
   older than `max_quote_age_seconds` (10 s) against the broker clock now return
   `None`, so the symbol gates as `missing_quote`. Same rule `check_leg` uses
   for option legs; all three call sites pass `clock.server_time`. Regression
   test `test_fetch_spot_mids_drops_stale_quotes` uses yesterday's GLD case.
3. **Log recheck rejections** (refactor) — applied. Every pre-order veto
   (`recheck: *`, `pending_order_conflict`, `options_level_too_low`) now goes
   through one `_veto` helper that writes the reason to the log as well as the
   journal.
4. **Tighten bare-MACD-cross guidance** (decision-layer text) — applied to the
   `paca-agent` skill's Step 2: a cross alone is not an entry; it needs a same-bar
   gap/breakout, both-EMA alignment with |hist|/ATR ≥ 0.10, or a stated
   higher-timeframe reason, and never a repeat same-direction cross on the same
   symbol in a session.
5. **No settings changes.** The 9/1 thresholds held up; the take-profit change is
   the user's and needs its own evidence.

Verification after applying: `uv run pytest -q` → 247 passed; `cli.py preflight`
→ passed.

### Watch next session

- **Bare-cross discipline:** count the decider's `macd_cross_*`-only picks and
  their +30m/+60m outcome. Target: zero bare-cross picks without a confirming
  element, or a positive hit rate if taken.
- **Frozen quotes:** count cycles where a symbol's mid repeats to the cent across
  ≥3 consecutive cycles. If the quote-age fix landed, this should be ~0 and
  `missing_quote` should appear in the gate tally instead.
- **Take-profit 3.0x:** does any exit fire? Does any spread that crossed 2.0x
  intraday close lower than that mark?
- **TSLA 375/380 x3:** outcome and exit reason. Entered on a bare cross at −21%
  overnight; it is the test case for finding 2.
- **SPY:** does it fire any event at all? Two sessions with zero SPY entries.
- **Stacking / second entries:** were any taken, and did the second entry have
  its own thesis (skill text says correlated echoes do not count)?
- **Recheck vetoes:** count and whether the price path vindicated them (2-for-2
  so far).

## Review — 2026-09-01 (first live day)

Written 2026-09-02 by Claude acting as the system's momentum-trader decision
layer, after running 32 live cycles on 2026-09-01 (13:28–16:01 ET) via
`/paca-agent`. Evidence: `logs/cycles.jsonl` (106 live cycles across 8/31–9/1),
the code as of commit `423a785`, and the closed-trade P&L. The changes this
review recommended were approved and landed in commit `cbe1cff`.

### Verdict

The architecture is right: deterministic screening, sizing, and exits with a
discretionary decision layer on top, an append-only journal, and risk caps that
cannot be bypassed. The safety layer visibly earned its keep on day one (the
pre-order recheck vetoed a QQQ put whose quotes had widened; the trade would
have lost). The losses came from three specific, fixable places — signal noise,
spread structure, and a mis-sized screener floor — not from the design.

### What the day's data showed

- **45 entry attempts → 6 orders.** 36 died as `no_spread`, 3 at the pre-order
  recheck, 1 at risk caps. The screener, not the signal, was the bottleneck.
- **SPY alone: 925 `too_narrow` rejections.** `min_width_pct: 0.02` = a $15.22
  width floor on a $761 underlying — the most liquid option chain in the world
  was nearly untradeable.
- **All 4 closed round trips were reversal-exit losses** (−$18, −$123, −$133,
  −$25 ≈ −$298 total), held 52 min–2 h 46 min. Stop-loss and take-profit never
  fired once — the reversal exit always cut first.
- **The MACD histogram flips sign 3–6×/day/symbol on 5m bars**, and a cross
  fired on *any* sign flip (even ±0.001). Each flip was both an entry candidate
  and a reversal-exit trigger: enter on a wiggle, exit on the next wiggle,
  pay 4 legs of option friction per round trip.
- **The spread ranker picked lottery tickets.** Max reward-to-risk ranking
  mathematically favors deep OTM: it chose a TSLA 380/390 call spread on a
  $356 stock — debit 11% of width, roughly a 0.15-delta bet.

### Findings and what was done (commit `cbe1cff`)

#### 1. MACD zero-cross had no magnitude threshold — the dominant loss source

A momentum event should represent impulse. The 2-ATR gap/breakout events do;
a bare histogram sign flip does not. **Fix:** `macd_cross_*` now fires only
when `|histogram| ≥ macd_min_hist_atr × ATR` (shipped 0.05). Reversal exits
consume the same events, so whipsaw exits inherit the fix automatically.

**What the formula means.** The MACD histogram is the MACD line minus its
signal line, in dollars: positive = short-term momentum accelerating up,
negative = down. A "cross" is the histogram changing sign. The old rule fired
on *any* sign change, but a flip of ±0.001 just means momentum is hovering at
exactly zero — in sideways chop the histogram wobbles across the line over and
over (3–6×/day/symbol on 9/1), and each wobble was both an entry candidate and
a reversal-exit trigger. The new rule demands the histogram *land* meaningfully
far from zero: at least 5% (`macd_min_hist_atr`) of the symbol's ATR — the
typical size of one bar's price movement, also in dollars.

Scaling by ATR instead of a fixed dollar floor matters because the histogram's
raw size depends on the stock's price and volatility: $0.02 is huge for a $60
ETF like XLE and pure noise for $760 SPY. Dividing by ATR makes one threshold
mean the same thing everywhere — *"momentum must have moved at least 5% of a
typical bar's range past zero"* — and it adapts automatically when volatility
changes. As with gap/breakout, the *previous* bar's ATR is used, so an event
bar can't inflate its own yardstick.

Calibration against 9/1 data (`|hist| / ATR` at the moment of cross):

| Signal | hist | ATR | ratio | verdict |
|---|---|---|---|---|
| TSLA cross-up 15:13 (good trade, taken) | +0.107 | 0.67 | 0.16 | fires ✓ |
| AAPL cross-up 15:04 (good trade, taken) | +0.031 | 0.58 | 0.054 | fires ✓ |
| SPY cross-down 14:35 (passed as noise) | −0.0135 | 0.45 | 0.030 | blocked ✗ |
| SPY cross-up 13:43 (whipsawed the puts) | +0.012 | 0.49 | 0.025 | blocked ✗ |
| TSLA cross-down 14:11 (passed as noise) | −0.0014 | 0.65 | 0.002 | blocked ✗ |
| MSFT cross-up 15:22 (pure noise) | +0.0007 | 0.55 | 0.001 | blocked ✗ |

Every trade the human decider took passes the threshold; every cross it passed
on as noise — including the one that whipsawed the SPY puts out at a loss — is
now blocked mechanically.

#### 2. RSI was computed but never used — exhaustion filtering lived in prompt text

Every RSI judgment ("don't chase a gap at RSI 75") depended on the decision
layer remembering to make it. **Fix:** a deterministic entry gate
(`rsi_exhausted`): CALL events are dropped at RSI ≥ `rsi_overbought` (70), PUT
events at RSI ≤ `rsi_oversold` (30). Entries only — the exit path still sees
raw events, so a capitulation gap at RSI 25 still closes a held call spread.

#### 3. Reward-to-risk ranking bought deep-OTM lottery spreads

A momentum spread trader buys the long leg near ATM (delta ~0.4–0.55), paying
25–45% of the width, so the position responds to the move being traded.
**Fix:** the debit must sit in `[min_debit_frac, max_debit_frac] × width`
(shipped 0.25–0.45), enforced both in the screener and again at the pre-order
recheck. Ranking stays max reward-to-risk *within* that band.

#### 4. Width floor mis-sized for index ETFs

`min_width_pct` 0.02 → 0.01. With the debit band in place, narrower spreads
remain economically sane, and SPY/QQQ can actually form candidates.

#### 5. Small bug: flat-price bars scored RSI 100

`loss == 0` forced RSI to 100 even when `gain == 0` too. A flat run is neutral:
now 50. (Mattered for thin symbols on the IEX feed.)

### Deliberately unchanged

- **`bar_timeframe: 5m`** — 15m bars would give better signals but near-zero
  trades in the hackathon's remaining two days. Revisit after Sep 4.
- **Risk fractions** (0.5% per entry / 1.5% per underlying / 10% total) —
  conservative and appropriate; sizing was never the problem.
- **Exit levels** (stop −50%, take-profit +100%, exit at DTE ≤ 2) — they never
  got a chance to act behind the hair-trigger reversal exit; judge them now
  that reversals require a real signal.
- **Liquidity filters** (OI ≥ 100, quote age ≤ 10 s, leg spread ≤ 350 bps) —
  they rejected a lot, but on the IEX feed they were doing genuine safety work.

### Deferred recommendations (tracked in TODO.md)

1. **Regular-hours session filter** — indicators are computed over extended-hours
   IEX bars. Thin overnight bars shrink ATR (the event denominator), and the
   09:30 gap event compares against the previous *extended-hours* bar, so real
   overnight gaps are largely invisible. Highest-value remaining item.
2. **Event cooldown / one-shot bookkeeping** — the same 5m bar persists across
   cycles (median cycle gap was 4.2 min), so one event can be acted on twice.
3. **Higher-timeframe trend alignment** — a 1h/daily EMA agreement gate so 5m
   longs only fire with the larger trend (the pre-rewrite journal had a
   `momentum_align` gate; it was lost in the rewrite).
4. **Exit-mark quote sanity** — stop/take-profit marks bypass `check_leg`, so a
   stale or absurdly wide option quote can trigger them.

### Watch next session

Watch the next live day's journal for: the mix of `rejected` reasons (if
`debit_out_of_band` dominates, loosen `min_debit_frac` toward 0.20); whether
SPY/QQQ now produce entries; holding times (should lengthen from ~1 h toward
multi-hour/overnight); and whether stop/take-profit exits finally fire. The
thresholds were calibrated on one session of data — treat them as a first
estimate, not truth.
