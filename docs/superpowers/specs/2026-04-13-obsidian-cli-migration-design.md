# Obsidian CLI Migration Design

**Date:** 2026-04-13
**Status:** Approved
**Scope:** Replace raw shell commands with Obsidian CLI, consolidate libraries, integrate obsidian-markdown skill

## Summary

Migrate the lyt-assistant plugin from raw shell commands (`find`, `grep`, `sed`, `mv`, `cat`) to the Obsidian CLI as the primary method for vault operations. Consolidate 5 library files into 2, trim skill tool lists, and reference the `obsidian:obsidian-markdown` skill for advanced markdown syntax.

## Decisions

- **CLI as primary:** Obsidian CLI replaces shell commands wherever possible. Claude Code tools (Edit) used only for inline content modifications the CLI can't handle.
- **Vault targeting:** Rely on default (most recently focused vault). No explicit `vault=` parameter.
- **Markdown skill integration:** Hybrid approach — brief inline examples for common patterns (wikilinks, frontmatter, Related sections), reference `obsidian:obsidian-markdown` for advanced syntax (callouts, embeds, block references).
- **Library consolidation:** 5 libs become 2 — `obsidian-operations.md` and `analysis.md`.
- **Tool lists:** Trimmed to `[Bash, Edit, AskUserQuestion]` for most skills. `/research` additionally gets `WebFetch` and Context7 MCP.
- **Migration approach:** Full rewrite (Approach 1). Plugin is v0.1.0, libs are instruction docs, low runtime risk.

## New Library Structure

### `lib/obsidian-operations.md`

Replaces `vault-scanner.md`, `link-parser.md`, and `frontmatter.md`. All operations use the `obsidian` CLI.

**Sections:**

1. **Pre-flight check** — `obsidian vault` to confirm Obsidian is running
2. **Vault scanning**
   - `obsidian files` — list all vault files
   - `obsidian files folder="000 - Inbox" ext=md` — list inbox files
   - `obsidian files folder="100 - MOCs" ext=md` — list MOCs
   - `obsidian folders` — list folder structure
   - `obsidian folders folder="300 - Reference"` — reference subfolder structure
3. **File operations**
   - `obsidian read file="Note"` — read file content
   - `obsidian create name="Note" content="..." silent` — create file
   - `obsidian create path="folder/Note.md" content="..."` — create at specific path
   - `obsidian move file="Note" to="destination/"` — move file
   - `obsidian rename file="Note" name="New Name"` — rename file
   - `obsidian append file="Note" content="..."` — append content
   - `obsidian prepend file="Note" content="..."` — prepend content
   - `obsidian delete file="Note"` — delete file (to trash)
4. **Properties (frontmatter)**
   - `obsidian property:set name="key" value="val" file="Note"` — set property
   - `obsidian property:set name="tags" value="tag1,tag2" type=list file="Note"` — set list property
   - `obsidian property:read name="key" file="Note"` — read property
   - `obsidian property:remove name="key" file="Note"` — remove property
   - `obsidian properties file="Note"` — list all properties
5. **Links**
   - `obsidian links file="Note"` — outgoing links
   - `obsidian backlinks file="Note"` — incoming links
   - `obsidian unresolved` — all broken links vault-wide
   - `obsidian orphans` — files with no incoming links
   - `obsidian deadends` — files with no outgoing links
6. **Search**
   - `obsidian search query="term"` — vault-wide search
   - `obsidian search query="term" path="200 - Notes"` — scoped search
   - `obsidian search query="term" total` — match count only
   - `obsidian search:context query="term"` — search with line context
7. **Tags**
   - `obsidian tags` — all tags in vault
   - `obsidian tags file="Note"` — tags for specific file
   - `obsidian tag name="tagname" verbose` — files with tag
8. **Structure analysis**
   - `obsidian outline file="Note"` — heading hierarchy
   - `obsidian file file="Note"` — file metadata (size, modified date, etc.)
   - `obsidian wordcount file="Note"` — word/character counts
