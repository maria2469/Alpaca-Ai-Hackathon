> Paths in braces ({TAXONOMY}, {BATCH}, {OUTPUT}) are given in your task message.

# Pass 2: assign one category per project

You are categorizing hackathon submissions (AI trading agents built on Alpaca) so a team can learn from what other teams built.

Inputs (read both with the Read tool):
- Final taxonomy: {TAXONOMY}  (list of {key, name, definition})
- Your batch file {BATCH}: ~20 projects with uid, slug, title, team, likes, url, shortDescription, description.

Rules:
- Read ONLY the description and shortDescription fields. Do NOT fetch any URL. Do NOT open GitHub repos or presentations. Do NOT use WebFetch or WebSearch.
- Assign exactly one category_key from the taxonomy per project, by PRIMARY trading approach (what the agent actually does to make or manage trades). Not by asset class, not by tech stack.
- Tie-breaks:
  - If the summary names a specific instrument-level strategy (premium selling, directional options, equity signals, event-driven, and so on), prefer that category even if the project also has a multi-agent architecture or a deterministic risk gate. Nearly every project has an "LLM proposes, Python gate disposes" pattern; that pattern alone is NOT a category.
  - Use a multi-agent / committee category only when the main pitch is the council or agent chain itself and the instrument strategy is generic buy/sell/hold.
  - Use a research-loop category only when generating, backtesting, scoring strategies or self-rewriting rules is the core loop, not a side feature.
  - Use "other" only if nothing fits; say why in notable.
- "notable": one sentence, at most 25 words, stating the single most distinctive or instructive idea in the summary that another team could learn from (a mechanism, safeguard, or workflow). Grounded strictly in the summary text. Do not invent details. No praise, no marketing adjectives.

Output: write strict JSON with the Write tool to {OUTPUT}:
[
  {"uid": "exact-uid-from-input", "category_key": "key-from-taxonomy", "notable": "..."}
]
Every uid in your batch must appear exactly once (uids are unique; slugs alone are not).

After writing the file, reply with only one line per project: uid -> category_key.
