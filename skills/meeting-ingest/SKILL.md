---
name: meeting-ingest
description: This skill should be used when the user asks to "ingest meetings", "pull zoom meetings", "sync zoom transcripts", "import zoom meetings", "process my zoom meetings", or wants to back-fill the `meetings/` folder from Zoom Cloud. Scans Zoom for the past 5 days, skips meetings that already have folders, and writes a folder + metadata + transcript + summary for each new meeting.
version: 0.1.0
allowed-tools: [Bash, Read, Write, Glob, mcp__claude_ai_Zoom_for_Claude__search_meetings, mcp__claude_ai_Zoom_for_Claude__get_meeting_assets]
---

# Meeting Ingest Skill

Pull Zoom transcripts from the past 5 days and write them to the vault's `meetings/` folder, skipping meetings that have already been ingested. For each new meeting, produce `_metadata.json`, `transcript-zoom.md`, and `summary-default.md` matching the existing vault convention.

## When to Use

Invoke this skill when:

- User runs `/lyt-assistant:meeting-ingest`
- User says "ingest meetings", "pull zoom meetings", "sync zoom transcripts", "import zoom meetings", "process my zoom meetings"
- User asks to back-fill or catch up the `meetings/` folder from Zoom

## Prerequisites

- The Zoom MCP (`claude.ai Zoom for Claude`) must be authenticated. If `mcp__claude_ai_Zoom_for_Claude__search_meetings` is unavailable, tell the user to run `/plugin` and authenticate Zoom before retrying.
- User's timezone is **America/Los_Angeles** (UTC−7 / UTC−8). All filesystem dates are LA-local; all Zoom queries use UTC.
- Vault location: `/Users/ian.bartholomew/Documents/Work/`. Meetings go in `meetings/`.

## Reference Output (Format Contract)

The output format was validated on 2026-05-11. Match it exactly:

- `/Users/ian.bartholomew/Documents/Work/meetings/2026-05-11-platform-standup/_metadata.json`
- `/Users/ian.bartholomew/Documents/Work/meetings/2026-05-11-platform-standup/transcript-zoom.md`
- `/Users/ian.bartholomew/Documents/Work/meetings/2026-05-11-platform-standup/summary-default.md`

If unsure about any structural detail, read those three files first.

## Workflow

### Step 1 — Compute the time window

Get today's date in LA. Window is the last 5 days through end of today.

```bash
TODAY_LA=$(TZ=America/Los_Angeles date +%Y-%m-%d)
FROM_LA=$(TZ=America/Los_Angeles date -v-5d +%Y-%m-%d 2>/dev/null || TZ=America/Los_Angeles date -d "5 days ago" +%Y-%m-%d)
# Convert window to UTC for the Zoom API
FROM_UTC="${FROM_LA}T07:00:00Z"     # 00:00 LA == 07:00 UTC (PDT)
TO_UTC=$(TZ=UTC date -v+1d +%Y-%m-%dT00:00:00Z 2>/dev/null || TZ=UTC date -u -d "tomorrow" +%Y-%m-%dT00:00:00Z)
echo "Window LA: $FROM_LA -> $TODAY_LA  | UTC: $FROM_UTC -> $TO_UTC"
```

### Step 2 — Query Zoom

Call `mcp__claude_ai_Zoom_for_Claude__search_meetings` with:

```json
{
  "from": "<FROM_UTC>",
  "to":   "<TO_UTC>",
  "include_zoom_my_notes": true,
  "page_size": 50
}
```

Paginate via `next_page_token` until exhausted.

### Step 3 — Filter the result list

Keep a meeting only if **all** of:

- `meeting_category == "history"` (drop scheduled/upcoming and recurring placeholders)
- `meeting_uuid` is present (drop entries without a UUID — they're calendar holds)
- At least one of: `has_transcript == true`, `has_summary == true`, or My Notes content (you'll resolve this in Step 5)

Drop meetings the user wasn't actually in (no `meeting_roles` or empty array).

### Step 4 — Index already-ingested meetings

Build a set of `meeting_uuid`s already present in `meetings/`:

```bash
cd /Users/ian.bartholomew/Documents/Work
for f in meetings/*/_metadata.json; do
  [ -f "$f" ] || continue
  jq -r 'select(.source == "zoom") | .meeting_uuid // empty' "$f"
done | sort -u > /tmp/zoom_ingested_uuids.txt
```

Skip any meeting whose `meeting_uuid` appears in that file. As a fallback for older folders without `meeting_uuid`, also collect existing folder names matching `YYYY-MM-DD-*` and use the folder-name pattern (date + slug) as a secondary check.

### Step 5 — For each new meeting (sequential)

For each meeting that survives filtering and dedup:

#### 5a. Fetch assets

Call `mcp__claude_ai_Zoom_for_Claude__get_meeting_assets` with the `meeting_uuid`.

If the result has no `transcript.transcript_items` (or empty) **and** `my_notes.content_markdown` is empty/whitespace-only, **skip** with reason "no content" and continue.

#### 5b. Compute folder name

- `date_la` = the meeting's `meeting_start_time` (or `start_time`) converted to `America/Los_Angeles`, formatted `YYYY-MM-DD`.
- `slug` = derived from `topic`:
  1. Strip any trailing `YYYY-MM-DD HH:MM(GMT...)` Zoom appends to ad-hoc meetings
  2. Lowercase
  3. Replace any run of non-alphanumeric chars with a single `-`
  4. Trim leading/trailing `-`
  5. Collapse repeated `-`
- `folder` = `meetings/{date_la}-{slug}`
- If `folder` already exists on disk, append `-{short_uuid}` where `short_uuid` is the first 8 chars of `meeting_uuid.replace("-", "").lower()`.

#### 5c. Write `_metadata.json`

```json
{
  "date": "<YYYY-MM-DD in LA>",
  "duration": "<Hh Mm Ss derived from start_time/end_time>",
  "meeting_name": "<slug>",
  "source": "zoom",
  "meeting_uuid": "<uuid>",
  "meeting_number": <int>,
  "host": "<host_name>",
  "attendees": ["<user_name>", "..."],
  "my_notes_url": "<my_notes.file_link or null>"
}
```

Pretty-print with 2-space indent.

#### 5d. Write `transcript-zoom.md`

Frontmatter:

```yaml
---
meeting: <slug>
date: <YYYY-MM-DD>
source: zoom
duration: "HH:MM:SS"
---
```

Body rules:

- Walk `transcript.transcript_items` in order. Each item has `start`, `end`, `text` (which begins with `Speaker Name: ...`).
- Parse speaker out of `text` (split on first `:`). Speaker names already include the full name (e.g. "Kareem Shahin", "peter.sutter").
- Group **consecutive items from the same speaker** into one block. Join their text bodies with a single space.
- Render each block as:

  ```markdown
  **<Speaker Name>:**
  [HH:MM:SS] <joined text>
  ```

  Use the first item's `start` time as the block timestamp (format `HH:MM:SS`, zero-padded).
- Within a same-speaker block, if the gap between two consecutive items is **> 30 seconds**, split into two paragraphs (still under the same speaker header). The second paragraph gets its own `[HH:MM:SS]` line.
- Separate blocks with a blank line.

#### 5e. Write `summary-default.md`

Frontmatter:

```yaml
---
meeting: <slug>
date: <YYYY-MM-DD>
template: default
provider: zoom-transcript
source: zoom
---
```

Body sections (in this order — omit a section only if there's truly nothing for it):

```markdown
## Meeting Summary: <Topic>
**Date:** <Month Day, Year>
**Duration:** ~<N> minutes

### Brief Overview
<2-4 sentences framing the meeting>

### Key Discussion Points
- **<Topic> (<Person>):** <one-paragraph summary>
- **<Topic> (<Person>):** <one-paragraph summary>
...

### Action Items
- [ ] **<Person>:** <action>
- [ ] **<Person>:** <action>
...

### Decisions Made
- **<short label>:** <decision>
...
```

Optional sections — include when clearly signaled in the transcript:

- `### Next Milestone (early signal)` — when participants discuss what's coming next
- `### Follow-ups` — open threads that didn't reach a decision

Synthesize from the transcript only. Do not invent facts. If a speaker is paraphrased, attribute it. Lift any direct quote that's load-bearing (e.g., a CTO commitment, a specific quantitative claim).

### Step 6 — Report

After processing all meetings, print a summary:

```markdown
## Ingest report (<FROM_LA> → <TODAY_LA>)

**Created (<N>):**
- `[[2026-05-11-platform-standup]]` — Platform Standup (18 min)
- ...

**Skipped — already ingested (<N>):**
- `[[2026-05-08-...]]`

**Skipped — no content (<N>):**
- The Golden Zone (recurring calendar block, no transcript)
- ...
```

Use Obsidian wikilinks (`[[folder-name]]`) so the user can click straight through.

## Edge Cases

- **Same meeting topic, multiple times in window**: each instance has its own `meeting_uuid`; dedup is per-UUID, not per-topic.
- **Meeting still processing**: if `get_meeting_assets` returns `transcript: null` but the meeting just ended, skip with reason "processing" and tell the user to re-run later.
- **Permission error from Zoom (403)**: log it, skip, continue. Don't abort the whole run.
- **Pagination**: if `next_page_token` is non-empty, keep calling `search_meetings` until it isn't. Limit to 5 pages defensively.
- **Slug collisions on same date**: append the short UUID. Never overwrite an existing folder.

## Anti-Patterns (Don't)

- Don't write to `wiki/_log.md` — the `meetings/` folder is user-owned per the vault's CLAUDE.md.
- Don't try to download `recording.flac` from Zoom — out of scope, and most standups don't have cloud recordings.
- Don't parallelize Zoom API calls; sequential keeps the rate limiter happy and the report ordered.
- Don't paraphrase action items in the summary if the speaker stated them verbatim — quote them.
- Don't ingest meetings outside the 5-day window even if they show up in the search — the search may return unbounded results.

## Quick sanity check before writing files

Before each `Write`, verify:

1. The target folder doesn't already exist (or apply the `-{short_uuid}` collision suffix).
2. The transcript is non-empty.
3. The slug is at least 3 chars (otherwise prepend `meeting-`).
