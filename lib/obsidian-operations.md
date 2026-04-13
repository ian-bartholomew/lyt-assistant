# Obsidian Operations Library

This utility provides instructions for all vault operations using the Obsidian CLI. Requires Obsidian to be running.

All skills should use these CLI commands instead of raw shell commands (`find`, `grep`, `sed`, `mv`, `cat`).

## Pre-flight Check

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

Use **AskUserQuestion** to get their choice. Do not proceed with vault operations until the pre-flight check passes.

## Vault Scanning

### List Files by Folder

```bash
# All vault files
obsidian files

# Inbox files
obsidian files folder="000 - Inbox" ext=md

# MOC files
obsidian files folder="100 - MOCs" ext=md

# Project files
obsidian files folder="150 - Projects" ext=md

# Note files
obsidian files folder="200 - Notes" ext=md

# Reference files
obsidian files folder="300 - Reference" ext=md

# Archive files
obsidian files folder="400 - Archive" ext=md
```

### List Folders

```bash
# All vault folders
obsidian folders

# Reference subfolder structure (for destination suggestions)
obsidian folders folder="300 - Reference"

# Archive structure
obsidian folders folder="400 - Archive"
```

### File Counts

```bash
obsidian files folder="000 - Inbox" ext=md total
obsidian files folder="100 - MOCs" ext=md total
obsidian files folder="200 - Notes" ext=md total
obsidian files folder="300 - Reference" ext=md total
```

### Validate LYT Vault Structure

To confirm the vault follows LYT conventions, check that expected folders exist:

```bash
obsidian folders
```

Verify the output contains: `000 - Inbox`, `100 - MOCs`, `150 - Projects`, `200 - Notes`, `300 - Reference`, `400 - Archive`. If any are missing, warn the user:

```
This doesn't appear to be a complete LYT vault. Missing folders: [list]
```

## File Operations

### Read File Content

```bash
# By name (resolves like a wikilink)
obsidian read file="My Note"

# By exact path
obsidian read path="200 - Notes/My Note.md"
```

### Create File

```bash
# Create with name (goes to vault root by default)
obsidian create name="My Note" content="# My Note\n\nContent here" silent

# Create at specific path
obsidian create path="200 - Notes/My Note.md" content="# My Note\n\nContent here" silent

# Create from template
obsidian create name="My Note" template="Note Template" silent

# Overwrite existing
obsidian create name="My Note" content="..." overwrite silent
```

**Multiline content:** Use `\n` for newlines in `content=` values. For large content blocks, prefer creating with minimal content then using `obsidian append` for the body, or use the `Edit` tool after creation.

### Move File

```bash
# Move to folder
obsidian move file="My Note" to="200 - Notes/"

# Move to specific path (rename + move)
obsidian move file="My Note" to="200 - Notes/New Name.md"
```

### Rename File

```bash
obsidian rename file="My Note" name="Better Title"
```

Obsidian automatically updates all links pointing to the renamed file.

### Append Content

```bash
obsidian append file="My Note" content="\n## Related\n\n- [[Other Note]]"
```

### Prepend Content

```bash
obsidian prepend file="My Note" content="Updated: 2026-04-13\n\n"
```

### Delete File

```bash
# Move to trash (safe)
obsidian delete file="My Note"

# Permanent delete (use with caution)
obsidian delete file="My Note" permanent
```

## Properties (Frontmatter)

The CLI manages YAML frontmatter properties directly. No manual YAML parsing needed.

### Set a Property

```bash
# Text property
obsidian property:set name="status" value="active" file="My Note"

# Date property
obsidian property:set name="created" value="2026-04-13" type=date file="My Note"

# List property (tags, mocs)
obsidian property:set name="tags" value="sre,reliability" type=list file="My Note"

# Checkbox property
obsidian property:set name="reviewed" value="true" type=checkbox file="My Note"
```

### Read a Property

```bash
obsidian property:read name="status" file="My Note"
obsidian property:read name="tags" file="My Note"
obsidian property:read name="mocs" file="My Note"
```

### Remove a Property

```bash
obsidian property:remove name="next_action" file="My Note"
```

### List All Properties

```bash
# All properties for a file
obsidian properties file="My Note"

# All properties for a file in YAML format
obsidian properties file="My Note" format=yaml

# All properties used across the vault
obsidian properties
```

### Common Property Patterns

**Set up a new Note's metadata:**

