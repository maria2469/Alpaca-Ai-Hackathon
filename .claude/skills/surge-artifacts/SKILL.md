---
name: surge-artifacts
description: Design and publish standalone HTML pages — reports, explainers, demos, dashboards, mini-sites — to surge.sh at miroai-artifacts-<slug>.surge.sh. Use this whenever the user wants a web page published or shared via surge, asks for a public/shareable URL hosted outside claude.ai, mentions "surge", "surge.sh", or "miroai artifact", or asks to deploy/host a page they can send to teammates. When surge hosting is requested, this skill replaces the built-in Artifact tool flow entirely — do not publish to claude.ai artifacts in that case.
---

# Surge Artifacts

Publish designed, self-contained web pages to surge.sh under the `miroai-artifacts-*` namespace. This is the surge-hosted equivalent of a claude.ai artifact: you author a complete HTML page, deploy it with the surge CLI, and hand the user a stable public URL they can share.

The deliverable is the live URL. A page that exists only on disk is not done.

## Preflight

Run these checks before writing any page content, so a missing prerequisite surfaces immediately rather than after the design work:

1. **CLI installed**: `command -v surge`. If missing, tell the user to install it with `npm install -g surge` and stop there — do not install it yourself, and do NOT suggest `brew install surge`, which is an unrelated package.
2. **Authenticated**: `surge whoami`. If logged out, ask the user for a `SURGE_TOKEN` (they can get one by running `surge token` on any machine where they're logged in) and prefix it onto every surge command as an env var: `SURGE_TOKEN=<token> surge …`. That token flow is surge's intended auth path for agents and CI — do not walk the user through the interactive `surge login`.

## Publishing workflow

**Where pages live.** Each artifact gets its own directory at the repo root: `surge_artifacts/<slug>/`, with `index.html` as the entry point. This directory persists across sessions — that persistence is what makes redeploys to the same URL possible later, so never write the page to a temp/scratch directory. Make sure `surge_artifacts/` is listed in the repo's `.gitignore` (add it if it isn't) — published page sources are build output, not project code.

**Choosing the slug.** Short kebab-case derived from the page's topic (`clip-search-explainer`, `q3-detector-report`). The domain is always `miroai-artifacts-<slug>.surge.sh`. Before the first publish of a new slug, run `surge list` to see what's already deployed — both to avoid collisions and to notice when the user is actually asking you to update an existing page rather than create a new one. (Deploys under other prefixes, e.g. `surge-artifacts-*`, are older manual experiments — leave them alone, but check them too when hunting for a page the user wants updated.)

**Deploying.** Write a `CNAME` file containing the bare domain (no protocol) into the artifact directory, then deploy. The paths below are relative to the repo root, and the working directory can reset between shell calls in agent environments — so run both commands from the repo root in a single invocation, or use absolute paths:

```bash
echo "miroai-artifacts-<slug>.surge.sh" > surge_artifacts/<slug>/CNAME && \
surge ./surge_artifacts/<slug> miroai-artifacts-<slug>.surge.sh
```

The CNAME file makes the domain durable metadata of the directory itself, so any future session can redeploy without guessing the domain.

**Updating.** Edit the files in the existing `surge_artifacts/<slug>/` directory and run the same surge command — the URL stays stable, exactly like redeploying an artifact. Keep the same slug across updates; a new slug means a new, separate page.

**Verifying.** After every deploy, confirm the page is actually live (`curl -sI https://miroai-artifacts-<slug>.surge.sh` should return 200) before reporting the URL to the user.

**Lifecycle.** `surge list` enumerates all deployed projects. `surge <domain> teardown` removes one — it's destructive and immediate, so confirm with the user before tearing anything down.

**Privacy — read this before publishing.** Surge pages are public to anyone who has (or guesses) the URL from the instant of deploy; there is no default-private state like claude.ai artifacts have. Never publish secrets, credentials, internal data the user has flagged as sensitive, content that impersonates a real person or organization, or fabricated records presented as genuine. Just as important: internal infrastructure identifiers don't belong on a public page even when they're harmless-looking — S3 bucket names, storage paths, internal hostnames and dev domains, employee usernames embedded in paths. Pages about internal systems are fine; name the *concepts* ("the team's S3 encodings bucket") and point readers at the private docs (CLAUDE.md, the repo) for the literal values. Before every deploy, grep the page source for this kind of identifier. If the content is borderline, ask before deploying.

## Authoring the page

Unlike the Artifact tool, nothing wraps your file. You author the complete document:

- Full skeleton: `<!doctype html>`, `<html lang="en">`, `<head>` with `<meta charset="utf-8">`, `<meta name="viewport" content="width=device-width, initial-scale=1">`, and a concise `<title>`, then `<body>`. There is no injected CSS reset — include your own minimal one (`*, *::before, *::after { box-sizing: border-box }`, zero out default margins, `img { max-width: 100% }`).
- Give the page a favicon so the tab isn't blank. An inline emoji works well and needs no asset file:
  `<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📊</text></svg>">`
- **No CSP.** Surge serves plain static files, so webfonts (Google Fonts `<link>`), CDN scripts, and remote images all work — a real advantage over artifacts. Use it deliberately: a characterful webfont is often the cheapest big design win. Still prefer inlining CSS/JS for a single-page artifact; fewer moving parts, and the page keeps working if a CDN changes.
- **Multi-file deploys work.** Surge publishes the whole directory, so a page can split into several HTML files, local images, a shared stylesheet — use this when a single file would get unwieldy, and keep `index.html` as the front door.
- Wide content — tables, code blocks, diagrams — scrolls inside its own `overflow-x: auto` container; the page body never scrolls horizontally. Use relative units and flex/grid so the page holds together on a phone.

