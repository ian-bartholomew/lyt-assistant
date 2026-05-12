---
name: meeting-action-items
description: This skill should be used when the user asks to "review meeting action items", "process meeting follow-ups", "extract action items from meetings", "make todos from meetings", or wants to convert recent meeting action items into Todoist tasks. Scans `meetings/` for summaries in a configurable lookback window (default: since last run, fallback 2 days), extracts items from "### Action Items" sections, and walks the user through each one interactively (make todo / dismiss / skip). Already-handled items are tracked in `.lyt-assistant/_action-item-state.json` so they don't re-appear.
version: 0.5.0
argument-hint: "[--days N | --since YYYY-MM-DD]"
allowed-tools: [Bash, Read, Write, Edit, Glob, Grep]
---

# Meeting Action Items Skill

Walk the user through every *unseen* action item from recent meeting summaries. For each item, offer to make a Todoist task in the `#Work` project, dismiss it, or skip it. Persist decisions in `.lyt-assistant/_action-item-state.json` so handled items never re-appear.

## When to Use

Invoke this skill when:

- User runs `/lyt-assistant:meeting-action-items`
- User says "review meeting action items", "process meeting follow-ups", "extract action items from meetings", "make todos from meetings", or any variation about turning recent meetings into todos
- User wants to catch up on recent meeting follow-ups before they fall off the radar

## Prerequisites

- **Vault root:** invoke from `/Users/ian.bartholomew/Documents/Work/` (the Obsidian vault). All paths in this skill are relative to that root.
- **Todoist CLI (`td`):** must be installed and authenticated. The skill verifies this in Step 2 and exits with instructions if not.
- **`jq` and `shasum`:** used for state-file operations and key hashing. Both are present on the user's macOS.

### Assignee filter

The skill only prompts for action items assigned to Ian, the FES platform team, or a broadcast audience (e.g. "All recipients", "Everyone"). Items prefixed with another person's or team's name (e.g. `**Matt:**`, `**Equity Comp team:**`) are skipped silently in Step 7 and counted in the run summary.

The allowlist lives in `$ASSIGNEE_ALLOW` in Step 3a. Matching rules:

- The assignee prefix is split on `/`, `,`, `+`, and `&`. Joint assignees include if **any** one part matches — `**Team / Peter+Rafael:**` includes because `team` is in the allowlist; `**Ian/Matt:**` includes because `ian` is.
- Each part is compared **case-insensitively and exactly** against the allowlist (after trimming whitespace). No substring matching, so `**Equity Comp team:**` does NOT match the bare `team` entry.
- Bullets with no assignee prefix at all are **included** (treated as everyone's responsibility — change the helper if you'd rather skip them).
- Already-checked `- [x]` bullets are auto-recorded as `todoed` regardless of assignee; the filter only gates the interactive prompt path.
- Filter decisions are **not** persisted to state. Adding a new name to `$ASSIGNEE_ALLOW` will resurface previously-filtered items on the next run.

## Arguments

| Flag | Behavior |
|------|----------|
| `--since YYYY-MM-DD` | Use this calendar date as the window start (inclusive). |
| `--days N` | Use `today - N days` as the window start. |
| *(neither)* | Use the date portion of `last_run` from the state file; fall back to `today - 2 days` if no `last_run`. |

`--since` and `--days` are mutually exclusive. If both are passed, bail with `Use either --days or --since, not both.`

## State File

Path: `.lyt-assistant/_action-item-state.json` (relative to vault root).

Schema:

```json
{
  "version": 1,
  "last_run": "2026-05-11T13:52:00-04:00",
  "items": {
    "2026-05-11-platform-standup::a3f1c9d7e0b2": {
      "meeting_dir": "2026-05-11-platform-standup",
      "text": "Ian: Write up the remaining IDP plan ...",
      "status": "todoed",
      "todoist_url": "https://app.todoist.com/app/task/...",
      "decided_at": "2026-05-11T14:05:33-04:00"
    },
    "2026-05-11-platform-standup::e7b2d1a04c89": {
      "meeting_dir": "2026-05-11-platform-standup",
      "text": "Matt: Send out the bumped IAC refactor survey today ...",
      "status": "dismissed",
      "decided_at": "2026-05-11T14:06:01-04:00"
    }
  }
}
```

Field rules:

- `version` — always `1`. If a different value is encountered, bail with `Unsupported state version <v>. Update the skill or migrate the file.`
- `last_run` — ISO 8601 with timezone offset. Updated at the very end of the loop (whether quit-early or natural completion).
- `items` — keyed by `<meeting_dir>::<sha256(normalized_text)[:12]>`. Per-meeting dedupe (the same text appearing in two meetings produces two distinct entries).
- `status` — `"todoed"` or `"dismissed"` only. `"skipped"` items are never recorded.
- `todoist_url` — non-null only when `status == "todoed"` AND `td task add` returned a URL. Null for `- [x]` already-checked bullets (auto-recorded as `todoed` but not created by this skill).

## Workflow

