# Design: `lyt-assistant:meeting-action-items`

**Date:** 2026-05-11
**Status:** Approved
**Plugin:** `lyt-assistant`

## Problem

Meeting summaries in the vault (`meetings/YYYY-MM-DD-<topic>/summary-default.md`) consistently contain an `### Action Items` section with bullets describing things the user is expected to do or follow up on. Today those items are read once and forgotten — there is no friction-free path from "I just had a meeting" to "this is a tracked task in Todoist." Manually reviewing every recent summary is tedious; doing it without keeping state means the same items get re-presented every time.

This skill closes that loop: scan recent meetings, surface each action item once, and let the user turn it into a `#Work` Todoist task, dismiss it, or skip it. State is persisted so already-handled items never re-appear.

## Goals

1. Walk the user through every *unseen* action item from meetings in a configurable lookback window.
2. For each item, offer three actions: **make todo**, **dismiss**, **skip**.
3. When making a todo, prompt for due date and priority every time; project is hard-coded to `Work`.
4. Persist seen/dismissed state in a single vault-level JSON file so future runs do not re-prompt for handled items.
5. Default lookback = "since the last successful run"; first-ever run defaults to 2 days. `--days N` and `--since DATE` overrides.

## Non-goals

- Auto-creating todos without user confirmation.
- Editing the meeting summary files in place (state lives outside summaries).
- Cross-meeting deduplication. The same text in two meetings produces two distinct items (per-meeting keying).
- Extracting from sections other than `### Action Items` (no `Decisions Made`, `Next Steps`, `Follow-Ups`, etc.).
- Auto-detecting follow-ups from transcripts or Key Discussion Points — only the dedicated Action Items section.
- Bulk operations ("dismiss all from this meeting"). v1 is one item at a time.

## Architecture

Pure markdown `SKILL.md` — no helper scripts. State-file operations are inline `jq` one-liners with `--argjson`. This matches the rest of the `lyt-assistant` plugin (e.g. `meeting-ingest`, `ingest`, `compile`) which are all procedural markdown skills.

Three logical stages run sequentially inside the skill:

```
┌─────────────┐   ┌──────────────┐   ┌──────────────────────┐
│ 1. Discover │ → │ 2. Extract   │ → │ 3. Interactive loop  │
│ meetings    │   │ action items │   │ (per item: do what?) │
│ in window   │   │ from summary │   │  · make todo         │
└─────────────┘   └──────────────┘   │  · dismiss           │
                                     │  · skip              │
                                     └──────────────────────┘
                          ▲                       │
                          │                       ▼
                  ┌─────────────────────────────────┐
                  │ .lyt-assistant/                 │
                  │   _action-item-state.json       │
                  │ (read for filter, write back)   │
                  └─────────────────────────────────┘
```

State writes are **streaming** — each per-item decision is committed before moving to the next item. A quit/crash mid-run preserves everything decided so far.

## Components

### Stage 1 — Discover meetings in window

- Determine the start date (a calendar date, day-precision):
  1. If `--since YYYY-MM-DD` is passed, use that.
  2. Else if `--days N` is passed, use `today - N days`.
  3. Else read `last_run` from the state file. If present, use its date portion (truncate the timestamp to YYYY-MM-DD). If absent (first run or missing state file), use `today - 2 days`.
- List directories under `meetings/` whose name matches `^YYYY-MM-DD-` and whose embedded date is `>=` start date (inclusive).
- The window is keyed off **directory-name date**, not on `last_run` timestamp granularity. This means a meeting from earlier today could appear on a second same-day run if any of its items are still undecided — the per-item dedupe in `items` prevents re-prompting for already-handled ones.
- Skip `meetings/.gitkeep`, `meetings/.DS_Store`, and any folder not matching the date prefix pattern.

### Stage 2 — Extract action items per meeting

For each meeting folder:

1. Pick the summary file:
   - Prefer `summary-default.md`.
   - Otherwise pick the first matching `summary-*.md` (alphabetical).
   - If none exists, skip the meeting with a one-line log entry.
