# Obsidian CLI Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace raw shell commands with Obsidian CLI, consolidate 5 lib files into 2, update all 7 skills to use CLI-first patterns with trimmed tool lists and obsidian-markdown skill references.

**Architecture:** Two new library files (`lib/obsidian-operations.md` for CLI operations, `lib/analysis.md` for classification/matching logic) replace five old libs. All seven skills are rewritten to reference the new libs, use CLI commands instead of shell, and carry minimal `allowed-tools` lists.

**Tech Stack:** Obsidian CLI (`obsidian` command), Claude Code plugin skill/lib markdown format, Obsidian Flavored Markdown.

**Spec:** `docs/superpowers/specs/2026-04-13-obsidian-cli-migration-design.md`

---

## File Map

### Files to Create

- `lib/obsidian-operations.md` — All CLI-based vault operations (scanning, files, properties, links, search, tags, patterns, errors)
- `lib/analysis.md` — Content classification, topic extraction, MOC matching, thematic grouping

### Files to Rewrite

- `skills/classify-inbox/SKILL.md` — CLI commands, trimmed tools, new lib refs
- `skills/create-note/SKILL.md` — CLI commands, trimmed tools, new lib refs
- `skills/check-moc-health/SKILL.md` — CLI commands, trimmed tools (gains Bash), new lib refs
- `skills/discover-links/SKILL.md` — CLI commands, trimmed tools, new lib refs
- `skills/research/SKILL.md` — CLI commands, trimmed tools (keeps WebFetch + Context7), new lib refs
- `skills/create-project/SKILL.md` — CLI commands, trimmed tools, new lib refs
- `skills/archive-project/SKILL.md` — CLI commands, trimmed tools, new lib refs

### Files to Delete

- `lib/vault-scanner.md`
- `lib/link-parser.md`
- `lib/frontmatter.md`
- `lib/content-analyzer.md`
- `lib/moc-matcher.md`

---

## Task 1: Create `lib/obsidian-operations.md`

**Files:**

- Create: `lib/obsidian-operations.md`

- [ ] **Step 1: Write `lib/obsidian-operations.md`**

Write the complete library file with the following content structure. This file replaces `vault-scanner.md`, `link-parser.md`, and `frontmatter.md`.

