# Workspace — Claude operating doctrine

This folder is your workspace root. Each subfolder is a self-contained project repo. **This file is the workspace-level operating doctrine** — any Claude session run from this folder reads it before doing anything else, and inherits the conventions below.

If KAGE isn't fully set up yet, ask Claude to "bootstrap KAGE" — it will follow `<this-workspace>/kage/CLAUDE.md` end-to-end.

## KAGE — the second brain

KAGE is the source of truth for active work and durable knowledge. Two backends, one skill:

- **GAMBATTE** (tasks · projects · milestones) → ClickUp workspace
- **BUNSHIN** (knowledge — entities, people, decisions, references) → Obsidian vault (optional; the ClickUp half works without it)

The `kage` skill (installed at `~/.claude/skills/kage/`) operates both halves. **Invoke it whenever** you mention a task, "what's on my plate", a person by name, an entity, "log this", "file this", "add a task", or any work that belongs in a second brain. It auto-triggers most of the time — if unsure, ask Claude to "use KAGE."

GAMBATTE (ClickUp) is canonical for tasks. BUNSHIN (Obsidian) is canonical for knowledge. **Don't dual-write the same thing into both** — bridge with a URL instead (an `obsidian://` link in a ClickUp task description, or a ClickUp task URL in an Obsidian note's frontmatter).

## Operating Doctrine — WAT + Three Philosophies

Every workflow, tool, and decision in this workspace assumes these four ideas. Full deep-dive at `kage/docs/wat-framework.md` and `kage/docs/philosophies.md`; this is the workspace-level restatement so a fresh Claude session has it without needing to follow links.

### The WAT Framework

WAT (Workflows, Agents, Tools) separates concerns so probabilistic AI handles reasoning while deterministic code handles execution.

- **Workflows** — markdown SOPs that define objective, inputs, tools, expected outputs, and edge cases.
- **Agents** — Claude. Reads the workflow, runs tools in order, recovers from errors, asks clarifying questions when inputs are ambiguous.
- **Tools** — Python scripts (or helpers in any language) that do the deterministic work. API calls, file I/O, transformations.

When AI handles every step directly, accuracy compounds badly — five steps at 90% accuracy lands at 59% success. Offloading execution to scripts keeps Claude focused on orchestration where it shines.

### Philosophy 1 — Bottom Up for Understanding, Top Down for Speed

Never automate what you don't understand. Build by hand first, prove a small case works, then wrap in a tool. The shortcut only has value once you know what's underneath. When something breaks, the foundation of understanding is what lets you fix it — not the abstraction that hid the complexity.

In KAGE specifically, this is **the Karpathy LLM-wiki pattern** — read the source, discuss takeaways, then write the summary. Don't dump raw text and call it a wiki.

### Philosophy 2 — The Flywheel

Every output is the next system's input. Don't build dead-end systems. A research tool produces insights → those feed a content workflow → which drives engagement → which feeds back into better research. **Manual gaps in this loop are flywheel opportunities — flag them.**

In KAGE: source → BUNSHIN ingest → surfaces during a future query → grounds a decision or task in GAMBATTE → completed task result filed back as a wiki page → becomes a source for the next ingest.

### Philosophy 3 — Clean Separation, Zero Entanglement

No circular dependencies. Each module extractable standalone. Dependencies flow one direction: foundational layers at the bottom, specialized tools on top. Nothing at the bottom reaches up; nothing at the top tangles sideways into an unrelated domain.

If a tool breaks, the blast radius is its folder and its consumers — not the whole system.

In KAGE: the **CQRS split** between BUNSHIN (reads/knowledge) and GAMBATTE (writes/work) is the cleanest expression of this. They share URIs as a bridge, never schema.

### The $80K Rule

Before any deployment that calls a metered API: **"If this endpoint got hit 1 million times tonight, what would it cost?"** If the answer isn't bounded — circuit breaker, daily cap, kill switch, hard provider limit — don't ship. This applies to Stripe, Twilio, OpenAI, Anthropic, ElevenLabs, Resend, Vercel, ClickUp, and anything else that bills per call.

For KAGE specifically, the equivalent is: "If this wave or write hits the wrong list / space / note, how much does the user have to clean up by hand?" If unbounded, ask before flushing.

## Workspace Guidelines

- **KAGE is the default context source.** Query it for entities, people, strategy, and decisions before guessing.
- **Each repo has its own CLAUDE.md.** Defer to repo-specific instructions once you're working inside one.
- **Confirm the repo before broad searches.** Don't grep across every repo unless explicitly asked.
- **Be direct.** Concise, practical responses. No fluff.
- **Run it, don't just say it.** When previews, dev servers, or build tools need launching, run them directly via the Bash tool. If you must show a command in chat, use the full absolute path.
- **The repo list below is yours to maintain.** Add your repos as you clone them so future Claude sessions know what's in this workspace.

## Repos in this workspace

(Fill in as you clone. The kage repo itself counts — list it here.)

- `kage/` — KAGE skill source. Cloned here, installed at `~/.claude/skills/kage/`. See `kage/README.md` for setup; `~/.claude/skills/kage/SKILL.md` for the operating manual.

## Where to learn more

- **The KAGE-mapped doctrine** (how WAT and the three philosophies show up specifically inside the kage skill) → `~/.claude/skills/kage/SKILL.md`, "Operating Doctrine" section.
- **The full WAT framework deep-dive** → `kage/docs/wat-framework.md`.
- **The full philosophies deep-dive** → `kage/docs/philosophies.md`.
- **Karpathy LLM-wiki methodology** (the doctrine BUNSHIN runs on) → `~/.claude/skills/kage/references/karpathy-llm-wiki.md`.
- **Wave semantics** (when to write to ClickUp immediately vs queue) → `~/.claude/skills/kage/references/waves.md`.
