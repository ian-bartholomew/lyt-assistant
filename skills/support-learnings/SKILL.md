---
name: support-learnings
description: >
  Use when the user asks to "extract support learnings", "process support channel",
  "review support threads", "support-learnings", "what happened in support",
  or wants to capture knowledge from Slack support channel interactions into
  structured Obsidian notes. Also triggers on "check unresolved threads",
  "revisit support threads", "revisit unresolved".
argument-hint: [revisit] [time-window] [--channel #channel-name]
---

# Support Learnings

Extract learnings from Slack support channels into structured, date-grouped Obsidian markdown files.

## When to Use

- User wants to process support channel threads into knowledge base notes
- User wants to check on previously unresolved support threads
- User wants to review what came through a support channel recently

## Arguments

- **No arguments:** Process new threads since last run (or 24h if first run).
- **`revisit`:** Revisit all unresolved threads in metadata. Does NOT process new threads.
- **Time window:** `3d`, `1w`, `12h` — override the lookback window
- **`--channel #name`:** Override the default channel (default: `#fes-platform-support`)

Parse the argument string. Time windows use format `<N><unit>` where unit is `h` (hours), `d` (days), `w` (weeks), or `m` (months). Convert to a Unix timestamp for the Slack API `oldest` parameter.

## Output Directory

All files go to `~/Documents/Work/raw/support_learnings/`.

## Workflow

There are two modes: **default** (process new threads) and **revisit** (check unresolved threads).

```dot
digraph workflow {
    rankdir=TB;
    "Read _metadata.yml" -> "Resolve channel ID";
    "Resolve channel ID" -> "Subcommand?";
    "Subcommand?" -> "Revisit unresolved" [label="revisit"];
    "Subcommand?" -> "Determine time window" [label="default"];
    "Determine time window" -> "Fetch new messages";
    "Fetch new messages" -> "Filter threads";
    "Filter threads" -> "Process each interactively";
    "Process each interactively" -> "Print summary";
    "Revisit unresolved" -> "Print summary";
}
```

### Phase 1: Setup

1. **Read metadata:** Read `~/Documents/Work/raw/support_learnings/_metadata.yml`. If it doesn't exist, initialize an empty structure:

   ```yaml
   channel_defaults: {}
   threads: []
   ```

2. **Resolve channel:** Check `channel_defaults` in metadata for cached channel name → ID mapping. If not cached, use `mcp__claude_ai_Slack__slack_search_channels` to look up the channel ID, then cache it in metadata.

3. **Route by subcommand:**
   - If argument is `revisit`: go to **Revisit Unresolved** mode
   - Otherwise: go to **Process New Threads** mode

4. **Determine time window** (Process New Threads mode only):
   - If explicit argument (e.g., `3d`): calculate Unix timestamp = now minus duration
   - If no argument: find the most recent `date_processed` across all threads in metadata, use start of that day as `oldest`
   - If no metadata entries exist: default to 24 hours ago

### Revisit Unresolved (only when `revisit` subcommand is used)

For each thread in metadata where `status: unresolved`:

1. Re-read the thread using `mcp__claude_ai_Slack__slack_read_thread` with the stored `ts` and `channel`
2. Show the user: the original title + a summary of the current thread state
3. Ask via `AskUserQuestion`: "Has this been resolved? Should I create an updated learning?"
4. **If resolved:** Extract the update, append to **today's** daily file using the **Update Template** below (the update goes on the day of resolution, not the original post date), set `status: resolved` and `date_resolved` in metadata
5. **If still unresolved / skip:** Leave metadata unchanged, move on

### Process New Threads (default mode)

1. Fetch messages using `mcp__claude_ai_Slack__slack_read_channel` with the channel ID and `oldest` timestamp
2. **Filter out:**
   - Messages with no thread replies (not a support interaction)
   - Threads whose `ts` already exists in metadata for this channel
   - Bot-only messages (Slackbot notifications, join messages)
3. For each remaining thread, **one at a time:**
   a. Read the full thread with `mcp__claude_ai_Slack__slack_read_thread`
   b. Extract: title, requester, problem, resolution (if any), learning, suggested tags
   c. Determine status: `resolved` if a clear solution was reached, `unresolved` if still in discussion or no answer
   d. **Determine the file date:** Use the date the thread's parent message was posted (from the message timestamp), NOT today's date. Convert the Slack `ts` to a date.
   e. Present the draft learning to the user using `AskUserQuestion` with options: Approve, Edit, Skip
   f. **Approve:** Append to the `YYYY-MM-DD.md` file matching the thread's post date, add entry to metadata
   g. **Edit:** Let user provide corrections, then append corrected version
   h. **Skip:** Do NOT add to metadata — thread will appear as unprocessed on next run

### Phase 4: Summary

Print: "Done. X threads processed, Y unresolved, Z skipped."

## Learning Template

Each learning is an H2 section in the daily file `YYYY-MM-DD.md`:

```markdown
## <Title>

**Thread:** [link](<slack_permalink>)
**Requester:** <name>
**Status:** <resolved|unresolved>
**Tags:** <comma-separated lowercase tags>

### Problem
<1-3 sentence description of what was asked/broken>

### Resolution
<What solved it, or "Unresolved — still in discussion" if no resolution>

### Learning
<The reusable takeaway — what would help someone facing this again>
```

**Slack permalink format:** `https://betfanatics.slack.com/archives/<CHANNEL_ID>/p<TS_WITH_NO_DOT>`

To construct the permalink, take the message `ts` (e.g., `1776963724.820519`), remove the dot to get `1776963724820519`, and build: `https://betfanatics.slack.com/archives/<CHANNEL_ID>/p1776963724820519`

## Update Template

When revisiting an unresolved thread that is now resolved, append to today's file:

```markdown
## [Update] <Original Title>

**Thread:** [link](<slack_permalink>)
**Original Learning:** [[<original-date>]] — "<Original Title>"
**Requester:** <name>
**Status:** resolved
**Tags:** <tags>

### Update
<What changed since the original learning>

### Learning
<Updated reusable takeaway>
```

## Daily File Frontmatter

When creating a new `YYYY-MM-DD.md`, start with:

```yaml
---
title: "Support Learnings - YYYY-MM-DD"
type: support-learnings
channel: <channel-name-without-hash>
---
```

If the file already exists (e.g., revisiting unresolved threads on a day that already has learnings), append new sections — do not overwrite.

## Metadata File Schema

`_metadata.yml` structure:

```yaml
channel_defaults:
  <channel-name>: <channel-id>

threads:
  - ts: "<message_ts>"
    channel: "<channel_id>"
    date_posted: <YYYY-MM-DD>       # date the thread was posted in Slack
    date_processed: <YYYY-MM-DD>    # date we extracted the learning
    date_resolved: <YYYY-MM-DD>     # date the revisit resolved it (only if revisited)
    status: <resolved|unresolved>
    title: "<thread title>"
    requester: "<person name>"
```

- **Unique key:** `ts` + `channel` (prevents reprocessing)
- **`date_posted`:** Derived from the Slack message `ts` — determines which daily file the learning goes into
- **`date_resolved`:** Set only when a revisit resolves the thread — the update learning goes into this date's file
- **Update metadata after each thread** (not at the end) to avoid data loss if interrupted

## Edge Cases

- **No new threads:** Report "No new threads found" after revisit phase
- **Thread with only bot replies:** Skip automatically
- **Very long threads (100+ replies):** Use cursor pagination on `slack_read_thread`
- **Channel not found:** Error with suggestion to check spelling
- **Daily file already exists:** Append new H2 sections, do not overwrite
- **Metadata missing or empty:** Create fresh, default to 24h lookback
