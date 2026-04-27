"""
Waves — batched ClickUp updates.

KAGE writes to ClickUp at two speeds:

  * "as we go" — immediate writes that go straight to ClickUp (status flips,
    urgent single task creation, quick comments).
  * "in waves" — batched bursts of updates that queue locally first, then ship
    to ClickUp as a single coherent checkpoint.

Why waves? Obsidian is the user's fast-path (single user, filesystem speed,
Claude-native). ClickUp is the team + mobile + PM surface. Shipping every tiny
change to ClickUp creates chatty half-done state visible to collaborators.
Waves let Claude mutate Obsidian freely during a session, then hand ClickUp a
finished snapshot at the wave boundary.

A wave is:
  1. Queue ops during a session via queue_op(...) — they append to pending.jsonl
  2. Flush at a checkpoint via flush_wave() — executes each op against ClickUp,
     records results, moves completed ops out of pending
  3. Archive applied ops by wave timestamp for auditability

Pending / applied state lives in the BUNSHIN vault under .bunshin/waves/ if a
vault is configured (so the wave log travels with the knowledge it concerns).
Without a vault, state lives in <skill_root>/.waves/ as a fallback.

CLI usage:
    python waves.py queue create_task --name "<task title>" \\
        --space "<Space Name>" --list "<List Name>" --priority Must
    python waves.py pending                 # show pending ops
    python waves.py flush                   # ship pending to ClickUp
    python waves.py flush --dry-run         # preview without writing
    python waves.py applied 10              # last 10 applied waves

Importable usage:
    import waves
    waves.queue_op("create_task", name="<task title>", space="<Space>",
                   list_name="<List>", priority="Must")
    waves.queue_op("update_task_status", task_id="abc123", status="in progress")
    result = waves.flush_wave()      # executes everything pending
    print(result["applied"], "ops applied")
"""
from __future__ import annotations

import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# clickup.py now lives alongside this file in the skill's scripts/ dir.
_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import clickup  # noqa: E402

# Wave queue lives inside the user's Obsidian vault if one is configured;
# falls back to the skill folder so waves still work without an Obsidian vault.
_VAULT_ENV = os.environ.get("BUNSHIN_VAULT", "")
if _VAULT_ENV:
    VAULT = Path(_VAULT_ENV).expanduser()
    WAVES_DIR = VAULT / ".bunshin" / "waves"
else:
    VAULT = None
    WAVES_DIR = Path(__file__).resolve().parent.parent / ".waves"
PENDING_PATH = WAVES_DIR / "pending.jsonl"
APPLIED_DIR = WAVES_DIR / "applied"

# Supported operation dispatch — op_name -> (callable, required args).
# The callable receives **args and returns a dict with whatever ClickUp
# returned. Errors bubble up — the flush loop handles them per-op.
_OPS: dict[str, callable] = {}


def _op(name: str):
    def _register(fn):
        _OPS[name] = fn
        return fn
    return _register


@_op("create_task")
def _do_create_task(**args) -> dict:
    # Supports business/department, project, or pillar routing via clickup.add_task.
    return clickup.add_task(
        args["name"],
        priority=args.get("priority", "Should"),
        business=args.get("business"),
        department=args.get("department"),
        project=args.get("project"),
        pillar=args.get("pillar"),
        marketing_sub=args.get("marketing_sub"),
        bunshin_ref=args.get("bunshin_ref"),
        description=args.get("description"),
        status=args.get("status"),
        tags=args.get("tags"),
    )


@_op("update_task")
def _do_update_task(**args) -> dict:
    task_id = args.pop("task_id")
    return clickup.update_task(task_id, **args)


@_op("update_task_status")
def _do_update_status(**args) -> dict:
    return clickup.update_task_status(args["task_id"], args["status"])


@_op("add_comment")
def _do_add_comment(**args) -> dict:
    return clickup.add_comment(args["task_id"], args["text"])


@_op("create_list")
def _do_create_list(**args) -> dict:
    # Folder-scoped create; rarely needed, but supported for milestones-as-lists cases.
    return clickup.create_list(args["folder_id"], args["name"])


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def _ensure_dirs() -> None:
    WAVES_DIR.mkdir(parents=True, exist_ok=True)
    APPLIED_DIR.mkdir(parents=True, exist_ok=True)
    if not PENDING_PATH.exists():
        PENDING_PATH.write_text("", encoding="utf-8")


def _load_pending() -> list[dict]:
    _ensure_dirs()
    ops: list[dict] = []
    for line in PENDING_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ops.append(json.loads(line))
        except json.JSONDecodeError:
            # Corrupt line — skip, don't nuke the file.
            continue
    return ops


