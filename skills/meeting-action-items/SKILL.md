---
name: meeting-action-items
description: This skill should be used when the user asks to "review meeting action items", "process meeting follow-ups", "extract action items from meetings", "make todos from meetings", or wants to convert recent meeting action items into Todoist tasks. Scans `meetings/` for summaries in a configurable lookback window (default: since last run, fallback 2 days), extracts items from "Action Items" sections, and triages each via AskUserQuestion (todo / dismiss / skip). Already-handled items are tracked in `.lyt-assistant/_action-item-state.json` so they don't re-appear.
version: 0.8.0
argument-hint: "[--days N | --since YYYY-MM-DD]"
allowed-tools: [Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion]
---

# Meeting Action Items Skill

All mechanical work lives in `meeting_action_items.py` next to this file
(Python 3 stdlib, no dependencies). The model's job is exactly three things:
run `list`, triage via AskUserQuestion, run `apply`. Never reimplement the
parsing, dedup, assignee filtering, or state writes inline, and never call
`td` or edit the state file directly: `apply` owns all mutation and flushes
state after every item so a crash never leaves a created task unrecorded.

## Prerequisites

- Vault root `~/Documents/Work/` (override with `--vault` for testing).
- Todoist CLI (`td`) authenticated. `apply` checks and aborts cleanly if not.

## Pipeline

### Step 1: List candidates

```bash
python3 <skill-dir>/meeting_action_items.py list [--days N | --since YYYY-MM-DD]
```

(`<skill-dir>` is this skill's base directory, announced when the skill
loads.) Output JSON: `window`, `meetings_scanned`, `pending[]` (each with
`key`, `meeting_dir`, `raw`, and `suggested` {title, description, due,
priority}), `auto_checked[]` (already `- [x]` in the summary), and
`filtered_count` (excluded by the assignee allowlist, which lives at the top
of the script).

`list` is pure: it never writes state, so it is always safe to re-run.

If `pending` is empty: run `apply` with just the `auto_checked` items
(Step 4, empty decisions list), then report "Nothing new in the window
across N meeting(s) (M filtered by assignee)." and stop.

### Step 2: Triage

Present every pending item via AskUserQuestion, one question per item
(options: Todo / Dismiss / Skip), batched 4 items per call. Show the raw
bullet plus the suggested title in each question text so the user sees what
Todo would create. AskUserQuestion has a 4-option cap per question, so do
NOT attempt one multi-select across items.

If there are more than 12 pending items, first show the full numbered list
in plain text and ask for a free-text bulk command (for example "todo 2,4,5;
dismiss rest"). Parse it, echo the plan, confirm with one AskUserQuestion,
and fall through to per-item questions only for items the command left
ambiguous.

### Step 3: Due and priority for the todos

For each item marked Todo, one AskUserQuestion round sets fields, two
questions per todo (so two todos per call):

- Due: options `tomorrow` / `Friday` / `next week` / `no due date`, with the
  script's suggested due pre-noted in the question text. Custom dates come
  in via Other.
- Priority: options `p1` / `p2` / `p3` / `p4` (default p2).

Title and description always use the script's suggestions unless the user
volunteers a change in chat.

### Step 4: Apply

Build the decisions JSON and pipe it in:

```bash
python3 <skill-dir>/meeting_action_items.py apply --input /tmp/mai-decisions.json
```

Input shape:

```json
{
  "auto_checked": [ {"key": "...", "meeting_dir": "...", "raw": "..."} ],
  "decisions": [
    {"key": "...", "meeting_dir": "...", "raw": "...", "action": "todo",
     "title": "...", "description": "...", "due": "tomorrow", "priority": "p2"},
    {"key": "...", "meeting_dir": "...", "raw": "...", "action": "dismiss"},
    {"key": "...", "meeting_dir": "...", "raw": "...", "action": "skip"}
  ]
}
```

`apply` creates Todoist tasks (project `Work`) via `td`, records state
atomically per item, updates `last_run`, and prints a results JSON (created
URL / dismissed / skipped / failed with the error). A malformed decision
fails that item and the batch continues. Exit code 1 means at
least one item failed: surface those failures verbatim and offer to re-run
`apply` with just the failed items.

### Step 5: Report

One line: "Made X todos, dismissed Y, skipped Z. (M filtered by assignee,
K auto-recorded as done.)" plus the created task URLs.

## State

`.lyt-assistant/_action-item-state.json`, schema version 1, unchanged from
v0.7.x: items keyed `<meeting_dir>::<sha256(normalized_text)[:12]>` with
`meeting_dir`, `text`, `status` (todoed | dismissed), `todoist_url`,
`decided_at`. Skipped items are never recorded and resurface next run.

## Testing

```bash
cd <skill-dir> && python3 test_meeting_action_items.py
```

Fixtures live in `test-fixtures/vault/`. `apply --dry-run` exercises the td
path without creating tasks.
