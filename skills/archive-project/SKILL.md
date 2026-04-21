---
name: archive-project
description: This skill should be used when the user asks to "archive a project", "complete a project", "finish a project", "close a project", or wants to move a completed project from projects/ to archive/projects/. Handles knowledge extraction into wiki, status updates, index updates, and archival.
version: 0.2.0
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob, AskUserQuestion]
---

# Archive Project Skill

Complete and archive a project by extracting knowledge artifacts into the wiki, updating indexes, and moving the project directory to archive.

## Purpose

Provide a structured workflow for completing projects that ensures no knowledge is lost. Projects produce insights and documentation — this skill compiles those into wiki articles (concepts, guides) before moving the project directory to archive.

## When to Use

Invoke this skill when:

- User explicitly runs `/archive-project`
- User says a project is done, complete, or finished
- User wants to close out or archive a project
- User asks to move a project to archive

## Workflow Overview

1. **Select project** - Identify which project to archive
2. **Review completion** - Check success criteria and README status
3. **Extract knowledge artifacts** - Compile insights into wiki articles
4. **Capture lessons learned** - Record in project log
5. **Move to archive** - Move entire project directory to `archive/projects/`
6. **Update indexes** - Update `projects/_projects-index.md` and `wiki/_log.md`
7. **Report summary** - Confirm what was done

## Process Flow

### Step 1: Select Project

List active projects:

```bash
# List all project directories in projects/
ls -d projects/*/
```

Present list:

```
Which project would you like to archive?

1) projects/alerting-migration/
2) projects/terraform-refactor/
3) projects/slo-dashboard/

Select (1-3):
```

If user already specified a project name, skip this step.

### Step 2: Review Completion Status

Read the project README and log:

```bash
cat "projects/<name>/README.md"
cat "projects/<name>/log.md"
```

Present status:

```
Project: <name>

README Status:
  Status: active
  Success Criteria:
  [x] Requirements defined
  [x] Implementation complete
  [ ] Documentation written          <-- INCOMPLETE
  [x] Reviewed and approved

1 of 4 criteria incomplete.
```

If criteria are incomplete, ask:

```
Some success criteria are incomplete. Would you like to:
A) Archive anyway (mark incomplete items as won't-do)
B) Update criteria status first
C) Cancel — keep working on the project
```

Use **AskUserQuestion** for this prompt.

### Step 3: Extract Knowledge Artifacts

This is the critical step. Review the project directory for knowledge worth preserving as wiki articles.

```
Reviewing project content for compilable knowledge:

Scanning:
- README.md — project overview and decisions
- log.md — chronological work log
- decisions.md — architecture decision records
- Any other .md files in the project directory

Looking for:
- Concepts → wiki/concepts/ articles
- How-to knowledge → wiki/guides/ articles
- Company-specific info → wiki/company/ articles
```

#### 3a. Scan Project Content

Read all markdown files in the project directory and analyze:

- **decisions.md** - ADRs that capture reusable patterns or concepts
- **log.md** - Entries that capture reusable insights
- **README.md** - Overview content worth preserving
- **Other files** - Any supplementary docs

#### 3b. Present Extraction Suggestions

```
Knowledge Extraction Suggestions:

  Concepts (wiki/concepts/):
  1. "circuit-breaker-pattern" — from decisions.md ADR on resilience approach
  2. "error-budget-policy" — from log entry on SLO negotiation

  Guides (wiki/guides/):
  1. "migrating-alerting-to-datadog" — from README and log entries
  2. "terraform-state-migration" — from decisions.md

  Company (wiki/company/):
  1. "alerting-architecture" — from project overview

Would you like to:
A) Create suggested articles now
B) Skip — all knowledge is already captured in wiki
C) Add your own artifacts to extract
```

#### 3c. Create Wiki Articles

For each approved artifact, create a properly structured wiki article:

```yaml
---
title: Circuit Breaker Pattern
domain: [sre, resilience]
maturity: draft
confidence: medium
related:
  - "[[bulkhead-pattern]]"
  - "[[error-budget-policy]]"
last_compiled: 2026-04-17
---
```

- Use kebab-case filenames
- Place in the appropriate wiki subfolder
- Add `related:` links to existing wiki articles
- Set `maturity: draft` for newly extracted articles
- Link back to the archived project for provenance

### Step 4: Capture Lessons Learned

If the project log does not have a lessons learned entry, prompt the user:

```
The project log has no lessons learned entry. This is valuable for future projects.

What went well?
> [User input]

What would you do differently?
> [User input]

Any surprises or unexpected challenges?
> [User input]
```

