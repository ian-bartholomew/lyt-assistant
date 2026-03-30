# Frontmatter Utility

This utility provides instructions for reading and writing YAML frontmatter in markdown files.

## Purpose

Provide consistent frontmatter operations across all LYT Assistant commands. Ensures metadata is properly formatted, preserved, and accessible.

## YAML Frontmatter Structure

Obsidian uses YAML frontmatter at the beginning of markdown files:

```markdown
---
tags: [sre, reliability]
created: 2026-03-26
type: reference
source: https://example.com
mocs:
  - [[SRE Concepts MOC]]
  - [[Observability MOC]]
---

# File Content

Content starts after frontmatter...
```

## Standard Fields

### Common Fields for All Files

- **`tags`**: Array of tags `[tag1, tag2]` or YAML list
- **`created`**: Creation date `YYYY-MM-DD`
- **`updated`**: Last update date `YYYY-MM-DD`
- **`mocs`**: Links to relevant MOCs (list of `[[MOC Name]]`)

### Fields for Reference Files (300 - Reference/)

- **`type`**: `internal` (company docs) or `external` (public sources)
- **`source`**: Single source URL or book title
- **`sources`**: Multiple sources (array)
- **`author`**: Original author of external content

### Fields for Notes (200 - Notes/)

- **`tags`**: Topics and themes
- **`created`**: When insight captured
- **`confidence`**: Optional - `low`, `medium`, `high`

## Core Operations

### Read Frontmatter from File

To extract and parse frontmatter:

```bash
# Check if file has frontmatter (starts with ---)
if head -n 1 "file.md" | grep -q "^---$"; then
  # Extract frontmatter (between first two ---)
  sed -n '/^---$/,/^---$/p' "file.md" | sed '1d;$d'
fi
```

**Parse specific fields:**

```bash
# Get tags field
grep "^tags:" "file.md" | sed 's/tags: *//'

# Get created date
grep "^created:" "file.md" | sed 's/created: *//'

# Get source field
grep "^source:" "file.md" | sed 's/source: *//'

# Get mocs list
sed -n '/^mocs:/,/^[a-z]/p' "file.md" | grep "  - " | sed 's/  - //'
```

### Write Frontmatter to File

#### Create New Frontmatter

For files without frontmatter:

```bash
# Create frontmatter block at top of file
{
  echo "---"
  echo "tags: [sre, observability]"
  echo "created: $(date +%Y-%m-%d)"
  echo "mocs:"
  echo "  - [[SRE Concepts MOC]]"
  echo "---"
  echo ""
  cat "file.md"
} > "file.md.tmp" && mv "file.md.tmp" "file.md"
```

#### Update Existing Frontmatter

To update a field:

```bash
# Update tags field
sed -i '' 's/^tags:.*/tags: [new, tags]/' "file.md"

# Update created date
sed -i '' "s/^created:.*/created: $(date +%Y-%m-%d)/" "file.md"

# Update source field
sed -i '' 's#^source:.*#source: https://new-url.com#' "file.md"
```

#### Add Field to Existing Frontmatter

```bash
# Add new field before closing ---
sed -i '' '/^---$/a\
new_field: value
' "file.md"
```

### Add or Update MOCs List

To manage the `mocs:` field:

```bash
# If mocs field doesn't exist, add it
if ! grep -q "^mocs:" "file.md"; then
  sed -i '' '/^---$/i\
mocs:\
  - [[New MOC]]\
' "file.md"
else
  # Add to existing mocs list
  sed -i '' '/^mocs:/a\
  - [[New MOC]]\
' "file.md"
fi
```

### Add or Update Tags

To manage tags:

```bash
# If tags field exists as array
if grep -q "^tags: \[" "file.md"; then
  # Parse array, add tag, rewrite
  CURRENT_TAGS=$(grep "^tags:" "file.md" | sed 's/tags: \[\(.*\)\]/\1/')
  NEW_TAGS="${CURRENT_TAGS}, newtag"
  sed -i '' "s/^tags:.*/tags: [${NEW_TAGS}]/" "file.md"
fi

# If tags field exists as YAML list
if grep -q "^tags:$" "file.md"; then
  sed -i '' '/^tags:/a\
  - newtag\
' "file.md"
fi
```

### Set Arbitrary Field

