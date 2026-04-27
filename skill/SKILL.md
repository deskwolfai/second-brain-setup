---
name: kage
description: Operate the KAGE second brain end-to-end — BUNSHIN (knowledge) in an Obsidian vault plus GAMBATTE (tasks, projects, milestones) in ClickUp. One skill, two backends. Routes every request to the right side, owns the wiki-style maintenance pattern for Obsidian (Karpathy LLM-wiki methodology), and batches ClickUp writes into "waves" so collaborators don't see half-done state. Trigger aggressively on KAGE, BUNSHIN, GAMBATTE, "what's on my plate", "bounty board", "add a task", "log this", "file this", "update the wiki", "ingest this source", journal entries, decisions, or any work that would naturally live in a second brain. Trigger even when specific systems aren't named — if the intent is "capture or recall something durable" or "make this workspace operate KAGE", this skill is the operator. ClickUp GAMBATTE is the source of truth for active work; Obsidian BUNSHIN is the source of truth for knowledge.
---

# KAGE Operating Manual (Obsidian + ClickUp)

KAGE is a Claude-driven second brain. Two backends, one skill:

- **BUNSHIN** (knowledge) → Obsidian vault. Path from `$BUNSHIN_VAULT` env var.
- **GAMBATTE** (tasks / projects / milestones) → ClickUp workspace. Credentials from `$CLICKUP_API_KEY` + `$CLICKUP_TEAM_ID`, or this skill's `.env`.

**Read this whole file once at trigger time. Then act.**

## The 60-Second Mental Model

**CQRS split:** reads and writes for knowledge vs tasks run in different places for different reasons.

| Side | Lives in | Why it lives there | Primary helper |
|---|---|---|---|
| BUNSHIN (knowledge — entities, people, decisions, references) | Obsidian vault | Filesystem speed, Claude-native markdown, offline, graph view, wikilinks | `scripts/obsidian.py` |
| GAMBATTE (tasks, projects, milestones) | ClickUp workspace | Team visibility, mobile, PM features (priorities, statuses, assignees, time tracking), ClickUp Brain | `scripts/waves.py` (batched) + `scripts/clickup.py` (immediate) |

**Obsidian is where you read; ClickUp is where work ships.** The user works in Obsidian (fast, private, Claude-driven); collaborators watch ClickUp. The skill's job is to keep the two in sync without making ClickUp chatty or making Obsidian stale.

**Karpathy LLM-wiki pattern:** BUNSHIN is maintained as a living wiki, not a dump of raw notes. Every time a source comes in — a conversation, a document, a decision, a transcript — Claude reads it, discusses takeaways, writes a summary page, **updates the index, refreshes relevant entity pages, logs the ingest**. The wiki compounds. See `references/karpathy-llm-wiki.md` for the full methodology.

**Waves:** task writes to ClickUp come in two speeds. "As we go" = immediate (status flips, urgent single task creation, quick comments) — use `clickup.py` directly. "In waves" = batched (bulk captures, planning dumps, BUNSHIN→GAMBATTE sync) — queue via `waves.py`, flush at a checkpoint. See `references/waves.md`. The default for multi-item captures is **always a wave**.

## Operating Doctrine — WAT + Three Philosophies

KAGE is built on four ideas. Every workflow below assumes these. The full deep-dive lives at `<kage-repo>/docs/wat-framework.md` and `<kage-repo>/docs/philosophies.md`; this section is the skill-internal restatement so the skill is self-contained.

### The WAT Framework

WAT (Workflows, Agents, Tools) separates concerns: probabilistic AI handles reasoning, deterministic code handles execution.

| WAT Layer | In KAGE |
|---|---|
| **Workflows** (instructions) | The "Common Workflows" recipes below + `references/karpathy-llm-wiki.md` + `references/waves.md` |
| **Agents** (decision-maker) | Claude reading this SKILL.md, routing BUNSHIN vs GAMBATTE |
| **Tools** (execution) | `scripts/obsidian.py`, `scripts/clickup.py`, `scripts/waves.py` |

When AI handles every step directly, accuracy compounds badly — five steps at 90% accuracy lands at 59%. The skill leans on helpers because vault writes, ClickUp calls, and wave flushes are deterministic. Claude orchestrates; the scripts execute.

