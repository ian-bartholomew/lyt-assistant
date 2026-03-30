---
name: check-moc-health
description: This skill should be used when the user asks to "check MOC health", "analyze MOC", "validate MOC", "check MOC quality", "audit MOC", "check for broken links in MOC", or wants to assess the quality and coverage of a Map of Content.
version: 0.1.0
allowed-tools: [Read, Edit, Grep, Glob, AskUserQuestion]
---

# Check MOC Health Skill

Analyze MOC (Map of Content) quality and suggest improvements by checking structure, detecting broken links, finding missing coverage, and identifying stale references.

## Purpose

Maintain MOC quality by performing comprehensive audits that check link validity, identify orphaned notes that should be included, detect stale references, and verify structural integrity. Ensures MOCs remain effective organizational tools.

## When to Use

Invoke this skill when:
- User explicitly runs `/check-moc-health`
- User mentions checking, analyzing, auditing, or validating a MOC
- User wants to find broken links in a MOC
- User asks about MOC quality or coverage
- After adding many new notes (to check if MOCs need updates)
- As part of regular vault maintenance

## Workflow Overview

1. **Select MOC** - Choose which MOC to analyze
2. **Structure audit** - Check formatting and organization
3. **Link validation** - Find broken links
4. **Coverage analysis** - Find orphaned notes
5. **Staleness detection** - Identify outdated references
6. **Present report** - Interactive findings and options
7. **Execute fixes** - Apply approved improvements

## Process Flow

### Step 1: Select MOC to Analyze

Present list of available MOCs:

```bash
# Get all MOCs using vault-scanner
MOC_FILES=$(find "100 - MOCs" -type f -name "*.md" | sort)

echo "Which MOC should I analyze?"
echo ""
i=1
for moc in $MOC_FILES; do
  echo "$i) $(basename "$moc" .md)"
  i=$((i + 1))
done
echo ""
echo "Enter number or MOC name:"
```

**Alternative:** Accept MOC name as argument:

```
/check-moc-health SRE Concepts MOC
```

### Step 2: Read and Parse MOC

Read MOC file:

```bash
MOC_PATH="100 - MOCs/${MOC_NAME}.md"
MOC_CONTENT=$(cat "$MOC_PATH")
```

Extract components:
- Frontmatter
- Headings (structure)
- Links (all [[target]] links)
- Sections (organize by heading)

### Step 3: Structure Audit

Check MOC structure and formatting:

#### 3a. Heading Hierarchy

Verify proper heading levels:

```bash
# Should have clear hierarchy: #, ##, ###
HEADINGS=$(grep '^#' "$MOC_PATH")

# Check for skipped levels (e.g., # → ###)
# Check for too many H1s (should be 1)
H1_COUNT=$(grep -c '^# ' "$MOC_PATH")
if [ $H1_COUNT -gt 1 ]; then
  echo "⚠️  Multiple H1 headings found (should be 1)"
fi
```

**Good structure:**
```markdown
# SRE Concepts MOC

## Reliability
### Patterns
### Metrics

## Observability
### Tools
### Practices
```

**Bad structure:**
```markdown
# SRE Concepts MOC
### Reliability  # Skipped H2
# Another Title  # Multiple H1s
```

#### 3b. Section Organization

Check if links are organized by section:

```bash
# MOC should group related topics
# Not just a flat list of links
```

**Good:**
```markdown
## Service Level Objectives

- [[SLOs]]
- [[SLIs]]
- [[Error Budget]]

## Incident Response

- [[Incident Roles]]
- [[Postmortem Template]]
```

**Bad (flat list):**
```markdown
# SRE Concepts MOC

- [[SLOs]]
- [[Incident Roles]]
- [[Error Budget]]
- [[Postmortem Template]]
```

#### 3c. Link Formatting

Check all links are properly formatted:

```bash
# Find malformed links
grep -n '\[.*\]([^)]*)' "$MOC_PATH"  # Markdown links (not wiki-style)
grep -n '\[\[[^]]*$' "$MOC_PATH"     # Unclosed links
```

**Report:**
```
📊 Structure Audit:
✅ Has clear heading hierarchy
✅ Links organized by section
⚠️  Line 23: Malformed link [Example](url) - should be [[Example]]
```

### Step 4: Link Validation (Broken Links)

Check each link target exists:

```bash
# Extract all links
LINKS=$(grep -o '\[\[[^]]*\]\]' "$MOC_PATH" | sed 's/\[\[\([^|]*\).*/\1/')

# For each link, verify target exists
for link in $LINKS; do
  if ! find . -name "${link}.md" 2>/dev/null | grep -q .; then
    echo "⚠️  Broken link: [[${link}]] (file doesn't exist)"
  fi
done
```

**Report:**
```
📊 Link Validation:
Total links: 34
Valid: 31
Broken: 3

⚠️  Broken links found:
  - [[Bulkhead Pattern]] (line 15)
  - [[Circuit Breaker]] (line 18)
  - [[Golden Signals]] (line 42)

These references don't exist in vault.
```

### Step 5: Coverage Analysis (Missing Notes)