9. **Common patterns**
   - Scan-and-process: scan inbox files, iterate, process each
   - Create-with-metadata: `obsidian create` then multiple `property:set` calls
   - Validate MOC links: `obsidian links` then check each target with `obsidian file`
   - Move-and-update: `obsidian move` then update properties and MOC references
10. **Multiline content** — Use `\n` for newlines in `content=` values. For large content blocks (full note bodies), prefer `obsidian create` with minimal content then `obsidian append` for the body, or use `Edit` tool after creation.
11. **Error handling**
    - Obsidian not running: `obsidian vault` fails → prompt user to open Obsidian
    - File not found: CLI error → show message, suggest alternatives
    - File already exists: `obsidian create` fails → offer rename/overwrite/cancel
    - No fallback to shell commands mid-workflow

### `lib/analysis.md`

Replaces `content-analyzer.md` and `moc-matcher.md`. Classification and matching logic remains custom; vault queries use CLI.

**Sections:**

1. **Note vs Reference classification**
   - Heuristic rules: first-person language, assertion titles, code blocks, source attribution, external quotes
   - Confidence levels: high, medium, low
   - Read content via `obsidian read`, then apply heuristics
2. **Topic extraction**
   - Extract keywords from content (technical terms, capitalized terms, hyphenated terms)
   - Use `obsidian search query="term"` for vault-wide term frequency instead of `grep -r`
   - Theme grouping: SRE, observability, incident management, performance, etc.
3. **Atomicity assessment**
   - Use `obsidian outline file="Note"` to count sections (replaces `grep -c "^## "`)
   - Use `obsidian wordcount file="Note" words` for length check
4. **Title generation**
   - Assertion-style for Notes: `[Subject] [verb] [outcome]`
   - Descriptive for References
5. **Destination suggestion**
   - Notes: flat in `200 - Notes/`
   - References: match topics to subfolders via `obsidian folders folder="300 - Reference"`
6. **MOC matching**
   - Scoring: `(keyword_matches * 2) + link_overlaps + (title_match * 3)`
   - Get MOC list via `obsidian files folder="100 - MOCs" ext=md`
   - Get MOC links via `obsidian links file="MOC Name"`
   - Confidence thresholds: high (>=5), medium (2-4), low (1)
   - New MOC detection: 3+ notes sharing uncovered topic
7. **Thematic grouping**
   - For discover-links clustering
   - Co-occurrence via `obsidian search query="term" total`

## Skill Updates

### All Skills: Common Changes

- **`allowed-tools`** trimmed to `[Bash, Edit, AskUserQuestion]` (exceptions noted below)
- **Pre-flight check** added: `obsidian vault` at start of every skill
- **Preamble reference** added: "For advanced Obsidian markdown syntax (callouts, embeds, block references), follow the obsidian:obsidian-markdown skill."
- **Lib references** updated: `lib/obsidian-operations.md` and `lib/analysis.md` replace the 5 old libs
- **Brief inline examples kept** for: wikilink syntax, frontmatter property names, `## Related` section format, MOC section structure

### `/classify-inbox`

| Operation | Old | New |
|---|---|---|
| List inbox files | `find "000 - Inbox" -name "*.md"` | `obsidian files folder="000 - Inbox" ext=md` |
| List MOCs | `find "100 - MOCs" -name "*.md"` | `obsidian files folder="100 - MOCs" ext=md` |
| Reference folder structure | `find "300 - Reference" -type d` | `obsidian folders folder="300 - Reference"` |
| Extract links | `grep -o '\[\[.*\]\]'` | `obsidian links file="Note"` |
| Search related content | `grep -rl "term" "200 - Notes"` | `obsidian search query="term" path="200 - Notes"` |
| Move file | `mv file.md dest/` | `obsidian move file="Note" to="dest/"` |
| Create frontmatter | Manual YAML + Write tool | `obsidian property:set` per field |
| Validate vault structure | `[ ! -d "000 - Inbox" ]` | `obsidian folders` and check output |

### `/create-note`