### Philosophy 1 — Bottom Up for Understanding, Top Down for Speed

Never automate what you don't understand. In KAGE this is **the Karpathy LLM-wiki pattern itself**: read the source, discuss takeaways, then write the summary. Don't dump raw text and call it a wiki. Understanding earns the right to compound.

In practice:
- Don't file an ingest you didn't actually read.
- Don't flush a 20-task wave whose intent you can't summarize in one sentence.
- On a search miss, say so and offer to file — don't fabricate.

### Philosophy 2 — The Flywheel

Every output is the next system's input. KAGE's flywheel:

```
Source → BUNSHIN ingest (raw + summary + entity update + log)
       → surfaces during a future query
       → grounds a decision or new task in GAMBATTE
       → completed task → comment / result
       → result filed back as wiki page (Workflow 8)
       → becomes a source for the next ingest
```

Manual gaps in this loop are **flywheel opportunities** — flag them.

### Philosophy 3 — Clean Separation, Zero Entanglement

The **CQRS split** is this philosophy in action. BUNSHIN owns reads, GAMBATTE owns writes. They share URIs as a bridge, never schema. **Don't dual-write** — putting a task into both sides re-tangles them.

Inside the skill itself, dependencies flow one direction:
- `obsidian.py` does not import `clickup.py`.
- `waves.py` depends on `clickup.py` (batched layer above immediate writes); the dependency never reverses.

Bridge with a URL, not a function call.

## Connection and Helpers

### Obsidian (BUNSHIN)

Vault path comes from `$BUNSHIN_VAULT`. It's just markdown files on disk. No daemon, no API. The bundled `scripts/obsidian.py` helper provides clean primitives (read/write/append/search/wikilink-extract, today's journal) with frontmatter handling baked in.

```bash
python ~/.claude/skills/kage/scripts/obsidian.py whoami
python ~/.claude/skills/kage/scripts/obsidian.py search "<term>"
python ~/.claude/skills/kage/scripts/obsidian.py read "Connections/<name>"
python ~/.claude/skills/kage/scripts/obsidian.py today
python ~/.claude/skills/kage/scripts/obsidian.py link "Entities/<slug>/index"
```

```python
import sys, os
sys.path.insert(0, os.path.expanduser("~/.claude/skills/kage/scripts"))
import obsidian

note = obsidian.read("Connections/<name>")           # {frontmatter, body, exists, ...}
obsidian.append("Entities/<slug>/index",
                "\n## Status — <date>\n\n<content>\n")
obsidian.create("Decisions/<date> <slug>",
                body="...", frontmatter={"type": "decision", "date": "<date>"})
hits = obsidian.search("<term>")                     # ranked matches
uri  = obsidian.obsidian_uri("Connections/<name>")   # obsidian:// link for ClickUp refs
```

### ClickUp (GAMBATTE)

GAMBATTE structures tasks as **`(space, list)` routes** — Spaces are top-level domains (per-business, per-project, per-life-area), Lists are categories within a Space. The skill reads this structure from `manifest.json` at the skill root (overridable via `$CLICKUP_MANIFEST`). The user generates this manifest during bootstrap; see `<kage-repo>/docs/clickup-setup.md` for the structure.

A common shape (yours may differ):

| Space | Lists |
|---|---|
| **<Business / Project Name>** | ADMIN, FULFILLMENT, MARKETING, SALES, ACCOUNTS, etc. |
| **Personal** | Health, Finance, People, etc. |
| **Inbox** | Quick Capture |

Route a task via `(space, list_name)`. The skill resolves to the correct `list_id` via the manifest.

### ClickUp — immediate writes

Credentials come from `CLICKUP_API_KEY` + `CLICKUP_TEAM_ID` — process env > skill-local `.env`. Helper at `scripts/clickup.py` exposes: `whoami`, `teams`, `search`, `list_id_in(space, list)`, `add_task`, `update_task_status`, `add_comment`, `list_musts` (bounty board across all Spaces), `build_manifest`.

