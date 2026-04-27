# ClickUp Setup for GAMBATTE

GAMBATTE is the active-work half of KAGE. It runs on ClickUp because ClickUp gives you real PM features (priorities, statuses, assignees, time tracking, mobile, dashboards, ClickUp Brain) without you having to build them.

This doc walks through setting up a ClickUp workspace that KAGE can drive.

## Sign up

1. Go to https://clickup.com.
2. Free Forever plan is fine to start. Upgrade if/when you need things like custom field bulk edits, advanced automations, or ClickUp Brain.
3. Create a workspace. The name is up to you — "Personal," "<your name>," "<your company>," whatever.
4. Skip ClickUp's onboarding wizard or fill it in to whatever depth feels useful — KAGE will reshape the structure during bootstrap anyway.

## Get your API token

1. Click your avatar (top-right).
2. **Settings → Apps → API Token**.
3. Copy the `pk_xxxxxxxxxxxxxxxxxxxxx` value.
4. Paste it into `.env` as `CLICKUP_API_KEY=pk_xxx...`.

Treat the token like a password. Don't commit it. Don't share it. Rotate it if it ever leaks.

## Get your workspace (team) ID

Open ClickUp in a browser. The URL after login looks like:

```
https://app.clickup.com/12345678/v/...
```

That `12345678` is your `team_id`. Paste into `.env` as `CLICKUP_TEAM_ID=12345678`.

Or run after the token's wired up:

```bash
python ~/.claude/skills/kage/scripts/clickup.py teams
```

Lists every workspace your token has access to.

## ClickUp's hierarchy

KAGE assumes this structure:

```
Workspace (= Team in API)
  └─ Space         = a top-level domain (a business, a project, "Personal", "Inbox")
       └─ List     = a category within that domain (a department, a pillar, etc.)
            └─ Task = the actual work
```

You can also have **Folders** between Spaces and Lists, but KAGE prefers a flat Space → List shape. Folders work if you need them but aren't required.

## Recommended Space layout

Pick a layout that maps to how you organize your life or business. A few patterns:

### Pattern A — Single user, mixed personal/work

```
Workspace
├─ Personal
│  ├─ Health
│  ├─ Finance
│  ├─ People
│  └─ Wisdom
├─ Work
│  ├─ ADMIN
│  ├─ FULFILLMENT
│  └─ MARKETING
└─ Inbox
   └─ Quick Capture
```

### Pattern B — Multiple businesses

```
Workspace
├─ <Business A>
│  ├─ ADMIN
│  ├─ MARKETING
│  ├─ SALES
│  ├─ FULFILLMENT
│  └─ ACCOUNTS
├─ <Business B>
│  └─ (same departments)
├─ <Business C>
│  └─ (same departments)
├─ Personal
│  └─ ...
└─ Inbox
   └─ Quick Capture
```

### Pattern C — Project-driven

```
Workspace
├─ <Project Alpha>
│  ├─ ROADMAP
│  ├─ FULFILLMENT
│  └─ ADMIN
├─ <Project Beta>
│  └─ ...
├─ Personal
│  └─ ...
└─ Inbox
   └─ Quick Capture
```

The recurring elements:

- **One `Inbox` Space** with a `Quick Capture` List. This is where ambiguous tasks land when KAGE can't immediately route them. You triage Inbox during weekly planning.
- **One `Personal` Space** if you want personal life items (health, finance, relationships) tracked alongside work.
- **One Space per high-level domain** (per business, per project, etc.) so each gets its own dashboards, statuses, and saved views.

## Set up Spaces and Lists in ClickUp

You can do this in ClickUp's UI:

1. In the sidebar, click **+ New Space**.
2. Name it (use the conventions above).
3. Create Lists inside the Space (right-click Space → **+ Create List**).
4. Optionally set custom statuses per Space (default `to do / in progress / complete` is usually fine; KAGE expects lowercase status names).

Or you can ask Claude to do it after bootstrap — once `CLICKUP_API_KEY` is wired, Claude can create Spaces and Lists via the API. **But KAGE intentionally doesn't auto-create Spaces and Lists during bootstrap** — they're permanent structural decisions that affect saved views and team workflows. Set them up by hand the first time.

## Generate the manifest

