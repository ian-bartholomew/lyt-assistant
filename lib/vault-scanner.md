# Vault Scanner Utility

This utility provides instructions for traversing and indexing an Obsidian vault following the LYT (Linking Your Thinking) system.

## Purpose

Provide consistent vault scanning and indexing operations across all LYT Assistant commands. This ensures all commands have the same view of vault structure.

## LYT Folder Structure

The vault follows this structure:

- **000 - Inbox/** - Capture zone for new content (temporary)
- **100 - MOCs/** - Maps of Content for navigation and organization
- **200 - Notes/** - Atomic concept notes in your own words
- **300 - Reference/** - Configs, runbooks, book notes, external materials
- **400 - Archive/** - Stale or superseded content

## Core Operations

### Scan Complete Vault

To build a complete index of the vault:

1. **List inbox files:**
   ```bash
   find "000 - Inbox" -type f -name "*.md" 2>/dev/null | sort
   ```

2. **List MOC files:**
   ```bash
   find "100 - MOCs" -type f -name "*.md" 2>/dev/null | sort
   ```

3. **List Note files:**
   ```bash
   find "200 - Notes" -type f -name "*.md" 2>/dev/null | sort
   ```

4. **List Reference files (with subfolder structure):**
   ```bash
   find "300 - Reference" -type f -name "*.md" 2>/dev/null | sort
   ```

5. **List Archive files:**
   ```bash
   find "400 - Archive" -type f -name "*.md" 2>/dev/null | sort
   ```

### Get Inbox Files

To list all files in the inbox:

```bash
find "000 - Inbox" -type f -name "*.md" 2>/dev/null
```

**Return empty list if:** Directory doesn't exist or contains no markdown files.

### Get All MOCs

To list all MOC files with their metadata:

1. Find all MOC files
2. For each file:
   - Extract title (filename without .md)
   - Extract all links using `grep -o '\[\[.*\]\]'`
   - Parse frontmatter if present

**Expected structure:**
```json
[
  {
    "path": "100 - MOCs/Home.md",
    "title": "Home",
    "links": ["SRE Concepts MOC", "Incident Management MOC"]
  },
  {
    "path": "100 - MOCs/SRE Concepts MOC.md",
    "title": "SRE Concepts MOC",
    "links": ["Error Budget", "SLOs", "Latency"]
  }
]
```

### Get Reference Structure

To understand the Reference folder organization:

```bash
find "300 - Reference" -type d | sort
```

This shows subfolders like:
- `300 - Reference/SRE-Concepts/`
- `300 - Reference/Reading/Book-Summaries/`
- `300 - Reference/Tools/`

**Use for:** Suggesting appropriate destination folders during classification.

### Find File by Name

To locate a file anywhere in the vault:

```bash
find . -type f -name "filename.md" 2>/dev/null
```

Or for partial match:

```bash
find . -type f -name "*partial*.md" 2>/dev/null
```

### Count Files by Folder

To get file counts:

```bash
find "000 - Inbox" -type f -name "*.md" | wc -l
find "100 - MOCs" -type f -name "*.md" | wc -l
find "200 - Notes" -type f -name "*.md" | wc -l
find "300 - Reference" -type f -name "*.md" | wc -l
```

## Error Handling

### Missing Directories

If a standard LYT directory doesn't exist, handle gracefully:

```bash
if [ ! -d "000 - Inbox" ]; then
  echo "⚠️  Inbox directory not found. Create it with: mkdir -p '000 - Inbox'"
  exit 1
fi
```

### Permission Errors

If files are not readable:

```bash
if [ ! -r "path/to/file.md" ]; then
  echo "❌ Cannot read file (permission denied or file locked)"
fi
```

### Empty Results

Return empty list rather than error when no files found:

```bash
find "000 - Inbox" -type f -name "*.md" 2>/dev/null || echo "[]"
```

## Caching Considerations

For commands that scan the vault multiple times:

1. **Scan once at start** - Store results in memory/variable
2. **Reuse throughout command** - Don't rescan unnecessarily
3. **Invalidate when changes made** - Rescan after moves/creates

Example flow:
```
1. User runs /classify-inbox
2. Scan vault once → store as $VAULT_INDEX
3. For each inbox file:
   - Use $VAULT_INDEX to find MOCs
   - Use $VAULT_INDEX to find related files
   - Don't rescan
4. After moving file → update $VAULT_INDEX or rescan
```

## Integration with Other Utilities

**Vault scanner provides data for:**
- **link-parser**: Needs file list to validate links exist
- **moc-matcher**: Needs MOC list to suggest relevant MOCs
- **content-analyzer**: Needs related files to analyze topics
- **frontmatter**: Needs file list to batch-process metadata

**All commands should:**
1. Call vault scanner first to build index
2. Pass index to other utilities
3. Avoid duplicate scans

## Performance Optimization

For large vaults (>500 files):

1. **Use find efficiently:**
   - Limit depth: `find "300 - Reference" -maxdepth 3`
   - Use -prune to skip directories

2. **Cache results:**
   - Store file list in variable
   - Only rescan when filesystem changes

3. **Parallel processing:**
   - Process multiple files concurrently when possible
   - Use xargs for batch operations

## Output Format

When presenting vault structure to user:

```
📦 Vault Overview:
├── 📥 Inbox: 3 files
├── 🗺️  MOCs: 12 files
├── 📝 Notes: 45 files
├── 📚 Reference: 128 files
│   ├── SRE-Concepts: 34 files
│   ├── Reading/Book-Summaries: 18 files
│   └── Tools: 12 files
└── 📦 Archive: 67 files
```

## Usage Pattern

Standard pattern for commands:

```bash
# 1. Check vault structure exists
if [ ! -d "000 - Inbox" ] || [ ! -d "100 - MOCs" ]; then
  echo "⚠️  This doesn't appear to be an LYT vault"
  exit 1
fi

# 2. Scan vault
INBOX_FILES=$(find "000 - Inbox" -type f -name "*.md")
MOC_FILES=$(find "100 - MOCs" -type f -name "*.md")
REFERENCE_STRUCTURE=$(find "300 - Reference" -type d)

# 3. Use results
for file in $INBOX_FILES; do
  # Process file
done
```

## Best Practices

1. **Always check directory exists** before scanning
2. **Handle empty results** gracefully (empty list, not error)
3. **Use consistent sorting** (alphabetical with `sort`)
4. **Provide user-friendly output** with emoji and structure
5. **Cache results** when possible to avoid rescanning
6. **Validate paths** before operations
7. **Report errors clearly** with actionable suggestions

## Summary

The vault scanner provides the foundation for all LYT Assistant operations by:
- Discovering vault structure
- Listing files by category
- Enabling consistent indexing
- Supporting link validation
- Informing classification decisions

All commands should use these patterns for consistent behavior.
