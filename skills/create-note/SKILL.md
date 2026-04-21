---
name: create-note
description: This skill should be used when the user asks to "create a note", "create new note", "make a note", "write a note", "add a note", "create an article", "write an article", or wants guided wiki article creation. Provides interactive creation with proper structure, classification, domain tagging, and index updates.
version: 0.2.0
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob, AskUserQuestion]
---

# Create Note Skill

Guided creation of wiki articles in the appropriate `wiki/` subfolder with proper frontmatter, domain tags, related links, index updates, and compile log entries.

## Purpose

Help create new wiki articles with correct structure, classification, linking, and organization. Articles are LLM-compiled knowledge organized by type: concepts (what is X?), guides (how do I X?), company (how does our org do X?), and learning (what did I learn from X?).

## When to Use

Invoke this skill when:

- User explicitly runs `/create-note`
- User asks to create, write, or add a new note or article
- User mentions making a new file for the vault
- User wants help structuring new content

## Workflow Overview

1. **Determine source** - Existing content or start from scratch
2. **Analyze content** - Classify type and extract domains
3. **Suggest structure** - Title, destination, related links
4. **Review and edit** - Interactive refinement
5. **Create file** - Write with proper frontmatter and links
6. **Update index and log** - Maintain wiki/_indexes/ and wiki/_log.md

## Process Flow

### Step 1: Determine Content Source

Ask user about starting point:

```
Let me help you create a wiki article.

Do you have content already, or should I help you structure something new?
A) I have content in raw/
B) I have content elsewhere
C) Start from scratch with a topic
```

Handle each option:

#### Option A: Content in raw/

```bash
# Scan raw/ for recent files
find raw -type f -name "*.md" -maxdepth 2 | head -20
```

Present list and read selected file for analysis.

#### Option B: Content Elsewhere

Ask for file path and read content.

#### Option C: Start from Scratch

Ask for topic and guide creation:

```
What topic or concept would you like to write about?

Examples:
- "Circuit breakers prevent cascading failures"
- "How to configure Terraform remote state"
- "Our team's deployment pipeline"
- "Lessons from the Q1 incident review"
```

### Step 2: Analyze Content

Determine article type by examining the content:

```
Analyzing content...

Content Analysis:
- Type: concept
- Domains: sre, resilience
- Maturity: draft
- Confidence: medium
- Reasoning: Explains what circuit breakers are and why they matter
```

### Step 3: Classify Article Type

Classify into one of four wiki categories:

| Type | Question it answers | Destination |
|------|-------------------|-------------|
| **concept** | What is X? | `wiki/concepts/` |
| **guide** | How do I X? | `wiki/guides/` |
| **company** | How does our org do X? | `wiki/company/` |
| **learning** | What did I learn from X? | `wiki/learning/` |

**Concept indicators:**

- Defines or explains a term, pattern, or principle
- General knowledge not specific to one org
- Assertion-style insight

**Guide indicators:**

- Step-by-step instructions
- How-to content
- Commands, configuration, procedures

**Company indicators:**

- References internal systems, teams, or processes
- Architecture decisions specific to the org
- Onboarding or org-specific runbooks

**Learning indicators:**

- Post-mortem reflections
- Conference or course takeaways
- Personal lessons from experience

**When ambiguous:**

```
This content could be:
- concept: It explains a general principle
- guide: It contains step-by-step instructions

Help me decide:
1. Is this general knowledge or specific instructions?
2. Would someone outside your org find this useful as-is?
3. Is the core value "understanding" or "doing"?
```

### Step 4: Suggest Title and Filename

Generate a clear, descriptive title and its kebab-case filename:

```
Suggested Title: "Circuit Breaker Pattern"
Filename: circuit-breaker-pattern.md
Destination: wiki/concepts/circuit-breaker-pattern.md

Would you like to:
A) Use this title
B) Edit title
C) Keep original
```

**Filename rules:**

- Always kebab-case (lowercase, hyphens)
- No spaces, no special characters
- Concise but descriptive
- Example: `circuit-breaker-pattern.md`, `terraform-remote-state-setup.md`

