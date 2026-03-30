---
name: classify-inbox
description: This skill should be used when the user asks to "process inbox", "classify inbox", "organize inbox files", "move files from inbox", or wants to process items in the "000 - Inbox" folder. Provides interactive classification of inbox files with intelligent destination suggestions and link recommendations.
version: 0.1.0
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob, AskUserQuestion]
---

# Classify Inbox Skill

Process inbox files interactively with intelligent classification, destination suggestions, and link recommendations based on content analysis.

## Purpose

Reduce friction in processing inbox items by analyzing each file, determining its type (Note vs Reference), suggesting destination folders, identifying relevant MOCs, and recommending related note links. Present suggestions interactively for user review and editing before execution.

## When to Use

Invoke this skill when:

- User explicitly runs `/classify-inbox`
- User mentions processing, organizing, or cleaning up the inbox
- User wants to move files from `000 - Inbox/`
- User asks to classify or categorize inbox content

## Workflow Overview

1. **Scan vault** - Build index of MOCs, notes, references
2. **List inbox files** - Find all markdown files in `000 - Inbox/`
3. **Process each file** - Analyze, suggest, present, execute
4. **Report completion** - Summary of moves and links added

## Process Flow

### Step 1: Initialize and Validate

Check vault structure exists:

```bash
if [ ! -d "000 - Inbox" ]; then
  echo "⚠️  Inbox directory not found"
  echo "This doesn't appear to be an LYT vault"
  exit 1
fi

if [ ! -d "100 - MOCs" ] || [ ! -d "150 - Projects" ] || [ ! -d "200 - Notes" ] || [ ! -d "300 - Reference" ]; then
  echo "⚠️  Missing LYT directories (MOCs, Projects, Notes, or Reference)"
  exit 1
fi
```

### Step 2: Scan Vault

Build complete vault index using **lib/vault-scanner.md** instructions:

- Get all inbox files
- Get all MOC files with their links
- Get Reference folder structure
- Get existing notes for related content matching

Store index for reuse throughout processing.

### Step 3: Process Each Inbox File

For each file in inbox:

#### 3a. Read and Analyze Content

Use **lib/content-analyzer.md** instructions:

- Read file content
- Classify as Note, Reference, or Project
- Extract topics and themes
- Assess atomicity
- Suggest title if needed
- Determine confidence level

**Output format:**

```
📄 Processing: "Error Budget Calculations.md" (1 of 3)

Content Analysis:
- Type: Reference (Confidence: High)
- Topics: error budgets, SLOs, reliability math
- Word count: 342
- Reasoning: Contains formulas and lookup information
```

#### 3b. Suggest Destination

Based on classification:

**If Project (150 - Projects/):**

- Destination: `150 - Projects/`
- Content describes a goal with deliverables, deadlines, or action items
- Suggest using `/create-project` for proper hub creation with frontmatter
- Project indicators: action items, deadlines, deliverables, goals, "need to", "we should", task lists

**If Note (200 - Notes/):**

- Destination: `200 - Notes/`
- Suggest assertion-style title if current title isn't one

**If Reference (300 - Reference/):**

- Use topics to match against existing Reference subfolders
- Suggest best-fit subfolder (e.g., `300 - Reference/SRE-Concepts/`)
- If no good match, list options or suggest creating new subfolder

**Output format:**

```
📁 Suggested Destination:
   300 - Reference/SRE-Concepts/
```

#### 3c. Suggest MOC Links

Use **lib/moc-matcher.md** instructions:

- Extract topics from content
- Score all MOCs by relevance
- Return top 2-3 matches with confidence levels
- Check if new MOC should be created

**Output format:**

```
🗺️  Suggested MOCs:
  - [[SLOs MOC]] (high confidence)
  - [[SRE Concepts MOC]] (medium confidence)
```

#### 3d. Suggest Related Note Links

Search vault for related content:

```bash
# Extract key terms from content
TERMS=$(extract_topics "$CONTENT")

# Search for files mentioning same terms
for term in $TERMS; do
  grep -rl "$term" "200 - Notes" "300 - Reference" --include="*.md"
done
```

