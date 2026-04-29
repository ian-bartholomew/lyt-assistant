---
name: ingest
description: This skill should be used when the user asks to "ingest", "process inbox", "process raw", "compile source", "process raw", "compile source", "organize raw files", or wants to process unprocessed sources in the "raw/" folder into wiki articles. Scans raw/ for sources not yet referenced by any wiki article, compiles them into wiki articles, updates domain indexes, and logs activity.
version: 0.3.0
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob, AskUserQuestion]
---

# Ingest Skill

Scan `raw/` for unprocessed sources and compile them into wiki articles with proper frontmatter, domain indexing, and activity logging.

## Purpose

Reduce friction in processing raw sources by scanning for unprocessed files, analyzing content, determining the appropriate wiki subfolder, compiling structured wiki articles with full frontmatter, updating domain indexes, and logging all activity. Present suggestions interactively for user review before execution.

## When to Use

Invoke this skill when:

- User explicitly runs `/ingest`
- User mentions ingesting, processing, or compiling raw sources
- User asks to process raw files into the wiki
- User mentions "ingest", "process raw", or "compile source"

## Vault Structure

This skill operates on a Karpathy-style LLM wiki vault:

| Folder | Owner | Purpose |
|--------|-------|---------|
| `raw/` | User | Immutable sources (clippings, docs) |
| `raw/daily/` | Hooks | Session logs captured by Claude Code hooks |
| `raw/clippings/` | User | Web clips via Obsidian Web Clipper |
| `raw/support_learnings/` | User | Support channel thread summaries |
| `raw/docs/` | User | Documents, proposals, write-ups |
| `raw/daily_notes/` | User | Brief work notes |
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
2. **Build article manifest** - Scan wiki frontmatter for dedup and context
3. **Identify unprocessed** - Cross-reference against manifest's `compiled_from` fields
4. **Detect batches** - Group related sources (e.g., multi-part article series)
5. **Process each source** - Analyze, classify, dedup check, present interactively
6. **Compile wiki article** - Write with proper frontmatter and reciprocal links
7. **Validate article** - Check wikilinks, word count, frontmatter before continuing
8. **Update indexes and log** - Maintain `wiki/_indexes/` and `wiki/_log.md`
9. **Report completion** - Summary of compiled articles

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

### Step 2: Build Article Manifest

Before scanning for unprocessed sources, build a lightweight manifest of all existing wiki articles. This avoids loading all article content into context.

```
For each .md file in wiki/concepts/, wiki/guides/, wiki/company/, wiki/learning/:
  Parse YAML frontmatter only (read from first --- to second ---)
  Extract: title, domain, maturity, compiled_from, related
  Record the file path
```

Build a compact one-line-per-article index:

```
concepts/karpenter.md | Karpenter | domain: [infrastructure, kubernetes] | compiled_from: [meetings/2026-04-14-karpenter/summary-default.md, ...] | related: [[eks-runbook]], [[karpenter-migration]]
concepts/circuit-breaker-pattern.md | Circuit Breaker Pattern | domain: [sre, resilience] | compiled_from: [raw/daily/2026-04-21.md] | related: [[bulkhead-pattern]], [[retry-with-backoff]]
...
```

Use this manifest throughout the workflow to:

- Identify which sources are already compiled (check `compiled_from` fields)
- Find related articles for the `related:` frontmatter field
- Detect duplicate topics before creating new articles
- Determine if a source should update an existing article vs create new

**When you need full article content** (e.g., to update an existing article), use the Read tool to read that specific file on demand.

### Step 3: Identify Unprocessed Sources

Using the manifest's `compiled_from` fields, find raw sources not yet referenced:

```
For each .md file in raw/ (recursively, all subdirectories):
  Check if any article's compiled_from list contains this file path
  If not referenced by any article: mark as unprocessed
```

If no unprocessed files:

```
No unprocessed sources found in raw/. Everything is compiled.
```

