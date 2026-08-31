# RegimePilot

An autonomous SPY options trading agent for the **Alpaca AI Trading Agents
Hackathon** (Aug 28 - Sep 4, 2026). This repository is the team's working
submission; the code was developed in phases and moved here from an earlier
practice repository.

> **Paper trading only.** Every client in this project is built with
> `paper=True` hard-coded and startup aborts on any live-trading signal, so the
> agent can only reach Alpaca's paper endpoint. Before submitting, check the
> account in `.env` is the **fresh paper account funded with exactly $100,000**
> the rules require: nothing in the code verifies that for you.

## Status: autonomous SPY options portfolio agent (paper)

Phase 3 adds read-only AI direction proposals (`BUY_CALL` / `BUY_PUT` / `HOLD`).
Phase 4 turns a proposal into one exact SPY option contract with deterministic
code. Phase 5A reads the real paper account (positions, open orders, equity,
options buying power). The portfolio `runner` turns that into an autonomous
agent: every held SPY option is managed independently (HOLD or CLOSE), at most
one new position is opened per cycle, exits are exact SELL_TO_CLOSE orders,
and every order passes deterministic risk (see "Run the portfolio agent").

| # | Phase | State |
|---|---------------------------------------|-------------|
| 1 | Environment and read-only connectivity | done |
| 2 | Read-only market observer + features | done |
| 3 | AI trade proposal, no execution | done |
| 4 | Deterministic contract selector (4A chain observation, 4B selection) | done |
| 5A | Read-only paper account state (positions, open orders, balances) | done |
| 5B-7 | Autonomous portfolio agent: HOLD/CLOSE per position, one entry per cycle, exact SELL_TO_CLOSE, paper execution, 15-minute loop | **current** |
| 8 | Dashboard and hackathon submission | not started |

**Not yet part of the numbered phases, added separately:** a pure regime
classifier (`regime.py`) and a backtest + scoring harness (`backtest.py`,
`score.py`, `black_scholes.py`) so a strategy change can be validated against
history before it reaches paper trading. See "Backtest and score a strategy
change" below. `regime.py`'s output is not yet wired into `evidence.py`'s
`EvidencePacket`, so it does not affect the live agent's decisions yet.

## Safety rules this code enforces

- Credentials are read from **environment variables only**.
- `ALPACA_PAPER` defaults to `true`, and an unrecognised value is an error, not a guess.
- Startup **aborts** if a live-trading flag (`ALPACA_LIVE`, `ALPACA_LIVE_TRADING`,
  `APCA_LIVE`) is true, or if any endpoint variable points at `api.alpaca.markets`.
- `TradingClient` is always constructed with `paper=True` hard-coded, so no
  environment value can flip it to live.
- Credentials live in `SecretStr` and are never printed or logged.
- `execution.submit_paper_order` is the **only** function that submits an order, and it
  runs only under `runner --execute`. Nothing cancels, replaces, closes or exercises.
- Unit tests make **no** network calls.

## Setup

Requires Python 3.11 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

### Create your `.env` yourself

`.env` is git-ignored and **must never be committed or pasted into a chat**.

1. Copy the template:

   ```bash
   cp .env.example .env      # PowerShell: Copy-Item .env.example .env
   ```

2. Open `.env` in an editor and paste your **paper** keys from
   <https://app.alpaca.markets/paper/dashboard/overview>:

   ```dotenv
   ALPACA_API_KEY=PK...your paper key...
   ALPACA_SECRET_KEY=...your paper secret...
   ALPACA_PAPER=true
   ```

3. Leave `ALPACA_PAPER=true`. Any other value stops the program.

4. For live LLM decisions (optional in Phase 3), add an OpenRouter key from
   <https://openrouter.ai/>:

   ```dotenv
   OPENROUTER_API_KEY=sk-or-...
   ```

   Use `--stub` if you do not have an OpenRouter key yet.

Do not set `ALPACA_BASE_URL` or `APCA_API_BASE_URL`. If you do, they must point at
`paper-api.alpaca.markets`; a live URL aborts startup.

## Run

Mocked unit tests (no credentials and no network needed):

```bash
uv run pytest
```

Read-only connectivity check (needs a filled-in `.env`):

```bash
uv run python -m regimepilot.smoke_test
```

Phase 2 feature observation:

```bash
uv run python -m regimepilot.history
uv run python -m regimepilot.history --json
```

Phase 3 modules:

```bash
# Filtered Alpaca news for SPY
uv run python -m regimepilot.news --json

# Full LLM briefing (features + news + pre-gates)
uv run python -m regimepilot.evidence --json

# Trade direction proposal
uv run python -m regimepilot.decision --stub --json   # no OpenRouter key needed
uv run python -m regimepilot.decision --json          # calls GLM-5.3 Flash via OpenRouter, free chain as fallback
```

`decision --json` prints one `TradeProposal`:

