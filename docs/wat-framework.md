# The WAT Framework

WAT = **Workflows · Agents · Tools.** It's a framework for organizing AI-driven systems so probabilistic AI handles reasoning while deterministic code handles execution. Originally articulated for AI engineering systems where reliability matters; KAGE is one expression of it.

This doc is the canonical agnostic version. The KAGE-specific mapping lives in `~/.claude/skills/kage/SKILL.md` ("Operating Doctrine" section). The workspace-level summary lives in `<workspace-root>/CLAUDE.md` after bootstrap.

## The problem WAT solves

When AI tries to handle every step of a multi-step task directly, accuracy compounds badly. If each step is 90% accurate, you're down to **59% success after just five steps**. By step ten, you're at 35%. This is why ambitious AI agents that try to "do everything" feel unreliable: the math is against them.

The fix isn't a smarter model. It's a smarter architecture: have AI do what it's good at (reasoning, orchestration, ambiguity-handling) and have deterministic code do what it's good at (API calls, data transforms, file operations, anything with a single right answer).

WAT structures this separation explicitly into three layers.

## Layer 1: Workflows — the instructions

**Workflows are markdown SOPs.** Plain language documents describing:

- The **objective** — what success looks like.
- The **inputs** — what the agent needs before starting.
- The **tools** — which deterministic scripts to use, in what order.
- The **expected outputs** — what the agent should produce.
- The **edge cases** — what to do when something fails or is ambiguous.

A good workflow is the same kind of document you'd write to brief a smart, brand-new teammate. No code. No special syntax. Just clear instructions.

Workflows live in markdown so they're version-controlled, diff-able, and editable by anyone — not just engineers.

```
workflows/
├── ingest_source.md           # ingest a new article/transcript/document
├── add_task.md                # create a single ClickUp task
├── capture_wave.md            # bulk-capture from a brain dump
├── bounty_board.md            # render the cross-Space Musts table
└── lint_wiki.md               # quarterly health check
```

## Layer 2: Agents — the decision-maker

**The agent is Claude.** (Or whatever LLM is wired up.) The agent's job is *not* to do everything — it's to:

1. **Read** the relevant workflow.
2. **Resolve** ambiguous inputs by asking the user clarifying questions.
3. **Run** tools in the correct sequence.
4. **Recover** from failures gracefully (retry, escalate, or report).
5. **Update** the workflow when it learns something new.

The agent is the connective tissue between human intent and deterministic execution. It's good at understanding "what does the user actually want" and bad at "make 47 sequential API calls perfectly." So we let it focus on the first job and delegate the second.

If you find Claude making API calls inline (constructing URLs, formatting headers, parsing JSON response shapes) instead of calling a tool — that's a signal a tool is missing. Build the tool, update the workflow.

## Layer 3: Tools — the execution