### Step 3.5: Detect Batches

Before presenting the unprocessed list, check for natural groupings:

```
For sources in raw/clippings/:
  Read frontmatter tags from each file
  Group files sharing 2+ non-generic tags (exclude "clippings" as a clustering signal)
  Flag multi-part series (files with "Part 1", "Part 2", etc. in the title)
```

Present count with batch suggestions:

```
Found 12 unprocessed sources in raw/:

  Batch 1 (9 files, shared tags: terraform, iac):
    1. Part 1 Overview of our recommended workflow  Terraform.md
    2. Part 2 Evaluate your current provisioning practices.md
    3. Part 3.1 Move from manual changes to semi-automation.md
    ...

  Individual sources (3 files):
    10. raw/daily/2026-04-24.md
    11. raw/support_learnings/2026-04-23.md
    12. raw/docs/datadog-idp-implementation-plan.md

Process options:
A) All (batches compiled together, individuals separately)
B) Select specific files/batches
C) Batches only
D) Individuals only
```

When processing a batch: concatenate all source contents and compile together into unified articles. This produces fewer, richer articles instead of many thin overlapping ones. Each source file is still tracked individually in the article's `compiled_from` frontmatter.

### Step 4: Process Each Source (or Batch)

For each unprocessed source:

#### 4a. Read and Analyze Content

Read the source file and determine:

- What wiki subfolder it belongs to (concepts, guides, company, learning)
- What domain tags apply
- What title the wiki article should have (kebab-case filename)
- What maturity and confidence levels to assign
- What related wiki articles exist (use the manifest)

**Source-type-specific compilation guidance:**

| Source Path | Content Type | Compilation Focus |
|-------------|-------------|-------------------|
| `raw/daily/` | Session logs | Extract decisions, lessons, patterns. Skip ephemeral task details (what commands were run, what files were read). Focus on knowledge that transfers to future work. |
| `raw/clippings/` | Web articles | Extract core concepts, frameworks, and best practices. Attribute ideas to the original author. Preserve the source URL from frontmatter in the article's sources section. |
| `raw/support_learnings/` | Support threads | Group threads by pattern, not per-thread. Focus on the "Learning" sections. Create `company/` articles for org-specific patterns and `concepts/` or `guides/` for general technical knowledge. |
| `raw/docs/` | Documents/proposals | Capture the problem statement, proposed solution, trade-offs, and decisions made. Don't just describe — extract the reasoning. |
| `raw/daily_notes/` | Brief work notes | These are typically thin. Prefer updating existing articles over creating new ones. Only create a new article if the note introduces a genuinely new concept. |
| `meetings/` | Meeting summaries | Extract actionable decisions and technical knowledge. Skip social/scheduling chatter. Group by topic, not by meeting. |

**Classification rules:**

| Subfolder | Content Type |
|-----------|-------------|
| `wiki/concepts/` | Atomic ideas, patterns, principles, definitions — "What is X?" |
| `wiki/guides/` | How-to content, runbooks, operational procedures — "How do I X?" |
| `wiki/company/` | Company-specific architecture, processes, tools, team knowledge |
| `wiki/learning/` | Study notes, course material, book highlights, learning paths |

**Output format:**

```
Processing: "raw/clippings/circuit-breaker-fowler.md" (1 of 3)

Content Analysis:
- Source type: clipping (web article)
- Suggested subfolder: wiki/concepts/
- Title: Circuit Breaker Pattern
- Filename: circuit-breaker-pattern.md
- Domain: [sre, resilience]
- Maturity: draft
- Confidence: medium
- Reasoning: Describes a pattern/principle — fits concepts/
```

#### 4b. Pre-Compilation Dedup Check

**This step is critical for quality.** Before creating any article, check if a wiki article on this topic already exists:

```bash
# Search by similar filename
find wiki/ -name "*circuit-breaker*" -type f

# Search by content keywords
grep -rl "circuit breaker" wiki/ --include="*.md"

# Check manifest for overlapping compiled_from sources
# (already done in Step 3, but verify for the specific topic)
```

