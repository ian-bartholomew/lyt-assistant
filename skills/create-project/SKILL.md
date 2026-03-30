---
name: create-project
description: This skill should be used when the user asks to "create a project", "new project", "start a project", "add a project", or wants to set up a new project hub note in the 150 - Projects/ folder. Provides guided project creation with proper frontmatter, structure, and MOC linking.
version: 0.1.0
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob, AskUserQuestion]
---

# Create Project Skill

Guided creation of a project hub note in `150 - Projects/` with proper frontmatter, structure, success criteria, and MOC associations.

## Purpose

Help create new project hub notes with correct structure, status tracking, and connections to the vault following LYT principles. Projects are temporal, action-oriented work containers that produce knowledge artifacts (Notes and Reference).

## When to Use

Invoke this skill when:

- User explicitly runs `/create-project`
- User asks to create, start, or add a new project
- User mentions tracking a new piece of work
- User wants to set up a project hub

## Workflow Overview

1. **Gather project details** - Name, goal, due date, area
2. **Suggest MOC links** - Match to existing MOCs
3. **Define success criteria** - Interactive checklist building
4. **Identify first actions** - Next steps to get started
5. **Create project file** - Write with proper frontmatter and structure
6. **Update Projects MOC** - Add project to the active list

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

### Step 2: Suggest MOC Links

Scan existing MOCs and suggest relevant ones based on the area and goal:

```bash
# List all MOCs
find "100 - MOCs" -name "*.md" -not -name "Home.md" -not -name "Projects MOC.md"
```

Present suggestions:

```
Suggested MOCs for this project:
  - [[Infrastructure & Architecture MOC]] (high confidence)
  - [[SRE Concepts MOC]] (medium confidence)

Would you like to:
A) Accept these MOCs
B) Edit MOC list
C) Skip MOC linking
```

### Step 3: Define Success Criteria

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

### Step 4: Identify Next Actions

Ask for immediate next steps:

```
What are the first 1-3 actions to get this started?
> [User enters actions]
```

The first action becomes the `next_action` frontmatter field.

### Step 5: Create Project File

Write the project hub note to `150 - Projects/`:

```markdown
---
type: project
status: active
area: [area from Step 1]
due_date: [date from Step 1]
next_action: [first action from Step 4]
tags: [auto-generated from goal and area]
lyt_related_mocs:
  - "[[MOC 1]]"
  - "[[MOC 2]]"
created: [today's date]
---

# [Project Name]

## Goal

[Goal from Step 1]

## Success Criteria

- [ ] [Criteria from Step 3]
- [ ] [Criteria from Step 3]

## Next Actions

- [ ] [Actions from Step 4]
- [ ] [Actions from Step 4]

## Log

- [today's date] - Project created

## Notes



## Resources
<!-- Links to relevant Notes (200) and Reference (300) files -->


## Lessons Learned
<!-- Populated on completion -->
```

Use the Write tool to create the file.

### Step 6: Update Projects MOC

Read the current Projects MOC and add the new project under the appropriate status section:

```bash
# Read current Projects MOC
cat "100 - MOCs/Projects MOC.md"
```

Use the Edit tool to add the new project to the `## Active` section:

```markdown
- [[Project-Name]] — due YYYY-MM-DD — [next_action]
```

### Step 7: Report Success

```
Project created successfully!

  Created: 150 - Projects/[Project-Name].md
  Status: active
  Due: [date]
  MOCs: [[MOC 1]], [[MOC 2]]
  Added to [[Projects MOC]]

Next steps:
- Work on first action: [next_action]
- Add resources and links as you go
- Update the Log section with progress
- Run /archive-project when complete
```

## Project Hub Template

The canonical project hub template:

```markdown
---
type: project
status: active          # active | blocked | on-hold | complete
area: [area]
due_date: YYYY-MM-DD
next_action: [first thing to do]
tags: []
lyt_related_mocs:
  - "[[MOC Name]]"
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

## Log

- YYYY-MM-DD - Project created

## Notes



## Resources
<!-- Links to relevant Notes (200) and Reference (300) files -->


## Lessons Learned
<!-- Populated on completion -->
```

## Error Handling

### File Already Exists

```
  File "150 - Projects/[Name].md" already exists

Options:
A) Choose a different name
B) Open existing project
C) Cancel
```

### Missing 150 - Projects/ Directory

```bash
mkdir -p "150 - Projects"
```

Create the directory silently and continue.

### No Due Date Provided

Set `due_date: ""` in frontmatter and note it in the output:

```
  No due date set. You can add one later in the frontmatter.
```

### Projects MOC Not Found

Create it from the template defined in the system, then add the project.

## Special Cases

### Quick Project Creation

If user provides all details in one message (e.g., "create a project called X for Y due Z"), skip the interactive prompts and create directly, then confirm.

### Project from Inbox Item

If user references an inbox item:

1. Read the inbox file
2. Extract goal and context
3. Pre-fill project details
4. Offer to move/delete the inbox item after creation

## Best Practices

1. **Keep project names short** - Use kebab-case or title case for filenames
2. **One goal per project** - If multiple goals, suggest splitting into separate projects
3. **Concrete success criteria** - Avoid vague items; make them checkable
4. **Always set a first action** - Projects without next actions stall
5. **Link to MOCs** - Keeps projects connected to the knowledge graph
6. **Start the log** - First entry is always "Project created"
7. **Update Projects MOC** - Always keep the index current

## Integration with Utilities

This skill uses shared utilities:

- **lib/moc-matcher.md** - Suggest relevant MOCs
- **lib/frontmatter.md** - Create proper metadata
- **lib/vault-scanner.md** - Check for existing projects and related content

## Related Skills

- **/archive-project** - Complete and archive a project
- **/classify-inbox** - Process inbox items (may become projects)
- **/create-note** - Create knowledge artifacts from project work
- **/check-moc-health** - Verify Projects MOC after changes

## Summary

The create-project skill provides guided project hub creation with proper structure, status tracking, MOC linking, and Projects MOC updates following LYT principles. Ensures new projects are properly integrated into the vault from creation.