To set any field value:

```bash
FIELD="author"
VALUE="John Doe"

if grep -q "^${FIELD}:" "file.md"; then
  # Update existing field
  sed -i '' "s/^${FIELD}:.*/${FIELD}: ${VALUE}/" "file.md"
else
  # Add new field
  sed -i '' "/^---$/a\\
${FIELD}: ${VALUE}
" "file.md"
fi
```

## Frontmatter Formats

### Array Format

```yaml
tags: [tag1, tag2, tag3]
```

**Pros:** Compact, single line
**Cons:** Harder to edit

### List Format

```yaml
tags:
  - tag1
  - tag2
  - tag3
```

**Pros:** Easy to read, easy to append
**Cons:** Takes more space

**Recommendation:** Use list format for `mocs:` (for easy appending), array format for `tags:` (for compactness).

### String Format

```yaml
source: https://example.com
created: 2026-03-26
```

**Use for:** Single values, URLs, dates

### Multi-line Format

```yaml
description: |
  This is a multi-line
  description that spans
  multiple lines.
```

**Use for:** Long text content

## Validation

### Check Frontmatter is Valid YAML

```bash
# Extract frontmatter and validate with python
python3 -c "
import yaml
import sys

with open('file.md', 'r') as f:
    content = f.read()
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            try:
                yaml.safe_load(parts[1])
                print('✅ Valid YAML')
                sys.exit(0)
            except yaml.YAMLError as e:
                print(f'❌ Invalid YAML: {e}')
                sys.exit(1)
"
```

### Required Fields Check

For different file types:

```bash
# Check Reference file has required fields
check_reference_frontmatter() {
  local file=$1

  if ! grep -q "^source:" "$file" && ! grep -q "^sources:" "$file"; then
    echo "⚠️  Reference file missing source field"
  fi

  if ! grep -q "^type:" "$file"; then
    echo "⚠️  Reference file missing type field"
  fi
}

# Check any file has created date
if ! grep -q "^created:" "file.md"; then
  echo "⚠️  File missing created date"
fi
```

## Frontmatter Templates

### Template for New Note

```yaml
---
tags: []
created: 2026-03-26
mocs:
  - [[MOC Name]]
---
```

### Template for New Reference

```yaml
---
tags: []
created: 2026-03-26
type: external
source: https://example.com
mocs:
  - [[MOC Name]]
---
```

### Template for Research Notes (Multiple Sources)

```yaml
---
tags: []
created: 2026-03-26
type: external
sources:
  - https://example.com/article1
  - https://example.com/article2
  - https://wikipedia.org/entry
mocs:
  - [[MOC Name]]
---
```

## Preserving Content

### Safe Update Pattern

Always preserve file content when updating frontmatter:

```bash
# 1. Extract frontmatter
FRONTMATTER=$(sed -n '/^---$/,/^---$/p' "file.md")

# 2. Extract content (everything after second ---)
CONTENT=$(sed -n '/^---$/,/^---$/!p' "file.md" | tail -n +3)

# 3. Modify frontmatter
NEW_FRONTMATTER=$(echo "$FRONTMATTER" | sed 's/old/new/')

# 4. Reconstruct file
{
  echo "$NEW_FRONTMATTER"
  echo ""
  echo "$CONTENT"
} > "file.md.tmp" && mv "file.md.tmp" "file.md"
```

### Backup Before Modification

```bash
# Create backup before modifying
cp "file.md" "file.md.backup"

# Modify frontmatter
# ... operations ...

# Verify result, restore if corrupted
if ! grep -q "^---$" "file.md"; then
  echo "❌ Frontmatter corrupted, restoring backup"
  mv "file.md.backup" "file.md"
fi
```

## Special Cases

### Files Without Frontmatter

When adding frontmatter to files that don't have it:

```bash
if ! head -n 1 "file.md" | grep -q "^---$"; then
  # No frontmatter - add it
  {
    echo "---"
    echo "tags: []"
    echo "created: $(date +%Y-%m-%d)"
    echo "---"
    echo ""
    cat "file.md"
  } > "file.md.tmp" && mv "file.md.tmp" "file.md"
fi
```

### Malformed Frontmatter

If frontmatter is corrupted:

```bash
# Check for common issues
if head -n 1 "file.md" | grep -q "^---$"; then
  # Has opening --- but check for closing
  if ! tail -n +2 "file.md" | grep -q "^---$"; then
    echo "❌ Frontmatter missing closing ---"
    echo "Options:"
    echo "A) Fix interactively"
    echo "B) Remove frontmatter"
    echo "C) Skip this file"
  fi
fi
```

### Empty Frontmatter

```yaml
---
---
```

Valid but not useful. Add fields as needed:

```bash
# Detect empty frontmatter
if sed -n '/^---$/,/^---$/p' "file.md" | wc -l | grep -q "^2$"; then
  echo "ℹ️  Frontmatter is empty, adding default fields"
fi
```

## Date Handling

### Get Current Date

```bash
DATE=$(date +%Y-%m-%d)
```

### Update Created Date (Only if Not Set)

```bash
if ! grep -q "^created:" "file.md"; then
  sed -i '' "/^---$/a\\
created: $(date +%Y-%m-%d)
" "file.md"
fi
```

### Set Updated Date

```bash
if grep -q "^updated:" "file.md"; then
  # Update existing field
  sed -i '' "s/^updated:.*/updated: $(date +%Y-%m-%d)/" "file.md"
else
  # Add field
  sed -i '' "/^---$/a\\
updated: $(date +%Y-%m-%d)
" "file.md"
fi
```

## Integration with Other Utilities

**Frontmatter provides data for:**
- **content-analyzer**: Type field helps classify files
- **moc-matcher**: MOCs field shows current associations
- **link-parser**: MOCs field contains wiki links to parse

**Frontmatter works with:**
- **vault-scanner**: Batch-process frontmatter across files
- All commands that need to store metadata

## Error Handling

### Permission Errors

```bash
if [ ! -w "file.md" ]; then
  echo "❌ Cannot write to file (may be locked by Obsidian)"
  exit 1
fi
```

### YAML Parsing Errors

```bash
# Try to parse, catch errors
if ! python3 -c "import yaml; yaml.safe_load('$FRONTMATTER')" 2>/dev/null; then
  echo "❌ YAML syntax error in frontmatter"
  echo "Run: /check-yaml file.md"
fi
```

### Corrupted Files

If file operations corrupt frontmatter:

```bash
# Verify frontmatter integrity after write
if ! head -n 1 "file.md" | grep -q "^---$"; then
  echo "❌ Frontmatter corrupted during write"
  # Restore backup
  mv "file.md.backup" "file.md"
fi
```

## Best Practices

1. **Always validate YAML** after modifications
2. **Preserve existing fields** unless explicitly updating
3. **Maintain format consistency** (array vs list)
4. **Use standard field names** (tags, created, source, mocs)
5. **Backup before modifying** critical files
6. **Check file is writable** before operations
7. **Handle missing frontmatter** gracefully
8. **Report malformed YAML** to user for decision
9. **Use appropriate templates** for file types
10. **Test with simple files first** before batch operations

## Usage Pattern

Standard pattern for frontmatter operations:

```bash
# 1. Check file has frontmatter
if head -n 1 "file.md" | grep -q "^---$"; then
  # Has frontmatter

  # 2. Read specific fields
  TAGS=$(grep "^tags:" "file.md")
  CREATED=$(grep "^created:" "file.md")

  # 3. Update or add fields
  if [ -z "$CREATED" ]; then
    # Add created date
    sed -i '' "/^---$/a\\
created: $(date +%Y-%m-%d)
" "file.md"
  fi

  # 4. Validate result
  if ! head -n 1 "file.md" | grep -q "^---$"; then
    echo "❌ Frontmatter corrupted"
  fi
else
  # No frontmatter - create it
  {
    echo "---"
    echo "tags: []"
    echo "created: $(date +%Y-%m-%d)"
    echo "---"
    echo ""
    cat "file.md"
  } > "file.md.tmp" && mv "file.md.tmp" "file.md"
fi
```

## Summary

The frontmatter utility provides consistent metadata operations by:
- Reading YAML frontmatter fields
- Writing and updating frontmatter safely
- Creating frontmatter templates
- Validating YAML syntax
- Preserving file content
- Handling malformed frontmatter
- Supporting standard field types

All commands should use these patterns for consistent metadata management.