Also check the manifest for articles with overlapping `related:` links or matching `domain:` tags that might cover the same ground.

If potential overlap found:

```
Existing article found: wiki/concepts/circuit-breaker-pattern.md
  - Compiled from: raw/daily/2026-04-21.md
  - Maturity: developing
  - Word count: 450

Options:
A) Update existing article with new source (recommended — avoids duplication)
B) Create separate article (use if topics are distinct despite similar names)
C) Skip this source
```

If updating, add the new raw file to the existing article's `compiled_from:` field, merge in new content, and update `last_compiled`.

#### 4c. Suggest Related Articles

Using the manifest, find related content:

- Articles sharing the same `domain:` tags
- Articles whose `related:` field references similar topics
- Keyword search across article titles in the manifest

```
Suggested Related Articles:
  - [[bulkhead-pattern]] (shared domain: sre, resilience)
  - [[retry-with-backoff]] (shared domain: sre)
  - [[graceful-degradation]] (referenced in related: by bulkhead-pattern)
```

### Step 5: Present Options Interactively

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

### Step 6: Compile Wiki Article

For each approved source, create the wiki article:

#### 6a. Generate Article Content

Synthesize the raw source into a structured wiki article:

```markdown
---
title: Circuit Breaker Pattern
domain: [sre, resilience]
maturity: draft
confidence: medium
compiled_from:
  - "raw/clippings/circuit-breaker-fowler.md"
related:
  - "[[bulkhead-pattern]]"
  - "[[retry-with-backoff]]"
last_compiled: 2026-04-17
---

# Circuit Breaker Pattern

## Overview

[Synthesized content from source]

## Key Concepts

[Main ideas — 3-5 bullet points]

## Details

[2+ paragraphs of substantive content]

## Examples

[Practical examples where applicable]

## Sources

- From [[raw/clippings/circuit-breaker-fowler.md]]: [specific claims extracted]
```

**Filename convention:** kebab-case, e.g., `circuit-breaker-pattern.md`

**Quality minimums for new articles:**

- Body must be >= 200 words (excluding frontmatter)
- Must have at least 2 entries in `related:`
- Must have a Key Concepts/Key Points section with 3-5 bullets
- Must have a Details section with 2+ paragraphs

#### 6b. Write the Article

Use **Write** tool to create the file at the determined path (e.g., `wiki/concepts/circuit-breaker-pattern.md`).

#### 6c. Add Reciprocal Links

**This step prevents orphan pages and asymmetric linking.**

For each article listed in the new article's `related:` frontmatter:

1. Read the target article's frontmatter
2. Check if the new article's slug is already in the target's `related:` list
3. If not, add it using Edit tool:

```yaml
# Before (in bulkhead-pattern.md)
related:
  - "[[load-shedding]]"

# After
related:
  - "[[load-shedding]]"
  - "[[circuit-breaker-pattern]]"
```

Report each reciprocal link added:

```
Reciprocal links:
  + [[circuit-breaker-pattern]] added to bulkhead-pattern.md
  + [[circuit-breaker-pattern]] added to retry-with-backoff.md
  (retry-with-backoff.md already had [[circuit-breaker-pattern]] — skipped)
```

#### 6d. Update Domain Index

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

#### 6e. Update Master Index

Add the new article to the "Recently Compiled" section in `wiki/_index.md`:

```markdown
- [[circuit-breaker-pattern]] — one-line summary (compiled 2026-04-17)
```

Update the article count in the header if present.

#### 6f. Append to Activity Log

Add entry to `wiki/_log.md`:

```markdown
## [2026-04-17] ingest | Circuit Breaker Pattern

- Source: `raw/clippings/circuit-breaker-fowler.md`
- Destination: `wiki/concepts/circuit-breaker-pattern.md`
- Domain: sre, resilience
- Maturity: draft
- Reciprocal links added: 2 (bulkhead-pattern, retry-with-backoff)
```

