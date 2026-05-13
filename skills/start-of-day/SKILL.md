---
name: start-of-day
description: This skill should be used when the user asks to "start of day", "SOD", "run start of day", "kick off the day", "start of day routine", or runs "/start-of-day".
version: 0.2.0
allowed-tools: [Bash]
---

# Start-of-Day Skill

Run the morning routine: surface (and optionally re-prioritize / re-schedule) every Todoist task that's due today or overdue.

## Purpose

Provide a single command that kicks off the workday with the full picture of what's due today plus anything still overdue — with an inline edit loop so the user can re-rank or push items without leaving the conversation.

Meeting action items are processed the evening before, by `/end-of-day`, so they show up in the today + overdue list automatically without needing a separate morning step.

## When to Use

Invoke this skill when:

- User explicitly runs `/start-of-day`
- User mentions "start of day", "SOD", "kick off the day", "start of day routine"
- User wants to triage today's todos at the start of the workday

## When NOT to Use

- If the user wants to review meeting action items: use `/meeting-action-items` (also runs automatically as part of `/end-of-day`)
- If the user only wants to see today's todos with no review loop: run `td today` directly
- If the user wants to edit one specific known task: use `td task update <ref>` directly — the `/start-of-day` loop is built around the day's whole list

## Pipeline Overview

```
Today + Overdue     →  List every task due today + overdue across all
                       projects (single combined list, oldest-due-first),
                       then enter an interactive edit loop where any
                       task can have its priority and/or due date changed
                       (direct `td` CLI invocations)
```

Single step — no parallelism, no sub-skills invoked.

## Prerequisites

- **Todoist CLI (`td`) authenticated.** If `td auth status` fails or `td` is not on `PATH`, the skill will surface the error. Fallback absolute path: `/opt/homebrew/bin/td`.

No MCPs required.

## Process Flow

Two phases: display the list, then enter an interactive edit loop. Shell out to `td` directly — the `todoist-cli` skill is a reference document for `td` syntax, not a workflow to invoke.

### Phase 1: Fetch and display

Run `td today --json` to fetch tasks with their IDs. Render them as a single combined, oldest-due-first numbered list:

```
Today + Overdue (12 tasks):
  [1] (p1, overdue 3d)  Finish quarterly review               id:8Jx4mVr72kPn3QwB
  [2] (p1, overdue 1d)  Reply to security review thread       id:3Vr2jKp89nLm5RsT
  [3] (p2, due today)   Send agenda for platform standup      id:6Kp9wLs83nLm5RsT
  ...
```

For each task, show: index, priority (`p1`-`p4`), due-date label (`overdue Nd` for past-due, `due today` for today), title, and short id (use the Todoist task id verbatim — needed for the update command).

If the list is empty, print `Nothing due today, nothing overdue.` and finish the skill (no edit loop, no prompt).

### Phase 2: Interactive edit loop

After the list is displayed, prompt:

```
[<N>] edit task N    [r] refresh list    [q] done
>
```

Handle the response:

- **`<N>` (integer)** — selected a task to edit. Validate `N` is in range; if not, re-prompt. Then ask two follow-up questions:
  1. **New priority?** Accept `p1` / `p2` / `p3` / `p4` to change, or `-` to leave alone.
  2. **New due date?** Accept any string `td --due` accepts (`tomorrow`, `next monday`, `2026-05-20`, `friday`, etc.), or `-` to leave alone.

  Build the update command from only the fields the user actually changed — do NOT emit a flag the user said `-` to:

  ```bash
  td task update id:<id> [--priority pN] [--due "<string>"]
  ```

  Examples:
  - User picks `p2` for priority and `-` for due → `td task update id:<id> --priority p2`
  - User picks `-` for priority and `next monday` for due → `td task update id:<id> --due "next monday"`
  - User picks `-` for both → skip the call entirely; print "No change."

  Print a one-line confirmation showing what changed, then return to the edit prompt:

  ```
  Updated [3] Send agenda for platform standup: p2 → p1, due today → tomorrow
  ```

- **`r`** — re-run `td today --json` and re-display the list (Phase 1). Useful after several edits to see the new ordering.
- **`q`** or empty input — exit the loop and finish the skill.

If a `td task update` call exits non-zero, surface stderr and stay in the loop — do not abort. The next prompt iteration gives the user a chance to retry or move on.

## Error Handling

### `td` Unavailable or Unauthenticated

If `td auth status` fails or `td` is not on `PATH`:

```
Couldn't run: `td` is not authenticated (or not installed).

  Suggested fix: `td auth login`  (or install via the project setup).

  [r] Retry — user fixes it now, then retry
  [h] Halt — stop here

Choice?
```

### `td task update` Fails on a Specific Task

Stay in the edit loop. Print the error, return to the `[<N>] / [r] / [q]` prompt. Do not abort the skill.

## Related Skills

- **/end-of-day** — End-of-day counterpart that handles meeting/Slack ingestion, the meeting action-items review, and the wiki compile
- **/meeting-action-items** — Standalone meeting action-item review (runs automatically as part of `/end-of-day`)
- **todoist-cli** (global reference skill at `~/.claude/skills/todoist-cli/`) — `td` CLI syntax reference; not invoked, but consulted

## Summary

The start-of-day skill runs the morning routine: list every task due today plus anything overdue across all projects, and offer an inline edit loop to re-prioritize or re-schedule on the spot. Meeting action items get reviewed the evening before by `/end-of-day`, so they're already in the list. Use `/start-of-day` as the single command to start the workday.
