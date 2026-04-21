---
name: classify-inbox
description: This skill should be used when the user asks to "process inbox", "classify inbox", "ingest", "process raw", "compile source", "organize raw files", or wants to process unprocessed sources in the "raw/" folder into wiki articles. Scans raw/ for sources not yet referenced by any wiki article, compiles them into wiki articles, updates domain indexes, and logs activity.
version: 0.2.0
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob, AskUserQuestion]
---

# Ingest Skill

Scan `raw/` for unprocessed sources and compile them into wiki articles with proper frontmatter, domain indexing, and activity logging.

## Purpose

Reduce friction in processing raw sources by scanning for unprocessed files, analyzing content, determining the appropriate wiki subfolder, compiling structured wiki articles with full frontmatter, updating domain indexes, and logging all activity. Present suggestions interactively for user review before execution.

## When to Use

Invoke this skill when:

- User explicitly runs `/classify-inbox`
- User mentions ingesting, processing, or compiling raw sources
- User asks to process raw files into the wiki
- User mentions "ingest", "process raw", or "compile source"

## Vault Structure

This skill operates on a Karpathy-style LLM wiki vault:

| Folder | Owner | Purpose |
|--------|-------|---------|
| `raw/` | User | Immutable sources (clippings, docs) |
| `wiki/` | LLM | Compiled knowledge |
| `wiki/concepts/` | LLM | Atomic concept articles |
| `wiki/guides/` | LLM | How-to and operational guides |
| `wiki/company/` | LLM | Company-specific knowledge |
| `wiki/learning/` | LLM | Learning paths and study notes |
| `wiki/_indexes/` | LLM | Domain index files |
| `wiki/_index.md` | LLM | Master index |
| `wiki/_log.md` | LLM | Activity log |
| `projects/` | Both | Active project workspaces |
| `meetings/` | User | Meeting recordings/transcripts |
| `archive/` | Stale | Superseded content |

## Workflow Overview

1. **Scan raw/** - Find all source files
2. **Identify unprocessed** - Cross-reference against wiki articles' `sources:` fields
3. **Process each source** - Analyze, suggest wiki subfolder, present interactively
4. **Compile wiki article** - Write with proper frontmatter
5. **Update indexes and log** - Maintain `wiki/_indexes/` and `wiki/_log.md`
6. **Report completion** - Summary of compiled articles

## Process Flow

### Step 1: Initialize and Validate

Check vault structure exists:

```bash
if [ ! -d "raw" ]; then
  echo "raw/ directory not found"
  echo "This doesn't appear to be a wiki vault"
  exit 1
fi

if [ ! -d "wiki" ]; then
  echo "wiki/ directory not found — creating wiki structure"
  mkdir -p wiki/concepts wiki/guides wiki/company wiki/learning wiki/_indexes
fi
```

Ensure required wiki infrastructure exists:

```bash
# Create _log.md if missing
if [ ! -f "wiki/_log.md" ]; then
  echo "# Wiki Activity Log" > wiki/_log.md
fi

# Create _index.md if missing
if [ ! -f "wiki/_index.md" ]; then
  echo "# Wiki Index" > wiki/_index.md
fi

# Create _indexes/ if missing
mkdir -p wiki/_indexes
```

### Step 2: Identify Unprocessed Sources

Scan `raw/` for all markdown files, then cross-reference against `sources:` fields in existing wiki articles.

```bash
# Get all raw source files
RAW_FILES=$(find raw/ -name "*.md" -type f)

# Get all sources already referenced by wiki articles
REFERENCED=$(grep -rh "sources:" wiki/ --include="*.md" -A 20 | grep '\[\[raw/' | sed 's/.*\[\[//;s/\]\].*//')

# Filter to only unprocessed files
for file in $RAW_FILES; do
  if ! echo "$REFERENCED" | grep -q "$file"; then
    UNPROCESSED+=("$file")
  fi
done
```

If no unprocessed files:

```
No unprocessed sources found in raw/. Everything is compiled.
```

Present count:

```
Found 3 unprocessed sources in raw/:

1. raw/clippings/circuit-breaker-fowler.md
2. raw/docs/terraform-state-locking.md
3. raw/clippings/littles-law-wikipedia.md

Process all? [Y/n/select specific]
```

### Step 3: Process Each Source

For each unprocessed source:

#### 3a. Read and Analyze Content

Read the source file and determine:

- What wiki subfolder it belongs to (concepts, guides, company, learning)
- What domain tags apply
- What title the wiki article should have (kebab-case filename)
- What maturity and confidence levels to assign
- What related wiki articles exist

**Classification rules:**

| Subfolder | Content Type |
|-----------|-------------|
| `wiki/concepts/` | Atomic ideas, patterns, principles, definitions |
| `wiki/guides/` | How-to content, runbooks, operational procedures |
| `wiki/company/` | Company-specific architecture, processes, tools |
| `wiki/learning/` | Study notes, course material, learning paths |

**Output format:**

```
Processing: "raw/clippings/circuit-breaker-fowler.md" (1 of 3)