**Tools are deterministic scripts.** Usually Python (in KAGE's case), but any language works. They:

- Make API calls.
- Transform data.
- Read and write files.
- Hit databases.
- Generate reports.

A tool's contract is **boring and explicit**: given these inputs, produce this output. No ambiguity. No "interpret the request." If the inputs aren't right, fail with a clear error.

Tools should be:

- **Idempotent where possible** — running twice produces the same result.
- **Small** — one tool, one job. Composition over monoliths.
- **Tested at the API boundary** — does the ClickUp endpoint actually return what we expect?
- **Throttled at the source** — rate-limiting baked in, not bolted on at call sites.

```
tools/                          # KAGE calls these `scripts/`
├── obsidian.py                 # Obsidian vault primitives
├── clickup.py                  # ClickUp API helper
└── waves.py                    # batched ClickUp writes
```

## How the layers fit together

A typical KAGE flow:

```
User: "log a decision: we're switching from Notion to Obsidian for knowledge"

Agent (Claude):
  1. Recognizes this matches workflow `Workflow 1 — Ingest a source` (or
     "Decision capture", a sub-pattern).
  2. Asks for any missing context (when, why, what does this affect).
  3. Reads `references/conventions.md` for the Decisions schema.
  4. Calls Tool: obsidian.create("Decisions/2026-04-23 Notion to Obsidian.md",
        body=..., frontmatter={...})
  5. Calls Tool: obsidian.append("log.md", "## [2026-04-23] decision | ...")
  6. Calls Tool: obsidian.append("index.md", "...")
  7. Reports back to user.
```

The agent never composed an HTTP request. The tools never decided what folder to file under. The workflow document was the schema both layers respected.

## When AI tries to do execution itself

A common anti-pattern:

```python
# Agent says: "Let me create that ClickUp task..."
# Agent emits: 
import requests
r = requests.post(
    "https://api.clickup.com/api/v2/list/901234567/task",
    headers={"Authorization": "Bearer pk_xxx"},   # WRONG — no Bearer prefix
    json={"name": "...", "priority": "Urgent"}    # WRONG — priority is an int enum
)
```

Two bugs in three lines, both quirks documented in `references/clickup-api-quirks.md`. The agent had to rediscover them on the fly. A tool that wraps `clickup.add_task(...)` makes both bugs impossible.

Every quirk you bake into a tool is one less thing AI has to remember (and re-remember every session, and sometimes forget).

## When tools try to do reasoning

The other anti-pattern:

```python
# Tool tries to parse natural language
def add_task_from_text(text: str):
    # Try to figure out priority, list, tags from the user's free text...
    if "urgent" in text.lower(): priority = 1
    elif "should" in text.lower(): priority = 2
    # ...this gets brittle fast
```

Don't. Let the agent resolve ambiguity. Tools take structured args. If the agent can't produce structured args, it should ask the user — not pass garbage to a tool that pretends to understand.

## Why this matters for AI reliability

**Each layer fails differently.**

- **Workflow failures** are documentation problems. Fix: clarify the SOP.
- **Agent failures** are reasoning problems. Fix: better workflow, more context, or escalate to the user.
- **Tool failures** are code problems. Fix: bug fix in the script.

When something goes wrong, you can almost always tell which layer broke. That's not true in a monolithic AI agent — when a 47-step end-to-end agent fails, isolating the cause is hours of work.

WAT also lets you **test the layers independently**:

- Tools have unit tests like any code.
- Workflows have integration tests (can the agent execute this workflow end-to-end with a mocked tool?).
- Agents have eval suites (does Claude pick the right workflow given a noisy user prompt?).

## Operating principles

**Build tools first, agents second.** When you face a new domain, the first instinct is to "ask the LLM to figure it out." Resist. Spend an hour writing a tool that captures the deterministic part. The agent's job becomes 10x easier.

**Workflows compound.** Every time the agent learns something new — a rate limit, a quirk, a smarter way to do a thing — update the workflow. Future sessions inherit the lesson. This is exactly the same pattern as the Karpathy LLM-wiki for knowledge: the SOPs become a living, compounding library of how to do things well.

**Don't let agents accumulate hidden state.** If the agent has a quirk it remembers from earlier in the session ("oh right, this user prefers X"), promote it to a written convention in `references/conventions.md`. Otherwise it disappears at session end.

**Tools should fail loudly.** Silent failures are how AI agents end up in confused states. A tool that returns `None` when something's wrong is worse than one that raises an exception with a clear message.

**One tool per file, one workflow per file.** Easy to find, easy to diff, easy for the agent to load only what it needs.

## The tradeoff

WAT trades upfront work (writing tools, writing workflows) for downstream reliability and speed. The first time you build something is slower; the tenth time is much faster because the layers compound.

If you're prototyping, this overhead may not be worth it — just let the agent do everything and accept the messiness. But for anything operational (a system that runs every day, a workflow you'll repeat 50 times, a knowledge base that needs to stay coherent for years), the WAT split pays for itself within a week.

## Further reading

- The original framing of WAT predates KAGE — it's a general pattern for AI-driven engineering systems. Variations exist as "agent + tools + memory" or "planner + executor + critic" architectures in the AI agent literature.
- KAGE's expression of WAT is documented in `~/.claude/skills/kage/SKILL.md`.
- The companion philosophies — Bottom Up for Understanding, the Flywheel, Clean Separation — are in `philosophies.md`. Together with WAT they form the four operating ideas behind KAGE.