```bash
obsidian property:set name="tags" value="topic1,topic2" type=list file="My Note"
obsidian property:set name="created" value="2026-04-13" type=date file="My Note"
obsidian property:set name="mocs" value="[[MOC Name]]" type=list file="My Note"
```

**Set up a new Reference's metadata:**

```bash
obsidian property:set name="tags" value="topic1,topic2" type=list file="My Ref"
obsidian property:set name="created" value="2026-04-13" type=date file="My Ref"
obsidian property:set name="type" value="external" file="My Ref"
obsidian property:set name="source" value="https://example.com" file="My Ref"
obsidian property:set name="mocs" value="[[MOC Name]]" type=list file="My Ref"
```

**Set up a new Project's metadata:**

```bash
obsidian property:set name="type" value="project" file="My Project"
obsidian property:set name="status" value="active" file="My Project"
obsidian property:set name="area" value="Infrastructure" file="My Project"
obsidian property:set name="due_date" value="2026-06-01" type=date file="My Project"
obsidian property:set name="next_action" value="Define scope" file="My Project"
obsidian property:set name="tags" value="project-tag" type=list file="My Project"
obsidian property:set name="created" value="2026-04-13" type=date file="My Project"
```

**Complete a Project:**

```bash
obsidian property:set name="status" value="complete" file="My Project"
obsidian property:set name="completed_date" value="2026-04-13" type=date file="My Project"
obsidian property:remove name="next_action" file="My Project"
```

## Links

### Outgoing Links

```bash
# All links from a file
obsidian links file="My Note"

# Link count
obsidian links file="My Note" total
```

### Backlinks (Incoming Links)

```bash
# All files linking to this one
obsidian backlinks file="My Note"

# With counts
obsidian backlinks file="My Note" counts

# Backlink count only
obsidian backlinks file="My Note" total

# As JSON for parsing
obsidian backlinks file="My Note" format=json
```

### Broken Links (Unresolved)

```bash
# All unresolved links in vault
obsidian unresolved

# Count only
obsidian unresolved total

# With source file info
obsidian unresolved verbose

# As JSON
obsidian unresolved format=json
```

### Orphaned Files (No Incoming Links)

```bash
# Files nobody links to
obsidian orphans

# Count only
obsidian orphans total
```

### Dead-End Files (No Outgoing Links)

```bash
# Files that link to nothing
obsidian deadends

# Count only
obsidian deadends total
```

## Search

### Basic Search

```bash
# Vault-wide search
obsidian search query="error budget"

# Scoped to folder
obsidian search query="error budget" path="200 - Notes"

# Limit results
obsidian search query="error budget" limit=5

# Count only
obsidian search query="error budget" total

# Case sensitive
obsidian search query="SLO" case
```

### Search with Context

```bash
# Shows matching lines with surrounding context
obsidian search:context query="error budget"

# Scoped
obsidian search:context query="error budget" path="300 - Reference"

# As JSON for parsing
obsidian search:context query="error budget" format=json
```

## Tags

### List Tags

```bash
# All tags in vault
obsidian tags

# Tags for a specific file
obsidian tags file="My Note"

# With counts
obsidian tags counts

# Sorted by frequency
obsidian tags sort=count counts

# Tag count only
obsidian tags total
```

### Tag Details

```bash
# Files with a specific tag
obsidian tag name="sre" verbose

# Count of files with tag
obsidian tag name="sre" total
```

## Structure Analysis

### Heading Outline

```bash
# Tree format (default)
obsidian outline file="My MOC"

# Markdown format
obsidian outline file="My MOC" format=md

# JSON for parsing
obsidian outline file="My MOC" format=json

# Heading count
obsidian outline file="My MOC" total
```

### File Metadata

```bash
# File info (path, size, dates)
obsidian file file="My Note"
```

Use this for:

- Checking if a file exists (returns info) vs doesn't exist (returns error)
- Getting modification dates for staleness checks
- Confirming file location after moves

### Word Count

```bash
# Full count
obsidian wordcount file="My Note"

# Words only
obsidian wordcount file="My Note" words

# Characters only
obsidian wordcount file="My Note" characters
```

## Tasks

### List Tasks

```bash
# All incomplete tasks
obsidian tasks todo

# All completed tasks
obsidian tasks done

# Tasks in a specific file
obsidian tasks file="My Project" todo

# Task count
obsidian tasks todo total
```

