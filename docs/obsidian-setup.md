# Obsidian Setup for BUNSHIN

This is the optional half of KAGE. The ClickUp half (GAMBATTE) works without Obsidian — but if you want a knowledge base that compounds over time, set up an Obsidian vault.

## What Obsidian gives you

- **Filesystem-speed markdown.** Notes are just `.md` files on disk. No daemon, no API, no lock-in.
- **Wikilinks.** `[[Note Name]]` resolves anywhere in the vault. Build a personal Wikipedia.
- **Graph view.** See the shape of your knowledge — what's connected, what's an island.
- **Plugin ecosystem.** Dataview for queries, Web Clipper for ingest, Marp for slide decks.
- **Offline-first.** Works with no internet. Sync optional.
- **Free for personal use.** Paid sync if you want it; not required.

## Install Obsidian

1. Download from https://obsidian.md
2. Install (Mac/Windows/Linux/iOS/Android — all platforms supported).
3. Open Obsidian. On first launch, create a new vault or open an existing folder.

## Create your BUNSHIN vault

Pick a folder anywhere on disk. Common spots:

- `~/Documents/BUNSHIN/`
- `~/Notes/BUNSHIN/`
- Any folder synced via iCloud / Dropbox / OneDrive (Obsidian + cloud sync = poor man's Obsidian Sync).

In Obsidian: **Open another vault → Create new vault → pick the folder.**

The vault name is whatever folder name you picked. KAGE doesn't care — it reads the absolute path from `BUNSHIN_VAULT`.

## Wire BUNSHIN_VAULT

In `~/.claude/skills/kage/.env`:

```bash
BUNSHIN_VAULT=/absolute/path/to/your/vault
```

Use forward slashes even on Windows: `BUNSHIN_VAULT=C:/Users/yourname/Documents/BUNSHIN`.

Verify:

```bash
python ~/.claude/skills/kage/scripts/obsidian.py whoami
```

Expected: vault path + count of `.md` files.

## Recommended starting structure

You don't need to create folders upfront — Claude creates them as needed during ingest. But here's what KAGE expects to see eventually:

```
<vault>/
├── index.md                    # wiki index — Claude maintains
├── log.md                      # chronological event log — Claude maintains
├── Connections/                # people
├── Entities/                   # businesses, products, orgs
├── Projects/                   # multi-thread efforts
├── Decisions/                  # YYYY-MM-DD <slug>.md
├── Concepts/                   # cross-cutting ideas
├── Strategy References/        # books, frameworks, canonical sources
├── Journal/                    # day notes (Journal/YYYY/MM - Month/DD - Weekday.md)
├── raw/                        # immutable source documents
└── .bunshin/                   # skill state (waves queue, etc.)
```

The full layout reference is in `~/.claude/skills/kage/references/obsidian-vault-layout.md`.

You can deviate from this structure — KAGE only enforces a few rules:

- Journal entries go in `Journal/YYYY/MM - Month/DD - Weekday.md`.
- Raw sources go in `raw/`.
- Wave queue lives in `.bunshin/waves/` (hidden from Obsidian's file browser).

## Recommended plugins

In Obsidian: **Settings → Community plugins → Browse**. Install:

- **Dataview** — runs queries over frontmatter. Lets you generate dynamic tables ("show me all decisions from this month").
- **Templater** — optional. Note templates with variables. Useful for journal stubs.

Browser extension (separate install):

- **Obsidian Web Clipper** — clip web articles directly into your vault as markdown. Killer feature for ingest.

## Useful Obsidian settings

**Files & Links:**
- **Default location for new attachments** → set to `raw/assets/` (keeps images near their source files)
- **Use [[Wikilinks]]** → ON (enables `[[Note Name]]` syntax)
- **New link format** → "Shortest path when possible" (cleaner wikilinks)

**Editor:**
- **Spell check** → off for technical content (Markdown gets misflagged a lot)

**Hotkeys:**
- Bind a hotkey to "Download attachments for current file" — after web-clipping, hit the hotkey to download all images locally so they don't break if URLs go away.

## What KAGE writes to your vault

When triggered, the skill will:

- Read existing notes via `obsidian.read(...)`.
- Append to `index.md` and `log.md` as new content arrives.
- Create new notes under `Decisions/`, `Connections/`, `Entities/`, etc.
- Update entity pages when sources mention them.
- Maintain the Karpathy LLM-wiki pattern (see `~/.claude/skills/kage/references/karpathy-llm-wiki.md`).

It will **never**:

- Delete a note (KAGE always archives or appends, never destroys).
- Modify raw sources in `raw/` (those are immutable by convention).
- Touch `.obsidian/` (Obsidian's own config folder).

## Working with KAGE in Obsidian

The intended workflow:

1. **Open Claude on one screen, Obsidian on the other.** You talk to Claude; you watch the changes happen in Obsidian's file tree and graph view in real time.
2. **You curate sources and ask questions.** Claude does the bookkeeping — summary pages, entity updates, log entries, cross-references.
3. **Use Obsidian's graph view often.** It tells you what's connected and what's orphaned. Orphans are usually a Claude-error or a missing wiki link.
4. **Use Obsidian's search (Ctrl+Shift+F) when you want to read things directly.** When you want Claude to do something with what it finds, ask Claude — it has its own search via `obsidian.search()`.

## Skipping Obsidian

If you don't want to maintain a vault:

- Leave `BUNSHIN_VAULT` unset.
- The ClickUp half of KAGE works fine standalone.
- You won't have durable knowledge storage — every conversation with Claude starts cold. (Claude's memory + ClickUp task descriptions cover some of the gap, but not all of it.)

You can add Obsidian later. KAGE is designed so the vault can be set up retroactively without breaking anything.