### Step 5: Assign Domains

Suggest domain tags based on content:

```
Suggested Domains: [sre, resilience]

Common domains: sre, infrastructure, terraform, kubernetes, observability,
reliability, networking, security, ci-cd, professional-development, leadership

Would you like to:
A) Accept these domains
B) Edit domain list
```

### Step 6: Suggest Related Links

Search wiki/ for related content:

```bash
# Search for related articles in wiki/
grep -rl "circuit.breaker\|resilience\|fault.tolerance" wiki/ --include="*.md" | head -10
```

Present suggestions using kebab-case wikilinks:

```
Suggested Related Links:
  - [[bulkhead-pattern]]
  - [[graceful-degradation]]
  - [[exponential-backoff]]
```

### Step 7: Interactive Review

Present complete suggestion:

```
Article Summary:

Title: "Circuit Breaker Pattern"
Type: concept
Destination: wiki/concepts/circuit-breaker-pattern.md
Domains: [sre, resilience]
Maturity: draft
Confidence: medium
Related: [[bulkhead-pattern]], [[graceful-degradation]]

Would you like to:
A) Create with these settings (recommended)
B) Edit title
C) Edit destination/type
D) Edit domains
E) Edit related links
F) Cancel
```

### Step 8: Create File

Once approved, create file with proper wiki frontmatter and structure.

#### For Concepts (wiki/concepts/)

```markdown
---
title: Circuit Breaker Pattern
domain: [sre, resilience]
maturity: draft
confidence: medium
sources:
  - "[[raw/clippings/circuit-breaker-article.md]]"
related:
  - "[[bulkhead-pattern]]"
  - "[[graceful-degradation]]"
last_compiled: 2026-04-17
---

# Circuit Breaker Pattern

[Content or placeholder]

## Key Points

- [Main takeaway 1]
- [Main takeaway 2]

## Related

- [[bulkhead-pattern]]
- [[graceful-degradation]]
- [[exponential-backoff]]
```

#### For Guides (wiki/guides/)

```markdown
---
title: Terraform Remote State Setup
domain: [terraform, infrastructure]
maturity: draft
confidence: medium
sources: []
related:
  - "[[terraform-state-locking]]"
last_compiled: 2026-04-17
---

# Terraform Remote State Setup

## Overview

[Brief introduction]

## Prerequisites

- [Requirement 1]

## Steps

1. [Step 1]
2. [Step 2]

## Troubleshooting

[Common issues]

## Related

- [[terraform-state-locking]]
```

#### For Company (wiki/company/)

```markdown
---
title: Deployment Pipeline
domain: [ci-cd, infrastructure]
maturity: draft
confidence: medium
sources: []
related:
  - "[[ci-cd-best-practices]]"
last_compiled: 2026-04-17
---

# Deployment Pipeline

## Overview

[How our org handles this]

## Architecture

[Internal specifics]

## Runbook

[Operational steps]

## Related

- [[ci-cd-best-practices]]
```

#### For Learning (wiki/learning/)

```markdown
---
title: Lessons from Q1 Incident Review
domain: [sre, incidents]
maturity: draft
confidence: high
sources: []
related:
  - "[[incident-response-process]]"
last_compiled: 2026-04-17
---

# Lessons from Q1 Incident Review

## Context

[What happened and when]

## Key Lessons

- [Lesson 1]
- [Lesson 2]

## Action Items

- [What changed as a result]

## Related

- [[incident-response-process]]
```

Use Write tool to create file.

### Step 9: Update Domain Index

After creating the article, update the relevant domain index in `wiki/_indexes/`.

For each domain in the article's `domain` field, update or create the index file:

```bash
# Check if domain index exists
ls wiki/_indexes/sre.md 2>/dev/null
```

If the index exists, use Edit to add the new article under the appropriate section. If not, create it:

```markdown
---
title: SRE Index
type: domain-index
last_updated: 2026-04-17
---

# SRE

## Concepts

- [[circuit-breaker-pattern]] - Circuit Breaker Pattern

## Guides

## Company

## Learning
```