Filter and rank:

- Exclude current file
- Exclude already-linked files
- Rank by topic overlap
- Return top 2-3 suggestions

**Output format:**

```
🔗 Suggested Related Links:
  - [[Implementing Service Level Objectives-Hidalgo]] (book notes)
  - [[SLO Calculations]] (reference)
```

#### 3e. Check for New MOC Opportunity

Using **lib/moc-matcher.md** logic:

If 3+ notes share topic not covered by existing MOCs:

```
💡 New MOC Opportunity:
   3 notes about "reliability patterns" without dedicated MOC
   Consider creating: "Reliability Patterns MOC"
```

### Step 4: Present Options Interactively

Use **AskUserQuestion** tool to present structured options:

```
Would you like to:
A) Accept and move (recommended)
B) Edit destination folder
C) Edit links
D) Skip this file
E) Cancel operation
```

Handle each choice:

#### Option A: Accept and Move

Execute the suggested moves and link additions.

#### Option B: Edit Destination

```
Current suggestion: 300 - Reference/SRE-Concepts/

Available Reference folders:
1. 300 - Reference/SRE-Concepts/
2. 300 - Reference/Reading/Book-Summaries/
3. 300 - Reference/Tools/
4. 300 - Reference/Incident-Management/
5. [Custom path]

Choose destination (1-5):
```

Update destination and proceed.

#### Option C: Edit Links

```
Suggested links:
1. [[SLOs MOC]]
2. [[SRE Concepts MOC]]
3. [[Implementing Service Level Objectives-Hidalgo]]

Actions:
- Keep all
- Remove specific links (enter numbers: 2,3)
- Add additional links (enter names)
```

Update link list and proceed.

#### Option D: Skip

Move to next file without changes.

#### Option E: Cancel

Stop processing, don't modify any files.

### Step 5: Execute Approved Actions

For each approved file:

#### 5a. Move File

Use Bash tool:

```bash
DEST="300 - Reference/SRE-Concepts/"
FILE="000 - Inbox/Error Budget Calculations.md"

# Check destination exists
if [ ! -d "$DEST" ]; then
  mkdir -p "$DEST"
fi

# Check for conflicts
if [ -f "${DEST}/$(basename "$FILE")" ]; then
  # Handle conflict (see Error Handling section)
fi

# Move file
mv "$FILE" "$DEST"
```

#### 5b. Add MOC Links

Use **lib/link-parser.md** instructions:

- Add MOC links to frontmatter `mocs:` field
- If frontmatter doesn't exist, create it
- Use **lib/frontmatter.md** for frontmatter operations

```markdown
---
tags: [sre, reliability]
created: 2026-03-26
mocs:
  - [[SLOs MOC]]
  - [[SRE Concepts MOC]]
---
```

#### 5c. Add Related Links

Add to "## Related" section:

- If section exists, append
- If not, create at end of file
- Use **lib/link-parser.md** for link insertion

```markdown
## Related

- [[Implementing Service Level Objectives-Hidalgo]]
- [[SLO Calculations]]
```

#### 5d. Update Frontmatter Metadata

Add or update fields:

```yaml
---
tags: [error-budget, slo, reliability]
created: 2026-03-26
type: external  # for Reference files
---
```

### Step 6: Verify and Report

After each file:

```
✅ Moved to: 300 - Reference/SRE-Concepts/Error Budget Calculations.md
✅ Added 2 MOC links
✅ Added 2 related links
✅ Updated frontmatter
```

After all files:

```
📊 Inbox Processing Complete

Processed: 3 files
Moved: 2 files
Skipped: 1 file
- Notes: 0
- References: 2
Links added: 8
MOCs updated: 3

✅ Inbox is now clean!
```

## Error Handling

### Empty Inbox

```
✅ Inbox is clean! No files to process.
```

### File Conflict at Destination

```
⚠️  File "Error Budget.md" already exists at destination

Options:
A) Rename new file to "Error Budget (2).md"
B) Merge with existing file (manual)
C) Skip this file
D) Overwrite existing (dangerous!)
```

