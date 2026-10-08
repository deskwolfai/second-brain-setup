# Obsidian setup

## Install and open

1. Download Obsidian from https://obsidian.md. It's free for personal use.
2. Launch it, choose **Open folder as vault**, and pick the 2nd brain folder.
3. Go to **Settings → Core plugins** and turn on **Daily notes** and **Templates**. The vault already ships settings pointing them at:
   - Daily notes folder `Journal`, format `YYYY/MM/YYYY-MM-DD`, template `_Templates/Daily Note`
   - Templates folder `_Templates`
   - New notes land in `00 Inbox`
4. Optional: in the **Files and links** settings, keep "Automatically update internal links" on, so renames don't break links.

## Using it with Claude Code

- Open a terminal in the vault folder and run `claude`. Claude reads `CLAUDE.md` and the guides, and the `second-brain` skill handles filing.
- Obsidian and Claude edit the same files. Obsidian picks up Claude's changes live.

## Backups (do this, day one)

Nothing is backed up until you choose an option:

- **Obsidian Sync** (paid; end-to-end encryption available). Keep the encryption password somewhere safe outside the vault.
- **A cloud folder** (iCloud, OneDrive, Dropbox, Google Drive). Put the vault inside it. Simple, but avoid opening the same vault on two devices at the same moment.
- **Git, kept private.** If you put the vault in a git repo, the remote **must be private**. A 2nd brain should never be in a public repo.

For any sync option, check what's excluded **before** the first upload. Files already uploaded stay on the remote even if you exclude them later.

## Optional community plugins

None are required. Some useful ones: Calendar (journal navigation) and Dataview (queries over frontmatter). Install community plugins only from authors you trust.
