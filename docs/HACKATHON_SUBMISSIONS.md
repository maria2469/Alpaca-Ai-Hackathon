# What the other teams built

A category map of all 427 submitted projects from the [Alpaca AI Trading Agents Hackathon](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon), built from each team's written summary on lablab.ai as fetched on 2026-09-04. Only the summaries were read; presentations and repositories were not reviewed. Community votes are shown for context. Winners were not announced at the time of writing. Categories were proposed and assigned by an LLM from the summaries, so boundaries are approximate; see [Method](#method).

Contents: [Directional options on signals (76)](#directional-options-on-signals) · [Options premium selling / income (76)](#options-premium-selling--income) · [LLM-discretionary agents behind a governance layer (65)](#llm-discretionary-agents-behind-a-governance-layer) · [Multi-agent debate / committee decisions (50)](#multi-agent-debate--committee-decisions) · [Volatility relative value & regime-routed structures (48)](#volatility-relative-value--regime-routed-structures) · [News, sentiment & scheduled-event trading (26)](#news-sentiment--scheduled-event-trading) · [Equity & crypto spot trading on signals (18)](#equity--crypto-spot-trading-on-signals) · [Strategy discovery & self-improving research loops (18)](#strategy-discovery--self-improving-research-loops) · [Trader copilot, chat & education (16)](#trader-copilot-chat--education) · [Risk & portfolio management overlays (14)](#risk--portfolio-management-overlays) · [Infrastructure, safety harnesses & tooling (8)](#infrastructure-safety-harnesses--tooling) · [Arbitrage, pairs & market making (7)](#arbitrage-pairs--market-making) · [Other (5)](#other) · [Category definitions](#category-definitions) · [Method](#method)

## Category definitions

| Category | What it covers | Projects |
|---|---|---|
| [Directional options on signals](#directional-options-on-signals) | A directional signal (technical indicators, momentum, options flow, or an LLM thesis) picks bullish or bearish, and the agent buys calls or puts or opens a vertical spread (debit or credit) in that direction, with stop-loss and take-profit exits. | 76 |
| [Options premium selling / income](#options-premium-selling--income) | Harvests option premium as the stated return source: cash-secured puts, covered calls, the wheel, iron condors or credit spreads sold systematically (often as a variance-risk-premium play) rather than to express a directional call. | 76 |
| [LLM-discretionary agents behind a governance layer](#llm-discretionary-agents-behind-a-governance-layer) | No named signal or edge: the model reads the market and picks a trade, usually from an allowlist of defined-risk structures, and the project's pitch is the deterministic gates, refusal ledger, audit trail or fail-closed plumbing around it. | 65 |
| [Multi-agent debate / committee decisions](#multi-agent-debate--committee-decisions) | The headline is the decision architecture: a council, debate, jury or chain of specialized LLM agents (analyst, bull, bear, risk, supervisor) produces the trade decision, and no single instrument-level strategy dominates the pitch. | 50 |
| [Volatility relative value & regime-routed structures](#volatility-relative-value--regime-routed-structures) | The edge is measured volatility, not direction: implied vs realized or forecast vol, skew or term structure, or a regime classifier that switches between credit and debit structures. The agent can be long or short vol, and often ranks candidate structures by probability of profit or expected value. | 48 |
| [News, sentiment & scheduled-event trading](#news-sentiment--scheduled-event-trading) | Entries are triggered by news flow, social sentiment, filings, insider or congressional disclosures, or a scheduled catalyst such as earnings (IV-crush condors, pre-report straddles) rather than by price signals. | 26 |
| [Equity & crypto spot trading on signals](#equity--crypto-spot-trading-on-signals) | Trades stocks, ETFs or crypto spot (not options) on momentum, trend, mean-reversion, z-score or fundamental quality scores; the LLM, if any, confirms or explains rather than originates. | 18 |
| [Strategy discovery & self-improving research loops](#strategy-discovery--self-improving-research-loops) | The core loop generates, backtests, stress-tests and scores strategies or the agent's own past decisions, then allocates capital or rewrites its rules from the results. A post-trade reflection memory bolted onto a fixed strategy does not qualify. | 18 |
| [Trader copilot, chat & education](#trader-copilot-chat--education) | A human stays in the loop: chat assistants, trade-idea explainers, one-click approval workflows, journaling or teaching tools that recommend rather than execute autonomously. | 16 |
| [Risk & portfolio management overlays](#risk--portfolio-management-overlays) | The product manages an existing portfolio's risk: hedging, rebalancing, exposure or drawdown limits, tail protection, or allocation across sleeves, rather than originating directional trades. | 14 |
| [Infrastructure, safety harnesses & tooling](#infrastructure-safety-harnesses--tooling) | MCP servers, SDK wrappers, broker-side safety or certification gates for any agent, stress-test harnesses, audit and replay tooling, dashboards or frameworks, where the trading strategy is only a demo payload. | 8 |
| [Arbitrage, pairs & market making](#arbitrage-pairs--market-making) | Trades relationships that should revert rather than direction: cointegrated pairs and stat-arb, cross-asset or cross-venue price gaps, no-arbitrage violations on the options surface, or two-sided market making with delta hedging. | 7 |
| [Other](#other) | Not a trading agent (unrelated apps, placeholders) or too vague to place. | 5 |

## Directional options on signals

A directional signal (technical indicators, momentum, options flow, or an LLM thesis) picks bullish or bearish, and the agent buys calls or puts or opens a vertical spread (debit or credit) in that direction, with stop-loss and take-profit exits.

- **[AlphaPilot AI](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/quantum-coders/alphapilot-ai)** — Quantum Coders · 27 votes  
  AlphaPilot AI is an automated SPY options paper-trading platform combining multi-factor signals, intelligent contract selection, risk controls, real-time monitoring, and performance analytics for transparent, zero-risk…  
  *Notable:* Contract scanner ranks the chain by DTE, strike proximity, open interest and liquidity; entry manager checks position collision and duplicate orders.
- **[SentryTheta AI - Autonomous Options Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/agent-00trade/sentrytheta-ai-autonomous-options-trading-agent)** — SentryTheta AI · 24 votes  
  SentryTheta AI is an autonomous options trading desk combining LLM market sentiment reasoning with deterministic mathematical risk guardrails and live execution on Alpaca Paper Trading.  
  *Notable:* Exit harvester rescans open contracts every 60 seconds for -15% stop and +30% take-profit; dashboard offers copilot one-click and autopilot modes.
- **[Alpacca trading bot](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/meridian/alpacca-trading-bot)** — Meridian · 15 votes  
  An autonomous AI agent that trades options on Alpaca paper trading: one LLM picks a direction, a second structures the trade against live option chains, and deterministic risk gates hold final veto power before anything…  
  *Notable:* The structuring LLM fetches option chains itself via MCP but cannot place orders; ticker screening stops cleanly when the daily LLM quota runs out.
- **[VegaGuard: Auditable AI Options Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/oster/vegaguard-auditable-ai-options-agent)** — OSTER · 7 votes  
  A paper-only autonomous options agent that scans ETFs, constructs defined-risk debit spreads, applies deterministic risk gates, executes through Alpaca MCP, monitors positions, and records an auditable trading lifecycle.  
  *Notable:* Shadow pipeline records hypothetical 15/30/60-minute outcomes for rejected candidates using ask-to-enter, bid-to-exit pricing; execution needs an expiring plan ID.
- **[AlphaQuant AI: Autonomous Options Trading Copilot](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/sahariar-dev/alphaquant-ai-autonomous-options-trading-copilot)** — Sahariar-Dev · 4 votes  
  Autonomous multi-agent options trading swarm powered by Alpaca MCP Server v2.1.0 and Trading APIs. Features Call/Put strategies on US equities, consensus voting, real-time Greeks (Delta/Theta), and defined-risk gates…  
  *Notable:* Four LLM personas vote deterministically (3/4 majority or unanimous) on call/put bias; contracts under 7 DTE are rejected for theta decay.
- **[Options Sniper - Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/primehack-security-team/options-sniper-trading-agent)** — primehack security team · 3 votes  
  Autonomous agent that scans 7 tickers, builds scored Bull Call Spreads, and paper-trades them on Alpaca with live API monitoring and auto-exit.  
  *Notable:* No LLM: keyword news sentiment adjusts the 0-120 score by plus or minus 5 and near corporate actions reject trades; short legs close first.
- **[Convexity — the agent that cannot buy a wide book](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/convexity/convexity-the-agent-that-cannot-buy-a-wide-book)** — Convexity · 2 votes  
  A paper options agent on Alpaca where no model sits in the fill path. Every entry clears a mandatory RiskGate on a fresh quote, priced at the ask and never the mid. A 15-second brain supervises the book and can only…  
  *Notable:* RiskGate prices entries at the ask, never mid; a losing day where every trade-level gate passed showed nothing checked correlated portfolio exposure.
- **[Signal Hunter](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/signal-hunter/signal-hunter)** — Signal Hunter · 2 votes  
  Signal Hunter is an autonomous AI agent that detects unusual options flow, reasons about catalysts and IV with an LLM, and trades within hard, code enforced risk limits via Alpaca's Trading API and MCP server.  
  *Notable:* A separate process manages exits against profit target, stop loss and a hard 3:45pm ET time stop with no LLM involvement.
- **[TradePilot AI](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/trade-pilot/tradepilot-ai)** — Trade Pilot · 2 votes  
  Autonomous, explainable AI trading agents on Alpaca that trade stocks and options. The AI proposes, a deterministic risk engine decides, and every step is logged in a full audit trail.  
  *Notable:* Agents reach the Alpaca MCP server through a read-only tool allowlist so they never see order-placement tools; execution goes via CLI.
- **[AeroQuant — Autonomous Options Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/kraven/aeroquant-autonomous-options-trading-agent)** — Kraven · 1 vote  
  A three-layer autonomous agent — deterministic quant signals, LLM reasoning, and a hard Python risk gate — that trades single-leg options on Alpaca paper trading with fail-closed safety controls throughout.  
  *Notable:* Code builds an exact whitelist of tradeable contracts; the LLM may only pick a candidate_id or WAIT, so it can never invent a contract.
- **[AI Options Trader](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/phantom-protocol/ai-options-trader)** — Phantom Protocol · 1 vote  
  Autonomous AI agent that analyzes options chains and executes multi-strategy trades with real-time dashboard.  
  *Notable:* Browser-resident agent scans options chains every 30 seconds across six rule-based strategies, sizing each trade to a 2% max risk.
- **[Alpaca Options Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/alpaca-options-agent/alpaca-options-agent)** — Alpaca Options Agent · 1 vote  
  AI-assisted options trading decisions combining Alpaca market data, technical signals, LLM reasoning, deterministic risk gates, and auditable decision history.  
  *Notable:* Decision log separates APPROVED, LLM_REJECTED and RISK_REJECTED outcomes so LLM vetoes and gate vetoes can be audited apart.
- **[AlphaDesk: Bounded-Risk AI Options Trading Desk](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/skypto/alphadesk-bounded-risk-ai-options-trading-desk)** — skypto · 1 vote  
  AlphaDesk is an institutional-grade options research and paper trading desk combining Alpaca market data, AI market intelligence, deterministic bounded-risk math, and fail-closed Guardian supervisory controls across…  
  *Notable:* Public demo workspace is architecturally barred from constructing broker adapters; LLMs are read-only advisors with no execution or risk-parameter authority.
- **[AlphaShield Prime: Autonomous Options Engine](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/the-eagle-the-lion-the-wolf/alphashield-prime-autonomous-options-engine)** — The Eagle The Lion The Wolf · 1 vote  
  Autonomous quantitative options desk executing defined-risk SPY contracts via Alpaca CLI binary IPC, guided by a Featherless GLM-5.2 Tri-Agent Council and protected by a deterministic Dual-Veto Risk Governor with…  
  *Notable:* Strategy Darwinism allocates capital by empirical edge score and quarantines or decommissions strategies whose score drops below 50.
- **[Augur](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/augur/augur)** — Augur · 1 vote  
  Augur is an autonomous SPY options trading agent that uses auction-market reasoning, Alpaca execution, explicit risk controls, and a verifiable audit trail for every decision.  
  *Notable:* Forms a falsifiable Auction Market Theory thesis every five minutes; a separate risk watcher enforces stops, break-even moves and session-close exits.
- **[CrossSignal: Auditable Cross-Market Options AI](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/frenimi/crosssignal-auditable-cross-market-options-ai)** — CrossSignal · 1 vote  
  CrossSignal uses AI to detect cross-market disagreements, challenge each thesis, and authorize only defined-risk Alpaca options trades that pass deterministic risk and execution gates.  
  *Notable:* Seals a SHA-256 Decision Contract with an invalidation condition before the outcome, then scores it against inverse and cash counterfactuals.
- **[DeltaMind_ai](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/lmentrics/deltamindai)** — Lmentrics · 1 vote  
  DeltaMind AI is an autonomous options-trading agent on Alpaca that gates every setup through hard, auditable risk thresholds before an LLM ever gets a say.  
  *Notable:* Deterministic hourly-trend plus fast-crossover screener must confirm momentum before any LLM call is spent; rejected setups logged with exact reason.
- **[Evidence-Gated Autonomous Options Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/corelab/evidence-gated-autonomous-options-agent)** — CoreLab · 1 vote  
  AI-verified, risk-controlled paper options trading on Alpaca  
  *Notable:* LLM verifier receives only a compact evidence packet and returns approve, reject or abstain; it cannot alter contracts or quantity.
- **[FVG Copilot: Multi-Agent Options Trading on Alpaca](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/teamhobbsian/fvg-copilot-multi-agent-options-trading-on-alpaca)** — TeamHobbsian · 1 vote  
  An AI agent pipeline (Scout, Risk Guardian, Executor) that turns a production Fair Value Gap equity strategy into an options trader on Alpaca, backtested to a 48.9% win rate and +$1,295 P&L across 1,569 trades on real…  
  *Notable:* Backtest on real historical options prices exposed same-timestamp entry/exit collisions from daily bars that faked zero P&L.
- **[KRAKN.AI](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/aussie-trading/kraknai)** — Aussie trading · 1 vote  
  An autonomous AI trading agent that finds, executes and manages crypto and US stock trades — without human intervention.  
  *Notable:* Every five closed trades, Claude adjusts 15 signal weights from outcomes; a Fear and Greed filter only permits entries during fear.
- **[Momentum Options Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/algotrade/momentum-options-agent)** — AlgoTrade · 1 vote  
  AI agent trading options on Alpaca via a momentum-and-pullback strategy, a hard risk governor, and an LLM reasoning layer. Built on the Alpaca CLI + Trading API, it scans movers, buys ATM calls/puts, and manages each…  
  *Notable:* Enters ATM options only on a pullback when daily and intraday direction agree; trailing ratchet exit simulated agent-side since Alpaca lacks option trailing stops.
- **[MSAR_HMM_Gamma_Trend_Strategy](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/wall-street-quant/msarhmmgammatrendstrategy)** — Wall Street Quant · 1 vote  
  Completed Short description: 4 calculational signal: MSAR (Markov Switching Autoregression), HMM (Hidden Markov Model), Option Greeks (Dealer Gamma), Trend following, at the validation stage right now  
  *Notable:* Validates the strategy with 10,000 block-bootstrapped counterfactuals and a permutation null, publishing the two failing checks on the dashboard.
- **[OCHOA: LLM Options Sniper & Risk Guardian](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/digueti/ochoa-llm-options-sniper-and-risk-guardian)** — Digueti · 1 vote  
  OCHOA is an autonomous AI Options trading agent. It pairs a predictive LLM "Brain" with a deterministic "Risk Guardian" that safely manages capital and executes orders on the S&P 500 and Mag 7 directly via the Alpaca…  
  *Notable:* LLM only emits a 0-100 Brain Score from news plus RSI/MACD; thresholds (>65 calls, <35 puts) trigger signals a deterministic guardian executes.
- **[OptionProof — Agents Propose, Evidence Decides](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/verified-alpha/optionproof-agents-propose-evidence-decides)** — Verified Alpha · 1 vote  
  An autonomous Alpaca options agent that scans ten liquid ETFs, challenges every AI proposal, and lets deterministic evidence and risk code authorize paper trades.  
  *Notable:* Scans ten ETFs for opening-range breakouts and range-edge rejections; a critic tries to falsify the chosen thesis before code grants one-use execution authority.
- **[optionwright — LLM proposes, code decides](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/optionwright/optionwright-llm-proposes-code-decides)** — optionwright · 1 vote  
  Autonomous options agent on Alpaca where the LLM proposes a direction and deterministic code decides every strike, size, and exit. Defined-risk spreads only, so maximum loss is fixed before each order fills.  
  *Notable:* Code pre-builds both a bull put and bear call spread with all numbers computed; the LLM returns only direction or abstain, gates can only shrink.
- **[Quiet Alpha](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/spartan/quiet-alpha)** — Spartan · 1 vote  
  Auditable SPY weekly credit-spread agent. Gemini judges direction; deterministic Python handles spread selection, 8 risk gates, sizing, and Alpaca paper execution. 6-month backtest (+$1,989, 81.8% win rate) and a real…  
  *Notable:* Validated three ways: six-month backtest on Alpaca data, a broker-confirmed autonomous paper round-trip, and 29+ fault-injection tests that fail closed.
- **[SPY Macro-Regime Options Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/niranda/spy-macro-regime-options-agent)** — Niranda · 1 vote  
  An autonomous quantitative trading agent for SPY options. Driven by ML regime classification and Alpaca's SDK/CLI, it executes 7–14 DTE ATM Call/Put orders with hard-capped 3% position risk sizing and sequence…  
  *Notable:* ML regime ensemble outputs a binary stance mapped to ATM SPY calls or puts; existing positions are liquidated before the new stance opens.
- **[Trade trooper](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/bananas/trade-trooper)** — Bananas · 1 vote  
  Trade-Trooper is an autonomous multi-agent options trading engine combining FinBERT sentiment, technical analysis, and deterministic risk management.  
  *Notable:* Sector-specific strategy weights are tuned with Optuna on historical data; a local Ollama model only writes explanations, never touches execution.
- **[TradeCouncil — Multi-Agent Options Alpha](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/silvercrane/tradecouncil-multi-agent-options-alpha)** — SilverCrane · 1 vote  
  TradeCouncil is a multi-agent options trading system using Featherless AI and Alpaca. Bull and Bear agents debate each setup, a CIO selects CALL, PUT, or NO TRADE, and deterministic risk gates can veto execution.  
  *Notable:* Deterministic indicator screen sends only the strongest candidates to the LLM debate, conserving inference credits before contract selection and risk veto.
- **[Tradenum](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/tradenum/tradenum)** — TradeNum · 1 vote  
  Tradenum watches unusual options flow on real stocks, builds defined-risk spreads, and runs Python risk gates before posting multi-leg orders to Alpaca paper. Gates that block are visible on a six-node play graph.  
  *Notable:* Classifies unusual option prints as follow, fade, or pass; quality gates can be overridden by a human stamp, hard gates cannot.
- **[VOLMIND — Autonomous Options Research Terminal](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/volmind/volmind-autonomous-options-research-terminal)** — Volmind · 1 vote  
  VOLMIND is an autonomous options trading terminal on Alpaca. LangGraph agents form an independent probability estimate, weigh it against market-implied pricing, pass diligence and risk review, then execute, monitor, and…  
  *Notable:* Trades the gap between an evidence-required AI probability estimate and market-implied probability from the option chain; unsupported forecasts get confidence clamped.
- **[Yield-paca: Multi-Agent AI Trading System](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/yield-paca/yield-paca-multi-agent-ai-trading-system)** — Yield-paca · 1 vote  
  Yield-paca is a multi-agent AI trading platform built on the. Its LLM-driven research, debate, and execution agents with risk gates, orchestrating three strategies through Temporal.io in Ruby on Rails — running safely…  
  *Notable:* MCP scoping as the safety boundary: only PortfolioManager holds trading tools, so the Trader LLM cannot submit orders even under prompt injection.
- **[ADQuant — Autonomous Agentic Options Trading Desk](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/adquant/adquant-autonomous-agentic-options-trading-desk)** — ADQuant · 0 votes  
  ADQuant is a fully autonomous AI options trading system built on LangGraph with multiple strategy agents reasoning, and Alpaca MCP execution. It scans assets, runs a confluence tournament, and trades US equity options…  
  *Notable:* IV-rank routes structure (long options, verticals, or credit spreads); the exit LLM is called only at PnL/DTE inflection points, cutting calls ~70%.
- **[Aegis Alpha: The Options Agent That Can Say No](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/alpecking/aegis-alpha-the-options-agent-that-can-say-no)** — ALPECKING · 0 votes  
  An explainable Alpaca paper-options agent that ranks SPY and QQQ debit spreads, applies deterministic risk controls, and blocks execution whenever market data, liquidity, exposure, or account state is unsafe.  
  *Notable:* Alpaca CLI provides an independent account and position view; any disagreement with the alpaca-py view blocks new orders.
- **[Aegis-OptionAI: Risk-Governed Options Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/weareherejustforthebuffet/aegis-optionai-risk-governed-options-agent)** — weareherejustforthebuffet · 0 votes  
  An autonomous options trading agent where an LLM proposes defined-risk vertical spreads, while deterministic stress tests and hard risk gates control every Alpaca paper-trading execution.  
  *Notable:* Chaos Sandbox reprices each proposed spread under 6x bid-ask widening, IV cut to 20%, and a 10% adverse move before hard vetoes apply.
- **[AEGIS-Q](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/team-v/aegis-q)** — Team V · 0 votes  
  AEGIS-Q is an autonomous options agent where bounded AI selects a pre-validated bullish or bearish spread—or abstains—while deterministic code controls contracts, position sizing, maximum loss, execution and exits…  
  *Notable:* Code builds one fully validated bullish and one bearish debit spread first; the AI may only pick one or abstain, never alter contracts or size.
- **[Aizen Autonomus Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/aizen-syndicate/aizen-autonomus-trading-agent)** — Aizen Syndicate · 0 votes  
  Multi-agent options trader on a LangGraph state machine: nine specialized agents, a news-driven GATv2 GNN, XGBoost option models, and a deterministic risk gate that refuses contradictory signals. Live paper-traded via…  
  *Notable:* Direction-mismatch gate blocks long puts on bullish signals; supervisor refuses any cycle where agents disagree or a recent realized loss exists on the symbol.
- **[Alpaca 0DTE Auto Trade](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/kiba/alpaca-0dte-auto-trade)** — KIBA · 0 votes  
  An autonomous 0DTE options agent on Alpaca that turned a fresh $100,000 paper account into $179,087 in three sessions. Max loss capped by construction, code-enforced gates, orders via the Alpaca CLI, and a full audit…  
  *Notable:* Claude layer is scoped as a veto that can only remove trades, never add them; hard 15:50 ET flatten keeps 0DTE from expiring.
- **[Alpaca AI Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/findalpaca/alpaca-ai-trading-agent)** — FindAlpaca · 0 votes  
  Autonomous AI trading agent using Alpaca’s paper trading API with options spreads, technical analysis, and risk management. Features real‑time Streamlit dashboard, automated trade execution, and comprehensive logging.  
  *Notable:* RSI/MACD/Bollinger signals drive bull call and bull put spreads with confidence-based position scaling under a 2% per-trade and $5,000 daily loss cap.
- **[Alpaca MCP Options Flow Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/import-alpha/alpaca-mcp-options-flow-agent)** — Import Alpha · 0 votes  
  Custom MCP server for Alpaca options flow detection powering a multi-agent AI trading system with defined-risk strategies.  
  *Notable:* A custom MCP server detects sweeps, block trades and volume spikes from Alpaca's WebSocket stream and uses that flow as the entry signal.
- **[alpaca_options_alpha_agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/ai-trader/alpacaoptionsalphaagent)** — ai trader · 0 votes  
  **AlphaPilot AI** is an autonomous AI-powered options trading agent built for the Alpaca Options Alpha Agents challenge. The system uses  
  *Notable:* EMA20/50, RSI, MACD, ATR and momentum are combined into one confidence score that gates a CALL/PUT/HOLD decision before contract selection.
- **[Alpha Council](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/jfkelly89/alpha-council)** — JFKELLY89 · 0 votes  
  An autonomous options paper-trading desk that debates its trades: a quant funnel finds candidates, GPT analysts propose, a Claude Red Team attacks, and a deterministic Risk Constitution decides — then measures whether…  
  *Notable:* Stores each decision as GPT proposal, Red Team change and execution so every governance layer's P&L contribution is measurable; refusals get shadow records.
- **[AlphaGate: Autonomous Options Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/include-logic/alphagate-autonomous-options-trading-agent)** — #include logic · 0 votes  
  An autonomous options agent: a deterministic screener finds momentum breakouts, Claude judges entries, and hard-coded risk gates have final veto power over every trade on Alpaca.  
  *Notable:* Because Alpaca options lack broker-side brackets, the agent runs its own premium-based and underlying-price stops/targets plus forced pre-expiry exits.
- **[AlphaPilot - Autonomous Options Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/lv/alphapilot-autonomous-options-agent)** — LV · 0 votes  
  An autonomous AI options trading agent that combines quantitative signals, AI reasoning, and deterministic risk controls to discover opportunities, evaluate trades, execute paper orders, and continuously manage…  
  *Notable:* A decision journal traces each trade from the originating market signal through AI evaluation, risk validation, execution and outcome.
- **[Autobelay - Long Premium, Short Leash](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/razorsedge/autobelay-long-premium-short-leash)** — RazorsEdge · 0 votes  
  An autonomous options agent on Alpaca's MCP server. An open-source model (Featherless) researches bars, chains and news, then proposes defined-risk premium trades; deterministic code sizes, stops and closes every one.…  
  *Notable:* Model prose is audited against its own inputs, priors are Brier-scored nightly, and the end-of-day critique comes from a model that did not trade.
- **[Breeze Trading](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/breeze-3/breeze-trading)** — Breeze 3 · 0 votes  
  An autonomous options trading architecture engineered to eliminate unconstrained model hallucination by separating probabilistic market reasoning from deterministic risk enforcement.  
  *Notable:* Requires Daily-to-4H trend alignment before scanning lower timeframes for continuation flags or 1H breakout-and-hover reversals.
- **[BullRun](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/capital-trader/bullrun)** — Capital Trader · 0 votes  
  AI proposes. Evidence decides. Humans authorize. A governed AI options trading agent with 12 deterministic risk gates, human consent, and SHA-256 audit trail on Alpaca paper trading.  
  *Notable:* After the LLM proposed 18% allocation despite a 2% limit, safety was rebuilt as hardcoded gates; missing data defaults to REJECT.
- **[ClockCross: Evidence-Gated AI Options Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/sss/clockcross-evidence-gated-ai-options-agent)** — SSS · 0 votes  
  ClockCross turns BTC-to-COIN repricing gaps into defined-risk Alpaca option spreads. AI can choose the thesis; chronological evidence and deterministic risk gates decide whether it becomes a trade.  
  *Notable:* Estimates COIN's expected move from BTC pre-open and trades only the unexplained residual; AI picks continuation, reversion or abstain, nothing else.
- **[Cloudrise Alphaca Ai trading app](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/cloudrise/cloudrise-alphaca-ai-trading-app)** — CloudRise · 0 votes  
  Alphaca Ai trading app. They see the market and tell you the result  
  *Notable:* Four indicator agents (EMA regime, momentum, breakout, RSI reversion) evaluate each ETF; the RSI agent can veto overcrowded entries.
- **[CONVEX](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/jenny-builds/convex)** — Jenny Builds · 0 votes  
  An autonomous SPY options agent on Alpaca's MCP server trading 0DTE, zero days to expiration. On 1 September, 43.8% of priced candidates showed a profit before costs that the spread ate entirely. It publishes its…  
  *Notable:* Ranks 0DTE candidates by profit after bid-ask spread before any risk check; 43.8% of candidates were eaten entirely by the spread.
- **[ConvictionSpread: Explainable Options Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/it-works-but-why/convictionspread-explainable-options-agent)** — It-works-but-why! · 0 votes  
  My friend and I built an explainable Alpaca paper-trading agent that turns market regime, momentum and volume into risk-gated bull call or bear put debit spreads, with a clear reason behind every decision.  
  *Notable:* Walk-forward testing against buy-and-hold, momentum and random-direction baselines, with one-contract paper canaries and duplicate-safe recovery from network timeouts.
- **[DeepSees Options Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/deepsees/deepsees-options-agent)** — DeepSees · 0 votes  
  Autonomous multi-agent options trading system. Six LLM agents make judgments; deterministic code computes every number, enforces every limit, and places every order.  
  *Notable:* Exit schema cannot express a wider stop, so a model attempting it fails at parse; the risk layer is monotone toward smaller and safer.
- **[DeltaForge](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/thetaforge/deltaforge)** — ThetaForge · 0 votes  
  An autonomous options agent on a validated 30-minute momentum signal: slightly-ITM calls, closed by the underlying's own stop, 3R target and DTE clock. Backtested on real Alpaca options data; +7.25% in four live paper…  
  *Notable:* Exits the call using the underlying's own levels (8-bar pivot stop, 3R target, 5-DTE clock); edge is loss asymmetry at the stop, not hit rate.
- **[DELTAX V2 — Autonomous AI Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/deltax/deltax-v2-autonomous-ai-trading-agent)** — Deltax · 0 votes  
  DELTAX V2 is an autonomous AI stock and options trading agent that combines technical signals, real-time news analysis, deterministic risk gates, Alpaca paper execution, position monitoring, and a fully auditable…  
  *Notable:* Technical signal first, AI confirms against news, then gates check confidence, conflicting news, and exposure; 1% planned loss, 3% halt, 5% kill switch.
- **[Evidence Governor: Permissioned AI Trading](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/jinho/evidence-governor-permissioned-ai-trading)** — Jinho · 0 votes  
  An auditable SPY options agent where AI may select a locked candidate or abstain, while deterministic evidence, sizing, risk gates, and Alpaca Paper execution retain final authority.  
  *Notable:* Code builds two vertical candidates and a locked evidence packet; the LLM may only choose A, B, or abstain, with invented evidence IDs failing closed.
- **[Evie - Electronic Volatility Intelligence Entity](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/evie/evie-electronic-volatility-intelligence-entity)** — evie · 0 votes  
  EVIE (Electronic Volatility Intelligence Entity) is a fully autonomous quant engine that combines strict technical analysis with a Gemini LLM Risk Gate to execute high-probability options trades on Alpaca via FastMCP.  
  *Notable:* Injects the last exit price and timestamp into the LLM prompt so it can distinguish a valid new setup from a re-entry chase.
- **[Gated Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/gated-agent/gated-agent)** — Gated Agent · 0 votes  
  An options agent that red-teams its own risk before every order — toy signal, real discipline.  
  *Notable:* Runs a seeded random twin on a shadow book as a placebo arm, with pre-registered exit rules frozen in config before the contest.
- **[Gatekeeper: the model proposes, code disposes](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/gate-zero/gatekeeper-the-model-proposes-code-disposes)** — Gate Zero · 0 votes  
  An autonomous options trading agent on Alpaca where Claude proposes every trade and 14 deterministic Python gates decide whether it is allowed to execute. The risk limits live in code the model cannot reach, not in the…  
  *Notable:* Regime call mechanically sets risk budget and forbids directions; targets Thursday expiry so no spread is open at peak gamma on judging Friday.
- **[golden_ticket: autonomous options agent on Alpaca](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/goldenticket/goldenticket-autonomous-options-agent-on-alpaca)** — golden_ticket · 0 votes  
  Autonomous long-options agent, unattended on Alpaca since July: scanner → screen → risk-gated entries → 12 s exit stack with a broker-side GTC failsafe, boot-validated risk config, Alpaca CLI reconciliation. 123 real…  
  *Notable:* 25 risk parameters are range- and relationship-checked at boot and the engine refuses to start on an incoherent set.
- **[iPulse AI Options Alpha Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/ipulse-ai-open-lab/ipulse-ai-options-alpha-agent)** — iPulse AI Open Lab · 0 votes  
  Inspectable six-advisor options research with deterministic risk gates, broker-verified Alpaca paper fills, and honest out-of-sample validation.  
  *Notable:* Rule frozen on 2021-2023 data, then tested on untouched 2024-2026 data; the failed momentum v0 is published alongside the winner.
- **[Momentum Intelligence Agent (MIA)](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/a9/momentum-intelligence-agent-mia)** — A9 · 0 votes  
  Momentum Intelligence Agent — Autonomous options trading system. K2 Analyst builds the thesis, Qwen Critic tries to falsify it. 11 deterministic risk gates. Alpaca paper execution. Every decision auditable. Every trade…  
  *Notable:* Seven deterministic exit conditions (including thesis expiry, momentum decay, regime change) monitor positions against their entry thesis; the AI never authorizes closes.
- **[PACA: Position-aware Agentic Capital Allocator](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/win-or-die/paca-position-aware-agentic-capital-allocator)** — Win or Die **(ours)** · 0 votes  
  An agentic system that uses momentum signal to trade vertical spread managed by an agent.  
  *Notable:* Momentum events (gaps, breakouts, MACD crosses) plus gates that drop exhausted or already-held names before the LLM picks at most one debit spread.
- **[Quant Mosquito](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/mosquito-gang/quant-mosquito)** — mosquito gang · 0 votes  
  An autonomous options trading agent that reasons over real SPY indicators and live news with an LLM, sizes trades by confidence, auto-manages exits, and trades on Alpaca's paper API and CLI — validated with real…  
  *Notable:* Hourly SPY indicators plus news go to an LLM whose confidence sets position size; the underlying signal was backtested over 90 days to inform it.
- **[Quant Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/bajwa-bulls/quant-trading-agent)** — Bajwa Bulls · 0 votes  
  An autonomous, explainable AI options desk live on Alpaca paper trading.  
  *Notable:* A Defense Mode monitors open positions and deploys a protective put, covered call or collar when capital-at-risk or drawdown thresholds are breached.
- **[Reinforcement Learning-First Live Options agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/team-basavaprasanna/reinforcement-learning-first-live-options-agent)** — Team Basavaprasanna · 0 votes  
  OptionRelay is a RL driven options paper-trading workflow. An end-of-day DQN converts historical options into structured trade intents, while an Alpaca-powered live monitor resolves currently tradable contracts before…  
  *Notable:* Maps a historically trained DQN's intent (option type, DTE, moneyness) onto currently listed contracts, then filters by quote freshness, size and spread cost.
- **[Research backed options strategy](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/omega/research-backed-options-strategy)** — Omega · 0 votes  
  A research-backed options agent: a Python signal layer scores setups, Claude reasons over the evidence to form a thesis, and every trade is expressed as a defined-risk spread executed and managed through Alpaca in live…  
  *Notable:* A signal Claude cannot justify in plain language does not trade; each position carries the invalidation conditions its thesis was written against.
- **[Risk Gate — Honest Options AI](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/risk-gate/risk-gate-honest-options-ai)** — Risk gate · 0 votes  
  An autonomous options-trading agent built on Alpaca's MCP server. Its edge isn't a magic signal — it's hard risk gates and out-of-sample honesty. Paper-only, every trade explainable. Finished the week at +1.82%.  
  *Notable:* Out-of-sample test showed the EMA/RSI signal beat buy-and-hold on 0 of 7 names; the team reports this openly and competes on discipline.
- **[SignalForge](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/alpha-agents/signalforge)** — Alpha agents · 0 votes  
  SignalForge is an autonomous AI options paper-trading agent that scans markets, uses Azure OpenAI to evaluate opportunities, applies strict risk controls, and executes and monitors trades through Alpaca.  
  *Notable:* Risk engine independently checks AI confidence, liquidity, bid-ask spread, expiration and premium before converting a signal into a call or put.
- **[SOGNO Options Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/sogno-options-agent/sogno-options-agent)** — SOGNO Options Agent · 0 votes  
  Agente autonomo de opciones que extiende un motor de senales tecnico + sentimiento de noticias hacia Alpaca, seleccionando contratos reales y ejecutando ordenes integramente via la CLI oficial de Alpaca.  
  *Notable:* Trades only when technical and news-sentiment signals agree in direction; all account, chain and order calls go through the Alpaca CLI via subprocess.
- **[TARK AI](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/team-cosmos/tark-ai)** — Team Cosmos · 0 votes  
  TARK is an autonomous AI-powered options trading system built around the principle: Reason Before Risk. Its purpose is not simply to find bullish or bearish signals and trade them.  
  *Notable:* Scores each thesis for fragility (contradictions, failure scenario, weak volume) and outputs TRADE, REDUCE, WAIT or ABSTAIN instead of a binary decision.
- **[TEDA — SMV Options Alpha Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/gedene/teda-smv-options-alpha-agent)** — Gedene · 0 votes  
  An autonomous trading agent powered by the Smart Money Vision (SMV) strategy. It analyzes 10 assets every 5 minutes, executing debit spreads and iron condors via Alpaca paper trading with strict 1% risk management and a…  
  *Notable:* Order-flow and liquidity-sweep signals feed debit spreads sized at 1% account risk with a stated 1:7 risk-reward target.
- **[The Bullish Bots](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/the-bullish-bots/the-bullish-bots)** — The Bullish Bots · 0 votes  
  The Bullish Bots is an autonomous AI options trading agent on Alpaca's API, MCP Server & WebSocket. It scans 30+ tickers for momentum setups, executes trades and enforces risk guardrails (take-profit, stop-loss, theta…  
  *Notable:* Position Reaper enforces three unattended exits: take-profit at +50-80%, stop-loss at -40%, and a theta safety exit within 1 DTE.
- **[Three Gates](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/netizen/three-gates)** — Netizen · 0 votes  
  An autonomous options agent on Alpaca built on one rule: every layer can only remove a trade, never create one. Up 24.8% across three sessions and we published the backtest proving our signal has no predictive edge.  
  *Notable:* The LLM's response schema is a boolean veto plus one sentence, so it can only remove trades; a published backtest shows the signal underperforms random.
- **[TradeProof](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/earlgreyroom/tradeproof)** — earlgreyroom · 0 votes  
  Autonomous Alpaca options agent. Scans all 6,171 optionable U.S. equities for a volume reawakening, trades defined-risk PAPER spreads behind 23 deterministic risk gates, and proves every trade it refused on a…  
  *Notable:* Liquidity multiplies the first-pass edge score instead of adding to it, so an illiquid name can never top the ranking.
- **[Trading Master](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/convexity-compiler/trading-master)** — Trading Master · 0 votes  
  I built Trading Master to answer a question I kept running into while working with options: even if the market forecast is right, is the trade itself actually worth taking?  
  *Notable:* A counterfactual layer attributes each outcome to forecast, option structure, execution, or whether refusing the trade was the better decision.
- **[ZikosoftTrader AI](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/zikosofttrader-ai/zikosofttrader-ai)** — ZikosoftTrader AI · 0 votes  
  Risk-governed multi-agent AI trading platform for Alpaca Paper Options, combining Claude agents, deterministic risk controls, contract selection, replay, portfolio monitoring, and explainable execution.  
  *Notable:* A Risk Critic agent challenges each proposal separately from the deterministic risk engine, and Historical Replay gives deterministic demos and backtests.

## Options premium selling / income

Harvests option premium as the stated return source: cash-secured puts, covered calls, the wheel, iron condors or credit spreads sold systematically (often as a variance-risk-premium play) rather than to express a directional call.

- **[QASIX-Alpaca AI Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/cyberai-builders/qasix-alpaca-ai-trading-agent)** — QASIX · 36 votes  
  An autonomous options trading agent on Alpaca paper trading. Gemini proposes covered calls and cash-secured puts; a deterministic risk manager and exit engine decide. Every call, approved or blocked, is logged for full…  
  *Notable:* Risk manager independently re-verifies eligibility (100+ shares held for covered call, cash available for CSP) instead of trusting the LLM's claims.
- **[TrendHunter AI Risk-Aware Options Selling](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/trendhunter-ai/trendhunter-ai-risk-aware-options-selling)** — TrendHunter AI · 12 votes  
  TrendHunter AI is a risk-aware options agent that uses Gemini to analyze cash-secured puts, challenge trade ideas, and apply deterministic risk controls before Alpaca paper execution.  
  *Notable:* An explicit self-challenge stage makes Gemini search for reasons to reject its own CSP thesis before the deterministic risk gate.
- **[AutoOverlay AI: Autonomous Options Yield Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/greyarch-syndicate/autooverlay-ai-autonomous-options-yield-agent)** — GreyArch Syndicate · 8 votes  
  AutoOverlay AI is an autonomous options overlay system that turns equity portfolios into income machines. A six-persona council analyzes underlyings and selects covered calls or puts, executing through Alpaca with a…  
  *Notable:* Monte Carlo Merton jump-diffusion stress test (1,000 paths) for VaR, plus mid-price limit orders to avoid market-order premium drag.
- **[AEGIS v3.1 — Autonomous Options Trading Desk](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/apexarbitrage/aegis-v31-autonomous-options-trading-desk)** — ApexArbitrage · 6 votes  
  AEGIS is a five-agent autonomous options trading desk on Alpaca that runs the Wheel strategy end-to-end: live RSS news, multi-LLM sentiment, sovereign risk governance, full position lifecycle management, and real tail…  
  *Notable:* Portfolio Manager runs first each cycle (50% take-profit, 200% stop, ITM rolls); SPY protective puts trigger when ATM-IV stress index exceeds 25.
- **[Stable Income Generator](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/intelligence-money-printer/stable-income-generator)** — Intelligence Money Printer · 4 votes  
  Stable Income Generator is a containerized Alpaca paper-options platform: a backtested QQQ Option income strategy, deterministic risk controls, public paper evidence, and an economics-aware AI veto for regime-adaptive…  
  *Notable:* The Gemini advisory gate can only allow or veto the unchanged deterministic wheel proposal; it cannot rewrite an order or bypass risk limits.
- **[REGRET: Autonomous AI Options Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/regret/regret-autonomous-ai-options-trading-agent)** — REGRET · 3 votes  
  REGRET is an autonomous options trading agent pairing Featherless open source LLMs with six deterministic Python risk gates to execute high probability defined risk credit spreads on Alpaca Paper Trading.  
  *Notable:* Screens for IV Rank above 50% before selling credit spreads; gates require positive theta and delta within 0.40; exits at 50% profit or 2x credit.
- **[Automated SPY Weekly Iron Butterfly Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/ai-velocity/automated-spy-weekly-iron-butterfly-trading-agent)** — AI Velocity · 2 votes  
  An autonomous trading agent that executes and manages weekly SPY Iron Butterfly strategies through Alpaca, using dynamic market-driven entry timing and automated risk management with continuous wing-breach, profit/loss…  
  *Notable:* Monday entry waits until the trailing 20-minute SPY range stabilizes; a mandatory Thursday exit keeps the butterfly out of expiration.
- **[Argus](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/leish/argus)** — Leish · 1 vote  
  Argus sells defined-risk SPY put spreads for weekly income, gated by an LLM that can only veto or shrink trades, then run through a falsification engine with the whole purpose of disproving its own edge before…  
  *Notable:* Deflated Sharpe Ratio weighs results against all 31 ideas tried on the same data to test whether the edge is luck.
- **[ASMA-Agent: Autonomous Options Risk Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/asma-ai/asma-agent-autonomous-options-risk-agent)** — Asma AI · 1 vote  
  An autonomous options-trading agent on Alpaca MCP. A five-stage risk funnel decides whether to trade — a deterministic risk gate that cannot be talked out of a veto means most of the time, the correct decision is to do…  
  *Notable:* Inverts Black-Scholes from real bid/ask quotes to compute its own IV because the free data tier returns no Greeks or IV.
- **[Beleth - Autonomous Options Risk DEMON](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/team-wait/beleth-autonomous-options-risk-demon)** — Beleth Agent · 1 vote  
  Beleth is an autonomous options-trading agent on Alpaca that sells defined-risk credit spreads only when the volatility risk premium justifies it and publishes every trade it refuses, live, with the full reasoning…  
  *Notable:* Linear position-size taper driven by 1-year VIX percentile, plus a deploy guard that blocks redeploys while markets are open.
- **[Eventus Algorithm](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/hivan04/eventus-algorithm)** — hivan04 · 1 vote  
  A multi-book strategy that attempts to maximise market returns via overnight and intraday and also an LLM-driven corporate events strategy.  
  *Notable:* Capital firewall: carry book reserves Reg T requirement first, transient books lease the remainder, and a ledger maps every leg to its book.
- **[GridFly: an AI council that sells the day](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/mostlyharmless/gridfly-an-ai-council-that-sells-the-day)** — MostlyHarmless · 1 vote  
  An options-income agent on Alpaca whose AI council decides, every half hour, whether the day is still boring enough to sell. Claude proposes and journals; it never touches the risk path. Judged week: $100k to $152,415…  
  *Notable:* Gate council seats earn weight by surviving a pre-registered study; realized vol holds the deciding seat, economic calendar holds a veto.
- **[Harvester](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/fsra-finance-bros/harvester)** — FSRA Finance Bros · 1 vote  
  An autonomous AI agent that sells over-priced options premium on Alpaca paper trading. Defined-risk spreads and iron condors, sized by fractional Kelly, gated by hard risk limits the AI can't override, with an LLM…  
  *Notable:* Volatility term-structure exposure scaler throttles sizing in stressed markets, alongside fractional Kelly sizing and an automatic delta hedge.
- **[LEFA AI - Governed Autonomous Alpha Companion](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/lefa-ai/lefa-ai-governed-autonomous-alpha-companion)** — Lefa AI · 1 vote  
  A character-first autonomous options trading companion combining Featherless AI serverless reasoning with Alpaca's MCP V2 and a deterministic dual-axis risk engine to harvest options premium safely. 🇿🇦 Built in South…  
  *Notable:* Summary gives little strategy detail; the concrete mechanism is a five-agent internal chain that filters evidence before the user-facing model decides.
- **[Nondollar - Borrow like a Billionaire](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/nondollar/nondollar-borrow-like-a-billionaire)** — Nondollar · 1 vote  
  Allowing non-US users to hold US tokenised stocks backed by real equities in Alpaca brokerage and then borrow against them. Never trigger a taxable sale. What billionaires do through private banks  
  *Notable:* Lending protocol, not an agent: covered call premium on the tokenized-stock collateral pool funds zero-interest stablecoin loans at 60% LTV.
- **[Opaca — Risk-Governed Autonomous Wheel Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/opaca/opaca-risk-governed-autonomous-wheel-agent)** — Opaca · 1 vote  
  Opaca is a PAPER-only autonomous options Wheel agent where AI proposes intent, deterministic software enforces capital and execution rules, and Alpaca executes only bounded, reconciled orders.  
  *Notable:* Model proposes only intent (underlying, willingness-to-own, DTE, confidence); software owns contract, quantity, price and reservation, and marks ambiguous broker state UNKNOWN without resubmitting.
- **[OptionGnome](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/stellamaris/optiongnome)** — Stellamaris · 1 vote  
  An autonomous options trading desk on Alpaca paper trading where the AI is the least-trusted part. Code builds and checks every trade; the model only ranks a shortlist, and a deterministic Risk Officer can overrule it.…  
  *Notable:* Arithmetic-only regime classifier withholds premium-selling permission unless implied vol exceeds realized; the LLM merely picks from pre-built candidates and is parsed as hostile input.
- **[Options Alpha Agent — grades its own refusals](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/kaelux/options-alpha-agent-grades-its-own-refusals)** — Kaelux · 1 vote  
  An options-selling agent on Alpaca that predicts each trade's outcome before it enters, then re-prices every trade it refused and publishes both. Live paper account, append-only ledger, nothing hidden.  
  *Notable:* Re-prices every refused trade against live marks and grades each gate; a gate-less shadow agent shows what the unsupervised LLM would have done.
- **[ORACLE - AI Multi-Agent Trading System](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/oracle-an-ai-powered/oracle-ai-multi-agent-trading-system)** — ORACLE - an AI-powered · 1 vote  
  A multi-agent AI trading system where 5 LLM-powered agents (Bull, Bear, Risk, Quant, Judge) debate every trade in real-time before executing complex multi-leg options strategies on Alpaca. One agent. Every edge. Zero…  
  *Notable:* Momentum-fade trigger (stocks moving over 5% intraday) plus VIX regime feeds iron condor construction; trades need a judge score of 70/100 or more.
- **[Pin Desk](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/gasbin/pin-desk)** — Gasbin · 1 vote  
  An autonomous options desk that maps dealer gamma to find where hedging pins the market, then sells defined-risk premium around that pin — only while dealers damp moves. Twelve deterministic gates can veto the LLM; it…  
  *Notable:* Locates the strike where net dealer gamma flips sign and sells condors around that pin only while dealers are long gamma; otherwise stands down.
- **[The IV League](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/the-iv-league/the-iv-league)** — The IV League · 1 vote  
  The IV League is a fully autonomous options trading system: AI agents with human in the loop rank, size, execute, and review real trades every day, then fix their own mistakes before the next session starts.  
  *Notable:* Ranks names by option pricing; calm names become short puts, volatile names go to a directional agent; a separate script force-closes at day end.
- **[VULCAN — Autonomous VRP Options Desk](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/vulcan/vulcan-autonomous-vrp-options-desk)** — Vulcan · 1 vote  
  An autonomous AI options trading agent that forecasts volatility with HAR, GARCH and Kalman models, harvests the variance risk premium with Monte Carlo risk gates, multi agent AI debate and a live dashboard  
  *Notable:* Sells premium only when a HAR/GARCH/Kalman realized-vol forecast says implied vol is rich; the LLM debate can only veto or shrink trades.
- **[Wheel House](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/ifeoluwa-ogunsemoyin/wheel-house)** — Ifeoluwa Ogunsemoyin · 1 vote  
  Autonomous cash-secured put and covered-call wheel on Alpaca paper. An LLM may pick among screened option contracts; a deterministic risk gate can veto any order before it hits the account.  
  *Notable:* If both LLMs fail, the top deterministically screened contract is still proposed so the book keeps trading; the gate vetoes cheap IV versus realized.
- **[AI Options Wheel Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/signalscout-ai/ai-options-wheel-agent)** — SignalScout AI · 0 votes  
  An auditable AI Options Wheel agent where Claude proposes options trades, deterministic risk gates enforce safety, and Alpaca paper trading executes only approved limit orders.  
  *Notable:* Explicit CASH/SHARES state machine chooses cash-secured puts or covered calls; risk layer enforces covered-call cost-basis constraints and fails closed.
- **[AIrealOGs' Alpaca AI-agentic options trading](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/airealogs/airealogs-alpaca-ai-agentic-options-trading)** — AIrealOGs · 0 votes  
  A multi-agent autonomous options trading system built for Alpaca's paper trading platform. Every trade decision is made by an LLM through a structured tool-calling loop, while all risk management is enforced by…  
  *Notable:* Regime agent routes among iron condors, calendars and bull put spreads; multi-provider LLM router with fallback chains and daily token budgeting.
- **[Alfred Investments — The Options Desk](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/alfred-investments/alfred-investments-the-options-desk)** — Alfred Investments · 0 votes  
  I have built 3 AI agents: a Steward selling cash-secured puts, a Hunter: Claude reading the tape live through Alpaca's MCP server, and a deterministic Risk Officer with the final say. Every decision is logged in plain…  
  *Notable:* Hunter LLM must return a sub-280-character thesis, spending cap and falsifier or be discarded whole; a kill switch drops the desk to income-only.
- **[Alpaca AI: Every Trade Debated](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/team-sigmasix/alpaca-ai-every-trade-debated)** — Team SigmaSix · 0 votes  
  Alpaca AI is a multi-agent options trading desk that debates opportunities, applies risk controls, and autonomously executes portfolio-aware paper trades.  
  *Notable:* Quant, Volatility, Bull, Bear, Risk Officer and PM agents debate each covered-call or cash-secured-put candidate to TRADE/NO TRADE before a deterministic Risk Gate.
- **[AlphaCondor](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/voxter/alphacondor)** — Voxter · 0 votes  
  Autonomous AI options trading system combining Google Gemini reasoning with deterministic risk guardrails to execute institutional Wheel (CSP/CC) and high-efficiency 0DTE Iron Condor strategies on Alpaca.  
  *Notable:* Pairs a blue-chip Wheel with 0DTE SPY iron condors at $500 defined margin per spread to avoid $30K+ cash-secured-put collateral lockup.
- **[AlphaGate — Trading Agents](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/daodreamer/alphagate-trading-agents)** — DaoDreamer · 0 votes  
  Two Alpaca paper-trading agents, options and equities, where an LLM proposes the structure and a deterministic, model-free Risk Gate holds the veto. Every order carries a decision record, naked shorts are…  
  *Notable:* Put credit spread rule was pre-registered against a sealed two-year window the research LLM never read; 'survived refutation' and 'confirmed' are stored as separate flags.
- **[Amanah Trader — Shariah Options Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/maybesolo/amanah-trader-shariah-options-agent)** — MaybeSolo · 0 votes  
  Autonomous AI that sells cash-secured puts only when Shariah, structure and risk gates all PASS — LLM proposes, hard rules decide — live on Alpaca PA3W2J1H6I3X at amanahtrader.uk/hackathon with full audit trail.  
  *Notable:* Six fail-closed gates with no LLM override; the proposer falls back to the top-ranked candidate, and a cron job buys-to-close expiring legs.
- **[ATLAS: Autonomous Trading, Limited-risk Alpha](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/atlas/atlas-autonomous-trading-limited-risk-alpha)** — ATLAS · 0 votes  
  An autonomous options desk that sells defined-risk credit spreads on a fixed, measured universe. Two models argue every candidate the risk gates allow, and code referees. They can veto a trade. They cannot cause one.  
  *Notable:* After every terminal order state, positions are reconciled and orphan legs closed immediately; IV is solved by bisection when Alpaca returns null greeks.
- **[Autonomous AI options trading agents on Alpaca](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/kreso/autonomous-ai-options-trading-agents-on-alpaca)** — Kreso · 0 votes  
  Alpaca Options Agents: four autonomous LLM agents independently trading distinct options strategies on live paper capital, governed by a shared risk gate, automatic stop-loss/profit targets, and self-healing…  
  *Notable:* Four independent strategy agents each use a different LLM backend with strict ownership boundaries under one shared risk gate.
- **[Autonomous options desk on Alpaca](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/nuka/autonomous-options-desk-on-alpaca)** — Nuka · 0 votes  
  An autonomous put-credit-spread desk on Alpaca paper. Seven deterministic gates run before any order exists; the single model call classifies news and can only veto a candidate, never create one. Most cycles end in…  
  *Notable:* Every LLM failure mode (missing key, transport error, malformed JSON) resolves to PASS, so the agent degrades to trading nothing rather than trading unchecked.
- **[Centra](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/centra/centra)** — Centra · 0 votes  
  Building a profitable spy strategy for ai trading on alpaca  
  *Notable:* Bull put spread ~5% below spot when SPY closes above SMA(80); exits at 50% credit captured, 5 DTE, or spot below short strike.
- **[Debatte — Five Analysts, One Trade](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/copycat/debatte-five-analysts-one-trade)** — Debatte - Team · 0 votes  
  Five LLM analysts with separated data views debate market theses. Deterministic code turns the winner into defined-risk option spreads. No model places orders.  
  *Notable:* Each analyst sees a different data slice so agreement is a real signal; cited figures deviating over 1% from the briefing discard the proposal.
- **[Delphi: Conformal Risk Control Condor](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/delphi-alpha/delphi-conformal-risk-control-condor)** — Delphi Alpha · 0 votes  
  An autonomous 0DTE SPY iron-condor agent on Alpaca. It sells a band only when the market pays more for it than the band's certified expected payout, behind 31 hard gates, with LLMs voting on categories only and every…  
  *Notable:* Sells the condor only when credit/wing at expected fill exceeds a conformal-certified expected payout plus a cost margin; regime vote disagreement means abstain.
- **[EasoLab's Alpaca AI Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/easo-lab/easolabs-alpaca-ai-trading-agent)** — Easo Lab · 0 votes  
  An autonomous AI agent that trades SPY iron condors unattended on a GitHub Actions cron, using a backtested volatility signal — Sharpe 2.53, 90.9% win rate over real historical data — with every decision logged to a…  
  *Notable:* Sells condors only when IV-over-RV and non-elevated put-call skew agree; the LLM is advisory-only, and Black-Scholes math stays in deterministic code.
- **[FLINCH](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/convex/flinch)** — Convex · 0 votes  
  An autonomous options-trading agent where a deterministic engine proposes defined-risk spreads and the model can only veto or shrink them — never invent a trade, move a strike, or raise size.  
  *Notable:* Code proposes fully priced spreads (max loss, credit/width, POP); the model's only outputs are VETO, SIZE_DOWN, or APPROVE, clamped in code.
- **[Glass Box](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/mastaadmi/glass-box)** — Mastaadmi · 0 votes  
  An autonomous options trading agent that shows its work. It sells volatility premium on SPY only when that premium is measurably there, declines out loud when it is not, and writes the reasoning behind every decision.  
  *Notable:* Pre-registered hypotheses provable from git history; every decision Merkle-sealed before outcomes, which caught a parsing bug that stacked four condors.
- **[GrowBot](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/chordhorbo/growbot)** — chor_dhorbo · 0 votes  
  An autonomous AI agent that sells cash secured puts on Alpaca, using delta based contract selection, LLM sentiment analysis via Groq, and rule based risk gates, executed entirely through Alpaca's official MCP server on…  
  *Notable:* Duplicate-exposure gate checks open unfilled orders as well as positions, since unfilled limit orders never appear in position data.
- **[Hal-Street](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/hal-street/hal-street)** — HAL Street · 0 votes  
  An autonomous options trading agent on Alpaca. The model proposes; eighteen deterministic gates dispose. A Python agent writes an append-only journal; a React panel reads it and never writes anything.  
  *Notable:* All seventeen gates run on every proposal so the journal records every failing gate, not just the first; a decline counts as a decision.
- **[hellomrsys-maker Market-trading-Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/sys-trading/hellomrsys-maker-market-trading-agent)** — Sys-Market-trading-Agent · 0 votes  
  The OptionAlpha Agent is an autonomous, AI-powered algorithmic trading application that trades US stock options and cryptocurrencies completely on its own through your Alpaca brokerage account—with no human intervention…  
  *Notable:* Runs the wheel and iron condors alongside crypto spot dip-buying, with take-profit at 50% of max gain and a 2% daily loss breaker.
- **[Helmsman | hermes agents](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/helmsman/helmsman-or-hermes-agents)** — Helmsman · 0 votes  
  ⏺ Helmsman — AI options trading system on Alpaca. Three agents (BackOffice, Research, Trader) with a hard AI/execution split: LLMs propose strategies, a deterministic Bot executes them. Trades spreads and iron condors…  
  *Notable:* 1DTE condor short strikes sit just outside the market-implied expected move so width adapts to current vol; nightly reflection writes skill documents.
- **[honest-wheel: cash-secured puts with an error bar](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/honest-wheel/honest-wheel-cash-secured-puts-with-an-error-bar)** — honest-wheel · 0 votes  
  An autonomous cash-secured-put agent on Alpaca that reports its P&L next to the smallest effect seven days could have detected. It publishes the number and says plainly that the number proves nothing yet.  
  *Notable:* LLM is a veto-only gate consulted last and fails open, so an LLM outage cannot become a trading halt.
- **[House Trader — AI Options Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/house-of-voices/house-trader-ai-options-trading-agent)** — House of Voices · 0 votes  
  AI agent that sells bull put spreads on liquid stocks. Deterministic risk gates ensure capped losses, while an LLM brain selects trades from pre-approved signals. Paper-traded a $100K portfolio to a profit over 3 days…  
  *Notable:* Forced flatten before Non-Farm Payrolls; if both LLMs are down it falls back to deterministic signal sorting so trading continues.
- **[Hypercube Quant: AI Options Alpha Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/hypercube-quant/hypercube-quant-ai-options-alpha-agent)** — Hypercube Quant · 0 votes  
  Autonomous AI options trading agent executing a 100% cash-secured Wheel Strategy on Alpaca, powered by chaos theory metrics (Hurst, Permutation Entropy, IPC) and a live Scribe audit engine.  
  *Notable:* Filters underlyings by Hurst exponent above 0.65 and permutation entropy below 0.60 before selling puts; take-profit at 80% premium decay.
- **[Investonaut](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/investonaut/investonaut)** — Investonaut · 0 votes  
  Investonaut is an autonomous AI options & equities agent on Alpaca MCP — multi-agent bull/bear/neutral debate, IV-rank structure selection, hard risk guardrails, and a walk-forward out-of-sample gate that decides what…  
  *Notable:* A walk-forward out-of-sample gate decides which strategies may trade at all; IV rank routes between selling premium and buying protection.
- **[IV Desk: knows when not to trade](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/uc3m/iv-desk-knows-when-not-to-trade)** — UC3M · 0 votes  
  An autonomous options-trading agent that sells overpriced volatility on SPY, QQQ and IWM and documents every time it refuses to trade, with an LLM desk that can only shrink or veto.  
  *Notable:* Sells condors only when volatility risk premium is positive and dealer gamma favors it; every stand-down is logged with the exact failing number.
- **[IV rank Premium  Harvester](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/elvera/iv-rank-premium-harvester)** — Elvera · 0 votes  
  An automated options-selling agent built on Alpaca's Trading API + Market Data API. It screens a watchlist for elevated implied volatility , when it finds a good setup, opens defined-risk credit spreads or iron condors…  
  *Notable:* Each 30-minute GitHub Actions run checks Alpaca's live market clock first, so holidays and early closes are respected automatically.
- **[MARKGAP — the P&L an agent can actually collect](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/luna/markgap-the-pandl-an-agent-can-actually-collect)** — Luna · 0 votes  
  An autonomous options agent that optimises realised cash at a fixed timestamp — not expected return. Two books, mid and liquidation, show the gap between them live, and it drives itself flat before its horizon. Defined…  
  *Notable:* Marks the book at both mid and liquidation value, decays its risk budget to zero on a clock, and hard-flattens before the scoring horizon.
- **[Measured, Not Assumed — Tax-Aware Options Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/ivedge/measured-not-assumed-tax-aware-options-agent)** — IVEdge · 0 votes  
  An autonomous options agent that sells defined-risk credit spreads on Alpaca. Claude proposes; hard risk gates veto. Includes an IRC 1091 wash-sale guard and books that reconcile to the broker every cycle.  
  *Notable:* Measured real SPY option half-spread at $0.17 versus assumed $0.02, so it trades wide and few and refuses trades under $150 net of execution cost.
- **[NewWheel: Claude proposes, Python decides](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/chjahi/newwheel-claude-proposes-python-decides)** — chjahi · 0 votes  
  An options wheel bot on Alpaca paper trading. Claude proposes cash-secured puts as strict JSON, 24 deterministic Python checks judge each one, and only what passes reaches an MCP executor the model cannot touch. Every…  
  *Notable:* Model has no tools and never sees place_option_order; market data comes from a separate MCP process without trading tools; gates fail closed on missing data.
- **[NorthStar — an ledger AI trading agent on Alpaca](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/lovepsy/northstar-an-ledger-ai-trading-agent-on-alpaca)** — lovepsy · 0 votes  
  NorthStar turns "grow $100k to $110k in a year" into a plan with honest odds (computed, not vibes), then trades options on Alpaca behind a 22-rule deterministic risk gate. It finished the contest week down 7% - and…  
  *Notable:* Translates a stated dollar goal into required return and computes odds from walk-forward and Monte Carlo distributions before any trade is placed.
- **[OA² Governance Harness for Autonomous Trading](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/team-indexa/oa2-governance-harness-for-autonomous-trading)** — Team Indexa · 0 votes  
  An autonomous options agent whose model cannot place an order: the MCP session it reasons through exposes no order tool. Eleven risk gates, every decision logged. The strategy is ordinary on purpose.  
  *Notable:* Runs two MCP instances with different toolsets so the reasoning session lacks place_option_order; tool counts are asserted at every startup.
- **[OWL Agent — trades on rails, AI on a leash](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/stoica/owl-agent-trades-on-rails-ai-on-a-leash)** — stoica · 0 votes  
  An autonomous options-wheel agent on Alpaca paper trading: a deterministic engine sells cash-secured puts and covered calls on hard-coded rails, while a Claude layer reads the market regime and vetoes risky entries — an…  
  *Notable:* Deterministic wheel engine trades; the LLM has exactly two powers, read regime and veto a new entry, and can never block an exit.
- **[Oxotradex: Autonomous Options Alpha Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/oxotradex/oxotradex-autonomous-options-alpha-agent)** — Oxotradex · 0 votes  
  An institutional-grade autonomous trading agent that monetizes the Volatility Risk Premium via defined-risk options spreads on liquid index ETFs, combining an AI tactical reasoner with 8 inviolable deterministic Python…  
  *Notable:* Eight hardcoded gates for credit spreads: short delta ceiling 0.30, minimum net credit 0.20, bid-ask under 0.25 with OI over 50, 2.5% daily breaker.
- **[Petra- Alpha Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/the-tech-herd/petra-alpha-agent)** — The Tech Herd · 0 votes  
  Petra is an autonomous options alpha trading agent originally built as a submission for the Alpaca AI Trading Hackathon. Here is a brief overview of how it works:Core Function: It automatically sells defined-risk credit…  
  *Notable:* LLM chooses regime, direction and structure; deterministic code sets delta-targeted strike, width and size, managed with 50% take-profit and 2x-credit stop.
- **[Phoenix Alpha: Autonomous Options Trading Desk](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/trading-team-1/phoenix-alpha-autonomous-options-trading-desk)** — Trading Team #1 · 0 votes  
  Autonomous options trading desk combining qualitative LLM news triage with deterministic, defined-risk Bull Put Spreads on Alpaca. Identifies S&P 100 drawdowns, assesses moat health, and executes with a strict 2%…  
  *Notable:* Screens S&P 100 names 15% off highs, then an LLM classifies each selloff as transitory or structural before selling 20-60 DTE bull put spreads.
- **[putALPHA](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/putalpha/putalpha)** — PUTALPHA · 0 votes  
  PutAlpha sells cash-secured puts only when volatility is elevated and the market regime is not clearly bearish. It sizes risk first, scores contracts second, and uses AI only as a veto ; never as the decision-maker.  
  *Notable:* Sells puts only when HV rank is 50+ and regime is not bearish; a weighted composite score picks one contract; missing Greeks means skip.
- **[Riskgate](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/izanagi/riskgate)** — Izanagi · 0 votes  
  An autonomous options-trading agent for Alpaca paper trading: an LLM proposes Bull Put Spreads with a score and rationale, but a fully deterministic Risk Engine is the only thing that can approve an order. safe…  
  *Notable:* Live testing exposed a duplicate-exposure check that failed to update mid-scan and LLM calls wasted on candidates that should have been pre-screened.
- **[Saadhak — the calibrated options agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/saadhaka/saadhak-the-calibrated-options-agent)** — Saadhaka · 0 votes  
  An autonomous Alpaca options agent that earns its position size by proving it knows what it knows.  
  *Notable:* Position size scales with the model's measured calibration: stating 48% but being right 57% over 40 forecasts earned 0.70x full size.
- **[Schmidt Capital](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/johannschmidt/schmidt-capital)** — JohannSchmidt · 0 votes  
  An autonomous options-trading agent on Alpaca: Claude reads the market through the official MCP server and can only make the system more conservative; eight deterministic risk gates with debounced kill switches decide…  
  *Notable:* Claude's morning research can only tighten risk parameters, clamped in code; stops fire only on sustained, sanity-checked breaches so glitches never liquidate.
- **[Slippage Desk](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/pantherzz/slippage-desk)** — Pantherzz · 0 votes  
  An options income agent that measures its own execution. It scores every fill against the mid it was priced at, learns what fraction of the credit each bucket really captures, and skips the buckets where the edge dies…  
  *Notable:* Scores every fill against the priced mid, keeps a capture ratio per underlying/tenor/delta/time bucket, and skips buckets where spreads eat the credit.
- **[Spread Sentinel](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/hinderager/spread-sentinel)** — Hinderager · 0 votes  
  An autonomous SPY put-credit-spread agent on Alpaca: a 30-year-tested weekly rule, sized by Claude through the Alpaca MCP server, with every decision written to a journal.  
  *Notable:* A 1,751-week backtest rejected stops, take-profits and condors; Claude decides only enter/skip, 3% vs 4% OTM, and size.
- **[Strike Sentry](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/strike-sentry/strike-sentry)** — Strike-sentry · 0 votes  
  An AI-powered options trading agent that researches live market data and executes cash-secured put trades on Alpaca's Paper Trading API and CLI, with Groq-powered reasoning.  
  *Notable:* Filters the chain for contracts with genuine tradable quotes rather than theoretically valid strikes, and defaults to hold under uncertainty.
- **[Tape: the proof-carrying options desk](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/tape/tape-the-proof-carrying-options-desk)** — Tape · 0 votes  
  An autonomous options agent on Alpaca paper that prints a serial-numbered receipt for everything it does: thesis, 13 risk gates, raw MCP calls, fills, repairs. Then it reconciles its journal against the broker, every…  
  *Notable:* Reconciles its journal against get_all_positions every cycle after an earlier account died holding 0-DTE spreads into expiry.
- **[tasty-wheel](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/pinkbot22/tasty-wheel)** — pinkBot22 · 0 votes  
  A deterministic cash-secured-put wheel options trading agent for Alpaca featuring strict risk gates and a read-only LLM narrator for explainability.  
  *Notable:* The LLM is a read-only narrator outside the trade path, explaining why deterministic wheel rules opened, held or skipped trades.
- **[The Refuser: fail-closed options agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/forge-kotlet/the-refuser-fail-closed-options-agent)** — Forge Kotlet · 0 votes  
  Fail-closed options agent on Alpaca paper trading: sells put credit spreads only when nine deterministic gates all pass, refuses everything else, and writes every decision to a hash-chained log a judge can verify with…  
  *Notable:* Limit prices are repriced with Black-Scholes off the live IEX underlying because free-tier option quotes are 15 minutes stale.
- **[Theta Warden](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/fatdaddy/theta-warden)** — FatDaddy · 0 votes  
  An autonomous AI agent that sells defined-risk put credit spreads on SPY. A Claude brain picks a trade or skips; code-enforced risk gate, position caps, a daily loss kill-switch, no naked shorts, can veto any proposal.…  
  *Notable:* Closing orders bypass the risk gates so a halted agent can always flatten; a keyless rule-based fallback degrades outages to inaction.
- **[ThetaGate](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/notafinancedude/thetagate)** — notafinancedude · 0 votes  
  ThetaGate is an AI-assisted, paper-only options desk that uses Alpaca market data and news to find opportunities, propose defined-risk credit spreads, and manage them through deterministic risk controls.  
  *Notable:* The AI proposer sees only liquidity-, expiry-, and delta-filtered real contracts and cannot invent strikes, set size, or reach order tools.
- **[ThetaGuard - Systematic Defined-Risk Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/one-man-army/thetaguard-systematic-defined-risk-agent)** — One Man Army · 0 votes  
  ThetaGuard is an autonomous options income agent that harvests premium on SPY and QQQ through defined-risk credit spreads while proactively standing down ahead of scheduled macro events like JOLTS and NFP instead of…  
  *Notable:* Expiry selection only picks expiries maturing before the next macro blackout window, so healthy positions never need forced early closes.
- **[Underwriter](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/fifty-eleven-ai/underwriter)** — FIFTY ELEVEN AI · 0 votes  
  Underwriter is an autonomous, paper-only options agent that sells defined-risk volatility insurance on liquid ETFs and records every reason it declines a trade.  
  *Notable:* LLM role is asymmetric: it may veto elevated vol explained by a catalyst but can never add candidates, size, price, or control exits.
- **[Vega Ledger: Auditable AI Options Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/syntax/vega-ledger-auditable-ai-options-agent)** — Syntax · 0 votes  
  Autonomous options agent on Alpaca with Deflated Sharpe Ratio (DSR) rejection testing, deterministic risk gates, and an immutable decision trail anchored to Ethereum Sepolia L1.  
  *Notable:* Ran Deflated Sharpe Ratio bootstrapping on its own VRP strategy net of friction, got DSR 0%, and declined to trade it.
- **[Veritas-Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/khokhar/veritas-agent)** — Khokhar · 0 votes  
  VERITAS is an autonomous AI options trading agent that uses Alpaca to identify, validate, execute, and manage defined-risk short-DTE credit spreads. Unlike a conventional trading bot.  
  *Notable:* An Execution Confidence Score from quote quality, liquidity and data freshness rejects low-confidence candidates or trades them at reduced size.
- **[Vig - it never takes a position it can't cover](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/vig/vig-it-never-takes-a-position-it-cant-cover)** — Vig · 0 votes  
  An autonomous options agent on Alpaca that computes and reserves every position's maximum loss before the order is submitted. An order that would not be covered is never sent.  
  *Notable:* A failed position-list call returned an empty array the reconciler read as a flat book, zeroing reserves and doubling position count.
- **[vol-desk](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/i-am-iron-man/vol-desk)** — I AM IRON MAN · 0 votes  
  An autonomous options-trading agent that sells defined-risk volatility premium (credit spreads, iron condors) across seven liquid ETFs using LLM judgment for regime and strategy combined with a deterministic risk engine…  
  *Notable:* A hard drawdown halt against the account high-water mark must be cleared manually rather than resetting itself.

## LLM-discretionary agents behind a governance layer

No named signal or edge: the model reads the market and picks a trade, usually from an allowlist of defined-risk structures, and the project's pitch is the deterministic gates, refusal ledger, audit trail or fail-closed plumbing around it.

- **[SENTINEL-Risk-Aware AI Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/swayrix/sentinel-risk-aware-ai-trading-agent)** — Swayrix · 6 votes  
  SENTINEL is an autonomous AI trading agent built on Alpaca infrastructure with an independent deterministic mathematical risk engine that vetoes unsafe trades before execution to prevent capital loss.  
  *Notable:* Six non-bypassable rules including a 70% conviction floor and 40% sector cap, exposed through a six-stage decision waterfall with latency profiling.
- **[Swiftward Alpaca](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/swiftward/swiftward-alpaca)** — Swiftward Alpaca · 4 votes  
  Declarative AI Trading with Governance, Risk and Compliance  
  *Notable:* Agent runs on a private network where orders, model calls and hosts are each allowlisted; every session reads prior sessions' refusals.
- **[Determinism | Autonomous Trader](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/iitb-davxwncc/determinism-or-autonomous-trader)** — IITB DAVxWnCC · 3 votes  
  Fully autonomous agent that balances Determinism and Agentic behavior, making use of the capability of transformers of being better at comparative ranking, than scoring.  
  *Notable:* LLMs rank rather than score: five BSM-selected contracts per company are pooled and an LLM ranks the whole pool before deterministic sizing.
- **[alphadecay: AI options agent on Alpaca paper](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/alphadecay/alphadecay-ai-options-agent-on-alpaca-paper)** — AlphaDecay · 2 votes  
  An AI options agent for Alpaca paper trading. It freezes the trade thesis first, lets fixed rules approve one defined risk SPY spread, and keeps thesis, order, fill, and reconciliation in one auditable record.  
  *Notable:* Thesis, legs, schedule and risk rules are frozen before any order; the model only classifies supplied evidence and missing facts mean no action.
- **[Axiom Trade Labs](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/axiom/axiom-trade-labs)** — Axiom · 2 votes  
  Axiom Trade Labs is a hybrid autonomous trading terminal that bridges advanced AI reasoning with strict deterministic financial controls. It separates AI intent from execution authority, ensuring institutional-grade…  
  *Notable:* Deterministic filters wake the LLM only on material events; runtime policy changes trigger a 60-second uncertainty freeze that pauses new executions.
- **[Circuit Breaker](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/circuit-breaker/circuit-breaker)** — Circuit Breaker · 2 votes  
  A fully autonomous AI trading agent that monitors the market, decides, executes defined-risk options trades, and adjusts its own strategy, all with zero human intervention, built on Alpaca's MCP server.  
  *Notable:* Claude picks trades freely within three hard backstops: defined-risk spreads only, never pay more than the spread's maximum value, 15% per-trade cap.
- **[Aegis: a trading agent you can audit](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/aegis-labs/aegis-a-trading-agent-you-can-audit)** — Aegis Labs · 1 vote  
  LLM agents are good at generating plausible trades and bad at refusing bad ones. Aegis re-derives or re-observes every claim a model makes about a trade before an order can reach the broker, and refuses anything it…  
  *Notable:* A test asserts the trade is byte-identical with and without the LLM; max loss derives from OCC strikes, and unverifiable claims are refused.
- **[FlightDeck Alpha](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/wloading/flightdeck-alpha)** — WLoading · 1 vote  
  FlightDeck Alpha is an autonomous options trading agent that scans liquid symbols, selects defined-risk options strategies, executes trades through Alpaca paper trading and records a replayable trail for every decision.…  
  *Notable:* Cockpit UI replays the agent's reasoning step by step from a persistent audit log before showing which of 12 risk gates decided.
- **[Glass Box Trading](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/glass-box-trading/glass-box-trading)** — Glass Box Trading · 1 vote  
  An options trading agent that journals every candidate and veto in public; deterministic risk gates, not the LLM, decide every order.  
  *Notable:* Dead-man watchdog was inert for a day; after repair it closed the last three structures when the runner failed to price closes.
- **[Guardrail](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/varun/guardrail)** — Varun · 1 vote  
  An autonomous AI options-trading agent that physically cannot reach the broker. The LLM only proposes a direction; a deterministic rules engine approves or blocks every order and logs why. Executes on Alpaca via its…  
  *Notable:* LLM outputs only bullish, bearish or skip; strike, expiry and size are fixed deterministically, and YAML rules apply first-block-wins.
- **[KRYPTA: Prove the Trade Before You Place It](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/strong/krypta-prove-the-trade-before-you-place-it)** — STRONG · 1 vote  
  KRYPTA is an AI options agent on Alpaca that has to prove a trade before it can place one. It builds a thesis, runs a second AI to try to invalidate it, checks a deterministic risk gate, then lets a human approve real…  
  *Notable:* Three-state verdict: deterministic REJECT cannot be overridden, while the AI critic's WAIT can be, only after the user acknowledges the specific concern.
- **[Lockean Lite](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/lockean-elites/lockean-lite)** — Lockean Elites · 1 vote  
  Autonomous SPY options trading on Alpaca with independent authorization, fail-closed execution, and live paper-account P&L.  
  *Notable:* Approval issues a short-lived cryptographic receipt bound to the proposal fingerprint; a separate execution gateway must verify it before submitting the MLEG order.
- **[MU/TH/UR 8400 — Autonomous Options Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/thesis/muthur-8400-autonomous-options-trading-agent)** — MU/TH/UR 8400 · 1 vote  
  An autonomous options trading agent that states a thesis, entry rationale, and invalidation condition before every trade, enforced by hardcoded risk gates, running on 100% self-hosted infrastructure.  
  *Notable:* Agent must write a thesis, structure rationale, and invalidation condition before acting, then checks that record against price action in later cycles.
- **[OmniAlpha: Autonomous AI Quantitative Trading Desk](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/bonkers/omnialpha-autonomous-ai-quantitative-trading-desk)** — OmniAlpha · 1 vote  
  An institutional grade AI trading engine powered by DeepSeek V4 and Gemini Flash. Features a 3 chamber API revolver, active reflexion memory, 15 min loss cooldowns, and a live prompt inspector providing complete…  
  *Notable:* Post-mortem lessons from closed positions are stored in a journal and injected into future system prompts; 15-minute loss cooldowns block re-entry into falling assets.
- **[OneSpread: Evidence-Gated AI Options Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/randomstocha/onespread-evidence-gated-ai-options-agent)** — randomstocha · 1 vote  
  OneSpread pairs GLM-5 on Featherless with deterministic risk gates to evaluate SPY debit spreads on Alpaca paper trading. The AI selects a supplied candidate or waits; fresh evidence, bounded risk, and broker…  
  *Notable:* After inference the engine refreshes quotes and account state; stale data, changed context, or price deterioration blocks entry, and ambiguous acknowledgements trigger reconciliation, not retries.
- **[Opticycle — Proof Before Capital](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/opticycle/opticycle-proof-before-capital)** — Opticycle · 1 vote  
  A self-verifying SPY options agent that binds risk approval to the exact MLEG payload, executes through Alpaca MCP, and never resubmits an ambiguous order.  
  *Notable:* Short-lived certificate binds the exact MLEG payload byte-for-byte; any mutation voids authorization, and an ambiguous broker response HALTs rather than resubmitting.
- **[ORION — Autonomous Options Alpha Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/frantal-company/orion-autonomous-options-alpha-agent)** — Frantal Company · 1 vote  
  An autonomous options trading agent that must PROVE every trade — deterministic quant, an adversarial challenger, and an independent Risk Governor — executing on Alpaca paper via the Alpaca CLI. "No Trade" is a…  
  *Notable:* NO TRADE is a first-class outcome; the LLM is optional with a deterministic fallback, and the adversarial agent can only lower the Alpha Score.
- **[Probability of Profit - POP Alpha Desk](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/probability-of-profit/probability-of-profit-pop-alpha-desk)** — Probability of Profit · 1 vote  
  Unattended paper options agent: AI suggests bias, a hard governor picks defined-risk verticals, sizes to 1% equity, and scores with Monte Carlo to Friday’s mark. Fail closed.  
  *Notable:* Monte Carlo scores candidates to the contest judging date rather than expiration, gating on the chance of reaching 25% of max profit by then.
- **[QUORUM — Autonomous AI Trading Desk](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/quorum/quorum-autonomous-ai-trading-desk)** — Quorum · 1 vote  
  QUORUM is an autonomous AI trading desk where language-model reasoning is constrained by deterministic risk controls, execution rules, reconciliation, and an auditable decision ledger.  
  *Notable:* A risk veto misrouted as an exit instruction caused a $3,052 paper loss; the team reconstructed it and added 16 regression tests.
- **[SignalPilot](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/signalpilot/signalpilot)** — SignalPilot · 1 vote  
  SignalPilot is a paper-trading dashboard that separates AI recommendations from final decisions. An LLM analyzes live Alpaca data and suggests BUY/SELL/HOLD with confidence, then a deterministic risk engine applies hard…  
  *Notable:* Positioned as an environment to stress-test prompt strategies; the risk engine rejects or resizes trades regardless of the LLM's confidence score.
- **[SpeedTrader AI](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/testerxma/speedtrader-ai)** — Testerxma · 1 vote  
  An autonomous Alpaca-native trading intelligence system combining quantitative signals, adversarial AI research, options analysis, deterministic risk controls, secure execution, reconciliation, and reproducible decision…  
  *Notable:* AI acts as a subtractive critic (CONFIRM/ABSTAIN/VETO) on deterministic candidates; decision fingerprints let past decisions be replayed and reproduced.
- **[TradeGuard AI](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/tradetwin-ai/tradeguard-ai)** — TradeTwin AI · 1 vote  
  An AI-powered paper-trading agent that analyzes options trades, challenges its own decisions, manages risk, and executes the trade lifecycle using Alpaca.  
  *Notable:* The agent challenges its own proposed options strategy before execution as a self-check step against impulsive trades.
- **[Uncharted Options](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/uncharted-labs/uncharted-options)** — Uncharted Labs · 1 vote  
  Autonomous agents ask you to trust that their limits will hold. This one doesn't ask. It trades only defined-risk spreads, where maximum loss is fixed by the broker and the OCC at order construction — not by code that…  
  *Notable:* Exposure gates are measured against equity, not buying power, because a margin account reports four times equity and would quadruple every trade.
- **[UniTrader](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/unitrader/unitrader)** — UniTrader · 1 vote  
  Autonomous AI trading agent with LLM governance, circuit breakers, and explainable decision journal built on Alpaca paper trading.  
  *Notable:* Proposer-Critic pair of LLMs, with a decision journal logging both models' reasoning and a human review queue on the dashboard.
- **[Alpaca AI Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/builder/alpaca-ai-trading-agent)** — Builder · 0 votes  
  An AI-powered algorithmic trading system built with Alpaca that combines market regime analysis, strategy generation, AI self-criticism, options selection, risk management, paper execution, backtesting, and real-time…  
  *Notable:* A self-criticism layer re-evaluates the AI analyst's decision before the risk engine and execution see it.
- **[Alpaca Options Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/loq/alpaca-options-agent)** — LOQ · 0 votes  
  An autonomous options agent on Alpaca where the LLM proposes and deterministic Python decides. We measured our own model: 100% of its decision turns changed on replay at temperature 0. Then our validation gate refused…  
  *Notable:* 240 temperature-0 replays showed the model changed its decision on 100% of turns when it held authority, so only deterministic Python builds orders.
- **[Alpaca Options Trading Agents](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/miramar-labs/alpaca-options-trading-agents)** — Miramar Labs · 0 votes  
  A three-agent options desk. An Analyst sets the daily universe; a Dealer turns each signal into a specific option contract via an Alpaca MCP agent; a Floor Broker executes and risk-manages it live. Every LLM call runs…  
  *Notable:* Reconciliation overwrites every number in the LLM's contract pick with live chain values, trusting only its reasoning; a deterministic fallback picks if output is empty.
- **[Alpaca XAI Agent: Explainable AI Trader](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/bluffing/alpaca-xai-agent-explainable-ai-trader)** — Bluffing · 0 votes  
  An autonomous trading agent built for transparency. Instead of acting like a black box, it writes a clear hypothesis before trading, continuously audits its positions against real-time market data, and learns from past…  
  *Notable:* Each trade requires a JSON hypothesis with target and invalidation conditions that a worker re-audits against live data every 15 minutes.
- **[alpaca-mcp-trading-agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/agenticalpha/alpaca-mcp-trading-agent)** — AgenticAlpha · 0 votes  
  AgenticAlpha, an open-source, community-driven AI Trading Agent built for the LabLab.ai x Alpaca Hackathon. Powered by Anthropic's MCP and Alpaca's execution infrastructure to research, simulate, and place trades…  
  *Notable:* Research agent derives IV-based defined-risk spreads; a separate deterministic Execution Guardrail Agent validates total capital at risk before SDK dispatch.
- **[Alpha Judge: Prove the Trade Before You Trade It](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/umair-saleem/alpha-judge-prove-the-trade-before-you-trade-it)** — Umair Saleem · 0 votes  
  An institutional-grade AI trading agent that prioritizes capital protection. It proposes trades using LLMs but executes only if strict deterministic risk gates (liquidity, spread, DTE) "prove" the trade is safe to…  
  *Notable:* Deterministic gate blocks trades when live bid/ask spread is too wide or no contract fits the DTE window; a chatbot explains which parameter failed.
- **[AlphaMind](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/silent-tactian/alphamind)** — Silent Tactians · 0 votes  
  AlphaMind is an AI-powered trading agent that analyzes market conditions, generates explainable BUY/SELL/HOLD decisions, and applies automated risk controls before executing trades in a protected paper-trading…  
  *Notable:* Combines confidence thresholds, duplicate-order prevention, idempotent order handling and bracket orders before any BUY/SELL/HOLD decision executes.
- **[Autonomous Alpaca Options Trading Desk](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/rebels/autonomous-alpaca-options-trading-desk)** — rebels · 0 votes  
  Autonomous AI options trading agent combining LLM-based strategy selection with deterministic risk gates. Built with Alpaca API, MCP, OpenRouter, TypeScript and React, featuring live market scanning, automated execution…  
  *Notable:* LLM recommendations are converted to structured JSON and validated with Zod before deterministic risk gates; unique client order IDs prevent duplicates.
- **[Autonomous Trade Agents](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/tradeninjas/autonomous-trade-agents)** — TradeNinjas · 0 votes  
  An autonomous options-trading agent that prices its own refusals. Every trade the risk engine blocks is marked to market against real option quotes so you can see which rules earn their keep.  
  *Notable:* A Refusal Ledger marks every blocked trade to market against real quotes, showing which veto rules actually add value.
- **[BaDing: Barokah Trading](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/doa-parent/bading-barokah-trading)** — Doa Parent · 0 votes  
  BaDing is an evidence-gated 5-minute intraday AI trading agent that mechanically refuses to execute unvalidated strategies. It ensures deterministic code always overrules AI proposals, proving exactly why a trade was…  
  *Notable:* Pre-registered out-of-sample test showed negative expectancy, so the risk layer mechanically denies that strategy with a CANDIDATE_NOT_VALIDATED reason code.
- **[CAJNMNSTR](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/cajnmnstr/cajnmnstr)** — CAJNMNSTR · 0 votes  
  CAJNMNSTR is an evidence-governed SPY options PAPER agent that completed 9 autonomous Alpaca trades and finished above starting equity, with sealed Passports, deterministic risk, and broker-flat reconciliation.  
  *Notable:* LLM sees an Evidence Passport rather than broker tools and must return thesis, counterargument, uncertainty, citations and invalidation; a deterministic Referee can REDUCE or BLOCK.
- **[ConvictionOS](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/vnno1/convictionos)** — VNNo1 · 0 votes  
  ConvictionOS is a paper-only Alpaca options trading agent that turns AI market reasoning into deterministic, auditable trade decisions with risk gates, broker reconciliation, and a live dashboard.  
  *Notable:* Three mandates (catalyst, swing, thematic) each carry separate risk budgets, expiry logic and abstention rules; disagreement between AI and quant checks triggers abstain.
- **[Covenant: Proof-Carrying Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/alpacachamps/covenant-proof-carrying-trading-agent)** — AlpacaChamps · 0 votes  
  Covenant is a proof-carrying AI options agent that turns mandates into enforceable policy, checks every SPY/QQQ spread against eight risk invariants, then permits paper execution only through a signed, 60-second…  
  *Notable:* Execution requires an Ed25519-signed TradePermit bound to exact legs, price band and snapshot hashes, expiring in 60 seconds with a single-use nonce.
- **[EPSILON — AI Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/epsilon/epsilon-ai-trading-agent)** — Epsilon · 0 votes  
  A safety-first autonomous AI trading agent for Alpaca paper trading, combining LLM-driven market analysis with deterministic risk gates, real-time data validation, and fail-closed execution.  
  *Notable:* Fail-closed on any dependency outage (data, LLM, database, broker) plus worker leader election and lease-loss handling to prevent duplicate execution.
- **[Glassbox](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/lord-of-the-pings/glassbox)** — Lord Of The Pings · 0 votes  
  An options agent that knows when it's being measured. At the valuation instant our mark said $99,642 and Alpaca's said $94,207 - same account, same second. It flattens what it cannot price honestly, and every forecast…  
  *Notable:* Inside a 45-minute window before valuation it flattens any option quoting wider than 12%, because indicative marks are not cash.
- **[GlassBox Alpha: Verifiable AI Options Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/xx/glassbox-alpha-verifiable-ai-options-agent)** — XX · 0 votes  
  GlassBox Alpha is a paper-only autonomous options agent that lets AI veto a defined-risk SPY or QQQ trade, while deterministic code controls construction, risk, execution, and the audit trail.  
  *Notable:* AI critic can only return ALLOW or VETO on a fully specified trade; timeouts, invalid replies or altered candidate IDs fail closed.
- **[GlassBox: agentic options trading, fully auditable](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/team-kiloko/glassbox-agentic-options-trading-fully-auditable)** — Team Kiloko · 0 votes  
  An autonomous options agent on Alpaca whose every order passes a deterministic, fail-closed risk governor. An append-only ledger replays any decision from its own inputs; the demo's centrepiece is a trade the governor…  
  *Notable:* Governor recomputes max loss from strikes, quantity and price instead of trusting the strategist; order builder requires a covering asset argument.
- **[Huarizo AI - Autonomous Options Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/huarizo/huarizo-ai-autonomous-options-trading-agent)** — Huarizo · 0 votes  
  Autonomous options-only trading agent built on Alpaca's Trading API and MCP server. Every order must survive deterministic rules, and an authorization ledger before it reaches Alpaca, so a judge can re-derive any…  
  *Notable:* An earlier build sent 180 orders in 18 seconds because idempotency used a derived key with no persisted reservation; guards followed.
- **[Infrangible](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/workaround/infrangible)** — Workaround · 0 votes  
  An autonomous options-trading agent whose every proposal must clear a deterministic, non-bypassable risk gate before it ever reaches the broker — built on Alpaca's official MCP server.  
  *Notable:* Risk engine enforces the 5% portfolio risk rule with native multiplier differentiation: 1x for equities, 100x for options.
- **[InnerOS Alpha: Sovereign AI Trading](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/inneros-alpha-trading-agents/inneros-alpha-sovereign-ai-trading)** — InnerOS Alpha Trading Agents · 0 votes  
  A local-first AI options trading control plane on Alpaca where Qwen proposes trades, deterministic code selects contracts and enforces risk, and every PAPER decision is auditable.  
  *Notable:* MCP server is a read-only sidecar with trading tools excluded; only the deterministic execution agent reaches the Trading API, kill switch starts ON.
- **[Kairo — Autonomous AI Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/hunterxxxx/kairo-autonomous-ai-trading-agent)** — Hunterxxxx · 0 votes  
  Kairo is an AI-powered autonomous trading agent that analyzes market conditions, evaluates risk, generates trade decisions, and executes paper trades through Alpaca with a transparent, user-friendly trading dashboard.  
  *Notable:* Generic analyze-thesis-risk-execute pipeline with a dashboard exposing decisions; no specific signal, instrument or safeguard is described.
- **[Killswitch Capital](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/team-quantus/killswitch-capital)** — Team Quantus · 0 votes  
  An autonomous options trading agent where Claude proposes and fifteen deterministic gates dispose. Reads run through the Alpaca MCP server, every order through the Alpaca CLI; so the model never holds a tool that can…  
  *Notable:* Reads go through the MCP server, writes through the Alpaca CLI, so the model never holds an order tool; exits are never gated.
- **[KopTrades Automated Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/koptrades/koptrades-automated-agent)** — KopTrades · 0 votes  
  An autonomous options trading agent for SPY and QQQ. A council agent proposes trades and a critic agent reviews them, but a deterministic chain has the final say on what actually reaches the broker. Ran unattended for…  
  *Notable:* Strategies are YAML files loaded at startup, so premium-selling ones were retired mid-competition; a morning probe order gates exit from shadow mode.
- **[Life Manager: Autonomous Options Money Loop](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/life-manager/life-manager-autonomous-options-money-loop)** — Life Manager · 0 votes  
  An autonomous launchd-scheduled investment loop using Alpaca CLI paper trading, model-guided options selection, deterministic risk gates, exactly-once orders, broker reconciliation, and Telegram receipts.  
  *Notable:* Every order gets a stable client order ID persisted before execution and reconciled against broker state before any retry, preventing duplicates.
- **[Machine Earning](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/a-z/machine-earning)** — A-Z · 0 votes  
  An autonomous self-improving Codex paper-trading agent that researches stocks and options, trades through Alpaca, and learns with time by comparing real trades with simulated alternatives.  
  *Notable:* Records realistic alternative decisions before each trade, then compares them with the real outcome to convert findings into lessons.
- **[Mandate](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/earl-grey/mandate)** — Earl Grey · 0 votes  
  mandate is an autonomous options-trading agent whose strategy is a written charter and whose safety lives outside the model: human-admitted tools, dollar caps signed into a locked envelope, deterministic exits, and…  
  *Notable:* Agent never holds an API key; dollar caps are signed into a locked envelope, and unauthorized changes quarantine every trading grant.
- **[Money Machine](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/money-machine/money-machine)** — Money Machine · 0 votes  
  An auditable AI volatility governor that auctions a finite risk budget across defined-risk Alpaca paper option structures—and makes every trade or abstention explainable.  
  *Notable:* Model chooses only among pre-compiled candidate structure IDs or cash; reconciliation halts new entries whenever account exposure cannot be explained.
- **[PacaPounce](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/a-meowmeow/pacapounce)** — A-MeowMeow · 0 votes  
  PacaPounce is an autonomous trading agent that lets AI hunt for option and stock opportunities, then uses Alpaca MCP and deterministic risk gates to trade only what is worth pouncing on.  
  *Notable:* Falls back to a Nasdaq-30 stock recovery strategy when no SPY/QQQ option qualifies, and reloads existing orders after restart to prevent duplicates.
- **[Proxima Quant](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/proxima/proxima-quant)** — Proxima · 0 votes  
  An autonomous options agent on Alpaca. Each cycle the model writes a Python program, runs it in a sandbox, and returns an intent. The host prices it, sizes it, and can refuse it. A watcher acts in ten seconds on…  
  *Notable:* Model writes sandboxed programs; orders require one program to stage an intent and a later one to confirm after the host re-prices from fresh quotes.
- **[QuineAI Fiduciary Continuities](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/quineai/quineai-fiduciary-continuities)** — QuineAI · 0 votes  
  QuineAI is an autonomous options fund manager that decides for itself — no playbook, no cage. It ran a $100,000 live paper account for a week, calling the plays and the refusals itself, and kept the whole thing on the…  
  *Notable:* Injects the agent's identity and journaled history before each prompt so decisions persist across sessions; a deterministic gate outside the AI vetoes non-defined-risk trades.
- **[Reason Before Result](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/fermion-fleet/reason-before-result)** — Fermion Fleet · 0 votes  
  An Alpaca paper-options agent whose explanation must exist before its order can.  
  *Notable:* Appends a plain-language judgment with legs, max loss, break-evens and exit to the ledger before a seven-rule gate can release the order.
- **[Sentinel Gate](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/sentinel-gate/sentinel-gate)** — Sentinel Gate · 0 votes  
  An autonomous Claude-powered options trading agent that reasons live over Alpaca market data through the official MCP server — every trade it wants to make has to pass code-enforced, defined-risk gates before it can…  
  *Notable:* Claude's MCP tools are read-only; orders flow only through a propose_trade tool running deterministic gates, with a separate 60-second code loop handling exits.
- **[Sigma IA: Autonomous Portfolio Manager](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/x-systems/sigma-ia-autonomous-portfolio-manager)** — SigmeGmas · 0 votes  
  Sigma IA is a fully autonomous AI portfolio manager that leverages NVIDIA LLMs and the Model Context Protocol (MCP) to dynamically size positions, manage risk, and trade equities, crypto, and options directly via Alpaca…  
  *Notable:* Sizes every trade to exactly 5% of equity and halts volatile crypto trades during turbulent Fear & Greed readings, rotating into conservative ETFs.
- **[ten-gates](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/reubaer/ten-gates)** — Reubaer · 0 votes  
  An autonomous options agent where the LLM classifies the market regime and deterministic code decides everything else - strikes, size, execution. Ten hard risk gates the model cannot reach. Every decision published…  
  *Notable:* Structure whitelist is an enum with no naked-option member, so naked shorts cannot be expressed rather than policed after the fact.
- **[TradeProof: Verifiable Alpaca Options Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/sayul/tradeproof-verifiable-alpaca-options-agent)** — sayul · 0 votes  
  Natural-language financial policy compiler and verifiable options execution agent built on Alpaca Markets with cryptographic receipts, dynamic 6,100+ optionable asset scanning, and fail-closed risk gates.  
  *Notable:* Compiles natural-language instructions into typed, hashed policies with separate investment budget vs max-loss caps and explicit permission to abstain.
- **[Trading Alpaca: an options desk that grades itself](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/coffeandcode/trading-alpaca-an-options-desk-that-grades-itself)** — CoffeAndCode · 0 votes  
  An AI options desk where deterministic code builds every defined-risk trade and the LLM may only pick one or refuse. Two vetoes, a fail-closed risk guard, a hash-chained journal, and Brier-scored analysts that lose…  
  *Notable:* Analysts emit probabilities; closed trades resolve them and Brier scores recompute analyst weights each cycle, so miscalibrated analysts lose their vote.
- **[Trading Wool](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/frustramatic/trading-wool)** — frustramatic · 0 votes  
  An autonomous AI trading agent built with Alpaca that learns to manage leveraged positions, apply risk guard rails and hedging, and explain its trading decisions.  
  *Notable:* Used the first version's over-leveraged behavior as a feedback loop to add position-sizing guard rails and hedging mechanisms.
- **[Underwrite-options agent to earn position size](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/celabe/underwrite-options-agent-to-earn-position-size)** — celabe · 0 votes  
  An autonomous options desk on Alpaca where an LLM proposes, a second model reviews the exact legs, a deterministic gate re-prices and sizes.  
  *Notable:* Position size unlocks from 0.25% to 1% of equity only after ten resolved structures meet Brier, calibration-error and claim-accuracy thresholds.
- **[Visheshak](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/overfit-and-chill/visheshak)** — visheshak · 0 votes  
  Visheshak (विशेषक, "the discerner") — an autonomous, defined-risk options agent where an LLM provides judgment but deterministic code holds veto power over every dollar.  
  *Notable:* Every prompt rule is tested against 'what if the LLM ignores this?'; the answer must be a worse trade inside limits or no trade.
- **[volition: AI trading agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/apex101/volition-ai-trading-agent)** — APEX101 · 0 votes  
  An autonomous, audit-first options risk desk built with Alpaca, private Qwen reasoning, deterministic risk gates, and Monte Carlo stress testing.  
  *Notable:* Monte Carlo stress is one of sixteen deterministic gates, and every review yields a tamper-evident decision passport with broker lifecycle events.
- **[Voltaic Alpha](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/voltaic-alpha/voltaic-alpha)** — Voltaic Alpha · 0 votes  
  Voltaic Alpha is an autonomous AI trading system that analyzes market conditions, volatility, events, and options data to identify trading opportunities, construct risk-defined strategies, and execute them through…  
  *Notable:* Each decision keeps a structured record of evidence, hypothesis, chosen strategy, risk assessment, confidence, execution decision, and later outcome.

## Multi-agent debate / committee decisions

The headline is the decision architecture: a council, debate, jury or chain of specialized LLM agents (analyst, bull, bear, risk, supervisor) produces the trade decision, and no single instrument-level strategy dominates the pitch.

- **[TradePilot AI - Autonomous AI Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/tradepilot/tradepilot-ai-autonomous-ai-trading-agent)** — TradePilot · 128 votes  
  TradePilot AI is an autonomous AI trading platform that analyzes live markets, generates trading decisions, manages risk, and executes trades through Alpaca with automated position protection.  
  *Notable:* Position management adds breakeven protection alongside stop-loss and take-profit, with 5% per-trade and 50% portfolio exposure caps.
- **[Should-AI Buy?](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/trioblessingmiracle/should-ai-buy)** — SquadBlessingMiracle · 12 votes  
  Autonomous AI Trading Council that challenges every trade before capital is deployed.  
  *Notable:* A dedicated red-team agent asks why the trade should NOT be taken; a 0-100% human risk slider scales capital in real time.
- **[Trade Guardian](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/upskillers/trade-guardian)** — Upstarters · 7 votes  
  TradeGuardian is an autonomous multi-agent AI trading terminal that scans stocks, ETFs, and crypto 24/7. It delivers institutional setups with adversarial risk checks, dynamic position sizing, options strategies, and…  
  *Notable:* Guardian Risk Agent stress-tests each order against volatility and drawdown limits with Kelly sizing; positions get trailing stops and market-close protections.
- **[Trade Verification Firewall](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/leo/trade-verification-firewall)** — LEO · 7 votes  
  An AI trading agent for Alpaca options that requires two independent Gemini agents to agree before any trade executes — a signal generator and a verifier — with every decision logged for full auditability via Supabase…  
  *Notable:* A second independent LLM whose only job is critiquing the signal agent's reasoning; n8n orchestrates and logs every step to Supabase and Sheets.
- **[QuantNova](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/quantnova/quantnova)** — QuantNova · 3 votes  
  Explainable AI options trading for Alpaca paper accounts, combining multi-agent market analysis, quantitative signals, deterministic risk controls, and auditable paper execution.  
  *Notable:* An eight-factor technical market score classifies regime before a four-agent engine with a Devil's Advocate proposes; invalid decisions fail closed to HOLD.
- **[SecondOrder](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/secondorder/secondorder)** — SecondOrder · 3 votes  
  An autonomous multi-agent fund that invests in the supply chains behind near-predictable futures. It walked 55 suppliers deep, found most of the chain is not for sale, and journaled every decision. Most of a market's…  
  *Notable:* Walks supply-chain dependency graph two hops from headline themes; only 1 of 55 second-hop suppliers cleared the option-liquidity screen.
- **[TradeCouncil — Multi-Agent Options Alpha](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/money-tree/tradecouncil-multi-agent-options-alpha)** — Money Tree · 3 votes  
  TradeCouncil is a multi-agent options system where Bull, Bear, and CIO AI debate trades, while deterministic Python enforces strict risk gates and executes paper options orders via the Alpaca CLI.  
  *Notable:* Python pre-ranks the watchlist so only the top one or two candidates reach the Bull/Bear/CIO council, capping a cycle at six LLM calls.
- **[Nexus-Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/hackstreet-hustlers/nexus-agent)** — Hackstreet hustlers · 2 votes  
  Nexus Agent is an autonomous AI options-trading system that uses multi-agent debate, real-time market intelligence, quantitative analysis, dynamic options strategies, and integrated risk controls to make explainable…  
  *Notable:* Bull, Bear and Portfolio Manager agents debate before capital is committed; Monte Carlo VaR feeds the decision and no-trade is allowed.
- **[Options Sentinel—Options Trading via AI & MCP](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/techinnovators/options-sentinel-options-trading-via-ai-and-mcp)** — Tech_Innovators · 2 votes  
  An autonomous options trading system where AI agents debate market signals, but a deterministic risk gate — not the LLM — decides whether any trade is allowed to execute.  
  *Notable:* Deterministic Risk Gate blocks trades exceeding hard-coded size, equity and risk thresholds regardless of how confident the debating agents were.
- **[OrbiTrade](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/orbitrade/orbitrade)** — OrbiTrade · 2 votes  
  OrbiTrade is a multi-agent autonomous options trading system that resolves LLM hallucinations. It continuously improves by decoupling numerical programming from the LLM and learning from past trades.  
  *Notable:* Each agent hands the next a structured, validated artifact rather than free text; Black-Scholes, Greeks and Kelly sizing stay in deterministic code.
- **[Aegis Alpha](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/haptus/aegis-alpha)** — Haptus · 1 vote  
  Aegis Alpha is an adversarial AI Investment Committee for autonomous options trading. Instead of asking AI what to trade, it asks whether a proposed trade deserves capital.  
  *Notable:* ABSTAIN is a first-class committee outcome when evidence is insufficient or disagreement remains; decisions get tamper-evident SHA-256 certificates.
- **[Algo:  Self Improving Autonomous Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/team-algo/algo-self-improving-autonomous-trading-agent)** — Team Algo · 1 vote  
  Algo is a self-improving multi-agent trading system that detects market regimes, selects strategies, critiques its own decisions, executes safely through Alpaca, and learns from every trade to improve future decisions.  
  *Notable:* A Critic Agent independently searches for reasons a proposed trade could fail before the Risk Agent and deterministic policy controls run.
- **[Autonomous Multi Agent AI trading system](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/project/autonomous-multi-agent-ai-trading-system)** — TradeSense · 1 vote  
  A fully autonomous multi-agent AI trading system built on Alpaca. Specialized agents handle market analysis, strategy generation, and strict risk assessment before executing live trades, all visualized in a stunning…  
  *Notable:* A deterministic filter on volume, liquidity and implied volatility screens candidates before any LLM agent runs.
- **[Autonomous Unified Risk & Alpha Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/ai-champians/autonomous-unified-risk-and-alpha-agent)** — ai-champians · 1 vote  
  AI agents are increasingly given real-world power — moving money, executing trades, taking actions with no human in the loop. But autonomy without accountability is dangerous. Most autonomous systems are black boxes…  
  *Notable:* A Critic agent performs adversarial self-critique of each thesis before a deterministic risk engine independently validates confidence, risk/reward and sizing.
- **[Berkshire Alpha](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/larp/berkshire-alpha)** — Larp · 1 vote  
  An autonomous options agent whose models argue — and whose risk layer cannot be argued with. Four LLMs debate every 3–7 DTE vertical spread; a deterministic Python gate sizes and decides. Trades a language model can…  
  *Notable:* Import-graph tests fail the build if any language model is wired to order execution; quarter-Kelly sizing can only reduce, never license.
- **[Devil's Advocate](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/dreamteam/devils-advocate)** — DreamTeam · 1 vote  
  Devil's advocate is an autonomous options-trading agent that uses one AI model to propose a trade, a second to challenge it, and deterministic risk controls to decide what can actually execute through Alpaca  
  *Notable:* Adversary model's severity score was calibrated on a 30-case benchmark of 24 flawed and 6 clean proposals, tuning revise/reject thresholds.
- **[MANDATE — The Stateful Multi-Agent Trading Desk](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/goatwhistle/mandate-the-stateful-multi-agent-trading-desk)** — GoatWhistle · 1 vote  
  A continuously running multi-agent trading desk that builds a live graph of news, market events, and their relationships in the background, then combines this evolving context with market data to research, challenge…  
  *Notable:* A persistent background process builds a graph linking news, events, companies and hypotheses, so each cycle reasons over accumulated context instead of an isolated prompt.
- **[NøIdea Autonomous Options Trader](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/i-have-no-idea-what-i-am-doing/noidea-autonomous-options-trader)** — I have NO IDEA what I am DOING · 1 vote  
  “Let’s put frontier models with all the tools in a room and see what happens.” and other bad ideas.  
  *Notable:* Deterministic C# portfolio arithmetic gets a vote alongside four LLM reviewers; the app refuses to start if any write-capable MCP tool is exposed.
- **[Sam Trading AI agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/code-pioneers/sam-trading-ai-agent)** — Code Pioneers · 1 vote  
  An autonomous AI trading agent that uses a multi-agent LLM debate to produce BUY/SELL/HOLD decisions, then executes them as options trades on Alpaca's paper market. Runs on local Qwen — no cloud API keys required for…  
  *Notable:* Debate yields BUY/SELL/HOLD; an executor maps direction, DTE and strike to a contract sized at 2% of equity, reasoning on local Qwen.
- **[ThetaSwarm: Autonomous Options Alpha Desk](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/theunemployed/thetaswarm-autonomous-options-alpha-desk)** — theunemployed · 1 vote  
  An autonomous, multi-agent options trading hedge fund. ThetaSwarm separates AI reasoning from execution by letting an LLM swarm propose trades, while a deterministic Python risk engine and the Alpaca MCP server enforce…  
  *Notable:* A Shadow Book keeps an append-only ledger of every trade the AI refused, as evidence the adversarial critic and risk gates work.
- **[Trade Titans](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/trade-titans/trade-titans)** — Trade Titans · 1 vote  
  Trade Titans is a multi-agent AI trading council where Bull, Bear, Hype Investigator, and Challenger agents debate market direction, while an Options Strategist and deterministic Risk Guardian guide safe Alpaca paper…  
  *Notable:* Adds a Hype Investigator and Challenger agent alongside Bull and Bear to explicitly counter sentiment-driven bias before the Risk Guardian rules.
- **[VANGUARD OS](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/vanguard-os/vanguard-os)** — Vanguard OS · 1 vote  
  VanguardOS is an autonomous AI trading agent powered by Alpaca, combining multi-brain intelligence, real-time market data, risk controls, shadow trading, adaptive learning, and automated paper execution in one auditable…  
  *Notable:* Paper execution, shadow trading, backtesting, and synthetic testing are kept conceptually separate so performance is judged against real broker data.
- **[**Bushwood Stratton: Autonomous AI Hedge Fund**](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/bushwood-stratton/bushwood-stratton-autonomous-ai-hedge-fund)** — Bushwood Stratton · 0 votes  
  Bushwood Stratton is an autonomous hedge fund where AI portfolio managers compete for capital and survival while specialized agents manage market intelligence, risk, compliance, and trade execution. Winners survive.…  
  *Notable:* Portfolio-manager agents compete for capital and are fired for poor performance; compliance reviews orders and a single CFO agent executes.
- **[Aegis Alpha](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/cobalt-ops/aegis-alpha)** — Cobalt Ops · 0 votes  
  An autonomous, multi-agent AI options trading engine. Aegis Alpha uses an LLM debate protocol to prevent hallucinations and enforces strict quantitative risk gates to safely execute complex multi-leg trades via the…  
  *Notable:* Proposer and challenger LLMs must reach consensus, then a Black-Scholes probability-of-profit below 55% vetoes the trade regardless; MLEG orders fill atomically.
- **[AI Trading Council — Multi-Agent Trading System](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/ascend-finance/ai-trading-council-multi-agent-trading-system)** — Ascend Finance · 0 votes  
  A multi-agent AI trading system where specialized agents analyze market data, technical indicators, and risk to collaboratively generate trading decisions and execute strategies through Alpaca's trading API.  
  *Notable:* Separate technical, trend and risk agents feed an orchestration layer that merges their analyses into one decision; no instrument strategy specified.
- **[AiAgentForTrading](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/ai-trading/aiagentfortrading)** — Ai-Trading · 0 votes  
  Multi-agent quant trading engine powered by Alpaca & LangGraph. Features 5-agent parallel debate, dual-track equity & options execution, real-time market regime adaptation, deterministic RiskGuard, and 24/7 Cron…  
  *Notable:* A regime engine reweights five agents' votes live; a Cron Sentinel attaches missing OCO orders to orphan positions and closes options at DTE 2.
- **[Alpaca Trading Committee](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/quantxtreme/alpaca-trading-committee)** — QuantXtreme · 0 votes  
  Multi-agent AI trading system. 4 LLM analysts (Technical, Fundamental, Sentiment, Macro) debate into one trade proposal; a deterministic 8-rule Risk Governor approves execution via Alpaca. All trades/rejections are…  
  *Notable:* Every rejected proposal is stored and evaluated counterfactually, so the Risk Governor's refusals are audited alongside executed trades.
- **[AlphaGuard AI: Autonomous Multi-Agent Trading Desk](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/alphaguard-ai/alphaguard-ai-autonomous-multi-agent-trading-desk)** — AlphaGuard AI · 0 votes  
  Autonomous multi-agent algorithmic trading desk powered by Gemini 2.5 Flash and Alpaca Paper API, enforcing strict 1% risk management and dynamic position sizing before order execution.  
  *Notable:* A Risk Officer agent enforces a 1% account-risk-per-trade cap and dynamically sizes positions; no order proceeds without its validation.
- **[AlphaSwarm Sovereign Capital](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/intelliyash/alphaswarm-sovereign-capital)** — AlphaSwarm Sovereign · 0 votes  
  Autonomous multi-agent quantitative hedge fund SaaS with adversarial dialectic debate, multimodal chart vision, and 1,000-path Monte Carlo risk gates on Alpaca Trading API, Options API, and MCP.  
  *Notable:* Bull/bear debate synthesized by an arbiter, then a 1,000-path Monte Carlo VaR gate with 1.5x ATR trailing stops and 3.0x ATR targets.
- **[Autonomous Multi-Agent Options Trading System](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/adventurouscat/autonomous-multi-agent-options-trading-system)** — AdventurousCat · 0 votes  
  Autonomous 4-agent options trading engine on Alpaca featuring Level-3 MLEG execution, zero-polling WebSocket streaming, and a 1.5 µs deterministic risk guardrail with a 55.4% audited win rate and 1.73 profit factor.  
  *Notable:* Risk gate auto-downsizes to a 3% NAV cap and requires risk/reward >= 1.20, which structurally vetoes naked options; portfolio |delta| capped at 150.
- **[ClearSpread](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/clearspread/clearspread)** — ClearSpread · 0 votes  
  An options trading agent that never trades alone: three independent analysts argue, a critic reconciles them, and a human clicks the only button that can touch the market. Every step is a sourced, hash-chained receipt.  
  *Notable:* Three analysts each see only their own data slice; a Critic must name disagreements as risk flags instead of averaging them away.
- **[KILLJOY](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/sonsonsahur/killjoy)** — SonSonSahur · 0 votes  
  KILLJOY is an autonomous AI options trader that proposes trades, attacks its own thesis, debates the decision, and uses deterministic risk gates before executing through Alpaca.  
  *Notable:* A dedicated Kill Agent attacks each thesis; rejected trades are scored with counterfactual estimates and Kill Agent precision to tune future decisions.
- **[Lyceum — A Market of AI Minds](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/lyceum/lyceum-a-market-of-ai-minds)** — lyceum · 0 votes  
  Lyceum is an autonomous AI options research and trading system where five market minds form probabilistic beliefs, while quantitative validation, execution-cost modeling, and deterministic risk decide whether a trade…  
  *Notable:* Agents emit probability distributions, with disagreement measured by entropy and Jensen-Shannon divergence; an execution-cost hurdle defaults to NO_TRADE.
- **[Market Jury — AI Investment Council](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/maya-systems-lab/market-jury-ai-investment-council)** — Maya Systems Lab · 0 votes  
  Market Jury is a safety-first AI investment council that combines live Alpaca IEX data, Bull/Bear/Red Team debate, an independent Judge, cost preflight, and explicit capital gates before any paper-trading action.  
  *Notable:* Cost preflight freezes and hashes the request set and computes maximum spend before any paid model call; decisions expire under a TTL.
- **[Maximus AI](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/delale/maximus-ai)** — Delale · 0 votes  
  Maximus is an autonomous paper trading agent that turns market data and news into short-term stock and options decisions, applies deterministic risk controls, and executes approved orders through Alpaca.  
  *Notable:* Keeps monitoring outside market hours to prepare scenarios before the next session; a critic agent searches for contradictory evidence before the principal decides.
- **[OptionFlow Sentinel: Autonomous AI Hedge Fund](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/optionflow-sentinel/optionflow-sentinel-autonomous-ai-hedge-fund)** — OptionFlow Sentinel · 0 votes  
  OptionFlow Sentinel is a multi-tenant AI hedge fund. It utilizes a 5-agent LangGraph debate system to scan market flows, formulate multi-leg strategies, rigorously vet risk, and autonomously execute trades via Alpaca.  
  *Notable:* Background workers poll live P&L and fire closing orders on preset profit or loss targets, independent of the five-agent debate graph.
- **[OPTIONS ALPHA](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/howwow/options-alpha)** — how@wow · 0 votes  
  14 LLM agents research a position. Arithmetic decides whether it trades. Defined-risk options structures are re-priced from live bid/ask, vetoed on seven rules, and closed on a stop, target or deadline. Alpaca MCP…  
  *Notable:* Agents choose a trade's shape but never its price; a deterministic gate re-prices every leg from live bid/ask and re-runs before submission.
- **[ORACLE X](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/giantis/oracle-x)** — Giantis · 0 votes  
  ORACLE X is an AI investment committee that analyzes market opportunities, challenges its own ideas, structures defined-risk options trades, and only allows paper trades to execute after deterministic risk and safety…  
  *Notable:* A dedicated adversary agent attacks each thesis, and post-trade autopsies are stored as advisory learning that cannot bypass the deterministic risk governor.
- **[ORACLE: 24/7 Autonomous Options Trading Desk](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/oracle/oracle-247-autonomous-options-trading-desk)** — ORACLE · 0 votes  
  ORACLE is a 24/7 autonomous options intelligence system where agents reason over market regimes, generate and score multi-leg strategies with ToT Monte Carlo, challenge each trade through adversarial risk analysis…  
  *Notable:* Tree-of-Thoughts Monte Carlo scores generated multi-leg strategies across scenarios; a risk bodyguard runs a 15-second profit ratchet and 0DTE assignment defenses.
- **[Refusal Rails](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/refusal-rails/refusal-rails)** — Refusal Rails · 0 votes  
  An autonomous options agent on Alpaca built around what it refuses to trade: an AI council that must agree before capital moves, fail-closed risk gates, and a hard clock guard. Dual transport, REST for orders and MCP…  
  *Notable:* Never auto-retries order POSTs because an ambiguous response retry can double a fill; gates on Alpaca's clock, treating an unreadable clock as closed.
- **[REGRET — Counterfactual Trading Intelligence](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/newbie/regret-counterfactual-trading-intelligence)** — Newbie · 0 votes  
  An autonomous Alpaca paper-trading agent that audits both trades it executes and opportunities it rejects, turning ShadowTrades, realized outcomes, and deterministic risk controls into measurable Decision Value.  
  *Notable:* Preserves rejected candidates as ShadowTrades and later scores them counterfactually as AVOIDED_LOSS or MISSED_ALPHA, so inaction is measured alongside execution.
- **[RiskCourt: Options Alpha Jury](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/icecolds-alpacas/riskcourt-options-alpha-jury)** — icecolds alpacas · 0 votes  
  RiskCourt is a paper-only options agent where independent AI jurors form calibrated odds and a deterministic risk court trades a defined-risk spread only when jury probability clears the option-implied hurdle.  
  *Notable:* Trades only when aggregated juror probability clears the spread's option-implied break-even by a margin; recorded mode replays prompt-injection and stale-data cases.
- **[SENTINEL : Autonomous Options Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/larry-prompts/sentinel-autonomous-options-trading-agent)** — Larry prompts · 0 votes  
  SENTINEL is an autonomous AI trading system designed to find and manage options trading opportunities using Alpaca's paper trading environment. Instead of using one AI to make every decision, SENTINEL uses multiple…  
  *Notable:* Five-role agent chain (Research, Strategy, Risk Officer, Execution, Portfolio) where the Risk Officer can reject any trade before execution.
- **[Sentinel AI](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/sentinel-ai/sentinel-ai)** — Sentinel AI · 0 votes  
  Sentinel is an adversarial AI options trader that analyzes markets, builds strategies, challenges its own thesis, enforces risk controls, and executes validated paper trades through Alpaca.  
  *Notable:* An independent adversarial agent red-teams each proposed options strategy for weak assumptions before a deterministic risk engine checks hard constraints.
- **[SpinUp Capital — Autonomous AI Trading Firm](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/successcoded/spinup-capital-autonomous-ai-trading-firm)** — SuccessCoded · 0 votes  
  SpinUp Capital is an autonomous AI trading firm where specialist agents are hired, stress-tested, debated, risk-governed, and deployed to execute options strategies through Alpaca’s Trading API and paper trading…  
  *Notable:* Newly created specialist agents must pass an Agent Arena of simulated scenarios before trading; rejected proposals get trade-surgery resizing instead of bypass.
- **[STONKS](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/larp-it-till-you-make-it/stonks)** — Larp it till you make it · 0 votes  
  An autonomous multi-agent options desk where AI agents analyze sentiment, debate, pass a deterministic 12-gate risk kernel, and trade defined-risk options live on a dedicated Alpaca paper account — then learn from their…  
  *Notable:* Post-mortem lessons feed future debates and parameter proposals are restrict-only, so the desk can only become more conservative over time.
- **[TAYGOS818’S ALPACA OPTIONS BOT](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/banshee/taygos818s-alpaca-options-bot)** — banshee · 0 votes  
  I built an autonomous multi-agent options trading bot that finds market opportunities, compares independent AI analysis, applies deterministic risk controls, executes through Alpaca, and logs every decision, trade…  
  *Notable:* Discovers candidates dynamically instead of a fixed ticker list and records every decision, including abstentions, with evidence provenance.
- **[The Tribunal](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/noobmaster/the-tribunal)** — NoobMaster · 0 votes  
  TRIBUNAL is an autonomous AI trading system where every trade goes to trial. Adversarial Bull, Bear, Quant, and Black Swan agents debate opportunities before a Judge verdict and a hard coded risk gate execute Alpaca…  
  *Notable:* A Regret Engine audits closed trades to score decision quality independently of raw P&L outcomes.
- **[ThesisCircuit](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/teqprotech/thesiscircuit)** — Teqprotech · 0 votes  
  ThesisCircuit is an auditable autonomous options system where competing strategy agents, a critic, and deterministic risk controls turn live Alpaca data into bounded PAPER decisions—including a verified real fill and…  
  *Notable:* NO TRADE outcomes, shadow ideas, and counterfactuals are stored as first-class evidence without being displayed as real broker activity.
- **[TradeLix AI](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/alpacorp/tradelix-ai)** — AlpaCorp · 0 votes  
  A paper-only AI trading cockpit that turns market data, news, technical signals, and ReAct agent reasoning into gated Alpaca paper trade proposals.  
  *Notable:* Execution is disabled by default and only sends orders when explicitly armed; the gate also checks duplicate working orders and a schedule window.

## Volatility relative value & regime-routed structures

The edge is measured volatility, not direction: implied vs realized or forecast vol, skew or term structure, or a regime classifier that switches between credit and debit structures. The agent can be long or short vol, and often ranks candidate structures by probability of profit or expected value.

- **[Skew: Autonomous Volatility Desk](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/zevora/skew-autonomous-volatility-desk)** — Zevora · 6 votes  
  An autonomous options desk with no view on price direction. It trades the gap between what the market charges for movement and what movement delivers, and refuses any structure whose stress grid breaches its budget.…  
  *Notable:* Stress grid reprices each structure across 84 shock scenarios and refuses on one breached cell; position size is earned through breach-free closes.
- **[Alpaca Volatility Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/last-commit/alpaca-volatility-agent)** — Last Commit · 5 votes  
  An autonomous options volatility-harvesting & hedging agent for Alpaca. Fuses a 4-state HMM regime detector, GARCH/HAR-RV forecasting, Zou-Derman SAS, and fractional Kelly sizing with Whalley-Wilmott delta hedging via…  
  *Notable:* Four-state HMM regime throttles risk multipliers; GARCH/HAR-RV forecasts versus implied vol; Whalley-Wilmott no-trade bands limit delta-hedge friction.
- **[Vetoed - an agent most useful when it says no](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/vetoed/vetoed-an-agent-most-useful-when-it-says-no)** — Vetoed · 3 votes  
  An options agent where the AI is the least-trusted component. It measures ~1,500 credit spreads a cycle and rejects almost all of them; the model only picks from what survives, and deterministic gates size it and can…  
  *Notable:* Prices each spread twice through one lognormal model using implied versus 20-day realized vol; the difference is the edge; LLM picks only from survivors.
- **[Regime-Aware AI Options Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/nyxion/regime-aware-ai-options-agent)** — Nyxion · 2 votes  
  An institutional-grade trading agent decoupling Gemini AI reasoning from a deterministic Hard Risk Gate. It executes regime-adaptive, defined-risk options strategies using Alpaca MCP Server and API.  
  *Notable:* Indicator-based regime classifier routes structure choice (Iron Condors in high vol, Bull Call Spreads in uptrends); gate caps 5% equity and bans naked shorts.
- **[+193% winner. Pythia out-forecasts the chain](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/pythia/193percent-winner-pythia-out-forecasts-the-chain)** — Pythia · 1 vote  
  The options chain is a prediction market — Pythia out-forecasts it. Brier 72% better than the chain; +6.8% on $100k Alpaca paper in 4 sessions; +193% and +101% winners auto-exited; zero manual entries. Claude finds the…  
  *Notable:* Derives market-implied probabilities from the chain, has the LLM forecast against them, logs Brier scores before resolution, trades the gap with debit spreads.
- **[AegisAlpha: Autonomous AI Options Desk](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/returnee/aegisalpha-autonomous-ai-options-desk)** — Returnee · 1 vote  
  Autonomous multi-agent options trading desk powered by Alpaca FastMCP, Qwen-2.5-72B on Featherless AI, and 7 zero-LLM deterministic mathematical risk guardrails.  
  *Notable:* A Greeks optimizer filters the live chain to roughly 0.40-delta long and 0.20-delta short legs before seven zero-LLM risk gates run.
- **[Cache Me If You Can: AI Options Trading Agents](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/cache-me/cache-me-if-you-can-ai-options-trading-agents)** — Cache Me · 1 vote  
  Autonomous multi-agent options trading system on Alpaca combining real-time regime detection, Black-Scholes Greeks, Kelly Criterion sizing, and a 6-gate risk engine to generate consistent alpha on a $100K paper…  
  *Notable:* A VIX regime orchestrator routes capital across four specialist agents: premium selling, momentum calls, earnings straddles and portfolio hedging.
- **[CaiSheng](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/capybaraknocknock/caisheng)** — CapybaraKnocKnock · 1 vote  
  CaiSheng is an autonomous options volatility desk on Alpaca. Specialist AI agents debate event mispricing under a strict critic, while deterministic Python code enforces 20 risk gates to route delta-neutral Level-3 MLEG…  
  *Notable:* Long-vol and short-vol advocate agents debate each event setup; a model-risk critic audits quote freshness and temporal data leakage with unoverridable veto.
- **[Contour — the measurement picks the structure](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/fluffymargins/contour-the-measurement-picks-the-structure)** — FluffyMargins · 1 vote  
  Everyone sells iron condors — both wings, unconditionally, so half the time you sell the side that isn't rich. Contour measures 25-delta skew first and sells only the rich side, on SPY, QQQ and IWM, behind nineteen risk…  
  *Notable:* Skew z-score decides put spread, call spread or condor; execute.py never imports the model layer, and a missing model halves size.
- **[Deflow - Autonomous Multi-Agent Options Desk](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/deflow/deflow-autonomous-multi-agent-options-desk)** — Deflow · 1 vote  
  Four AI agents propose. Twelve deterministic breakers decide. No model touches capital. Deflow trades the gap between implied and realised volatility with defined-risk spreads on Alpaca paper, and hash-chains every fill…  
  *Notable:* Compares implied vol to a jump-robust realized-vol forecast (bipower variation); sells premium when rich, buys convexity when cheap, refuses inside the band.
- **[Devastra Trading](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/devastra/devastra-trading)** — Devastra · 1 vote  
  An autonomous agent that scans the day's biggest movers, cross-checks them against live market data from Alpaca, and decides whether a call or put is statistically justified — before ever placing a trade.  
  *Notable:* Screens top movers by realized-vs-implied vol gap, then Monte Carlo simulates expected value to decide whether to buy or sell a call or put.
- **[GlassBox AI Quant](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/monolith-one/glassbox-ai-quant)** — Monolith One · 1 vote  
  Autonomous options agent trading the gap between news-implied moves and market pricing. The LLM estimates; deterministic code decides. A 19-check risk gate controls broker access, and every trade, veto, and outcome is…  
  *Notable:* LLM returns schema-validated expected-move estimates from news, compared against the ATM straddle implied move and adjusted for moves already realized.
- **[Midpoint - the options bill nobody shows you](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/sahuexpertise/midpoint-the-options-bill-nobody-shows-you)** — sahuexpertise · 1 vote  
  Two near-identical option trades: one costs $1 to get in and out of, the other $306. Options have no legally required execution receipt, so I measured 65 real contracts on live markets and built one, plus an agent that…  
  *Notable:* Journals every refused proposal with its market snapshot and settles it at expiry, so the value of saying no becomes measurable P&L.
- **[options-allocation-agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/abc/options-allocation-agent)** — abc · 1 vote  
  Autonomous agent trading three defined-risk QQQ options strategies. An LLM allocator proposes each strategy's share of a hard risk budget; a challenger critiques it; risk gates approve or clip it before it executes live…  
  *Notable:* Headline metric is allocation delta: whether LLM weighting of bull put, bear call and strangle sleeves beats equal-weighting the same three.
- **[Options-M: Autonomus AI Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/option-m/options-m-autonomus-ai-trading-agent)** — Option-M · 1 vote  
  options-m is an autonomous options-trading agent: five cooperating AI/rule-based workers watch markets, pick strategies, execute trades, manage risk, and log every decision's full reasoning for complete auditability.  
  *Notable:* One bounded AI call assesses regime, then a deterministic rule table maps regime to an options structure; a reflection agent writes lessons back.
- **[THETA DESK — Autonomous Options Desk](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/qwertys/theta-desk-autonomous-options-desk)** — Qwertys · 1 vote  
  An autonomous options desk on Alpaca that doesn't predict prices — it prices the volatility risk premium, sizes only what it has earned, checks its exits every minute, and refuses any trade that fails a 12-gate wall…  
  *Notable:* Position size is earned: per-structure caps step up only after 0/5/15 closed trades with non-negative realized results, and drawdown takes rungs back.
- **[VolHelix AI: Multi-Agent Options Trading Swarm](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/trojanxode/volhelix-ai-multi-agent-options-trading-swarm)** — TrojanXode · 1 vote  
  VolHelix AI is an autonomous multi-agent options trading swarm powered by Alpaca FastMCP and Gemini. It fuses institutional order flow with zero-hallucination mathematical risk gates and a 24/7 Position Guardian to…  
  *Notable:* A decoupled 24/7 Position Guardian daemon manages take-profit and stop-loss exits even when the scanning autopilot is switched off.
- **[Wingman - an AI Volatility Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/hubert/wingman-an-ai-volatility-trading-agent)** — Hubert · 1 vote  
  I'm building an AI agent that will trade volatility by calculating the implied volatility from quotes on the market and executing based on any mispricing.  
  *Notable:* Fits an IV surface from live quotes every 15 minutes; cheap quotes open long straddles, rich quotes open short call verticals, otherwise wait.
- **[a continual learning agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/trueintrinsics-agent/a-continual-learning-agent)** — trueintrinsics-agent · 0 votes  
  Pure-options agent using PX5000 hourly volatility forecasts, Alpaca option chains/quotes, and a continual stock-selection learning agent memory overlay to rank near-ATM straddles by predicted-vs-implied move, catalysts…  
  *Notable:* Ranks near-ATM straddles by neural predicted move versus option-implied move, joined point-in-time with a memory of catalysts and priced-in names.
- **[AI Options Triple Strategy](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/grteam/ai-options-triple-strategy)** — GRTeam · 0 votes  
  Create a risk-defined simulator that classifies the market, selects one of three option strategies, sizes the position at no more than 1% of equity, and submits a single multi-leg limit order to Alpaca paper trading.  
  *Notable:* Market classifier selects one of three option strategies, sized at 1% of equity as a single multi-leg limit order; description gives no further detail.
- **[AlphaLoop: Autonomous Neural Options Trader](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/alphaloop-autonomous/alphaloop-autonomous-neural-options-trader)** — AlphaLoop Autonomous · 0 votes  
  AlphaLoop is a fully autonomous, multi-agent options trading system that leverages Gemini 2.5 Flash for live market analysis, dynamic risk mitigation, and algorithmic execution via the Alpaca MCP.  
  *Notable:* LLM routes structure by regime (iron condors in high IV, credit spreads on momentum); a Risk Guardian checks portfolio net delta before execution.
- **[BRIGHTLINE](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/aaf11/brightline)** — AAF11 · 0 votes  
  An autonomous options-trading agent that combines quantitative market signals with multi-model AI, deterministic rule enforcement, risk controls, broker reconciliation, and autonomous execution.  
  *Notable:* Same signal vector goes to one live model and two shadow models that never trade, enabling cross-model comparison and faithfulness checks.
- **[early, not wrong](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/earlynotwrong/early-not-wrong)** — earlynotwrong · 0 votes  
  Early, Not Wrong is an autonomous AI options trading agent on Alpaca paper. A domain-agnostic conviction harness scores cheap implied-vol premiums, runs adversarial verification, and enforces strict risk gates.  
  *Notable:* Reconstructs IV and Greeks via Black-Scholes inversion, scores contracts on an 8-factor model, and runs a cross-family LLM adversarial verifier before entry.
- **[Gamma Shepherd: Autonomous Options Agent on Alpaca](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/simplequant/gamma-shepherd-autonomous-options-agent-on-alpaca)** — SimpleQuant · 0 votes  
  Paper-only autonomous options agent on Alpaca: reads OI-gamma balance across 37 symbols at 13 intraday checkpoints, trades iron condors / reverse condors as atomic 4-leg orders, with a veto-only LLM, code-enforced risk…  
  *Notable:* Classifies regime from OI-gamma balance to choose condor versus reverse condor, then flattens via a timed close ladder ending 15:57:30 with no overnight holds.
- **[Gamma Watch](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/el-knight/gamma-watch)** — Gamma Watch · 0 votes  
  An autonomous options trading agent that reads market conditions, picks a fitting strategy, sizes the risk, gets an AI check before placing anything, and trades on Alpaca's paper account, on its own, every few minutes.  
  *Notable:* Classifies each symbol into five trend/chop states and compares option price to its recent range to route between strategies or wait.
- **[HalfSpread](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/srotdev/halfspread)** — SrotDev · 0 votes  
  Every options agent knows how to enter a trade. Almost none price what it costs to get out. HALFSPREAD measures execution cost before every order, then never pays it twice: it settles instead of closing. Alpaca paper…  
  *Notable:* Measures bid-ask crossing cost per leg before entry, ranks structures by EV after that cost, and holds to settlement rather than paying to exit.
- **[HedgeMePlease](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/hedgemeplease/hedgemeplease)** — HedgeMePlease · 0 votes  
  A fully autonomous AI options desk build on LangGraph and the official Alpaca MCP Server that grew a $100K Alpaca account for 4 days with only 1.92% of capital deployed: a 10.6% return on the deployed capital.  
  *Notable:* Sells iron condors only when four checks confirm implied vol exceeds its own forecast; agents may only reduce risk, never increase it.
- **[Institutional Options Alpha Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/blackbear001/institutional-options-alpha-agent)** — BlackBear001 · 0 votes  
  An autonomous options agent bridging a GARCH(1,1) volatility engine and atomic multi-leg execution via Featherless LLM and the Model Context Protocol (MCP).  
  *Notable:* GARCH(1,1) variance forecast routes between iron condors and straddles; the quant engine builds the exact multi-leg payload so the LLM only audits.
- **[KAIROS](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/cattos-in-ai/kairos)** — Cattos in AI · 0 votes  
  Kairos is a governed, autonomous options-trading agent that analyses market volatility, proposes hedges via AI, and lets a deterministic Risk Officer approve or veto every trade before execution through Alpaca.  
  *Notable:* After execution, trades are verified by fill-price slippage and Greeks reconciliation; the Risk Officer also checks portfolio vega and margin utilization.
- **[Kink — an autonomous options trading agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/kink/kink-an-autonomous-options-trading-agent)** — KINK · 0 votes  
  A trading program that grades its own guesses. It checked 9,500 of them, including every trade it turned down — and when the results disagreed with its own idea, it said so instead of quietly changing the rules.  
  *Notable:* Scores every refused trade (9,500 guesses) and subtracts peer-symbol moves before judging one symbol's term-structure signal.
- **[Magno](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/crackd/magno)** — Crackd · 0 votes  
  Magno is an autonomous options desk that captures volatility mispricings while hardwiring downside risk limits. It enforces 9 deterministic Python risk gates and runs a 24/7 continuous dynamic delta-hedging loop to hold…  
  *Notable:* A 5-second loop dispatches fractional underlying equity orders to hold portfolio delta at zero; Greeks are computed locally via Newton-Raphson.
- **[Option Alpha Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/the-overfitters/option-alpha-agent)** — The Overfitters · 0 votes  
  An autonomous options trading agent on Alpaca. It reads volatility and trend, deploys defined-risk spreads and iron condors, then grades every candidate against nine explicit checks - recording why it traded, watched or…  
  *Notable:* Two-factor regime model (IV rich or cheap crossed with trending or range-bound) selects the defined-risk structure; logs traded, watched or declined.
- **[OptionForge - Alpaca Options Alpha Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/optionforge/optionforge-alpaca-options-alpha-trading-agent)** — OptionForge · 0 votes  
  Autonomous multi-strategy options trading agent pairing explainable LLM reasoning (Featherless & Gemini) with deterministic Python hard risk gates, 52-week IV Rank regime adaptation, and a hybrid Alpaca MCP + SDK…  
  *Notable:* Routes by 52-week IV rank and ADX: credit structures above IVR 50, debit spreads in strong trends, and halts entirely in low-vol chop.
- **[Options Alpha Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/pulgateam/options-alpha-agent)** — pulga_team · 0 votes  
  An autonomous options-trading agent that asks whether the market is paying enough for a specific risk, prices with implied vol, scores with realised vol, and refuses to trade when the edge isn't real.  
  *Notable:* Prices structures with implied vol but scores probability with realized vol, trading only when EV clears 2% of risk; the LLM shifts probability only.
- **[Options Alpha Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/malaew/options-alpha-agent)** — malaew · 0 votes  
  An options agent trading implied-vs-realized volatility. Defined-risk spreads only, every refusal logged with its reason, and every broker call made through Alpaca's official CLI.  
  *Notable:* Reads the realized-vol window twice, once with its largest day removed, so an earnings gap cannot make options look falsely cheap.
- **[OptionsVisor](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/lugia/optionsvisor)** — Lugia · 0 votes  
  Agentic trading that scans hundreds of stocks for volatility mispricing and trades credit spreads and iron condors via Deepseek.  
  *Notable:* Two-stage vectorized screener flags implied-vs-realized vol richness, then a signal layer routes each name to an iron condor or directional credit spread.
- **[Parallax - Dispersion Barbell](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/viyon/parallax-dispersion-barbell)** — Viyon · 0 votes  
  Autonomous Alpaca options agent running a Dispersion Barbell: short rich single-name volatility via defined-risk credit spreads, hedged by small long index convexity. Fully autonomous screen→AI…  
  *Notable:* Risk engine can only shrink or reject a proposal, verified by a property test; a dated endgame state machine forces the account flat before deadline.
- **[RAMON — an options agent that refuses out loud](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/ramon/ramon-an-options-agent-that-refuses-out-loud)** — Ramon · 0 votes  
  An options agent that trades one thing — the gap between calendar-time pricing and trading-time variance — and refuses everything else out loud, with every refusal timestamped and every dead idea logged.  
  *Notable:* Sells delta-hedged straddles only when IV² × calendar days exceeds RV² × trading days; refused pre-holiday weekend; RECONCILE stage flattened orphaned leg in 77 seconds.
- **[Realized-vs-Implied Options Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/tradegoats/realized-vs-implied-options-trading-agent)** — Tradegoats · 0 votes  
  An autonomous options agent that trades vertical spreads on 11 liquid US names via Alpaca's MCP server. It compares implied vs. realized volatility to size positions, then screens every trade through a hard risk gate…  
  *Notable:* Scores each spread by how many multiples of round-trip slippage the IV-RV edge covers; a portfolio dollar-delta cap blocks correlated directional stacking.
- **[Theta Council](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/theta-council/theta-council)** — Theta Council · 0 votes  
  An autonomous options desk on Alpaca that sells the variance risk premium in defined-risk spreads — where the LLM holds a veto and a size dial, and a deterministic Risk Officer holds the wheel.  
  *Notable:* Each vertical is priced twice, at implied and at realized vol; the difference after a bid/ask haircut ranks candidates by EV/max_loss.
- **[Three decision architecture experiment](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/rookie-riot/three-decision-architecture-experiment)** — Rookie Riot · 0 votes  
  An autonomous agent trading defined-risk options spreads on Alpaca, gated by risk code the LLM can't override — built alongside two more agents on that same code, opposite decision architectures, compared live on a…  
  *Notable:* Three agents with opposite decision architectures run on the same imported risk code and are compared live on a public dashboard.
- **[Vanguard_Sentinel_options_trading_agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/team-vanguard/vanguardsentineloptionstradingagent)** — Team Vanguard · 0 votes  
  Vanguard Sentinel: an autonomous options agent trading ETFs on Alpaca paper trading.  
  *Notable:* Regime classifier routes between selling iron condors, buying strangles ahead of catalysts, or standing aside; dual LLM provider with local fallback.
- **[Vega — autonomous long-gamma options agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/isquividet/vega-autonomous-long-gamma-options-agent)** — isquividet · 0 votes  
  An autonomous agent that buys SPY convexity through Alpaca's MCP server, refuses quotes it cannot trade, and cannot lose more than the premium it pays. 48 of 48 claims it publishes reproduce from one credential-free…  
  *Notable:* Deliberately omits mark-to-market stops on long premium, quantifying that a stop fires on 91% of paths and cuts modelled top-3 odds.
- **[VolGuard AI](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/brikita/volguard-ai)** — brikita · 0 votes  
  VolGuard scans live Alpaca options, abstains when evidence is weak, and governs atomic paper trades through fourteen risk gates and automated lifecycle monitoring.  
  *Notable:* Decision Memory requires repeated agreement across recent open-market scans, so a first sighting or conflicting analysis cannot trigger an entry.
- **[VOLTA — Volatility Surface Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/kriz/volta-volatility-surface-trading-agent)** — KriZ · 0 votes  
  VOLTA is an options trading agent that detects mispricing across the volatility surface. It scans strikes and expirations, builds defined-risk spreads, and executes via Alpaca MCP with an LLM pipeline, deterministic…  
  *Notable:* Three surface anomaly detectors (skew, term structure, local z-score) feed a six-dimension deterministic score before the LLM makes a go/no-go call.
- **[VOLTRON - Volatility Alpha](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/karmajs/voltron-volatility-alpha)** — Karmajs · 0 votes  
  An autonomous AI options trading agent that combines IV/RV volatility alpha, Gemini reasoning, deterministic risk controls and Alpaca paper execution.  
  *Notable:* IV/RV ratio produces an opportunity score; risk engine also tracks consecutive losses and options buying power, failing closed to NO TRADE.
- **[VRP Engine: Autonomous Options Agent on Alpaca](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/participant/vrp-engine-autonomous-options-agent-on-alpaca)** — Participant · 0 votes  
  Autonomous paper-trading agent that harvests the variance risk premium with defined-risk option spreads, risk gates, and Alpaca API + MCP + CLI.  
  *Notable:* Opens only when a positive probability wedge shows the specific structure mispriced, not merely rich IV; CLI verifies the book before and after every order.
- **[Worca - An Agentic Swarm to automate Trading](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/yvl/worca-an-agentic-swarm-to-automate-trading)** — yvl · 0 votes  
  Two option-trading agents each watch one thing: gamma exposure walls, or IV term-structure dislocations. A Featherless LLM reads both and allocates capital between them. Risk limits are deterministic Python, so the LLM…  
  *Notable:* Two specialists (gamma walls, IV term structure) publish to a shared bus; the LLM only allocates capital between them, never touching risk limits.

## News, sentiment & scheduled-event trading

Entries are triggered by news flow, social sentiment, filings, insider or congressional disclosures, or a scheduled catalyst such as earnings (IV-crush condors, pre-report straddles) rather than by price signals.

- **[PRISM](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/iskolar/prism)** — ISKOLAR · 5 votes  
  PRISM combines multi-agent AI with deterministic risk controls to analyze markets, govern trades, explain decisions, and test alternatives through ShadowFund.  
  *Notable:* ShadowFund counterfactuals compare each decision against cash, smaller size, contrarian and unconstrained-AI alternatives to measure whether decisions were better.
- **[AegisAlpha — Autonomous Event-Driven Options Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/zenith/aegisalpha-autonomous-event-driven-options-agent)** — Zenith · 3 votes  
  AegisAlpha is an autonomous, event-driven options trading agent that discovers market catalysts, uses Bull/Bear AI reasoning, and applies deterministic risk controls before executing trades through Alpaca.  
  *Notable:* An AI screener discovers catalysts instead of a fixed watchlist; the Decision Journal records rejected opportunities with the exact reason.
- **[AI Options Agent aka ThetaTrap](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/neural-point-analytica/ai-options-agent-aka-thetatrap)** — Neural Point Analytica · 1 vote  
  ThetaTrap uses Qwen and Alpaca’s official MCP server to evaluate earnings risk and execute defined-risk paper options trades inside deterministic safety limits.  
  *Notable:* Earnings iron condors on a frozen event universe, one broker entry attempt per strategy date, max loss capped at lower of $500 or 0.5% equity.
- **[Cascade](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/cascade/cascade)** — Cascade · 1 vote  
  Cascade trades the ripple, not the splash. An autonomous agent that maps supplier–customer relationships from SEC filings, then trades the companies a shock hasn't reached yet — every hop citing a real filing.  
  *Notable:* Builds a supplier-customer graph offline from XBRL customer-concentration disclosures; 'not moved yet' is a beta-stripped, vol-normalised residual z-score.
- **[Catalyst Surface Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/no-hallucinations/catalyst-surface-agent)** — No Hallucinations · 1 vote  
  An autonomous event-driven options agent that discovers scheduled catalysts, validates them with a bounded Featherless committee, executes through Alpaca MCP, and publishes a tamper-evident decision trail.  
  *Notable:* Replays each candidate's historical options and promotes only setups that survive a frozen policy; the model committee may veto but not invent trades.
- **[Congressional Insider Trading Desk](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/team-shaw/congressional-insider-trading-desk)** — Team SHAW · 1 vote  
  Building a fully agentic Congressional Insider trading desk that leverages Claude Code and Alpaca's MCP server to autonomously process public financial disclosures and execute matching options strategies.  
  *Notable:* Uses Claude to visually read scanned paper filings lacking a text layer, then judges whether a month-stale disclosure signal is still live.
- **[Crowd Excess](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/ichika/crowd-excess)** — Ichika · 1 vote  
  An auditable AI agent that detects when attention and price outrun objective news, then expresses a controlled contrarian view with defined-risk Alpaca paper option spreads.  
  *Notable:* Uses cross-border NAVER search attention as a crowd signal and takes contrarian option spreads when attention outruns objective news evidence.
- **[Esscher](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/nx1/esscher)** — QuantNotts · 1 vote  
  Esscher is a paper-trading AI agent that measures the move after the market’s first reaction to earnings. It can stay in cash or choose shares, a long option, or a debit spread—with hard risk limits and traceable…  
  *Notable:* Freezes evidence at a decision cutoff after the first earnings reaction, then compares cash, shares, long option and debit spread as one view.
- **[Hermes Trader — Autonomous AI Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/team-lunarnodal/hermes-trader-autonomous-ai-trading-agent)** — Team LunarNodal · 1 vote  
  Autonomous AI trading pipeline that ingests news every 5 minutes, maps cross-sector market dependencies, and enforces 6 protection layers before any trade executes. Hermes provides natural language access to the system…  
  *Notable:* Failed trades trigger an automated post-mortem that writes a new cross-sector inference rule fed into every future prediction.
- **[PrintRunner, Closed-Loop Earnings Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/beyond-vibe/printrunner-closed-loop-earnings-agent)** — beyond-vibe · 1 vote  
  Earnings-season options agent on Alpaca paper. LLM least-trusted: deterministic verticals/condors, 10 hard gates, mleg execution, hash-chained journal, breaker at 2x costs, and a hypothesis graph that compounds from…  
  *Notable:* A persistent hypothesis graph stores every rejected hypothesis with its regime; the next query retrieves the three most similar past failures first.
- **[Sentinel: The Gates Decide](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/ai-trading-jrwater101/sentinel-the-gates-decide)** — AI Trading JrWater101 · 1 vote  
  Evidence-driven, event-only options agent: the LLM proposes LULU/NFP trades; deterministic gates decide. Alpaca paper execution is limit-only, defined-risk, and audit-visible on a credential-free dashboard.  
  *Notable:* Trend engines were disabled after cross-validation showed weak evidence; a durable permit binds each decision to a policy hash and git revision.
- **[AlgoSentinel](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/algosentinel/algosentinel)** — AlgoSentinel · 0 votes  
  AlgoSentinel is an autonomous AI trading agent that reads live market news, scores sentiment with Google Gemini, and executes SPY options trades on Alpaca — fully automated, no human intervention needed.  
  *Notable:* Gemini scores Google News RSS headlines every 15 minutes into a BULLISH/BEARISH signal that must clear 60% confidence before buying ATM SPY options.
- **[Alpaca Reflex](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/mmac-team/alpaca-reflex)** — MMAC Team · 0 votes  
  Alpaca Reflex is a cross-asset event-to-options operating system. Every Alpaca order carries proof of why it exists. AI proposes; deterministic code authorizes.  
  *Notable:* Selector computes a contract budget first and searches farther OTM for a liquid, affordable contract instead of proposing an ATM name the gate would reject.
- **[BioTrader AI Autonomous Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/mp-vision/biotrader-ai-autonomous-trading-agent)** — Mp vision · 0 votes  
  BioTrader AI is an autonomous quantitative trading agent that parses PubMed abstracts, FDA clinical trials, and protein binding metrics using MCP tools to execute real-time biotech stock trades via the Alpaca Trading…  
  *Notable:* Parses clinical trial p-values, binding affinity and toxicity rates as alt-data; buys on p<0.01 significance, sells on FDA holds.
- **[CLEANROOM: A Trading Agent That Can't Be Hijacked](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/cleanroom/cleanroom-a-trading-agent-that-cant-be-hijacked)** — CLEANROOM · 0 votes  
  CLEANROOM is an autonomous Alpaca trading agent whose news-reading LLM has zero tools — it can lie, but it cannot place an order. Isolation is structural, not detected: 0/15 injected attacks land hardened, 5/15 land…  
  *Notable:* News-reading LLM has zero tools and outputs only a Pydantic struct; a reproducible injection corpus shows 0/15 attacks land hardened versus 5/15 unhardened.
- **[Dailies, dailies, watch it work](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/dailies/dailies-dailies-watch-it-work)** — Dailies · 0 votes  
  An autonomous options agent that reads Alpaca's news wire, forms a macro thesis on each market sector, and trades it as a defined-risk credit spread. Every order goes through the Alpaca CLI. Every risk limit sits…  
  *Notable:* Loss caps measure against starting capital rather than live equity; each sector's past closes and error rate are replayed into its next prompt.
- **[Horizon Blackline](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/horizon-blackline/horizon-blackline)** — Horizon Blackline · 0 votes  
  A governed autonomous options-trading agent on Alpaca: the LLM proposes, deterministic risk gates authorize, every decision is hash-chained and auditable.  
  *Notable:* Dispatcher claims execution via compare-and-swap so concurrent attempts never both reach the broker; stop-breach closes bypass the liquidity gate.
- **[LSJ Management - Corporate Actions, Kalshi, +1](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/lsj-management/lsj-management-corporate-actions-kalshi-1)** — LSJ Management · 0 votes  
  Four autonomous trading sleeves turned $100k into $1.85M on Alpaca paper. Corporate actions, cross-market volatility, options spreads and systematic research, with an LLM veto layer and deterministic risk controls.  
  *Notable:* LLM is veto-only after deterministic gates: 47 of 157 decisions rejected pre-model, 18 reached the LLM, 2 vetoed for arithmetic errors.
- **[NewsFlow Trader](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/cubiczan/newsflow-trader)** — cubiczan · 0 votes  
  NewsFlow Trader is an autonomous LLM-driven news trading agent on Alpaca's paper Trading API. Reads financial headlines, scores them, applies a configurable risk guard, and submits approved orders — all observable in a…  
  *Notable:* Risk guard blocked SELLs on positions not held and BUYs over a position cap; ships a machine-readable proof artifact of every filled order.
- **[Newsstrike AI](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/solodev/newsstrike-ai)** — solodev · 0 votes  
  An autonomous desk that reads the market's news feed the way a discretionary options trader would, then expresses each real signal as a capped-risk directional spread instead of a naked bet  
  *Notable:* Streams Alpaca's real-time news websocket, classifies headline sentiment and materiality, and expresses signals as bull-call or bear-put debit spreads.
- **[Sentinel Options](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/nexus-ai/sentinel-options)** — Nexus AI · 0 votes  
  An autonomous AI options trading agent combining Gemini market analysis, deterministic risk controls, and Alpaca CLI execution to select, execute, and monitor options trades without human intervention.  
  *Notable:* Gemini turns Google News RSS headlines into structured CALL/PUT signals with confidence; approved orders execute via subprocess calls to the Alpaca CLI.
- **[Sentinel: Autonomous AI Options Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/miners/sentinel-autonomous-ai-options-trading-agent)** — Miners · 0 votes  
  Sentinel is an experimental autonomous pipeline that ingests real-time financial news, uses Groq (Llama 3.3) to generate structured Options signals, routes them through a strict risk-management gate, and executes on the…  
  *Notable:* Risk gate kills orders when LLM confidence is too low; an interactive Alpaca CLI terminal is embedded in the React dashboard.
- **[SlashSlash — Autonomous Earnings IV Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/slash/slashslash-autonomous-earnings-iv-agent)** — Slash · 0 votes  
  An autonomous agent that sells iron condors into earnings-driven implied volatility, then closes them after the crush. Built on Alpaca's Trading API, Market Data API, and official CLI, with an LLM event-risk filter and…  
  *Notable:* Switched from delta-targeted to percent-OTM strike selection after finding Alpaca's free options feed returns no Greeks or IV.
- **[Snowmelt - Autonomous AI Options Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/alphafa/snowmelt-autonomous-ai-options-trading-agent)** — Alphafa · 0 votes  
  Autonomous AI agent that scans the week’s earnings calendar, narrows to high-vol liquid names, buys tiered OTM options via Alpaca, and exits by T+1 close before IV crush.  
  *Notable:* Splits earnings-option risk across three OTM tiers (40/30/30) and hard-exits by T+1 close to avoid IV crush and expiry theta.
- **[TariffEdge](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/tariff/tariffedge)** — TARIFF · 0 votes  
  TariffEdge is an autonomous options trading agent that converts real-time tariff and trade-policy news (via GDELT) into risk-gated equity option spreads on Alpaca with a hard $500 max-loss cap, full audit trail, and a…  
  *Notable:* Maps GDELT tariff and export-control news to sector tickers (steel to NUE, semis to SMH) and trades debit spreads under a $500 max-loss cap.
- **[VolHarvest: Autonomous LLM Options Trader](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/volharvest-ai/volharvest-autonomous-llm-options-trader)** — VolHarvest AI · 0 votes  
  VolHarvest is an autonomous AI trading agent that uses NVIDIA's 550B Nemotron LLM to analyze live macroeconomic news and mathematically execute delta-neutral Options Straddles via the Alpaca CLI to profit off pure…  
  *Notable:* LLM predicts reaction magnitude (EXTREME vs SIDEWAYS) from headlines rather than direction, then buys the cheapest same-strike straddle.

## Equity & crypto spot trading on signals

Trades stocks, ETFs or crypto spot (not options) on momentum, trend, mean-reversion, z-score or fundamental quality scores; the LLM, if any, confirms or explains rather than originates.

- **[Elite-Bot: Multi-Asset AI Agent Trading Hub](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/teambhairava/elite-bot-multi-asset-ai-agent-trading-hub)** — Team_Bhairava · 3 votes  
  Elite-Bot is an autonomous multi-asset trading hub bridging quant finance and generative AI. It leverages mathematical models to find setups across Crypto and Stocks, and uses CrewAI agents powered by Groq to validate…  
  *Notable:* Execution pauses when a z-score setup fires and a CrewAI desk debates it; a daemon uses agents to manage trailing stops.
- **[Apex Cypher](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/apex-cypher/apex-cypher)** — APEX CYPHER · 1 vote  
  Fully automated trading bot using IFVG (Inefficiency Fair Value Gap) strategy on Alpaca paper trading. Detects market inefficiencies, enters positions with strict risk management, and tracks live PnL in real-time.  
  *Notable:* Fair-value-gap entries only above VWAP, stop at VWAP plus or minus one ATR, and trading halts after three losses in a day.
- **[Catalyst Router](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/itsmeyaw/catalyst-router)** — itsmeYAW · 1 vote  
  Catalyst Router is an autonomous, risk-bounded AI trading agent for Alpaca paper trading. It uses point-in-time Alpaca market data, an XGBoost directional model, and deterministic risk controls to place protected long…  
  *Notable:* News extraction runs in shadow mode only, while a checksummed XGBoost model supplies direction and idempotent bracket orders carry broker-hosted exits.
- **[EdgeStack: Evidence-Gated Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/edgestack-ai/edgestack-evidence-gated-trading-agent)** — EdgeStack AI · 1 vote  
  An autonomous Alpaca trading agent built on one idea — evidence opens the door to opportunity: 33 years of data, and a public graveyard of rejected ideas behind an equity-plus-options strategy that journals every trade…  
  *Notable:* Publishes a graveyard of rejected ideas with the statistic that killed each; trades SPY overnight-only gated by 12-month trend and credit canary.
- **[Explainable AI Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/trade-minds/explainable-ai-trading-agent)** — Trade Minds · 1 vote  
  An AI trading agent that combines moving average signals with Gemini-powered explanations, so every trade decision on Alpaca's paper trading platform comes with a clear, beginner-friendly reason.  
  *Notable:* Gemini writes a beginner-level explanation after a deterministic 5/20-day MA crossover fires; the LLM explains rather than decides.
- **[Finly: AI Trading That Shows Its Work](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/hackingnoises/finly-ai-trading-that-shows-its-work)** — hackingnoises · 1 vote  
  In a 2013–2026 cost-modeled historical simulation, Finly turned $10K into $106,711—$38,629 more than SPY. AI explains the market; tested code controls the money.  
  *Notable:* Options sleeve logged 24 cycles ending in no trade, with refusals categorized as failed certification, insufficient evidence or late entry window.
- **[OFFLeash: Guardrails for AI Trading Agents](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/khata-lemo/offleash-guardrails-for-ai-trading-agents)** — Khata Lemo · 1 vote  
  An autonomous AI trading agent that polices its own behavioral biases. OFFLeash uses deterministic guardrails to detect oversized positions, overexposure, revenge trading, and overtrading—blocking risky trades and…  
  *Notable:* Four behavioral guardrails (oversized, overexposure, revenge trading, overtrading) block trades, and blocked trades are tracked counterfactually to price the value of restraint.
- **[quantify](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/quantify/quantify)** — quantify · 1 vote  
  AI-powered trading strategy combining Hull Moving Average, AI consensus, multi-timeframe analysis, risk management, and backtesting for smarter, systematic market decisions.  
  *Notable:* Hull Moving Average direction generates entries and exits, validated by AI consensus and multi-timeframe analysis before backtesting and deployment.
- **[AFTERIMAGE — GuavaMango](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/the-strawhats/afterimage-guavamango)** — The StrawHats · 0 votes  
  An autonomous Alpaca agent where market memory finds the trade, a four-model jury attacks it, and only a cost-aware 3R, cryptographically signed intent can reach the broker.  
  *Notable:* A shadow clock carries skipped setups forward as market memory so live behavior matches backtests; a single-use Ed25519 warrant binds each order intent.
- **[Alpacaruns](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/uganda-cranes/alpacaruns)** — Uganda cranes · 0 votes  
  Alpacaruns is a safety-first AI trading system combining multi-agent reasoning with adaptive trading experts, deterministic risk gates, and Alpaca paper execution across equities, crypto, and options.  
  *Notable:* Nine specialist signals are aggregated by performance-weighted voting with volatility-regime awareness; the options overlay falls back to equities when data is unavailable.
- **[BARCO-Alpaca AI Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/guacalita/barco-alpaca-ai-trading-agent)** — GUACALITA · 0 votes  
  Autonomous AI agent that trades stocks and crypto using Claude + Alpaca API. Claude analyzes quantum signals, CNN order book data, and NLP sentiment every 15 min via MCP tools, then executes real trades with automatic…  
  *Notable:* Three signal sources are aggregated into one Meta-Brain score; Claude trades only above +0.3 while a separate 30-second Python monitor enforces TP/SL.
- **[LIQWID - Autonomous Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/ghostvariables/liqwid-autonomous-trading-agent)** — ghostvariables · 0 votes  
  An agentic trading system that analyzes market data, detects signals, scores conviction, applies risk controls, and executes paper trades autonomously through an MCP-powered pipeline.  
  *Notable:* Same MCP tool layer serves both a CLI and an LLM agent; signal and instrument are unspecified, and backtest claims are explicitly withheld.
- **[Momentum Gogogo!](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/flexmasterfeng/momentum-gogogo)** — Flexmasterfeng · 0 votes  
  Five autonomous agents trade momentum stocks and sell defined-risk put spreads against them on Alpaca paper trading — with a risk agent that can veto any order and capital math that makes double-spending structurally…  
  *Notable:* Risk agent's capital math makes committing the same dollar twice structurally impossible; writeup separates universe-selection return from real edge.
- **[Portfolio Risk Guardian](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/portfolio-risk-guardian/portfolio-risk-guardian)** — Portfolio Risk Guardian · 0 votes  
  A multi-agent AI trading system built on Alpaca paper trading. Its real product isn't 4 agents — it's a rigorous, honest validation pipeline that found its own signal doesn't generalize, and explains exactly why.  
  *Notable:* Walk-forward and out-of-universe tests exposed that the tuned RSI/SMA/ADX signal did not generalize; diversifying across 16 tickers raised Sharpe.
- **[ProductAdvisors: Agent that cuts what it measures](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/product-advisors/productadvisors-agent-that-cuts-what-it-measures)** — Product Advisors · 0 votes  
  Four-sleeve autonomous options-and-equity agent on Alpaca. Math places every order; local LLMs may only veto a buy. When the broker ledger said a sleeve was losing, we cut it.  
  *Notable:* A sleeve was retired when the broker ledger showed a loss while the engine claimed profit; the 2% daily-loss breaker survives restarts.
- **[SentinelTrade](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/freedolls/sentineltrade)** — FreeDolls · 0 votes  
  A risk-gated algorithmic trading agent built on Alpaca. It scans market data, generates BUY/HOLD/SELL signals from moving averages and RSI, then routes every trade through a hard-coded risk manager before paper…  
  *Notable:* Every run defaults to dry-run printing intended orders; a --live flag is required, and existing holdings are checked to avoid re-buying.
- **[The Future of Autonomous Bot Trading: JuventusAI](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/juventusai-the-future-of-autonomous-bots/the-future-of-autonomous-bot-trading-juventusai)** — JuventusAI - The Future of Autonomous Bots · 0 votes  
  JuventusAI is an autonomous trading bot that pairs technical pattern detection and LLM trade validation with a hardcoded Deterministic Risk Gate on Alpaca, eliminating AI hallucinations and human emotion to execute…  
  *Notable:* Optuna tunes moving-average windows and confluence thresholds on historical data before deployment; exits use bracket orders plus signal-driven market exits.
- **[TradOX](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/tradox/tradox)** — TradOX · 0 votes  
  TradOX is an autonomous AI trading agent for Alpaca's paper trading platform. It scans a stock watchlist using RSI, MACD, and moving averages, only trades when signals agree, and enforces a hard stop-loss.  
  *Notable:* Acts only when two of three indicators (RSI, MACD, SMA trend) agree; a goal-of-the-day target locks gains and pauses trading.

## Strategy discovery & self-improving research loops

The core loop generates, backtests, stress-tests and scores strategies or the agent's own past decisions, then allocates capital or rewrites its rules from the results. A post-trade reflection memory bolted onto a fixed strategy does not qualify.

- **[Alpha Hunter — Autonomous AI Trading Scientist](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/crazyxyz/alpha-hunter-autonomous-ai-trading-scientist)** — crazyxyz · 135 votes  
  An autonomous AI trading scientist that discovers, challenges, validates, and deploys trading strategies with adaptive capital allocation, risk management, and real Alpaca paper execution.  
  *Notable:* An adversarial AI layer tries to break candidate strategies for overfitting and regime dependence before survivors get an Edge Score and compete for capital.
- **[trdrbot - a sELF improving options trading agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/trdrbot/trdrbot-a-self-improving-options-trading-agent)** — trdrbot · 12 votes  
  An autonomous options-trading agent that gathers research, forms theses, simulates the outcomes and sizes the best opportunities, then learns how to improve every step based on its goals.  
  *Notable:* Post-trade scoring separates whether the view, the structure, or luck drove the outcome, then rewrites prompts and selection criteria accordingly.
- **[Synthetix Alpha](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/synthetix-alpha-agents/synthetix-alpha)** — Synthetix Alpha Agents · 3 votes  
  An autonomous, risk-gated quantitative trading: LLM agents research strategies from arXiv and verify them out of sample, then a runtime agent trades options, equities and crypto on an Alpaca paper account through the…  
  *Notable:* Strategies are declarative JSON specs backtested with fills at mid plus half-spread, then re-tested on an unseen vendor and underlying for fragility.
- **[AllPath — Self-Evolving Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/duduandollie/allpath-self-evolving-trading-agent)** — DuduAndOllie · 1 vote  
  An autonomous agent that drafts its own strategies, trades them via Alpaca's MCP server, reflects nightly, and revises itself — behind a deterministic risk gate and a 15% drawdown circuit breaker. Live all week, zero…  
  *Notable:* Strategies are YAML with prose thesis plus deterministic entry/exit rules; a zero-LLM sentinel evaluates them every 30 minutes and nightly reflection revises them.
- **[alpaca-mind: a living trading mind](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/freedom-from-the-known/alpaca-mind-a-living-trading-mind)** — Freedom from the Known · 1 vote  
  A self-evolving options-trading agent that owns its schedule, playbooks, and risk doctrine — plus a second agent that grows a living web UI from the trader’s own journals. Born free: no preset strategy. No two…  
  *Notable:* Pre-registers research as git commits before running the numbers; agent-written scanners run under shadow validation with automatic quarantine.
- **[DarkRoom — AI Quant Research Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/agent-darkroom/darkroom-ai-quant-research-trading-agent)** — Agent Darkroom · 1 vote  
  DarkRoom is an autonomous AI trading agent that researches markets, generates strategies, tests them against historical data, evaluates risk and executes decisions through a structured quantitative workflow.  
  *Notable:* Generates multiple strategy candidates and rejects those failing backtests run under transaction-cost and execution-constraint assumptions before committing.
- **[tiffjaifam](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/tiffjaifam/tiffjaifam)** — Tiffjaifam · 1 vote  
  An autonomous AI trading agent that backtests and selects validated strategies, adapts to market regimes, translates signals into options trades, manages risk, and executes through Alpaca.  
  *Notable:* Treats trading methodologies as competing strategy families evaluated by walk-forward validation and regime analysis before translating a view into options trades.
- **[TradingHive](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/order-x-ai/tradinghive)** — ORDER X AI · 1 vote  
  TradingHive is an autonomous AI trading agent that combines reinforcement learning, real-time Alpaca market data, dynamic risk management, and multi-agent strategy evolution to make adaptive, auditable options-trading…  
  *Notable:* A reinforcement-learning layer learns from state-action-reward outcomes while a Hive evaluates and evolves multiple strategy bots across generations.
- **[AlphaBeater](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/stillcookin/alphabeater)** — StillCookin · 0 votes  
  An LLM-powered research agent that turns Alpaca market data into testable factors, validates them, builds risk-capped options trades, and executes paper experiments through Alpaca MCP.  
  *Notable:* LLM hypotheses are compiled into a constrained factor language evaluated by Python, never model-generated code, across chronological train/validation/test splits with costs.
- **[Aperture: a desk that fires its own strategies](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/night-lab/aperture-a-desk-that-fires-its-own-strategies)** — Night Lab · 0 votes  
  An autonomous options desk where four AI agents argue with each other and deterministic code decides what they may risk. It researches, funds and fires its own strategies. Final scored result: -1.081% over four sessions.  
  *Notable:* Risk Warden reduces each leg to expiry payoff geometry and vetoes any uncovered loss region; strategy sleeves lose budget after repeated vetoes.
- **[APEX - Anti-Overfitting Research Pipeline + agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/richardlim/apex-anti-overfitting-research-pipeline-agent)** — RICHARDLIM · 0 votes  
  An autonomous Alpaca trading agent where nothing trades live unless it survives walk-forward out-of-sample gates — 16 strategies tested, 10 rejected, plus a signal-keyed options wheel (CSPs + covered calls) already…  
  *Notable:* Strategies deploy only after passing walk-forward gates (OOS Sharpe >= 0.5, all folds positive, IS-to-OOS degradation under 50%) using identical backtest/live code.
- **[AURIGA Autonomous Quant Research&Investment Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/mythology/auriga-autonomous-quant-researchandinvestment-agent)** — Mythology · 0 votes  
  AURIGA is an autonomous quant research agent that discovers XGBoost trading rules, gates them through 8 deterministic risk checks, and deploys defined-risk options spreads on Alpaca paper — the LLM narrates, it never…  
  *Notable:* Trading rules are extracted from XGBoost tree paths and admitted only after Sharpe, win-rate, profit-factor and FDR-controlled thresholds, with a 20% untouched holdout.
- **[Futarchists Options](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/futarchists/futarchists-options)** — Futarchists · 0 votes  
  Futarchists Options is a modular strategy discovery and execution system that encodes options strategies as genetic sequences, evolves them through validated research, and uses deterministic Python for testing, risk…  
  *Notable:* Encodes strategies as genomes (structure, signals, delta, DTE, width) evolved via crossover and mutation; agents propose experiments but cannot promote strategies.
- **[Hindsight Alpha — options agent, leak-checked](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/hindsight-alpha/hindsight-alpha-options-agent-leak-checked)** — Hindsight Alpha · 0 votes  
  An autonomous options agent on Alpaca (CLI) that scores every parameter twice — full history vs. only what was knowable — and refuses to trade when the winners disagree. Every run and every refusal is logged and…  
  *Notable:* Scores each parameter on full history and again with the last 20 days hidden; refuses the symbol if the winning parameter changes.
- **[Odysseus - AI-Powered Strategy Research](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/odysseus/odysseus-ai-powered-strategy-research)** — Odysseus · 0 votes  
  Odysseus turns any AI agent into an autonomous trading researcher that discovers hypotheses, builds deterministic C# StockSharp strategies, backtests and optimizes them on Alpaca data, and validates finalists on unseen…  
  *Notable:* Splits data into development, validation and a hidden closed slice measured only as a final check; every dataset is frozen and hashed.
- **[OrderGuard: Safe AI Trading](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/thevincicoder/orderguard-safe-ai-trading)** — the_vinci_coder · 0 votes  
  A multi-agent AI trading system that researches, backtests, stress-tests, and evolves strategies before execution, with deterministic risk controls ensuring AI decisions cannot bypass safety limits on Alpaca paper…  
  *Notable:* Strategies get an adversary robustness score and a lifecycle state (ALIVE/WATCH/KILLED) that the deterministic order gate checks before any trade.
- **[SPECIES - Evolutionary Quant Research](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/origin-labs/species-evolutionary-quant-research)** — Origin Labs · 0 votes  
  An evolutionary quant research system that breeds trading strategies, validates survivors with deterministic evidence, and safely connects qualified candidates to Alpaca paper trading.  
  *Notable:* Evolved strategy champions must pass separate walk-forward and regime-robustness qualification gates, with traceable lineage, before touching paper execution.
- **[SPY Sentinel AI](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/spy-sentinel-ai/spy-sentinel-ai)** — SPY Sentinel AI · 0 votes  
  Alpaca-connected SPY options paper agent with two separate authorities: evidence must earn the right to become learning, and learning must independently earn the right to replace the Champion.  
  *Notable:* Quarantined option data whose freshness could not be proven, excluding it from learning while preserving records; Challengers cannot self-promote over the Champion.

## Trader copilot, chat & education

A human stays in the loop: chat assistants, trade-idea explainers, one-click approval workflows, journaling or teaching tools that recommend rather than execute autonomously.

- **[AI Stock Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/shubhpreetaiadda1/ai-stock-trading-agent)** — ShubhpreetAIAdda#1 · 1 vote  
  AI Stock Trading Agent is an intelligent system that analyzes stock market data, identifies trading opportunities, predicts market trends, and generates buy, sell, or hold signals using Artificial Intelligence and…  
  *Notable:* Generates buy/sell/hold signals from MA, RSI and MACD as a decision-support tool; paper trading and risk assessment are listed as future work.
- **[lattice](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/yassine/lattice)** — yassine · 1 vote  
  Lattice makes AI-powered market analysis and paper trading accessible through natural language, while giving users clear control over risk.  
  *Notable:* Keeps technical and news strategies as separately toggleable agents so every opportunity's origin (price evidence vs. real-world event) stays attributable.
- **[TradeMind - AI Options Trading & Risk Engine](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/trademind/trademind-ai-options-trading-and-risk-engine)** — TradeMind · 1 vote  
  TradeMind is an autonomous AI options trading engine with deterministic guardrails. It turns natural language prompts into priced trade proposals, requiring human confirmation before executing via Alpaca Trading API.  
  *Notable:* Plain-English conditional prompts become priced trade proposals gated by a 10% buying-power cap and 24-hour order limits, then require human confirmation.
- **[Axiom: A trade helper](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/team029/axiom-a-trade-helper)** — Team_029 · 0 votes  
  Axiom is an AI trading agent that reasons over live Alpaca market data and per-ticker ML forecasts, then executes real options trades in your paper account through natural conversation — no manual order forms, the agent…  
  *Notable:* Per-ticker ML models with chronological splits and precision-based evaluation feed a rules layer that picks calls, puts or spreads by direction and volatility.
- **[BABIL — Human-in-the-Loop AI Options Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/babil/babil-human-in-the-loop-ai-options-trading-agent)** — BABIL · 0 votes  
  BABIL is a human-in-the-loop AI options trading agent that separates AI reasoning from execution authority through deterministic risk gates, explicit human approval, fail-closed execution, and a kill switch.  
  *Notable:* Proposed price, strike, quantity and premium are re-validated by a deterministic layer before a human gives final approval; kill switch included.
- **[Dark Wolf Sentinel](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/dark-wolf-sentinel/dark-wolf-sentinel)** — Dark Wolf Sentinel · 0 votes  
  Dark Wolf Sentinel is a safety-first AI market intelligence and paper-trading research agent using Alpaca data, Alpaca MCP news context, and GPT-5.6 analysis to produce transparent trade-or-pass reasoning without…  
  *Notable:* Separates probabilistic analysis from deterministic authority: outputs trade-or-pass reasoning with regime, conflicting evidence, and invalidation logic, with execution disabled entirely.
- **[Gypsi Avenger](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/wescodies/gypsi-avenger)** — WesCodies · 0 votes  
  Gypsi is an AI-powered trading platform with a conversational agent, real-time market analysis, deterministic trading logic, and MCP tools, enabling users to analyze markets, manage risk, and trade across platforms…  
  *Notable:* Backend computes Smart Money Concepts (liquidity sweeps, order blocks, fair value gaps) deterministically while the LLM interprets and converses.
- **[Multi-Asset Watchlist Scanner](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/alpacateam/multi-asset-watchlist-scanner)** — AlpacaTeam · 0 votes  
  Track and scan multiple asset classes in real time with customizable technical and fundamental alerts. Monitor stocks, crypto, forex, and commodities simultaneously to catch market breakouts and trading opportunities…  
  *Notable:* Alert scanner rather than an agent: technical, price-action and fundamental scans fire desktop, mobile or webhook alerts for a human to act on.
- **[Options Strategy Lab](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/who-knows/options-strategy-lab)** — who knows · 0 votes  
  Options Strategy Lab is an advanced paper-trading web application designed for multi-leg options strategies on commodity ETFs. Key feature is its wizard for principiant and data driven support combining meteo, news…  
  *Notable:* Beginner wizard for multi-leg options with a rule that the agent cannot execute any trade it cannot logically justify.
- **[RazorStack Trading](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/runtime-terror/razorstack-trading)** — Runtime Terror · 0 votes  
  RazorStack Trading is an AI-assisted platform that transforms market signals into explainable, risk-gated paper-trading decisions.  
  *Notable:* HOLD signals cannot create orders and the browser never touches broker credentials; a server-side risk service is the sole approval authority.
- **[SolidRoute: Risk-Managed Options Execution Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/finance/solidroute-risk-managed-options-execution-agent)** — InvestTech · 0 votes  
  SolidRoute safeguards traders by combining automated Alpaca API execution, live account balance tracking, and an interactive volatility-based risk gatekeeper to prevent emotional execution.  
  *Notable:* An IV-based gatekeeper triggers a cool-down warning banner before risky orders and offers a pivot to low-risk defensive ETFs.
- **[Trade Bot](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/trade-bot/trade-bot)** — Trade Bot · 0 votes  
  An AI customer service agent for stock trading—explaining portfolio updates, order statuses, and finance terms via the Alpaca API.  
  *Notable:* Conversational agent places market and limit orders and doubles as support that decodes order errors and explains finance terms.
- **[TradeAudit AI — AI Trade Audit Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/code-voyagers/tradeaudit-ai-ai-trade-audit-agent)** — Code Voyagers · 0 votes  
  An AI agent that automatically explains every stock trade in plain English, scores risk levels, maintains audit logs, and answers trading questions via natural language. Built on Alpaca Trading API + Groq AI.  
  *Notable:* WebSocket fill detection triggers an LLM plain-English explanation and risk score saved to an audit database users can query by chat.
- **[TradeGuard](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/breath/tradeguard)** — Breath · 0 votes  
  TradeGuard: a human-in-the-loop options trading agent for Alpaca. An AI proposes a defined-risk call or put with reasoning; a human approves or denies it; only then does it execute, with every decision logged to a…  
  *Notable:* A tool denylist blocks anything named order or delete, and proposals are validated against pre-filtered candidates to stop hallucinated symbols.
- **[TradePilot: Explainable AI Trading Agents](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/white-hat/tradepilot-explainable-ai-trading-agents)** — White Hat · 0 votes  
  TradePilot is an accountable AI trading system where AI proposes trades, deterministic risk controls constrain them, humans approve, and Alpaca executes paper trades. Every decision is recorded in an explainable audit…  
  *Notable:* A Forensics agent derives stored lessons only from closed trades with real outcomes, never from open or hypothetical trades.
- **[Vermiliion](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/vermilion/vermiliion)** — Vermilion · 0 votes  
  Vermilion is a self-auditing AI trading agent on Alpaca. DeepSeek scores a 13-symbol watchlist, refuses by default, and queues every trade for human approval via Telegram, WhatsApp, or Email. 17-tool MCP server and…  
  *Notable:* Every order waits in a pending_decisions queue until a human approves via Telegram, WhatsApp, email, or the in-app queue.

## Risk & portfolio management overlays

The product manages an existing portfolio's risk: hedging, rebalancing, exposure or drawdown limits, tail protection, or allocation across sleeves, rather than originating directional trades.

- **[VibeHedge: Autonomous AI Options Hedging Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/shinydatatech/vibehedge-autonomous-ai-options-hedging-agent)** — ShinyDataTech · 7 votes  
  An autonomous AI trading agent combining ForecastAgent xLSTM time-series forecasting, FinRL-X risk gates, and Vibe-Trading Options Lab Greeks to execute protective options hedges via Alpaca FastMCP on Google Cloud Run.  
  *Notable:* Hedging activates only when equity breaches a 2.5% drawdown floor; protective put targeted at delta -0.35 within a 1.5% cost budget.
- **[Liquidity Leak](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/liquidity-leak/liquidity-leak)** — Liquidity Leak · 5 votes  
  An autonomous agent that holds a real book of stocks on Alpaca paper and defends it with options. It never predicts direction. It measures risk in deterministic Python, lets a model judge posture, and enforces every cap…  
  *Notable:* Model picks one pre-sized candidate from an admissible set and never chooses strike, expiry or size; premium selling disallowed above risk score 40.
- **[Hedgify](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/torque/hedgify)** — Torque · 1 vote  
  Hedgify is an autonomous multi-agent trading system built on Alpaca's paper trading + options APIs. A supervisor agent monitors your portfolio for drawdowns in real time.  
  *Notable:* Idempotency guard checks whether a symbol already carries protection, so sixteen duplicate drawdown alerts produced zero duplicate put orders.
- **[SentinelAlpha](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/sentinel-alpha/sentinelalpha)** — Sentinel Alpha · 1 vote  
  SentinelAlpha is an explainable AI portfolio-protection agent that detects risk, selects and sizes protective puts, applies deterministic risk gates, and autonomously executes approved hedges through Alpaca paper…  
  *Notable:* Hedge ratio is bounded and sized against actual 100-share lots; each ExplainHedge record pre-commits the conditions for releasing the hedge.
- **[TailGuard AI: Autonomous Options Insurance](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/solo32/tailguard-ai-autonomous-options-insurance)** — Solo32 · 1 vote  
  TailGuard turns a plain-English downside-risk mandate into a live, deterministic QQQ put-spread proposal using Alpaca Paper account and market data, then proves every safety decision with a machine-readable receipt.  
  *Notable:* Plain-English loss mandate becomes a deterministic QQQ put-spread payload that is staged, not submitted, with a machine-readable JSON audit receipt.
- **[AEGIS - Autonomous Adaptive Portfolio Hedge Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/riwano/aegis-autonomous-adaptive-portfolio-hedge-agent)** — Riwano · 0 votes  
  Autonomous multi-agent quantitative system that monitors live Alpaca equity portfolios, evaluates competing multi-leg option hedge structures through deterministic risk gate, executes trades, and dynamically adapts…  
  *Notable:* Simulates puts, spreads, collars and an explicit no-hedge baseline, then rolls or trims protection as delta drift and volatility shift.
- **[Alpha: Autonomous Portfolio Intelligence](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/alpha/alpha-autonomous-portfolio-intelligence)** — Alpha · 0 votes  
  Alpha is an autonomous portfolio intelligence system that learns from market data, manages risk, and optimizes investment decisions in real time through adaptive, data-driven automation.  
  *Notable:* A Data-Learn-Decide-Execute cycle feeds executed trades and outcomes back into allocation decisions; no specific signal or instrument is named.
- **[Backstop](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/crtlaltdestroy/backstop)** — Crtl_Alt_Destroy · 0 votes  
  Backstop is a policy-governed autonomous paper-trading agent that rebalances an inverse-volatility basket while enforcing fail-closed pre-trade risk controls.  
  *Notable:* Drawdown killswitch blocks risk-adding orders but allows a narrow, provably exposure-reducing equity sell; inconsistent exposure data fails closed.
- **[Bloom Trading Agent - AI-Powered Market Insights](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/the-fugees/bloom-trading-agent-ai-powered-market-insights)** — The Fugees · 0 votes  
  An autonomous options-only trading Agent,backed by a real Alpaca paper account  
  *Notable:* Falls back to deterministic heuristics when no LLM provider is available; autonomous entry disabled by default with two-step confirmation on liquidation.
- **[Drawdown Guard](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/woolly-trader/drawdown-guard)** — Woolly Trader · 0 votes  
  Drawdown Guard is an autonomous AI agent that keeps the portfolio within a client-defined downside limit through an options overlay strategy  
  *Notable:* Stress-tests the portfolio across decline scenarios each session and buys protective puts or collars only when the client's downside budget is breached.
- **[raptorclick](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/raptorclick/raptorclick)** — RaptorClick · 0 votes  
  RaptorClick — An AI-Assisted Portfolio-Protection Auction on Alpaca  
  *Notable:* Keeps a Shadow Book of the unprotected portfolio to compute a Protection Delta, making each hedge's cost and coverage explicitly measurable.
- **[Shield-AI Autonomous Risk Guardrails Hedging Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/baaibeek-supreme/shield-ai-autonomous-risk-guardrails-hedging-agent)** — Baaibeek supreme · 0 votes  
  Shield-AI is an autonomous risk agent for Alpaca. It computes 99% Portfolio VaR and net Delta continuously; when a guardrail breaks, its LLM layer reasons over the news shock and hedges the book with protective puts…  
  *Notable:* LLM stays idle until a VaR or net-delta guardrail breaks, then selects protective puts or collars inside a deterministic cost and exposure filter.
- **[TradeDog - The Datadog for AI Trading Agents](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/tradedog-the-datadog-for-ai-trading-agents/tradedog-the-datadog-for-ai-trading-agents)** — TradeDog - The Datadog for AI Trading Agents · 0 votes  
  An autonomous guardian that watches your trading bot 24/7 on Alpaca - fixes stuck orders, kills rogue bots, insures positions with real multi-leg option collars, and barks on WhatsApp before the AI agent herd stampedes.  
  *Notable:* Emergencies skip the LLM entirely (kill switch first, explanation after); positions are insured with near-zero-cost collars as single multi-leg orders.
- **[Volatility-Aware Options Hedging Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/alphawire/volatility-aware-options-hedging-agent)** — AlphaWire · 0 votes  
  An autonomous agent that watches SPY in real time, scores risk from live market data, and executes an explainable protective-put hedge via Alpaca's Trading API when conditions justify it.  
  *Notable:* Only the volume-spike threshold was tuned to make the hedge path demonstrable; the other thresholds were left untouched and disclosed.

## Infrastructure, safety harnesses & tooling

MCP servers, SDK wrappers, broker-side safety or certification gates for any agent, stress-test harnesses, audit and replay tooling, dashboards or frameworks, where the trading strategy is only a demo payload.

- **[MIZAN](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/superbuddies/mizan)** — SuperBuddies · 1 vote  
  Mizan is an AI trading governance system that lets agents research and propose trades, while deterministic risk controls, authorization, audit trails, and Alpaca Paper Trading decide what can actually reach the broker.  
  *Notable:* Governor can APPROVE, REDUCE, or REJECT a proposal; advisory AI may never override deterministic rules or increase an authorized quantity.
- **[13forge: AI Trading Safety Airlock](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/13forge/13forge-ai-trading-safety-airlock)** — 13forge · 0 votes  
  AI can propose the trade. Rust decides if it is safe. 13forge is a strict execution airlock that runs deterministic safety gates on AI options trading strategies before any order reaches the Alpaca broker API.  
  *Notable:* Rust airlock rebuilds the order from quoted market data, runs seven deterministic gates, refuses by default, and records exactly what was refused and why.
- **[Abitda](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/visionaries/abitda)** — Visionaries · 0 votes  
  ABITDA is an institutional options agent harness that stress-tests AI agents against real Black Swan crashes, enforces Black-Scholes Greeks barriers, and deploys only Grade A+ certified agents to a live Alpaca paper…  
  *Notable:* Replays five historical crashes bar-by-bar to grade an agent before granting broker access; a rolling Z-score win-rate monitor self-suspends trading.
- **[Alphora](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/alphora/alphora)** — Alphora · 0 votes  
  AI-agent financial trading platform built with Rust and Model Context Protocol, connecting VS Code and other compatible clients to Alpaca's paper-trading and market-data APIs for autonomous market research, portfolio…  
  *Notable:* Rust MCP server exposing 23 Alpaca paper-trading tools with auto-generated schemas, defaulting to the paper environment for safety.
- **[Gauntlet](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/midexol/gauntlet)** — Mide_xol · 0 votes  
  GAUNTLET is an adversarial AI strategy-validation layer for trading strategies, built for the Alpaca AI Trading Agents Hackathon.  
  *Notable:* Attacks a proposed strategy across regimes, parameter perturbations, and volatility shocks through a fixed pipeline before it is allowed to trade paper capital.
- **[Guardian](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/packy/guardian)** — Packy · 0 votes  
  Autonomous paper trading on Alpaca, with policy-gated execution.  
  *Notable:* Policy engine yields three outcomes (block, approve for human review, submit) and one guardrail engine is shared by web, MCP and Telegram.
- **[Options Alpha Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/newbe/options-alpha-agent)** — Newbe · 0 votes  
  Three autonomous options-trading agents — deterministic rules, a fully autonomous LangChain agent, and a self-computed volatility-edge strategy — sharing one hard-coded risk layer across three separate Alpaca paper…  
  *Notable:* Three differently-decisioned agents run on three separate paper accounts behind one shared code-enforced risk layer with a kill switch checked first.
- **[QuantDesk: Safe AI Trading Infrastructure](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/quantdesk/quantdesk-safe-ai-trading-infrastructure)** — QuantDesk · 0 votes  
  QuantDesk is a safety-first AI quantitative trading system that separates model research from execution, validates strategies before use, and routes paper trades through deterministic risk, broker-reconciliation, and…  
  *Notable:* Python research is separated from a C#/.NET runtime that is the sole execution authority and checks the research artifact is validated and current.

## Arbitrage, pairs & market making

Trades relationships that should revert rather than direction: cointegrated pairs and stat-arb, cross-asset or cross-venue price gaps, no-arbitrage violations on the options surface, or two-sided market making with delta hedging.

- **[Autonomous Prediction Market Arbitrage Engine](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/apache-ai/autonomous-prediction-market-arbitrage-engine)** — Apache AI · 2 votes  
  Real-time prediction market arbitrage dashboard scanning Polymarket, Kalshi, and leading venues. Instantly detects cross-exchange price gaps, calculates fee-adjusted yields, and delivers live execution alerts to lock in…  
  *Notable:* Computes a fee-adjusted APY for each cross-venue mispricing, factoring venue fees, slippage and liquidity before alerting operators.
- **[MarginCalled — TP2 Options Arbitrage Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/margincalled/margincalled-tp2-options-arbitrage-agent)** — Margincalled · 2 votes  
  An autonomous options agent that finds four-contract price rectangles breaking a no-arbitrage theorem, proves each one is real before trading, and exits when the mispricing corrects. 98% of 43,566 tracked violations…  
  *Notable:* Treats an empty dividend list as unresolved, not proof of no dividend; found the 2c mispricing equals the 2c spread, so execution decides sign.
- **[The Specialist-Options market-maker+convexity desk](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/alpekka/the-specialist-options-market-makerconvexity-desk)** — ALPEKKA · 1 vote  
  An autonomous options market maker on Alpaca: it quotes both sides of the market, hedges every fill instantly, and runs a defined-risk convexity book in parallel with an LLM that advises but never places a trade.  
  *Notable:* Reconciliation logic specifically guards against Alpaca's ~10% random partial fills on multi-leg orders, which can leave a spread as a naked position.
- **[Vantage, your AI trader](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/salamancasharks/vantage-your-ai-trader)** — SalamancaSharks · 1 vote  
  Vantage is an autonomous AI trading agent for Alpaca's paper trading environment — Gemini analyzes live market data via MCP and executes a transparent pairs-trading strategy with full reasoning audit logs.  
  *Notable:* Analytics page reports 'insufficient data' instead of fabricating Sharpe or win-rate figures when trade history is too sparse.
- **[Options Alpha Agents: Pairs Trading Bot](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/vgatrades/options-alpha-agents-pairs-trading-bot)** — VGA_trades · 0 votes  
  An autonomous options pairs-trading agent that finds statistically cointegrated S&P 500 stocks and trades divergence through defined-risk spreads, with tested stop-loss, take-profit, and drawdown risk gates enforced…  
  *Notable:* Cointegrated-pair z-score divergence expressed via defined-risk option spreads, with a 3-day time stop and a one-open-pair-per-stock concentration rule.
- **[THESIS: options volatility engine](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/volound/thesis-options-volatility-engine)** — Volound · 0 votes  
  An autonomous options agent that fits arbitrage-free volatility surfaces to live SPY chains, detects where the market disagrees with its own model, and refuses any trade whose edge fails to clear measured execution cost.  
  *Notable:* Edge must clear 1.5x a round-trip cost that was measured by actually opening and closing a real spread.
- **[Z-Gate](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/nullsignal/z-gate)** — NullSignal · 0 votes  
  Z-Gate is a hybrid multi-agent statistical arbitrage system trading equity options and 24/7 crypto via Alpaca. It uses a Kalman Filter and Ornstein-Uhlenbeck SDE to extract dynamic beta and link options DTE directly to…  
  *Notable:* Option expiration is snapped to the OU mean-reversion half-life, DTE = clamp(tau * 2.5, 7, 30), so contracts outlast expected spread convergence.

## Other

Not a trading agent (unrelated apps, placeholders) or too vague to place.

- **[Tissue Regeneration & Genetic Factor Navigator](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/tissulogic/tissue-regeneration-and-genetic-factor-navigator)** — Tissulogic · 2 votes  
  An AI-powered autonomous platform mapping tissue engineering parameters directly to algorithmic biotech equity & options execution via Alpaca (MCP/CLI Enabled).  
  *Notable:* Description is a bioinformatics platform for tissue regeneration; no trading logic is described beyond the short-description tagline.
- **[ACPIA-Srishti](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/godh/acpia-srishti)** — GodH · 1 vote  
  SRISHTI — AI Criminal & Paedophile Investigation Platform (ACPIA) SRISHTI (System for Real-time Investigation & Synthetic Threat Intelligence) is an enterprise-grade AI Criminal & Paedophile Investigation Assistant.  
  *Notable:* Criminal-investigation evidence pipeline; nothing in the summary relates to trading or Alpaca.
- **[SmartLink: Autonomous AI Trading & Analytics Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/smart-link/smartlink-autonomous-ai-trading-and-analytics-agent)** — smart link · 1 vote  
  SmartLink is an autonomous AI agent powered by LLMs and ClickHouse to analyze high-frequency traffic conversions, detect automated anomalies, and execute real-time algorithmic marketing and trading decisions.  
  *Notable:* Not a trading agent: an LLM writes read-only SQL over ClickHouse clickstream data for anomaly and bot detection in marketing campaigns.
- **[AURA AI Trading Agent](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/team-believer/aura-ai-trading-agent)** — Team believer · 0 votes  
  An autonomous options trading and risk intelligence console powered by a microservices architecture (Vue, Laravel, FastAPI). AURA AI evaluates market trends and executes simulated trades with real-time risk analysis.  
  *Notable:* Summary describes only a Vue/Laravel/FastAPI microservices split; no trading strategy, signal or risk mechanism is specified.
- **[Jsjsjsjsjsjsjsjsjss](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon/uahahaha/jsjsjsjsjsjsjsjsjss)** — Uahahaha · 0 votes  
  Sjjsjsjsjsjsjsjjsjsjsjsjsjsjjssnsnsjsjsjsjsjsjjdjjdj  
  *Notable:* Placeholder submission; title and description are keyboard gibberish with no trading content.

## Method

Submissions were pulled from lablab's public submissions API (`/api/v4/submissions`, paged, then filtered to this event) by the `.claude/skills/hackathon-submissions` skill, whose script also renders this page. Each project's description field, the same text shown on its lablab page, was the only input. Projects were split into batches of 20 and read by parallel Claude subagents in two passes: the first proposed categories from what each batch's agents actually do (the trading approach, not the asset class or tech stack), which were merged by hand into the list above; the second assigned every project to exactly one category and wrote the *Notable* line, grounded in the summary only.

Caveats: summaries are marketing copy capped at 2,000 characters, so a project may do more or less than it claims. A project that combines several approaches sits under its primary one. Vote counts are community likes on lablab, not judging results.
