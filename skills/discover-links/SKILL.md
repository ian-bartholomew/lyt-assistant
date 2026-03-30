---
name: discover-links
description: This skill should be used when the user asks to "discover links", "find missing connections", "find missing links", "connect notes", "link discovery", or wants to identify relationships between existing notes that aren't currently linked.
version: 0.1.0
allowed-tools: [Read, Edit, Grep, Glob, AskUserQuestion]
---

# Discover Links Skill

Find missing connections between existing notes by analyzing shared topics and suggesting link opportunities grouped by theme.

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

1. **Scan vault** - Build topic index for all notes
2. **Find opportunities** - Identify shared topics without links
3. **Group by theme** - Organize suggestions by topic area
4. **Present interactively** - Allow review and selection
5. **Add links** - Execute approved connections

## Process Flow

### Step 1: Scan Vault and Build Topic Index

Use **lib/vault-scanner.md** to get all files:

```bash
# Get all markdown files
ALL_FILES=$(find . -name "*.md" -not -path "*/000 - Inbox/*" -not -path "*/400 - Archive/*")
```

For each file, extract topics using **lib/content-analyzer.md**:

```bash
for file in $ALL_FILES; do
  # Extract topics (keywords, technical terms)
  TOPICS=$(analyze_topics "$file")

  # Store: file → [topics]
  echo "$file|$TOPICS" >> topic_index
done
```

Build topic-to-files mapping:

```bash
# For each topic, list files that mention it
for topic in $(all_topics); do
  FILES=$(grep "$topic" topic_index | cut -d'|' -f1)
  echo "$topic → $FILES"
done
```

### Step 2: Find Connection Opportunities

For each topic, find files that:
1. **Share the topic** (both mention it)
2. **Don't link to each other** (missing connection)
3. **Aren't the same file**

```bash
for topic in $(all_topics); do
  # Get files mentioning this topic
  FILES=$(files_for_topic "$topic")

  # For each pair of files
  for file_a in $FILES; do
    for file_b in $FILES; do
      if [ "$file_a" != "$file_b" ]; then
        # Check if they link to each other
        if ! grep -q "\[\[$(basename "$file_b" .md)\]\]" "$file_a"; then
          # Missing link opportunity
          echo "$file_a → $file_b (topic: $topic)"
        fi
      fi
    done
  done
done
```

### Step 3: Group Suggestions by Theme

Cluster related suggestions:

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

For each approved connection, use **lib/link-parser.md**:

```bash
# Add link to appropriate section
if grep -q "^## Related" "$FILE"; then
  # Add to existing Related section
  sed -i '' '/^## Related/a\
- [[Target Note]]\
' "$FILE"
else
  # Create Related section
  echo -e "\n## Related\n\n- [[Target Note]]" >> "$FILE"
fi
```

**Verify no duplicates:**

```bash
# Check link doesn't already exist
if grep -q "\[\[Target Note\]\]" "$FILE"; then
  echo "Link already exists, skipping"
fi
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

```bash
ERROR_BUDGET_TERMS="error budget|slo|sli|availability|uptime"
INCIDENT_TERMS="incident|postmortem|on-call|pager|runbook"
RELIABILITY_TERMS="circuit.breaker|bulkhead|retry|timeout|fallback"
OBSERVABILITY_TERMS="metric|log|trace|monitor|alert"
PERFORMANCE_TERMS="latency|throughput|capacity|scalability"
```

Match files to themes:

```bash
for file in $FILES; do
  if grep -qi "$ERROR_BUDGET_TERMS" "$file"; then
    THEME="Error Budgets"
  elif grep -qi "$INCIDENT_TERMS" "$file"; then
    THEME="Incident Management"
  fi
  # ... etc
done
```

### Co-occurrence Analysis

Find terms that frequently appear together:

```bash
# Count how often two terms appear in same file
count_cooccurrence() {
  TERM1=$1
  TERM2=$2

  for file in $ALL_FILES; do
    if grep -qi "$TERM1" "$file" && grep -qi "$TERM2" "$file"; then
      COUNT=$((COUNT + 1))
    fi
  done

  echo "$COUNT"
}
```

High co-occurrence suggests thematic connection.

## Link Quality Scoring

### Calculate Confidence

For each suggestion:

```bash
# Keyword frequency
FREQ=$(grep -ic "$TOPIC" "$FILE")

# Context relevance (appears in headings?)
HEADING=$(grep -i "^## .*$TOPIC" "$FILE")

# File proximity (same folder?)
if [ "$(dirname "$FILE_A")" = "$(dirname "$FILE_B")" ]; then
  PROXIMITY=1
fi

# Confidence = frequency + heading_match + proximity
CONFIDENCE=$((FREQ + HEADING * 2 + PROXIMITY))
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
LINK_COUNT=$(grep -o '\[\[[^]]*\]\]' "$FILE" | wc -l)
if [ $LINK_COUNT -gt 15 ]; then
  echo "File already well-connected, skipping"
fi
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

Detect files with zero incoming or outgoing links:

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

## Integration with Utilities

This skill uses shared utilities:

- **lib/vault-scanner.md** - Scan all files and build index
- **lib/content-analyzer.md** - Extract topics from files
- **lib/link-parser.md** - Add links to files
- **lib/moc-matcher.md** - Identify thematic groupings

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

The discover-links skill finds missing connections by analyzing shared topics, grouping suggestions thematically, and allowing interactive review before adding links. Improves vault connectivity systematically.