```markdown
# Obsidian Operations Library

This utility provides instructions for all vault operations using the Obsidian CLI. Requires Obsidian to be running.

All skills should use these CLI commands instead of raw shell commands (`find`, `grep`, `sed`, `mv`, `cat`).

## Pre-flight Check

Before any vault operation, verify Obsidian is running:

\`\`\`bash
obsidian vault
\`\`\`

If this fails, present to the user:

\`\`\`
Obsidian doesn't appear to be running. This plugin requires an open Obsidian vault.

Options:
A) Open Obsidian and retry
B) Cancel
\`\`\`

Use **AskUserQuestion** to get their choice. Do not proceed with vault operations until the pre-flight check passes.

## Vault Scanning

### List Files by Folder

\`\`\`bash
# All vault files
obsidian files

# Inbox files
obsidian files folder="000 - Inbox" ext=md

# MOC files
obsidian files folder="100 - MOCs" ext=md

# Project files
obsidian files folder="150 - Projects" ext=md

# Note files
obsidian files folder="200 - Notes" ext=md

# Reference files
obsidian files folder="300 - Reference" ext=md

# Archive files
obsidian files folder="400 - Archive" ext=md
\`\`\`

### List Folders

\`\`\`bash
# All vault folders
obsidian folders

# Reference subfolder structure (for destination suggestions)
obsidian folders folder="300 - Reference"

# Archive structure
obsidian folders folder="400 - Archive"
\`\`\`

### File Counts

\`\`\`bash
obsidian files folder="000 - Inbox" ext=md total
obsidian files folder="100 - MOCs" ext=md total
obsidian files folder="200 - Notes" ext=md total
obsidian files folder="300 - Reference" ext=md total
\`\`\`

### Validate LYT Vault Structure

To confirm the vault follows LYT conventions, check that expected folders exist:

\`\`\`bash
obsidian folders
\`\`\`

Verify the output contains: `000 - Inbox`, `100 - MOCs`, `150 - Projects`, `200 - Notes`, `300 - Reference`, `400 - Archive`. If any are missing, warn the user:

\`\`\`
This doesn't appear to be a complete LYT vault. Missing folders: [list]
\`\`\`

## File Operations

### Read File Content

\`\`\`bash
# By name (resolves like a wikilink)
obsidian read file="My Note"

# By exact path
obsidian read path="200 - Notes/My Note.md"
\`\`\`

### Create File

\`\`\`bash
# Create with name (goes to vault root by default)
obsidian create name="My Note" content="# My Note\n\nContent here" silent

# Create at specific path
obsidian create path="200 - Notes/My Note.md" content="# My Note\n\nContent here" silent

# Create from template
obsidian create name="My Note" template="Note Template" silent

# Overwrite existing
obsidian create name="My Note" content="..." overwrite silent
\`\`\`

**Multiline content:** Use `\n` for newlines in `content=` values. For large content blocks, prefer creating with minimal content then using `obsidian append` for the body, or use the `Edit` tool after creation.

### Move File

\`\`\`bash
# Move to folder
obsidian move file="My Note" to="200 - Notes/"

# Move to specific path (rename + move)
obsidian move file="My Note" to="200 - Notes/New Name.md"
\`\`\`

### Rename File

\`\`\`bash
obsidian rename file="My Note" name="Better Title"
\`\`\`

Obsidian automatically updates all links pointing to the renamed file.

### Append Content

\`\`\`bash
obsidian append file="My Note" content="\n## Related\n\n- [[Other Note]]"
\`\`\`

### Prepend Content

\`\`\`bash
obsidian prepend file="My Note" content="Updated: 2026-04-13\n\n"
\`\`\`

### Delete File

\`\`\`bash
# Move to trash (safe)
obsidian delete file="My Note"

# Permanent delete (use with caution)
obsidian delete file="My Note" permanent
\`\`\`

## Properties (Frontmatter)

The CLI manages YAML frontmatter properties directly. No manual YAML parsing needed.

### Set a Property

\`\`\`bash
# Text property
obsidian property:set name="status" value="active" file="My Note"

# Date property
obsidian property:set name="created" value="2026-04-13" type=date file="My Note"

# List property (tags, mocs)
obsidian property:set name="tags" value="sre,reliability" type=list file="My Note"

# Checkbox property
obsidian property:set name="reviewed" value="true" type=checkbox file="My Note"
\`\`\`

### Read a Property

\`\`\`bash
obsidian property:read name="status" file="My Note"
obsidian property:read name="tags" file="My Note"
obsidian property:read name="mocs" file="My Note"
\`\`\`

### Remove a Property

\`\`\`bash
obsidian property:remove name="next_action" file="My Note"
\`\`\`

### List All Properties

\`\`\`bash
# All properties for a file
obsidian properties file="My Note"

# All properties for a file in YAML format
obsidian properties file="My Note" format=yaml

# All properties used across the vault
obsidian properties
\`\`\`

### Common Property Patterns

**Set up a new Note's metadata:**
\`\`\`bash
obsidian property:set name="tags" value="topic1,topic2" type=list file="My Note"
obsidian property:set name="created" value="2026-04-13" type=date file="My Note"
obsidian property:set name="mocs" value="[[MOC Name]]" type=list file="My Note"
\`\`\`

**Set up a new Reference's metadata:**
\`\`\`bash
obsidian property:set name="tags" value="topic1,topic2" type=list file="My Ref"
obsidian property:set name="created" value="2026-04-13" type=date file="My Ref"
obsidian property:set name="type" value="external" file="My Ref"
obsidian property:set name="source" value="https://example.com" file="My Ref"
obsidian property:set name="mocs" value="[[MOC Name]]" type=list file="My Ref"
\`\`\`

**Set up a new Project's metadata:**
\`\`\`bash
obsidian property:set name="type" value="project" file="My Project"
obsidian property:set name="status" value="active" file="My Project"
obsidian property:set name="area" value="Infrastructure" file="My Project"
obsidian property:set name="due_date" value="2026-06-01" type=date file="My Project"
obsidian property:set name="next_action" value="Define scope" file="My Project"
obsidian property:set name="tags" value="project-tag" type=list file="My Project"
obsidian property:set name="created" value="2026-04-13" type=date file="My Project"
\`\`\`

**Complete a Project:**
\`\`\`bash
obsidian property:set name="status" value="complete" file="My Project"
obsidian property:set name="completed_date" value="2026-04-13" type=date file="My Project"
obsidian property:remove name="next_action" file="My Project"
\`\`\`

## Links

### Outgoing Links

\`\`\`bash
# All links from a file
obsidian links file="My Note"

# Link count
obsidian links file="My Note" total
\`\`\`

### Backlinks (Incoming Links)

\`\`\`bash
# All files linking to this one
obsidian backlinks file="My Note"

# With counts
obsidian backlinks file="My Note" counts

# Backlink count only
obsidian backlinks file="My Note" total

# As JSON for parsing
obsidian backlinks file="My Note" format=json
\`\`\`

### Broken Links (Unresolved)

\`\`\`bash
# All unresolved links in vault
obsidian unresolved

# Count only
obsidian unresolved total

# With source file info
obsidian unresolved verbose

# As JSON
obsidian unresolved format=json
\`\`\`

### Orphaned Files (No Incoming Links)

\`\`\`bash
# Files nobody links to
obsidian orphans

# Count only
obsidian orphans total
\`\`\`

### Dead-End Files (No Outgoing Links)

\`\`\`bash
# Files that link to nothing
obsidian deadends

# Count only
obsidian deadends total
\`\`\`

## Search

### Basic Search

\`\`\`bash
# Vault-wide search
obsidian search query="error budget"

# Scoped to folder
obsidian search query="error budget" path="200 - Notes"

# Limit results
obsidian search query="error budget" limit=5

# Count only
obsidian search query="error budget" total

# Case sensitive
obsidian search query="SLO" case
\`\`\`

### Search with Context

\`\`\`bash
# Shows matching lines with surrounding context
obsidian search:context query="error budget"

# Scoped
obsidian search:context query="error budget" path="300 - Reference"

# As JSON for parsing
obsidian search:context query="error budget" format=json
\`\`\`

## Tags

### List Tags

\`\`\`bash
# All tags in vault
obsidian tags

# Tags for a specific file
obsidian tags file="My Note"

# With counts
obsidian tags counts

# Sorted by frequency
obsidian tags sort=count counts

# Tag count only
obsidian tags total
\`\`\`

### Tag Details

\`\`\`bash
# Files with a specific tag
obsidian tag name="sre" verbose

# Count of files with tag
obsidian tag name="sre" total
\`\`\`

## Structure Analysis

### Heading Outline

\`\`\`bash
# Tree format (default)
obsidian outline file="My MOC"

# Markdown format
obsidian outline file="My MOC" format=md

# JSON for parsing
obsidian outline file="My MOC" format=json

# Heading count
obsidian outline file="My MOC" total
\`\`\`

### File Metadata

\`\`\`bash
# File info (path, size, dates)
obsidian file file="My Note"
\`\`\`

Use this for:
- Checking if a file exists (returns info) vs doesn't exist (returns error)
- Getting modification dates for staleness checks
- Confirming file location after moves

### Word Count

\`\`\`bash
# Full count
obsidian wordcount file="My Note"

# Words only
obsidian wordcount file="My Note" words

# Characters only
obsidian wordcount file="My Note" characters
\`\`\`

## Tasks

### List Tasks

\`\`\`bash
# All incomplete tasks
obsidian tasks todo

# All completed tasks
obsidian tasks done

# Tasks in a specific file
obsidian tasks file="My Project" todo

# Task count
obsidian tasks todo total
\`\`\`

## Common Workflow Patterns

### Scan and Process Inbox

\`\`\`bash
# 1. Pre-flight
obsidian vault

# 2. List inbox files
obsidian files folder="000 - Inbox" ext=md

# 3. For each file, read and analyze
obsidian read file="Inbox Note"

# 4. After classification, move to destination
obsidian move file="Inbox Note" to="200 - Notes/"

# 5. Set properties on moved file
obsidian property:set name="tags" value="tag1,tag2" type=list file="Inbox Note"
obsidian property:set name="created" value="2026-04-13" type=date file="Inbox Note"
obsidian property:set name="mocs" value="[[MOC Name]]" type=list file="Inbox Note"

# 6. Add Related section
obsidian append file="Inbox Note" content="\n## Related\n\n- [[Related Note]]"
\`\`\`

### Create Note with Full Metadata

\`\`\`bash
# 1. Create file with content
obsidian create path="200 - Notes/My insight about X.md" content="# My insight about X\n\nContent here." silent

# 2. Set all properties
obsidian property:set name="tags" value="topic1,topic2" type=list file="My insight about X"
obsidian property:set name="created" value="2026-04-13" type=date file="My insight about X"
obsidian property:set name="mocs" value="[[Relevant MOC]]" type=list file="My insight about X"

# 3. Add Related section
obsidian append file="My insight about X" content="\n## Related\n\n- [[Related Note 1]]\n- [[Related Note 2]]"
\`\`\`

### Validate MOC Links

\`\`\`bash
# 1. Get all outgoing links from MOC
obsidian links file="SRE Concepts MOC"

# 2. Check for unresolved links vault-wide (or specific to MOC)
obsidian unresolved verbose

# 3. Find orphans that might belong in this MOC
obsidian orphans

# 4. Check heading structure
obsidian outline file="SRE Concepts MOC"
\`\`\`

### Move and Update (Archive Project)

\`\`\`bash
# 1. Update status properties
obsidian property:set name="status" value="complete" file="My Project"
obsidian property:set name="completed_date" value="2026-04-13" type=date file="My Project"
obsidian property:remove name="next_action" file="My Project"

# 2. Move to archive
obsidian move file="My Project" to="400 - Archive/Projects/"

# 3. Verify new location
obsidian file file="My Project"
\`\`\`

## Output Formats

Use `format=json` when you need to parse structured data programmatically.
Use `format=tsv` for tabular data.
Use default text format for human-readable output shown to the user.
Use `total` flag when you only need a count.

## Error Handling

### Obsidian Not Running

If `obsidian vault` fails:
\`\`\`
Obsidian doesn't appear to be running. This plugin requires an open Obsidian vault.

Options:
A) Open Obsidian and retry
B) Cancel
\`\`\`

### File Not Found

If a CLI command returns a "file not found" error:
\`\`\`
File "[name]" not found in vault.

Options:
A) Search for similar files
B) Create the file
C) Cancel
\`\`\`

Use `obsidian search query="partial name"` to suggest alternatives.

### File Already Exists

If `obsidian create` fails because the file exists (and `overwrite` flag not set):
\`\`\`
File "[name]" already exists at [path].

Options:
A) Choose a different name
B) Overwrite existing file
C) Open existing file
D) Cancel
\`\`\`

### General CLI Errors

If a CLI command fails mid-workflow:
- Report the error to the user
- Offer to retry the specific operation
- Do NOT silently fall back to shell commands
- Do NOT mix CLI and shell approaches within a single workflow run

## Integration with Analysis Library

This library handles all vault I/O. The **lib/analysis.md** library handles classification and matching logic. Skills should:

1. Use **obsidian-operations** to read content and scan the vault
2. Pass content to **analysis** logic for classification, topic extraction, MOC matching
3. Use **obsidian-operations** to execute the resulting actions (create, move, set properties, append links)

## Best Practices

1. **Always run pre-flight check** before any vault operation
2. **Use `silent` flag** on `create` to prevent files from opening in Obsidian
3. **Use `file=` for name-based resolution** (like wikilinks) and `path=` for exact paths
4. **Use `format=json`** when parsing output programmatically
5. **Use `total` flag** when you only need counts
6. **Set properties individually** rather than trying to write raw YAML
7. **Use `obsidian append`** for adding sections rather than rewriting entire files
8. **Check `obsidian file`** to verify a file exists before operating on it
9. **Use `obsidian unresolved`** instead of manual link validation loops
10. **Use `obsidian orphans`** instead of manual backlink scanning loops
```

