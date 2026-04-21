---
name: create-project
description: This skill should be used when the user asks to "create a project", "new project", "start a project", "add a project", or wants to set up a new project directory in the projects/ folder. Provides guided project creation with README.md, log.md, decisions.md, and projects index updates.
version: 0.2.0
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob, AskUserQuestion]
---

# Create Project Skill

Guided creation of a project directory in `projects/` with README.md (hub), log.md (work log), and decisions.md (key decisions), plus projects index updates.

## Purpose

Help create new project directories with correct structure, status tracking, and connections to the vault. Projects are temporal, action-oriented work containers that live in `projects/<kebab-case-name>/` with multiple files for different concerns.

## When to Use

Invoke this skill when:

- User explicitly runs `/create-project`
- User asks to create, start, or add a new project
- User mentions tracking a new piece of work
- User wants to set up a project hub

## Workflow Overview

1. **Gather project details** - Name, goal, due date, area
2. **Define success criteria** - Interactive checklist building
3. **Identify first actions** - Next steps to get started
4. **Create project directory** - Write README.md, log.md, decisions.md
5. **Update projects index** - Add to projects/_projects-index.md

## Process Flow

### Step 1: Gather Project Details

Ask user for core project information:

```
Let me help you create a new project.

What's the project name?
> [User provides name]

What's the goal? (One sentence describing what "done" looks like)
> [User provides goal]

When is it due? (YYYY-MM-DD or leave blank for no deadline)
> [User provides date]

What area does this relate to? (e.g., Infrastructure, SRE, Professional Development)
> [User provides area]
```

Use **AskUserQuestion** tool for each prompt.

**Derive the kebab-case directory name from the project name:**

- "Load Testing Framework" becomes `load-testing-framework`
- "Q2 SRE Hiring" becomes `q2-sre-hiring`

### Step 2: Define Success Criteria

Guide the user through defining what "done" looks like:

```
Let's define success criteria. What needs to be true for this project to be complete?

Enter criteria one at a time (empty line to finish):
> [User enters criteria]
```

If user provides fewer than 2 criteria, suggest common ones based on the area:

```
Consider adding:
- [ ] Work completed and tested
- [ ] Documentation updated
- [ ] Stakeholders informed
- [ ] Lessons learned captured
```

### Step 3: Identify Next Actions

Ask for immediate next steps:

```
What are the first 1-3 actions to get this started?
> [User enters actions]
```

The first action becomes the `next_action` frontmatter field.

### Step 4: Generate Tags

Auto-generate tags from the project name, area, and goal:

```
Suggested tags: [load-testing, infrastructure, performance]

Would you like to:
A) Accept these tags
B) Edit tag list
```

### Step 5: Create Project Directory

Create the directory and all three files:

```bash
mkdir -p projects/load-testing-framework
```

#### File 1: README.md (Project Hub)

```markdown
---
type: project
status: active
area: Infrastructure
due_date: 2026-06-30
next_action: Set up k6 test harness
tags: [load-testing, infrastructure, performance]
created: 2026-04-17
---

# Load Testing Framework

## Goal

Build a reusable load testing framework using k6 for all critical API endpoints.

## Success Criteria

- [ ] k6 test harness configured and running
- [ ] Tests covering top 10 API endpoints
- [ ] CI integration for automated performance regression detection
- [ ] Documentation for team onboarding

## Next Actions

- [ ] Set up k6 test harness
- [ ] Identify top 10 endpoints by traffic volume
- [ ] Draft test scenarios for checkout flow

## Resources

<!-- Links to wiki articles, raw sources, external docs -->

## Lessons Learned

<!-- Populated on completion -->
```

#### File 2: log.md (Work Log)

```markdown
# Load Testing Framework - Log

Work log for the project. Newest entries at the top.

## 2026-04-17

- Project created
- Goal: Build a reusable load testing framework using k6 for all critical API endpoints
- First action: Set up k6 test harness
```

#### File 3: decisions.md (Key Decisions)

```markdown
# Load Testing Framework - Decisions

Key decisions made during this project. Record the context, options considered, and rationale.

## Template

<!--
### [Decision Title]
**Date:** YYYY-MM-DD
**Status:** proposed | accepted | superseded
**Context:** Why this decision was needed
**Options considered:**
1. Option A - pros/cons
2. Option B - pros/cons
**Decision:** What was chosen and why
-->

*No decisions recorded yet.*
```

Use the Write tool to create all three files.