2. Read the file. Locate any heading whose normalized text matches `/^\s*\d*\.?\s*action items\s*$/i` after stripping `**` bold markers (handles `### Action Items`, `### **Action Items**`, `### **3. Action Items**`).
3. Collect every bullet line under that heading until the next H2/H3 heading or EOF. Bullet patterns:
   - `- [ ] ...`
   - `- [x] ...` (treat as already-handled; auto-mark `todoed` with `todoist_url=null`)
   - `- ...`
   - `* ...`
   - `*   ...` (multiple spaces — seen in some templates)
4. For each bullet, capture the raw text and a normalized form (see Item Identity).

### Stage 3 — Interactive loop

For each extracted item, compute its composite key and check the state file. If the key already exists in `items` with any status, skip silently.

For each remaining (unseen) item:

```
[N of M]  <meeting_dir>

  <raw bullet text, trimmed>

  [t] make todo   [d] dismiss   [s] skip   [q] quit
> _
```

On user input:

- **`t`** → enter make-todo sub-prompt:
  - `Todoist task content [<auto-suggested>]:` (auto-suggestion = stripped of `- [ ]`, leading `**Person:**`, and trailing whitespace; ↵ accepts)
  - `Due (e.g. "tomorrow", "fri", "2026-05-15", or blank for no date):`
  - `Priority [p3] (p1=highest, p4=lowest):`
  - Run `td task add "<content>" --project "Work" [--due "..."] [--priority pN]`
  - Parse the URL from `td` stdout (or run `--json` and read `.url`); record in state.
  - If `td` fails, show error, offer **retry / dismiss / skip**.
- **`d`** → mark dismissed in state, advance.
- **`s`** → no state change, advance. Item will re-appear next run.
- **`q`** → halt loop, write `last_run` (see below), exit clean.

### State file format

Path: `<vault_root>/.lyt-assistant/_action-item-state.json`
(Created on first run if missing. `<vault_root>` is the cwd when the skill is invoked, expected to be the Obsidian vault root.)

```json
{
  "version": 1,
  "last_run": "2026-05-11T13:52:00-04:00",
  "items": {
    "2026-05-11-platform-standup::a3f1c9d7e0b2": {
      "meeting_dir": "2026-05-11-platform-standup",
      "text": "Ian: Write up the remaining IDP plan (3 of 4 epics) as a one-pager / Confluence page so the team can continue the work.",
      "status": "todoed",
      "todoist_url": "https://app.todoist.com/app/task/...",
      "decided_at": "2026-05-11T14:05:33-04:00"
    },
    "2026-05-11-platform-standup::e7b2d1a04c89": {
      "meeting_dir": "2026-05-11-platform-standup",
      "text": "Matt: Send out the bumped IAC refactor survey today; synthesize results this week.",
      "status": "dismissed",
      "decided_at": "2026-05-11T14:06:01-04:00"
    }
  }
}
```

Field rules:

- `version` — schema version. Hard-coded `1` for now. Any other value → bail with "unsupported state version".
- `last_run` — ISO 8601 with offset. Updated once per skill invocation, at the **end** of the loop (whether quit-early or natural completion). Items decided before quit still persist regardless.
- `items` — keyed by `<meeting_dir>::<sha256(normalized_text)[:12]>`. Per-meeting dedupe.
- `status` — `"todoed"` or `"dismissed"` only. `"skipped"` is not stored.
- `todoist_url` — present and non-null only when `status == "todoed"` AND `td task add` returned a URL. Present and null for items that were `- [x]` in the source summary (already done, not created by this skill).

### Item identity (key derivation)

```
normalized_text = bullet_text
  .strip_leading("- [ ]" | "- [x]" | "*" | "-" | whitespace)
  .strip_leading("**<word>:**" | "<word>:")     # optional person prefix
  .strip()
  .collapse_internal_whitespace_to_single_space
  .lowercase

key = "<meeting_dir>::" + sha256(normalized_text)[:12]
```

Stable across re-runs against the same summary. Robust to checkbox flips (`- [ ]` ↔ `- [x]`) and case changes. Sensitive to substantive edits — if the user edits a summary to clarify an item, it becomes a "new" item.

## Data flow

