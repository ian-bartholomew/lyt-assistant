---
name: check-moc-health
description: This skill should be used when the user asks to "check MOC health", "analyze MOC", "validate MOC", "check MOC quality", "audit MOC", "check for broken links in MOC", or wants to assess the quality and coverage of a Map of Content.
version: 0.2.0
allowed-tools: [Bash, Edit, AskUserQuestion]
---

# Check MOC Health Skill

Analyze MOC (Map of Content) quality and suggest improvements by checking structure, detecting broken links, finding missing coverage, and identifying stale references.

For advanced Obsidian markdown syntax (callouts, embeds, block references), follow the `obsidian:obsidian-markdown` skill.

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

1. **Pre-flight check** - Verify Obsidian CLI connection
2. **Select MOC** - Choose which MOC to analyze
3. **Structure audit** - Check formatting and organization
4. **Link validation** - Find broken links
5. **Coverage analysis** - Find orphaned notes
6. **Staleness detection** - Identify outdated references
7. **Present report** - Interactive findings and options
8. **Execute fixes** - Apply approved improvements

## Process Flow

### Step 0: Pre-flight Check

Verify Obsidian CLI connection before proceeding:

```bash
obsidian vault
```

If this fails, inform the user that the Obsidian CLI is not available and exit gracefully.

### Step 1: Select MOC to Analyze

Get all MOCs using Obsidian CLI:

```bash
obsidian files folder="100 - MOCs" ext=md
```

Present list to user:

```
Which MOC should I analyze?

1) SRE Concepts MOC
2) Incident Management MOC
3) Observability MOC

Enter number or MOC name:
```

**Alternative:** Accept MOC name as argument:

```
/check-moc-health SRE Concepts MOC
```

### Step 2: Read and Parse MOC

Read MOC file using Obsidian CLI:

```bash
obsidian read file="SRE Concepts MOC"
```

Extract components:

- Frontmatter (properties)
- Headings (structure via `obsidian outline`)
- Links (all [[target]] links via `obsidian links`)
- Sections (organize by heading)

### Step 3: Structure Audit

Check MOC structure and formatting using Obsidian CLI:

#### 3a. Heading Hierarchy

Get heading structure:

```bash
obsidian outline file="SRE Concepts MOC"
```

Verify proper heading levels:

- Should have clear hierarchy: #, ##, ###
- Check for skipped levels (e.g., # → ###)
- Count H1 headings (should be 1)

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

Check if links are organized by section using the outline structure.

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

Read the file content and check for malformed links using the Read tool:

- Markdown links (should be wiki-style [[links]])
- Unclosed links

**Report:**

```
📊 Structure Audit:
✅ Has clear heading hierarchy
✅ Links organized by section
⚠️  Line 23: Malformed link [Example](url) - should be [[Example]]
```

### Step 4: Link Validation (Broken Links)

Check each link target exists using Obsidian CLI:

```bash
# Get all links from the MOC
obsidian links file="SRE Concepts MOC"

# For each link target, verify it exists
obsidian file file="Target Note Name"
```

Use `obsidian unresolved` to get vault-wide unresolved links, then filter for those in the MOC.

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

Find notes that should be in MOC but aren't using the analysis library.

#### 5a. Identify MOC Topics

Use `lib/analysis.md` functions:

- Extract topics from MOC title and sections
- Use heading extraction to identify themes

```bash
# Get section headings
obsidian outline file="SRE Concepts MOC"
```

Extract keywords: "SRE", "reliability", "observability", "incidents"

#### 5b. Find Related Orphans

Use `lib/analysis.md` matching functions:

1. Get all links currently in the MOC:

```bash
obsidian links file="SRE Concepts MOC"
```

1. Search for notes matching MOC topics:

```bash
obsidian search query="reliability" path="200 - Notes"
obsidian search query="sre" path="300 - Reference"
```

1. Get orphaned notes:

```bash
obsidian orphans
```

1. Cross-reference: find notes that match topics but aren't linked from MOC

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

Check if any MOC links point to Archive:

```bash
# For each link target, check its location
obsidian file file="Target Note"
# Check if path contains "400 - Archive"
```

Or search for archived content:

```bash
obsidian search query="term" path="400 - Archive"
```

#### 6b. Old Content

Check last modified dates using `obsidian file`:

```bash
# For each link target
obsidian file file="Target Note"
# Examine the modified date in the output
```

Calculate age and flag notes not updated in >365 days.

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

For each broken link, create stub file using Obsidian CLI:

```bash
obsidian create file="Bulkhead Pattern" path="200 - Notes"

# Set properties
obsidian property:set file="Bulkhead Pattern" property=created value="2026-04-13"
obsidian property:set file="Bulkhead Pattern" property=tags value="[]"
obsidian property:set file="Bulkhead Pattern" property=mocs value="[[SRE Concepts MOC]]"
```

Then use Edit tool to add initial content:

```markdown
# Bulkhead Pattern

[Content to be added]

## Related

- [[SRE Concepts MOC]]
```

#### Option B: Add Missing References

Add orphaned notes to MOC using Edit tool:

```bash
# Read the MOC
obsidian read file="SRE Concepts MOC"
```

Use Edit tool to add links in appropriate sections:

```markdown
## Related Notes

- [[Exponential Backoff]]
- [[Load Shedding]]
```

#### Option C: Generate Detailed Report

Create markdown report file using Obsidian CLI:

```bash
obsidian create file="MOC Health Report - SRE Concepts MOC - 2026-04-13" path="000 - Inbox"
```

Then use Edit tool to populate:

```markdown
# MOC Health Report: SRE Concepts MOC
**Date:** 2026-04-13

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

#### Option D: Fix Broken Links

Remove broken links using Edit tool:

```bash
# Read the MOC
obsidian read file="SRE Concepts MOC"
```

Use Edit tool to remove or comment out broken link lines:

```markdown
# - [[Bulkhead Pattern]]  # TODO: Create this note
```

#### Option E: Fix All Automatically

Comprehensive auto-fix:

1. Create stub files for broken links (Option A)
2. Add high-confidence orphans to MOC (Option B)
3. Comment out stale references (Edit tool)
4. Generate report (Option C)

#### Option F: Review Individually

Walk through each issue with AskUserQuestion:

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

### Obsidian CLI Connection Error

```
❌ Cannot connect to Obsidian CLI

Please ensure:
1. Obsidian is running
2. Local REST API plugin is enabled
3. API token is configured

Try again? [Y/n]
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

## Integration with Libraries

This skill uses shared libraries:

- **lib/obsidian-operations.md** - All CLI-based vault operations
- **lib/analysis.md** - Content classification, topic extraction, MOC matching

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

The check-moc-health skill performs comprehensive MOC audits by validating structure, checking links, finding missing coverage, and detecting stale references. Provides interactive fixing with detailed reporting. Uses Obsidian CLI for all vault operations.
