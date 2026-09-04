# Dashboards — how the two surge pages are generated

PACA publishes two static pages on [surge.sh](https://surge.sh). Neither page
talks to Alpaca: a shell script exports fresh data files next to `index.html`
and redeploys the directory, and the page `fetch()`es those files when it
loads. Everything below is read-only with respect to trading — the exporters
never submit, cancel, or change an order.

| Page | URL | Directory | Data producer |
|---|---|---|---|
| Cycle monitor | [alpaca-hackathon-2026-artifacts-paca-cycles.surge.sh](https://alpaca-hackathon-2026-artifacts-paca-cycles.surge.sh) | `surge_artifacts/paca-cycles/` | `cli.py account --export`, `pnl.py`, the journal |
| Candles | [alpaca-hackathon-2026-artifacts-paca-candles.surge.sh](https://alpaca-hackathon-2026-artifacts-paca-candles.surge.sh) | `surge_artifacts/paca-candles/` | `export_candles.py` |

Both pages link to each other in their headers. The `/paca-agent` skill runs
both deploy scripts at the end of every cycle, so after a trading day they
reflect the latest cycle. To refresh by hand:

```bash
sh surge_artifacts/paca-cycles/deploy.sh
sh surge_artifacts/paca-candles/deploy.sh
```

Each script `cd`s into its own directory, calls the repo tools with
`uv run --env-file .env`, then runs `surge . <domain>`. Requires the surge CLI
(`npm install -g surge`) and a logged-in account (`surge whoami`).

## Cycle monitor

**What it shows.** The cycle journal (one card per cycle: candidates, gate
results, exits, entry decision, order receipts), open positions with Alpaca's
unrealized PnL, realized PnL per closed spread, and the trading config.

**How `deploy.sh` builds it.**

1. `cli.py account --export` writes `logs/account.json` (equity, options level,
   paired spreads, open premium at risk, warnings) and the script copies it
   into the page directory. Best effort: if the export fails, the previous
   snapshot is deployed and a warning is printed.
2. `pnl.py positions --json` → `positions.json` and
   `pnl.py realized --json --days 30` → `realized.json`. Each is written to a
   `.tmp` file and renamed only on success, so a failed export can never
   truncate the previous copy. Loguru warnings go to stderr, not into the JSON.
3. `settings.yaml` is dumped to `config.json` with the `llm` section removed,
   so model names stay private.
4. `logs/cycles.jsonl` is copied verbatim.
5. `surge . alpaca-hackathon-2026-artifacts-paca-cycles.surge.sh`.

**How the page reads it.** `index.html` fetches `cycles.jsonl` and parses it
line by line, skipping malformed lines. A missing journal is the only fatal
error (the page shows "redeploy"). The other four files are fetched
independently and each degrades to an empty panel if absent. Realized fills are
joined to cycles by `client_order_id`, which the agent builds deterministically
as `sp-<cycle_id>-enter-<SYM>` and `sp-<cycle_id>-exit-<SYM>-<strike tag>`.
`#cycle=<cycle_id>` deep-links to one cycle.

## Candles page

**What it shows.** For each whitelisted symbol, 5m candlesticks with the
indicators `signals.py` actually uses (RSI 14, ATR 14, MACD 12/26/9) plus
display-only EMA 11 and EMA 22, every bar where an entry event fired, and every
vertical spread the agent filled: a strike band from entry to exit (dotted while
open), a triangle at entry, an × at exit colored by P&L. Hover shows the trigger
event, thesis, debit, credit, exit reason and hold time. Below the chart the
same spreads appear as a table. Controls: 1d / 5d / 1m / All view, "Regular
hours only", and "Event markers".

**How `deploy.sh` builds it.** One step:
`export_candles.py --days 10 --out surge_artifacts/paca-candles/data.json`,
then `surge`. The exporter writes to `data.json.tmp` and renames on success.

**What `export_candles.py` does** (read-only; reuses the trading modules, no
new indicator math beyond the two EMAs):

- Bars: `market_data.fetch_ohlcv` for each symbol in `settings.yaml`, with
  `lookback_bars = days × 78 + 150` (78 regular-hours 5m bars per day plus
  indicator warm-up). Then `signals.add_indicators` for RSI/ATR/MACD and two
  `ewm(span=11|22)` columns.
- Events per bar: `bar_events` replays `signals.detect_events` over every bar
  with the same rules (previous-bar ATR, `atr_event_mult`,
  `macd_min_hist_atr`). A test asserts it agrees with `detect_events` on the
  last bar.
- Closed spreads: `broker.fetch_spread_fills` + `pnl.realized_frame`
  (FIFO-matched entry/exit fills with prices, times, P&L).
- Open spreads: `broker.fetch_account_state` + `pos_and_risk.pair_spreads`;
  the entry time comes from the matching `enter` fill.
- Journal join from `logs/cycles.jsonl`: exit reason (`stop`, `take_profit`,
  `expiry`, `reversal`) by the exit order's `client_order_id`; entry thesis,
  trigger events and cycle id by leg pair and cycle start time. Anything that
  does not match is `null`, never guessed. The LLM model name is not exported.

**`data.json` shape.**

```json
{
  "generated_at": "...", "timeframe": "5m", "days": 10,
  "settings": {"rsi_period": 14, "atr_period": 14, "macd": [12, 26, 9],
               "atr_event_mult": 2.0, "macd_min_hist_atr": 0.05,
               "rsi_overbought": 70, "rsi_oversold": 30, "ema": [11, 22]},
  "columns": ["t", "open", "high", "low", "close", "volume", "rsi", "atr",
              "macd", "macd_signal", "macd_hist", "ema11", "ema22"],
  "symbols": {
    "NVDA": {
      "bars":    [[1756740000, 227.1, 228.0, 226.9, 227.8, 73174, 61.2, 0.71, ...], ...],
      "events":  [[1756740300, ["macd_cross_up"]], ...],
      "spreads": [{"status": "closed", "type": "C", "direction": "CALL",
                   "expiration": "2026-09-09", "long_strike": 227.5, "short_strike": 235.0,
                   "qty": 11, "entered_at": 1756741200, "exited_at": 1756750800,
                   "entry_debit": 0.86, "exit_credit": 2.06, "pnl": 1320.0, "pnl_pct": 1.395,
                   "exit_reason": "take_profit", "thesis": "...", "events_at_entry": ["macd_cross_up"],
                   "cycle_id": "20260901-154703",
                   "exit_order": "sp-20260902-150504-exit-NVDA-260909C227500-235000"}]
    }
  },
  "warnings": []
}
```

Timestamps are epoch seconds UTC; the page renders them in US Eastern. Bars
are lists in `columns` order to keep the file small (about 1.4 MB for 15
symbols × 930 bars). `NaN` becomes `null`.

**Things to know.**

- The IEX feed returns a few pre-market and after-hours 5m bars per day. They
  are included in the indicator math, exactly as the live agent computes
  signals, but hidden by default ("Regular hours only" collapses 16:00–09:30
  and weekends).
- `--days` controls history. The default 10 gives about 13 trading days of
  bars; the 1m view button needs at least 21 to differ from All.
- Every redraw purges and rebuilds the Plotly figure. `Plotly.react` cannot
  recover once the container's DOM has been cleared, which is what made symbol
  switching go blank in the first version.
- Plotly is loaded from its CDN; surge sets no content-security policy.

## Conventions shared by both pages

- **Source is tracked, data is not.** `.gitignore` excludes
  `surge_artifacts/*` and re-includes only `index.html`, `deploy.sh` and
  `CNAME` per page. The exported JSON/JSONL copies are build output.
- **`CNAME`** holds the domain so a future session can redeploy without
  guessing it. Both use the `alpaca-hackathon-2026-artifacts-<slug>` prefix.
- **Privacy.** Pages are public the moment they deploy. Exports strip the
  `llm` section of settings and never include credentials. Client order ids and
  theses are considered fine to publish.
- **Theme.** Same design tokens and light/dark toggle (`paca-theme` in
  localStorage) so the two pages read as one project.
- **Adding a page.** Create `surge_artifacts/<slug>/` with `index.html`,
  `deploy.sh` (export → `surge . <domain>`) and `CNAME`; add the three
  `.gitignore` re-include lines; add the deploy call to
  `.claude/skills/paca-agent/SKILL.md` step 5 if it should refresh every cycle.
