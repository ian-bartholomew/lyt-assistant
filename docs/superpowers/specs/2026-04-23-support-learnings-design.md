# Support Learnings Skill — Design Spec

## Context

The FES Platform team runs a Slack support channel (#fes-platform-support) that accumulates valuable tribal knowledge — what broke, why, how it was fixed, and what the workarounds are. This knowledge lives only in Slack threads and is effectively lost after a few days. This skill extracts those learnings into structured Obsidian-compatible markdown files so they become part of the user's knowledge base.

## Skill Identity

- **Name:** `support-learnings`
- **Location:** `~/.claude/skills/support-learnings/SKILL.md` (global skill)
- **Argument hint:** `[time-window] [--channel #channel-name]`
- **Default channel:** `#fes-platform-support`
- **Default time window:** Since last processed thread timestamp (from metadata), or 24h if no metadata exists

## Output

**Directory:** `~/Documents/Work/raw/support_learnings/`

### Daily Learnings File — `YYYY-MM-DD.md`

All learnings for a given day are grouped into a single file. Each thread is an H2 section.

```markdown
---
title: "Support Learnings - 2026-04-23"
type: support-learnings
channel: fes-platform-support
---

## Cassandra Connection Details for XP Marketing ID Backfill

**Thread:** [link](https://betfanatics.slack.com/archives/CHANNEL_ID/pTIMESTAMP)
**Requester:** Josh Chan
**Status:** resolved
**Tags:** cassandra, credentials, xp-migration

### Problem
Needed prod Cassandra connection details for the XP marketing ID backfill against the `id` keyspace.

### Resolution
Kareem Shahin provided the connection details via DM. JIRA ticket FANDEVX-2620 created.

### Learning
Prod Cassandra credentials are handled via DM by the platform on-call team — no self-service path exists today.

---
```

When revisiting an unresolved thread on a later date, a **new** learning entry is appended to that day's file (not the original day's file). It references the original:

```markdown
## [Update] Eventenrichment Access to Marketing Table

**Thread:** [link](https://betfanatics.slack.com/archives/CHANNEL_ID/pTIMESTAMP)
**Original Learning:** [[2026-04-23]] — "Eventenrichment Access to Marketing Table"
**Requester:** Garrett Kelley
**Status:** resolved
**Tags:** cassandra, eventenrichment, privatelink

### Update
The enrichment migration completed. EventEnrichment now runs as FES Connect pipelines with native Cassandra access.

### Learning
After FES Connect migration, services in FES space have direct Cassandra access — no PrivateLink configuration needed.
```

### Metadata File — `_metadata.yml`

Tracks all processed threads and caches channel ID lookups.

```yaml
channel_defaults:
  fes-platform-support: C06PUG6V6NT

threads:
  - ts: "1776963724.820519"
    channel: C06PUG6V6NT
    date_processed: 2026-04-23
    status: resolved
    title: "Cassandra Connection Details for XP Marketing ID Backfill"
    requester: "Josh Chan"

  - ts: "1776950305.003079"
    channel: C06PUG6V6NT
    date_processed: 2026-04-23
    status: unresolved
    title: "Eventenrichment Access to Marketing Table"
    requester: "Garrett Kelley"
```

- **Unique key:** `ts` + `channel` (prevents reprocessing)
- **`status`:** `resolved` or `unresolved`
- **`channel_defaults`:** Caches channel name → ID to avoid redundant Slack API calls

## Workflow

### Phase 1: Setup

1. Read `_metadata.yml` from `~/Documents/Work/raw/support_learnings/` (create if missing)
2. Resolve channel name → ID (check `channel_defaults` cache first, then `slack_search_channels`)
3. Determine time window:
   - Explicit argument (e.g., `3d`, `1w`) → calculate oldest timestamp
   - No argument → find latest `date_processed` in metadata → use that as oldest
   - No metadata at all → default to 24 hours ago

### Phase 2: Revisit Unresolved

For each thread in metadata with `status: unresolved`:

1. Re-read the thread via `slack_read_thread`
2. Show the user: original learning summary + current thread state
3. Ask: "Has this been resolved? Should I create an updated learning?"
4. If yes → extract updated learning, append to today's `YYYY-MM-DD.md` with `[Update]` prefix, update metadata `status` to `resolved`
5. If no/skip → leave metadata unchanged

### Phase 3: Process New Threads

1. Fetch channel messages via `slack_read_channel` with `oldest` timestamp
2. Filter out:
   - Messages with no thread replies (not a support interaction)
   - Threads already in metadata (by `ts` + `channel`)
   - Bot-only messages (Slackbot join notifications, etc.)
3. For each remaining thread (one at a time, interactive):
   a. Read full thread via `slack_read_thread`
   b. Extract: title, problem, resolution (if any), learning, requester, tags
   c. Determine status: `resolved` if a clear solution was reached, `unresolved` otherwise
   d. Present draft learning to user via `AskUserQuestion`
   e. User approves, requests edits, or skips
   f. If approved → append to today's `YYYY-MM-DD.md`, add entry to metadata
   g. If skipped → do not add to metadata (will appear again next run)

### Phase 4: Summary

Print a summary: threads processed, unresolved count, skipped count.

## Skill Frontmatter

```yaml
---
name: support-learnings
description: >
  Extract learnings from Slack support channels into structured Obsidian notes.
  Use when the user asks to "extract support learnings", "process support channel",
  "review support threads", "support-learnings", or wants to capture knowledge from
  Slack support interactions. Automatically revisits unresolved threads.
argument-hint: [time-window] [--channel #channel-name]
---
```

## Tools Required

- `Read`, `Write`, `Edit`, `Glob`, `Grep` — file operations
- `Bash` — YAML parsing if needed
- `AskUserQuestion` — interactive review of each thread
- `mcp__claude_ai_Slack__slack_search_channels` — resolve channel name → ID
- `mcp__claude_ai_Slack__slack_read_channel` — fetch channel messages
- `mcp__claude_ai_Slack__slack_read_thread` — read full thread replies

## Edge Cases

- **Empty channel / no new threads:** Report "No new threads found" and exit after revisit phase
- **Thread with only bot replies:** Skip (not a real support interaction)
- **Very long threads (100+ replies):** Paginate via cursor parameter on `slack_read_thread`
- **Channel not found:** Error with suggestion to check channel name spelling
- **Metadata file corrupted:** Warn user, offer to rebuild from existing `YYYY-MM-DD.md` files
- **Daily file already exists:** Append new sections (don't overwrite)
- **Time window argument parsing:** Support `Nd` (days), `Nw` (weeks), `Nh` (hours)

## Verification

1. Run `/support-learnings` with no arguments — should process last 24h of #fes-platform-support
2. Verify `_metadata.yml` is created with correct thread entries
3. Verify `YYYY-MM-DD.md` is created with proper frontmatter and learning sections
4. Run again — should report "No new threads" (all already processed)
5. Manually set a thread to `status: unresolved` in metadata, run again — should prompt for revisit
6. Run `/support-learnings 3d` — should process threads from 3-day window
7. Run `/support-learnings --channel #other-channel` — should target different channel
