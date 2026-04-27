"""
Obsidian helper module — clean primitives for the BUNSHIN vault.

Vault lookup order:
    1. os.environ["BUNSHIN_VAULT"]
    2. Raises RuntimeError if unset.

Why this exists: Obsidian is filesystem-based markdown, so "API" = read/write
.md files. But doing it naively loses YAML frontmatter, breaks wikilinks, or
scatters notes outside the conventions. This module enforces the schema.

If BUNSHIN_VAULT is unset, every function raises a clear error. Users who don't
maintain a local vault simply don't call these functions — the ClickUp half of
the skill still works.

CLI usage:
    python obsidian.py search "<term>"
    python obsidian.py read "Connections/<name>"
    python obsidian.py append "Entities/<slug>/index" "## New note\n\n..."
    python obsidian.py create "Decisions/<date> <slug>" --body "..."
    python obsidian.py today                        # today's journal path
    python obsidian.py whoami                       # vault sanity check
    python obsidian.py link "Connections/<name>"    # emit obsidian:// URI

Importable usage:
    import obsidian
    note = obsidian.read("Connections/<name>")
    obsidian.append("Entities/<slug>/index",
                    "\n## Status — <date>\n\nThing happened.\n")
    obsidian.create("Decisions/<date> <slug>",
                    body="...", frontmatter={"type":"decision","date":"<date>"})
    hits = obsidian.search("<term>")
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.parse
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

_VAULT_ENV = os.environ.get("BUNSHIN_VAULT", "")
VAULT = Path(_VAULT_ENV).expanduser() if _VAULT_ENV else None
VAULT_NAME = os.environ.get("BUNSHIN_VAULT_NAME") or (VAULT.name if VAULT else "BUNSHIN")

# Obsidian-illegal characters for filenames on Windows + cross-platform safety.
_ILLEGAL_FS = set('/\\:*?"<>|')


def _ensure_vault() -> Path:
    if VAULT is None:
        raise RuntimeError(
            "BUNSHIN_VAULT environment variable is not set. "
            "Set it to the absolute path of your Obsidian vault, or "
            "add BUNSHIN_VAULT=/path/to/vault to ~/.claude/skills/kage/.env."
        )
    if not VAULT.exists():
        raise RuntimeError(f"Obsidian vault not found at {VAULT}")
    return VAULT


def _resolve(note_ref: str) -> Path:
    """
    Turn a note reference into an absolute .md path. Accepts:
    - Relative path without extension: "Connections/First Last"
    - Relative path with extension:    "Connections/First Last.md"
    - Bare title:                      "First Last"   (searches vault)
    """
    p = note_ref.strip().lstrip("/").replace("\\", "/")
    if not p.endswith(".md"):
        p_with_ext = p + ".md"
    else:
        p_with_ext = p

    direct = VAULT / p_with_ext
    if direct.exists():
        return direct

    # Bare title fallback — search by filename across vault.
    target = p_with_ext.split("/")[-1].lower()
    for md in VAULT.rglob("*.md"):
        if md.name.lower() == target:
            return md

    # Not found — return the most plausible path so caller can decide.
    return direct


def _sanitize_segment(segment: str) -> str:
    return "".join("_" if ch in _ILLEGAL_FS else ch for ch in segment).strip() or "untitled"


def _split_frontmatter(text: str) -> tuple[dict, str]:
    """Split ---yaml--- frontmatter from body. Returns (frontmatter_dict, body)."""
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    raw = text[4:end]
    body = text[end + 5 :]
    fm: dict = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm, body


def _render_frontmatter(fm: dict) -> str:
    if not fm:
        return ""
    lines = ["---"]
    for k, v in fm.items():
        if isinstance(v, (list, tuple)):
            lines.append(f"{k}:")
            for item in v:
                lines.append(f"  - {item}")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def read(note_ref: str) -> dict:
    """Read a note. Returns {path, frontmatter, body, exists, size_bytes}."""
    _ensure_vault()
    path = _resolve(note_ref)
    if not path.exists():
        return {"path": str(path.relative_to(VAULT)) if path.is_relative_to(VAULT) else str(path),
                "exists": False, "frontmatter": {}, "body": "", "size_bytes": 0}
    text = path.read_text(encoding="utf-8")
    fm, body = _split_frontmatter(text)
    return {
        "path": str(path.relative_to(VAULT)),
        "exists": True,
        "frontmatter": fm,
        "body": body,
        "size_bytes": len(text.encode("utf-8")),
    }


def write(note_ref: str, body: str, frontmatter: dict | None = None) -> dict:
    """Overwrite a note. Creates parent dirs. Returns read() of the written note."""
    _ensure_vault()
    path = _resolve(note_ref)
    if not path.suffix:
        path = path.with_suffix(".md")
    path.parent.mkdir(parents=True, exist_ok=True)
    text = (_render_frontmatter(frontmatter or {}) + body).rstrip() + "\n"
    path.write_text(text, encoding="utf-8")
    return read(str(path.relative_to(VAULT)))


def create(note_ref: str, body: str = "", frontmatter: dict | None = None,
           *, overwrite: bool = False) -> dict:
    """Create a new note. Raises if exists unless overwrite=True."""
    _ensure_vault()
    path = _resolve(note_ref)
    if not path.suffix:
        path = path.with_suffix(".md")
    if path.exists() and not overwrite:
        raise FileExistsError(f"Note already exists: {path.relative_to(VAULT)}")
    return write(str(path.relative_to(VAULT)) if path.is_relative_to(VAULT) else str(path),
                 body, frontmatter)


def append(note_ref: str, content: str) -> dict:
    """Append content to a note. Creates the note if missing."""
    _ensure_vault()
    path = _resolve(note_ref)
    if not path.suffix:
        path = path.with_suffix(".md")
    if path.exists():
        text = path.read_text(encoding="utf-8")
        if not text.endswith("\n"):
            text += "\n"
        path.write_text(text + content + ("\n" if not content.endswith("\n") else ""),
                        encoding="utf-8")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content + ("\n" if not content.endswith("\n") else ""),
                        encoding="utf-8")
    return read(str(path.relative_to(VAULT)))


def search(query: str, *, fulltext: bool = True, limit: int = 50) -> list[dict]:
    """
    Search the vault. If fulltext=True, greps inside note bodies as well as filenames.
    Returns [{path, title, matches: [{line_no, text}], score}, ...] sorted by score desc.
    """
    _ensure_vault()
    q = query.lower()
    results: list[dict] = []
    for md in VAULT.rglob("*.md"):
        # Skip hidden / vault-internal
        if any(part.startswith(".") for part in md.relative_to(VAULT).parts):
            continue
        rel = md.relative_to(VAULT).as_posix()
        title = md.stem
        score = 0
        matches: list[dict] = []

        if q in title.lower():
            score += 100
        if fulltext:
            try:
                text = md.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                text = ""
            for i, line in enumerate(text.splitlines(), start=1):
                if q in line.lower():
                    score += 1
                    if len(matches) < 5:
                        matches.append({"line_no": i, "text": line.strip()[:200]})

        if score:
            results.append({"path": rel, "title": title, "matches": matches, "score": score})

    results.sort(key=lambda r: -r["score"])
    return results[:limit]


def list_folder(folder_ref: str) -> list[dict]:
    """List immediate children (files + subfolders) of a vault folder."""
    _ensure_vault()
    p = VAULT / folder_ref if folder_ref else VAULT
    if not p.exists():
        return []
    out: list[dict] = []
    for child in sorted(p.iterdir()):
        rel = child.relative_to(VAULT).as_posix()
        if child.is_dir():
            out.append({"type": "folder", "path": rel, "name": child.name})
        elif child.suffix == ".md":
            out.append({"type": "note", "path": rel, "name": child.stem})
    return out


def obsidian_uri(note_ref: str) -> str:
    """Return an obsidian:// URI that opens the note in Obsidian desktop."""
    rel = note_ref.replace("\\", "/")
    if rel.endswith(".md"):
        rel = rel[:-3]
    return f"obsidian://open?vault={urllib.parse.quote(VAULT_NAME)}&file={urllib.parse.quote(rel)}"


