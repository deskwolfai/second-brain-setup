# The Three Philosophies (and the $80K Rule)

Three operating principles plus one deployment rule. Together with the WAT framework (`wat-framework.md`), they're the four ideas every workflow, tool, and decision in KAGE assumes. This doc is the canonical agnostic version.

## Philosophy 1 — Bottom Up for Understanding, Top Down for Speed

**Never automate what you don't understand.** Build by hand first, prove a small case works, then wrap in a tool. The shortcut only has value once you know what's underneath.

The trap: AI makes it tempting to skip the foundation. Why learn the ClickUp API when Claude can "figure it out"? Why understand the Karpathy wiki pattern when the LLM can just "manage your notes"? Why grok how rate limiting works when there's a library for it?

Because **when something breaks — and it will — the foundation of understanding is what lets you fix it.** Without that foundation, you're not debugging; you're guessing. The shortcut hid the complexity, and now you can't see the bug.

In KAGE specifically, this philosophy IS **the Karpathy LLM-wiki pattern itself.** Read the source. Discuss the takeaways with the LLM. Then write the summary. Don't dump raw text and call it a wiki — the bookkeeping that makes a wiki useful only works because the LLM (and the human) actually engaged with the content.

**In practice for AI-assisted work:**

- Don't accept code from an AI without reading it.
- Don't run a generated SQL query without understanding what it does.
- Don't ingest a 200-page document into your wiki and then ask "what does it say" — that's RAG, not synthesis.
- When evaluating a new tool/library/framework, do one manual run before adopting the abstraction. Even when the manual run is slower.
- When something breaks, resist "ask the AI to fix it." Read the error. Form a hypothesis. *Then* ask the AI for help if needed.

**Top-down speed earns its keep only after bottom-up understanding has built the floor.** Once you understand a workflow, automate it. Once you understand an API's quirks, wrap it in a tool. Once you understand a decision, file it as a wiki page that future-you can lean on.

The philosophy is bidirectional: never skip the bottom step, but also don't stop at the bottom forever. Build up; then build down on top of it.

## Philosophy 2 — The Flywheel

**Every output is the next system's input.** Don't build dead-end systems. The best architecture is a snake biting its own tail — each piece of work feeds, upgrades, supports, or improves something else in the ecosystem.

This is how compounding value works:

```
Research tool produces insights
  → Insights feed a content workflow
  → Content drives engagement
  → Engagement data feeds back into better research
  → ...
```

The loop never stops. Each pass through makes the whole system stronger.

Even at the point of "final delivery," the flywheel continues. Delivered work feeds into a review process that improves the tools, sharpens the workflows, and raises the quality of the next deliverable. There is no true endpoint — only the next revolution.

**KAGE's flywheel:**

```
Source (article / conversation / decision)
  → BUNSHIN ingest (raw + summary + entity update + log update)
  → surfaces during a future query (Workflow 6)
  → grounds a decision or task creation
  → task lands in GAMBATTE with a bunshin_ref backlink
  → completed task generates a comment / result
  → result is filed back as a wiki page (Workflow 8)
  → becomes a source for the next ingest
```

**Flywheel opportunities are flag-able.** When you spot a manual gap in the loop — an analysis Claude produced that didn't get filed back, a closed task whose result didn't update the entity page, a decision that didn't propagate into the affected entity's index — that's not a feature. It's a leak. Flag it and close it.

**In practice for any system:**

- When building a tool, ask: what consumes this output next? Design outputs as inputs.
- Don't build isolated one-shot systems. Connect them.
- A tool that produces a report should produce it in a format another tool can read (markdown for Claude, JSON for code, never PDF unless a human is the only consumer).
- When a workflow reaches its "final" output, route it to a review or feedback loop that improves the process for next time.
- Shared data structures (JSON files, vault indexes, manifests) exist specifically to enable this — one system writes, many systems read.
- If you notice a manual step connecting two automated systems, **that gap is a flywheel opportunity**. Flag it. Close it.

The flywheel is what separates a *collection of automation scripts* from a *system that compounds.*

## Philosophy 3 — Clean Separation, Zero Entanglement

**No circular dependencies. Each module extractable standalone. Every import path gets one clean rewrite.**

This is how you keep a system modular and portable. Every tool, folder, and integration should be self-contained enough that you could pull it out of this repo, drop it into another project, and it works — no surgery required.

Dependencies flow in one direction: foundational layers at the bottom, specialized tools on top. Nothing at the bottom reaches up; nothing at the top tangles sideways into an unrelated domain.

**This isn't just code hygiene — it's what makes systems durable.** If a tool breaks, the blast radius is its folder and its consumers, not the whole system. When you reorganize, rename, or upgrade a module, every import path changes exactly once, in exactly the places you'd expect. When you onboard a new collaborator, they can understand one folder without first understanding the whole repo.

