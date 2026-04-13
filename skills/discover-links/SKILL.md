---
name: discover-links
description: This skill should be used when the user asks to "discover links", "find missing connections", "find missing links", "connect notes", "link discovery", or wants to identify relationships between existing notes that aren't currently linked.
version: 1.0.0
allowed-tools: [Bash, Edit, AskUserQuestion]
---

# Discover Links Skill

Find missing connections between existing notes by analyzing shared topics and suggesting link opportunities grouped by theme.

For advanced Obsidian markdown syntax (callouts, embeds, block references), follow the `obsidian:obsidian-markdown` skill.

## Purpose

Improve vault connectivity by discovering notes that mention similar topics but aren't linked to each other. Groups suggestions by theme for easy review and presents batch or individual link-adding options.

## When to Use

Invoke this skill when:

- User explicitly runs `/discover-links`
- User mentions finding, discovering, or creating connections
- User wants to improve vault linking
- User asks about orphaned or under-connected notes
- After processing inbox files (to connect new content)

## Workflow Overview

1. **Pre-flight check** - Verify Obsidian vault access
2. **Scan vault** - Build topic index for all notes
3. **Find opportunities** - Identify shared topics without links
4. **Group by theme** - Organize suggestions by topic area
5. **Present interactively** - Allow review and selection
6. **Add links** - Execute approved connections

## Process Flow

### Step 0: Pre-flight Check

Verify Obsidian CLI access:

```bash
obsidian vault
```

This confirms:

- Vault path is accessible
- CLI is properly configured
- Vault root is correct

If this fails, abort and report configuration issue.

### Step 1: Scan Vault and Build Topic Index

Get all files excluding inbox and archive using **lib/obsidian-operations.md**:

```bash
# Get all markdown files
obsidian files format=json > all_files.json
```

Filter out inbox (000) and archive (400) folders manually from the JSON.

For each file, extract topics using **lib/analysis.md**:

```bash
# Read file content
obsidian read file="Note Name"

# Extract topics using lib/analysis.md:
# - Keywords (technical terms)
# - Concepts (important nouns)
# - Technologies (tools, languages)
# Store: file → [topics]
```

Build topic-to-files mapping:

```bash
# For each topic, list files that mention it using search
obsidian search query="topic" format=json total

# This gives count of matches per topic
# Parse JSON to build topic → [files] mapping
```

### Step 2: Find Connection Opportunities

For each topic, find files that:

1. **Share the topic** (both mention it)
2. **Don't link to each other** (missing connection)
3. **Aren't the same file**

```bash
# For each topic:
# 1. Find files mentioning this topic
obsidian search query="topic" format=json

# 2. For each pair of files in results:
#    Check if file_a links to file_b
obsidian links file="File A" format=json

# 3. Parse JSON to check if "File B" is in the links array
# 4. If not found, record as missing connection opportunity
```

Example logic:

```
Topic: "error budget"
Files: [A.md, B.md, C.md]

Check A → B: obsidian links file="A" | check if B exists
Check A → C: obsidian links file="A" | check if C exists
Check B → A: obsidian links file="B" | check if A exists
Check B → C: obsidian links file="B" | check if C exists
Check C → A: obsidian links file="C" | check if A exists
Check C → B: obsidian links file="C" | check if B exists

Missing links = opportunities
```

### Step 3: Group Suggestions by Theme

Cluster related suggestions using **lib/analysis.md**:

**Group criteria:**

- Shared topics (same keyword domain)
- Similar file locations
- Common MOC associations

Example grouping:

```
Group 1: Error Budget Theme
- 8 connections around "error budgets", "SLOs"

Group 2: Incident Management Theme
- 5 connections around "incidents", "postmortems"

Group 3: Reliability Patterns Theme
- 12 connections around "circuit breaker", "bulkhead", "retry"
```

### Step 4: Rank Groups by Confidence

Score each suggestion:

- **High confidence:** Topic appears frequently in both files
- **Medium confidence:** Topic appears in one file, related topic in other
- **Low confidence:** Weak topic overlap

Sort groups by:

1. Total connections in group
2. Average confidence
3. Thematic coherence

### Step 5: Present Grouped Suggestions

Show top groups first:

```
Scanning vault for connection opportunities...

Found 23 potential link groups:

📚 Group 1: Error Budget Theme (8 connections, high confidence)

Notes mentioning error budgets without linking:
1. "300 - Reference/SRE-Concepts/RTO and RPO.md"
   → [[SLOs MOC]]
   (mentions "error budget" 3 times)

2. "300 - Reference/Reading/Book-Summaries/SRE Workbook.md"
   → [[SLOs MOC]]
   (mentions "error budget", "SLO")

3. "100 - MOCs/SRE Concepts MOC.md"
   → [[Error Budget Calculations]]
   (section on SLOs missing this link)

[... 5 more ...]

Actions for Group 1:
A) Apply all 8 connections
B) Review individually
C) Skip group
```

