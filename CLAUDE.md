# Second Brain Setup — installer instructions for Claude

You are running inside the **second-brain-setup** repo. The user cloned it to set up a personal 2nd brain in Obsidian. Your job: install the skill, then build their vault.

## When the user says "set me up" (or "install", "get started", "I just cloned this")

1. **Install the skill.** Copy this repo's `skill/` folder to `~/.claude/skills/second-brain/`, creating `~/.claude/skills/` if needed.
   - macOS/Linux/Git Bash: `mkdir -p ~/.claude/skills && cp -R skill ~/.claude/skills/second-brain`
   - PowerShell: `New-Item -ItemType Directory -Force "$HOME\.claude\skills" | Out-Null; Copy-Item -Recurse skill "$HOME\.claude\skills\second-brain"`
   - If `~/.claude/skills/second-brain/` already exists, ask before replacing it, because it may be an older install the user has edited. On a yes, first rename the old folder to `second-brain.bak-YYYYMMDD`, then copy. Copying onto an existing folder nests the new copy inside it as `second-brain/skill/`.
   - Check that `~/.claude/skills/second-brain/SKILL.md` and `~/.claude/skills/second-brain/templates/vault/executive.md` exist.

2. **Build the vault.** Read `~/.claude/skills/second-brain/SKILL.md` and follow **Workflow 1: Set up a new vault** from the interview onward. The skill's template lives at `~/.claude/skills/second-brain/templates/vault/`.

3. **Finish.** Tell the user:
   - The skill is installed and their vault is at `<path>`.
   - To open the vault in Obsidian, choose "Open folder as vault", then turn on the **Daily notes** and **Templates** core plugins.
   - From now on, run `claude` from inside the vault folder.
   - This repo folder can be deleted.
   - Backups aren't set up yet (see `~/.claude/skills/second-brain/references/obsidian-setup.md`).

The vault must **never** go inside this repo folder, since the user will delete the folder after setup.

## Rules during setup

- Confirm the vault path before writing. Never overwrite an existing folder or file.
- The template contains no personal data. Everything personal comes from the user's answers.
- Don't push, publish, or upload anything. The vault stays on the user's computer.
- Keep explanations plain. Assume the user is smart but may be new to the terminal.