### Step 1 — Parse arguments and compute start date

```bash
# Reject mutually exclusive flags
if [[ -n "$ARG_DAYS" && -n "$ARG_SINCE" ]]; then
  echo "Use either --days or --since, not both."
  exit 1
fi

TODAY=$(date +%Y-%m-%d)

if [[ -n "$ARG_SINCE" ]]; then
  START_DATE="$ARG_SINCE"
elif [[ -n "$ARG_DAYS" ]]; then
  START_DATE=$(date -v-"${ARG_DAYS}"d +%Y-%m-%d 2>/dev/null || date -d "${ARG_DAYS} days ago" +%Y-%m-%d)
else
  # Try state file's last_run
  STATE_FILE=".lyt-assistant/_action-item-state.json"
  if [[ -f "$STATE_FILE" ]]; then
    LAST_RUN=$(jq -er '.last_run // empty' "$STATE_FILE" 2>/dev/null || true)
  fi
  if [[ -n "$LAST_RUN" ]]; then
    START_DATE="${LAST_RUN%%T*}"  # date portion only
  else
    START_DATE=$(date -v-2d +%Y-%m-%d 2>/dev/null || date -d "2 days ago" +%Y-%m-%d)
  fi
fi

echo "Window: $START_DATE -> $TODAY (inclusive)"
```

The window keys off the **directory-name date**, not on `last_run` timestamp granularity. A meeting from earlier today can re-appear in a second same-day run if any of its items remain undecided — the per-item state filter prevents re-prompting for already-handled ones.

### Step 2 — Verify Todoist authentication

```bash
if ! td auth status >/dev/null 2>&1; then
  echo "Todoist CLI is not authenticated. Run 'td auth login' and try again."
  exit 1
fi
```

Do NOT run `td auth login` automatically — it's an interactive OAuth flow that needs the user's hands on the keyboard.

### Step 3 — Initialize state

```bash
STATE_DIR=".lyt-assistant"
STATE_FILE="$STATE_DIR/_action-item-state.json"
mkdir -p "$STATE_DIR"

if [[ -f "$STATE_FILE" ]]; then
  # Validate JSON
  if ! jq -e '.' "$STATE_FILE" >/dev/null 2>&1; then
    echo "State file corrupt: $STATE_FILE. Move or fix it, then re-run."
    exit 1
  fi
  # Validate version
  STATE_VERSION=$(jq -r '.version' "$STATE_FILE")
  if [[ "$STATE_VERSION" != "1" ]]; then
    echo "Unsupported state version $STATE_VERSION. Update the skill or migrate the file."
    exit 1
  fi
else
  # First-run sentinel; will be materialized on first write
  echo '{"version": 1, "last_run": null, "items": {}}' > "$STATE_FILE"
fi
```

### Step 3a — Define helpers and counters

Define all helper functions and initialize the run counters **before** entering the meeting loop. Later steps call these by name.

