# KAGE manual install reference

This is the step-by-step manual install. Most people should ignore this and use the **easy path**: clone, `cd kage`, run `claude`, say "set me up." Claude reads `CLAUDE.md` in this folder and walks you through the same steps automatically.

If you'd rather do it by hand, here it is.

## Prerequisites

1. **Claude Code CLI** — install from https://docs.claude.com/en/docs/claude-code/overview if missing. (You don't need `claude` to be on your shell's PATH — the skill only needs the `~/.claude/skills/` directory the installer creates.)
2. **Python 3.9+** — see the Python notes below; Windows users in particular should read these before starting.
3. **Git** — to clone this repo. (Skip if you've downloaded the zip.)
4. **A ClickUp account** with API access. Free Forever and up.
5. **(Optional) An Obsidian vault.** Skip if you don't use Obsidian — the ClickUp half works standalone.

### Python notes (read this if you're on Windows)

Windows ships a "Microsoft Store stub" for `python` — a placeholder that opens the Store instead of running an interpreter. Symptoms: `python --version` exits silently, or you see "Python was not found; run without arguments to install from the Microsoft Store."

**Two ways to fix:**

**A) Install real Python from python.org (recommended)**

1. Download Python 3.12 (or any 3.9+) from https://www.python.org/downloads/.
2. **CRITICAL: during install, check the "Add python.exe to PATH" checkbox** at the bottom of the first installer screen. This is the most-missed step.
3. Disable the Store stubs: Settings → Apps → "App execution aliases" → toggle off both `python.exe` and `python3.exe`.
4. Open a fresh terminal (PATH only refreshes on new shells).

After install, on Windows you'll have **`py -3`** as the universal Python launcher — it always finds a real Python regardless of PATH order. Use `py -3` instead of `python` everywhere on Windows. Mac/Linux users use `python3`.

**B) Detect what works and use that**

Try each in this order — use the first that prints a real version:

```bash
py -3 --version          # Windows Python Launcher (preferred on Windows)
python3 --version        # macOS / Linux preferred
python --version         # Fallback (may be the Store stub on Windows)
```

In every command below, replace `python` with whichever one worked for you. If none did, install Python first (Option A above).

## Step 1 — Clone

```bash
cd <your-workspace-folder>     # wherever you keep code
git clone <this-repo-url> kage
cd kage
```

The repo can live anywhere. Common spots: `~/Projects/`, `~/Documents/repos/`, `~/code/`.

## Step 2 — Install the skill

The skill at `skill/` needs to live at `~/.claude/skills/kage/` so Claude Code auto-discovers it.

### macOS / Linux

```bash
mkdir -p ~/.claude/skills
ln -s "$(pwd)/skill" ~/.claude/skills/kage
```

Symlink is preferred — when you `git pull` updates to this repo, the installed skill updates automatically.

### Windows (PowerShell, run as Administrator if you want a symlink)

```powershell
New-Item -ItemType Directory -Force -Path "$HOME\.claude\skills"
# Symlink (admin required):
New-Item -ItemType SymbolicLink -Path "$HOME\.claude\skills\kage" -Target "$PWD\skill"
```

### Windows (no admin — copy)

```powershell
Copy-Item -Recurse "$PWD\skill" "$HOME\.claude\skills\kage"
```

If you copy, remember to re-copy after every `git pull`.

## Step 3 — Set up credentials

```bash
cp .env.example .env
```

Open `.env` and fill in:

- **`CLICKUP_API_KEY`** — your ClickUp personal token.
  1. Open ClickUp.
  2. Click your avatar (top-right) → Settings.
  3. Sidebar → Apps → API Token.
  4. Copy the `pk_xxxxx...` value.
  5. Paste as `CLICKUP_API_KEY=pk_xxxxx...`. **No `Bearer ` prefix.**

- **`CLICKUP_TEAM_ID`** — your ClickUp workspace ID.
  - Open ClickUp in a browser. The URL after login looks like `https://app.clickup.com/12345678/v/...` — that `12345678` is your team_id.
  - Or run `python ~/.claude/skills/kage/scripts/clickup.py teams` after step 4 verifies your token.

