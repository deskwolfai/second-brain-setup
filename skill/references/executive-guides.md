# Executive guides (`executive.md`)

Every folder has one lowercase `executive.md`. It is a map, not a summary of contents: it tells a person or an AI what the folder is for and where to go next, so nobody has to scan the vault.

## Format

```markdown
# <Folder> — Executive summary

**Last reviewed:** YYYY-MM-DD

## TL;DR

One or two sentences: what this folder is for.

## Where to go

- [Child folder](<Child folder/executive.md>)
- [Key note](<Key note.md>)
- [Parent folder guide](<../executive.md>)

## Working context

- What belongs here and what doesn't, plus where the neighbors live.
- Rules specific to this folder (privacy, voice, naming).

## Keep this guide current

- Update when purpose, layout, or key notes change. Set Last reviewed after checking.

## Change log

| Date | Change | By |
| --- | --- | --- |
| YYYY-MM-DD | Created. | Claude |
```

Links use the `[Name](<relative path>)` form. The angle brackets let paths contain spaces and `&`, and the links work both in Obsidian and on GitHub.

## Rules

- **Read guides on the path to the task:** root, then pillar, then subfolder, then the actual notes. Verify against the notes before trusting a guide's summary.
- **Guides describe organization, not personal facts.** Don't put diagnoses, balances, or relationship details in a guide; those live in notes.
- **Not every note needs a guide.** Only folders get guides; individual notes, people, and journal days don't.
- **Update on change.** When you add, rename, move, or retire a folder or a key note, do four things:
  1. Update that folder's guide.
  2. Fix the parent guide's **Where to go**.
  3. Set **Last reviewed**.
  4. Add one change-log row saying what changed and why.
- **Keep earlier change-log rows.** Record completed changes, not promises.
- **Check links.** After any move, every relative link in the affected guides must point to a real file.