```bash
# Run counters (referenced in Step 7/8 handlers and Step 9 summary)
N_TODOED=0
N_DISMISSED=0
N_SKIPPED=0
N_FILTERED=0   # items skipped by the assignee filter in Step 7

# Allowlist of normalized assignee values that should pass the filter. Each
# entry is matched case-insensitively after splitting the raw assignee on
# `/`, `,`, `+`, and `&` and trimming whitespace — any single part matching
# any entry in this list flips the whole item to "included".
#
# To change who counts as "me" or extend the team-level allow set, edit this
# array directly. Add/remove names rather than tweaking the matching logic.
ASSIGNEE_ALLOW=(
  # Self
  "ian" "ian bartholomew" "ian-bartholomew" "ian b" "ian b." "ian bart" "me"
  # Broadcast assignees
  "all" "all recipients" "all hands" "all employees" "everyone"
  # FES platform team variants
  "team" "fes" "fes team" "fes platform" "fes platform team"
  "platform" "platform team" "sre" "sre team"
)

# Extract Action Items bullets from a summary file
extract_action_items() {
  local file="$1"
  awk '
    BEGIN { inside = 0 }
    {
      line = $0
      stripped = line
      gsub(/\*\*/, "", stripped)
    }
    /^#{1,6} / {
      if (inside) { exit }
      hdr = stripped
      sub(/^#+ +/, "", hdr)
      sub(/^[0-9]+\.? +/, "", hdr)
      if (tolower(hdr) ~ /^action items[[:space:]]*$/) {
        inside = 1
        next
      }
      next
    }
    inside && /^[[:space:]]*[-*]/ { print }
  ' "$file"
}

# Normalize bullet text for hashing. The Word-colon strip is intentionally
# greedy and will eat labels like "Action:" or "TODO:" as well as person
# prefixes — accepted trade-off; keeps keys stable for the common case.
normalize() {
  local s="$1"
  s="$(echo "$s" | sed -E 's/^[[:space:]]*[-*][[:space:]]+(\[[ xX]\][[:space:]]+)?//')"
  s="$(echo "$s" | sed -E 's/^\*\*[A-Za-z][A-Za-z0-9 ,/+&-]*:\*\*[[:space:]]+//')"
  s="$(echo "$s" | sed -E 's/^[A-Za-z][A-Za-z0-9 ,/+&.-]*:[[:space:]]+//')"
  s="$(echo "$s" | tr -s '[:space:]' ' ' | sed -E 's/^ //; s/ $//' | tr '[:upper:]' '[:lower:]')"
  printf '%s' "$s"
}

# Composite key = "<meeting_dir>::<sha256(normalized)[:12]>"
key_for() {
  local meeting_dir="$1" normalized="$2"
  local hash
  hash=$(printf '%s' "$normalized" | shasum -a 256 | cut -c1-12)
  printf '%s::%s' "$meeting_dir" "$hash"
}

# Extract the assignee prefix from a raw bullet. Returns the name(s) inside
# `**...**` (preferred) or the bare `Name:` prefix. Strips a trailing colon
# if the markdown emphasis wraps it (the common `**Ian:**` style). Empty
# output means the bullet has no assignee prefix.
extract_assignee() {
  local raw="$1" body
  # Strip the leading bullet marker + optional checkbox.
  body=$(printf '%s' "$raw" | sed -E 's/^[[:space:]]*[-*][[:space:]]+(\[[ xX]\][[:space:]]+)?//')
  # `[[:space:]]*` (not `+`) so `**Matt:**no-space-after-bold` still parses as
  # an assignee prefix — otherwise such bullets bypass the filter and look
  # unassigned. `-` is placed last in the bare-name char class to be safe in
  # POSIX bracket expressions (no escaping needed there).
  if [[ "$body" =~ ^\*\*([^*]+)\*\*[[:space:]]* ]]; then
    # **Ian:** style — capture inside the asterisks, then drop trailing colon.
    local inner="${BASH_REMATCH[1]}"
    printf '%s' "${inner%:}"
  elif [[ "$body" =~ ^([A-Za-z][A-Za-z0-9\ /,+\&.-]*):[[:space:]] ]]; then
    # Ian: style — capture up to the first colon.
    printf '%s' "${BASH_REMATCH[1]}"
  fi
}

# Decide whether an assignee is in scope. Returns 0 (include) for:
#   - empty assignee (no prefix → treat as everyone's item, don't filter)
#   - any single split-part matching an entry in $ASSIGNEE_ALLOW
# Returns 1 (skip) otherwise. Splits the raw assignee on `/`, `,`, `+`, and
# `&` so joint assignees like "Team / Peter+Rafael" or "Ian/Matt" include if
# *any* one part is allowed. Exact-match on each part (after lowercasing and
# trimming) — no substring matching, so "Equity Comp team" does NOT match
# the bare "team" entry.
should_include_assignee() {
  local assignee="$1" part allowed
  [[ -z "$assignee" ]] && return 0
  # `printf '%s\n'` ensures a trailing newline so `read` consumes the final
  # part. Without it, single-part inputs like "Ian" would be silently
  # dropped because they have no line terminator.
  while IFS= read -r part; do
    part="${part#"${part%%[![:space:]]*}"}"   # ltrim
    part="${part%"${part##*[![:space:]]}"}"   # rtrim
    [[ -z "$part" ]] && continue
    for allowed in "${ASSIGNEE_ALLOW[@]}"; do
      if [[ "$part" == "$allowed" ]]; then
        return 0
      fi
    done
  done < <(printf '%s\n' "$assignee" | tr '[:upper:]' '[:lower:]' | tr '/,+&' '\n')
  return 1
}

# ISO 8601 timestamp with strict ":"-separated TZ offset
iso_now() {
  local now
  now=$(date "+%Y-%m-%dT%H:%M:%S%z")
  printf '%s' "${now:0:${#now}-2}:${now: -2}"
}

# Write an item entry to state.json. todoist_url_json must be a valid JSON
# value: a quoted string ('"..."') or the literal 'null'.
record_state() {
  local key="$1" meeting_dir="$2" text="$3" status="$4" todoist_url_json="$5"
  local now entry
  now=$(iso_now)

  entry=$(jq -n \
    --arg meeting_dir "$meeting_dir" \
    --arg text "$text" \
    --arg status "$status" \
    --argjson todoist_url "$todoist_url_json" \
    --arg decided_at "$now" \
    '{meeting_dir: $meeting_dir, text: $text, status: $status, todoist_url: $todoist_url, decided_at: $decided_at}')

  jq --arg k "$key" --argjson e "$entry" '.items[$k] = $e' "$STATE_FILE" \
    > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"
}

# Update last_run on state.json (called once at the end)
update_last_run() {
  local now
  now=$(iso_now)
  jq --arg t "$now" '.last_run = $t' "$STATE_FILE" \
    > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"
}

# Single-form editor prompt. Opens $EDITOR (default: nvim) on a tempfile
# pre-filled with all four task fields — title, due, priority, description —
# so the user can review and edit them in one pass instead of being prompted
# one-by-one. Updates the global variables TITLE, DESC, DUE, PRIO on return.
#
# Tempfile format (the parser is forgiving of blank lines and `#` comments
# above the `---` separator):
#
#     # Edit the fields below, then save & exit.
#     # title/due/priority go above `---`; description is everything below.
#
#     title: <suggested>
#     due:
#     priority: p3
#     ---
#     <suggested description, possibly multi-line>
#
# If a field is missing or empty after the edit, the corresponding suggestion
# is restored. If the `---` separator is missing entirely, the whole file is
# treated as the description and title/due/priority fall back to suggestions.
#
# IMPORTANT: $EDITOR must be a blocking editor. GUI editors like `code` or
# `subl` return immediately unless invoked with `--wait` / `-w`, which would
# cause this function to read the tempfile before the user has saved. If
# $EDITOR is graphical, set `EDITOR='code --wait'` (or equivalent) before
# running the skill.
prompt_edit_all() {
  local s_title="$1" s_desc="$2" s_due="$3" s_prio="$4"
  local tmp line key val in_desc=0

  TITLE="$s_title"; DESC=""; DUE="$s_due"; PRIO="$s_prio"

  if ! tmp=$(mktemp -t maitem.XXXXXX 2>/dev/null); then
    echo "mktemp failed; using all suggestions unedited." >&2
    DESC="$s_desc"
    return
  fi

  {
    printf '# Edit the fields below, then save & exit.\n'
    printf '# title/due/priority go above `---`; description is everything below.\n'
    printf '# Lines starting with `#` above the separator are comments and ignored.\n'
    printf '\n'
    printf 'title: %s\n' "$s_title"
    printf 'due: %s\n' "$s_due"
    printf 'priority: %s\n' "$s_prio"
    printf -- '---\n'
    printf '%s\n' "$s_desc"
  } > "$tmp"

  "${EDITOR:-nvim}" "$tmp" </dev/tty >/dev/tty 2>&1

  # Parse — single pass, switching to description mode at the first `---` line.
  while IFS= read -r line || [[ -n "$line" ]]; do
    if (( in_desc )); then
      if [[ -z "$DESC" ]]; then
        DESC="$line"
      else
        DESC="$DESC"$'\n'"$line"
      fi
      continue
    fi
    # Above the separator: skip blanks and `#` comments.
    if [[ "$line" == "---" ]]; then
      in_desc=1
      continue
    fi
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ -z "${line//[[:space:]]/}" ]] && continue
    if [[ "$line" =~ ^([a-zA-Z_]+):[[:space:]]*(.*)$ ]]; then
      key="${BASH_REMATCH[1]}"
      val="${BASH_REMATCH[2]}"
      # rtrim trailing whitespace from val
      val="${val%"${val##*[![:space:]]}"}"
      case "$key" in
        title) [[ -n "$val" ]] && TITLE="$val" ;;
        due) DUE="$val" ;;
        priority|prio) [[ -n "$val" ]] && PRIO="$val" ;;
      esac
    fi
  done < "$tmp"

  rm -f "$tmp"

  # Strip leading/trailing blank lines from DESC.
  while [[ "$DESC" == $'\n'* ]]; do DESC="${DESC#$'\n'}"; done
  while [[ "$DESC" == *$'\n' ]]; do DESC="${DESC%$'\n'}"; done
  # Whitespace-only DESC counts as empty — fall back to the suggestion so we
  # don't ship a whitespace string to `td task add`.
  [[ -z "${DESC//[[:space:]]/}" ]] && DESC="$s_desc"
}
```

### Step 4 — Discover meetings in window

```bash
# List meetings/<date>-* directories where <date> >= START_DATE.
# Directory names sort lexically; ISO date prefixes sort identically to date order.
MEETINGS=()
for d in meetings/*/; do
  name="${d%/}"; name="${name##*/}"
  # Must match YYYY-MM-DD prefix
  if [[ ! "$name" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}- ]]; then continue; fi
  date_part="${name:0:10}"
  if [[ "$date_part" < "$START_DATE" ]]; then continue; fi
  MEETINGS+=("$name")
