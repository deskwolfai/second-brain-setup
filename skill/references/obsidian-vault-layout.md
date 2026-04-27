# BUNSHIN — Obsidian Vault Layout

This is the **recommended** vault layout for KAGE. The user can deviate — KAGE doesn't enforce structure beyond the conventions in `conventions.md` (frontmatter shape, journal path, raw/ folder for sources). Treat the layout below as a strong default, not a hard requirement.

## Vault Location

The vault path is read from `BUNSHIN_VAULT` environment variable. If unset, Obsidian-side helper functions raise an error — KAGE's ClickUp half still works.

The vault name is whatever folder name the user picked. Obsidian URI format: `obsidian://open?vault=<vault_name>&file=<path>`. The `obsidian.obsidian_uri()` helper builds these.

## Recommended Top-Level Structure

```
<vault>/
├── index.md                    # Karpathy wiki index — Claude maintains
├── log.md                      # append-only ingest/query/lint/decision log
├── Connections/                # people (one .md per person)
│   ├── Clients/
│   ├── Team/
│   ├── Advisors/
│   └── Family/
├── Entities/                   # businesses, products, orgs (each its own folder)
│   └── <Name>/
│       ├── index.md
│       ├── Strategy.md
│       ├── Brand.md
│       └── Context Docs/
├── Projects/                   # multi-thread efforts that span entities
│   └── <Project Name>/
│       └── index.md
├── Decisions/                  # timestamped decision records
│   └── YYYY-MM-DD <slug>.md
├── Concepts/                   # cross-cutting domain concepts
├── Strategy References/        # books, frameworks, canonical sources
├── Journal/                    # day notes
│   └── YYYY/MM - Month/DD - Weekday.md
├── raw/                        # immutable source documents (per Karpathy)
│   ├── assets/
│   └── lint/
└── .bunshin/                   # skill state (hidden from Obsidian browser)
    └── waves/
        ├── pending.jsonl
        └── applied/wave-<ts>.jsonl
```

The dotfolder at the bottom is hidden from Obsidian's file browser but fully accessible via the filesystem and the helper.

## Journal

Path: `Journal/YYYY/MM - Month/DD - Weekday.md`

Examples:
- `Journal/2026/04 - April/23 - Thursday.md`
- `Journal/2026/04 - April/07 - Tuesday.md`

One file per day. Multiple sections inside separated by `## <section header>` (e.g. `## Bootup`, `## Evening update`, `## Notes`). `obsidian.ensure_today_journal()` creates the day file idempotently with a stub header.

## Connections (People)

Path: `Connections/<First Last>.md` or `Connections/<category>/<First Last>.md`

Common sub-categories:
- `Connections/Clients/`
- `Connections/Team/`
- `Connections/Advisors/`
- `Connections/Family/`

Frontmatter:
```yaml
---
type: entity
kind: person
roles: [founder, advisor, client, ...]
entities: [<Org Name>, <Org Name>]
last_interaction: YYYY-MM-DD
---
```

## Entities (Businesses / Orgs / Products)

Path: `Entities/<Name>/...`

Recommended children:
- `index.md` — main page (what it is, current state, one-line pitch)
- `Strategy.md` — vision, positioning, plan
- `Brand.md` — voice, identity, marketing
- `Context Docs/` — misc reference, files, exports

Frontmatter for an entity root:
```yaml
---
type: entity
kind: business | product | org
status: active | paused | closed
started: YYYY-MM-DD
clickup_space: <Space Name>      # so the skill knows to route tasks here
---
```

## Projects

Path: `Projects/<Name>/...`

Projects are **not entities** — they're multi-thread efforts that span or support an entity (e.g. a product launch, a migration, a campaign). They have their own folder and `index.md`. Pick sub-folders as needed; no fixed structure.

## Decisions

Path: `Decisions/YYYY-MM-DD <slug>.md`

Frontmatter:
```yaml
---
type: decision
date: YYYY-MM-DD
affects: [<entity>, <project>]
supersedes: "Decisions/<earlier-decision>.md"   # optional
---
```

Body structure (recommended):
1. **Context** — what was going on
2. **Options considered** — bullets
3. **Decision** — one sentence
4. **Reason** — why this one
5. **Consequences** — what changes
6. **Follow-ups** — bullets (often become waved ClickUp tasks)

## Strategy References

Path: `Strategy References/<Book/Framework>.md`

For canonical strategy/marketing/operational references cited across multiple pages.

## Concepts

Domain concepts that belong to more than one entity — frameworks, heuristics, principles. Filename should be noun-y: `Concepts/CQRS.md`, `Concepts/Loss Aversion.md`.

## Raw Sources

Path: `raw/<slug>.md` (or `.pdf`, `.html`, etc.)

**Immutable.** Once filed, don't edit a raw source — if a new version comes in, file as `raw/<slug> v2.md` and note the supersession in the summary.

Images that belong to a raw source go in `raw/assets/<slug>/<image>.png` so they stay co-located.

## index.md (Wiki Index)

Per Karpathy: content-oriented catalog of everything in the wiki. Organized by category (entities, concepts, sources, decisions, journals); each entry = one line linking to the page with a one-line summary.

Update on every ingest. At medium scale (hundreds of pages) this beats embedding RAG.

## log.md (Chronological Log)

Append-only `## [YYYY-MM-DD] <kind> | <title>` + one-line summary. Kinds:
- `ingest` — new source added
- `query` — non-trivial question answered with wiki synthesis
- `analysis` — deep synthesis filed back as its own page
- `decision` — new decision recorded
- `lint` — health-check pass
- `migration` — structural change (rare)

Parseable with grep:
```bash
grep "^## \[" "<vault>/log.md" | tail -10
```

## Illegal Filename Characters

Windows + Obsidian disallow `/ \ : * ? " < > |` in filenames. The `obsidian.py` helper sanitizes these to `_` on create. Hand-crafting paths bypasses this and silently fails on Windows.

## Wikilink Resolution

- `[[First Last]]` → resolves by **filename stem** anywhere in the vault
- `[[First Last|short alias]]` → link with display alias
- `[[First Last#Heading]]` → deep link to a heading
- `[[First Last#Heading|alias]]` → deep link with alias

Obsidian picks the first match if two files share a stem. Avoid duplicates; if needed, disambiguate by parenthetical: `First Last (Org).md`.

## Frontmatter Type Taxonomy

Keep `type` values in a small, consistent set:

- `entity` — a person, business, product, org (use `kind:` to narrow)
- `source` — raw ingested source (in `raw/`)
- `source-summary` — a summary page that cites a raw source
- `decision` — in `Decisions/`
- `journal` — day notes in `Journal/`
- `analysis` — synthesis filed back into the wiki
- `concept` — a domain concept page

Avoid inventing new types ad-hoc — it breaks Dataview queries.

## Useful Obsidian Plugins

Optional but handy:

- **Dataview** — runs queries over frontmatter, generates dynamic tables.
- **Graph View** (core) — see the wiki's shape, find orphans.
- **Web Clipper** (browser extension) — convert articles to markdown in one click.
- **Marp** — markdown-based slide decks.

## Searching

Prefer the skill helpers:

- `obsidian.search("query")` — filename + fulltext, ranked, in the helper
- `obsidian.list_folder("path")` — browse a directory
- Plain `grep` (via the harness Grep tool) is fine for targeted searches

Obsidian's built-in search (Ctrl-O, Ctrl-Shift-F) is for the user when using the app directly.