### Step 7: Post-Compilation Validation

**Run these checks on each newly written article before moving to the next source.**

#### 7a. Wikilink Validation

Extract all `[[wikilinks]]` from the article body and frontmatter. For each link:

```bash
# Search for the target file
find wiki/ -name "<link-target>.md" -type f
```

If a link target doesn't exist:

```
Broken wikilink found: [[rate-limiting]] (no matching file)

Options:
A) Create stub article for [[rate-limiting]]
B) Remove the link from the article
C) Keep the link (will create the article later)
```

If creating a stub:

```yaml
---
title: Rate Limiting
domain: [sre]
maturity: stub
confidence: low
related:
  - "[[circuit-breaker-pattern]]"
last_compiled: 2026-04-17
---

# Rate Limiting

*This article is a stub. It was auto-generated because other articles reference this topic.*

## Referenced By

- [[circuit-breaker-pattern]]
```

#### 7b. Word Count Check

Count words in the article body (excluding frontmatter):

```
If word count < 200:
  Warning: Article body is only 142 words.

  Options:
  A) Expand — re-read the source and add more detail
  B) Merge — fold this content into an existing article instead
  C) Accept as-is (maturity will be set to "stub")
```

If the user accepts a thin article, automatically set `maturity: stub`.

#### 7c. Frontmatter Validation

Check all required fields are present and valid:

- `title` — non-empty string
- `domain` — list with at least one valid domain
- `maturity` — one of: stub, draft, developing, mature
- `confidence` — one of: low, medium, high
- `compiled_from` — list with at least one source path
- `related` — list with at least 2 entries
- `last_compiled` — valid YYYY-MM-DD date

If any field is missing or invalid, fix it automatically and report:

```
Frontmatter fix: added missing "confidence: medium" to circuit-breaker-pattern.md
```

### Step 8: Verify and Report

After each source:

```
Compiled: wiki/concepts/circuit-breaker-pattern.md
  Word count: 387
  Related links: 3 (2 reciprocal links added)
  Wikilinks: 5 (all valid)
  Frontmatter: valid
Updated index: wiki/_indexes/sre.md
Logged to: wiki/_log.md
```

After all sources:

```
Ingest Complete

Processed: 12 sources (1 batch of 9 + 3 individual)
Compiled: 8 articles (4 new, 4 updated)
Skipped: 1 source
Stubs created: 2 (for broken wikilinks)

Quality Summary:
  Articles above 200 words: 8/8
  Reciprocal links added: 14
  Broken links found and resolved: 2
  Frontmatter issues fixed: 1

  - New concepts: 3
  - New guides: 1
  - Updated: circuit-breaker-pattern, karpenter, terraform-state-locking, deploy-pipeline
  - Stubs: rate-limiting, error-budget-policy

Indexes updated: 4
Log entries added: 8

Suggested next steps:
  - Run /lint to check full wiki health
  - Run /discover-links to find new connections
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

1. **Build the manifest once** at start, reuse for all processing
2. **Process sources sequentially** for user control
3. **Always run dedup check** before creating new articles
4. **Always add reciprocal links** when creating related: entries
5. **Always validate after writing** — check links, word count, frontmatter
6. **Preserve raw sources** — never modify files in `raw/`
7. **Use kebab-case filenames** for all wiki articles
8. **Always update indexes** after compiling an article
9. **Always log activity** in `wiki/_log.md`
10. **Set maturity to draft** for newly compiled articles (stub only if <200 words)
11. **Batch related sources** when they share tags or form a series
12. **Allow editing** before execution
13. **Report reciprocal links** so user sees the graph growing

## Usage Examples

### Example 1: Single Source Ingest

```
User: /ingest

Building article manifest... (193 articles scanned)

Found 1 unprocessed source in raw/:
1. raw/clippings/terraform-state-locking.md