Find notes that should be in MOC but aren't:

#### 5a. Identify MOC Topics

Extract topics from MOC title and sections:

```bash
MOC_NAME="SRE Concepts MOC"
TOPICS="sre reliability observability incidents"

# Extract from section headings
SECTIONS=$(grep '^##' "$MOC_PATH" | sed 's/^## //')
# "Reliability Patterns" → add "reliability", "patterns"
```

#### 5b. Find Related Orphans

Search vault for notes matching MOC topics but not linked from MOC:

```bash
# Get all MOC links
MOC_LINKS=$(grep -o '\[\[[^]]*\]\]' "$MOC_PATH" | sed 's/\[\[\([^|]*\).*/\1/')

# Find notes mentioning MOC topics
for topic in $TOPICS; do
  CANDIDATES=$(grep -rl "$topic" "200 - Notes" "300 - Reference" --include="*.md")

  # Filter: not already in MOC links
  for candidate in $CANDIDATES; do
    BASENAME=$(basename "$candidate" .md)
    if ! echo "$MOC_LINKS" | grep -q "$BASENAME"; then
      echo "Missing: $candidate (mentions $topic)"
    fi
  done
done
```

**Report:**
```
📦 Coverage Analysis:
Missing from MOC but should be included (8 notes):

High confidence:
  - "Exponential Backoff.md" (in Reference/SRE-Concepts/, mentions reliability)
  - "Load Shedding.md" (in Reference/SRE-Concepts/, mentions patterns)

Medium confidence:
  - "Graceful Degradation.md" (mentions reliability, in Notes/)
  - "Latency Budgets.md" (related to SLOs)

[... 4 more ...]
```

### Step 6: Staleness Detection

Check for links to archived or outdated content:

#### 6a. Archived References

```bash
# Check if any MOC links point to Archive
for link in $MOC_LINKS; do
  if find "400 - Archive" -name "${link}.md" | grep -q .; then
    echo "⚠️  Links to archived content: [[${link}]]"
  fi
done
```

#### 6b. Old Content

Check last modified dates:

```bash
# Find files not updated in >1 year
for link in $MOC_LINKS; do
  FILE=$(find . -name "${link}.md")
  if [ -f "$FILE" ]; then
    MTIME=$(stat -f%m "$FILE")  # macOS
    AGE=$(( ($(date +%s) - $MTIME) / 86400 ))  # days

    if [ $AGE -gt 365 ]; then
      echo "ℹ️  Old content (${AGE} days): [[${link}]]"
    fi
  fi
done
```

**Report:**
```
🕰️  Staleness Detection:
✅ No archived references
ℹ️  2 notes not updated in >6 months:
  - [[Old Pattern.md]] (412 days)
  - [[Deprecated Tool.md]] (523 days)

Consider reviewing these for relevance.
```

### Step 7: Present Comprehensive Report

Combine all findings:

```
Analyzing "SRE Concepts MOC.md"...

📊 Structure Audit:
✅ Has clear sections
✅ Uses proper heading hierarchy
⚠️  3 broken links found:
  - [[Bulkhead Pattern]]
  - [[Circuit Breaker]]
  - [[Golden Signals]]

📦 Coverage Analysis:
Missing from MOC but should be included (8 notes):
  - "Exponential Backoff.md" (high confidence)
  - "Load Shedding.md" (high confidence)
  - "Graceful Degradation.md" (medium confidence)
  [... 5 more ...]

🕰️  Staleness Detection:
✅ No archived references
ℹ️  2 notes not updated in >6 months

Would you like to:
A) Create missing notes (Bulkhead Pattern, Circuit Breaker, Golden Signals)
B) Add missing references to MOC (8 notes)
C) Generate detailed report (save as markdown)
D) Fix broken links (remove them)
E) Fix all issues automatically
F) Review each issue individually
```

### Step 8: Execute Fixes

Handle user selection:

#### Option A: Create Missing Notes

For each broken link, create stub file:

```bash
for link in $BROKEN_LINKS; do
  echo "---
tags: []
created: $(date +%Y-%m-%d)
mocs:
  - [[${MOC_NAME}]]
---

# ${link}

[Content to be added]

## Related

- [[${MOC_NAME}]]
" > "200 - Notes/${link}.md"

  echo "✅ Created: 200 - Notes/${link}.md"
done
```

#### Option B: Add Missing References

Add orphaned notes to MOC:

```bash
# Determine appropriate section
SECTION="## Related Notes"  # or existing section

# Add links
for note in $MISSING_NOTES; do
  # Add to MOC
  sed -i '' "/${SECTION}/a\\
- [[$(basename "$note" .md)]]\\
" "$MOC_PATH"

  echo "✅ Added [[$(basename "$note" .md)]] to MOC"
done
```

#### Option C: Generate Detailed Report

Create markdown report file:

```markdown
# MOC Health Report: SRE Concepts MOC
**Date:** 2026-03-26

## Summary
- Total links: 34
- Broken links: 3
- Missing coverage: 8 notes
- Stale references: 2

## Broken Links
1. [[Bulkhead Pattern]] (line 15)
   - Status: File doesn't exist
   - Action: Create stub or remove link

[... detailed report ...]
```

