---
name: archive-project
description: This skill should be used when the user asks to "archive a project", "complete a project", "finish a project", "close a project", or wants to move a completed project from 150 - Projects/ to 400 - Archive/Projects/. Handles status updates, knowledge extraction, MOC updates, and archival.
version: 0.1.0
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob, AskUserQuestion]
---

# Archive Project Skill

Complete and archive a project by updating its status, extracting knowledge artifacts, moving it to archive, and updating the Projects MOC.

## Purpose

Provide a structured workflow for completing projects that ensures no knowledge is lost. Projects produce insights (Notes) and documentation (Reference) — this skill makes sure those artifacts are captured before the project hub moves to archive.

## When to Use

Invoke this skill when:

- User explicitly runs `/archive-project`
- User says a project is done, complete, or finished
- User wants to close out or archive a project
- User asks to move a project to archive

## Workflow Overview

1. **Select project** - Identify which project to archive
2. **Review completion** - Check success criteria status
3. **Update status frontmatter** - Set status to `complete`
4. **Extract knowledge artifacts** - Identify Notes and Reference to create
5. **Capture lessons learned** - Fill in the Lessons Learned section
6. **Move to archive** - Move hub note to `400 - Archive/Projects/`
7. **Update Projects MOC** - Move from Active to Recently Completed
8. **Report summary** - Confirm what was done

## Process Flow

### Step 1: Select Project

List active projects and let user choose:

```bash
# List all projects in 150 - Projects/
find "150 - Projects" -name "*.md" -type f
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
cat "150 - Projects/[Project-Name].md"
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

Update the project's frontmatter:

```yaml
---
type: project
status: complete              # changed from active
area: [unchanged]
due_date: [unchanged]
next_action: ""               # cleared — no more actions
completed_date: YYYY-MM-DD    # added — today's date
tags: [unchanged]
lyt_related_mocs:
  - "[[MOC 1]]"
created: [unchanged]
---
```

Use the Edit tool to update frontmatter fields.

### Step 4: Extract Knowledge Artifacts

This is the critical step. Review the project's Notes, Log, and Resources sections for knowledge worth preserving.

```
Let's check for knowledge artifacts to extract before archiving.

Reviewing project content for:
- Insights or concepts → should become Notes (200)
- Configs, runbooks, or docs → should become Reference (300)
```

#### 4a. Scan Project Content

Read the project file and analyze:

- **Log entries** - Any entries that capture reusable insights?
- **Notes section** - Any content that should be a standalone note?
- **Resources section** - Are all referenced files already in Notes/Reference?
- **Lessons Learned** - These often become great Notes (200)

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
- Add to relevant MOCs

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

Update the project file's Lessons Learned section:

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

```bash
# Ensure archive directory exists
mkdir -p "400 - Archive/Projects"

# Move the project hub note
mv "150 - Projects/[Project-Name].md" "400 - Archive/Projects/"
```

Verify the move:

```bash
ls "400 - Archive/Projects/[Project-Name].md"
```

### Step 7: Update Projects MOC

Read and update the Projects MOC (`100 - MOCs/Projects MOC.md`):

1. **Remove** the project from its current status section (Active, On Hold, or Blocked)
2. **Add** the project to the `## Recently Completed` section with completion date

Use the Edit tool:

```markdown
## Recently Completed

- [[Project-Name]] — completed 2026-03-30
```

### Step 8: Report Summary

```
Project archived successfully!

  Archived: 150 - Projects/[name].md → 400 - Archive/Projects/[name].md
  Status: complete (completed 2026-03-30)
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

```yaml
status: blocked    # or on-hold
```

Move the project to the appropriate section in Projects MOC.

### For Reactivate

If project is in `400 - Archive/Projects/`:

```bash
mv "400 - Archive/Projects/[name].md" "150 - Projects/"
```

Update frontmatter to `status: active` and move in Projects MOC.

## Error Handling

### Project Not Found

```
  Project "[name]" not found in 150 - Projects/

Searching archive...
[If found in archive]: This project is already archived at 400 - Archive/Projects/[name].md
[If not found anywhere]: No project with that name exists. Use /create-project to create one.
```

### Archive Directory Missing

```bash
mkdir -p "400 - Archive/Projects"
```

Create silently and continue.

### Projects MOC Missing or Malformed

If the Projects MOC doesn't exist or doesn't have the expected sections, create/fix it before updating.

### File Conflict in Archive

```
  File already exists in archive: 400 - Archive/Projects/[name].md

Options:
A) Rename to [name] (2).md
B) Overwrite existing
C) Cancel
```

## Best Practices

1. **Always check success criteria** - Don't archive incomplete projects without acknowledgment
2. **Extract knowledge first** - The whole point of projects is to produce lasting knowledge
3. **Capture lessons learned** - Even brief notes are valuable for future projects
4. **Update the MOC** - Keep the index accurate
5. **Add completion date** - Useful for tracking project duration
6. **Clear next_action** - Completed projects have no next action
7. **Verify the move** - Confirm the file landed in archive
8. **Link artifacts to project** - Provenance helps trace where knowledge came from

## Integration with Utilities

This skill uses shared utilities:

- **lib/frontmatter.md** - Update metadata fields
- **lib/vault-scanner.md** - Find project files and check for artifacts
- **lib/content-analyzer.md** - Analyze project content for extractable knowledge
- **lib/moc-matcher.md** - Suggest MOCs for extracted artifacts

## Related Skills

- **/create-project** - Create new project hubs
- **/create-note** - Create knowledge artifacts during extraction
- **/classify-inbox** - Process inbox items that may relate to projects
- **/check-moc-health** - Verify Projects MOC after archival

## Summary

The archive-project skill provides a structured workflow for completing projects that ensures knowledge is preserved. It handles status updates, knowledge extraction, lessons learned capture, archival, and MOC updates — making sure nothing valuable is lost when a project finishes.