- [ ] **Step 2: Review the file for completeness against the spec**

Read back `lib/obsidian-operations.md` and verify it covers all 11 sections from the spec:

1. Pre-flight check
2. Vault scanning
3. File operations
4. Properties (frontmatter)
5. Links
6. Search
7. Tags
8. Structure analysis
9. Common patterns
10. Multiline content
11. Error handling

- [ ] **Step 3: Commit**

```bash
git add lib/obsidian-operations.md
git commit -m "Add obsidian-operations library replacing vault-scanner, link-parser, frontmatter"
```

---

## Task 2: Create `lib/analysis.md`

**Files:**

- Create: `lib/analysis.md`

- [ ] **Step 1: Write `lib/analysis.md`**

Write the complete library file. This replaces `content-analyzer.md` and `moc-matcher.md`. Classification logic is custom; vault queries reference `lib/obsidian-operations.md` CLI commands.

```markdown
# Analysis Library

This utility provides instructions for content classification, topic extraction, MOC matching, and thematic grouping. Uses Obsidian CLI (via **lib/obsidian-operations.md**) for all vault queries.

## Note vs Reference Classification

The fundamental distinction in LYT:

- **Notes (200 - Notes/)**: Ideas you've internalized, your own synthesis and insights
- **Reference (300 - Reference/)**: Things you look up, external information and documentation

### Heuristic Rules

**Strong Note indicators:**

1. **First-person language:** "I think...", "In my experience...", "I've learned...", "My understanding is..."
2. **Assertion-style title:** "Circuit breakers prevent cascading failures", "Error budgets decouple reliability from velocity"
3. **Personal synthesis:** Connections between concepts, opinion, interpretation, lessons learned
4. **Short and focused:** Single clear idea (atomic), few paragraphs
5. **No external quotes:** Written entirely in the author's voice

**Strong Reference indicators:**

1. **External content:** Quotes from articles/books/docs, code snippets, commands, configuration examples
2. **Source attribution:** "According to [source]...", URLs, book citations, author names
3. **How-to instructions:** Step-by-step procedures, runbooks, configuration guides
4. **Multiple topics:** Several distinct sections, comprehensive coverage, reference lookup format
5. **Code blocks:** Extensive code examples or configuration

### Classification Algorithm

To classify content:

1. Read file content: `obsidian read file="Note Name"`
2. Check for Note indicators (first-person language, assertion title, personal synthesis)
3. Check for Reference indicators (source attribution, code blocks, external quotes)
4. If both present, assess which dominates
5. Assign confidence level

### Confidence Levels

- **High:** Clear indicators, no ambiguity. Single type dominates.
- **Medium:** Some indicators of both types, but one is stronger. Proceed with suggestion but note the ambiguity.
- **Low:** Mixed signals, roughly equal. Ask the user to clarify.

### Handling Ambiguity

When confidence is low, present to the user:

\`\`\`
This content has mixed signals:
- Has first-person language (Note indicator)
- Has code blocks (Reference indicator)

Help me decide:
1. Is this your synthesis/opinion (Note), or documentation/lookup (Reference)?
2. Will this need regular updates from external sources?
3. Do you reference this for lookup, or is it an insight?
\`\`\`

Use **AskUserQuestion** to get their decision.

### Project Detection

Content may also be a Project (150 - Projects/). Project indicators:
- Action items, task lists, deadlines
- Goal or deliverable descriptions
- "Need to", "we should", "by [date]"
- Multiple phases or milestones

If project detected, suggest using `/create-project` for proper hub creation.

## Topic Extraction

### Extract Keywords from Content

Read content with `obsidian read`, then identify:

1. **Technical terms:** Capitalized acronyms (SLO, SRE, API), hyphenated terms (error-budget, circuit-breaker)
2. **Domain terms:** Compound phrases (service level objective, error budget, circuit breaker)
3. **Heading terms:** Words from H2/H3 headings (use `obsidian outline file="Note" format=md`)

### Vault-Wide Term Frequency

To check how prevalent a topic is across the vault:

\`\`\`bash
obsidian search query="error budget" total
\`\`\`

This replaces the old `grep -r "term" | wc -l` pattern.

### Theme Grouping

Common themes to detect (extend based on vault content):

- **Reliability:** SLO, SLI, error budget, availability, uptime
- **Observability:** metrics, logs, traces, monitoring, alerting
- **Incident management:** incident, postmortem, on-call, pager, runbook
- **Performance:** latency, throughput, capacity, scalability
- **Deployment:** release, rollback, canary, feature flag

Match extracted topics to themes for grouping suggestions.

## Atomicity Assessment

Notes should cover a single concept. To assess:

### Count Sections

\`\`\`bash
obsidian outline file="Note" total
\`\`\`

If more than 4 headings, the note may cover multiple topics. Suggest splitting:

\`\`\`
Multiple topics detected ([count] sections).
Consider splitting into separate notes:
- Note 1: [First topic from headings]
- Note 2: [Second topic from headings]
\`\`\`

### Check Length

\`\`\`bash
obsidian wordcount file="Note" words
\`\`\`

- **Under 500 words:** Good for a Note (focused)
- **Over 500 words:** May be Reference material or needs splitting
- **Under 50 words:** Very brief — could be a placeholder or needs expansion

## Title Generation

### For Notes (Assertion-Style)

Pattern: `[Subject] [verb] [outcome]`

Examples:
- "Circuit breakers prevent cascading failures"
- "Error budgets enable feature velocity"
- "Exponential backoff reduces thundering herd"
- "Graceful degradation maintains user experience"

Extract the main claim from the first paragraph or conclusion. Simplify to assertion form.

### For References (Descriptive)

Use the topic name directly:
- "Terraform State Management Guide"
- "Circuit Breaker Pattern"
- "PostgreSQL Performance Tuning"

## Destination Suggestion

### Notes

Notes go flat in `200 - Notes/`:

\`\`\`
200 - Notes/Circuit breakers prevent cascading failures.md
\`\`\`

### References

References go in topic-specific subfolders. Match topics to existing structure:

\`\`\`bash
obsidian folders folder="300 - Reference"
\`\`\`

Compare extracted topics against folder names. Suggest the closest match:

\`\`\`
Suggested destination: 300 - Reference/SRE-Concepts/
\`\`\`

If no good match exists, offer options:
\`\`\`
Topics [new-topic] don't match existing folders.

Options:
A) Create new folder: "300 - Reference/new-topic/"
B) Place in closest match: "300 - Reference/SRE-Concepts/"
C) Specify custom location
\`\`\`

### Projects

Projects go in `150 - Projects/`.

## MOC Matching

### Algorithm

For a piece of content with extracted topics:

1. **Get all MOCs:**
   \`\`\`bash
   obsidian files folder="100 - MOCs" ext=md
   \`\`\`

2. **For each MOC, calculate score:**

   **A. Keyword match (weight: 2x):** Read MOC content with `obsidian read file="MOC Name"`. Count how many content topics appear in the MOC.

   **B. Link overlap (weight: 1x):** Get MOC links with `obsidian links file="MOC Name"`. Count how many link targets overlap with content topics.

   **C. Title match (weight: 3x):** Check if MOC title contains any content topic.

   **Total:** `(keyword_matches * 2) + link_overlaps + (title_match * 3)`

3. **Assign confidence:**
   - **High (score >= 5):** Multiple keyword matches, clear thematic fit
   - **Medium (score 2-4):** Some matches, related but not primary
   - **Low (score 1):** Weak connection

4. **Return top 2-3 matches** with confidence and reasoning.

### Presentation Format

\`\`\`
Suggested MOCs:
  - [[SLOs MOC]] (high confidence) — 3 keyword matches, title match
  - [[SRE Concepts MOC]] (medium confidence) — 1 keyword match, parent MOC
\`\`\`

### New MOC Detection

Suggest creating a new MOC when:

1. **3+ notes share an uncovered topic:**
   \`\`\`bash
   obsidian search query="reliability patterns" total
   \`\`\`
   If count >= 3 and no MOC covers this topic, suggest creation.

2. **Existing MOC is too large:**
   \`\`\`bash
   obsidian links file="Big MOC" total
   \`\`\`
   If > 30 links, suggest splitting into sub-MOCs.

3. **Topic is a subsection of existing MOC** with 10+ items — suggest extracting to its own MOC.

### MOC Naming

Follow patterns:
- Topic + MOC: "Reliability Patterns MOC"
- Category + MOC: "SRE Concepts MOC"
- Domain + MOC: "Terraform MOC"

### Validation

Before suggesting a MOC:
- Verify it exists: `obsidian file file="MOC Name"`
- Verify it's not archived: check it's in `100 - MOCs/`, not `400 - Archive/`
- Don't suggest "Home" or "Index" MOCs unless content is top-level organizational

## Thematic Grouping (for Link Discovery)

### Co-occurrence Analysis

For discovering missing links between notes:

1. Build a topic index by reading files and extracting topics
2. For each pair of files sharing topics but not linking to each other, record a suggestion
3. Group suggestions by theme using the theme categories above

### Confidence Scoring

For each link suggestion:

\`\`\`bash
# Keyword frequency in target file
obsidian search:context query="term" format=json

# Check if term appears in headings
obsidian outline file="Note" format=md
\`\`\`

Score: `keyword_frequency + (heading_match * 2) + (same_folder * 1)`

Thresholds:
- **High (>= 5):** Strong topical overlap
- **Medium (2-4):** Related content
- **Low (1):** Weak connection

### Filtering

Skip suggestions where:
- Topic mentioned only once in passing
- File already has > 15 links (over-linked)
- Files are in completely different domains

\`\`\`bash
obsidian links file="Note" total
\`\`\`

If > 15, note the file is already well-connected and only show high-confidence suggestions.

## Integration with Obsidian Operations

This library handles analysis logic. For all vault I/O, use **lib/obsidian-operations.md** commands:

- Read content: `obsidian read`
- Scan vault: `obsidian files`, `obsidian folders`
- Check links: `obsidian links`, `obsidian backlinks`
- Search: `obsidian search`
- Get structure: `obsidian outline`, `obsidian wordcount`
```