def _save_pending(ops: list[dict]) -> None:
    _ensure_dirs()
    PENDING_PATH.write_text(
        "".join(json.dumps(op, ensure_ascii=False) + "\n" for op in ops),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def queue_op(op: str, **args) -> dict:
    """Append an op to the pending wave. Returns the queued op record."""
    if op not in _OPS:
        raise ValueError(f"Unknown op: {op}. Known: {sorted(_OPS)}")
    record = {
        "id": str(uuid.uuid4())[:8],
        "ts": datetime.now(timezone.utc).isoformat(),
        "op": op,
        "args": args,
        "status": "pending",
    }
    _ensure_dirs()
    with PENDING_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def list_pending() -> list[dict]:
    return _load_pending()


def flush_wave(*, dry_run: bool = False, op_filter: str | None = None) -> dict:
    """
    Execute pending ops against ClickUp. Moves applied ops to applied/wave-<ts>.jsonl.

    Returns {"applied": N, "failed": M, "skipped": K, "wave_file": path_or_None}.
    """
    pending = _load_pending()
    if not pending:
        return {"applied": 0, "failed": 0, "skipped": 0, "wave_file": None}

    wave_ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    wave_file = APPLIED_DIR / f"wave-{wave_ts}.jsonl"

    applied: list[dict] = []
    remaining: list[dict] = []
    applied_count = 0
    failed_count = 0
    skipped_count = 0

    for record in pending:
        if op_filter and record["op"] != op_filter:
            remaining.append(record)
            skipped_count += 1
            continue

        if dry_run:
            record_preview = dict(record, status="dry-run")
            applied.append(record_preview)
            skipped_count += 1
            continue

        fn = _OPS.get(record["op"])
        if fn is None:
            record["status"] = "error"
            record["error"] = f"unknown op: {record['op']}"
            applied.append(record)
            failed_count += 1
            continue

        try:
            result = fn(**record.get("args", {}))
            record["status"] = "applied"
            record["applied_at"] = datetime.now(timezone.utc).isoformat()
            record["result"] = {k: result.get(k) for k in ("id", "url", "name")
                                if isinstance(result, dict) and k in result}
            applied.append(record)
            applied_count += 1
        except Exception as e:
            record["status"] = "error"
            record["error"] = str(e)
            record["failed_at"] = datetime.now(timezone.utc).isoformat()
            applied.append(record)
            failed_count += 1
            # Keep errored ops in remaining so they can be retried? No — leave
            # them in the applied log with status=error, and drop from pending.
            # If the user wants to retry, they can re-queue explicitly.

    if not dry_run and applied:
        _ensure_dirs()
        with wave_file.open("w", encoding="utf-8") as f:
            for record in applied:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        _save_pending(remaining)
    elif op_filter:
        # Filtered non-dry-run: only applied the matching ops, remaining kept as-is.
        _save_pending(remaining)

    return {
        "applied": applied_count,
        "failed": failed_count,
        "skipped": skipped_count,
        "wave_file": str(wave_file) if (not dry_run and applied) else None,
    }


def list_applied(limit: int = 10) -> list[dict]:
    """Return the most recent applied wave files (metadata only)."""
    _ensure_dirs()
    waves = sorted(APPLIED_DIR.glob("wave-*.jsonl"), reverse=True)[:limit]
    out: list[dict] = []
    for w in waves:
        ops = [json.loads(l) for l in w.read_text(encoding="utf-8").splitlines() if l.strip()]
        summary: dict[str, int] = {}
        for op in ops:
            summary[op["status"]] = summary.get(op["status"], 0) + 1
        out.append({"file": w.name, "op_count": len(ops), "summary": summary})
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_flags(rest: list[str]) -> tuple[list[str], dict]:
    """Split positional args and --flag value pairs. Known single-valued only."""
    pos: list[str] = []
    flags: dict = {}
    i = 0
    while i < len(rest):
        a = rest[i]
        if a.startswith("--"):
            key = a[2:]
            if i + 1 < len(rest) and not rest[i + 1].startswith("--"):
                flags[key] = rest[i + 1]
                i += 2
            else:
                flags[key] = True
                i += 1
        else:
            pos.append(a)
            i += 1
    return pos, flags


def _cli(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    cmd, *rest = argv
    try:
        if cmd == "queue":
            if not rest:
                print("usage: waves.py queue <op> --arg1 val1 --arg2 val2 ...")
                print(f"ops: {sorted(_OPS)}")
                return 1
            op_name = rest[0]
            _pos, flags = _parse_flags(rest[1:])
            # Parse tags as CSV if given.
            if "tags" in flags and isinstance(flags["tags"], str):
                flags["tags"] = [t.strip() for t in flags["tags"].split(",") if t.strip()]
            rec = queue_op(op_name, **flags)
            print(json.dumps(rec, indent=2, ensure_ascii=False))
            return 0
        if cmd == "pending":
            pending = list_pending()
            print(f"{len(pending)} pending op(s):")
            for p in pending:
                args_preview = ", ".join(f"{k}={v!r}" for k, v in p.get("args", {}).items())[:120]
                print(f"  [{p['id']}] {p['op']:<22}  {args_preview}")
            return 0
        if cmd == "flush":
            _pos, flags = _parse_flags(rest)
            result = flush_wave(dry_run=bool(flags.get("dry-run")),
                                op_filter=flags.get("only"))
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0
        if cmd == "applied":
            limit = int(rest[0]) if rest else 10
            for w in list_applied(limit):
                print(f"{w['file']}  |  {w['op_count']} ops  |  {w['summary']}")
            return 0
        print(f"unknown command: {cmd}")
        print(__doc__)
        return 1
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(_cli(sys.argv[1:]))