done

if [[ ${#MEETINGS[@]} -eq 0 ]]; then
  echo "No meetings found in window."
  # Still update last_run before exit
  update_last_run
  exit 0
fi
```

### Step 5 — Extract action items per meeting

For each meeting, pick the summary file and slurp bullets under the Action Items heading.

**Pick the summary file:**

```bash
SUMMARY=""
if [[ -f "meetings/$M/summary-default.md" ]]; then
  SUMMARY="meetings/$M/summary-default.md"
else
  # Fall back to alphabetically first summary-*.md
  for f in "meetings/$M"/summary-*.md; do
    if [[ -f "$f" ]]; then SUMMARY="$f"; break; fi
  done
fi

if [[ -z "$SUMMARY" ]]; then
  echo "$M: no summary-*.md, skipping"
  continue
fi
```

**Extract bullets under the Action Items heading** (using `extract_action_items` from Step 3a). The heading matches `#{1,6} [optional **] [optional N.] action items [optional **]` (case-insensitive). Bullets are every non-blank, non-heading line until the next heading or EOF:

```bash
# bash 3.2-safe (macOS system bash has no `mapfile`/`readarray`)
BULLETS=()
while IFS= read -r line; do
  BULLETS+=("$line")
done < <(extract_action_items "$SUMMARY")

if [[ ${#BULLETS[@]} -eq 0 ]]; then
  echo "$M: no action items, skipping"
  continue
fi
```

### Step 6 — Normalize and key each bullet

Use `normalize` and `key_for` from Step 3a. `normalize` strips the bullet marker, optional checkbox, optional person prefix (`**Person:**` or `Person:`), collapses whitespace, and lowercases. `key_for` produces `<meeting_dir>::<sha256(normalized)[:12]>`. No new code at this step — Step 7 calls them directly.

### Step 7 — Filter against state, by assignee; auto-handle `- [x]` bullets

Across **all** meetings discovered in Step 4, build three parallel arrays (`ITEM_KEYS`, `ITEM_DIRS`, `ITEM_RAWS`) of items that need user attention. Parallel arrays (rather than a single delimited string) keep bullet text containing `|`, `:`, or other separators safe.

Items are filtered out at this step if their assignee prefix is not in `$ASSIGNEE_ALLOW` (defined in Step 3a). The filter is intentionally **not** persisted to the state file — if you later add a new name to the allow list, previously-filtered items will resurface on the next run. The trade-off is that filtered items get re-evaluated every run, which is fast (a few string ops per bullet). Already-checked `- [x]` bullets are still auto-recorded as `todoed` regardless of assignee — they're done, no need to filter.

```bash
ITEM_KEYS=()
ITEM_DIRS=()
ITEM_RAWS=()

# Inside the per-meeting loop (after BULLETS is populated for the current $M):
for raw in "${BULLETS[@]}"; do
  NORM=$(normalize "$raw")
  if [[ -z "$NORM" ]]; then continue; fi  # skip empty after normalization
  KEY=$(key_for "$M" "$NORM")

  # Skip if already in state (any status)
  if jq -e --arg k "$KEY" '.items[$k] // empty' "$STATE_FILE" >/dev/null 2>&1; then
    continue
  fi

  # Auto-record [x] bullets as todoed (no prompt, no URL) — these are done
  # regardless of who they were assigned to; record before assignee filtering.
  if [[ "$raw" =~ ^[[:space:]]*[-*][[:space:]]+\[[xX]\] ]]; then
    record_state "$KEY" "$M" "$raw" "todoed" "null"
    continue
  fi

  # Assignee filter — skip bullets owned by people not in $ASSIGNEE_ALLOW.
  ASSIGNEE=$(extract_assignee "$raw")
  if ! should_include_assignee "$ASSIGNEE"; then
    (( N_FILTERED++ ))
    continue
  fi

  ITEM_KEYS+=("$KEY")
  ITEM_DIRS+=("$M")
  ITEM_RAWS+=("$raw")
done
```

After all meetings are processed, if no items are pending:

```bash
FILTERED_NOTE=""
if (( N_FILTERED > 0 )); then
  FILTERED_NOTE=" ($N_FILTERED filtered by assignee)"
fi

if [[ ${#ITEM_KEYS[@]} -eq 0 ]]; then
  echo "Nothing new in the window across ${#MEETINGS[@]} meeting(s)$FILTERED_NOTE."
  update_last_run
  exit 0
fi
echo "Found ${#ITEM_KEYS[@]} new action items across ${#MEETINGS[@]} meeting(s)$FILTERED_NOTE."
```

### Step 8 — Interactive loop

> **EXECUTOR REQUIREMENT — read this before touching the loop.**
>
> Run the bash code in this step verbatim. Do **not** substitute any tool-based picker UI (`AskUserQuestion`, structured choice prompts, multi-select menus, etc.) for any prompt in this loop. Tool pickers hide the suggested title and description and short-circuit the `$EDITOR` editing flow, which defeats the entire point of this skill. The user must see the suggested title and description in the action prompt **and** get the single-form editor with all four fields pre-filled when `t` is picked.
>
> The bash `read` / `prompt_edit_all` flow is required in all cases. **There is no condition under which a tool-based picker is acceptable here** — not when you think it'd be clearer, not when you have only one item, not ever. If you cannot run interactive bash (e.g. you have no TTY), stop and tell the user; do not fall back to a picker.

Iterate the parallel arrays from Step 7 **one item at a time**. For each item print a prompt block and wait for the user's response before moving to the next. Never batch multiple items into a single prompt, never auto-decide, and never assume a default action — every undecided item gets its own round-trip with the user.

The action prompt shows the raw bullet **plus** the suggested title and description that `t` would pre-fill, so the user can see what they'd be editing before they commit to "make todo":

```
[2 of 7]  2026-05-11-platform-standup

  - [ ] **Ian:** Write up the remaining IDP plan (3 of 4 epics) as a one-pager / Confluence page so the team can continue the work.

  Suggested title:        Write up the remaining IDP plan (3 of 4 epics) as a one-pager…
  Suggested description:
    Write up the remaining IDP plan (3 of 4 epics) as a one-pager / Confluence page so the team can continue the work.

    From meeting: platform-standup (2026-05-11)

  [t] make todo (edit fields)   [d] dismiss   [s] skip   [q] quit
> _
```

When the user picks `t`, open all four fields in `$EDITOR` (default `nvim`) at once via `prompt_edit_all`. The user reviews and edits a single tempfile, saves, and exits — no one-field-at-a-time prompting. The tempfile looks like:

```
# Edit the fields below, then save & exit.
# title/due/priority go above `---`; description is everything below.
# Lines starting with `#` above the separator are comments and ignored.

title: Write up the remaining IDP plan (3 of 4 epics) as a one-pager…
due:
priority: p3
---
Write up the remaining IDP plan (3 of 4 epics) as a one-pager / Confluence page so the team can continue the work.

From meeting: platform-standup (2026-05-11)
```

Field semantics:

1. **Title** — Todoist task content. Suggestion: bullet body with marker, checkbox, and `**Person:**` prefix stripped, truncated to ~70 chars on a word boundary.
2. **Description** — everything below the `---` separator. Suggestion: full action item body + `From meeting: <slug> (<YYYY-MM-DD>)` footer.
3. **Due** — natural-language or `YYYY-MM-DD`. Default blank (no due date); `--due` is omitted from `td task add` if the user leaves it empty.
4. **Priority** — `p1`–`p4`. Default `p3`.

Notes for the executor:

- Read a single response token for the top-level action choice — typically a one-character reply (`t`, `d`, `s`, `q`). Accept the first non-whitespace char and treat anything else as invalid (re-prompt this item).
- For the `t` path, call `prompt_edit_all` once. Do not break it back into per-field prompts.
- The suggested title and description must be computed **before** the action prompt is displayed so they can be shown in it. Compute them once and reuse the same values when `t` is picked.
- State writes are streamed inside each branch — a quit (`q`) or crash preserves everything decided so far.

```bash
TOTAL=${#ITEM_KEYS[@]}
for i in "${!ITEM_KEYS[@]}"; do
  KEY="${ITEM_KEYS[$i]}"
  M="${ITEM_DIRS[$i]}"
  raw="${ITEM_RAWS[$i]}"
  IDX=$((i + 1))

  # --- Compute suggestions BEFORE the action prompt so they can be shown. ---

  # Body: bullet with checkbox + **Person:** / Person: prefix stripped.
  BODY=$(echo "$raw" | sed -E 's/^[[:space:]]*[-*][[:space:]]+(\[[ xX]\][[:space:]]+)?//; s/^\*\*[^*]+\*\*[[:space:]]+//; s/^[A-Za-z][A-Za-z0-9 ,/+&-]*:[[:space:]]+//')

  # Suggested brief title: truncate BODY to ~70 chars on a word boundary when
  # possible, falling back to a hard mid-word cut. Append an ellipsis when
  # truncated, then strip trailing punctuation.
  if [[ ${#BODY} -le 70 ]]; then
    SUGGESTED_TITLE="$BODY"
  else
    SLICE="${BODY:0:70}"
    TRIMMED="${SLICE% *}"
    # `% *` is a no-op when the slice contains no space (one long token);
    # in that case keep the hard 70-char cut rather than the whole slice.
    if [[ "$TRIMMED" != "$SLICE" ]]; then
      SUGGESTED_TITLE="${TRIMMED}…"
    else
      SUGGESTED_TITLE="${SLICE}…"
    fi
  fi
  SUGGESTED_TITLE=$(echo "$SUGGESTED_TITLE" | sed -E 's/[[:space:]]*[.,;:]+$//')

  # Meeting display: parse "YYYY-MM-DD-slug" -> "slug (YYYY-MM-DD)".
  M_DATE="${M:0:10}"
  M_NAME="${M:11}"
  MEETING_LABEL="$M_NAME ($M_DATE)"

  # Suggested description: full body + provenance footer (meeting name + date).
  SUGGESTED_DESC="$BODY"$'\n\n'"From meeting: $MEETING_LABEL"

  # Indent each line of the suggested description by 4 spaces for the prompt block.
  SUGGESTED_DESC_INDENTED="    ${SUGGESTED_DESC//$'\n'/$'\n'    }"

  # --- Action prompt: shows raw bullet + the two suggestions side-by-side. ---

  printf '\n[%d of %d]  %s\n\n  %s\n\n  Suggested title:        %s\n  Suggested description:\n%s\n\n  [t] make todo (edit fields)   [d] dismiss   [s] skip   [q] quit\n> ' \
    "$IDX" "$TOTAL" "$M" "$raw" "$SUGGESTED_TITLE" "$SUGGESTED_DESC_INDENTED"
  read -r CHOICE
  CHOICE="${CHOICE:0:1}"

  case "$CHOICE" in
    q) break ;;
    s) (( N_SKIPPED++ )) ;;
    d)
      record_state "$KEY" "$M" "$raw" "dismissed" "null"
      (( N_DISMISSED++ ))
      ;;
    t)
      # Open all four fields in $EDITOR at once. prompt_edit_all sets the
      # globals TITLE / DESC / DUE / PRIO.
      echo "Opening task fields in ${EDITOR:-nvim} — save & exit to continue."
      prompt_edit_all "$SUGGESTED_TITLE" "$SUGGESTED_DESC" "" "p3"

      # td task add with description; --due is optional.
      TD_CMD=(td task add "$TITLE" --project "Work" --priority "$PRIO" --description "$DESC")
      if [[ -n "$DUE" ]]; then TD_CMD+=(--due "$DUE"); fi

      while true; do
        if OUT=$("${TD_CMD[@]}" 2>&1); then
          # td prints "https://app.todoist.com/app/task/..." on success
          TODOIST_URL=$(printf '%s\n' "$OUT" | grep -oE 'https://app\.todoist\.com/app/task/[^[:space:]]+' | head -1)
          # Always pass a valid JSON value for --argjson: quoted string or literal null
          if [[ -n "$TODOIST_URL" ]]; then
            TODOIST_URL_JSON="\"$TODOIST_URL\""
            echo "✓ Created — $TODOIST_URL"
          else
            TODOIST_URL_JSON="null"
            echo "✓ Created (no URL returned by td)"
          fi
          record_state "$KEY" "$M" "$raw" "todoed" "$TODOIST_URL_JSON"
          (( N_TODOED++ ))
          break
        else
          echo "td failed: $OUT"
          printf '  [r] retry   [d] dismiss   [s] skip: '
          read -r RETRY
          case "${RETRY:0:1}" in
            r) continue ;;
            d) record_state "$KEY" "$M" "$raw" "dismissed" "null"; (( N_DISMISSED++ )); break ;;
            s) (( N_SKIPPED++ )); break ;;
            *) echo "  invalid; treating as skip"; (( N_SKIPPED++ )); break ;;
          esac
        fi
      done
      ;;
    *)
      echo "  invalid choice; skipping"
      (( N_SKIPPED++ ))
      ;;
  esac
