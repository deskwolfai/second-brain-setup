---
name: second-brain
description: Set up and run a personal 2nd brain in Obsidian with Claude. Builds the vault (five life pillars, Inbox, Journal, DOCTRINES, Life Operations, Archive, an executive.md guide in every folder) and a CLAUDE.md that teaches every future Claude session how to work in it. Then operates it day to day. Use when the user says "set up my second brain", "set me up", "build my vault", "2nd brain", "capture this", "add to my inbox", "journal", "today's note", "log this", "file this", "add a person", "remember this about <name>", "add a doctrine", "weekly review", "clean up my inbox", "import my notes", or "new folder in my vault". Also use for any request to save, find, or organize something personal and durable.
---

# Second Brain

A personal knowledge vault in Obsidian that Claude can navigate. It is just folders of markdown files on the user's computer: no accounts, APIs, or keys. Obsidian is the window you read through; Claude does the bookkeeping.

**Read this file once when triggered, then act.** Load a reference only when the task needs it:

- [references/vault-layout.md](references/vault-layout.md) covers every folder: what goes where, plus edge cases.
- [references/executive-guides.md](references/executive-guides.md) covers the `executive.md` guide format and upkeep.
- [references/conventions.md](references/conventions.md) covers journal paths, people notes, labels, voice, and privacy.
- [references/obsidian-setup.md](references/obsidian-setup.md) covers installing Obsidian, opening the vault, settings, sync, and backups.

## The model in one breath

Every folder has an `executive.md`: a short guide saying what the folder is for, where to go next, and how to keep it current. A thin `CLAUDE.md` at the vault root points Claude at those guides and holds the owner's working rules. So any new Claude session can open the vault cold, read two or three guides, and land on the right notes without scanning everything.

```
<Name>'s 2nd Brain/
├── CLAUDE.md            ← Claude reads this on entry
├── executive.md         ← vault overview
├── 00 Inbox/            ← quick capture
├── Journal/YYYY/MM/YYYY-MM-DD.md
├── DOCTRINES/           ← adopted personal rules
├── Life Operations/     ← goals, routines, life admin
├── Happiness/  Health/  Love/  Wealth/  Wisdom/   ← the five pillars
├── 99 Archive/
└── _Templates/          ← Daily Note, Person, Doctrine, Folder Guide
```

## Workflow 1: Set up a new vault

Run this when the user asks to set up their 2nd brain. Confirm paths before writing; never overwrite an existing folder.

1. **Interview (short, one message).** Ask:
   - What name should the vault use? (It becomes "<Name>'s 2nd Brain".)
   - Where should it live? Default: a new folder named `<Name>'s 2nd Brain` inside their Documents folder.
   - Keep the five pillars (Happiness, Health, Love, Wealth, Wisdom) as they are, or rename or drop any? Default: keep.
   - Anything Claude should know about how you like to work? (Goes in CLAUDE.md under "Personal notes for Claude".) Optional.
   - Do you have existing notes to bring in? (Optional; see Workflow 8.)

   If the user says "just do it", use the defaults and their first name if known.

2. **Resolve and check the target.**
   - Turn the answer into a full absolute path before using it, and never pass a literal `~` inside quotes. To find Documents: on Windows, run `[Environment]::GetFolderPath('MyDocuments')` in PowerShell (it is often inside OneDrive); on macOS or Linux, use `$HOME/Documents`.
   - Show the user the full path and get a yes.
   - Never put the vault inside the second-brain-setup repo folder, or inside `~/.claude`.
   - If the folder exists and isn't empty, stop and ask. Options: pick another path, or merge (add only missing files, never replace).

3. **Copy the template.** The template lives at `templates/vault/` inside this skill (normally `~/.claude/skills/second-brain/templates/vault/`). Copy the whole tree, including the `.obsidian/` settings folder. Use the absolute `<target>` from step 2.
   - New folder, macOS/Linux/Git Bash: `cp -R "$HOME/.claude/skills/second-brain/templates/vault" "<target>"`
   - New folder, PowerShell: `Copy-Item -Recurse "$HOME\.claude\skills\second-brain\templates\vault" "<target>"`
   - Existing empty folder, macOS/Linux/Git Bash: `cp -R "$HOME/.claude/skills/second-brain/templates/vault/." "<target>/"`
   - Existing empty folder, PowerShell: `Copy-Item -Recurse -Force "$HOME\.claude\skills\second-brain\templates\vault\*" "<target>"`
   - Afterwards, confirm that `<target>/.obsidian/daily-notes.json` and `<target>/executive.md` both exist, and that nothing ended up nested as `<target>/vault/`.

