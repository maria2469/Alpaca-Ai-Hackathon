---
name: trading-review
description: Post-close review of a PACA trading day — digest the cycle journal and PnL, score the previous review's watch-items, grade the day's entry/pass decisions, prepend a dated review to docs/trading_review.md, then recommend improvements and apply only what the user picks. Use when the user asks to "review today's trading", "run the trading review", "post-market review", "daily review", "how did we trade today", or "grade today's trades".
---

# Trading review

Run the after-close review of one trading day, as an experienced momentum trader auditing
their own book. The output is a new dated section at the TOP of `docs/trading_review.md` (a
living document, newest first) plus prioritized recommendations. You are reviewing both
the system AND the decision layer's judgment — grade honestly, including your own passes.

## Guardrails

- **Read-only until Step 6.** Analysis never places orders, edits settings, or touches code.
- **Never commit.** End by listing what is modified-but-uncommitted; the user commits.
- **Methodology changes are proposed, never applied silently** (CLAUDE.md rules). Apply a
  recommendation only after the user picks it in Step 6.
- Show the full output of every command verbatim — the user must see what you saw.
- If the market is still open (`TZ=America/New_York date` before ~16:00 ET on a weekday),
  say the day's data is incomplete and ask whether to continue anyway.
- One day is a small sample. State uncertainty; do not overclaim from a handful of trades.

## Step 1 — Gather (read-only)

```bash
TZ=America/New_York date
uv run python .claude/skills/trading-review/analyze.py 2>&1          # journal digest (pass YYYY-MM-DD for another day)
uv run --env-file .env pnl.py realized --json --days 1 2>&1          # authoritative round-trip P&L
uv run --env-file .env pnl.py positions --json 2>&1                  # open positions and marks
git log --oneline --since="6am" -- settings.yaml '*.py' 2>&1         # what changed in code/settings today
```

The digest is journal-only. `pnl.py` is the P&L authority — never recompute P&L from
journal marks. The git log matters for attribution: if behavior shifted mid-day, check
whether a settings/code change landed before blaming the market.

## Step 2 — Score the previous review's watch-items

Read the **newest** `## Review — ...` section of `docs/trading_review.md` and its
"Watch next session" list. Grade every item explicitly against today's digest:
**met / not met / no data**, one line of evidence each. This is the feedback loop that
tells us whether the last round of changes worked — never skip it.

## Step 3 — Grade the day's decisions

From the digest's decision-quality table (gate-PASS events) and the entry list:

- **Entries taken**: did the move continue (mid at +30m/+60m/EOD vs entry)? Was the exit
  reason sensible in hindsight? Account for spread friction — a "right direction" trade
  that couldn't clear the bid/ask round trip is not a win.
- **Passes**: for each event passed on, would the standard structure (debit ~1/3 of width)
  have paid? Separate "right process, wrong outcome" from genuine misses.
- **Screener/recheck blocks**: for entries the decider wanted but the machine refused,
  judge whether the block saved money or cost money.

Rows marked `h±x.xxx` predate mid journaling — grade those on histogram follow-through
only and say so. Verdict per decision: good / bad / inconclusive, one line each.

## Step 4 — Findings and recommendations

Prioritized list. For each: the evidence (numbers from Steps 1–3), the proposed change,
its CLAUDE.md classification (**bug fix / refactor / methodology change**), and a triage
(**FIX NOW / DEFER / IGNORE FOR HACKATHON**). Weigh probability × impact against
complexity — do not propose churn after one quiet day. "No changes recommended" is a
perfectly good outcome.

## Step 5 — Write the review

Prepend a section to `docs/trading_review.md`, directly under the intro paragraph and above
the previous `## Review — ...` section (older reviews stay untouched):

```markdown
## Review — YYYY-MM-DD

### Session stats
### P&L
### Prior watch-item scorecard
### Decision grades
### Findings
### Recommendations
### Watch next session
```

Keep it evidence-first, in the voice of the existing reviews. "Watch next session" must
be a concrete, checkable list — the next run's Step 2 grades it.

## Step 6 — Ask and apply

Present the recommendations with AskUserQuestion ("none" is a valid pick). Apply **only**
what the user picks, then verify:

```bash
uv run pytest -q 2>&1 | tail -3
uv run --env-file .env cli.py preflight 2>&1 | tail -1
```

If a picked change alters strategy/docs, keep `README.md` (Methodology) and the review's
Recommendations section consistent with what was actually applied.

## Step 7 — Report

End with: the day in three sentences, the watch-item scorecard verdicts, what was applied
vs deferred, tests run, and the explicit list of modified-but-uncommitted files with a
reminder that this skill never commits.