```json
{
  "observed_at": "2026-08-25T14:30:00+00:00",
  "symbol": "SPY",
  "action": "BUY_CALL",
  "confidence": "medium",
  "thesis": "Stub rule: 15m and 60m momentum align upward.",
  "evidence_used": ["gates.momentum_align", "underlying.return_15m", "underlying.return_60m"],
  "gate_skipped": false,
  "model": "stub"
}
```

Pre-gate failures return `action: "HOLD"` with `gate_skipped: true` without calling
the LLM.

Phase 4A chain observation (read-only; prints the SPY contracts around the money
for one direction with bid, ask, spread and quote age, and judges nothing):

```bash
uv run python -m regimepilot.chain --action BUY_CALL
uv run python -m regimepilot.chain --action BUY_PUT --json
```

`--action` is required and never comes from the LLM: this command exists to look
at real indicative quotes during market hours before any selection threshold is
chosen.

Phase 4B contract selection (read-only; runs evidence -> proposal -> chain ->
selection and prints one `SelectionResult`, or `--action` to select for a given
direction without the LLM):

```bash
uv run python -m regimepilot.selector --stub                # rule-based proposal, no OpenRouter key
uv run python -m regimepilot.selector --json                # LLM proposal, JSON result
uv run python -m regimepilot.selector --action BUY_CALL     # skip the LLM, select for one direction
```

Selection rules (approved 2026-08-26): expiration with days-to-expiration
nearest 7 within the 5-10 day window (ties go later), strike nearest the SPY
midpoint (ties go in-the-money), quotes rejected when not tradable, missing,
crossed, stamped in the future, older than 10 s by the server clock, or wider
than 350 bps of mid; the nearest acceptable strike at the same expiration is
taken instead, and the expiration is never changed. A `no_contract` result is a
normal outcome. No quantity, no price, no order.

Phase 5A account state (read-only; prints the paper account's equity, options
buying power, every open position and every open order, and whether any of them
is a SPY option contract):

```bash
uv run python -m regimepilot.account
uv run python -m regimepilot.account --json
```

A SPY option is an `us_option` position or order whose OCC root symbol is exactly
`SPY` (the same filter Phase 4A queries contracts with). Held SPY options become
the portfolio the agent manages; a pending order on a symbol blocks only actions
on that symbol (and new entries while a buy is pending). If any account read
fails, the whole cycle stops with an error rather than assuming an empty
account.

## Run the portfolio agent (one cycle, or the autonomous loop)

One command runs evidence -> entry gates -> portfolio context (every held SPY
option with its marks and journal memo, every pending order by symbol) -> LLM
`PortfolioDecision` (HOLD/CLOSE per position, at most one new entry) ->
deterministic risk per action -> orders, and appends one JSON line per cycle to
`logs/cycles.jsonl` (git-ignored). The default is a **dry run**: nothing is
submitted.

```bash
uv run python -m regimepilot.runner --stub                  # rule-based decision, dry run
uv run python -m regimepilot.runner                         # LLM decision, dry run
uv run python -m regimepilot.runner --enter CALL --execute  # force one entry (after the entry pre-check), real PAPER order
uv run python -m regimepilot.runner --close SPY260902P00765000 --execute   # close exactly this position
uv run python -m regimepilot.runner --loop --execute        # autonomous: the LLM manages, every 15 min, no per-trade approval
uv run python -m regimepilot.runner --json                  # the CycleRecord instead of the summary
```

`--execute` is the only way an order is submitted, and the trading client is
still built with `paper=True` hard-coded, so it can only reach the paper
endpoint. `--enter` / `--close` are validation helpers: they replace the model's
choice but never bypass the entry pre-check or the exit safety rules.

Approved methodology (2026-08-27): at most **3** open SPY option positions (a
pending buy counts), **1** new entry per cycle, **$1,000** premium per entry,
**$3,000** total premium; entries are buy-to-open, 1 contract, **limit at the
fresh ask**, day; an exit closes the **whole** fresh closable quantity of one
exact symbol, **limit at the fresh bid**, day, sell-to-close. Entry gates
(market open, >= 30 min to close, fresh bars, momentum) block only new entries;
a position can always be closed while the market is open, its quote is fresh,
and no order is pending on that symbol. Malformed model output means HOLD every
position and open nothing. Every cycle is journaled with the full evidence,
the decision, each action's risk verdict, plan and receipt.

## Backtest and score a strategy change before it goes to paper

`backtest.py` replays historical SPY minute bars through the **same** pure
pipeline the live runner uses (`features.build_feature_packet` ->
`gates.evaluate_gates` -> `regime.classify_regime` -> `decision.stub_proposal`
by default), so a backtest result reflects the real decision logic rather
than a parallel approximation of it. `score.py` turns the resulting trades
into a scorecard: win rate, profit factor, a per-trade Sharpe-like ratio, max
drawdown, and a buy-and-hold baseline for comparison.

Neither module touches the network, Alpaca, or an LLM by default, and neither
submits anything: `run_backtest` only ever appends to an in-memory list. Two
things are necessarily approximated because a historical SPY option chain is
not available to this project: contract premiums are simulated with
Black-Scholes (`black_scholes.py`) from the historical spot, a strike nearest
the money, a fixed 7-day expiration and an assumed volatility; and a
simulated position always closes at the same session's close rather than
being carried and managed across days the way the live portfolio agent can.
Both simplifications are documented in `backtest.py`'s module docstring —
read it before trusting a scorecard number for anything beyond a relative
comparison between two strategy variants.