def today_journal_path() -> str:
    """Vault-relative path for today's daily journal note (Journal/YYYY/MM - Month/DD - Weekday.md)."""
    now = datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m - %B")
    day = now.strftime("%d - %A")
    return f"Journal/{year}/{month}/{day}"


def ensure_today_journal() -> dict:
    """Ensure today's journal exists (empty stub if new). Returns read()."""
    path = today_journal_path()
    p = _resolve(path)
    if not p.suffix:
        p = p.with_suffix(".md")
    if not p.exists():
        today = datetime.now()
        fm = {
            "type": "journal",
            "date": today.strftime("%Y-%m-%d"),
            "weekday": today.strftime("%A"),
        }
        create(path, body=f"# {today.strftime('%A, %B %d %Y')}\n\n", frontmatter=fm)
    return read(path)


def whoami() -> dict:
    """Sanity check — vault exists, readable, note count."""
    _ensure_vault()
    md_count = sum(1 for _ in VAULT.rglob("*.md"))
    total_bytes = sum(p.stat().st_size for p in VAULT.rglob("*.md"))
    return {
        "vault": str(VAULT),
        "vault_name": VAULT_NAME,
        "note_count": md_count,
        "total_bytes": total_bytes,
        "exists": True,
    }


# ---------------------------------------------------------------------------
# Wikilinks & refs
# ---------------------------------------------------------------------------

_WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#([^\]|]+))?(?:\|([^\]]+))?\]\]")


def extract_wikilinks(text: str) -> list[dict]:
    """Extract all [[WikiLinks]] from text. Returns [{target, section, alias}, ...]."""
    out: list[dict] = []
    for m in _WIKILINK_RE.finditer(text):
        out.append({"target": m.group(1).strip(),
                    "section": (m.group(2) or "").strip() or None,
                    "alias": (m.group(3) or "").strip() or None})
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _print_json(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def _cli(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    cmd, *rest = argv
    try:
        if cmd == "whoami":
            _print_json(whoami())
            return 0
        if cmd == "search":
            if not rest:
                print("usage: obsidian.py search <query> [limit]")
                return 1
            limit = int(rest[1]) if len(rest) > 1 else 50
            for r in search(rest[0], limit=limit):
                print(f"{r['score']:>4}  |  {r['path']}")
                for m in r["matches"][:2]:
                    print(f"        L{m['line_no']}: {m['text']}")
            return 0
        if cmd == "read":
            if not rest:
                print("usage: obsidian.py read <note_ref>")
                return 1
            n = read(rest[0])
            if n.get("frontmatter"):
                print(_render_frontmatter(n["frontmatter"]))
            print(n.get("body", ""))
            return 0
        if cmd == "append":
            if len(rest) < 2:
                print('usage: obsidian.py append <note_ref> "<content>"')
                return 1
            n = append(rest[0], rest[1])
            print(f"appended to {n['path']} ({n['size_bytes']} B)")
            return 0
        if cmd == "create":
            if not rest:
                print('usage: obsidian.py create <note_ref> [--body "..."]')
                return 1
            body = ""
            if "--body" in rest:
                idx = rest.index("--body")
                body = rest[idx + 1] if len(rest) > idx + 1 else ""
            n = create(rest[0], body=body)
            print(f"created {n['path']}")
            return 0
        if cmd == "ls":
            folder = rest[0] if rest else ""
            for item in list_folder(folder):
                print(f"{item['type']:<6}  {item['path']}")
            return 0
        if cmd == "today":
            print(today_journal_path())
            return 0
        if cmd == "link":
            if not rest:
                print("usage: obsidian.py link <note_ref>")
                return 1
            print(obsidian_uri(rest[0]))
            return 0
        print(f"unknown command: {cmd}")
        print(__doc__)
        return 1
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(_cli(sys.argv[1:]))