### Step 6: Handle User Selection

#### Option A: Apply All

Add all suggested links in group:

```
Applying 8 connections...

✅ Added [[SLOs MOC]] to "RTO and RPO.md"
✅ Added [[SLOs MOC]] to "SRE Workbook.md"
✅ Added [[Error Budget Calculations]] to "SRE Concepts MOC.md"
[...]

✅ Group 1 complete (8 links added)
```

#### Option B: Review Individually

Present each suggestion one by one:

```
Connection 1 of 8:
From: "300 - Reference/SRE-Concepts/RTO and RPO.md"
To: [[SLOs MOC]]
Reason: Both discuss error budgets

Context:
"RTO and RPO.md" mentions:
"Error budgets help balance reliability and feature velocity..."

Add this link?
A) Yes
B) No
C) Skip remaining
```

#### Option C: Skip Group

Move to next group.

### Step 7: Add Links

For each approved connection, use **Edit** tool:

```bash
# First, read the file to see current structure
obsidian read file="Target Note"

# Check if "Related" section exists
obsidian outline file="Target Note" format=md

# If Related section exists, use Edit tool to add link:
#   - Find "## Related" section
#   - Add "- [[Link Target]]" under it
#
# If no Related section, use obsidian append:
obsidian append file="Target Note" content="\n## Related\n\n- [[Link Target]]"
```

**Verify no duplicates:**

```bash
# Check link doesn't already exist
obsidian links file="Target Note" format=json

# Parse JSON array to check if "Link Target" is already present
# If found, skip adding
```

### Step 8: Report Summary

After processing all groups:

```
📊 Link Discovery Complete

Groups reviewed: 5
Links added: 23
Files updated: 15

By theme:
- Error Budgets: 8 links
- Incident Management: 5 links
- Reliability Patterns: 7 links
- Observability: 3 links

Next steps:
- Run /check-moc-health to verify MOC coverage
- Review added links in Obsidian graph view
```

## Grouping Logic

### Identify Themes

Common SRE themes to detect:

```
ERROR_BUDGET_TERMS: "error budget" OR "slo" OR "sli" OR "availability" OR "uptime"
INCIDENT_TERMS: "incident" OR "postmortem" OR "on-call" OR "pager" OR "runbook"
RELIABILITY_TERMS: "circuit breaker" OR "bulkhead" OR "retry" OR "timeout" OR "fallback"
OBSERVABILITY_TERMS: "metric" OR "log" OR "trace" OR "monitor" OR "alert"
PERFORMANCE_TERMS: "latency" OR "throughput" OR "capacity" OR "scalability"
```

Match files to themes using **obsidian search**:

```bash
# Check if file matches theme
obsidian search query="error budget OR slo OR sli" format=json

# Parse results to categorize files by theme
```

### Co-occurrence Analysis

Find terms that frequently appear together:

```bash
# Count how often two terms appear in same file
# Use obsidian search with AND operator
obsidian search query="term1 AND term2" total

# This returns count of files with both terms
# High co-occurrence suggests thematic connection
```

Example:

```bash
# How many files mention both "error budget" AND "SLO"?
obsidian search query="error budget AND SLO" total
# Output: 12

# This indicates strong thematic relationship
```

## Link Quality Scoring

### Calculate Confidence

For each suggestion:

```bash
# Keyword frequency - count matches in specific file
obsidian search query="topic" format=json
# Parse to count occurrences in specific file

# Context relevance - check if appears in headings
obsidian outline file="Note" format=md
# Parse markdown to see if topic appears in section headings

# File proximity - check folder location
obsidian info file="Note" format=json
# Parse path to determine if files are in same folder

# Confidence = frequency + (heading_match * 2) + proximity
```

**Thresholds:**

- High: Confidence >= 5
- Medium: Confidence 2-4
- Low: Confidence 1

### Filter Low-Quality Suggestions

Skip if:

- Topic mentioned only once in passing
- Files are completely different domains
- Already extensively linked (>10 links)

```bash
# Check if file is over-linked
obsidian links file="Note" format=json total

# If total > 15, file is well-connected
# Only suggest high-confidence links
```

## Bidirectional Linking

When adding link from A → B, consider adding B → A:

```
Found: "Circuit Breaker.md" mentions "Bulkhead Pattern" but doesn't link

Add bidirectional links?
A → B: [[Circuit Breaker]] → [[Bulkhead Pattern]]
B → A: [[Bulkhead Pattern]] → [[Circuit Breaker]]

Both are reliability patterns, bidirectional makes sense.

Add both? [Y/n]
```

