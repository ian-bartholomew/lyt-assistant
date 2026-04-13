---
name: create-note
description: This skill should be used when the user asks to "create a note", "create new note", "make a note", "write a note", "add a note", or wants guided note creation assistance. Provides interactive note creation with proper structure, classification, and linking.
version: 1.0.0
allowed-tools: [Bash, Edit, AskUserQuestion]
---

# Create Note Skill

Guided creation of properly structured Notes or Reference files with appropriate links, frontmatter, and MOC associations.

## Purpose

Help create new notes with correct structure, classification, linking, and organization following LYT principles. Distinguishes between Notes (personal insights) and Reference (external information), suggests appropriate titles, and establishes connections to existing vault content.

For advanced Obsidian markdown syntax (callouts, embeds, block references), follow the `obsidian:obsidian-markdown` skill.

## When to Use

Invoke this skill when:

- User explicitly runs `/create-note`
- User asks to create, write, or add a new note
- User mentions making a new file for the vault
- User wants help structuring new content

## Workflow Overview

1. **Validate vault** - Pre-flight check and LYT structure validation
2. **Determine source** - Existing content or start from scratch
3. **Analyze content** - Classify type and extract topics
4. **Suggest structure** - Title, destination, links
5. **Review and edit** - Interactive refinement
6. **Create file** - Write with proper frontmatter and links

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

### Step 2: Determine Content Source

Ask user about starting point:

```
Let me help you create a note.

Do you have content already, or should I help you structure something new?
A) I have content in inbox
B) I have content elsewhere
C) Start from scratch with a topic
```

Handle each option:

#### Option A: Content in Inbox

List inbox files:

```bash
obsidian files folder="000 - Inbox" ext=md
```

Present list to user:

```
Select a file from inbox:
1) random thoughts on circuit breakers.md
2) error budget notes.md
3) terraform state docs.md
```

Use **AskUserQuestion** to get selection, then read selected file:

```bash
obsidian read file="[selected file name]"
```

Proceed to analysis.

#### Option B: Content Elsewhere

Ask for file path and read content:

```bash
obsidian read file="[user-provided file name]"
```

If file not found, try searching:

```bash
obsidian search query="[partial file name]" limit=5
```

Proceed to analysis.

#### Option C: Start from Scratch

Ask for topic and guide creation:

```
What topic or concept would you like to write about?

Examples:
- "Circuit breakers prevent cascading failures"
- "Error budgets enable feature velocity"
- "Kubernetes service mesh patterns"
```

Use **AskUserQuestion** to get topic, then suggest template based on likely type (Note vs Reference).

### Step 3: Analyze Content

Use **lib/analysis.md** instructions for classification:

**Read file content:**

```bash
obsidian read file="Note Name"
```

**Classify as Note, Reference, or Project** based on:

- First-person language, assertion titles → Note
- External quotes, code blocks, source attribution → Reference
- Action items, deadlines, deliverables → Project

**Extract topics and themes** from content and headings:

```bash
obsidian outline file="Note Name" format=md
```

**Assess atomicity:**

```bash
obsidian wordcount file="Note Name" words
obsidian outline file="Note Name" total
```

- Under 500 words: Good for a Note
- Over 500 words: May be Reference or needs splitting
- More than 4 headings: May cover multiple topics

**Determine confidence level** (High/Medium/Low).

**Output format:**

```
Analyzing content...

📄 Content Analysis:
- Type: Note (personal insight)
- Topics: circuit breakers, reliability, fault tolerance
- Word count: 287
- Atomicity: Single concept (3 sections)
- Confidence: High
- Reasoning: First-person synthesis, assertion-style
```

If project detected, suggest using `/create-project` for proper hub creation.

### Step 4: Suggest Title

For **Notes** (200 - Notes/):

Suggest assertion-style title following pattern: `[Subject] [verb] [outcome]`

Examples:

- "Circuit breakers prevent cascading failures"
- "Error budgets enable feature velocity"
- "Bulkhead pattern isolates component failures"

For **References** (300 - Reference/):

Suggest descriptive title:

- "Terraform State Management Guide"
- "Kubernetes Service Mesh Comparison"
- "PostgreSQL Performance Tuning"