- **`BUNSHIN_VAULT`** *(optional)* — absolute path to your Obsidian vault folder. Leave unset if you don't use Obsidian.

Then mirror the file into the installed skill folder so the helpers can find it:

```bash
cp .env ~/.claude/skills/kage/.env       # or symlink
```

## Step 4 — Verify ClickUp auth

```bash
python ~/.claude/skills/kage/scripts/clickup.py whoami
```

Expected: a JSON blob with your ClickUp profile (id, username, email, color, profilePicture).

Common failures:
- **401 Unauthorized** — token is wrong or has a `Bearer ` prefix smuggled in. Re-check `.env`.
- **403 Forbidden on a team** — `CLICKUP_TEAM_ID` doesn't match a workspace your token has access to.
- **`requests` not installed** — `pip install requests`.

## Step 5 — Build the ClickUp manifest

The skill needs a map of your Spaces and Lists to route tasks. Run:

```bash
python ~/.claude/skills/kage/scripts/clickup.py build-manifest > ~/.claude/skills/kage/manifest.json
```

If `build-manifest` doesn't exist as a CLI command, see [docs/clickup-setup.md](docs/clickup-setup.md) for the manual structure. The shape is:

```json
{
  "team_id": "<your team_id>",
  "spaces": {
    "<Space Name>": {
      "space_id": "<space_id>",
      "lists": {
        "<List Name>": "<list_id>"
      }
    }
  }
}
```

## Step 6 — (Optional) Verify Obsidian

If you set `BUNSHIN_VAULT`:

```bash
python ~/.claude/skills/kage/scripts/obsidian.py whoami
```

Expected: vault path + count of `.md` files in the vault.

If it errors with `vault not found`, fix the path. Use forward slashes everywhere — even on Windows: `BUNSHIN_VAULT=C:/Users/yourname/Documents/MyVault`.

## Step 7 — Scaffold the workspace-level CLAUDE.md

Copy the doctrine template up one folder so every Claude session in your workspace inherits the operating doctrine:

### macOS / Linux

```bash
cp skill/templates/workspace-CLAUDE.md ../CLAUDE.md
```

### Windows (PowerShell)

```powershell
Copy-Item "skill\templates\workspace-CLAUDE.md" "..\CLAUDE.md"
```

**If `../CLAUDE.md` already exists, don't blindly overwrite.** Read both. Either:

- Append the doctrine sections from `skill/templates/workspace-CLAUDE.md` to your existing file (recommended), or
- Replace entirely (only if your existing file has no content worth keeping), or
- Skip and merge by hand later.

## Step 8 — Smoke test

Run the bounty board to prove end-to-end:

```bash
python ~/.claude/skills/kage/scripts/clickup.py musts
```

Expected: a flat table of every Urgent task across your Spaces. Empty is fine if you have no open Musts.

## Done

From any future Claude session in your workspace, the skill auto-fires when you mention tasks, knowledge, people, or any second-brain operation. Try:

- "what's on my plate this week"
- "add a task to call the dentist by Friday"
- "log this decision: switched from notion to obsidian"
- "ingest this article: <url>"
- "search my notes for <topic>"

Read `~/.claude/skills/kage/SKILL.md` for the full operating manual. Read `docs/wat-framework.md` + `docs/philosophies.md` for the operating doctrine.

## Updating

When you `git pull` updates to this repo:

- **Symlinked install** — changes flow through automatically. Just verify with `python ~/.claude/skills/kage/scripts/clickup.py whoami`.
- **Copied install** — re-run the copy from step 2.

Your `.env`, `manifest.json`, and any custom edits to `references/conventions.md` should be preserved across updates — they're either gitignored or per-user data.

## Uninstalling

```bash
rm -rf ~/.claude/skills/kage          # removes the skill (or `Remove-Item -Recurse` on Windows)
rm <workspace-root>/CLAUDE.md         # if you want to drop the workspace doctrine too
```

The kage repo itself can stay or go — it's only used for updates and reference after install.
