---
name: classify-inbox
description: This skill should be used when the user asks to "process inbox", "classify inbox", "organize inbox files", "move files from inbox", or wants to process items in the "000 - Inbox" folder. Provides interactive classification of inbox files with intelligent destination suggestions and link recommendations.
version: 1.0.0
allowed-tools: [Bash, Edit, AskUserQuestion]
---

# Classify Inbox Skill

Process inbox files interactively with intelligent classification, destination suggestions, and link recommendations based on content analysis.

## Purpose

Reduce friction in processing inbox items by analyzing each file, determining its type (Note vs Reference), suggesting destination folders, identifying relevant MOCs, and recommending related note links. Present suggestions interactively for user review and editing before execution.

For advanced Obsidian markdown syntax (callouts, embeds, block references), follow the `obsidian:obsidian-markdown` skill.

## When to Use

Invoke this skill when:

- User explicitly runs `/classify-inbox`
- User mentions processing, organizing, or cleaning up the inbox
- User wants to move files from `000 - Inbox/`
- User asks to classify or categorize inbox content

## Workflow Overview

1. **Validate vault** - Pre-flight check and LYT structure validation
2. **Scan vault** - Build index of MOCs, notes, references
3. **List inbox files** - Find all markdown files in `000 - Inbox/`
4. **Process each file** - Analyze, suggest, present, execute
5. **Report completion** - Summary of moves and links added

## Process Flow

### Step 1: Pre-flight Check and Validate

Before any vault operation, verify Obsidian is running:

```bash
obsidian vault
```

If this fails, present to the user:

```
Obsidian doesn't appear to be running. This plugin requires an open Obsidian vault.

Options:
A) Open Obsidian and retry
B) Cancel
```

Use **AskUserQuestion** to get their choice.

Once Obsidian is confirmed running, validate LYT vault structure:

```bash
obsidian folders
```

Verify output contains all required LYT folders: `000 - Inbox`, `100 - MOCs`, `150 - Projects`, `200 - Notes`, `300 - Reference`, `400 - Archive`.

If any are missing:

```
⚠️  Missing LYT directories: [list missing folders]
This doesn't appear to be a complete LYT vault.
```

Exit if critical folders are missing.

### Step 2: Scan Vault

Build complete vault index using **lib/obsidian-operations.md** and **lib/analysis.md** instructions:

**Get inbox files:**

```bash
obsidian files folder="000 - Inbox" ext=md
```

**Get all MOC files:**

```bash
obsidian files folder="100 - MOCs" ext=md
```

**Get Reference folder structure:**

```bash
obsidian folders folder="300 - Reference"
```

**Get existing notes:**

```bash
obsidian files folder="200 - Notes" ext=md
```

Store index for reuse throughout processing.

### Step 3: Process Each Inbox File

For each file in inbox:

#### 3a. Read and Analyze Content

Use **lib/analysis.md** instructions:

**Read file content:**

```bash
obsidian read file="Inbox Note"
```

**Classify as Note, Reference, or Project** based on:

- First-person language, assertion titles → Note
- External quotes, code blocks, source attribution → Reference
- Action items, deadlines, deliverables → Project

**Extract topics and themes** from content and headings:

```bash
obsidian outline file="Inbox Note" format=md
```

**Assess atomicity:**

```bash
obsidian wordcount file="Inbox Note" words
obsidian outline file="Inbox Note" total
```

- Under 500 words: Good for a Note
- Over 500 words: May be Reference or needs splitting
- More than 4 headings: May cover multiple topics

**Suggest title if needed** (assertion-style for Notes).

**Determine confidence level** (High/Medium/Low).

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
- Get folder list:

  ```bash
  obsidian folders folder="300 - Reference"
  ```

- Suggest best-fit subfolder (e.g., `300 - Reference/SRE-Concepts/`)
- If no good match, list options or suggest creating new subfolder

**Output format:**

```
📁 Suggested Destination:
   300 - Reference/SRE-Concepts/
```

#### 3c. Suggest MOC Links

Use **lib/analysis.md** instructions:

**Get all MOCs:**

```bash
obsidian files folder="100 - MOCs" ext=md
```

**For each MOC, calculate relevance score:**

- Read MOC content and check keyword matches
- Get MOC links and check overlap with content topics:

  ```bash
  obsidian links file="MOC Name"
  ```

- Check if MOC title matches content topics

**Return top 2-3 matches** with confidence levels (High/Medium/Low).

**Check if new MOC should be created:**

```bash
obsidian search query="topic term" total
```

If 3+ notes share a topic not covered by existing MOCs, suggest creation.