Processing: "raw/clippings/terraform-state-locking.md" (1 of 1)

Content Analysis:
- Source type: clipping (web article)
- Suggested subfolder: wiki/guides/
- Title: Terraform State Locking
- Filename: terraform-state-locking.md
- Domain: [infrastructure, terraform]
- Reasoning: Contains operational steps and configuration — fits guides/

Dedup check:
- No existing article on "terraform state locking" found
- Related articles: [[terraform-state-management]], [[terraform-operations-best-practices]]

[User accepts]

Compiled: wiki/guides/terraform-state-locking.md (412 words)
Reciprocal links:
  + [[terraform-state-locking]] added to terraform-state-management.md
  + [[terraform-state-locking]] added to terraform-operations-best-practices.md
Validation: all wikilinks valid, frontmatter complete
Updated index: wiki/_indexes/infrastructure.md
Logged to: wiki/_log.md

Ingest Complete — 1 article compiled, 2 reciprocal links added
```

### Example 2: Batch Processing

```
User: process raw

Building article manifest... (193 articles scanned)

Found 12 unprocessed sources in raw/:

  Batch 1 (9 files, shared tags: terraform, iac, bestpractices):
    1-9. Terraform recommended practices series (Parts 1-4 + supporting docs)

  Individual:
    10. raw/daily/2026-04-24.md
    11. raw/support_learnings/2026-04-23.md
    12. raw/docs/datadog-idp-implementation-plan.md

Process all? [A/select/cancel]

[User selects A]

Processing batch 1 (9 Terraform sources)...

  Dedup check: found existing [[terraform-recommended-practices]]
  → Updating existing article + creating 2 new guides

  Compiled:
    Updated: wiki/concepts/terraform-recommended-practices.md (now 1,200 words, 9 sources)
    Created: wiki/guides/terraform-migration-workflow.md (480 words)
    Created: wiki/guides/terraform-folder-conventions.md (390 words)
  Reciprocal links added: 8
  Validation: all clean

Processing source 10 (daily log)...
[... continues ...]

Ingest Complete
Compiled: 8 articles (3 new, 5 updated)
Skipped: 1 source
```

### Example 3: Source Updates Existing Article

```
Processing: "raw/docs/circuit-breaker-v2.md"

Dedup check:
  Existing article found: wiki/concepts/circuit-breaker-pattern.md
    - Currently compiled from: raw/daily/2026-04-21.md
    - Maturity: developing
    - Word count: 450

Options:
A) Update existing article with new source (recommended)
B) Create separate article
C) Skip

[User selects A]

Updated: wiki/concepts/circuit-breaker-pattern.md
  - Added source: raw/docs/circuit-breaker-v2.md to compiled_from
  - Merged new content (now 680 words)
  - Updated last_compiled: 2026-04-17
  - Maturity promoted: developing → mature (now has 2 sources, 680 words)
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
- **Batch related clippings** — Multi-part series produce better unified articles than many thin ones
- **Reciprocal links always** — Every related link should go both ways

## Related Skills

- **/compile** - Full compilation pipeline (ingest + validate + discover links)
- **/create-note** - Create new notes from scratch
- **/research** - Research a topic and create a wiki article
- **/create-project** - Create project hubs
- **/archive-project** - Complete and archive projects
- **/discover-links** - Find missing connections after ingesting
- **/lint** - Check wiki health after bulk ingestion

## Summary

The ingest skill processes unprocessed sources from `raw/` into structured wiki articles. It builds an article manifest for efficient dedup and context, analyzes content with source-type-specific guidance, determines the appropriate wiki subfolder, compiles articles with full frontmatter, adds reciprocal links to related articles, validates each article (wikilinks, word count, frontmatter) before moving on, updates domain indexes in `wiki/_indexes/`, and logs all activity to `wiki/_log.md`. Related sources are batched for richer output. All suggestions are presented interactively for user review.
