"""Research helper for the hackathon-submissions skill: pull one lablab.ai
hackathon's submissions and render docs/HACKATHON_SUBMISSIONS.md from
LLM-assigned categories.

Three subcommands, run in order (see SKILL.md for the subagent passes between
`batch` and `build`):

    python submissions.py fetch --event <slug>
    python submissions.py batch --event <slug> --top 10 --size 5 --out DIR
    python submissions.py build --event <slug> --taxonomy T.json --assignments DIR

`fetch` pages lablab's public JSON API. The server ignores every event filter,
so we page everything newest-first and keep only this event's entries
client-side, then check the count against the event's live-stats endpoint.
`batch` writes per-subagent input files. `build` merges the subagents'
assignment files and renders markdown; it is deterministic and refuses to run
if any project is missing, duplicated, or in an unknown category.

Stdlib only. Not part of the trading system.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

DEFAULT_EVENT = "alpaca-ai-trading-agents-hackathon"
DEFAULT_OURS = "win-or-die/paca-position-aware-agentic-capital-allocator"
API = "https://lablab.ai/api/v4/submissions?"
STATS = "https://lablab.ai/api/v4/{event}/live-stats"
SKILL_PATH = ".claude/skills/hackathon-submissions"


def event_url(event: str) -> str:
    return f"https://lablab.ai/ai-hackathons/{event}"


def cache_path(event: str) -> Path:
    return Path(f"logs/lablab_{event}.json")


def get_json(url: str) -> dict:
    req = urllib.request.Request(
        url, headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


# ---------------------------------------------------------------- fetch ----

def fetch(args: argparse.Namespace) -> None:
    event = args.event
    expected = get_json(STATS.format(event=event)).get("submissionCount")
    print(f"live-stats says {expected} submissions for {event}")

    cursor = None
    kept: dict[str, dict] = {}
    event_name = None
    pages = 0
    idle = 0  # pages in a row with no new entries for this event
    while True:
        q = {"take": "100", "order": "desc"}
        if cursor:
            q["cursor"] = cursor
        data = get_json(API + urllib.parse.urlencode(q))
        pages += 1
        before = len(kept)
        for s in data["submissions"]:
            if s["event"]["slug"] == event:
                kept[s["id"]] = slim(s, event)
                event_name = event_name or s["event"]["name"]
        cursor = data.get("nextCursor")
        idle = idle + 1 if len(kept) == before and kept else 0
        print(f"page {pages}: {len(data['submissions'])} items, kept so far {len(kept)}")
        # The feed is newest-first across all events; once this event has
        # stopped appearing for several pages, older pages will not have it.
        if not cursor or idle >= 5:
            break

    subs = sorted(kept.values(), key=lambda s: (-s["likes"], s["title"].lower()))
    if len(subs) != expected and not args.allow_mismatch:
        sys.exit(f"expected {expected} submissions, got {len(subs)}; "
                 "pass --allow-mismatch to write anyway")
    out = cache_path(event)
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"fetched": date.today().isoformat(),
                               "event": event, "event_name": event_name,
                               "submissions": subs}, indent=1))
    print(f"wrote {len(subs)} submissions to {out}")


def slim(s: dict, event: str) -> dict:
    return {
        "uid": f"{s['team']['slug']}/{s['slug']}",  # slugs alone repeat across teams
        "slug": s["slug"],
        "title": s["title"].strip(),
        "team": s["team"]["name"].strip(),
        "team_slug": s["team"]["slug"],
        "likes": s["_count"]["likes"],
        "url": f"{event_url(event)}/{s['team']['slug']}/{s['slug']}",
        "tech": [t["tech"]["name"] for t in s.get("techIn", [])],
        "shortDescription": (s.get("shortDescription") or "").strip(),
        "description": (s.get("description") or "").strip(),
    }


def load_cache(event: str) -> dict:
    path = cache_path(event)
    if not path.exists():
        sys.exit(f"{path} missing; run `fetch --event {event}` first")
    return json.loads(path.read_text())


# ---------------------------------------------------------------- batch ----

def batch(args: argparse.Namespace) -> None:
    subs = load_cache(args.event)["submissions"]
    if args.top:
        subs = subs[: args.top]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("batch_*.json"):
        old.unlink()
    n = 0
    for i in range(0, len(subs), args.size):
        chunk = [{k: s[k] for k in ("uid", "slug", "title", "team", "likes", "url",
                                    "shortDescription", "description")}
                 for s in subs[i:i + args.size]]
        (out / f"batch_{n:02d}.json").write_text(json.dumps(chunk, indent=1))
        n += 1
    print(f"wrote {n} batch files ({len(subs)} projects) to {out}")


# ---------------------------------------------------------------- build ----

def build(args: argparse.Namespace) -> None:
    cache = load_cache(args.event)
    subs = cache["submissions"]
    by_uid = {s["uid"]: s for s in subs}
    taxonomy = json.loads(Path(args.taxonomy).read_text())
    cats = {c["key"]: c for c in taxonomy}
    if "other" not in cats:
        sys.exit("taxonomy must contain an 'other' category")

    assigned: dict[str, dict] = {}
    problems: list[str] = []
    for f in sorted(Path(args.assignments).glob("assign_*.json")):
        for a in json.loads(f.read_text()):
            uid = a.get("uid")
            if uid not in by_uid:
                problems.append(f"{f.name}: unknown uid {uid!r}")
            elif uid in assigned:
                problems.append(f"{f.name}: duplicate uid {uid!r}")
            elif a.get("category_key") not in cats:
                problems.append(f"{f.name}: {uid} -> unknown category {a.get('category_key')!r}")
            else:
                assigned[uid] = a
    scope = subs[: args.top] if args.top else subs
    for s in scope:
        if s["uid"] not in assigned:
            problems.append(f"missing assignment for {s['uid']}")
    if problems:
        print("\n".join(problems))
        sys.exit(f"{len(problems)} problem(s); doc not written")

    groups: dict[str, list[dict]] = {k: [] for k in cats}
    for s in scope:
        groups[assigned[s["uid"]]["category_key"]].append(s)
    order = [c["key"] for c in taxonomy if c["key"] != "other"]
    order.sort(key=lambda k: (-len(groups[k]), cats[k]["name"].lower()))
    order.append("other")

    md = render(cache, scope, cats, groups, order, assigned, args)
    Path(args.out).write_text(md)
    print(f"wrote {args.out}: {len(scope)} projects in "
          f"{sum(1 for k in order if groups[k])} categories")


def anchor(text: str) -> str:
    a = text.strip().lower()
    a = re.sub(r"[^\w\s-]", "", a)
    return a.replace(" ", "-")  # GitHub keeps one hyphen per space, so "a / b" -> "a--b"


def render(cache, scope, cats, groups, order, assigned, args) -> str:
    n = len(scope)
    event_name = cache.get("event_name") or args.event
    sample = (f"the {n} most-voted projects" if args.top else f"all {n} submitted projects")
    lines = [
        "# What the other teams built",
        "",
        f"A category map of {sample} from the "
        f"[{event_name}]({event_url(args.event)}), built from each team's "
        f"written summary on lablab.ai as fetched on {cache['fetched']}. Only the summaries "
        "were read; presentations and repositories were not reviewed. Community "
        "votes are shown for context. Winners were not announced at the time of "
        "writing. Categories were proposed and assigned by an LLM from the "
        "summaries, so boundaries are approximate; see [Method](#method).",
        "",
        "Contents: " + " · ".join(
            f"[{cats[k]['name']} ({len(groups[k])})](#{anchor(cats[k]['name'])})"
            for k in order if groups[k]
        ) + " · [Category definitions](#category-definitions) · [Method](#method)",
        "",
        "## Category definitions",
        "",
        "| Category | What it covers | Projects |",
        "|---|---|---|",
    ]
    for k in order:
        if groups[k]:
            lines.append(f"| [{cats[k]['name']}](#{anchor(cats[k]['name'])}) | "
                         f"{cats[k]['definition']} | {len(groups[k])} |")
    lines.append("")

    for k in order:
        if not groups[k]:
            continue
        lines += [f"## {cats[k]['name']}", "", f"{cats[k]['definition']}", ""]
        for s in groups[k]:
            ours = " **(ours)**" if args.ours and s["uid"] == args.ours else ""
            votes = f"{s['likes']} vote" + ("" if s["likes"] == 1 else "s")
            summary = one_line(s["shortDescription"] or s["description"])
            notable = assigned[s["uid"]].get("notable", "").strip()
            lines.append(f"- **[{s['title']}]({s['url']})** — {s['team']}{ours} · {votes}  ")
            lines.append(f"  {summary}  ")
            if notable:
                lines.append(f"  *Notable:* {notable}")
        lines.append("")

    lines += [
        "## Method",
        "",
        f"Submissions were pulled from lablab's public submissions API "
        f"(`/api/v4/submissions`, paged, then filtered to this event) by the "
        f"`{SKILL_PATH}` skill, whose script also renders this page. Each project's "
        f"description field, the same text shown on its lablab page, was the only "
        f"input. Projects were split into batches of {args.batch_size} and read by "
        "parallel Claude subagents in two passes: the first proposed categories "
        "from what each batch's agents actually do (the trading approach, not the "
        "asset class or tech stack), which were merged by hand into the list above; "
        "the second assigned every project to exactly one category and wrote the "
        "*Notable* line, grounded in the summary only.",
        "",
        "Caveats: summaries are marketing copy capped at 2,000 characters, so a "
        "project may do more or less than it claims. A project that combines "
        "several approaches sits under its primary one. Vote counts are community "
        "likes on lablab, not judging results.",
        "",
    ]
    return "\n".join(lines)


def one_line(text: str, limit: int = 220) -> str:
    t = re.sub(r"\s+", " ", text).strip()
    if len(t) <= limit:
        return t
    cut = t[:limit].rsplit(" ", 1)[0]
    return cut.rstrip(" ,;:—-") + "…"


# ----------------------------------------------------------------- main ----

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--event", default=DEFAULT_EVENT,
                        help="hackathon slug from the lablab.ai URL")
    sub = p.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fetch", parents=[common], help="download all submissions to logs/")
    f.add_argument("--allow-mismatch", action="store_true",
                   help="write even if the count differs from live-stats")
    f.set_defaults(fn=fetch)

    b = sub.add_parser("batch", parents=[common], help="write per-subagent input batches")
    b.add_argument("--top", type=int, default=0, help="only the N most-voted (0 = all)")
    b.add_argument("--size", type=int, default=20)
    b.add_argument("--out", required=True)
    b.set_defaults(fn=batch)

    d = sub.add_parser("build", parents=[common], help="render the markdown from assignments")
    d.add_argument("--taxonomy", required=True)
    d.add_argument("--assignments", required=True, help="dir of assign_*.json")
    d.add_argument("--top", type=int, default=0, help="scope: N most-voted (0 = all)")
    d.add_argument("--batch-size", type=int, default=20, help="for the Method note")
    d.add_argument("--ours", default=DEFAULT_OURS,
                   help="uid (team_slug/slug) of our own entry; '' for none")
    d.add_argument("--out", default="docs/HACKATHON_SUBMISSIONS.md")
    d.set_defaults(fn=build)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