Content Analysis:
- Suggested subfolder: wiki/concepts/
- Title: Circuit Breaker Pattern
- Filename: circuit-breaker-pattern.md
- Domain: [sre, resilience]
- Maturity: draft
- Confidence: medium
- Reasoning: Describes a pattern/principle — fits concepts/
```

#### 3b. Check for Existing Wiki Article

Before creating, check if a wiki article on this topic already exists:

```bash
# Search by similar filename
find wiki/ -name "*circuit-breaker*" -type f

# Search by similar content
grep -rl "circuit breaker" wiki/ --include="*.md"
```

If found:

```
Existing article found: wiki/concepts/circuit-breaker-pattern.md

Options:
A) Update existing article with new source
B) Create separate article
C) Skip this source
```

If updating, add the new raw file to the existing article's `sources:` field and update `last_compiled`.

#### 3c. Suggest Related Articles

Search wiki for related content:

```bash
# Extract key terms from source content
# Search for wiki articles mentioning same terms
grep -rl "resilience\|fault tolerance\|cascade" wiki/ --include="*.md"
```

**Output format:**

```
Suggested Related Articles:
  - [[bulkhead-pattern]]
  - [[retry-with-backoff]]
```

### Step 4: Present Options Interactively

Use **AskUserQuestion** tool to present structured options:

```
Source: raw/clippings/circuit-breaker-fowler.md

Compiled Article:
  Destination: wiki/concepts/circuit-breaker-pattern.md
  Title: Circuit Breaker Pattern
  Domain: [sre, resilience]
  Maturity: draft
  Confidence: medium
  Related: [[bulkhead-pattern]], [[retry-with-backoff]]

Would you like to:
A) Accept and compile (recommended)
B) Edit destination subfolder
C) Edit domain tags
D) Edit related links
E) Skip this source
F) Cancel operation
```

Handle each choice:

#### Option A: Accept and Compile

Execute the compilation.

#### Option B: Edit Destination

```
Current: wiki/concepts/

Available destinations:
1. wiki/concepts/
2. wiki/guides/
3. wiki/company/
4. wiki/learning/

Choose (1-4):
```

#### Option C: Edit Domain Tags

```
Current domains: [sre, resilience]

Actions:
- Keep all
- Remove specific (enter tags)
- Add additional (enter tags)
```

#### Option D: Edit Related Links

```
Suggested related:
1. [[bulkhead-pattern]]
2. [[retry-with-backoff]]

Actions:
- Keep all
- Remove specific (enter numbers)
- Add additional (enter article names in kebab-case)
```

#### Option E: Skip

Move to next source without changes.

#### Option F: Cancel

Stop processing entirely.

### Step 5: Compile Wiki Article

For each approved source, create the wiki article:

#### 5a. Generate Article Content

Synthesize the raw source into a structured wiki article:

```markdown
---
title: Circuit Breaker Pattern
domain: [sre, resilience]
maturity: draft
confidence: medium
sources:
  - "[[raw/clippings/circuit-breaker-fowler.md]]"
related:
  - "[[bulkhead-pattern]]"
  - "[[retry-with-backoff]]"
last_compiled: 2026-04-17
---

# Circuit Breaker Pattern

## Overview

[Synthesized content from source]

## Key Concepts

[Main ideas]

## Examples

[Practical examples]

## Related

- [[bulkhead-pattern]]
- [[retry-with-backoff]]
```

**Filename convention:** kebab-case, e.g., `circuit-breaker-pattern.md`

#### 5b. Write the Article

Use **Write** tool to create the file at the determined path (e.g., `wiki/concepts/circuit-breaker-pattern.md`).

#### 5c. Update Domain Index

Find or create the relevant domain index in `wiki/_indexes/`:

```bash
# e.g., for domain "sre"
INDEX_FILE="wiki/_indexes/sre.md"
```

If the index file exists, append the new article link. If not, create it:

```markdown
---
title: SRE Domain Index
domain: sre
last_updated: 2026-04-17
---

# SRE

## Concepts

- [[circuit-breaker-pattern]] — Circuit Breaker Pattern

## Guides

[entries here]
```

Add the new article under the appropriate section (Concepts, Guides, Company, Learning) matching the subfolder.

#### 5d. Update Master Index

If the article introduces a new domain not yet in `wiki/_index.md`, add it:

```markdown
## Domains

- [[wiki/_indexes/sre|SRE]]
- [[wiki/_indexes/resilience|Resilience]]
```

#### 5e. Append to Activity Log

Add entry to `wiki/_log.md`:

```markdown
## [2026-04-17] ingest | Circuit Breaker Pattern