done
```

### Step 9 — Finalize

Update `last_run` (using `update_last_run` from Step 3a) and print the end-of-run summary. Reached on natural completion OR after `q` quit OR after Step 4 / Step 7 early-exit paths — `last_run` is updated in all cases.

```bash
update_last_run
SUMMARY="Made $N_TODOED todos, dismissed $N_DISMISSED, skipped $N_SKIPPED."
if (( N_FILTERED > 0 )); then
  SUMMARY="$SUMMARY Filtered $N_FILTERED items by assignee."
fi
echo "$SUMMARY"
```

## Edge Cases

| Condition | Behavior |
|-----------|----------|
| State file missing | First run. Window defaults to `today - 2 days`. File is materialized in Step 3. |
| State file corrupt JSON | Bail with `State file corrupt: <path>. Move or fix it, then re-run.` Do not auto-recover. |
| State `version` ≠ 1 | Bail with `Unsupported state version <v>.` |
| Meeting folder doesn't match `YYYY-MM-DD-` prefix | Skip silently in Step 4. |
| Summary file missing in a meeting folder | Log `<dir>: no summary-*.md, skipping` and continue. |
| No Action Items heading in a summary | Log `<dir>: no action items, skipping` and continue. |
| Action Items section is empty | Log `<dir>: no action items, skipping` and continue. |
| `td auth status` fails before loop | Exit early with auth hint; do NOT start the loop. |
| `td task add` fails mid-loop | Show stderr; offer `[r]etry / [d]ismiss / [s]kip` on that item. Don't write state until success. |
| Both `--days` and `--since` passed | Bail with `Use either --days or --since, not both.` |
| No new items in window | Print `Nothing new in the window across N meeting(s).` Still update `last_run` and exit clean. |
| User quits with `q` mid-loop | Flush state to disk, update `last_run`, print summary, exit 0. Per-item decisions made before `q` are already persisted (streaming writes). |
| `$EDITOR` unset | `prompt_edit_all` defaults to `nvim`. If `nvim` isn't installed either, the editor invocation fails — set `EDITOR=vi` (or any installed editor) and re-run that item. |
| `$EDITOR` is a GUI editor without a wait flag (`code`, `subl`, etc.) | The editor process forks and returns immediately; the skill reads the tempfile before the user saves, so all four fields silently revert to the suggested defaults. Set `EDITOR='code --wait'`, `EDITOR='subl -w'`, etc. before running. |
| `mktemp` fails (disk full, `/tmp` unwritable) | `prompt_edit_all` prints `mktemp failed; using all suggestions unedited.` to stderr and proceeds with the suggested values (title, description, blank due, p3 priority). Free space or fix `/tmp` perms if you need to edit. |
| User deletes the `---` separator | The parser never enters description mode; the file is treated as key-value lines only. `DESC` stays empty and falls back to the suggested description. Title/due/priority also fall back if their lines were deleted. To deliberately keep the description blank, leave the area below `---` empty rather than removing the separator. |
| User wipes the file or makes the description whitespace-only | Description falls back to the suggestion (a whitespace-only string is treated as empty so it doesn't leak into `td task add`). To deliberately clear a field, leave its value empty (`title:`, `due:`, etc.) — empty title and priority fall back to the suggestion; empty due means "no due date". |
| User edits priority to an invalid value (not `p1`–`p4`) | Passed through to `td task add`, which rejects it. The skill falls into the standard `td failed` retry/dismiss/skip prompt. |
| Executor substitutes a tool-based picker (`AskUserQuestion`, structured choice) for the action prompt | Wrong — the user loses the suggested title/description preview and the editing flow. Step 8's executor-requirement callout forbids this. If you can't run interactive bash with a TTY, stop and tell the user; do not fall back to a picker. |
| Action item has no assignee prefix (no `**Name:**` or `Name:`) | Included — treated as everyone's responsibility. Change `should_include_assignee` to `return 1` for empty assignees if you'd rather skip these. |
| Joint assignee like `**Ian / Matt:**` or `**Team / Peter+Rafael:**` | Included if **any** split-part is in `$ASSIGNEE_ALLOW`. Split happens on `/`, `,`, `+`, `&`. |
| Bullet prefix is `**Equity Comp team:**` or `**Marketing Team:**` | Excluded — exact-match against `$ASSIGNEE_ALLOW` (not substring), so `"team"` alone in the allowlist doesn't pull in `"equity comp team"`. Add the specific name to the allowlist to override. |
| Update `$ASSIGNEE_ALLOW` to add a new alias | Edit the array in Step 3a directly. No state migration needed — previously-filtered items will resurface on the next run because filter decisions aren't persisted. |

## Examples

### Example 1 — First run on a clean vault

```
User: /lyt-assistant:meeting-action-items