Save to `000 - Inbox/MOC-Health-Report-${DATE}.md`

#### Option D: Fix Broken Links

Remove or comment out broken links:

```bash
for link in $BROKEN_LINKS; do
  # Remove the link line
  sed -i '' "/\[\[${link}\]\]/d" "$MOC_PATH"
done
```

Or comment them:

```bash
# - [[Bulkhead Pattern]]  # TODO: Create this note
```

#### Option E: Fix All Automatically

Comprehensive auto-fix:
1. Create stub files for broken links
2. Add high-confidence orphans to MOC
3. Comment out stale references
4. Generate report

#### Option F: Review Individually

Walk through each issue:

```
Issue 1 of 13:
⚠️  Broken link: [[Bulkhead Pattern]]

Context: Under "## Reliability Patterns" section

Actions:
A) Create stub file
B) Remove link
C) Skip
D) Manual fix (I'll guide you)
```

### Step 9: Report Results

```
✅ MOC Health Check Complete

Actions taken:
- Created 3 stub files
- Added 5 missing notes to MOC
- Commented out 2 stale references
- Generated detailed report

Updated MOC:
- Total links: 39 (was 34)
- Broken links: 0 (was 3)
- Coverage improved: 13 additional notes linked

Next steps:
- Fill in content for stub files
- Review stale references
- Run /discover-links to find more connections
```

## Special Cases

### Perfect MOC

```
✅ "SRE Concepts MOC" is healthy!

Structure: ✅ Excellent
Links: ✅ All valid (34/34)
Coverage: ✅ Good (no orphans detected)
Freshness: ✅ All references current

No issues found. Great job maintaining this MOC!
```

### No MOCs in Vault

```
ℹ️  No MOCs found in 100 - MOCs/

MOCs are organizational notes that link related content.
Create your first MOC? [Y/n]

Suggested: "Home MOC" (main entry point)
```

### Empty or Minimal MOC

```
⚠️  "New MOC" has only 2 links

This MOC might be underdeveloped.

Options:
A) Find related notes to add
B) Keep as minimal MOC
C) Delete and redistribute links
```

### Circular MOC References

```
ℹ️  Detected MOC loop:
"SRE Concepts MOC" → "Reliability MOC" → "SRE Concepts MOC"

This is valid (MOCs can reference each other) but verify it's intentional.
```

## Error Handling

### MOC File Not Found

```
❌ MOC not found: "Nonexistent MOC"

Available MOCs:
- SRE Concepts MOC
- Incident Management MOC
- Observability MOC

Choose from list? [Y/n]
```

### Read Permission Error

```
❌ Cannot read MOC file (permission denied)

File may be locked by Obsidian. Close it and retry? [Y/n]
```

### Too Many Issues

```
⚠️  Found 47 issues in this MOC

That's a lot! Process in stages:
A) Fix critical issues first (broken links)
B) Fix all automatically
C) Generate report for manual review
```

## Best Practices

1. **Run regularly** - Monthly MOC health checks
2. **Prioritize broken links** - Fix first
3. **Review orphans carefully** - Not all belong
4. **Maintain structure** - Keep sections organized
5. **Clean stale content** - Archive old references
6. **Create stubs thoughtfully** - Add meaningful placeholders
7. **Don't over-populate** - MOC with 50+ links may need splitting
8. **Use sections** - Group related topics
9. **Link to sub-MOCs** - When appropriate
10. **Document in report** - Keep records of changes

## Integration with Utilities

This skill uses shared utilities:

- **lib/vault-scanner.md** - Get MOC list and vault index
- **lib/link-parser.md** - Validate and add links
- **lib/content-analyzer.md** - Match topics for coverage
- **lib/moc-matcher.md** - Find related orphans

## Usage Examples

### Example 1: Healthy MOC

```
User: /check-moc-health SRE Concepts MOC

Analyzing "SRE Concepts MOC.md"...

✅ MOC is healthy!
Structure: ✅ Links: ✅ (34/34 valid)
Coverage: ✅ Freshness: ✅

No issues found.
```

### Example 2: Broken Links

```
Analyzing "Reliability MOC.md"...

⚠️  3 broken links:
  - [[Circuit Breaker]]
  - [[Bulkhead Pattern]]
  - [[Golden Signals]]

Create stub files? [Y/n]

✅ Created 3 stubs
✅ MOC now healthy
```

### Example 3: Coverage Gaps

```
📦 Coverage Analysis:
8 related notes not in MOC:
  - "Exponential Backoff.md"
  - "Load Shedding.md"
  [...]

Add these to MOC? [Y/n]

✅ Added 8 notes
✅ MOC coverage improved
```

## Related Skills

- **/discover-links** - Find connections between notes
- **/classify-inbox** - Add notes to MOCs
- **/create-note** - Create notes referenced by MOCs

## Summary

The check-moc-health skill performs comprehensive MOC audits by validating structure, checking links, finding missing coverage, and detecting stale references. Provides interactive fixing with detailed reporting.