```python
import sys, os
sys.path.insert(0, os.path.expanduser("~/.claude/skills/kage/scripts"))
import clickup

# Immediate: use for status flips, single urgent adds, comments on in-motion tasks
clickup.update_task_status(task_id, "in progress")
clickup.add_comment(task_id, "Blocked by <reason> — <date>.")
```

### ClickUp (GAMBATTE) — wave-batched writes

```python
import sys, os
sys.path.insert(0, os.path.expanduser("~/.claude/skills/kage/scripts"))
import waves

# Queue ops locally — nothing hits ClickUp yet
waves.queue_op("create_task", name="<task title>",
               space="<Space Name>", list_name="<List Name>", priority="Must",
               bunshin_ref=obsidian.obsidian_uri("Entities/<slug>/index"))
waves.queue_op("update_task_status", task_id="abc123", status="complete")

# Flush when the wave is coherent (end of session, after a planning pass, etc.)
result = waves.flush_wave()   # {"applied": N, "failed": 0, "wave_file": "..."}
```

`waves.py` persists pending ops to `<vault>/.bunshin/waves/pending.jsonl` and applied ops to `.bunshin/waves/applied/wave-<ts>.jsonl`. The queue survives session boundaries — captures in one session can be flushed in another, nothing is lost.

## When to Read KAGE

Proactively, not just when explicitly asked:

- **User mentions a person by name** → search Obsidian under `Connections/` (or wherever the user's vault keeps people).
- **User references an entity, project, or "what we decided"** → search the vault (title match first, then fulltext) before guessing.
- **User mentions "what's on my plate", "bounty board", or priorities** → `clickup.list_musts()` and emit a flat table.
- **User says "did I already do X"** → `clickup.search("X")` + `obsidian.search("X")`. Both.
- **Starting a session and user references an entity/project** → pull the BUNSHIN entity page AND any open tasks (`list_musts(space=...)`) before reasoning.
- **User is about to make a decision that depends on past context** → read the relevant Obsidian page first. Don't fabricate.

If the search comes up empty, say so and offer to file a new note (or task, if it's active work).

## When to Write to KAGE

### Write to BUNSHIN (Obsidian) when

- You learn a **durable fact** about a person, entity, project, or relationship.
- The user makes a **decision** worth preserving → create a `Decisions/YYYY-MM-DD <slug>.md` with context, options considered, the call.
- A **source** comes in (article, transcript, PDF, meeting notes) → file the raw source under `raw/`, then write a summary page, update relevant entity pages, add a log entry. This is the Karpathy ingest loop — see `references/karpathy-llm-wiki.md`.
- The user introduces a new **convention** or **preference** → add it to `references/conventions.md` in this skill AND (if domain-specific) to the relevant BUNSHIN page.
- An analysis or answer you produced is **worth filing back** → file as its own wiki page under the right folder.

### Write to GAMBATTE (ClickUp) when

- A **new task** appears. Ask: immediate (urgent, single) or batched (part of a bigger capture)?
  - Immediate → `clickup.add_task(...)`.
  - Batched → `waves.queue_op("create_task", ...)`, then flush when the capture is done.
- A **status changes** (to do → in progress → blocked → complete) → `clickup.update_task_status(...)` immediately. No wave needed — status is atomic.
- A **comment / status note** belongs on a task in motion → `clickup.add_comment(...)` (immediate) or queue as `add_comment` op in a wave if multiple tasks are being updated together.
- A **project or milestone** is being set up (new Space, new List, milestone-as-task) → wave-queue it. **Never auto-create Spaces or Lists without asking** — it can break saved views.

**Don't dual-write.** Don't capture the same task in Obsidian AND queue it to ClickUp — pick one. Knowledge → Obsidian. Active work → ClickUp. Bridge them with a URL.

## Common Workflows

### Workflow 1 — Ingest a source (Karpathy pattern)

A new article/transcript/doc/meeting notes comes in.

1. Save the raw source under `<vault>/raw/<slug>.md` or `<vault>/raw/<slug>.pdf`. Keep it immutable from now on.
2. Discuss key takeaways with the user (2-3 sentences, not a book report).
3. Write a **summary page** under the right topic folder with:
   - YAML frontmatter: `type: source`, `date: YYYY-MM-DD`, `raw: raw/<slug>`, `entities: [...]`.
   - Body: key claims, quotes with context, what this changes about the synthesis.
4. **Update affected entity pages** — if the source names a person, project, or product that already has a page, add a section citing the source. If not, decide with the user whether it deserves one.
5. **Append to `log.md`** at vault root: `## [YYYY-MM-DD] ingest | <source title>` + one line of why it mattered.
6. **Update `index.md`** at vault root: add the new page under the right category.

### Workflow 2 — Add a task (one-off, urgent)

1. Resolve Space (the domain — business, project, life area). Ask if ambiguous.
2. Resolve List (the category — ADMIN, FULFILLMENT, etc.).
3. Resolve priority (Must / Should / Could → maps to ClickUp priority enum 1/2/4).
4. Call `clickup.add_task(...)` directly. Title imperative + concrete; description explains why/scope/blockers.
5. If a BUNSHIN page grounds this task, pass `bunshin_ref=obsidian.obsidian_uri("path/to/note")`.

### Workflow 3 — Capture a wave (bulk tasks from a planning pass or brain dump)

1. As each item is named, call `waves.queue_op("create_task", ...)` — nothing hits ClickUp yet.
2. When the capture feels coherent, show the pending queue: `waves.list_pending()`.
3. Confirm: "ready to flush this wave?" Then `waves.flush_wave()`.
4. Report the result: X applied, Y failed, wave file location.

If there's a long break between capture and flush, the queue persists at `.bunshin/waves/pending.jsonl`. Ask before flushing if the queue is stale (>24h old).

### Workflow 4 — Bounty board (flat cross-Space Musts table)

1. `clickup.list_musts()` — every open Urgent task across all Spaces.
2. Emit a flat Markdown table: Space | List | Task | Status | Assignee.
3. Default sort: by Space, then List. Skip Coulds unless asked.
4. Tree stays canonical — the flat table is a **view**, never a restructure.

### Workflow 5 — Update an in-motion task

1. Find the task: `clickup.search("<term>")`.
2. Status change: `clickup.update_task_status(task_id, "blocked" | "in progress" | "complete")` — immediate.
3. Context note: `clickup.add_comment(task_id, "<note>")`. Prefer comments over body rewrites so history reads cleanly.
4. **Never delete — archive.** Closed tasks stay searchable.

### Workflow 6 — Look up a person, entity, or decision

1. `obsidian.search("<term>")` (BUNSHIN knowledge, fast).
2. `clickup.search("<term>")` (open GAMBATTE tasks tied to them).
3. Surface relevant pieces, not entire pages. Return the Obsidian URI for in-place open: `obsidian.obsidian_uri(path)`.

### Workflow 7 — Today's journal

1. `obsidian.ensure_today_journal()` — idempotent; creates `Journal/YYYY/MM - Month/DD - Weekday.md` if missing.
2. Read current content.
3. `obsidian.append(path, "\n## <section header>\n\n<content>\n")` — preserve existing sections.

Journal entries are BUNSHIN content, not GAMBATTE. They're the timeline, not the task queue.

### Workflow 8 — File an analysis back into the wiki

The user just asked for a deep comparison, competitive analysis, or synthesis. The answer is valuable — don't let it disappear into chat.

1. Ask: "want me to file this as a wiki page?"
2. If yes: pick the right folder (`Entities/<slug>/Analysis/`, `Strategy/`, `Decisions/`).
3. `obsidian.create(path, body=the_analysis, frontmatter={"type":"analysis","date":today})`.
4. Update `index.md` and `log.md`.

This is the **compound** part of the pattern — the wiki grows from queries too, not just ingests.

### Workflow 9 — Lint / health check (occasional)

1. Find orphan pages (no inbound wikilinks).
2. Find contradictions: pages with conflicting claims about the same entity.
3. Find stale claims: pages not updated in >6 months that assert time-sensitive facts.
4. Find missing cross-references: a source page mentions X but doesn't link to X's entity page.
5. Emit a lint report as a temporary page under `raw/lint/<date>.md`. Ask which items to fix this pass.

### Workflow 10 — First-time bootstrap

This workflow runs from the kage repo (one level above the installed skill). See `<kage-repo>/CLAUDE.md` for the canonical bootstrap steps. Trigger phrases: "set me up", "bootstrap KAGE", "install KAGE", "I just cloned this".

The skill itself can re-run bootstrap idempotently if the user adds a new ClickUp Space or rotates their token — both are non-destructive operations that update the manifest or `.env`.

## Critical Gotchas

### Obsidian

1. **Filenames can't contain `/ \ : * ? " < > |`.** The `obsidian.py` helper sanitizes these to `_`. Hand-writing `Path.write_text(...)` bypasses this and silently fails on Windows.
2. **Frontmatter must be `---` delimited and YAML-ish.** The helper renders keys/values safely. Hand-writing means escaping colons and quotes in values.
3. **Wikilinks resolve by filename stem, not path.** `[[First Last]]` resolves to whatever file in the vault has `First Last.md` as its filename — regardless of folder. Avoid duplicate filenames.
4. **Obsidian ignores folders starting with `.`** — which is why the waves queue lives at `.bunshin/waves/`. Invisible in the file browser but fully accessible via filesystem.
5. **Don't trust stdout for em-dashes on Windows console** — terminal `cp1252` will print `?` or `�`. The vault stores UTF-8 correctly.

### ClickUp

1. **No `Bearer` prefix on the Authorization header.** Send the literal `pk_...` token. Notion habit will 401 you.
2. **Priority is an integer enum** (1=Urgent/Must, 2=High/Should, 4=Low/Could; 3 is unused). The helper maps strings; raw callers must send ints.
3. **Status names are lowercase** (`to do`, `in progress`, `complete`). `"To Do"` won't match.
4. **"Workspace" in UI = "Team" in API.** `team_id` and workspace ID are the same thing.
5. **Don't auto-create Spaces or Lists.** The manifest routes tasks to existing Lists. New silent Spaces/Lists break saved views — ask first.
6. **Never delete — archive.** Closed tasks stay searchable. Delete only for tasks created in error.
7. **Rate limit ~100 req/min.** The `clickup.py` helper throttles to ~92/min. `waves.py` batches sequentially, so wave flushes are throttled automatically.

### Waves

1. **Pending ops persist across sessions.** If you queue 10 items and the session ends without a flush, they're still there next session. Check `waves.list_pending()` on boot if a capture might be stale.
2. **A failed op stays applied (with status=error) — it doesn't retry automatically.** Failures are visible in the applied log; the user decides whether to re-queue. Don't silently re-queue without asking.
3. **`dry_run=True` previews without writing and without draining pending.** Use before a big flush to sanity-check the batch.

## What's in the Reference Files

- `references/karpathy-llm-wiki.md` — **The LLM-Wiki methodology (Karpathy).** Read before any non-trivial ingest, lint, or wiki design decision.
- `references/waves.md` — When to write immediately vs queue in a wave, the wave lifecycle, idempotency rules, and the exact envelope of each op.
- `references/conventions.md` — User's hard preferences. **Update this file whenever a new preference comes up.** Starts mostly empty for a fresh install.
- `references/obsidian-vault-layout.md` — Recommended vault folder conventions (where Connections go, how Entities are structured, the journal path, the raw/ and assets/ directories). The user can override; this is a starting point.
- `references/clickup-api-quirks.md` — ClickUp's specific gotchas (auth, priority enum, pagination, status case, team/workspace naming).

## How This Skill Should Feel

A fresh Claude session should boot cold and **act in one or two turns**. If you find yourself rediscovering where Connections live, hand-writing a ClickUp request body, or debating whether to write immediately or queue — stop, open the reference. The whole reason this skill exists is so the user doesn't pay to teach the same lesson twice.

When you discover something new — a new convention the user mentions in passing, a new workflow pattern, a fresh gotcha — **update the relevant reference file in this skill before the session ends**. That's how the skill compounds. Treat every session as an opportunity to leave the skill sharper than you found it.

BUNSHIN compounds through the Karpathy wiki pattern. The skill compounds through you updating it. GAMBATTE stays coherent through waves. All three loops are what turn KAGE from a pile of notes into a real second brain.

You are operating someone's brain. Be careful, be fast, and don't let anything important leak out the bottom.