Window: 2026-05-09 -> 2026-05-11 (inclusive)
Found 7 new action items across 2 meetings.

[1 of 7]  2026-05-11-platform-standup

  - [ ] **Ian:** Write up the remaining IDP plan (3 of 4 epics) as a one-pager / Confluence page so the team can continue the work.

  Suggested title:        Write up the remaining IDP plan (3 of 4 epics) as a one-pager…
  Suggested description:
    Write up the remaining IDP plan (3 of 4 epics) as a one-pager / Confluence page so the team can continue the work.

    From meeting: platform-standup (2026-05-11)

  [t] make todo (edit fields)   [d] dismiss   [s] skip   [q] quit
> t

Opening task fields in nvim — save & exit to continue.

  (editor opens with a single tempfile containing all four fields:

     # Edit the fields below, then save & exit.
     # title/due/priority go above `---`; description is everything below.

     title: Write up the remaining IDP plan (3 of 4 epics) as a one-pager…
     due:
     priority: p3
     ---
     Write up the remaining IDP plan (3 of 4 epics) as a one-pager / Confluence page so the team can continue the work.

     From meeting: platform-standup (2026-05-11)

   — user edits any/all of: title, due, priority, description, then saves & exits)

✓ Created — https://app.todoist.com/app/task/write-up-remaining-idp-epics-8Jx4mVr72kPn3QwB