KAGE needs a map of Space names → Space IDs and List names → List IDs to route tasks. After you've set up Spaces and Lists, run:

```bash
python ~/.claude/skills/kage/scripts/clickup.py build-manifest > ~/.claude/skills/kage/manifest.json
```

The output looks like:

```json
{
  "team_id": "12345678",
  "spaces": {
    "Personal": {
      "space_id": "987654321",
      "lists": {
        "Health": "111222333",
        "Finance": "111222334"
      }
    },
    "Work": {
      "space_id": "987654322",
      "lists": {
        "ADMIN": "111222335",
        "FULFILLMENT": "111222336"
      }
    }
  }
}
```

KAGE reads this on every task creation to resolve `(space, list_name)` → `list_id`.

## Re-generate when you restructure

If you add a new Space or List in ClickUp, **regenerate the manifest**:

```bash
python ~/.claude/skills/kage/scripts/clickup.py build-manifest > ~/.claude/skills/kage/manifest.json
```

KAGE caches the manifest per session, so re-running this and re-loading Claude is the fast way to pick up changes.

## Priorities

ClickUp has 4 priority levels (the API encodes them as ints):

| Name | API value | KAGE label |
|---|---|---|
| Urgent | 1 | Must |
| High | 2 | Should |
| Normal | 3 | (unused) |
| Low | 4 | Could |

KAGE uses **Must / Should / Could** as the labels Claude understands. They map to ClickUp's Urgent / High / Low. The "Normal" middle slot stays unused — it's too vague to be useful.

The `clickup.list_musts()` helper queries every Urgent (priority=1) task across every Space — that's your "bounty board."

## Statuses

ClickUp statuses are **lowercase and case-sensitive**. Default Space statuses are:

- `to do`
- `in progress`
- `complete`

Some Spaces also have:

- `blocked` (recommended — add it via Space settings)
- `in review`
- `closed` (auto-archives older tasks)

KAGE assumes lowercase. If you customize a Space's statuses, keep them lowercase or KAGE's status updates will silently fail.

## Tags

Tags are free-form labels. KAGE uses them for categorization without requiring custom fields:

- `paid`, `owned`, `free` — for marketing tasks (channel type)
- `<priority>` — sometimes redundant with the priority enum
- `blocked` — fallback if the Space doesn't have a `blocked` status

You can add any tags you want. Just be consistent — `urgent` and `Urgent` are different tags.

## Verify end-to-end

```bash
# Auth
python ~/.claude/skills/kage/scripts/clickup.py whoami

# Spaces
python ~/.claude/skills/kage/scripts/clickup.py spaces

# Manifest (lists what's routable)
python ~/.claude/skills/kage/scripts/clickup.py manifest

# Bounty board — should be empty until you add a Must
python ~/.claude/skills/kage/scripts/clickup.py musts
```

If all four work, GAMBATTE is wired up. From any Claude session in your workspace, just say what you want — "add a must to call the dentist by Friday in Personal/Health" — and the skill auto-fires.

## Optional: ClickUp Brain

ClickUp Brain (paid add-on, ~$5/user/month at time of writing) is ClickUp's built-in AI for in-workspace queries — "summarize all overdue Musts," "what did <person> ship this week," etc. It runs on top of your ClickUp data and is a nice complement to KAGE:

- Use **ClickUp Brain** for in-workspace summaries that don't need cross-context.
- Use **KAGE (Claude)** for anything that bridges tasks + knowledge + repos — Brain doesn't see BUNSHIN or your codebase.

You don't need Brain to use KAGE. But if you spend a lot of time inside ClickUp answering "what's the state of X across all our work," Brain pays for itself fast.

## Troubleshooting

- **`401 Unauthorized`** → token is wrong, or has a `Bearer ` prefix smuggled in.
- **`403 Forbidden`** → token doesn't have access to the requested team. Check `CLICKUP_TEAM_ID`.
- **`No List ID resolved for Space='X' List='Y'`** → manifest is stale. Re-run `build-manifest`.
- **`429 Too Many Requests`** → rate limit. The helper throttles automatically; if you keep hitting this, another process is sharing your token.
- **Task created but doesn't appear in the right List** → manifest probably has stale IDs. Re-generate.

The full ClickUp API quirks reference is in `~/.claude/skills/kage/references/clickup-api-quirks.md`.