**Output format:**

```
🗺️  Suggested MOCs:
  - [[SLOs MOC]] (high confidence)
  - [[SRE Concepts MOC]] (medium confidence)
```

#### 3d. Suggest Related Note Links

Search vault for related content by extracting key terms and searching:

```bash
obsidian search query="term" path="200 - Notes"
obsidian search query="term" path="300 - Reference"
```

Get search context for relevance scoring:

```bash
obsidian search:context query="term" format=json
```

Filter and rank:

- Exclude current file
- Get existing links to exclude already-linked files:

  ```bash
  obsidian links file="Inbox Note"
  ```

- Rank by topic overlap
- Return top 2-3 suggestions

**Output format:**

```
🔗 Suggested Related Links:
  - [[Implementing Service Level Objectives-Hidalgo]] (book notes)
  - [[SLO Calculations]] (reference)
```

#### 3e. Check for New MOC Opportunity

Using **lib/analysis.md** logic:

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

```bash
# Get available Reference folders
obsidian folders folder="300 - Reference"
```

Present to user:

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

Use **lib/obsidian-operations.md**:

```bash
# Move to destination
obsidian move file="Error Budget Calculations" to="300 - Reference/SRE-Concepts/"
```

Verify the move:

```bash
obsidian file file="Error Budget Calculations"
```

Handle conflicts: If the file already exists at destination, present options:

```
⚠️  File "Error Budget.md" already exists at destination

Options:
A) Rename new file to "Error Budget (2).md"
B) Merge with existing file (manual)
C) Skip this file
D) Overwrite existing (dangerous!)
```

#### 5b. Add MOC Links

Use **lib/obsidian-operations.md** for frontmatter operations:

Add MOC links to `mocs:` property:

```bash
obsidian property:set name="mocs" value="[[SLOs MOC]],[[SRE Concepts MOC]]" type=list file="Error Budget Calculations"
```

This creates frontmatter if it doesn't exist:

```markdown
---
tags: [sre, reliability]
created: 2026-04-13
mocs:
  - [[SLOs MOC]]
  - [[SRE Concepts MOC]]
---
```

#### 5c. Add Related Links

Add to `## Related` section using append:

```bash
obsidian append file="Error Budget Calculations" content="\n## Related\n\n- [[Implementing Service Level Objectives-Hidalgo]]\n- [[SLO Calculations]]"
```

**If section exists**, read file first and use **Edit** tool to append to existing section rather than creating a duplicate.

#### 5d. Update Frontmatter Metadata

Add or update fields using **lib/obsidian-operations.md**:

```bash
# Add tags
obsidian property:set name="tags" value="error-budget,slo,reliability" type=list file="Error Budget Calculations"

# Set created date
obsidian property:set name="created" value="2026-04-13" type=date file="Error Budget Calculations"

# For Reference files, add type
obsidian property:set name="type" value="external" file="Error Budget Calculations"
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

```bash
obsidian files folder="000 - Inbox" ext=md total
```

If count is 0:

```
✅ Inbox is clean! No files to process.
```

### File Conflict at Destination

If move fails due to existing file:

```
⚠️  File "Error Budget.md" already exists at destination

Options:
A) Rename new file to "Error Budget (2).md"
B) Merge with existing file (manual)
C) Skip this file
D) Overwrite existing (dangerous!)
```

### Ambiguous Classification

If **lib/analysis.md** returns Low confidence:

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

Before adding a link, verify target exists:

```bash
obsidian file file="Target Note"
```

If not found:

```
⚠️  Cannot add link [[Non-existent Note]]
Target file doesn't exist in vault

Options:
A) Skip this link
B) Create stub file
C) Edit link target
```

### Permission Error

If Obsidian CLI command fails with permission error:

```
❌ Cannot write to "file.md"
File may be locked by Obsidian

Close the file and retry?
```

### Obsidian Not Running

If pre-flight check fails:

```
Obsidian doesn't appear to be running. This plugin requires an open Obsidian vault.

Options:
A) Open Obsidian and retry
B) Cancel
```

## Best Practices

1. **Run pre-flight check** before any operation
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

This skill uses shared utilities:

- **lib/obsidian-operations.md** - All vault operations via Obsidian CLI
- **lib/analysis.md** - Classification, topic extraction, MOC matching

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

The classify-inbox skill provides intelligent, interactive inbox processing by analyzing content, suggesting destinations and links, and executing approved actions. Uses shared utilities (**lib/obsidian-operations.md**, **lib/analysis.md**) for consistent vault operations via Obsidian CLI.
