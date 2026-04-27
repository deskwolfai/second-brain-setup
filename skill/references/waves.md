# Waves — Batched ClickUp Updates

## What a Wave Is

A **wave** is a batched checkpoint of ClickUp operations. Between waves, Claude mutates Obsidian (BUNSHIN) freely as a working draft. At a wave boundary, a coherent set of changes ships to ClickUp (GAMBATTE) as a single visible snapshot.

**Why this exists.** Obsidian is the user's fast-path — single-user, filesystem speed, Claude-native. ClickUp is the team's surface — mobile, dashboards, PM features, other humans watching. Shipping every tiny change to ClickUp creates chatty, half-baked state: collaborators see a task appear, then change name 30 seconds later, then get re-prioritized, then get a comment added. Waves collapse that noise into one coherent commit.

Think of it like Git vs. a shared network drive. You don't push every keystroke; you commit a coherent change.

## Two Speeds — Which to Use When

### Immediate writes (use `clickup.py` directly)

Go straight to ClickUp — no queue — when the action is:

| Signal | Why immediate |
|---|---|
| **Status change on an existing task** (`to do → in progress → blocked → complete`) | Status is atomic, reflects reality right now, someone may be about to work on it |
| **Single urgent task creation** | Waiting loses the point |
| **Comment on a task in motion** | Collaborators need the current note |
| **Assignee change** | Somebody is about to look for "their" tasks |
| **Re-prioritization of a single task that someone else is watching** | Stale priority misleads |

```python
clickup.update_task_status(task_id, "blocked")
clickup.add_task("<urgent task title>", priority="Must",
                 space="<Space Name>", list_name="<List Name>")
clickup.add_comment(task_id, "<status note>")
```

### Wave-queued writes (use `waves.py`)

Queue locally; ship as a wave when the capture is coherent.

| Signal | Why queued |
|---|---|
| **Bulk capture from a brain-dump or meeting** | Each item gets its own row in ClickUp, but showing up one at a time creates noise |
| **Weekly planning pass** | Collaborators should see the new week's plan as a single snapshot, not a live trickle |
| **BUNSHIN→GAMBATTE sync** (turning a decision or analysis into tasks) | Coherent story; flushes together with the BUNSHIN update |
| **Milestone / project structure changes** (new project → several initial Lists+tasks) | Team sees a new project "appear" fully formed |
| **Multi-task status sweep** ("we shipped Monday's 5 Musts — mark all complete") | One ClickUp notification storm vs five |

```python
waves.queue_op("create_task", name="<task 1>", space="<Space>", list_name="<List>",
               priority="Must", bunshin_ref=obsidian.obsidian_uri("<path>"))
waves.queue_op("create_task", name="<task 2>", space="<Space>", list_name="<List>",
               priority="Should")
waves.queue_op("update_task_status", task_id="abc123", status="complete")
waves.queue_op("add_comment", task_id="def456", text="<status note>")

result = waves.flush_wave()  # ships them all, atomically from collaborators' POV
```

## Wave Lifecycle

```
 ┌────────────────────┐
 │ Claude captures    │◀── user talks to Claude
 │ ops → pending.jsonl│
 └──────────┬─────────┘
            │  queue_op(...)
            ▼
 ┌────────────────────┐
 │ pending.jsonl      │◀── persists across sessions
 │ (vault/.bunshin/)  │
 └──────────┬─────────┘
            │  flush_wave()
            ▼
 ┌────────────────────┐         ┌──────────────────────────┐
 │ applied/wave-<ts>  │────────▶│ ClickUp gets all ops      │
 │   .jsonl (audit)   │         │ (throttled by clickup.py) │
 └────────────────────┘         └──────────────────────────┘
            │
            │  pending.jsonl now empty
            ▼
       next wave
```

**State locations:**

If `BUNSHIN_VAULT` is set:
- `<vault>/.bunshin/waves/pending.jsonl` — ops queued but not yet shipped. One op per line.
- `<vault>/.bunshin/waves/applied/wave-YYYYMMDDTHHMMSSZ.jsonl` — one file per flushed wave, preserved for audit.

If no Obsidian vault is configured, waves fall back to `<skill_root>/.waves/`.

The dotfolder under the vault is hidden from Obsidian's file browser but fully accessible via the filesystem.

## Op Envelope

Every queued op is a JSON line with a consistent shape:

```json
{
  "id": "ab12cd34",
  "ts": "<iso timestamp>",
  "op": "create_task",
  "args": { "name": "<task>", "priority": "Must", "space": "<Space>", "list_name": "<List>" },
  "status": "pending"
}
```

