---
name: create-note
description: This skill should be used when the user asks to "create a note", "create new note", "make a note", "write a note", "add a note", or wants guided note creation assistance. Provides interactive note creation with proper structure, classification, and linking.
version: 0.1.0
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob, AskUserQuestion]
---

# Create Note Skill

Guided creation of properly structured Notes or Reference files with appropriate links, frontmatter, and MOC associations.

## Purpose

Help create new notes with correct structure, classification, linking, and organization following LYT principles. Distinguishes between Notes (personal insights) and Reference (external information), suggests appropriate titles, and establishes connections to existing vault content.

## When to Use

Invoke this skill when:
- User explicitly runs `/create-note`
- User asks to create, write, or add a new note
- User mentions making a new file for the vault
- User wants help structuring new content

## Workflow Overview

1. **Determine source** - Existing content or start from scratch
2. **Analyze content** - Classify type and extract topics
3. **Suggest structure** - Title, destination, links
4. **Review and edit** - Interactive refinement
5. **Create file** - Write with proper frontmatter and links

## Process Flow

### Step 1: Determine Content Source

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

```bash
# Scan inbox
INBOX_FILES=$(find "000 - Inbox" -type f -name "*.md")

# Present list
echo "Select a file from inbox:"
for i in $(seq 1 $(echo "$INBOX_FILES" | wc -l)); do
  FILE=$(echo "$INBOX_FILES" | sed -n "${i}p")
  echo "$i) $(basename "$FILE")"
done
```

Read selected file for analysis.

#### Option B: Content Elsewhere

Ask for file path and read content.

#### Option C: Start from Scratch

Ask for topic and guide creation:

```
What topic or concept would you like to write about?

Examples:
- "Circuit breakers prevent cascading failures"
- "Error budgets enable feature velocity"
- "Kubernetes service mesh patterns"
```

### Step 2: Analyze Content

Use **lib/content-analyzer.md** instructions:

```
Analyzing content...

📄 Content Analysis:
- Type: Note (personal insight)
- Topics: circuit breakers, reliability, fault tolerance
- Atomicity: Single concept
- Confidence: High
- Reasoning: First-person synthesis, assertion-style
```

### Step 3: Suggest Title

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

### Step 4: Suggest Destination

Based on classification:

**For Notes:**
```
📁 Suggested Destination:
   200 - Notes/Circuit breakers prevent cascading failures.md
```

**For References:**

Use **lib/content-analyzer.md** to match topics to Reference subfolders:

```
📁 Suggested Destination:
   300 - Reference/SRE-Concepts/Circuit Breaker Pattern.md

Available alternatives:
- 300 - Reference/Reliability-Patterns/
- 300 - Reference/Tools/
```

### Step 5: Suggest MOC Links

Use **lib/moc-matcher.md** instructions:

```
🗺️  Suggested MOCs:
  - [[Reliability Patterns MOC]] (high confidence)
  - [[SRE Concepts MOC]] (medium confidence)

💡 Create new MOC?
   "Reliability Patterns MOC" doesn't exist but would fit 3+ existing notes
   Create it? [Y/n]
```

### Step 6: Suggest Related Links

Search vault for related content:

```bash
# Extract topics
TOPICS=$(extract_topics "$CONTENT")

# Find related notes
for topic in $TOPICS; do
  grep -rl "$topic" "200 - Notes" "300 - Reference" --include="*.md"
done
```

Present suggestions:

```
🔗 Suggested Related Links:
  - [[Bulkhead Pattern]]
  - [[Graceful Degradation]]
  - [[Exponential Backoff]]
```

### Step 7: Interactive Review

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

### Step 8: Create File

Once approved, create file with proper structure:

#### For Notes (200 - Notes/):

```markdown
---
tags: [circuit-breaker, reliability, fault-tolerance]
created: 2026-03-26
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

#### For References (300 - Reference/):

```markdown
---
tags: [circuit-breaker, pattern]
created: 2026-03-26
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

Use Write tool to create file.

### Step 9: Report Success

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

### Atomicity Check

Ensure note covers single concept:

```bash
# Count main sections
SECTIONS=$(grep -c "^## " "content.md")

if [ $SECTIONS -gt 4 ]; then
  echo "⚠️  Multiple topics detected ($SECTIONS sections)"
  echo "Consider splitting into separate notes:"
  echo "- Note 1: [First topic]"
  echo "- Note 2: [Second topic]"
fi
```

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

### Empty or Minimal Content

If content is very brief:

```
ℹ️  Content is brief (47 words)

This could work as:
- Note: If it's a focused insight (good!)
- Placeholder: Fill in more detail later

Create now or expand first?
```

## Error Handling

### File Already Exists

```
⚠️  File already exists: "200 - Notes/Circuit breakers prevent cascading failures.md"

Options:
A) Choose different name
B) Merge with existing (manual)
C) Overwrite (dangerous!)
D) Open existing for editing
```

### Invalid Destination

```
❌ Destination doesn't exist: "300 - Reference/New-Category/"

Options:
A) Create directory
B) Choose existing directory
C) Cancel
```

### MOC Doesn't Exist

```
⚠️  MOC doesn't exist: "Reliability Patterns MOC"

Options:
A) Create MOC now
B) Skip this MOC
C) Choose different MOC
```

### No Content Provided

```
ℹ️  No content provided

I'll create a placeholder file with proper structure.
You can fill in the content later in Obsidian.

Proceed?
```

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

- **lib/content-analyzer.md** - Classify type, extract topics, suggest title
- **lib/moc-matcher.md** - Suggest relevant MOCs
- **lib/vault-scanner.md** - Find related content
- **lib/link-parser.md** - Add links properly
- **lib/frontmatter.md** - Create proper metadata

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
