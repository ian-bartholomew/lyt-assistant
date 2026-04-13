---
name: create-project
description: This skill should be used when the user asks to "create a project", "new project", "start a project", "add a project", or wants to set up a new project hub note in the 150 - Projects/ folder. Provides guided project creation with proper frontmatter, structure, and MOC linking.
version: 0.2.0
allowed-tools: [Bash, Edit, AskUserQuestion]
---

# Create Project Skill

Guided creation of a project hub note in `150 - Projects/` with proper frontmatter, structure, success criteria, and MOC associations.

For advanced Obsidian markdown syntax (callouts, embeds, block references), follow the `obsidian:obsidian-markdown` skill.

## Purpose

Help create new project hub notes with correct structure, status tracking, and connections to the vault following LYT principles. Projects are temporal, action-oriented work containers that produce knowledge artifacts (Notes and Reference).

## When to Use

Invoke this skill when:

- User explicitly runs `/create-project`
- User asks to create, start, or add a new project
- User mentions tracking a new piece of work
- User wants to set up a project hub

## Workflow Overview

1. **Pre-flight check** - Verify Obsidian is running
2. **Gather project details** - Name, goal, due date, area
3. **Suggest MOC links** - Match to existing MOCs
4. **Define success criteria** - Interactive checklist building
5. **Identify first actions** - Next steps to get started
6. **Create project file** - Write with proper frontmatter and structure
7. **Update Projects MOC** - Add project to the active list

## Libraries

- **lib/obsidian-operations.md** - All CLI-based vault operations
- **lib/analysis.md** - Content classification, topic extraction, MOC matching

## Process Flow

### Step 1: Pre-flight Check

Before any vault operations, verify Obsidian is running:

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

Use **AskUserQuestion** to get their choice. Do not proceed until the pre-flight check passes.

### Step 2: Gather Project Details

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

### Step 3: Suggest MOC Links

Scan existing MOCs and suggest relevant ones based on the area and goal:

```bash
# List all MOCs
obsidian files folder="100 - MOCs" ext=md
```

Read relevant MOCs to analyze content:

```bash
obsidian read file="MOC Name"
```

Use **lib/analysis.md** MOC matching algorithm to calculate confidence scores based on:

- Keyword matches (weight: 2x)
- Title matches (weight: 3x)
- Link overlap (weight: 1x)

Present suggestions:

```
Suggested MOCs for this project:
  - [[Infrastructure & Architecture MOC]] (high confidence) — keyword match
  - [[SRE Concepts MOC]] (medium confidence) — related topic

Would you like to:
A) Accept these MOCs
B) Edit MOC list
C) Skip MOC linking
```

### Step 4: Define Success Criteria

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

### Step 5: Identify Next Actions

Ask for immediate next steps:

```
What are the first 1-3 actions to get this started?
> [User enters actions]
```

The first action becomes the `next_action` frontmatter field.

### Step 6: Create Project File

Create the project hub note in `150 - Projects/`:

```bash
# Create file with initial content
obsidian create path="150 - Projects/[Project-Name].md" content="# [Project Name]\n\n## Goal\n\n[Goal from Step 2]\n\n## Success Criteria\n\n[Criteria from Step 4]\n\n## Next Actions\n\n[Actions from Step 5]\n\n## Log\n\n- 2026-04-13 - Project created\n\n## Notes\n\n\n\n## Resources\n<!-- Links to relevant Notes (200) and Reference (300) files -->\n\n\n## Lessons Learned\n<!-- Populated on completion -->" silent
```

Set all frontmatter properties:

```bash
obsidian property:set name="type" value="project" file="[Project-Name]"
obsidian property:set name="status" value="active" file="[Project-Name]"
obsidian property:set name="area" value="[area from Step 2]" file="[Project-Name]"
obsidian property:set name="due_date" value="[date from Step 2]" type=date file="[Project-Name]"
obsidian property:set name="next_action" value="[first action from Step 5]" file="[Project-Name]"
obsidian property:set name="tags" value="[auto-generated from goal and area]" type=list file="[Project-Name]"
obsidian property:set name="created" value="2026-04-13" type=date file="[Project-Name]"
```

If MOCs were selected in Step 3, set the lyt_related_mocs property:

```bash
obsidian property:set name="lyt_related_mocs" value="[[MOC 1]],[[MOC 2]]" type=list file="[Project-Name]"
```

### Step 7: Update Projects MOC

Read the current Projects MOC:

```bash
obsidian read file="Projects MOC"
```

Use the Edit tool to add the new project to the `## Active` section:

```markdown
- [[Project-Name]] — due YYYY-MM-DD — [next_action]
```

If the Projects MOC doesn't have an Active section, use Edit tool to add it following the Projects MOC template structure.

### Step 8: Report Success

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

### Obsidian Not Running

If pre-flight check fails:

```
Obsidian doesn't appear to be running. This plugin requires an open Obsidian vault.

Options:
A) Open Obsidian and retry
B) Cancel
```

### File Already Exists

Check before creating:

```bash
obsidian file file="[Project-Name]"
```

If the file exists:

```
  File "150 - Projects/[Name].md" already exists

Options:
A) Choose a different name
B) Open existing project
C) Cancel
```

### No Due Date Provided

If user leaves due date blank, omit the `due_date` property and note it in the output:

```
  No due date set. You can add one later in the frontmatter.
```

### Projects MOC Not Found

If `obsidian read file="Projects MOC"` fails, the Projects MOC doesn't exist. Create it using the canonical template:

```bash
obsidian create path="100 - MOCs/Projects MOC.md" content="# Projects MOC\n\n## Active\n\n- [[Project-Name]] — due YYYY-MM-DD — [next_action]\n\n## Blocked\n\n\n## On Hold\n\n\n## Complete\n\n" silent
```

Then set properties:

```bash
obsidian property:set name="type" value="moc" file="Projects MOC"
obsidian property:set name="created" value="2026-04-13" type=date file="Projects MOC"
```

## Special Cases

### Quick Project Creation

If user provides all details in one message (e.g., "create a project called X for Y due Z"), skip the interactive prompts and create directly, then confirm.

### Project from Inbox Item

If user references an inbox item:

1. Read the inbox file:

   ```bash
   obsidian read file="Inbox-Item-Name"
   ```

2. Extract goal and context from content
3. Pre-fill project details
4. Offer to move/delete the inbox item after creation:

   ```bash
   obsidian delete file="Inbox-Item-Name"
   ```

## Best Practices

1. **Keep project names short** - Use kebab-case or title case for filenames
2. **One goal per project** - If multiple goals, suggest splitting into separate projects
3. **Concrete success criteria** - Avoid vague items; make them checkable
4. **Always set a first action** - Projects without next actions stall
5. **Link to MOCs** - Keeps projects connected to the knowledge graph
6. **Start the log** - First entry is always "Project created"
7. **Update Projects MOC** - Always keep the index current
8. **Use CLI for all operations** - No direct shell commands (`mkdir`, `cat`, `find`)

## Related Skills

- **/archive-project** - Complete and archive a project
- **/classify-inbox** - Process inbox items (may become projects)
- **/create-note** - Create knowledge artifacts from project work
- **/check-moc-health** - Verify Projects MOC after changes

## Summary

The create-project skill provides guided project hub creation with proper structure, status tracking, MOC linking, and Projects MOC updates following LYT principles. Uses Obsidian CLI for all vault operations. Ensures new projects are properly integrated into the vault from creation.