```
invocation
   │
   ▼
read state.json (or init)
   │
   ▼
compute window start date
   │
   ▼
glob meetings/YYYY-MM-DD-* with date >= start
   │
   ▼
for each meeting:
   read summary file → extract action items → for each item: key = hash, filter against state
   │
   ▼
present count: "Found 7 new action items across 3 meetings"
   │
   ▼
for each unseen item (interactive):
   prompt → user chooses (t/d/s/q)
     t → prompt content/due/priority → `td task add ...` → write state entry
     d → write state entry
     s → no-op
     q → break
   │
   ▼
write last_run timestamp, save state.json
   │
   ▼
end-of-run summary: "Made N todos, dismissed M, skipped K"
```

## Error handling

| Condition | Behavior |
|-----------|----------|
| State file missing | Treat as first run. Window defaults to `today - 2 days`. Materialize the file on first state write (first decision OR end-of-run `last_run` update, whichever comes first). |
| State file corrupt JSON | Bail with "State file corrupt: `<path>`. Move or fix it, then re-run." Do not auto-recover. |
| State `version` ≠ 1 | Bail with "Unsupported state version `<v>`. Update the skill or migrate the file." |
| Meeting folder name doesn't match date prefix | Skip silently. |
| Summary file missing in a meeting folder | Skip the meeting with a one-line log: `<dir>: no summary-*.md, skipping`. |
| No `Action Items` heading in a summary | Skip the meeting with a one-line log. |
| Action Items section is empty | Skip the meeting with a one-line log. |
| `td auth status` fails before the loop starts | Exit early: "Todoist CLI is not authenticated. Run `td auth login` and try again." Do not start the loop. |
| `td task add` fails mid-loop | Show stderr; offer retry / dismiss / skip on that item. Do not write state until success. |
| User passes both `--days` and `--since` | Bail with "Use either `--days` or `--since`, not both." |
| No new items in window | Print "Nothing new in the last N days across M meeting(s)." Exit clean. Still update `last_run`. |
| User quits with `q` mid-loop | Flush state to disk, update `last_run`, print summary, exit 0. Per-item decisions made before `q` are already persisted (streaming writes). |

## Testing

End-to-end manual verification:

1. **First-run on a clean vault.** Delete `.lyt-assistant/_action-item-state.json`, invoke the skill, confirm window = last 2 days, items presented one at a time, state file is created with `version`, `last_run`, and decided items only.
2. **Second run, no overrides.** Re-invoke immediately. Window now starts at the date portion of the previous `last_run`. Items decided in run #1 (todoed or dismissed) must not re-appear. If any items were `s`-skipped in run #1, confirm they DO re-appear (skip ≠ persist).
3. **`--days 7` override.** Reaches back 7 days even with a recent `last_run`. Already-handled items from prior runs do not re-appear.
4. **`--since 2026-05-01` override.** Same as `--days` but absolute date.
5. **Mixed bullet formats.** Run against `meetings/2026-05-11-platform-standup/summary-default.md` (`### Action Items` + `- [ ] **Person:**`) AND `meetings/2026-04-28-standup/summary-default.md` (`### **Action Items**` + `*   **Person:**`) AND `meetings/2026-04-27-ssm-meeting/summary-default.md` (`### **3. Action Items**`). All three should extract correctly.
6. **Mid-loop quit.** After making 2 todos, dismissing 1, then `q`. Re-invoke; the 2 todoed + 1 dismissed should be filtered out; remaining items resurface.
7. **Todoist auth failure.** Run with `unset TODOIST_API_TOKEN; td auth logout`. Skill should exit cleanly with an auth hint, not start the loop.
8. **Already-checked bullet.** A `- [x]` line in a summary should be auto-recorded as `todoed` with `todoist_url=null` and not prompt the user.

Acceptance criteria: each scenario completes as described; state file remains valid JSON throughout; no summary files are modified.

## Open questions

None — all design decisions resolved in the brainstorming session (see commit message for the four decisions).

## File layout (deliverables)

```
skills/meeting-action-items/
  SKILL.md           # the only file; pure markdown procedural skill
```

That's the entirety of the new functionality. No script files, no MCP integration, no hooks.