Present suggestion:

```
📝 Suggested Title:
   "Circuit breakers prevent cascading failures"

Would you like to:
A) Use this title
B) Edit title
C) Keep original
```

Use **AskUserQuestion** to get their choice.

### Step 5: Suggest Destination

Based on classification:

**For Notes:**

```
📁 Suggested Destination:
   200 - Notes/Circuit breakers prevent cascading failures.md
```

**For References:**

Use **lib/analysis.md** to match topics to Reference subfolders:

```bash
obsidian folders folder="300 - Reference"
```

Compare extracted topics against folder names. Present suggestion:

```
📁 Suggested Destination:
   300 - Reference/SRE-Concepts/Circuit Breaker Pattern.md

Available alternatives:
- 300 - Reference/Reliability-Patterns/
- 300 - Reference/Tools/
```

If no good match exists:

```
Topics [new-topic] don't match existing folders.

Options:
A) Create new folder: "300 - Reference/new-topic/"
B) Place in closest match: "300 - Reference/SRE-Concepts/"
C) Specify custom location
```

### Step 6: Suggest MOC Links

Use **lib/analysis.md** instructions for MOC matching:

**Get all MOCs:**

```bash
obsidian files folder="100 - MOCs" ext=md
```

**For each MOC, calculate score:**

- **Keyword match (weight: 2x):** Read MOC content and count topic overlaps
- **Link overlap (weight: 1x):** Get MOC links and count overlaps with content topics
- **Title match (weight: 3x):** Check if MOC title contains any content topic

**Assign confidence:**

- **High (score >= 5):** Multiple keyword matches, clear thematic fit
- **Medium (score 2-4):** Some matches, related but not primary
- **Low (score 1):** Weak connection

**Present suggestions:**

```
🗺️  Suggested MOCs:
  - [[Reliability Patterns MOC]] (high confidence) — 3 keyword matches, title match
  - [[SRE Concepts MOC]] (medium confidence) — 1 keyword match, parent MOC
```

**Check for new MOC opportunity:**

```bash
obsidian search query="reliability patterns" total
```

If count >= 3 and no MOC covers this topic:

```
💡 Create new MOC?
   "Reliability Patterns MOC" doesn't exist but would fit 3+ existing notes
   Create it? [Y/n]
```

### Step 7: Suggest Related Links

Search vault for related content using extracted topics:

**For each topic, search vault:**

```bash
obsidian search query="[topic]" path="200 - Notes" limit=5
obsidian search query="[topic]" path="300 - Reference" limit=5
```

**Check relevance** by reading files and counting topic frequency.

**Filter suggestions:**

- Skip if only one passing mention
- Check link counts to avoid over-linking:

  ```bash
  obsidian links file="Note" total
  ```

  If > 15, only show high-confidence suggestions.

**Present suggestions:**

```
🔗 Suggested Related Links:
  - [[Bulkhead Pattern]]
  - [[Graceful Degradation]]
  - [[Exponential Backoff]]
```

### Step 8: Interactive Review

Present complete suggestion:

```
📋 Note Summary:

Title: "Circuit breakers prevent cascading failures"
Type: Note
Destination: 200 - Notes/
MOCs: [[Reliability Patterns MOC]], [[SRE Concepts MOC]]
Related: [[Bulkhead Pattern]], [[Graceful Degradation]]

Would you like to:
A) Create with these settings (recommended)
B) Edit title
C) Edit destination
D) Edit MOCs
E) Edit related links
F) Cancel
```

Use **AskUserQuestion** to get their choice. Allow iterative refinement for options B-E.

### Step 9: Create File

Once approved, create file with proper structure using **lib/obsidian-operations.md** instructions:

#### For Notes (200 - Notes/)

**Create file:**

```bash
obsidian create path="200 - Notes/[title].md" content="# [title]\n\n[User's content or placeholder]" silent
```

**Set properties:**

```bash
obsidian property:set name="tags" value="[tag1],[tag2],[tag3]" type=list file="[title]"
obsidian property:set name="created" value="2026-04-13" type=date file="[title]"
obsidian property:set name="mocs" value="[[Reliability Patterns MOC]],[[SRE Concepts MOC]]" type=list file="[title]"
```