Add the new article under the matching type heading (Concepts, Guides, Company, or Learning).

### Step 10: Append to Compile Log

Append an entry to `wiki/_log.md`:

```markdown
- 2026-04-17 - Created [[circuit-breaker-pattern]] (concept) in wiki/concepts/
```

If `wiki/_log.md` does not exist, create it:

```markdown
---
title: Wiki Compile Log
type: log
---

# Wiki Compile Log

- 2026-04-17 - Created [[circuit-breaker-pattern]] (concept) in wiki/concepts/
```

### Step 11: Report Success

```
Created: wiki/concepts/circuit-breaker-pattern.md
Updated: wiki/_indexes/sre.md
Updated: wiki/_indexes/resilience.md
Logged: wiki/_log.md

Next steps:
- Fill in content if placeholder was used
- Review and refine related links
- Update maturity/confidence as the article evolves
```

## Maturity and Confidence Levels

### Maturity

| Level | Meaning |
|-------|---------|
| `stub` | Placeholder with minimal content |
| `draft` | Initial write-up, needs review |
| `mature` | Well-developed, reviewed, trustworthy |
| `canonical` | Authoritative reference, actively maintained |

New articles default to `draft`. Use `stub` if creating with placeholder content only.

### Confidence

| Level | Meaning |
|-------|---------|
| `low` | Uncertain, needs verification |
| `medium` | Reasonable understanding, may have gaps |
| `high` | Well-understood, verified against sources |

## Special Cases

### Starting from Scratch

If user chooses to start fresh:

1. **Ask for topic**
2. **Determine article type** based on the question the topic answers
3. **Provide template** based on type
4. **User fills in content**
5. **Review and create**

### Existing Content with Poor Structure

```
Content appears unstructured.

Options:
A) Auto-structure (extract title, organize sections)
B) Use as-is with frontmatter only
C) Manually structure (I'll guide you)
```

### Empty or Minimal Content

```
Content is brief (47 words).

This could work as:
- stub: Placeholder to expand later
- draft: If it captures the core idea

Create as stub or draft?
```

### Content That Spans Multiple Types

If content is both a concept explanation and a how-to guide:

```
This content covers both "what" and "how."

Options:
A) Create as concept (focus on understanding)
B) Create as guide (focus on doing)
C) Split into two articles (recommended)
   - wiki/concepts/circuit-breaker-pattern.md
   - wiki/guides/implementing-circuit-breakers.md
```

## Error Handling

### File Already Exists

```
File already exists: wiki/concepts/circuit-breaker-pattern.md

Options:
A) Choose different name
B) Merge with existing (manual)
C) Overwrite (dangerous!)
D) Open existing for editing
```

### Directory Doesn't Exist

```bash
mkdir -p wiki/concepts
```

Create the directory silently and continue.

### Domain Index Doesn't Exist

Create a new domain index file in `wiki/_indexes/` and add the article.

### No Content Provided

```
No content provided.

I'll create a stub file with proper structure.
You can fill in the content later in Obsidian.

Proceed?
```

## Best Practices

1. **One concept per article** - Keep articles atomic and focused
2. **Use descriptive titles** - Clear and searchable
3. **Kebab-case filenames always** - Consistent, URL-friendly
4. **Assign domains, not folders** - Domains are the organizational primitive
5. **Link to sources in raw/** - Maintain provenance
6. **Set realistic maturity** - Don't over-rate initial drafts
7. **Update indexes immediately** - Keep discovery paths current
8. **Log every creation** - wiki/_log.md is the audit trail
9. **Allow iteration** - Easy to edit before creating
10. **Guide next steps** after creation

## Related Skills

- **/classify-inbox** - Process raw/ files into wiki articles
- **/research** - Research and create reference articles
- **/check-moc-health** - Verify indexes after adding articles

## Summary

The create-note skill provides guided wiki article creation with proper classification into concepts/guides/company/learning, kebab-case naming, domain tagging, index updates, and compile logging. Ensures new articles are properly integrated into the wiki from creation.