- [ ] **Step 2: Review the file for completeness against the spec**

Read back `lib/analysis.md` and verify it covers all 7 sections from the spec:

1. Note vs Reference classification
2. Topic extraction
3. Atomicity assessment
4. Title generation
5. Destination suggestion
6. MOC matching
7. Thematic grouping

- [ ] **Step 3: Commit**

```bash
git add lib/analysis.md
git commit -m "Add analysis library replacing content-analyzer and moc-matcher"
```

---

## Task 3: Delete old library files

**Files:**

- Delete: `lib/vault-scanner.md`
- Delete: `lib/link-parser.md`
- Delete: `lib/frontmatter.md`
- Delete: `lib/content-analyzer.md`
- Delete: `lib/moc-matcher.md`

- [ ] **Step 1: Delete the 5 old library files**

```bash
git rm lib/vault-scanner.md lib/link-parser.md lib/frontmatter.md lib/content-analyzer.md lib/moc-matcher.md
```

- [ ] **Step 2: Verify only the 2 new libs remain**

```bash
ls lib/
```

Expected output:

```
analysis.md
obsidian-operations.md
```

- [ ] **Step 3: Commit**

```bash
git add -A lib/
git commit -m "Remove old library files replaced by obsidian-operations and analysis"
```

---

## Task 4: Rewrite `/classify-inbox` skill

