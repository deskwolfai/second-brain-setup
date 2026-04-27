# KAGE — a Claude-driven second brain

KAGE is a self-contained operator for two things every knowledge worker needs: **active work** (tasks, projects, milestones) and **durable knowledge** (people, decisions, references, the stuff that compounds over time).

It's two backends bridged by one Claude Code skill:

- **GAMBATTE** — your tasks live in **ClickUp**. Real PM features, mobile, team visibility, ClickUp Brain.
- **BUNSHIN** — your knowledge lives in an **Obsidian vault**. Filesystem-speed, Claude-native markdown, offline, graph view, wikilinks.

The skill (`skill/`) routes every request to the right side, owns a wiki-style maintenance pattern for Obsidian (Karpathy's LLM-wiki methodology), and batches ClickUp writes into "waves" so collaborators don't see half-done state.

KAGE is **agnostic** — no company, framework, or industry baked in. Bring your own ClickUp workspace, your own (optional) Obsidian vault, and KAGE handles the orchestration.

## Why use it

- **One mental model, two backends.** Stop deciding where to put a thought — KAGE routes it.
- **Knowledge compounds.** Every source you ingest updates the wiki. Old notes stay current because Claude does the bookkeeping.
- **Tasks ship.** Bulk captures go through "waves" so 20 brain-dumped items hit ClickUp as one coherent batch, not 20 half-formed updates your teammates have to wade through.
- **Cold-start speed.** A fresh Claude session reads the skill once and operates the whole second brain in 1–2 turns.

## Install (the easy way — 60 seconds)

Prerequisites:
- [Claude Code CLI](https://docs.claude.com/en/docs/claude-code/overview) installed (`claude` available in your shell).
- A ClickUp account with a personal API token.
- (Optional) An [Obsidian](https://obsidian.md) vault — KAGE works without one, the ClickUp half stands alone.

Steps:
1. Clone this repo into your workspace folder (e.g. `~/Projects/`, `~/Documents/repos/`, wherever you keep code):
   ```bash
   git clone <this-repo-url> kage
   cd kage
   ```
2. Run `claude` from inside the `kage/` folder.
3. Tell Claude: **"set me up"** (or "bootstrap KAGE", "install KAGE").
4. Claude reads `CLAUDE.md` in this folder and walks you through:
   - Installing the skill into `~/.claude/skills/kage/`
   - Setting up `.env` with your ClickUp token (and optional Obsidian vault path)
   - Building a `manifest.json` for your ClickUp Spaces and Lists
   - Verifying ClickUp auth with a `whoami` smoke test
   - **Scaffolding a workspace-level `CLAUDE.md` one folder up** (so every future Claude session in your workspace inherits the operating doctrine)
   - A bounty-board smoke test to prove end-to-end ClickUp access

That's it. From any future session in your workspace, just say what you want — "add a task to call the dentist", "log a decision about Q3 roadmap", "what's on my plate this week" — and the skill auto-fires.

## Install (manual, if you'd rather not delegate to Claude)

See [INSTALL.md](INSTALL.md) for step-by-step copy-paste instructions.

## What's in this repo

- `README.md` — this file.
- `CLAUDE.md` — instructions Claude reads when you run `claude` inside this folder. Handles bootstrap.
- `INSTALL.md` — detailed manual install reference.
- `.env.example` — credentials template. Copy to `.env` after install.
- `.gitignore` — keeps `.env` and Python bytecode out of git.
- `skill/` — the Claude Code skill itself. Drops into `~/.claude/skills/kage/` during bootstrap.
  - `SKILL.md` — operating manual. The brain of the system.
  - `manifest.json` — your ClickUp Space + List ID map. Generated during bootstrap.
  - `scripts/` — Python helpers for Obsidian, ClickUp, and the wave-batched writer.
  - `references/` — doctrine docs Claude reads on demand (Karpathy wiki pattern, wave semantics, conventions, vault layout, ClickUp API quirks).
  - `templates/workspace-CLAUDE.md` — the doctrine Claude scaffolds at your workspace root during bootstrap.
- `docs/` — agnostic reference material humans can read directly.
  - `wat-framework.md` — the WAT (Workflows / Agents / Tools) framework that underpins how KAGE operates.
  - `philosophies.md` — the three operating philosophies + the $80K rule.
  - `obsidian-setup.md` — how to set up an Obsidian vault for BUNSHIN.
  - `clickup-setup.md` — how to set up a ClickUp workspace for GAMBATTE.

## Philosophy summary

KAGE is built on four ideas. Read [docs/philosophies.md](docs/philosophies.md) for depth.

1. **WAT framework** — Workflows (instructions), Agents (Claude), Tools (deterministic scripts). Probabilistic AI handles reasoning; code handles execution.
2. **Bottom up for understanding, top down for speed.** Never automate what you don't understand. The Karpathy wiki pattern is this philosophy in action.
3. **The flywheel.** Every output is the next system's input. Manual gaps in the loop are flag-able opportunities, not features.
4. **Clean separation, zero entanglement.** BUNSHIN owns reads, GAMBATTE owns writes — bridged by URLs, never schema. Don't dual-write.

## Compatibility

- **Operating systems:** Windows 10+, macOS 12+, Linux (any modern distro).
- **Python:** 3.9+ (the helper scripts are stdlib + `requests` — minimal deps).
- **Claude Code:** any recent version. Skills auto-discovered from `~/.claude/skills/`.
- **ClickUp:** any plan with API access (Free Forever and up).
- **Obsidian:** any version. Optional — ClickUp half works without it.

## License

[Your choice — MIT, Apache-2.0, etc. Add a LICENSE file before publishing.]

## Credits

KAGE's architecture borrows from:
- **Andrej Karpathy's LLM-wiki methodology** ([karpathy-llm-wiki.md](skill/references/karpathy-llm-wiki.md)) — the maintenance pattern BUNSHIN runs on.
- **CQRS** (Command Query Responsibility Segregation) — the read/write split between BUNSHIN and GAMBATTE.
- **The WAT framework** — Workflows / Agents / Tools, originally articulated for AI-driven engineering systems.