### Ambiguous Classification

```
📄 Content Analysis:
- Mixed signals detected
  - Has first-person language (Note indicator)
  - Has code blocks (Reference indicator)

Help me decide:
1. Is this your synthesis/opinion, or documentation?
2. Will this need regular updates from external sources?
```

Use **AskUserQuestion** to clarify.

### Broken Links During Addition

```
⚠️  Cannot add link [[Non-existent Note]]
Target file doesn't exist in vault

Options:
A) Skip this link
B) Create stub file
C) Edit link target
```

### Permission Error

```
❌ Cannot write to "file.md"
File may be locked by Obsidian

Close the file and retry?
```

### Invalid Destination

```
⚠️  Destination "invalid/path/" doesn't exist

Options:
A) Create directory
B) Choose different destination
C) Skip this file
```

## Best Practices

1. **Scan vault once** at start, reuse index
2. **Process files sequentially** for user control
3. **Always validate paths** before moving
4. **Check for duplicates** before adding links
5. **Preserve file content** - never corrupt files
6. **Provide clear feedback** at each step
7. **Allow editing** before execution
8. **Report errors clearly** with recovery options
9. **Summarize results** at end
10. **Clean up** - remove empty sections

## Integration with Utilities

This skill uses all shared utilities:

- **lib/vault-scanner.md** - Initial vault scan and indexing
- **lib/content-analyzer.md** - Classify Note vs Reference, extract topics
- **lib/moc-matcher.md** - Suggest relevant MOCs
- **lib/link-parser.md** - Add and validate links
- **lib/frontmatter.md** - Update metadata

## Usage Examples

### Example 1: Simple Reference File

```
User: /classify-inbox

📄 Processing: "Terraform State Locking.md" (1 of 1)

Content Analysis:
- Type: Reference (Confidence: High)
- Topics: terraform, state management, locking
- Reasoning: Contains commands and configuration examples

📁 Suggested Destination: 300 - Reference/terraform/
🗺️  Suggested MOCs: [[Terraform MOC]]
🔗 Suggested Links: [[Terraform Best Practices]]

[User accepts]

✅ Moved to: 300 - Reference/terraform/Terraform State Locking.md
✅ Added 1 MOC link
✅ Added 1 related link

✅ Inbox is now clean!
```

### Example 2: Note with Title Suggestion

```
📄 Processing: "thoughts on circuit breakers.md"

Content Analysis:
- Type: Note (Confidence: High)
- First-person synthesis detected
- Suggested title: "Circuit breakers prevent cascading failures"

📁 Suggested Destination: 200 - Notes/
🗺️  Suggested MOCs: [[Reliability Patterns MOC]], [[SRE Concepts MOC]]

Would you like to:
A) Accept (including title change)
B) Keep original title
C) Edit manually
```

### Example 3: Multiple Files

```
Found 3 files in inbox. Processing...

[File 1 processed]
[File 2 processed]
[File 3 skipped by user]

📊 Summary:
Processed: 3 files
Moved: 2 files
Skipped: 1 file
```

## Tips

- **Process regularly** - Don't let inbox grow too large
- **Review suggestions** - Edit before accepting
- **Check MOC relevance** - Remove low-confidence suggestions
- **Maintain atomicity** - Split files if they cover multiple topics
- **Use consistent naming** - Follow vault conventions
- **Create MOCs proactively** - When patterns emerge
- **Link bidirectionally** - When appropriate
- **Archive old content** - Move stale items to `400 - Archive/`

## Related Skills

- **/create-note** - Create new notes from scratch
- **/create-project** - Create project hubs (when inbox item is a project)
- **/archive-project** - Complete and archive projects
- **/discover-links** - Find missing connections after classification
- **/check-moc-health** - Verify MOCs after adding links

## Summary

The classify-inbox skill provides intelligent, interactive inbox processing by analyzing content, suggesting destinations and links, and executing approved actions. Uses all shared utilities for consistent vault operations.