- Source: `[[raw/clippings/circuit-breaker-fowler.md]]`
- Destination: `wiki/concepts/circuit-breaker-pattern.md`
- Domain: sre, resilience
- Maturity: draft
```

### Step 6: Verify and Report

After each source:

```
Compiled: wiki/concepts/circuit-breaker-pattern.md
Updated index: wiki/_indexes/sre.md
Logged to: wiki/_log.md
```

After all sources:

```
Ingest Complete

Processed: 3 sources
Compiled: 2 articles
Skipped: 1 source
  - Concepts: 1
  - Guides: 1
Indexes updated: 3
Log entries added: 2

Unprocessed sources remaining: 0
```

## Error Handling

### No Unprocessed Sources

```
No unprocessed sources in raw/. Everything is already compiled.
```

### File Conflict at Destination

```
Article "circuit-breaker-pattern.md" already exists at wiki/concepts/

Options:
A) Update existing article (add new source, refresh content)
B) Create with different name
C) Skip this source
```

### Ambiguous Classification

```
Content Analysis:
- Mixed signals detected
  - Contains operational steps (guide indicator)
  - Describes a concept/pattern (concept indicator)

Help me decide:
1. Is this primarily a how-to guide or a concept explanation?
2. Does it describe what something IS or how to DO something?
```

Use **AskUserQuestion** to clarify.

### Missing Wiki Infrastructure

```
wiki/_indexes/ directory not found — creating it now.
wiki/_log.md not found — creating it now.
```

Automatically create missing infrastructure and continue.

### Empty Source File

```
Source "raw/clippings/empty-file.md" has no content.

Options:
A) Skip this source
B) Delete empty file
```

### Permission Error

```
Cannot write to "wiki/concepts/article.md"
File may be locked by Obsidian.

Close the file and retry?
```

## Best Practices

1. **Scan wiki sources once** at start, reuse for all processing
2. **Process sources sequentially** for user control
3. **Always validate paths** before writing
4. **Check for existing articles** before creating duplicates
5. **Preserve raw sources** — never modify files in `raw/`
6. **Use kebab-case filenames** for all wiki articles
7. **Always update indexes** after compiling an article
8. **Always log activity** in `wiki/_log.md`
9. **Set maturity to draft** for newly compiled articles
10. **Allow editing** before execution

## Usage Examples

### Example 1: Single Source Ingest

```
User: /classify-inbox

Found 1 unprocessed source in raw/:
1. raw/clippings/terraform-state-locking.md

Processing: "raw/clippings/terraform-state-locking.md" (1 of 1)

Content Analysis:
- Suggested subfolder: wiki/guides/
- Title: Terraform State Locking
- Filename: terraform-state-locking.md
- Domain: [terraform, infrastructure]
- Reasoning: Contains operational steps and configuration

[User accepts]

Compiled: wiki/guides/terraform-state-locking.md
Updated index: wiki/_indexes/terraform.md
Logged to: wiki/_log.md

Ingest Complete — 1 article compiled
```

### Example 2: Multiple Sources

```
User: process raw

Found 3 unprocessed sources in raw/

[Source 1 compiled to wiki/concepts/]
[Source 2 compiled to wiki/guides/]
[Source 3 skipped by user]

Ingest Complete
Compiled: 2 articles
Skipped: 1 source
```

### Example 3: Source Updates Existing Article

```
Processing: "raw/docs/circuit-breaker-v2.md"

Existing article found: wiki/concepts/circuit-breaker-pattern.md

Options:
A) Update existing article with new source

[User selects A]

Updated: wiki/concepts/circuit-breaker-pattern.md
  - Added source: [[raw/docs/circuit-breaker-v2.md]]
  - Refreshed content with new information
  - Updated last_compiled: 2026-04-17
Logged to: wiki/_log.md
```

## Tips

- **Process regularly** — Don't let raw/ accumulate too many unprocessed sources
- **Review suggestions** — Edit domain tags and subfolder before accepting
- **Check related links** — Remove irrelevant suggestions
- **Raw is immutable** — Never modify source files; only compile from them
- **Draft first, mature later** — New articles start as drafts; revisit to promote maturity
- **Domain indexes are navigation** — Keep them organized by subfolder type
- **Kebab-case everything** — Article filenames and wikilinks use kebab-case

## Related Skills

- **/create-note** - Create new notes from scratch
- **/research** - Research a topic and create a wiki article
- **/create-project** - Create project hubs
- **/archive-project** - Complete and archive projects
- **/discover-links** - Find missing connections after ingesting

## Summary

The ingest skill processes unprocessed sources from `raw/` into structured wiki articles. It analyzes content, determines the appropriate wiki subfolder, compiles articles with full frontmatter (title, domain, maturity, confidence, sources, related, last_compiled), updates domain indexes in `wiki/_indexes/`, and logs all activity to `wiki/_log.md`. All suggestions are presented interactively for user review.
