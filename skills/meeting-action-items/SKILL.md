---
name: meeting-action-items
description: This skill should be used when the user asks to "review meeting action items", "process meeting follow-ups", "extract action items from meetings", "make todos from meetings", or wants to convert recent meeting action items into Todoist tasks. Scans `meetings/` for summaries in a configurable lookback window (default: since last run, fallback 2 days), extracts items from "Action Items" sections, and triages each via AskUserQuestion (todo / dismiss / skip). Already-handled items are tracked in `.lyt-assistant/_action-item-state.json` so they don't re-appear.
version: 0.9.0
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
python3 ${CLAUDE_SKILL_DIR}/meeting_action_items.py list [--days N | --since YYYY-MM-DD]
```

(`${CLAUDE_SKILL_DIR}` expands to this skill's directory; if it reaches
you unexpanded, use the base directory announced when the skill loaded.)
Output JSON: `window`, `meetings_scanned`, `pending[]` (each with
`key`, `meeting_dir`, `raw`, and `suggested` {title, description, due,
priority}), `auto_checked[]` (already `- [x]` in the summary), and
`filtered_count` (excluded by the assignee allowlist, which lives at the top
of the script).

`list` is pure: it never writes state, so it is always safe to re-run.

If `list` exits non-zero, abort the run and show its stderr verbatim. Do
not treat missing output as an empty pending list: a corrupt or
version-mismatched state file is a stop-the-line error, not a
nothing-to-do.

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
dismiss rest"). Parse it, echo the plan (noting any out-of-range indices, which are
ignored), confirm with one AskUserQuestion, then fall through to per-item
questions for every item the command did not explicitly address.
Unaddressed items are never silently skipped or dismissed: the per-item
question is the safe default.

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
python3 ${CLAUDE_SKILL_DIR}/meeting_action_items.py apply --input /tmp/mai-decisions.json
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
`apply` with a new input containing ONLY the failed items in `decisions`
and an EMPTY `auto_checked` list (re-submitting the original input would
re-record already-applied items). If apply aborted before the batch
started (td not authenticated, unreadable --input), fix the cause and
re-run the original input unchanged.

`apply` also dedups every `todo` against the live Todoist Work project
(`td task list --project Work --all --json`) before creating it. A candidate
whose title is a normalized-equal or high-token-overlap (>= 0.85) match for an
existing open task returns outcome `duplicate` (with the matched title) and is
**not created and not recorded in state** -- so it resurfaces next run if the
matched live todo is later completed. Substring containment is never used, so a
short title ("Email Bob") is not swallowed by a longer one ("Email Bob about
the Q3 contract"). Callers driving non-interactive runs MUST mark a
model-detected semantic duplicate as `skip` (non-terminal), never `dismiss`
(terminal) -- permanent suppression of an action item is reserved for an
explicit user decision.

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
cd ${CLAUDE_SKILL_DIR} && python3 test_meeting_action_items.py
```

Fixtures live in `test-fixtures/vault/`. `apply --dry-run` exercises the td
path without creating tasks.