Check both directions:

```bash
# Check A → B
obsidian links file="Circuit Breaker" format=json
# Look for "Bulkhead Pattern" in links array

# Check B → A
obsidian links file="Bulkhead Pattern" format=json
# Look for "Circuit Breaker" in links array

# If neither exists, suggest bidirectional link
```

## Special Cases

### No Missing Links Found

```
✅ No missing connections found!

Your vault is well-linked. Great work!

Stats:
- Total files: 156
- Average links per file: 5.3
- Well-connected: 92%
```

Calculate stats:

```bash
# Total files
obsidian files total

# For average links per file:
# For each file:
#   obsidian links file="X" total
# Sum and divide by file count
```

### Too Many Suggestions

If >50 suggestions:

```
Found 73 potential link groups

That's a lot! Options:
A) Show high-confidence only (23 groups)
B) Show by theme (process one theme at a time)
C) Show all (will take a while)
```

### Orphaned Files (No Links)

Detect files with zero incoming or outgoing links using **lib/obsidian-operations.md**:

```bash
# Find orphaned files (no incoming or outgoing links)
obsidian orphans format=json

# Find dead-end files (no outgoing links)
obsidian deadends format=json
```

Present orphans:

```
⚠️  Found 3 orphaned files:

- "300 - Reference/Tools/obscure-tool.md"
  No links to or from this file

- "200 - Notes/old-thought.md"
  No connections found

Options:
A) Suggest connections for orphans
B) Consider archiving (move to 400 - Archive/)
C) Skip for now
```

### Files with Extensive Links

If file already has many links:

```bash
obsidian links file="SRE Concepts MOC" total
# Returns: 24
```

```
ℹ️  "SRE Concepts MOC.md" already has 24 links

Adding more may reduce navigability.
Only show high-confidence suggestions? [Y/n]
```

## Error Handling

### Read Permission Errors

```
❌ Cannot read "file.md" (permission denied)

Skipping this file. Continue? [Y/n]
```

### Invalid Link Targets

```
⚠️  Link target doesn't exist: [[Non-existent Note]]

This file might be referencing a note that should be created.

Options:
A) Create stub file
B) Skip this link
C) Report for later
```

Use:

```bash
# Check if target note exists
obsidian info file="Non-existent Note" format=json
# Will error if file doesn't exist

# If creating stub:
obsidian create file="Non-existent Note" content="# Non-existent Note\n\nStub note to be expanded.\n"
```

### Corrupted Files

```
❌ Cannot parse "file.md" (invalid markdown)

Skipping this file from link discovery.
```

## Best Practices

1. **Start with high-confidence groups** - Quick wins
2. **Review before applying** - Especially for batch operations
3. **Consider bidirectional links** - When contextually appropriate
4. **Don't over-link** - Quality over quantity
5. **Group thematically** - Easier to review
6. **Check file context** - Link should make sense
7. **Preserve file structure** - Add to appropriate sections
8. **Report clearly** - Show what was added
9. **Allow undo** - Keep backups
10. **Run periodically** - After adding new content

## Integration with Libraries

This skill uses shared libraries:

- **lib/obsidian-operations.md** - All CLI-based vault operations
- **lib/analysis.md** - Content classification, topic extraction, MOC matching

## Usage Examples

### Example 1: High-Confidence Group

```
User: /discover-links

Scanning vault...

Found 3 link groups:

📚 Group 1: SLO Theme (5 connections, high confidence)

1. "Error Budget.md" → [[SLOs MOC]]
2. "Uptime Calculations.md" → [[SLOs MOC]]
3. "SRE Workbook Summary.md" → [[Error Budget]]
[...]

Apply all 5? [Y/n]

✅ Added 5 links
```

### Example 2: Review Individually

```
📚 Group 2: Incident Management (3 connections, medium confidence)

Actions:
B) Review individually

Connection 1 of 3:
"Runbook Template.md" → [[Incident Roles]]

Context: Both discuss incident response structure

Add? [Y/n/s]
```

### Example 3: No Links Found

```
User: /discover-links

Scanning vault...

✅ No missing connections found!
Your vault is well-linked (avg 5.2 links/file)
```

## Related Skills

- **/classify-inbox** - Add links when processing new files
- **/check-moc-health** - Find orphans missing MOC connections
- **/create-note** - Add links when creating notes

## Summary

The discover-links skill finds missing connections by analyzing shared topics, grouping suggestions thematically, and allowing interactive review before adding links. Improves vault connectivity systematically using Obsidian CLI commands for all vault operations.