**KAGE's expression of this is the CQRS split** (Command Query Responsibility Segregation): BUNSHIN owns reads (knowledge); GAMBATTE owns writes (active work). They share **URIs as a bridge, never schema**. That's why "don't dual-write" is a hard rule — putting a task into both Obsidian and ClickUp re-tangles them, and now changes have to ripple in two directions to stay consistent.

Inside the kage skill, the same rule:

- `obsidian.py` does not import from `clickup.py`. They share nothing but the vault path used for `bunshin_ref` URIs.
- `waves.py` depends on `clickup.py` (it's the batched layer above immediate writes). The dependency never reverses.
- `references/` holds doctrine. `scripts/` holds execution. `manifest.json` holds routing data. None of these reach sideways into each other.

If you ever want to "make BUNSHIN call ClickUp directly" or "let a wave op write a BUNSHIN page" — stop. Bridge with a URL, not a function call. The URL bridge survives schema changes; a function call doesn't.

**In practice for any codebase:**

- Dependencies flow downward: `core/` depends on nothing, everything else depends on `core/`, no folder imports from a sibling unless there's an explicit, documented reason.
- Every folder has an entry point (an `__init__.py`, an `index.ts`, a `mod.rs`) that exports its public API. Consumers import from the folder, not from individual files buried inside it.
- Before adding a cross-folder import, ask: does this create a cycle? If yes, refactor — move the shared piece down to a foundational layer or restructure the dependency.
- When building new tools, place them in the folder that matches their domain. If they don't fit, that's a signal to create a new folder — not to dump them at the root.
- Test portability: if you can't `import tools.<folder>` (or `from .tools import <folder>`) without dragging the whole repo, something is coupled that shouldn't be.

## The $80K Rule

Before any deployment that calls a metered API, ask:

> **"If this endpoint got hit 1 million times tonight, what would it cost?"**

If the answer isn't bounded — circuit breaker, daily cap, kill switch, hard provider limit — **don't ship.**

This is the deployment doctrine. It applies to every API that bills per call:

| Provider | Why it matters |
|---|---|
| **OpenAI / Anthropic** | LLM completions can run $0.10+ per call at scale; a bad loop is $1000s/hour |
| **Stripe** | Webhook abuse can rack up processor fees |
| **Twilio** | SMS / voice calls bill per message and per minute |
| **ElevenLabs** | TTS bills per character; long generations get expensive fast |
| **Vercel / Render / Fly** | Compute scales linearly; runaway functions = runaway bills |
| **Google Cloud / AWS / Azure** | Egress, function invocations, storage I/O — many billable surfaces |
| **ClickUp / Notion / Airtable** | API quotas; exceeding them throttles or breaks integrations |

The $80K name comes from the public horror stories — startups waking up to five-figure bills because a single endpoint went into a loop or got attacked. Every story is preventable. The fix is always "we should have had a hard cap."

**Defense in depth — no single layer is enough:**

1. **Provider-side hard caps.** Most APIs let you set a billing limit. Use it. This is the fail-safe of last resort.
2. **Circuit breakers in your code.** Track spend per day, per hour, per endpoint. Auto-disable when caps are reached.
3. **Rate limiting at the edge.** Don't let a malicious user even reach your expensive code paths.
4. **Anomaly detection.** Spend going 10x normal in an hour? Page someone.
5. **Daily cost digest.** Even if nothing's wrong, see today's spend in one place.

**For KAGE specifically**, the $80K rule is mostly inapplicable — Obsidian is filesystem-only, and ClickUp's API is friendly (~100 req/min, no per-call cost beyond your subscription). The KAGE-flavored equivalent is:

> **"If this wave or write hits the wrong list / space / note, how much does the user have to clean up by hand?"**

If the answer isn't bounded — wave queue is too big to review, write goes to a destructive endpoint, op affects shared resources — ask before flushing. The wave system exists precisely so the answer can stay "nothing" most of the time.

## How the four ideas relate

```
                        WAT Framework
                  (Workflows · Agents · Tools)
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
  Bottom Up for         The Flywheel       Clean Separation,
  Understanding,                            Zero Entanglement
  Top Down for Speed
                              │
                              ▼
                       The $80K Rule
                  (deployment safety floor)
```

WAT is the **architecture**. The three philosophies are the **operating principles** that govern how the architecture should grow over time. The $80K rule is the **safety floor** that catches the rare case where reasoning fails.

Together they describe a system that:

- Stays reliable as it grows (WAT's separation of concerns).
- Earns its abstractions instead of guessing them (Bottom Up).
- Compounds in value rather than collecting cruft (Flywheel).
- Stays modular and portable (Clean Separation).
- Doesn't burn the building down on a bad night (the $80K Rule).

KAGE is one example of a system built on these. The same four ideas apply to any AI-augmented operational system you might build next.
