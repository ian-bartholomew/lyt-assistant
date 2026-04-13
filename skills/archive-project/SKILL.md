---
name: archive-project
description: This skill should be used when the user asks to "archive a project", "complete a project", "finish a project", "close a project", or wants to move a completed project from 150 - Projects/ to 400 - Archive/Projects/. Handles status updates, knowledge extraction, MOC updates, and archival.
version: 1.0.0
allowed-tools: [Bash, Edit, AskUserQuestion]
---

# Archive Project Skill

Complete and archive a project by updating its status, extracting knowledge artifacts, moving it to archive, and updating the Projects MOC.

For advanced Obsidian markdown syntax (callouts, embeds, block references), follow the `obsidian:obsidian-markdown` skill.

## Purpose

Provide a structured workflow for completing projects that ensures no knowledge is lost. Projects produce insights (Notes) and documentation (Reference) — this skill makes sure those artifacts are captured before the project hub moves to archive.

## When to Use

Invoke this skill when:

- User explicitly runs `/archive-project`
- User says a project is done, complete, or finished
- User wants to close out or archive a project
- User asks to move a project to archive

## Workflow Overview

1. **Pre-flight check** - Verify Obsidian is running
2. **Select project** - Identify which project to archive
3. **Review completion** - Check success criteria status
4. **Update status frontmatter** - Set status to `complete`
5. **Extract knowledge artifacts** - Identify Notes and Reference to create
6. **Capture lessons learned** - Fill in the Lessons Learned section
7. **Move to archive** - Move hub note to `400 - Archive/Projects/`
8. **Update Projects MOC** - Move from Active to Recently Completed
9. **Report summary** - Confirm what was done

## Process Flow

### Step 0: Pre-flight Check

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

Use **AskUserQuestion** to get their choice. Do not proceed with vault operations until the pre-flight check passes.

### Step 1: Select Project

List active projects and let user choose:

```bash
# List all projects in 150 - Projects/
obsidian files folder="150 - Projects" ext=md
```

Present list:

```
Which project would you like to archive?

1) FooBar-Project (due 2026-04-30) — active
2) New-Alerting-System-Runbook (due 2026-03-31) — active
3) Performance-Reviews-Q1 (due 2026-03-31) — active
4) JFrog Artifactory — on-hold

Select (1-4):
```

If user already specified a project name, skip this step.

### Step 2: Review Completion Status

Read the project file and check success criteria:

```bash
obsidian read file="Project-Name"
```

Present status:

```
Project: [Project Name]

Success Criteria Status:
  [x] Project scope and requirements defined
  [x] All deliverables identified
  [ ] Work completed and tested          <-- INCOMPLETE
  [x] Project reviewed and approved
  [ ] Lessons learned documented          <-- INCOMPLETE

2 of 5 criteria incomplete.
```

If criteria are incomplete, ask:

```
Some success criteria are incomplete. Would you like to:
A) Archive anyway (mark incomplete items as won't-do)
B) Update criteria status first
C) Cancel — keep working on the project
```

Use **AskUserQuestion** for this prompt.

### Step 3: Update Status Frontmatter

Update the project's frontmatter properties using Obsidian CLI:

```bash
# Set status to complete
obsidian property:set name="status" value="complete" file="Project-Name"

# Add completion date (use today's date)
obsidian property:set name="completed_date" value="2026-04-13" type=date file="Project-Name"

# Remove next_action (no more actions for completed projects)
obsidian property:remove name="next_action" file="Project-Name"
```

The `type`, `area`, `due_date`, `tags`, `lyt_related_mocs`, and `created` properties remain unchanged.

### Step 4: Extract Knowledge Artifacts

This is the critical step. Review the project's Notes, Log, and Resources sections for knowledge worth preserving.

```
Let's check for knowledge artifacts to extract before archiving.

Reviewing project content for:
- Insights or concepts → should become Notes (200)
- Configs, runbooks, or docs → should become Reference (300)
```

#### 4a. Scan Project Content

Read the project file content (from Step 2) and analyze:

- **Log entries** - Any entries that capture reusable insights?
- **Notes section** - Any content that should be a standalone note?
- **Resources section** - Are all referenced files already in Notes/Reference?
- **Lessons Learned** - These often become great Notes (200)

Use the classification logic from **lib/analysis.md** to identify:

- Content with first-person synthesis → Note candidates
- Content with code, configs, or how-to instructions → Reference candidates

#### 4b. Present Extraction Suggestions

```
Knowledge Extraction Suggestions:

  Notes (200) — insights to preserve:
  1. "Phased migrations reduce blast radius" (from Log entry 2026-03-30)
  2. [No more suggestions]

  Reference (300) — docs to preserve:
  1. Runbook content could become "300 - Reference/Runbooks/[name].md"
  2. [No more suggestions]

Would you like to:
A) Create suggested artifacts now (uses /create-note for each)
B) Skip — all knowledge is already captured
C) Add your own artifacts to extract
```

#### 4c. Create Artifacts

For each approved artifact:

- Use the create-note workflow (from the create-note skill) to create properly structured files
- Link back to the archived project for provenance
- Add to relevant MOCs using **lib/analysis.md** MOC matching

### Step 5: Capture Lessons Learned

If the Lessons Learned section is empty, prompt the user:

```
The Lessons Learned section is empty. This is valuable for future projects.

What went well?
> [User input]

What would you do differently?
> [User input]

Any surprises or unexpected challenges?
> [User input]
```

Update the project file's Lessons Learned section using the Edit tool:

```markdown
## Lessons Learned

**What went well:**
- [User's input]

**What to do differently:**
- [User's input]

**Surprises:**
- [User's input]
```

If the section is already filled, skip this step.

### Step 6: Move to Archive

Move the project hub note to archive:

```bash
# Move the project hub note (creates directory if needed)
obsidian move file="Project-Name" to="400 - Archive/Projects/"
```

Verify the move:

```bash
# Confirm new location
obsidian file file="Project-Name"
```

The output should show the file is now in `400 - Archive/Projects/`.

### Step 7: Update Projects MOC

Read and update the Projects MOC (`100 - MOCs/Projects MOC.md`):

```bash
# Read the MOC
obsidian read file="Projects MOC"
```

1. **Remove** the project from its current status section (Active, On Hold, or Blocked)
2. **Add** the project to the `## Recently Completed` section with completion date

Use the Edit tool:

```markdown
## Recently Completed

- [[Project-Name]] — completed 2026-04-13
```

### Step 8: Report Summary

```
Project archived successfully!

  Archived: 150 - Projects/[name].md → 400 - Archive/Projects/[name].md
  Status: complete (completed 2026-04-13)
  Knowledge artifacts created: [count]
  Lessons learned: captured
  Projects MOC: updated

The project hub is now in archive. Knowledge artifacts remain in:
- Notes (200): [list any created]
- Reference (300): [list any created]
```

## Status Transition Options

This skill also handles non-archival status updates when invoked. If the user wants to change status without archiving:

```
What status change do you need?

A) Complete and archive (full workflow)
B) Mark as blocked — update status only
C) Put on hold — update status only
D) Reactivate — move back to active
```

### For Blocked/On-Hold

Only update frontmatter and Projects MOC:

```bash
# Update status
obsidian property:set name="status" value="blocked" file="Project-Name"
# or
obsidian property:set name="status" value="on-hold" file="Project-Name"
```

Read and edit the Projects MOC to move the project to the appropriate section.

### For Reactivate

If project is in `400 - Archive/Projects/`:

```bash
# Move back to active projects
obsidian move file="Project-Name" to="150 - Projects/"

# Update status to active
obsidian property:set name="status" value="active" file="Project-Name"

# Remove completed_date if present
obsidian property:remove name="completed_date" file="Project-Name"
```

Read and edit the Projects MOC to move the project back to the Active section.

## Error Handling

### Obsidian Not Running

If the pre-flight check fails:

```
Obsidian doesn't appear to be running. This plugin requires an open Obsidian vault.

Options:
A) Open Obsidian and retry
B) Cancel
```

### Project Not Found

```bash
# Search for project
obsidian file file="Project-Name"
```

If not found in `150 - Projects/`:

```
  Project "[name]" not found in 150 - Projects/

Searching archive...
```

```bash
# Check archive
obsidian files folder="400 - Archive/Projects" ext=md
```

[If found in archive]: This project is already archived at 400 - Archive/Projects/[name].md
[If not found anywhere]: No project with that name exists. Use /create-project to create one.

### Projects MOC Missing or Malformed

Check if Projects MOC exists:

```bash
obsidian file file="Projects MOC"
```

If the Projects MOC doesn't exist or doesn't have the expected sections, use the Edit tool to create/fix it before updating.

Expected sections:

- `## Active`
- `## On Hold`
- `## Blocked`
- `## Recently Completed`

### File Conflict in Archive

If `obsidian move` reports file already exists:

```
  File already exists in archive: 400 - Archive/Projects/[name].md

Options:
A) Rename to [name] (2).md
B) Overwrite existing (use with caution)
C) Cancel
```

Use **AskUserQuestion** to get their choice.

## Best Practices

1. **Always run pre-flight check** before any vault operation
2. **Always check success criteria** - Don't archive incomplete projects without acknowledgment
3. **Extract knowledge first** - The whole point of projects is to produce lasting knowledge
4. **Capture lessons learned** - Even brief notes are valuable for future projects
5. **Update the MOC** - Keep the index accurate
6. **Add completion date** - Useful for tracking project duration
7. **Clear next_action** - Completed projects have no next action
8. **Verify the move** - Confirm the file landed in archive using `obsidian file`
9. **Link artifacts to project** - Provenance helps trace where knowledge came from
10. **Use CLI for all operations** - Never fall back to shell commands mid-workflow

## Integration with Libraries

This skill uses shared libraries:

- **lib/obsidian-operations.md** - All vault I/O operations using Obsidian CLI
- **lib/analysis.md** - Content classification, topic extraction, MOC matching for artifact extraction

## Related Skills

- **/create-project** - Create new project hubs
- **/create-note** - Create knowledge artifacts during extraction
- **/classify-inbox** - Process inbox items that may relate to projects
- **/check-moc-health** - Verify Projects MOC after archival

## Summary

The archive-project skill provides a structured workflow for completing projects that ensures knowledge is preserved. It handles status updates, knowledge extraction, lessons learned capture, archival, and MOC updates — making sure nothing valuable is lost when a project finishes. All operations use the Obsidian CLI for safe, reliable vault manipulation.