[2 of 7]  2026-05-11-platform-standup
...
```

### Example 2 — Second run, items deduped

```
User: /lyt-assistant:meeting-action-items

Window: 2026-05-11 -> 2026-05-11 (inclusive)
Nothing new in the window across 1 meeting(s).
```

Already-decided items are filtered out before the prompt. A `--days 7` override would re-scan a wider window without re-prompting on the same items.

### Example 3 — Mid-loop quit

```
[3 of 7]  2026-04-28-standup

  - [ ] **Kareem:** Lead shadowing sessions for service onboarding ...

  Suggested title:        Lead shadowing sessions for service onboarding
  Suggested description:
    Lead shadowing sessions for service onboarding ...

    From meeting: standup (2026-04-28)

  [t] make todo (edit fields)   [d] dismiss   [s] skip   [q] quit
> q

Made 2 todos, dismissed 0, skipped 0.
```

Re-running the skill will surface items 3-7 again (item-3 was never decided, so it re-appears). State for items 1-2 is preserved.

## Related Skills

- **`/lyt-assistant:meeting-ingest`** — sibling skill that backfills the `meetings/` folder from Zoom Cloud. Run that first if you've fallen behind on transcript ingestion.
- **`todoist`** — global user-level skill (`~/.claude/skills/todoist-cli/`) that documents the `td` CLI's full surface. This skill uses `td task add` and `td auth status`; see the todoist skill for richer task management (listing, updating, completing).