After `flush_wave()` the record gets `status`, `applied_at` / `failed_at`, and `result` (a trimmed version of the ClickUp response) or `error` fields, then moves into the wave file.

## Supported Ops

| op | Required args | What it does |
|---|---|---|
| `create_task` | `name` + one of `{space+list_name, project, pillar}` | Routes via `clickup.add_task(...)`; supports `priority`, `description`, `bunshin_ref`, `tags`, `status` |
| `update_task` | `task_id` + arbitrary `**fields` | Passes through to `clickup.update_task(task_id, **fields)` |
| `update_task_status` | `task_id`, `status` | Single-field status change |
| `add_comment` | `task_id`, `text` | Adds a comment (not a body rewrite) |
| `create_list` | `folder_id`, `name` | Creates a new List in a Folder. **Rare** — only for new milestones. Ask first. |

## Flushing — Rules of Thumb

1. **Default to flushing at the end of the capture.** If the user dumps 10 tasks and stops talking about them, flush before moving to a different topic. Don't let waves linger across topics.
2. **Always surface the queue before flushing.** Show `waves.list_pending()` and get a "yes flush" before writing to ClickUp. The user controls the checkpoint.
3. **Use `dry_run=True` when the batch is big** (>10 ops) or when the user is uncertain. It prints what would happen without touching ClickUp.
4. **Don't flush partial.** If one op in a wave fails validation pre-flight, fix it first. A half-flushed wave is the exact noise waves exist to prevent.
5. **Apply the `op_filter` only when draining a specific class** — e.g. `flush_wave(op_filter="update_task_status")` to sweep all status changes without shipping pending creates.
6. **Stale queues** (>24h old): ask the user if the queue is still accurate before flushing. Context shifts.

## Idempotency and Error Handling

- `create_task` is **not** idempotent on its own — two identical queue_op calls ship two tasks. The helper also doesn't dedupe against existing ClickUp tasks by name (too expensive). If the user says "add X" twice, ask whether to skip.
- `update_task_status` is naturally idempotent: setting a task to `complete` twice is the same state.
- **Failures stay in the applied log with `status=error`.** They do NOT auto-retry. This is deliberate — silent retries could re-ship half-baked state. If the user wants to retry, they queue explicitly.

## When NOT to Use Waves

- **Live debugging**: when the user is iterating on a single task's status ("no that's blocked, wait now it's in progress, wait actually complete"), don't wave-queue the confusion. Update immediately, each time.
- **Cross-team conversations mid-flight**: if someone is about to open a task right now, they need current state — write immediately.
- **Atomic status flips**: one `complete` is faster direct than through the wave machinery.

Waves are for **bulk, coherent snapshots**. Single atomic truth updates go direct.

## BUNSHIN ↔ GAMBATTE Pattern via Waves

The cleanest cross-vault pattern uses the wave as the bridge.

1. Work happens in BUNSHIN first — a meeting gets ingested, a decision gets documented, an analysis gets filed.
2. If the BUNSHIN change **implies tasks**, queue them as wave ops that include `bunshin_ref=obsidian.obsidian_uri(...)` pointing back.
3. Flush the wave as part of closing the BUNSHIN change. Collaborators now see the tasks, each linked to the Obsidian page that grounds them.
4. When a ClickUp task is worked, the team can click the `BUNSHIN:` header in the description to jump into the wiki context in Obsidian desktop.

This is the only sanctioned bridge between the two halves. Don't duplicate knowledge into ClickUp descriptions beyond a 1-2 line summary + the BUNSHIN link; don't duplicate task metadata into Obsidian frontmatter (other than a ClickUp URL if the note is specifically about that task).

## CLI Cheat Sheet

```bash
# Queue a task creation
python ~/.claude/skills/kage/scripts/waves.py queue create_task \
    --name "<task title>" \
    --space "<Space Name>" --list "<List Name>" --priority Must

# Queue a status update
python ~/.claude/skills/kage/scripts/waves.py queue update_task_status \
    --task_id abc123 --status complete

# See what's pending
python ~/.claude/skills/kage/scripts/waves.py pending

# Ship the wave (writes to ClickUp)
python ~/.claude/skills/kage/scripts/waves.py flush

# Preview without writing
python ~/.claude/skills/kage/scripts/waves.py flush --dry-run

# History
python ~/.claude/skills/kage/scripts/waves.py applied 5
```

## TL;DR

- **Atomic and visible-now → immediate** (`clickup.py`).
- **Batched and coherent → wave** (`waves.py`).
- **Queue survives sessions**, but stale queues warrant a review before flush.
- **Status changes are always immediate**; list creates are always waves (and always confirmed first).
- **The wave file is the audit log** — never edit it, just appended.