4. **Fill tokens.** In every `.md` file under the target, replace `{{OWNER}}` with the name and `{{DATE}}` with today's date (YYYY-MM-DD). Leave Obsidian's own `{{date:...}}` and `{{title}}` tokens in `_Templates/` alone; Obsidian fills those. Afterwards, search for `{{OWNER}}` and `{{DATE}}` and confirm there are zero hits.

5. **Apply interview answers.**
   - A renamed pillar means renaming its folder, its principles note, and its guide title, plus every mention of it: the link in the root `executive.md`, the pillar list in that guide's TL;DR, and the **Five pillars** line in `CLAUDE.md`.
   - A dropped pillar means moving its folder to `99 Archive/`, not deleting it, then fixing the links.
   - Write the "how I like to work" answers under **Personal notes for Claude** in `CLAUDE.md`.

6. **Verify.** List the tree, open the root `executive.md` and `CLAUDE.md`, and check that every relative link resolves to a real file. Fix any broken link.

7. **Hand off.** Tell the user, in plain words:
   - Install Obsidian from https://obsidian.md if they don't have it. Choose **Open folder as vault** and pick the new folder.
   - In Obsidian, go to Settings → Core plugins and turn on **Daily notes** and **Templates**. The vault already points them at `Journal` and `_Templates`.
   - From now on, start Claude Code inside the vault folder (`cd` into it, then `claude`) so it reads `CLAUDE.md`.
   - Try it: "journal: today was…", "capture: idea for…", "add my friend Sam to my rolodex".
   - Set up backups (see `references/obsidian-setup.md`). Nothing is backed up yet.

## Creating notes from templates

Obsidian fills `{{title}}` and `{{date:...}}` only when the **user** inserts a template inside Obsidian. When Claude creates a note from a file in `_Templates/`, Claude replaces those tokens itself: `{{title}}` becomes the note name, and `{{date:YYYY-MM-DD}}` becomes today's date in that format. A saved note must never contain a raw `{{...}}` token.

## Workflow 2: Capture

"Capture / note / save / remember this" with no obvious home goes to `00 Inbox/` as a new note with a short descriptive title. Add a `captured: YYYY-MM-DD` line and the source if there is one. If the home **is** obvious (a person, a book, a health observation), file it there directly and say where it went.

## Workflow 3: Journal

- Today's note is `Journal/YYYY/MM/YYYY-MM-DD.md`. Create it from `_Templates/Daily Note.md` if it's missing, filling the date heading yourself, and append under the right section.
- Write what the user said in **their words**. Clean up structure only if asked. Never sand off tone or swearing.
- Reviews are `Journal/YYYY/MM/YYYY-MM-DD Weekly Review.md` (or Monthly or Yearly).
- If an entry mentions a person, goal, or doctrine, offer to link it. Don't silently edit other notes from a journal entry.

## Workflow 4: People

One note per person in `Love/Rolodex/<Category>/<First Last>.md`, made from the Person template. The categories are Family, Friends, Romance, Mentors, Colleagues, Acquaintances, and VIPs. Before creating a note, search the whole Rolodex for the name so you don't make a duplicate. "Remember X about Sam" appends a dated line under **Notes** and updates `last_connected` if they talked.

## Workflow 5: Doctrines and principles

- A rule the user has **explicitly adopted** becomes `DOCTRINES/<Rule name>.md` from the Doctrine template, in their words.
- Beliefs about a pillar go in that pillar's `<Pillar> — Principles.md`.
- An idea from a book is not a doctrine until the user adopts it. Keep it in `Wisdom/` and ask before promoting it.

## Workflow 6: File the inbox (weekly review)

1. List `00 Inbox/` and propose a destination for each item in one table: item → destination → action (move, merge, archive, delete).
2. Wait for the user's OK, adjusting as they say.
3. Move the files, update links, and refresh any affected `executive.md` guides.
4. Offer a weekly review note in Journal covering wins, open loops, and next actions.

## Workflow 7: New folder

When a topic outgrows a single note, make a subfolder and give it an `executive.md` from `_Templates/Folder Guide.md`. Then add it to the parent guide's **Where to go** list and add a change-log row. See `references/executive-guides.md`.

## Workflow 8: Import existing notes

1. Copy (don't move) the user's existing notes into `00 Inbox/Import YYYY-MM-DD/`.
2. Read before sorting. Propose destinations in batches as a table, and get an OK before moving anything.
3. Merge duplicates into one primary note, keeping the unique parts of each. Keep dates and sources.
4. Flag anything that looks like a password or key, and offer to remove it (see conventions).

## Always

- Search before creating, so each person, source, or topic has only one primary note.
- After filing anything, say the path you wrote to.
- Label anything not confirmed by the user as `proposed` or `unverified`.
- Never send, share, upload, or publish vault content without explicit OK in the current conversation.
- Ask before deleting, bulk-moving, or rewriting the user's own words.
