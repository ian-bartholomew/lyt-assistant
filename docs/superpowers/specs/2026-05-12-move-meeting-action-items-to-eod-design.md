---
title: Move /meeting-action-items from /start-of-day to /end-of-day
date: 2026-05-12
status: approved
---

# Move /meeting-action-items from /start-of-day to /end-of-day

## Problem

`/meeting-action-items` currently runs as Step 1 of `/start-of-day`. The action items it processes come from meetings ingested by `/meeting-ingest`, which runs as Step 1 of `/end-of-day` the previous evening. Processing the meetings the morning after delays follow-up by ~12 hours and decouples the action-item review from the context of the meetings themselves. Co-locating the two steps in `/end-of-day` lets the user act on each day's commitments while the meetings are still fresh.

## Goals

- `/end-of-day` runs `/meeting-action-items` interactively after `/meeting-ingest` has finished.
- `/start-of-day` no longer invokes `/meeting-action-items`; it becomes a single-step "today + overdue" review.
- Plugin version bumps to `2.12.0` and `CHANGELOG.md` records the change.
- Branch `feat-move-meeting-action-items-to-eod` and worktree `.worktrees/feat-move-meeting-action-items-to-eod/` carry the work.

## Non-Goals

- No changes to the `meeting-action-items` skill's own behavior, prompts, or state file.
- No changes to `meeting-ingest`, `compile`, or any other end-of-day sub-skill.
- No change to `/meeting-action-items` as a standalone command — it remains directly invocable.

## Design

### `/end-of-day` updates

Insert `/meeting-action-items` as a new **Step 5**, immediately after the Step 4.5 join and before compile. Renumber existing Step 5 (Compile) → Step 6 and Step 6 (Report) → Step 7.

Updated pipeline:

```
Step 1: Meeting Ingest             (background subagent)
Step 2: FES Support → Confluence   (background subagent)
Step 3: Support Learnings → raw/
Step 4: Internal Channel → raw/
Step 4.5: Join                     (wait for Steps 1 and 2)
Step 5: Meeting Action Items       (interactive, NEW)
Step 6: Compile                    (was Step 5)
Step 7: Final Report               (was Step 6)
```

Step 5 invocation:

```
Skill: meeting-action-items
Args: (none — default lookback "since last run, fallback 2 days")
```

Track per run: items reviewed, todos created, dismissed, skipped. Recorded status values: `ok`, `nothing-new`, `quit-early`, `failed`. These mirror the values that were previously recorded inside `/start-of-day`.

**Why after the join, not inline with Step 1:** `meeting-action-items` reads from `meetings/` — the directory populated by `meeting-ingest`. Step 1 runs as a background subagent (parallel with Steps 2–4); pulling it foreground to satisfy action-items' dependency would defeat the existing parallelism. Placing action-items after the join guarantees Step 1 has finished without restructuring the parallel work.

**Why before compile, not after the report:** compile doesn't read action-items output, but running an interactive review after the "End-of-Day Complete" report would be backwards. Keep all interactive steps upstream of the summary.

**Error handling for Step 5:** apply the same continue / retry / halt prompt used elsewhere in `/end-of-day`. If the user `[q]`s mid-loop, treat as `ok` (partial-progress), record counts, and continue to compile — matches the existing `quit-early` handling.

**Report (Step 7) additions:** extend the report block with a "Step 5 — Meeting Action Items" section showing reviewed / created / dismissed / skipped, and add a corresponding line to the `wiki/_log.md` entry, e.g. `- Meeting action items: 4 reviewed, 2 created, 1 dismissed, 1 skipped`.

### `/start-of-day` updates

Remove Step 1 (Meeting Action Items) entirely. The skill becomes a single-step routine: list today + overdue and run the edit loop.

Sections to update:

- **Title block & Purpose:** drop the "two beats" framing; describe a single beat (today + overdue with edit loop).
- **Pipeline Overview:** replace the two-step diagram with a single step (Today + Overdue).
- **Prerequisites:** keep `td` requirement; no other change.
- **Process Flow:** delete the Step 1 section; promote former Step 2 to be the body of the skill (drop the "Step 2" heading or rename to "Process").
- **Error Handling:** remove the "`meeting-action-items` Quits Early" subsection. Keep `td` unavailable and `td task update` failure subsections.
- **Related Skills:** keep `/meeting-action-items` as a related skill, but reframe it as "run directly if you want to review meeting follow-ups outside the end-of-day pipeline." Keep the `/end-of-day` cross-reference and note that it now owns the action-item review.
- **Summary:** rewrite to reflect the single-step routine.
- **`allowed-tools` frontmatter:** drop `Skill` (no longer invokes a sub-skill) — `Bash` is sufficient.

### Version and changelog

- `plugin.json`: `"version": "2.11.0"` → `"version": "2.12.0"`.
- `CHANGELOG.md`: prepend a `## [2.12.0] - 2026-05-12` block under the existing entries with:

```markdown
### Changed
- `/meeting-action-items` now runs as part of `/end-of-day` (new Step 5, after the meeting-ingest join), instead of as Step 1 of `/start-of-day`. Action items from each day's meetings are reviewed while the meetings are still fresh, rather than the following morning.
- `/start-of-day` is now a single-step routine (today + overdue, with edit loop).
```

No `### Added` / `### Removed` entries — `/meeting-action-items` itself is unchanged and still directly invocable.

### Branch and worktree

- Branch: `feat-move-meeting-action-items-to-eod` (created from `main`).
- Worktree: `.worktrees/feat-move-meeting-action-items-to-eod/`.
- `.worktrees/` is already in `.gitignore`.

## File-by-file change list

| File | Change |
|---|---|
| `skills/end-of-day/SKILL.md` | Insert new Step 5 (Meeting Action Items); renumber Step 5 → 6 and Step 6 → 7; extend Step 7 report block and `_log.md` template; update Pipeline Overview diagram, Prerequisites note (mentions Todoist now), Related Skills list, and Summary |
| `skills/start-of-day/SKILL.md` | Remove Step 1; collapse into single-step skill; update Purpose, Pipeline Overview, Process Flow, Error Handling, Related Skills, Summary; drop `Skill` from `allowed-tools` |
| `plugin.json` | Bump `version` `2.11.0` → `2.12.0` |
| `CHANGELOG.md` | Add `## [2.12.0] - 2026-05-12` block with the `### Changed` entry above |

## Testing plan

This is documentation-only (no executable code). Verification:

1. Read both updated SKILL.md files end-to-end; check for orphaned references to the old Step 1 in `/start-of-day`, dangling step-number references in `/end-of-day`, and consistency between Pipeline Overview, Process Flow, and Summary.
2. Run `grep -n "Step [0-9]" skills/end-of-day/SKILL.md` and confirm the sequence is 1, 2, 3, 4, 4.5, 5, 6, 7 with no gaps or duplicates.
3. Confirm `plugin.json` version is `2.12.0` and `CHANGELOG.md` has the new top-most entry.
4. Live smoke test (post-merge, by the user): run `/end-of-day` on a day with new meetings and confirm Step 5 fires interactively after the join and before compile; run `/start-of-day` and confirm it goes straight to the today+overdue list.

## Risks and trade-offs

- **Loss of morning prompt:** the user no longer gets a fresh prompt to review yesterday's action items at the start of the day. Mitigation: `/meeting-action-items` is still directly invocable. If a user wants the morning beat back, they run `/meeting-action-items` standalone.
- **Longer `/end-of-day` interactive time:** end-of-day now has three interactive steps (3, 4, 5) instead of two. Acceptable — they're all interactive review of fresh content.
- **Action-items state file (`.lyt-assistant/_action-item-state.json`):** unchanged. Since `/meeting-action-items` tracks "already handled" items via this file, moving the step does not risk double-processing.
