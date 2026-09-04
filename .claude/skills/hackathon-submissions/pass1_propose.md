> Paths in braces ({TAXONOMY}, {BATCH}, {OUTPUT}) are given in your task message.

# Pass 1: propose categories for one batch

You are helping categorize hackathon submissions (AI trading agents built on Alpaca) so a team can learn from what other teams built.

Inputs (read both with the Read tool):
- The current taxonomy: {TAXONOMY}  (list of {key, name, definition})
- Your batch file {BATCH}: a list of ~20 projects with slug, title, team, likes, url, shortDescription, description.

Rules:
- Read ONLY the description and shortDescription fields. Do NOT fetch any URL. Do NOT open GitHub repos or presentations. Do NOT use WebFetch or WebSearch.
- Categorize by PRIMARY TRADING APPROACH: what the agent actually does to make or manage trades. Not by asset class, not by tech stack.
- Nearly every project has an "LLM proposes, deterministic Python risk gate disposes" pattern. That pattern alone is NOT a category.
- First try to place each project in an existing taxonomy category. Propose a NEW category only when 2 or more projects in your batch clearly share an approach that none of the existing categories covers (for example a crypto-specific approach, 0DTE scalping, pairs/stat-arb, earnings IV-crush plays, market making, copy/social trading, non-trading tools). Give the new category a short name and a one-sentence definition.
- Use "other" for projects that fit nothing, and say why in one short phrase.

Output: write strict JSON (no comments) with the Write tool to {OUTPUT}:
{
  "existing": {"<taxonomy key>": ["slug-a", "slug-b"], ...},
  "new": [{"name": "...", "definition": "...", "slugs": ["..."]}],
  "other": {"slug-x": "why it fits nothing"},
  "observations": "2-3 sentences: any existing category definition that felt wrong or too broad/narrow for this batch, and the most common pattern you saw."
}
Every slug in your batch must appear exactly once across existing, new, and other.

After writing the file, reply with only: one line per category (existing key or new name) with its count, then the observations sentence(s).