### Theming: two states, not three

There is no artifact viewer stamping `data-theme` attributes — the only theme signal is the visitor's OS via `prefers-color-scheme`. So the pattern is simple:

- Define the complete palette as custom-property tokens on `:root` (this is your light theme, or your base theme for a dark-first design).
- Redefine only the tokens inside `@media (prefers-color-scheme: dark)`.
- Style every component through the tokens; never give a color its only definition inside the media query, or it silently never applies in the other theme.
- `body` gets an explicit `background` from a token.

A design that deliberately commits to a single look (a neon arcade screen, a letterpress card) may skip the media query — but then paint the background and every color explicitly, as a choice rather than an omission. Whichever route, give the second theme the same care as the first: don't naively invert, keep contrast legible, make sure the accent works on both grounds.

## Design guidance

Approach this as the design lead at a small studio known for versatility: every page gets a visual identity pitched at the treatment the task actually calls for, with deliberate choices about palette, typography, and layout that are specific to the subject.

### Read the request first

Calibrate treatment, not whether to design. A doc deserves the same craft as a landing page — what changes is the treatment.

- **Utilitarian** (a plan, a memo, a report, a demo): polished — real typographic hierarchy, considered spacing, a proper palette — but not over-designed. Most pages do not need a flashy hero. Keep flourishes tasteful and limited.
- **Editorial** (a landing page, a game, an app or tool the user will keep or share): the client is paying for a distinctive point of view. Make opinionated calls and take one real aesthetic risk where it serves the work.

When unsure: a well-composed page is never the wrong answer; an over-designed visual identity sometimes is.

### Fundamentals for every page

**Honor what's already there.** Look for an existing design system first — CLAUDE.md, a tokens or theme file, existing component styles. When one exists, apply it. Precedence is always: the user's own words, then the project's existing system, then your choices.

**Ground it in the subject.** Pin one concrete subject, its audience, and the page's single job. The subject's own world — its materials, instruments, vernacular — is where distinctive choices come from. Build with real content throughout, never lorem.

**Pair typefaces.** Typography carries the page even when the page isn't about typography. With no CSP you can link webfonts directly — pick a characterful display face and a complementary body face rather than defaulting to system fonts (verify the `<link>` loads; a typo'd family name falls back silently). Keep running text near 65 characters wide; set a type scale and stay on it; give headings `text-wrap: balance`, body text room to breathe, uppercase labels a touch of letter-spacing, and `font-variant-numeric: tabular-nums` wherever digits line up in columns.

**Choose neutrals, don't default to them.** A pure mid-grey reads as unconsidered; a grey with a slight hue bias toward the page's accent reads as chosen. Pure white and near-black are fine grounds when they suit the subject — the point is that the neutral was picked, not inherited.

**Let layout do the spacing.** Lay out sibling groups with flex or grid and `gap`, not per-element margins that silently collapse or double. Watch selector specificity — it's easy to generate classes that cancel each other out (a `.section` fighting a `.cta` over spacing). Structure the cascade so it doesn't silently undo itself.

**Avoid the templated AI look.** AI-generated design clusters around a few looks: warm cream (#F4F1EA) with a serif display and terracotta accent; near-black with a lone acid-green or vermilion pop; broadsheet hairline rules with dense columns; a purple-to-blue gradient hero on white; Inter or Space Grotesk as the "safe" face; emoji as section markers; everything centered; `rounded-lg` everywhere; accent bars on rounded cards. Where the user pins down a visual direction, follow it exactly — their words always win, including when they ask for one of these looks. Where nothing is specified, don't spend that freedom on one of these defaults.

**Build cleanly.** Close every non-void element, double-quote attributes, give keyboard focus a visible state, respect `prefers-reduced-motion`. Visual bugs hide in the gap between source and output — overlapping elements, cascade collisions, silent font fallbacks. For generative or decorative graphics, reach for Canvas or WebGL rather than hand-authoring long SVG path data.

**Words are design material.** Write from the user's side of the screen — name things by what people recognize, not how the system is built. Active voice; a control says exactly what happens. Errors explain what went wrong and how to fix it. Specific beats clever.

**Structure is information.** Numbering, eyebrows, dividers, and labels should encode something true about the content, not decorate it. Numbered markers (01 / 02 / 03) are only appropriate when the content actually is a sequence.

**When it's a UI, not a document.** A dashboard or tool is scanned and operated, not read top-to-bottom, so the craft shifts from typography to information design. Surface the summary before the detail; encode state in form as well as number — a pill, a chip, a severity stripe. Semantic color (good / warning / critical) is separate from the accent hue and doesn't count as your accent. Give sparklines and charts the same care as type. What's interactive should look interactive.

### Process

Before writing code, sketch a short design plan — a compact token system:

- **Color**: the palette as 4–6 named hex values.
- **Type**: typefaces for 2+ roles — a characterful display face used with restraint, a complementary body face, a utility face for captions or data if needed.
- **Layout**: the layout concept in one or two sentences.

Then build, deriving every color and type decision from the plan.

For editorial requests, review the plan against the subject before building: if any part reads like the generic default you'd produce for any similar page, revise that part. The hero is a thesis — open with the most characteristic thing in the subject's world. Leverage motion deliberately: one orchestrated moment usually lands harder than scattered effects, and sometimes less is more. Match complexity to the vision — maximalist directions need elaborate execution; minimal directions need precision in spacing, type, and detail. Spend your boldness in one place and keep everything around it quiet.

## Wrapping up

Report to the user: the live URL first, then a sentence on what the page contains and where the source lives (`surge_artifacts/<slug>/`) so they know how to ask for updates later.
