"""
ClickUp helper module — clean primitives for GAMBATTE on ClickUp.

Architecture:
    Workspace (Team)
      Space   = a domain (a business, a project, "Personal", or "Inbox")
        List  = a category within that domain (a department, a pillar, etc.)
          Task = the actual work

Each top-level domain gets its own Space (so it can have its own statuses,
custom fields, dashboards, permissions, automations). The shape of your
Spaces and Lists is captured in manifest.json — generated during bootstrap.

Credentials (looked up in this order):
    1. os.environ["CLICKUP_API_KEY"] / os.environ["CLICKUP_TEAM_ID"]
    2. .env in the skill dir (~/.claude/skills/kage/.env)
    3. .env in cwd

Manifest (looked up in this order):
    1. os.environ["CLICKUP_MANIFEST"]
    2. manifest.json one dir up from this file (~/.claude/skills/kage/manifest.json)

CLI:
    python clickup.py whoami
    python clickup.py teams
    python clickup.py spaces
    python clickup.py manifest
    python clickup.py add-task "Title" Must "<Space Name>" "<List Name>"
    python clickup.py musts
    python clickup.py search "<term>"

Importable:
    import clickup
    clickup.add_task("Ship the pricing page", priority="Must",
                      space="Work", list_name="FULFILLMENT")
    clickup.add_task("Schedule physical", pillar="Health")
    clickup.add_task("Random thought to triage")

Priority mapping:
    Must -> 1 (Urgent), Should -> 2 (High), Could -> 4 (Low)
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE = "https://api.clickup.com/api/v2"
_TOKEN_CACHE: str | None = None
_ENV_CACHE: dict[str, str] | None = None
_LAST_REQUEST_TS: float = 0.0
_MIN_INTERVAL = 0.65  # ~100/min ceiling, leave headroom

PRIORITY_TO_INT = {"Must": 1, "Should": 2, "Normal": 3, "Could": 4}
PRIORITY_FROM_INT = {1: "Must", 2: "Should", 3: "Normal", 4: "Could", None: None}

INBOX_SPACE = "Inbox"
INBOX_LIST = "Quick Capture"
PERSONAL_SPACE = "Personal"

_MANIFEST_CACHE: dict | None = None


def _skill_dir() -> Path:
    # <skill_root>/scripts/clickup.py -> <skill_root>
    return Path(__file__).resolve().parent.parent


def _env_candidates() -> list[Path]:
    return [
        _skill_dir() / ".env",
        Path.cwd() / ".env",
    ]


def _load_env() -> dict[str, str]:
    global _ENV_CACHE
    if _ENV_CACHE is not None:
        return _ENV_CACHE
    out: dict[str, str] = {}
    for env_path in _env_candidates():
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
            break
    # Process env always wins (so a teammate can override without touching files).
    for k, v in os.environ.items():
        if k.startswith("CLICKUP_") or k == "BUNSHIN_VAULT":
            out[k] = v
    _ENV_CACHE = out
    return out


def _token() -> str:
    global _TOKEN_CACHE
    if _TOKEN_CACHE:
        return _TOKEN_CACHE
    tok = _load_env().get("CLICKUP_API_KEY", "").strip()
    if not tok:
        raise RuntimeError(
            "CLICKUP_API_KEY missing. Set the env var, or copy "
            "kage/.env.example to ~/.claude/skills/kage/.env and fill it in."
        )
    _TOKEN_CACHE = tok
    return tok


def _team_id() -> str:
    t = _load_env().get("CLICKUP_TEAM_ID", "").strip()
    if not t:
        raise RuntimeError("CLICKUP_TEAM_ID missing. Run `python clickup.py teams` and set it in .env.")
    return t


def _manifest_path() -> Path:
    env = _load_env().get("CLICKUP_MANIFEST", "").strip()
    if env:
        return Path(env).expanduser()
    return _skill_dir() / "manifest.json"


def manifest(refresh: bool = False) -> dict:
    """Read the bootstrap manifest produced by setup_workspace.py."""
    global _MANIFEST_CACHE
    if not refresh and _MANIFEST_CACHE is not None:
        return _MANIFEST_CACHE
    p = _manifest_path()
    _MANIFEST_CACHE = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    return _MANIFEST_CACHE


def _throttle() -> None:
    global _LAST_REQUEST_TS
    elapsed = time.time() - _LAST_REQUEST_TS
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)
    _LAST_REQUEST_TS = time.time()


def _request(method: str, path: str, *, json_body=None, query: dict | None = None) -> tuple[int, bytes]:
    _throttle()
    url = f"{BASE}{path}" if path.startswith("/") else f"{BASE}/{path}"
    if query:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(query, doseq=True)
    headers = {"Authorization": _token(), "accept": "application/json"}
    data: bytes | None = None
    if json_body is not None:
        data = json.dumps(json_body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def _request_json(method: str, path: str, **kwargs) -> dict:
    status, body = _request(method, path, **kwargs)
    if status == 429:
        time.sleep(2.0)
        status, body = _request(method, path, **kwargs)
    if not (200 <= status < 300):
        raise RuntimeError(f"{method} {path} -> {status}: {body.decode('utf-8', 'replace')}")
    return json.loads(body.decode("utf-8")) if body else {}


# ---------------------------------------------------------------------------
# Hierarchy primitives
# ---------------------------------------------------------------------------

def whoami() -> dict:
    return _request_json("GET", "/user")


def teams() -> list[dict]:
    return _request_json("GET", "/team").get("teams", [])


def spaces(team_id: str | None = None) -> list[dict]:
    return _request_json("GET", f"/team/{team_id or _team_id()}/space",
                         query={"archived": "false"}).get("spaces", [])


def get_space(space_id: str) -> dict:
    return _request_json("GET", f"/space/{space_id}")


def create_space(name: str, team_id: str | None = None) -> dict:
    body = {
        "name": name,
        "multiple_assignees": True,
        "features": {
            "due_dates": {"enabled": True, "start_date": True,
                          "remap_due_dates": False, "remap_closed_due_date": False},
            "time_tracking": {"enabled": True},
            "tags": {"enabled": True},
            "time_estimates": {"enabled": True},
            "checklists": {"enabled": True},
            "custom_fields": {"enabled": True},
            "remap_dependencies": {"enabled": True},
            "dependency_warning": {"enabled": True},
            "portfolios": {"enabled": True},
            "priorities": {"enabled": True},
        },
    }
    return _request_json("POST", f"/team/{team_id or _team_id()}/space", json_body=body)


def delete_space(space_id: str) -> None:
    status, body = _request("DELETE", f"/space/{space_id}")
    if not (200 <= status < 300):
        raise RuntimeError(f"DELETE space {space_id} -> {status}: {body.decode('utf-8', 'replace')}")


def folders(space_id: str) -> list[dict]:
    return _request_json("GET", f"/space/{space_id}/folder",
                         query={"archived": "false"}).get("folders", [])


def create_folder(space_id: str, name: str) -> dict:
    return _request_json("POST", f"/space/{space_id}/folder", json_body={"name": name})


def lists_in_folder(folder_id: str) -> list[dict]:
    return _request_json("GET", f"/folder/{folder_id}/list",
                         query={"archived": "false"}).get("lists", [])


def lists_in_space(space_id: str) -> list[dict]:
    return _request_json("GET", f"/space/{space_id}/list",
                         query={"archived": "false"}).get("lists", [])


def create_list(folder_id: str, name: str) -> dict:
    return _request_json("POST", f"/folder/{folder_id}/list", json_body={"name": name})


def create_folderless_list(space_id: str, name: str) -> dict:
    return _request_json("POST", f"/space/{space_id}/list", json_body={"name": name})


# ---------------------------------------------------------------------------
# Task primitives
# ---------------------------------------------------------------------------

def get_task(task_id: str) -> dict:
    return _request_json("GET", f"/task/{task_id}")


def list_tasks(list_id: str, *, include_closed: bool = False,
               page: int = 0, max_pages: int = 20) -> list[dict]:
    out: list[dict] = []
    for p in range(page, page + max_pages):
        resp = _request_json("GET", f"/list/{list_id}/task",
                             query={"archived": "false",
                                    "include_closed": "true" if include_closed else "false",
                                    "page": str(p)})
        batch = resp.get("tasks", [])
        if not batch:
            break
        out.extend(batch)
        if resp.get("last_page") is True:
            break
    return out


def create_task(list_id: str, name: str, *,
                description: str | None = None,
                priority: str | int | None = None,
                status: str | None = None,
                due: int | None = None,
                tags: list[str] | None = None,
                assignees: list[int] | None = None) -> dict:
    body: dict = {"name": name}
    if description is not None:
        body["description"] = description
    if priority is not None:
        body["priority"] = PRIORITY_TO_INT[priority] if isinstance(priority, str) else priority
    if status is not None:
        body["status"] = status
    if due is not None:
        body["due_date"] = due
    if tags:
        body["tags"] = tags
    if assignees:
        body["assignees"] = assignees
    return _request_json("POST", f"/list/{list_id}/task", json_body=body)


def update_task(task_id: str, **fields) -> dict:
    if "priority" in fields and isinstance(fields["priority"], str):
        fields["priority"] = PRIORITY_TO_INT[fields["priority"]]
    return _request_json("PUT", f"/task/{task_id}", json_body=fields)


def update_task_status(task_id: str, status: str) -> dict:
    return update_task(task_id, status=status)


def delete_task(task_id: str) -> None:
    status, body = _request("DELETE", f"/task/{task_id}")
    if not (200 <= status < 300):
        raise RuntimeError(f"DELETE task {task_id} -> {status}: {body.decode('utf-8', 'replace')}")


def add_comment(task_id: str, text: str) -> dict:
    return _request_json("POST", f"/task/{task_id}/comment",
                         json_body={"comment_text": text, "notify_all": False})


def search(query: str, *, team_id: str | None = None) -> list[dict]:
    return _request_json("GET", f"/team/{team_id or _team_id()}/task",
                         query={"page": "0",
                                "order_by": "updated",
                                "search": query,
                                "include_closed": "true",
                                "subtasks": "true"}).get("tasks", [])


# ---------------------------------------------------------------------------
# GAMBATTE-specific routing (uses the manifest)
# ---------------------------------------------------------------------------

def space_id_for(space_name: str) -> str | None:
    return (manifest().get("spaces", {}).get(space_name) or {}).get("space_id")


def list_id_in(space_name: str, list_name: str) -> str | None:
    sp = manifest().get("spaces", {}).get(space_name)
    if not sp:
        return None
    return sp.get("lists", {}).get(list_name)


def all_space_ids() -> list[str]:
    return [sp["space_id"] for sp in manifest().get("spaces", {}).values() if sp.get("space_id")]


def add_task(name: str, priority: str = "Should", *,
             space: str | None = None,
             list_name: str | None = None,
             business: str | None = None,
             department: str | None = None,
             project: str | None = None,
             pillar: str | None = None,
             marketing_sub: str | None = None,
             bunshin_ref: str | None = None,
             description: str | None = None,
             status: str | None = None,
             tags: list[str] | None = None) -> dict:
    """
    Create a GAMBATTE task. Routes to the correct (Space, List) by:
      1. Explicit (space, list_name) — wins
      2. (business, department) — Space=business, List=department
      3. project — Space=project, List=FULFILLMENT (default for projects)
      4. pillar — Space=Personal, List=pillar
      5. Fallback — Space=Inbox, List=Quick Capture
    """
    sp = list_n = None

    if space and list_name:
        sp, list_n = space, list_name
    elif business and department:
        sp, list_n = business, department
    elif project:
        sp = project
        for default in ("FULFILLMENT", "MOBILE", "ROADMAP", "ADMIN"):
            if list_id_in(project, default):
                list_n = default
                break
        list_n = list_n or "FULFILLMENT"
    elif pillar:
        sp, list_n = PERSONAL_SPACE, pillar
    else:
        sp, list_n = INBOX_SPACE, INBOX_LIST

    list_id = list_id_in(sp, list_n)
    if not list_id:
        raise RuntimeError(f"No List ID resolved for Space='{sp}' List='{list_n}'. "
                           "Check manifest.json or ask the workspace admin.")

    final_tags: list[str] = list(tags or [])
    if marketing_sub:
        final_tags.append(marketing_sub.lower())

    desc = description or ""
    if bunshin_ref:
        desc = f"BUNSHIN: {bunshin_ref}\n\n{desc}".strip()

    return create_task(list_id, name,
                       description=desc or None,
                       priority=priority,
                       status=status,
                       tags=final_tags or None)


def list_musts(space: str | None = None) -> list[dict]:
    """Bounty board: every Urgent (Must) task across all GAMBATTE Spaces, optionally scoped."""
    space_ids = [space_id_for(space)] if space else all_space_ids()
    space_ids = [s for s in space_ids if s]
    if not space_ids:
        return []
    out: list[dict] = []
    for p in range(0, 20):
        resp = _request_json("GET", f"/team/{_team_id()}/task", query={
            "page": str(p),
            "priorities[]": ["1"],
            "include_closed": "false",
            "subtasks": "true",
            "space_ids[]": space_ids,
        })
        batch = resp.get("tasks", [])
        if not batch:
            break
        out.extend(batch)
        if len(batch) < 100:
            break
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
            _print_json(whoami()); return 0
        if cmd == "teams":
            for t in teams():
                print(f"{t['id']}  |  {t['name']}")
            return 0
        if cmd == "spaces":
            tid = rest[0] if rest else _team_id()
            for s in spaces(tid):
                print(f"{s['id']}  |  {s['name']}")
            return 0
        if cmd == "folders":
            for f in folders(rest[0]):
                print(f"{f['id']}  |  {f['name']}")
            return 0
        if cmd == "lists":
            target = rest[0]
            try:
                for l in lists_in_folder(target):
                    print(f"FOLDER {l['id']}  |  {l['name']}")
            except Exception:
                pass
            try:
                for l in lists_in_space(target):
                    print(f"SPACE  {l['id']}  |  {l['name']}")
            except Exception:
                pass
            return 0
        if cmd == "tasks":
            for t in list_tasks(rest[0], include_closed=True):
                pri = (t.get("priority") or {}).get("priority", "-") if t.get("priority") else "-"
                print(f"{t['id']}  |  [{pri}] {t['name']}  |  {t['status']['status']}")
            return 0
        if cmd == "add-task":
            if len(rest) < 1:
                print('usage: clickup.py add-task "Title" [Must|Should|Could] [Space] [List]')
                return 1
            name = rest[0]
            priority = rest[1] if len(rest) > 1 else "Should"
            sp = rest[2] if len(rest) > 2 else None
            ln = rest[3] if len(rest) > 3 else None
            t = add_task(name, priority=priority, space=sp, list_name=ln)
            _print_json({"id": t["id"], "url": t.get("url"), "name": t["name"]})
            return 0
        if cmd == "musts":
            for t in list_musts(rest[0] if rest else None):
                space_name = (t.get("space") or {}).get("name", "-")
                lst = (t.get("list") or {}).get("name", "-")
                print(f"[{space_name}/{lst}] {t['name']}")
            return 0
        if cmd == "search":
            for t in search(rest[0]):
                space_name = (t.get("space") or {}).get("name", "-")
                lst = (t.get("list") or {}).get("name", "-")
                print(f"{t['id']}  |  [{space_name}/{lst}] {t['name']}")
            return 0
        if cmd == "manifest":
            _print_json(manifest()); return 0
        if cmd == "delete-space":
            delete_space(rest[0]); print(f"deleted space {rest[0]}"); return 0
        print(f"unknown command: {cmd}")
        print(__doc__)
        return 1
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(_cli(sys.argv[1:]))