**Files:**

- Rewrite: `skills/classify-inbox/SKILL.md`

- [ ] **Step 1: Write the updated `skills/classify-inbox/SKILL.md`**

Key changes from original:

- Frontmatter: `allowed-tools: [Bash, Edit, AskUserQuestion]`
- Add obsidian-markdown skill reference in preamble
- Replace all `find`, `grep`, `mv`, `sed` commands with CLI equivalents
- Reference `lib/obsidian-operations.md` and `lib/analysis.md` instead of old 5 libs
- Add pre-flight check as Step 1
- Vault validation uses `obsidian folders` instead of `[ ! -d ]`
- File moves use `obsidian move` instead of `mv`
- Frontmatter uses `obsidian property:set` instead of manual YAML
- Related content search uses `obsidian search` instead of `grep -rl`
- Link extraction uses `obsidian links` instead of `grep '\[\['`
- Keep inline examples for: wikilink syntax, frontmatter property names, `## Related` format
- Keep all interactive workflow logic (AskUserQuestion options A-E), error handling patterns, and user-facing output formats
- Keep the overall workflow structure (scan, analyze, suggest, present, execute, verify, report)

Write the complete skill file preserving the existing workflow structure, interactive patterns, and presentation format while replacing all vault operations with CLI commands.

- [ ] **Step 2: Verify the skill file has correct frontmatter**

