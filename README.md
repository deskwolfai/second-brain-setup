# Second Brain Setup

A personal 2nd brain in [Obsidian](https://obsidian.md), set up and run by [Claude Code](https://docs.claude.com/en/docs/claude-code/overview).

You get a ready-made vault organized around five areas of life (**Happiness, Health, Love, Wealth, Wisdom**), plus an Inbox, a Journal, your personal rules (DOCTRINES), Life Operations, and an Archive. Every folder has a short guide (`executive.md`), so Claude can find its way around without reading everything. A `CLAUDE.md` at the top teaches every future Claude session how to work with you.

Your notes are plain markdown files on your own computer. The vault needs no extra accounts, API keys, or plugins.

## Set it up (about 5 minutes)

You need:

- A Claude subscription with [Claude Code](https://docs.claude.com/en/docs/claude-code/overview) installed
- [git](https://git-scm.com/downloads)
- [Obsidian](https://obsidian.md) (free)

To open a terminal: on Windows, right-click the Start button and choose **Terminal**. On a Mac, open the **Terminal** app. Then paste:

```bash
git clone https://github.com/deskwolfai/second-brain-setup.git
cd second-brain-setup
claude
```

Then tell Claude: **"set me up"**.

Claude will:

1. Install the `second-brain` skill into `~/.claude/skills/`.
2. Ask your name, where you want the vault, and whether to keep the five pillars as they are.
3. Build the vault and fill in your `CLAUDE.md`.
4. Walk you through opening it in Obsidian.

When it's done, you can delete this repo folder. The skill and your vault stay.

## Use it

Open a terminal in your vault folder, type `claude`, and just talk. To open a terminal in a folder:

- **Windows:** right-click the folder and choose **Open in Terminal**.
- **Mac:** right-click the folder and choose **Services → New Terminal at Folder**.

Some things to say:

- "journal: rough day, but the gym session was great"
- "capture: business idea, a dog-walking app for apartments"
- "add my cousin Maria to my rolodex, birthday is June 3"
- "I've decided: no phone for the first hour of the day. Make that a doctrine."
- "let's do a weekly review and clean out my inbox"
- "import my old notes from ~/Documents/Notes"

## What's inside

```
skill/
├── SKILL.md                 the operating manual Claude follows
├── references/              layout, guide format, conventions, Obsidian setup
└── templates/vault/         the starter vault, copied during setup
    ├── CLAUDE.md            Claude's entry file for your vault
    ├── executive.md         vault overview (every folder has one)
    ├── 00 Inbox/  Journal/  DOCTRINES/  Life Operations/  99 Archive/  _Templates/
    └── Happiness/  Health/  Love/  Wealth/  Wisdom/
```

## Make it yours

Rename, drop, or add folders whenever you want. Just ask Claude, and it will keep the guides and links in sync. Put your preferences in the **Personal notes for Claude** section at the bottom of your vault's `CLAUDE.md`.

## Keep it private

Your vault is personal. Back it up (Obsidian Sync, a cloud folder, or a **private** git repo), but never push it to a public repo. Don't store passwords or account numbers in it; write "in my password manager" instead.

## Manual install

If you'd rather not have Claude do the setup:

1. Copy `skill/` to `~/.claude/skills/second-brain/`.
2. Copy `skill/templates/vault/` to wherever you want your vault, and rename the folder.
3. In every `.md` file, replace `{{OWNER}}` with your name and `{{DATE}}` with today's date. Leave the `{{date:...}}` and `{{title}}` tokens in `_Templates/` alone; Obsidian fills those in.
4. Open the folder in Obsidian, and turn on the **Daily notes** and **Templates** core plugins.

## License

MIT. See [LICENSE](LICENSE).
