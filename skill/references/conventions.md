# KAGE Conventions

These are rules that govern how Claude operates KAGE. Treat them as **defaults you don't override without asking the user**. When in doubt, follow these.

This file ships with **default conventions** that match the standard KAGE setup. The user is expected to **add their own** as preferences emerge — that's how the skill compounds across sessions. When the user says "from now on do X" or "stop doing Y", **add it to this file before the session ends**.

---

## Cross-System Defaults

### 1. Route every request by half: knowledge → Obsidian, tasks → ClickUp

If it's a fact, person, entity detail, decision, or analysis — it goes to BUNSHIN in Obsidian. If it's something to do, ship, or track — it goes to GAMBATTE in ClickUp. If it's both (a decision that implies tasks), write the decision first, then wave-queue the tasks with a `bunshin_ref` back to the decision page.

### 2. Don't dual-write

Never capture the same content in both Obsidian AND ClickUp. Pick one. The bridge is **one URL**: a `BUNSHIN:` line in a ClickUp task description, OR a ClickUp task URL in an Obsidian note's frontmatter if the note is specifically about a task.

### 3. Obsidian is the fast-path; ClickUp is the coherent snapshot

Mutate Obsidian freely during a session — it's private and fast. Ship changes to ClickUp in **waves** unless the update is atomic and visible-now (status flips, single urgent task, comment on an in-motion task). See `waves.md`.

### 4. Verify before acting on recalled state

Vault paths and ClickUp List IDs drift when the user restructures. Before mass writes or destructive ops on recalled identifiers, do a quick verify (Obsidian: `obsidian.read(path).exists`; ClickUp: `clickup.get_task(task_id)`). If stale, search by name and update the skill reference before proceeding.

---

## Obsidian (BUNSHIN) Defaults

### 5. Tasks are NEVER stored in Obsidian

Tasks live in ClickUp. Period. Obsidian notes can *reference* a ClickUp task (via URL or frontmatter) but the canonical task state is in ClickUp. Do not maintain a parallel todo list in an Obsidian note.

Exception: a "followups" section in a journal entry is fine — those are captures that will be wave-queued into ClickUp at the next flush, not a permanent todo list.

### 6. The vault is a wiki, not a file dump (Karpathy pattern)

Every ingest, query, or analysis compounds the wiki:

- Raw sources under `raw/`
- Summary pages that cite raw sources
- Entity pages updated when a source mentions them
- `index.md` at the root, cataloged by category
- `log.md` at the root, append-only with `## [YYYY-MM-DD] <kind> | <title>` entries

See `karpathy-llm-wiki.md` for the full methodology. This is the doctrine — not optional.

### 7. Frontmatter schema (minimal but consistent)

Every note gets YAML frontmatter:

```yaml
---
type: entity | source | decision | journal | analysis | concept | source-summary
date: YYYY-MM-DD        # when this note is about, not when it was written
tags: [tag1, tag2]
source: raw/<slug>      # for source-summaries, the raw file
---
```

Don't invent new `type` values without a reason. Consistency enables Dataview queries.

### 8. Wikilinks by filename stem, not path

`[[First Last]]` resolves to whatever file is named `First Last.md` anywhere in the vault. If two notes share a filename, Obsidian picks one — avoid duplicates. For disambiguation, parenthetical: `First Last (Org).md`.

### 9. Journal entries go in today's note (one file per day)

Path: `Journal/YYYY/MM - Month/DD - Weekday.md`. Multiple sections inside separated by `## <section header>`. `obsidian.ensure_today_journal()` creates the stub.

### 10. Don't rewrite a note's body to record a status — append

When a page needs a status update (a decision got revisited, a claim changed), append a new section with a dated header (`## Update — YYYY-MM-DD`). Don't modify the earlier body — it preserves history and makes diffs legible.

---

## ClickUp (GAMBATTE) Defaults

### 11. One task = one ClickUp row

Never inline bulleted to-do lists in a task description. Every actionable item is its own ClickUp task. Views, filters, assignments, and time-tracking only work on actual tasks.

### 12. Priority is for this week, not ever

- **Must (Urgent / priority 1)** — has to ship this week
- **Should (High / priority 2)** — important this week
- **Could (Low / priority 4)** — nice-to-have

Re-prioritize at the start of each week. Don't let Musts pile up across months.

### 13. Status is lowercase: `to do`, `in progress`, `blocked`, `complete`

ClickUp's default statuses are lowercase; `"Complete"` ≠ `"complete"`. If a List doesn't have `blocked` as a Status, fall back to a `blocked` tag.

### 14. Never delete — archive

`archived: true` keeps the task searchable. `DELETE /task/...` is only for tasks created in error.

### 15. Don't auto-create Spaces or Lists

The manifest routes every task to an existing List. Silent new Spaces/Lists break saved views and dashboards. If a domain is genuinely new, ask before creating.

### 16. Comments for status notes, not body rewrites

When a task has been in motion and needs a progress note, add a **comment** (`clickup.add_comment(...)`) instead of rewriting the description. Reads cleanly as history.

### 17. Titles are imperative + concrete

- Good: "Send <person> the <doc>", "Ship <feature>", "Update <thing>"
- Bad: "<person> stuff", "<thing>", "things"

### 18. Bounty board is a view, not a structure

The flat cross-Space Musts table is rendered on demand via `clickup.list_musts()` + a Markdown emit. Never persist the bounty board as a saved ClickUp view that reshapes the canonical hierarchy. Tree stays canonical; flat table is query-only.

### 19. Daily journal stays in Obsidian

ClickUp doesn't have a natural daily journal pattern. Journal entries live in Obsidian at `Journal/...`. If the user wants ClickUp-side journaling for team visibility later, add a folderless `Journal` List with one task per day — but this is not the default.

---

## Waves Defaults

### 20. Default multi-item captures to a wave

If the user is listing 3+ task-shaped things, queue them (`waves.queue_op(...)`) rather than immediately calling `clickup.add_task()`. Confirm with the user before flushing. See `waves.md`.

### 21. Status changes are never waved

A status change (`to do → in progress → blocked → complete`) is atomic truth and visible to collaborators; ship immediately via `clickup.update_task_status(...)`.

### 22. Surface the queue before flushing

Always show `waves.list_pending()` before `waves.flush_wave()`. The user controls the checkpoint.

### 23. Don't auto-retry failed ops

A failed op stays in the applied log with `status=error` and does NOT auto-retry. If the user wants to retry, they re-queue explicitly.

---

## Operating Style

### 24. Run it, don't just show the command

When the user asks for something operational Claude can do, **do it**. If Claude must show a command (for the user to run on a different machine or for documentation), use **full absolute paths** so they can copy-paste from anywhere.

### 25. New conventions get written here

If the user introduces a convention mid-session ("from now on do X", "stop doing Y", "I prefer Z"), **add it to this file before the session ends**. The whole point of this skill is durable improvement across sessions. Don't rely on conversational memory — codify it here.

### 26. New entities, people, or projects trigger reference updates

When you encounter a new entity that doesn't have an Obsidian page, a new ClickUp List that's not in `manifest.json`, or a new workflow pattern — update the relevant reference file in this skill before the session ends.

---

## User-Specific Conventions

*(Add yours below as they come up. Examples of what tends to live here: domain-specific routing rules, naming patterns, hard "never do X" rules, sensitive data that should never be written anywhere, preferred section headers, time-of-day patterns, etc.)*

<!-- Begin user-specific conventions -->

<!-- End user-specific conventions -->