Check that frontmatter contains:

```yaml
---
name: classify-inbox
description: [same as before]
version: 0.2.0
allowed-tools: [Bash, Edit, AskUserQuestion]
---
```

- [ ] **Step 3: Commit**

```bash
git add skills/classify-inbox/SKILL.md
git commit -m "Rewrite classify-inbox skill to use Obsidian CLI"
```

---

## Task 5: Rewrite `/create-note` skill

**Files:**

- Rewrite: `skills/create-note/SKILL.md`

- [ ] **Step 1: Write the updated `skills/create-note/SKILL.md`**

Key changes from original:

- Frontmatter: `allowed-tools: [Bash, Edit, AskUserQuestion]`
- Add obsidian-markdown skill reference in preamble
- Reference `lib/obsidian-operations.md` and `lib/analysis.md`
- Add pre-flight check
- Inbox listing uses `obsidian files folder="000 - Inbox" ext=md`
- File reading uses `obsidian read`
- Related content search uses `obsidian search`
- File creation uses `obsidian create` + `obsidian property:set`
- Conflict check uses `obsidian file file="name"` (exists = info returned, not found = error)
- Atomicity check uses `obsidian outline` + `obsidian wordcount`
- Keep all interactive workflow logic, templates, and presentation format

Write the complete skill file.

