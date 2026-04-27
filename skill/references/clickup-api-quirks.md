# ClickUp API Quirks (the ones that burn time)

The bundled `scripts/clickup.py` encapsulates every quirk below. **Always prefer the helper over hand-rolled requests.**

## 1. NO `Bearer` prefix on the Authorization header

ClickUp uses the literal token as the header value. Sending `Bearer pk_xxx` returns 401.

```http
Authorization: pk_xxx_actual_token_here
```

Most common Notion/Slack-habit mistake.

## 2. Priority is an integer enum, not a string

The API expects:
- `1` = Urgent (Must)
- `2` = High (Should)
- `3` = Normal (unused in KAGE)
- `4` = Low (Could)

Sending `"priority": "Urgent"` does NOT error — it silently sets nothing. The helper converts strings; raw callers must send ints.

## 3. Status names are lowercase and case-sensitive

Default Space statuses are `to do`, `in progress`, `complete`. `"To Do"` won't match. Echo back whatever the API returned in `status.status` as canonical case.

## 4. "Workspace" in UI = "Team" in API

ClickUp rebranded Teams → Workspaces a couple years ago, but the API still says `team`. `team_id` and "workspace ID" are the same thing. `GET /api/v2/team` lists workspaces.

## 5. List IDs, Folder IDs, Space IDs are numeric strings

They look like ints but they're strings. `list_id="901234567"`, not `list_id=901234567`.

## 6. Pagination: `page` param + `last_page` flag

Endpoints that paginate (e.g. `GET /list/{list_id}/task`) take `page=0,1,2...` and the response has `last_page: bool`. Loop until `last_page == true` OR the batch is empty.

## 7. Search vs filter

- `GET /team/{team_id}/task?search=keyword` — fuzzy name + description search across the workspace.
- `GET /list/{list_id}/task` — ALL tasks in that List with no name search (filter by status/priority/tags via query params).
- For "find a task across the whole workspace by name" → `search`.
- For "everything in this List" → the list endpoint.

## 8. Custom field creation is plan-gated

`POST /list/{list_id}/field` requires Business+ plan + admin perms on some configs. If you get 403, fall back to tags + description headers.

## 9. Setting a custom field value is a separate endpoint

`POST /api/v2/task/{task_id}/field/{field_id}` with `{"value": ...}`. Value shape varies by field type: text=string, dropdown=option_id, labels=array of option_ids. `GET /list/{list_id}/field` to learn the type first.

## 10. Rate limit: ~100 req/min per token

Friendlier than Notion. The `clickup.py` helper throttles to ~92/min via `_MIN_INTERVAL = 0.65`. If you hit 429, the response includes `X-RateLimit-Reset`. The helper auto-retries once after 2s on 429; persistent 429s mean another process is sharing the token.

Wave flushes ship through the helper, so a wave of 50 ops takes ~30s to flush. That's fine — waves are explicitly NOT for real-time updates.

## 11. Archive vs delete

- Default: `archived: false`. To "remove without losing", `PUT /task/{task_id}` with `{"archived": true}`.
- True delete: `DELETE /task/{task_id}` — avoid except for tasks created in error.
- **KAGE convention: never delete. Archive.**

## 12. Subtasks are real tasks with `parent` set

A subtask is a task whose `parent` field points to another task ID. Full task API works on them. They show up in `list/{list_id}/task` only if you pass `subtasks=true`.

## 13. Webhooks for live sync

If wiring automation, use `POST /api/v2/team/{team_id}/webhook` with an events array. ClickUp's built-in Automations cover most of this without webhooks.

## 14. Routing in GAMBATTE

The `manifest.json` file (generated during bootstrap, lives at the skill root) maps every Space + List name to its List ID. The helper reads it:

```python
clickup.list_id_for("<Space Name>", "<List Name>")
```

If a lookup returns `None`, the manifest is stale — regenerate via `python clickup.py build-manifest > ~/.claude/skills/kage/manifest.json` or ask the user. Don't auto-create a List.

## 15. Priority filter in bounty board

`clickup.list_musts()` uses:
```
GET /team/{team_id}/task?priorities[]=1&include_closed=false&page=0
```

The bracketed `priorities[]=1` is correct array syntax — ClickUp expects it, not `priority=1`.

## 16. ClickUp Brain is in-workspace only

ClickUp Brain (paid add-on) answers questions inside the workspace. It does NOT see BUNSHIN, Claude's chat, or any other context. Use Brain for in-workspace summaries; use Claude (this skill) for cross-context reasoning that bridges tasks + knowledge.

## TL;DR Survival List

1. Always route through `clickup.py` (via `waves.py` or directly).
2. If hand-rolling: literal token, priority ints, lowercase statuses, `team` not `workspace`.
3. IDs are strings.
4. Paginate via `page` + `last_page`.
5. Never delete — archive.
6. For custom state beyond the schema: tags + description headers, not custom fields.