## Common Workflow Patterns

### Scan and Process Inbox

```bash
# 1. Pre-flight
obsidian vault

# 2. List inbox files
obsidian files folder="000 - Inbox" ext=md

# 3. For each file, read and analyze
obsidian read file="Inbox Note"

# 4. After classification, move to destination
obsidian move file="Inbox Note" to="200 - Notes/"

# 5. Set properties on moved file
obsidian property:set name="tags" value="tag1,tag2" type=list file="Inbox Note"
obsidian property:set name="created" value="2026-04-13" type=date file="Inbox Note"
obsidian property:set name="mocs" value="[[MOC Name]]" type=list file="Inbox Note"

# 6. Add Related section
obsidian append file="Inbox Note" content="\n## Related\n\n- [[Related Note]]"
```

### Create Note with Full Metadata

```bash
# 1. Create file with content
obsidian create path="200 - Notes/My insight about X.md" content="# My insight about X\n\nContent here." silent

# 2. Set all properties
obsidian property:set name="tags" value="topic1,topic2" type=list file="My insight about X"
obsidian property:set name="created" value="2026-04-13" type=date file="My insight about X"
obsidian property:set name="mocs" value="[[Relevant MOC]]" type=list file="My insight about X"

# 3. Add Related section
obsidian append file="My insight about X" content="\n## Related\n\n- [[Related Note 1]]\n- [[Related Note 2]]"
```

### Validate MOC Links

```bash
# 1. Get all outgoing links from MOC
obsidian links file="SRE Concepts MOC"

# 2. Check for unresolved links vault-wide (or specific to MOC)
obsidian unresolved verbose

# 3. Find orphans that might belong in this MOC
obsidian orphans

# 4. Check heading structure
obsidian outline file="SRE Concepts MOC"
```

### Move and Update (Archive Project)

```bash
# 1. Update status properties
obsidian property:set name="status" value="complete" file="My Project"
obsidian property:set name="completed_date" value="2026-04-13" type=date file="My Project"
obsidian property:remove name="next_action" file="My Project"

# 2. Move to archive
obsidian move file="My Project" to="400 - Archive/Projects/"

# 3. Verify new location
obsidian file file="My Project"
```

## Output Formats

Use `format=json` when you need to parse structured data programmatically.
Use `format=tsv` for tabular data.
Use default text format for human-readable output shown to the user.
Use `total` flag when you only need a count.

## Error Handling

### Obsidian Not Running

If `obsidian vault` fails:

```
Obsidian doesn't appear to be running. This plugin requires an open Obsidian vault.

Options:
A) Open Obsidian and retry
B) Cancel
```

### File Not Found

If a CLI command returns a "file not found" error:

```
File "[name]" not found in vault.

Options:
A) Search for similar files
B) Create the file
C) Cancel
```

Use `obsidian search query="partial name"` to suggest alternatives.

### File Already Exists

If `obsidian create` fails because the file exists (and `overwrite` flag not set):

```
File "[name]" already exists at [path].

Options:
A) Choose a different name
B) Overwrite existing file
C) Open existing file
D) Cancel
```

### General CLI Errors

If a CLI command fails mid-workflow:

- Report the error to the user
- Offer to retry the specific operation
- Do NOT silently fall back to shell commands
- Do NOT mix CLI and shell approaches within a single workflow run

## Integration with Analysis Library

This library handles all vault I/O. The **lib/analysis.md** library handles classification and matching logic. Skills should:

1. Use **obsidian-operations** to read content and scan the vault
2. Pass content to **analysis** logic for classification, topic extraction, MOC matching
3. Use **obsidian-operations** to execute the resulting actions (create, move, set properties, append links)

## Best Practices

1. **Always run pre-flight check** before any vault operation
2. **Use `silent` flag** on `create` to prevent files from opening in Obsidian
3. **Use `file=` for name-based resolution** (like wikilinks) and `path=` for exact paths
4. **Use `format=json`** when parsing output programmatically
5. **Use `total` flag** when you only need counts
6. **Set properties individually** rather than trying to write raw YAML
7. **Use `obsidian append`** for adding sections rather than rewriting entire files
8. **Check `obsidian file`** to verify a file exists before operating on it
9. **Use `obsidian unresolved`** instead of manual link validation loops
10. **Use `obsidian orphans`** instead of manual backlink scanning loops