| Operation | Old | New |
|---|---|---|
| List inbox files | `find "000 - Inbox" -name "*.md"` | `obsidian files folder="000 - Inbox" ext=md` |
| Search related content | `grep -rl "term"` | `obsidian search query="term"` |
| Create file | Write tool | `obsidian create name="Note" content="..."` |
| Set properties | Manual YAML in content | `obsidian property:set` per field |
| Conflict check | `find . -name "filename.md"` | `obsidian file file="filename"` |

### `/check-moc-health`

**Gains `Bash`** in allowed-tools (didn't have it before).

| Operation | Old | New |
|---|---|---|
| List MOCs | `find "100 - MOCs" -name "*.md"` | `obsidian files folder="100 - MOCs" ext=md` |
| Broken link detection | `grep` + `find` loop | `obsidian unresolved` or `obsidian links` + validate |
| Orphan detection | `grep -rl "topic"` | `obsidian search query="topic"` + `obsidian orphans` |
| Heading hierarchy | `grep '^#'` | `obsidian outline file="MOC"` |
| File staleness | `stat -f%m` | `obsidian file file="Note"` |
| Link removal/addition | `sed` | `Edit` tool |

### `/discover-links`

| Operation | Old | New |
|---|---|---|
| List all files | `find . -name "*.md" -not -path ...` | `obsidian files` with folder filtering |
| Extract links | `grep -o '\[\[.*\]\]'` | `obsidian links file="Note"` |
| Topic matching | `grep -qi "term" file` | `obsidian search query="term"` |
| Co-occurrence counting | `grep -c` | `obsidian search query="term" total` |
| Add Related section | `sed` / `echo >>` | `Edit` tool or `obsidian append` |
| Orphan detection | Manual loop | `obsidian orphans` + `obsidian deadends` |

### `/research`

**Allowed tools:** `[Bash, Edit, WebFetch, mcp__plugin_context7_context7__query-docs, AskUserQuestion]`

| Operation | Old | New |
|---|---|---|
| Check existing topic | `grep -rl` | `obsidian search query="topic"` |
| Reference folder structure | `find "300 - Reference" -type d` | `obsidian folders folder="300 - Reference"` |
| Create file | Write tool | `obsidian create` + `obsidian property:set` |

### `/create-project`

| Operation | Old | New |
|---|---|---|
| List MOCs | `find "100 - MOCs" -name "*.md"` | `obsidian files folder="100 - MOCs" ext=md` |
| Create project file | Write tool | `obsidian create path="150 - Projects/Name.md" content="..."` |
| Read Projects MOC | `cat` | `obsidian read file="Projects MOC"` |
| Update MOC | Edit tool | `obsidian append file="Projects MOC" content="..."` or `Edit` |
| Create missing dir | `mkdir -p` | Not needed — `obsidian create` handles paths |

### `/archive-project`

| Operation | Old | New |
|---|---|---|
| List projects | `find "150 - Projects" -name "*.md"` | `obsidian files folder="150 - Projects" ext=md` |
| Read project | `cat` | `obsidian read file="Project"` |
| Move to archive | `mv` | `obsidian move file="Project" to="400 - Archive/Projects/"` |
| Update frontmatter | Edit + manual YAML | `obsidian property:set name="status" value="complete"` |
| Verify move | `ls` | `obsidian file file="Project"` |

## Files to Delete

- `lib/vault-scanner.md`
- `lib/link-parser.md`
- `lib/frontmatter.md`
- `lib/content-analyzer.md`
- `lib/moc-matcher.md`

## Files to Create

- `lib/obsidian-operations.md`
- `lib/analysis.md`

## Files to Update

- `skills/classify-inbox/SKILL.md`
- `skills/create-note/SKILL.md`
- `skills/check-moc-health/SKILL.md`
- `skills/discover-links/SKILL.md`
- `skills/research/SKILL.md`
- `skills/create-project/SKILL.md`
- `skills/archive-project/SKILL.md`

## No Changes Needed

- `.claude-plugin/plugin.json` — no changes
- `.claude-plugin/marketplace.json` — no changes
- `examples/` — can be updated later if needed
- `README.md`, `INSTALL.md`, `TESTING.md`, `CHANGELOG.md` — update after implementation
