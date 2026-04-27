# KAGE repo — Claude instructions

You are running inside the **KAGE installer repo**. The user has cloned this repo into their workspace folder and is asking you for help. Your primary job: get KAGE installed and operational on their machine, then hand off to the installed skill.

This file is read automatically when `claude` runs from this folder. Read it, then act.

## What is KAGE

A self-contained second-brain operator. Two backends, one Claude Code skill:

- **GAMBATTE** — tasks / projects / milestones in ClickUp.
- **BUNSHIN** — durable knowledge in an Obsidian vault.

The skill lives in `skill/` in this repo. Once installed, it routes every request to the right backend.

See `README.md` for the user-facing pitch. See `docs/wat-framework.md` and `docs/philosophies.md` for the operating doctrine that underpins all of KAGE.

## Bootstrap workflow

If the user says "set me up", "bootstrap KAGE", "install KAGE", "I just cloned this", or anything that signals first-time setup, run this sequence. Confirm each non-trivial step with the user — never assume paths.

### Step 1 — Locate the repo and the workspace root

The kage repo is the folder containing this `CLAUDE.md`. The **workspace root** is its parent — that's where you'll scaffold the workspace-level `CLAUDE.md` in step 6. Confirm with the user that this is where they want KAGE rooted; if they cloned somewhere unusual, ask before assuming.

### Step 2 — Verify Claude Code's skills directory + detect Python

**Don't run `claude --version`.** You're already running — Claude Code is installed. The CLI may not be on the non-interactive shell's PATH (especially on Windows / PowerShell), but that's irrelevant: what the skill actually needs is the discovery directory at `~/.claude/skills/`.

```bash
# Confirm the skills directory exists. If not, mkdir it.
test -d ~/.claude/skills && echo "ok" || mkdir -p ~/.claude/skills
```

**Now detect a working Python.** This is the step that bites Windows users hardest. On Windows, `python` often resolves to the Microsoft Store stub (a placeholder that opens the Store instead of running a real interpreter). The Python Launcher `py -3` always finds a real Python if one is installed.

Detection order — try each and use the first that works:

```bash
# Try in this order, pick the first that prints a real version (3.9+):
py -3 --version          # Windows Python Launcher — preferred on Windows
python3 --version        # macOS / Linux preferred
python --version         # Fallback; on Windows may be the Store stub
```

The Store stub's tell: `python --version` may print nothing, exit silently, or trigger a Store popup. If you see "Python was not found; run without arguments to install from the Microsoft Store" — that's the stub.

**If none of the three work**, the user needs a real Python. Walk them through:

1. Open https://www.python.org/downloads/ in their browser.
2. Download Python 3.12 (or whatever's current — anything 3.9+ is fine).
3. **CRITICAL: during install, check the "Add python.exe to PATH" checkbox at the bottom of the first installer screen.** This is the most-missed step.
4. Also recommend the user disable the Microsoft Store stub: Settings → Apps → "App execution aliases" → toggle off both `python.exe` and `python3.exe`.
5. Re-open their terminal (PATH refreshes only on new shells) and re-run detection.

Once you've identified the working Python command, **remember it for every subsequent step.** Refer to it below as `<PY>`. On Windows it'll usually be `py -3`; on Mac/Linux it'll usually be `python3`.

### Step 3 — Install the skill

The skill at `skill/` needs to live at `~/.claude/skills/kage/` to be auto-discovered. Two options:

- **Symlink (preferred on macOS/Linux):** `ln -s "$(pwd)/skill" ~/.claude/skills/kage`. Updates to this repo flow through automatically.
- **Copy (default on Windows, where symlinks need admin):** copy `skill/*` recursively into `~/.claude/skills/kage/`. Manual re-copy after `git pull`.

Detect the OS. On Windows, prefer copy. On Mac/Linux, prefer symlink unless the user prefers copy.

If `~/.claude/skills/kage/` already exists, **do not overwrite silently** — ask the user. They may have a previous install with local edits.

### Step 4 — Wire credentials

Inside the kage repo:

```bash
cp .env.example .env
```

Open `.env` and fill in:

- `CLICKUP_API_KEY` — their ClickUp personal token. ClickUp avatar menu → Settings → Apps → API Token → copy the `pk_...` value. Paste literally — **NO `Bearer ` prefix**.
- `CLICKUP_TEAM_ID` — their ClickUp workspace ID. Found in any ClickUp URL: `https://app.clickup.com/<this-number>/...`. Or run `python skill/scripts/clickup.py teams` after step 5 verifies auth.
- `BUNSHIN_VAULT` *(optional)* — absolute path to their Obsidian vault folder. Leave unset if they don't use Obsidian; the ClickUp half works alone.

After filling in, also `cp .env ~/.claude/skills/kage/.env` so the installed skill can find credentials. (Or symlink, same OS rules as step 3.)

### Step 5 — Verify ClickUp auth

```bash
<PY> ~/.claude/skills/kage/scripts/clickup.py whoami
```

(Where `<PY>` is the working Python command you detected in Step 2 — e.g. `py -3` on Windows, `python3` on Mac/Linux.)

Expect a JSON blob with the user's ClickUp profile. If it 401s, the token is wrong or has a smuggled `Bearer ` prefix — fix and retry. If it 403s on a Team, they're missing the team_id or it's wrong. If it errors with `ModuleNotFoundError: No module named 'requests'`, run `<PY> -m pip install requests` and retry.

### Step 6 — Generate the ClickUp manifest

KAGE needs a map of the user's ClickUp Spaces and Lists to route tasks correctly. Run the manifest generator:

```bash
<PY> ~/.claude/skills/kage/scripts/clickup.py build-manifest > ~/.claude/skills/kage/manifest.json
```

(If `build-manifest` doesn't exist as a CLI command yet, walk the user through ClickUp's Spaces+Lists API manually — see `docs/clickup-setup.md` for the structure. The shape is `{team_id, spaces: {<space_name>: {space_id, lists: {<list_name>: <list_id>}}}}`.)

### Step 7 — Scaffold the workspace-level CLAUDE.md

This is the load-bearing step. Read `skill/templates/workspace-CLAUDE.md`. Copy it to `<workspace-root>/CLAUDE.md` (one level up from this kage repo).

**If `<workspace-root>/CLAUDE.md` already exists, do NOT overwrite.** Read both files, show the user the diff, and ask:
- Append the KAGE doctrine sections to their existing file?
- Replace entirely?
- Skip and let them merge by hand?

Default behavior on collision: append a "## KAGE — the second brain" section + the doctrine sections from the template, leaving any existing repo list / project-specific content intact.

The workspace-level CLAUDE.md is what makes every future Claude session in the workspace inherit the operating doctrine. **Without it, KAGE works but the rest of their workspace doesn't get the WAT / philosophies context.**

### Step 8 — Smoke test

Run the bounty board to prove end-to-end ClickUp access:

```bash
<PY> ~/.claude/skills/kage/scripts/clickup.py musts
```

Expect a flat table of every Urgent task across all their Spaces. If empty, that's fine — confirms auth and manifest are good, they just don't have any open Musts yet.

If they set up Obsidian:

```bash
<PY> ~/.claude/skills/kage/scripts/obsidian.py whoami
```

Expect vault path + a count of notes.

### Step 9 — Hand off

Tell the user:
- KAGE is installed at `~/.claude/skills/kage/`.
- Their workspace doctrine is at `<workspace-root>/CLAUDE.md`.
- Future sessions: just say what they want ("what's on my plate", "add a task", "log a decision", "ingest this article"). The skill auto-fires.
- Read `~/.claude/skills/kage/SKILL.md` if they want the full operating manual. Read `docs/wat-framework.md` + `docs/philosophies.md` for the doctrine.

Offer to demo one workflow — the bounty board, a journal entry, or ingesting a sample source — so they see KAGE in action before the session ends.

## Edge cases

- **`claude` not found on PATH** → ignore. You're already running, so it's installed. The bootstrap doesn't need the CLI on PATH; it only needs `~/.claude/skills/` (which exists or can be created with `mkdir -p`).
- **`python` opens the Microsoft Store instead of running** → that's the Windows Store stub. Use `py -3` instead. If `py` also fails, real Python isn't installed — see Step 2 for the install walkthrough.
- **`python3` works but `python` doesn't (or vice versa)** → fine, just use whichever works. Remember it as `<PY>` for every subsequent command.
- **`ModuleNotFoundError: No module named 'requests'`** → run `<PY> -m pip install requests` and retry. Don't use `pip install` directly — it might install into a different Python than the one you detected.
- **Skill folder already exists at `~/.claude/skills/kage/`** → ask before overwriting; surface what's there. They may have local edits worth preserving.
- **`.env` already populated** → don't clobber; show what's there and ask if anything needs updating.
- **Workspace `CLAUDE.md` already mentions KAGE** → assume bootstrap was partially run before. Surface what's done vs missing, finish only the missing parts.
- **User on Mac/Linux** → all skill paths work, but symlinks (`ln -s`) are preferred over copy so updates flow through.
- **User has no Obsidian vault** → that's fine. Skip the `BUNSHIN_VAULT` env var, skip the obsidian.py smoke test. The ClickUp half operates standalone.
- **User's ClickUp workspace has zero Spaces** → they need to create at least one Space + one List in ClickUp before the manifest step makes sense. Walk them through it via `docs/clickup-setup.md`.

## After bootstrap

Once installed, this `CLAUDE.md` (in the kage repo) is rarely useful — the user mostly operates from their workspace root, where `<workspace-root>/CLAUDE.md` and the auto-discovered skill take over. They only come back to this repo to `git pull` updates or to read the docs.

If a returning user asks you (running from inside this kage repo) to do KAGE operations directly, redirect: "the skill is installed at `~/.claude/skills/kage/` — run from your workspace root and ask there. The skill lives there, not here."

## Idempotency

This entire bootstrap is idempotent. A second run should detect what's already done, skip those steps cleanly, and only do what's missing. Never duplicate-write anything.