### Step 6: Update Projects Index

Read `projects/_projects-index.md` and add the new project under the Active section.

```bash
# Check if projects index exists
ls projects/_projects-index.md 2>/dev/null
```

If the index exists, use Edit to add the new project:

```markdown
- [[load-testing-framework/README|Load Testing Framework]] - due 2026-06-30 - Set up k6 test harness
```

If the index does not exist, create it:

```markdown
---
title: Projects Index
type: index
last_updated: 2026-04-17
---

# Projects Index

## Active

- [[load-testing-framework/README|Load Testing Framework]] - due 2026-06-30 - Set up k6 test harness

## On Hold

## Completed

## Archived
```

### Step 7: Report Success

```
Project created successfully!

Created: projects/load-testing-framework/
  - README.md (project hub)
  - log.md (work log)
  - decisions.md (decision record)
Updated: projects/_projects-index.md

Next steps:
- Work on first action: Set up k6 test harness
- Record decisions in decisions.md as they come up
- Update log.md with progress entries
- Run /archive-project when complete
```

## Project Directory Structure

The canonical project structure:

```
projects/
  _projects-index.md          # Index of all projects
  load-testing-framework/
    README.md                  # Hub with frontmatter, goal, criteria, actions
    log.md                     # Chronological work log
    decisions.md               # Key decisions with context and rationale
```

## README.md Template

```markdown
---
type: project
status: active          # active | blocked | on-hold | complete
area: [area]
due_date: YYYY-MM-DD
next_action: [first thing to do]
tags: []
created: YYYY-MM-DD
---

# [Project Name]

## Goal

[One sentence: what does "done" look like?]

## Success Criteria

- [ ] [Measurable outcome 1]
- [ ] [Measurable outcome 2]

## Next Actions

- [ ] [Immediate next step]

## Resources

<!-- Links to wiki articles, raw sources, external docs -->

## Lessons Learned

<!-- Populated on completion -->
```

## log.md Template

```markdown
# [Project Name] - Log

Work log for the project. Newest entries at the top.

## YYYY-MM-DD

- Project created
- Goal: [goal]
- First action: [next_action]
```

## decisions.md Template

```markdown
# [Project Name] - Decisions

Key decisions made during this project. Record the context, options considered, and rationale.

## Template

<!--
### [Decision Title]
**Date:** YYYY-MM-DD
**Status:** proposed | accepted | superseded
**Context:** Why this decision was needed
**Options considered:**
1. Option A - pros/cons
2. Option B - pros/cons
**Decision:** What was chosen and why
-->

*No decisions recorded yet.*
```

## Error Handling

### Directory Already Exists

```
Directory "projects/load-testing-framework/" already exists.

Options:
A) Choose a different name
B) Open existing project
C) Cancel
```

### Missing projects/ Directory

```bash
mkdir -p projects
```

Create the directory silently and continue.

### No Due Date Provided

Set `due_date: ""` in frontmatter and note it in the output:

```
No due date set. You can add one later in the README.md frontmatter.
```

### Projects Index Not Found

Create it from scratch with the new project as the first entry.

## Special Cases

### Quick Project Creation

If user provides all details in one message (e.g., "create a project called Load Testing Framework for building k6 tests, due June 30"), skip the interactive prompts and create directly, then confirm.

### Project from Raw Source

If user references a raw/ file:

1. Read the raw file
2. Extract goal and context
3. Pre-fill project details
4. Create project with source linked in Resources

## Best Practices

1. **Kebab-case directory names always** - `load-testing-framework`, not `Load Testing Framework`
2. **One goal per project** - If multiple goals, suggest splitting into separate projects
3. **Concrete success criteria** - Avoid vague items; make them checkable
4. **Always set a first action** - Projects without next actions stall
5. **Start the log immediately** - First entry records creation context
6. **Record decisions early** - Even small decisions matter in retrospect
7. **Update the projects index** - Always keep discovery paths current
8. **Use Resources for links** - Connect to wiki articles and raw sources

## Related Skills

- **/archive-project** - Complete and archive a project
- **/classify-inbox** - Process raw/ files (may become projects)
- **/create-note** - Create wiki articles from project work

## Summary

The create-project skill provides guided project directory creation with README.md (hub), log.md (work log), and decisions.md (decision record) in `projects/<kebab-case-name>/`. Updates `projects/_projects-index.md` to keep the project discoverable. Ensures new projects are properly structured and integrated from creation.