`regime.py` is the other new addition: a pure classifier (no network) that
turns realized volatility, an ADX-like trend-strength reading, and (when a
real IV history is wired in) IV rank into one of `trending_up`,
`trending_down`, `high_vol_chop`, `low_vol_drift`, or `unknown`. `evidence.py`
does not yet attach a `RegimeReading` to the LLM's briefing — `regime.py`
exists and is tested, but wiring its output into `EvidencePacket` and adding
the regime-aware confidence override described in `decision.py`'s docstring
is the next step, not yet done here.

Both commands take historical minute bars as a CSV
(`timestamp,open,high,low,close,volume`, one row per minute).
`scripts/export_historical_bars.py` fetches them for you from Alpaca's IEX
historical bars (read-only, same paper-only client construction as the rest of
the project, submits nothing); it is not part of the trading pipeline.
`data/spy_minute_bars.csv` is committed as an **empty placeholder** — a header
row and no data — so run the export before the first backtest:

```bash
uv run python scripts/export_historical_bars.py \
    --start 2026-03-01 --end 2026-08-27 --out data/spy_minute_bars.csv

uv run python -m regimepilot.backtest --csv data/spy_minute_bars.csv
uv run python -m regimepilot.backtest --csv data/spy_minute_bars.csv --json

uv run python -m regimepilot.score --csv data/spy_minute_bars.csv
uv run python -m regimepilot.score --csv data/spy_minute_bars.csv --json
```

How much history comes back depends on the Alpaca plan behind your keys: the
IEX free tier covers only recent history, so check the plan's data window
before concluding a thin CSV means something is broken.

## Layout

```text
.
├── .env.example
├── pyproject.toml
├── README.md
├── data/
│   └── spy_minute_bars.csv   # empty placeholder; fill with the export script
├── scripts/
│   └── export_historical_bars.py  # read-only Alpaca bar export for backtest.py
├── src/regimepilot/
│   ├── config.py         # credential loading + paper-trading guards
│   ├── smoke_test.py     # Phase 1 connectivity check
│   ├── models.py         # frozen observation models
│   ├── observer.py       # Phase 2A read-only market observer
│   ├── features.py       # Phase 2B deterministic features
│   ├── history.py        # Phase 2B Alpaca bar/quote reads
│   ├── gates.py          # Phase 3A pre-gates + session labels
│   ├── regime.py         # regime classification: vol + ADX-like trend + IV rank (pure, new)
│   ├── news.py           # Phase 3B filtered Alpaca news
│   ├── evidence.py       # Phase 3C evidence briefing assembly
│   ├── decision.py       # Phase 3D LLM / stub trade proposal
│   ├── console.py        # tolerant console output (non-UTF-8 terminals)
│   ├── chain.py          # Phase 4A read-only option chain observation
│   ├── selector.py       # Phase 4B deterministic contract selection
│   ├── account.py        # Phase 5A read-only paper account state
│   ├── risk.py           # deterministic entry/exit risk -> OrderPlan (pure)
│   ├── execution.py      # fresh re-check + the only paper order submission (buy/sell)
│   ├── memory.py         # journal-backed position memory
│   ├── black_scholes.py  # pure BS pricing + implied vol solver (pure, new)
│   ├── backtest.py       # replay historical bars through the live pipeline (pure, new)
│   ├── score.py          # trades -> Sharpe-like scorecard + baseline (pure, new)
│   └── runner.py         # portfolio cycle runner, JSONL journal, 15-minute loop
└── tests/
    ├── test_config.py
    ├── test_smoke_test.py
    ├── test_observer.py
    ├── test_features.py
    ├── test_history.py
    ├── test_gates.py
    ├── test_regime.py         # new
    ├── test_news.py
    ├── test_evidence.py
    ├── test_decision.py
    ├── test_console.py
    ├── test_chain.py
    ├── test_selector.py
    ├── test_account.py
    ├── test_risk.py
    ├── test_execution.py
    ├── test_runner.py
    ├── test_memory.py
    ├── test_black_scholes.py  # new
    ├── test_backtest.py       # new
    ├── test_score.py          # new
    └── test_mvp_end_to_end.py
```

## Planned baseline (do not change without approval)

Monitor SPY only. Gather market data, option contracts, chain data and account
state. Emit one of `BUY_CALL`, `BUY_PUT`, `HOLD`. Deterministic code (not the LLM)
picks the exact contract and quantity. Every proposal passes hard risk checks.
Execution is Alpaca paper only. Every decision is logged, including `HOLD` and
rejected trades.

Phase 3 now includes filtered Alpaca news as LLM context. Out of scope for now:
multi-agent architectures, reinforcement learning, Jump or Hidden Markov Models,
vertical spreads and multi-leg options, 0DTE, multiple underlyings, automatic
strategy optimization.