**Add Related section:**

```bash
obsidian append file="[title]" content="\n## Related\n\n- [[Bulkhead Pattern]]\n- [[Graceful Degradation]]\n- [[Exponential Backoff]]"
```

**Example final structure:**

```markdown
---
tags: [circuit-breaker, reliability, fault-tolerance]
created: 2026-04-13
mocs:
  - [[Reliability Patterns MOC]]
  - [[SRE Concepts MOC]]
---

# Circuit breakers prevent cascading failures

[User's content or placeholder]

## Related

- [[Bulkhead Pattern]]
- [[Graceful Degradation]]
- [[Exponential Backoff]]
```

#### For References (300 - Reference/)

**Create file:**

```bash
obsidian create path="300 - Reference/[subfolder]/[title].md" content="# [title]\n\n[User's content or placeholder]" silent
```

**Set properties:**

```bash
obsidian property:set name="tags" value="[tag1],[tag2]" type=list file="[title]"
obsidian property:set name="created" value="2026-04-13" type=date file="[title]"
obsidian property:set name="type" value="external" file="[title]"
obsidian property:set name="source" value="[URL or book if known]" file="[title]"
obsidian property:set name="mocs" value="[[Reliability Patterns MOC]]" type=list file="[title]"
```

**Add Related section:**

```bash
obsidian append file="[title]" content="\n## Related\n\n- [[Bulkhead Pattern]]\n- [[Retry Patterns]]"
```

**Example final structure:**

```markdown
---
tags: [circuit-breaker, pattern]
created: 2026-04-13
type: external
source: [URL or book if known]
mocs:
  - [[Reliability Patterns MOC]]
---

# Circuit Breaker Pattern

[User's content or placeholder]

## Related

- [[Bulkhead Pattern]]
- [[Retry Patterns]]
```

### Step 10: Report Success

```
✅ Created: 200 - Notes/Circuit breakers prevent cascading failures.md
✅ Added to [[Reliability Patterns MOC]]
✅ Added 3 related links
✅ Created frontmatter with tags and metadata

Next steps:
- Fill in content if placeholder was used
- Review and refine links
- Update MOCs with new note
```

Verify file creation:

```bash
obsidian file file="[title]"
```

## Content Analysis Details

### Determining Note vs Reference

**Note indicators:**

- First-person language
- Personal insights
- Assertion-style claim
- Short and focused
- Your voice throughout

**Reference indicators:**

- External quotes
- Code examples
- Commands/configuration
- Multiple topics
- Source attribution

**When ambiguous:**

```
This content could be either:
- Note: Contains personal insights
- Reference: Contains specific examples

Help me decide:
1. Is this your synthesis, or documentation?
2. Will this need regular updates from external sources?
3. Do you reference this for lookup, or is it an insight?
```

Use **AskUserQuestion** to get clarification.

### Atomicity Check

Ensure note covers single concept:

**Count sections:**

```bash
obsidian outline file="Note" total
```

If more than 4 headings:

```
⚠️  Multiple topics detected ([count] sections)
Consider splitting into separate notes:
- Note 1: [First topic]
- Note 2: [Second topic]
```

Use **AskUserQuestion** to confirm split or proceed as-is.

### Title Generation

For Notes, convert content to assertion:

```
Content: "I've learned that circuit breakers are essential for preventing cascading failures in distributed systems"

→ Title: "Circuit breakers prevent cascading failures"
```

Pattern: Extract main claim, simplify to assertion form.

## Special Cases

### Starting from Scratch

If user chooses to start fresh:

1. **Ask for topic**
2. **Research if needed** (suggest `/research` for unfamiliar topics)
3. **Provide template** based on type
4. **User fills in content**
5. **Review and create**

**Note template:**

```markdown
# [Assertion-style title]

[Opening: State the insight clearly]

[Body: Explain reasoning, provide context]

[Examples or evidence if applicable]

[Conclusion: Reinforce the insight]

## Related

- [[Related Note 1]]
- [[Related Note 2]]
```

**Reference template:**

```markdown
# [Descriptive Title]

## Overview

[Brief introduction]

## Key Concepts

[Main content with sections]

## Examples

[Code or configuration examples]

## References

[External sources]

## Related

- [[Related Reference 1]]
```

