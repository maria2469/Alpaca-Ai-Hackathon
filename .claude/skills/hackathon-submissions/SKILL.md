---
name: hackathon-submissions
description: Categorize every submission of a lablab.ai hackathon from the teams' written summaries into docs/HACKATHON_SUBMISSIONS.md, organized by trading approach with a TOC, definitions and a one-line "notable idea" per project, using parallel subagents in two passes (propose categories, then assign). Use when the user asks to "categorize the hackathon submissions", "see what the other teams built", "learn from other teams' submissions", "pull the lablab submissions", or wants a hackathon post-mortem of the field.
---

# Hackathon submissions

Turn the public lablab.ai submission summaries of one hackathon into a category map the team
can learn from. Data comes from lablab's JSON API through `submissions.py` (beside this file);
categorization is done by parallel subagents reading batch files; the markdown is rendered
deterministically. Test on the top 10 first, then run the full set on a separate go-ahead.

## Guardrails

- **Summaries only.** Subagents read the `description` field. Nobody opens repos, presentations
  or demo links. The prompt templates forbid WebFetch/WebSearch; keep it that way.
- **Read-only against lablab**, about 30 GET requests total. robots.txt disallows the ClaudeBot
  crawler and signals `ai-train=no`; this is personal research through a plain script, not a
  crawl. Do not add retries in a loop or parallel fetches.
- **Key on `uid` (`team_slug/slug`), never on `slug`.** In 2026 five slugs were reused by
  different teams (one by three). `build` refuses to write if any uid is missing, duplicated or
  in an unknown category; fix the assignment file, do not weaken the check.
- **Concurrency cap is 20 subagents.** A 22-batch run needs two waves; launching more returns an
  error, not a queue.
- **The taxonomy merge is a judgment step.** Show the user the proposals summary before
  finalizing `taxonomy.json`. "LLM proposes, deterministic Python gate disposes" is nearly
  universal and is **not** a category; categorize by primary trading approach.
- **Stop after the test run** and report; the full run is a separate go-ahead (CLAUDE.md,
  one task at a time). The skill commits at the very end and never pushes.
- Show the user the full output of every `submissions.py` command.

## Step 1 — Fetch

```bash
EVENT=alpaca-ai-trading-agents-hackathon      # the slug in the lablab.ai URL
SKILL=.claude/skills/hackathon-submissions
SCRATCH=<scratchpad dir>/subs                  # batches, proposals, assignments live here
uv run python $SKILL/submissions.py fetch --event $EVENT 2>&1 | tail -3
```

It pages `/api/v4/submissions` newest-first, keeps only this event, and compares the count to
`/api/v4/<event>/live-stats`. A mismatch aborts; pass `--allow-mismatch` only after telling the
user. The cache is `logs/lablab_<event>.json` (gitignored). Find our own entry's uid for later:

```bash
uv run python - <<'EOF'
import json,glob; d=json.load(open(glob.glob('logs/lablab_*.json')[0]))
print([s['uid'] for s in d['submissions'] if 'paca' in s['title'].lower()])
EOF
```

## Step 2 — Test run on the top 10

```bash
uv run python $SKILL/submissions.py batch --event $EVENT --top 10 --size 5 --out $SCRATCH/batches
mkdir -p $SCRATCH/propose $SCRATCH/assign
```

**Pass 1 (propose).** One `general-purpose` subagent per batch file, all in one message. Each
prompt is exactly these lines, with paths filled in:

```
Read and follow exactly: <abs path>/.claude/skills/hackathon-submissions/pass1_propose.md
{TAXONOMY} = <abs path>/.claude/skills/hackathon-submissions/taxonomy_seed.json
{BATCH}    = $SCRATCH/batches/batch_NN.json
{OUTPUT}   = $SCRATCH/propose/propose_NN.json
```

Wait for all of them, then summarize the proposals (also used in Step 3):

```bash
uv run python - <<EOF
import json,glob
from collections import Counter
ex=Counter(); new=[]; other=[]
for f in sorted(glob.glob("$SCRATCH/propose/propose_*.json")):
    d=json.load(open(f)); n=f[-7:-5]
    for k,v in d.get("existing",{}).items(): ex[k]+=len(v)
    for c in d.get("new",[]): new.append((n,c["name"],len(c["slugs"]),c["definition"]))
    for k,v in d.get("other",{}).items(): other.append((n,k,v))
print("existing:",dict(ex.most_common()))
print("\nNEW:"); [print(f" [{n}] {name} ({c}): {d}") for n,name,c,d in new]
print(f"\nOTHER ({len(other)}):"); [print(f" [{n}] {k}: {v}") for n,k,v in other]
EOF
```