Append a final entry to `projects/<name>/log.md`:

```markdown
## 2026-04-17 — Project Archived

### Lessons Learned

**What went well:**
- [User's input]

**What to do differently:**
- [User's input]

**Surprises:**
- [User's input]
```

If lessons are already captured, skip this step.

### Step 5: Move to Archive

```bash
# Ensure archive directory exists
mkdir -p "archive/projects"

# Move the entire project directory
mv "projects/<name>" "archive/projects/<name>"
```

Verify the move:

```bash
ls "archive/projects/<name>/README.md"
```

### Step 6: Update Indexes

#### 6a. Update Projects Index

Read and update `projects/_projects-index.md`:

1. **Remove** the project from its current status section (Active, On Hold, or Blocked)
2. **Add** the project to the `## Recently Completed` section with completion date and archive path

Use the Edit tool:

```markdown
## Recently Completed

- ~~<name>~~ — completed 2026-04-17 → `archive/projects/<name>/`
```

#### 6b. Append to Wiki Log

Append an entry to `wiki/_log.md`:

```markdown
## [2026-04-17] archive | Archived project: <name>

- Moved `projects/<name>/` to `archive/projects/<name>/`
- Extracted knowledge artifacts:
  - `wiki/concepts/circuit-breaker-pattern.md` (new)
  - `wiki/guides/migrating-alerting-to-datadog.md` (new)
- Lessons learned captured in project log
```

#### 6c. Update Domain Indexes

For each wiki article created during extraction, ensure it appears in the relevant domain index under `wiki/_indexes/`.

### Step 7: Report Summary

```
Project archived successfully.

  Moved: projects/<name>/ → archive/projects/<name>/
  Files in archive: [count]
  Knowledge artifacts created: [count]
  Lessons learned: captured
  Projects index: updated
  Wiki log: updated

  Wiki articles created:
  - wiki/concepts/circuit-breaker-pattern.md
  - wiki/guides/migrating-alerting-to-datadog.md
  - wiki/company/alerting-architecture.md
```

## Status Transition Options

This skill also handles non-archival status updates when invoked. If the user wants to change status without archiving:

```
What status change do you need?

A) Complete and archive (full workflow)
B) Mark as blocked — update status only
C) Put on hold — update status only
D) Reactivate — move back from archive to active
```

### For Blocked/On-Hold

Only update the project README frontmatter and projects index:

```yaml
status: blocked    # or on-hold
```

Move the project to the appropriate section in `projects/_projects-index.md`.

### For Reactivate

If project is in `archive/projects/<name>/`:

```bash
mv "archive/projects/<name>" "projects/<name>"
```

Update README frontmatter to `status: active` and move in projects index.

## Error Handling

### Project Not Found

```
Project "<name>" not found in projects/

Searching archive...
[If found in archive]: This project is already archived at archive/projects/<name>/
[If not found anywhere]: No project with that name exists. Use /create-project to create one.
```

### Archive Directory Missing

```bash
mkdir -p "archive/projects"
```

Create silently and continue.

### Projects Index Missing or Malformed

If `projects/_projects-index.md` doesn't exist or doesn't have the expected sections, create/fix it before updating.

### Directory Conflict in Archive

```
Directory already exists in archive: archive/projects/<name>/

Options:
A) Rename to <name>-2
B) Overwrite existing
C) Cancel
```

## Best Practices

1. **Always check success criteria** - Don't archive incomplete projects without acknowledgment
2. **Extract knowledge first** - The whole point of projects is to produce lasting wiki knowledge
3. **Capture lessons learned** - Even brief notes are valuable for future projects
4. **Update both indexes** - Projects index and wiki log must stay accurate
5. **Add completion date** - Useful for tracking project duration
6. **Use kebab-case** - All wiki article filenames use kebab-case
7. **Verify the move** - Confirm the directory landed in archive
8. **Link artifacts to project** - Provenance helps trace where knowledge came from
9. **Set maturity: draft** - Newly extracted articles need review before promotion

## Related Skills

- **/create-project** - Create new project hubs
- **/create-note** - Create wiki articles during extraction
- **/ingest** - Process raw items that may relate to projects
- **/lint** - Verify wiki health after archival

## Summary

The archive-project skill provides a structured workflow for completing projects that ensures knowledge is compiled into the wiki before archival. It handles knowledge extraction, lessons learned capture, directory archival, and index updates — making sure nothing valuable is lost when a project finishes.