### Existing Content with Poor Structure

If content is unstructured:

```
⚠️  Content appears unstructured

Options:
A) Auto-structure (extract title, organize sections)
B) Use as-is with frontmatter only
C) Manually structure (I'll guide you)
```

Use **AskUserQuestion** to get their choice.

### Empty or Minimal Content

If content is very brief:

```bash
obsidian wordcount file="Note" words
```

If under 50 words:

```
ℹ️  Content is brief (47 words)

This could work as:
- Note: If it's a focused insight (good!)
- Placeholder: Fill in more detail later

Create now or expand first?
```

Use **AskUserQuestion** to confirm.

## Error Handling

### File Already Exists

Check if file exists before creating:

```bash
obsidian file file="[title]"
```

If file info is returned (file exists):

```
⚠️  File already exists: "200 - Notes/Circuit breakers prevent cascading failures.md"

Options:
A) Choose different name
B) Merge with existing (manual)
C) Overwrite (dangerous!)
D) Open existing for editing
```

Use **AskUserQuestion** to get their choice.

### Invalid Destination

If creating at a subfolder that might not exist:

```bash
obsidian folders folder="300 - Reference"
```

Verify the target subfolder exists in the list. If not:

```
❌ Destination doesn't exist: "300 - Reference/New-Category/"

Options:
A) Create directory
B) Choose existing directory
C) Cancel
```

For option A, create a file in the new folder (Obsidian CLI creates intermediate folders automatically):

```bash
obsidian create path="300 - Reference/New-Category/.gitkeep" content="" silent
```

### MOC Doesn't Exist

Verify MOC exists:

```bash
obsidian file file="[MOC name]"
```

If not found:

```
⚠️  MOC doesn't exist: "Reliability Patterns MOC"

Options:
A) Create MOC now
B) Skip this MOC
C) Choose different MOC
```

Use **AskUserQuestion** to get their choice.

### No Content Provided

```
ℹ️  No content provided

I'll create a placeholder file with proper structure.
You can fill in the content later in Obsidian.

Proceed?
```

Use **AskUserQuestion** to confirm.

## Best Practices

1. **Assess atomicity** - One concept per Note
2. **Use assertion titles** for Notes
3. **Add minimal but relevant links** - Don't over-link
4. **Create proper frontmatter** from start
5. **Suggest MOC creation** when appropriate
6. **Provide templates** for empty content
7. **Allow iteration** - Easy to edit before creating
8. **Validate paths** before writing
9. **Report clearly** what was created
10. **Guide next steps** after creation

## Integration with Utilities

This skill uses shared utilities:

- **lib/obsidian-operations.md** - All vault operations (read, create, search, properties)
- **lib/analysis.md** - Classify type, extract topics, suggest title, match MOCs

## Usage Examples

### Example 1: Create from Inbox

```
User: /create-note

Do you have content already?
A) I have content in inbox

Select file:
1) random thoughts on circuit breakers.md

[Analyzes content]

This looks like a Note (personal insight).
Suggested title: "Circuit breakers prevent cascading failures"
Destination: 200 - Notes/

Create? [Y/n]

✅ Created: 200 - Notes/Circuit breakers prevent cascading failures.md
```

### Example 2: Start from Scratch

```
Do you have content already?
C) Start from scratch

What topic?
> Error budgets and feature velocity

I'll create a Note template. This seems like personal synthesis.

Title: "Error budgets enable feature velocity"
Type: Note

[Creates template]

✅ Created with placeholder content
Open in Obsidian to complete
```

### Example 3: Reference Creation

```
[Analyzes content]

This looks like Reference material (external documentation).
Type: Reference
Topics: terraform, state management

Suggested destination: 300 - Reference/terraform/
Suggested MOCs: [[Terraform MOC]]

✅ Created: 300 - Reference/terraform/State Management.md
```

## Related Skills

- **/classify-inbox** - Process existing inbox files
- **/research** - Research and create reference notes
- **/check-moc-health** - Verify MOC after adding note

## Summary

The create-note skill provides guided note creation with proper classification, structure, linking, and organization following LYT principles. Ensures new notes are properly integrated into the vault from creation.