**Merge.** Write `$SCRATCH/taxonomy.json`: start from `taxonomy_seed.json`, add a category
only when two or more batches proposed the same idea or one batch has 3+ projects for it, tighten
any definition the agents flagged as ambiguous, keep `other` last. Aim for 10–13 categories.
Show the user the resulting list.

**Pass 2 (assign).** One subagent per batch, same shape, template `pass2_assign.md`,
`{TAXONOMY}` = `$SCRATCH/taxonomy.json`, output `$SCRATCH/assign/assign_NN.json`.

**Build and check.**

```bash
uv run python $SKILL/submissions.py build --event $EVENT --top 10 --batch-size 5 \
  --taxonomy $SCRATCH/taxonomy.json --assignments $SCRATCH/assign --ours <team_slug/slug>
```

Read the generated `docs/HACKATHON_SUBMISSIONS.md` end to end. Report the taxonomy that
emerged, one borderline call you had to make, the cost per batch, and what to adjust. **Stop
here** and wait for the go-ahead.

## Step 3 — Full run

```bash
mkdir -p $SCRATCH/test_run && mv $SCRATCH/propose $SCRATCH/assign $SCRATCH/test_run/
mkdir -p $SCRATCH/propose $SCRATCH/assign
uv run python $SKILL/submissions.py batch --event $EVENT --size 20 --out $SCRATCH/batches
```

Pass 1 over all batches in waves of at most 20 agents; `{TAXONOMY}` is the test run's merged
`taxonomy.json` so agents propose only what is genuinely new. Run the proposals summary, merge
again (the test taxonomy is the seed; expect two to four additions), show the user, then pass 2
in waves. Build without `--top`:

```bash
uv run python $SKILL/submissions.py build --event $EVENT --batch-size 20 \
  --taxonomy $SCRATCH/taxonomy.json --assignments $SCRATCH/assign --ours <team_slug/slug>
```

Budget from 2026: about 50k subagent tokens and 90 s per 20-project batch per pass, so a
430-project run is roughly 44 agents and 2.5M tokens.

## Step 4 — Verify

`build` already guarantees every uid is assigned exactly once to a known category. Then:

```bash
uv run python - <<'EOF'
import re
md=open('docs/HACKATHON_SUBMISSIONS.md').read()
heads={re.sub(r'[^\w\s-]','',h.strip().lower()).replace(' ','-') for h in re.findall(r'^## (.+)$',md,re.M)}
links=set(re.findall(r'\]\(#([^)]+)\)',md))
print('unresolved anchors:', links-heads or 'none')
print('TOC sum:', sum(int(x) for x in re.findall(r'\((\d+)\)\]\(#',md)), '| entries:', md.count('\n- **['))
w=[len(n.split()) for n in re.findall(r'\*Notable:\* (.+)',md)]; print('notables:',len(w),'max words',max(w))
print('ours marked:', '**(ours)**' in md)
EOF
```

Spot-check three project URLs return HTTP 200 (`curl -sL -o /dev/null -w '%{http_code}'`).
GitHub anchors keep one hyphen per space and drop punctuation, so "a / b" becomes `a--b`;
the script's `anchor()` matches that rule.

## Step 5 — Link and commit

Add or refresh one sentence in `README.md` pointing at `docs/HACKATHON_SUBMISSIONS.md` (in
2026 it sits at the end of the Methodology section's "deeper studies" paragraph). Then commit
only the doc and README, message naming the event, project count and category count. Do not
push. The skill folder itself is committed separately by the user when it changes.

## Step 6 — Report

End with: the category table with counts, where our entry landed and how crowded that bucket
is, the categories that emerged beyond the seed, cost per batch, caveats (LLM-drawn
boundaries from 2,000-character marketing summaries; votes are community likes, not judging),
and the commit hash.

## Lessons from 2026

- The API ignores every event-filter parameter; `/apps?event=` is not filtered either, and
  the live page's "Load more" is client-side over a preloaded top 50. Paging newest-first and
  filtering on `event.slug` is the only complete route; the sitemap
  (`/server-sitemap/submission/N`) confirms the count.
- Descriptions are capped at 2,000 characters. Track tags are useless (all "Agent Builder /
  App Builder / Finance"). Winners are announced after the results page goes up; `position`
  is null until then.
- 267 of 427 projects had zero votes; the top two had more than 120 each.
- Categories that emerged and were not in the first seed: volatility relative value and
  regime-routed structures (proposed independently by 12 of 22 batches), LLM-discretionary
  agents whose whole pitch is the governance layer, and arbitrage / pairs / market making.
- Agents disagreed most on direction-chosen credit spreads (income vs directional) and on
  whether a bull/bear council makes a project "multi-agent". The tie-break rules in
  `pass2_assign.md` exist for that reason; tighten them rather than adding categories.