- [ ] **Step 2: Verify frontmatter**

```yaml
---
name: create-note
description: [same as before]
version: 0.2.0
allowed-tools: [Bash, Edit, AskUserQuestion]
---
```

- [ ] **Step 3: Commit**

```bash
git add skills/create-note/SKILL.md
git commit -m "Rewrite create-note skill to use Obsidian CLI"
```

---

## Task 6: Rewrite `/check-moc-health` skill

**Files:**

- Rewrite: `skills/check-moc-health/SKILL.md`

- [ ] **Step 1: Write the updated `skills/check-moc-health/SKILL.md`**

Key changes from original:

- Frontmatter: `allowed-tools: [Bash, Edit, AskUserQuestion]` (gains Bash, didn't have it before)
- Add obsidian-markdown skill reference in preamble
- Reference `lib/obsidian-operations.md` and `lib/analysis.md`
- Add pre-flight check
- MOC listing uses `obsidian files folder="100 - MOCs" ext=md`
- MOC reading uses `obsidian read`
- Link extraction uses `obsidian links file="MOC"`
- Broken link detection uses `obsidian unresolved` (replaces grep+find loop)
- Heading hierarchy uses `obsidian outline file="MOC"` (replaces `grep '^#'`)
- Orphan detection uses `obsidian orphans` + `obsidian search`
- Staleness uses `obsidian file file="Note"` (replaces `stat -f%m`)
- Stub creation uses `obsidian create` + `obsidian property:set`
- Link addition to MOC uses `Edit` tool or `obsidian append`
- Keep all interactive workflow, report format, fix options

Write the complete skill file.

- [ ] **Step 2: Verify frontmatter**

```yaml
---
name: check-moc-health
description: [same as before]
version: 0.2.0
allowed-tools: [Bash, Edit, AskUserQuestion]
---
```

- [ ] **Step 3: Commit**

```bash
git add skills/check-moc-health/SKILL.md
git commit -m "Rewrite check-moc-health skill to use Obsidian CLI"
```

---

## Task 7: Rewrite `/discover-links` skill

**Files:**

- Rewrite: `skills/discover-links/SKILL.md`

- [ ] **Step 1: Write the updated `skills/discover-links/SKILL.md`**

Key changes from original:

- Frontmatter: `allowed-tools: [Bash, Edit, AskUserQuestion]`
- Add obsidian-markdown skill reference in preamble
- Reference `lib/obsidian-operations.md` and `lib/analysis.md`
- Add pre-flight check
- File listing uses `obsidian files` with folder filtering
- Link extraction uses `obsidian links file="Note"`
- Topic search uses `obsidian search query="term"`
- Co-occurrence counting uses `obsidian search query="term" total`
- Orphan detection uses `obsidian orphans` + `obsidian deadends`
- Link addition uses `Edit` tool or `obsidian append`
- Over-link check uses `obsidian links file="Note" total`
- Keep all grouping logic, interactive review, bidirectional linking patterns

Write the complete skill file.

- [ ] **Step 2: Verify frontmatter**

```yaml
---
name: discover-links
description: [same as before]
version: 0.2.0
allowed-tools: [Bash, Edit, AskUserQuestion]
---
```

- [ ] **Step 3: Commit**

```bash
git add skills/discover-links/SKILL.md
git commit -m "Rewrite discover-links skill to use Obsidian CLI"
```

---

## Task 8: Rewrite `/research` skill

**Files:**

- Rewrite: `skills/research/SKILL.md`

- [ ] **Step 1: Write the updated `skills/research/SKILL.md`**

Key changes from original:

- Frontmatter: `allowed-tools: [Bash, Edit, WebFetch, mcp__plugin_context7_context7__query-docs, AskUserQuestion]`
- Add obsidian-markdown skill reference in preamble
- Reference `lib/obsidian-operations.md` and `lib/analysis.md`
- Add pre-flight check
- Existing topic check uses `obsidian search query="topic"`
- Reference folder structure uses `obsidian folders folder="300 - Reference"`
- File creation uses `obsidian create` + `obsidian property:set`
- Related note search uses `obsidian search`
- Keep WebFetch and Context7 for research strategy
- Keep all interactive workflow, source quality guidelines, synthesis patterns

Write the complete skill file.

- [ ] **Step 2: Verify frontmatter**

```yaml
---
name: research
description: [same as before]
version: 0.2.0
argument-hint: <topic>
allowed-tools: [Bash, Edit, WebFetch, mcp__plugin_context7_context7__query-docs, AskUserQuestion]
---
```

- [ ] **Step 3: Commit**

```bash
git add skills/research/SKILL.md
git commit -m "Rewrite research skill to use Obsidian CLI"
```

---

## Task 9: Rewrite `/create-project` skill

**Files:**

- Rewrite: `skills/create-project/SKILL.md`

- [ ] **Step 1: Write the updated `skills/create-project/SKILL.md`**

Key changes from original:

- Frontmatter: `allowed-tools: [Bash, Edit, AskUserQuestion]`
- Add obsidian-markdown skill reference in preamble
- Reference `lib/obsidian-operations.md` and `lib/analysis.md`
- Add pre-flight check
- MOC listing uses `obsidian files folder="100 - MOCs" ext=md`
- Project file creation uses `obsidian create path="150 - Projects/Name.md" content="..."` + `obsidian property:set` for each field
- Reading Projects MOC uses `obsidian read file="Projects MOC"`
- Updating MOC uses `obsidian append file="Projects MOC" content="..."` or `Edit`
- No `mkdir -p` needed — `obsidian create` handles paths
- Keep all interactive prompts, templates, error handling

Write the complete skill file.

- [ ] **Step 2: Verify frontmatter**

```yaml
---
name: create-project
description: [same as before]
version: 0.2.0
allowed-tools: [Bash, Edit, AskUserQuestion]
---
```

- [ ] **Step 3: Commit**

```bash
git add skills/create-project/SKILL.md
git commit -m "Rewrite create-project skill to use Obsidian CLI"
```

---

## Task 10: Rewrite `/archive-project` skill

**Files:**

- Rewrite: `skills/archive-project/SKILL.md`

- [ ] **Step 1: Write the updated `skills/archive-project/SKILL.md`**

Key changes from original:

- Frontmatter: `allowed-tools: [Bash, Edit, AskUserQuestion]`
- Add obsidian-markdown skill reference in preamble
- Reference `lib/obsidian-operations.md` and `lib/analysis.md`
- Add pre-flight check
- Project listing uses `obsidian files folder="150 - Projects" ext=md`
- Project reading uses `obsidian read file="Project Name"`
- Frontmatter updates use `obsidian property:set` (status, completed_date) and `obsidian property:remove` (next_action)
- Move to archive uses `obsidian move file="Project" to="400 - Archive/Projects/"`
- Verify move uses `obsidian file file="Project"`
- Projects MOC reading uses `obsidian read file="Projects MOC"`
- Projects MOC updating uses `Edit` tool
- Keep all interactive workflow, knowledge extraction, lessons learned capture

Write the complete skill file.

- [ ] **Step 2: Verify frontmatter**

```yaml
---
name: archive-project
description: [same as before]
version: 0.2.0
allowed-tools: [Bash, Edit, AskUserQuestion]
---
```

- [ ] **Step 3: Commit**

```bash
git add skills/archive-project/SKILL.md
git commit -m "Rewrite archive-project skill to use Obsidian CLI"
```

---

## Task 11: Final review and verification

**Files:**

- Review: all files in `lib/` and `skills/`

- [ ] **Step 1: Verify file structure**

```bash
ls lib/
ls skills/*/SKILL.md
```

Expected `lib/`:

```
analysis.md
obsidian-operations.md
```

Expected skills (7 files):

```
skills/archive-project/SKILL.md
skills/check-moc-health/SKILL.md
skills/classify-inbox/SKILL.md
skills/create-note/SKILL.md
skills/create-project/SKILL.md
skills/discover-links/SKILL.md
skills/research/SKILL.md
```

- [ ] **Step 2: Verify no old lib references remain in skills**

Search all skill files for references to the old library names:

```bash
grep -r "vault-scanner\|link-parser\|frontmatter\.md\|content-analyzer\|moc-matcher" skills/
```

Expected: no matches. If any found, update those references to `lib/obsidian-operations.md` or `lib/analysis.md`.

- [ ] **Step 3: Verify no raw shell commands remain in skills**

Search for old shell patterns that should have been replaced:

```bash
grep -r 'find "\|grep -\|sed -\|cat "\|head -\|tail -\|mv "\|mkdir -p' skills/
```

Expected: no matches. Any remaining should be replaced with CLI equivalents.

- [ ] **Step 4: Verify all skills have correct allowed-tools**

Check each skill's frontmatter:

```bash
grep -A1 "allowed-tools" skills/*/SKILL.md
```

Expected:

- Most skills: `[Bash, Edit, AskUserQuestion]`
- Research: `[Bash, Edit, WebFetch, mcp__plugin_context7_context7__query-docs, AskUserQuestion]`

- [ ] **Step 5: Verify all skills reference obsidian-markdown**

```bash
grep "obsidian-markdown" skills/*/SKILL.md
```

Expected: 7 matches (one per skill).

- [ ] **Step 6: Verify all skills reference new libs**

```bash
grep "obsidian-operations\|lib/analysis" skills/*/SKILL.md
```

Expected: 14 matches (2 per skill — one for each lib).

- [ ] **Step 7: Verify all skills have pre-flight check**

```bash
grep "obsidian vault" skills/*/SKILL.md
```

Expected: 7 matches (one per skill).

- [ ] **Step 8: Final commit if any fixes were needed**

```bash
git add -A
git commit -m "Fix any remaining references from final review"
```

Only run this if Step 2-7 found issues that were fixed.
