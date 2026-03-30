# Link Parser Utility

This utility provides instructions for extracting, validating, and manipulating Obsidian wiki-style links (`[[Link Name]]`).

## Purpose

Provide consistent link handling across all LYT Assistant commands. Ensures links are properly formatted, valid, and inserted in appropriate locations.

## Obsidian Link Syntax

### Basic Links

```markdown
[[Target Note]]
[[Target Note|Display Text]]
```

### Link Types

1. **Simple link:** `[[Note Name]]`
2. **Link with alias:** `[[Note Name|Alias]]`
3. **Link to heading:** `[[Note Name#Heading]]`
4. **Link with both:** `[[Note Name#Heading|Display Text]]`

## Core Operations

### Extract All Links from Content

To find all wiki-style links in a file:

```bash
grep -o '\[\[[^]]*\]\]' "file.md"
```

Output:
```
[[SRE Concepts MOC]]
[[Error Budget]]
[[Implementing Service Level Objectives-Hidalgo|SLO Book]]
```

**Parse link components:**

```bash
# Extract link target (everything before | or ]])
echo "[[Note Name|Alias]]" | sed 's/\[\[\([^|]*\).*/\1/'
# Output: Note Name

# Extract alias if present
echo "[[Note Name|Alias]]" | grep -o '|[^]]*' | sed 's/|//'
# Output: Alias
```

### Validate Link Target Exists

To check if a link target exists in the vault:

1. **Extract target name** from link (remove [[, ]], and alias)
2. **Search for file** with that name:
   ```bash
   find . -type f -name "Target Name.md" 2>/dev/null
   ```

3. **Report result:**
   - Found: Valid link ✅
   - Not found: Broken link ⚠️

**Example validation:**

```bash
# Given link: [[Circuit Breaker]]
TARGET="Circuit Breaker"
if find . -type f -name "${TARGET}.md" | grep -q .; then
  echo "✅ Valid link"
else
  echo "⚠️  Broken link: [[${TARGET}]] (file doesn't exist)"
fi
```

### Get Backlinks (Find Who Links to This File)

To find all files linking to a target:

```bash
TARGET="SRE Concepts MOC"
grep -r "\[\[${TARGET}\]\]" --include="*.md" .
```

Output shows all files that link to the target.

**Formatted output:**

```
📎 Backlinks to "SRE Concepts MOC":
  - 300 - Reference/SRE-Concepts/Error Budget.md
  - 300 - Reference/SRE-Concepts/SLOs.md
  - 200 - Notes/Reliability patterns.md
```

## Link Insertion

### Add Link to File

To add a link to a file in the appropriate location:

#### 1. Determine Insertion Location

**For MOC links** (links to Maps of Content):
- **Preferred:** Add to frontmatter `mocs:` field
- **Alternative:** Add at top of content (after frontmatter)

**For related note links:**
- **Preferred:** Add to "## Related" or "## See Also" section
- **Alternative:** Create section if doesn't exist, add at end

#### 2. Check for Duplicates

Before adding, verify link doesn't already exist:

```bash
LINK="SRE Concepts MOC"
if grep -q "\[\[${LINK}\]\]" "file.md"; then
  echo "Link already exists, skipping"
fi
```

#### 3. Insert Link

**Add to frontmatter (MOC links):**

```bash
# If frontmatter exists with mocs field, append
# If frontmatter exists without mocs, add field
# If no frontmatter, create it

# Read frontmatter
if grep -q "^---$" "file.md"; then
  # Has frontmatter - add to mocs field or create it
  sed -i '' '/^mocs:/s/$/\n  - [[SRE Concepts MOC]]/' "file.md"
fi
```

**Add to Related section:**

```bash
# Check if "## Related" section exists
if grep -q "^## Related" "file.md"; then
  # Add after ## Related heading
  sed -i '' '/^## Related/a\
- [[New Link]]\
' "file.md"
else
  # Create section at end
  echo -e "\n## Related\n\n- [[New Link]]" >> "file.md"
fi
```

#### 4. Format Properly

Ensure proper spacing and markdown:

```markdown
## Related

- [[Link One]]
- [[Link Two]]
- [[Link Three]]
```

### Remove Link from File

To remove a specific link:

```bash
LINK="Old Link"
sed -i '' "/\[\[${LINK}\]\]/d" "file.md"
```

**Clean up empty sections** after removal:

```bash
# If ## Related section is now empty, remove it
sed -i '' '/^## Related$/,/^$/{ /^## Related$/d; /^$/d; }' "file.md"
```

## Link Format Validation

### Check Link Syntax

Valid Obsidian links:
- `[[Target]]` ✅
- `[[Target|Alias]]` ✅
- `[[Target#Heading]]` ✅
- `[[Target#Heading|Alias]]` ✅

Invalid patterns:
- `[Target]` ❌ (single brackets)
- `[[Target]` ❌ (unclosed)
- `[[]]` ❌ (empty)
- `[[ Target ]]` ⚠️ (extra spaces - works but discouraged)

### Normalize Links

To clean up link formatting:

```bash
# Remove extra spaces inside links
sed 's/\[\[ */\[\[/g' "file.md" | sed 's/ *\]\]/\]\]/g'
```

## Bidirectional Linking

For two-way connections between files:

### Add Bidirectional Links

When linking File A → File B, also add File B → File A:

```bash
# Add link from A to B
echo "- [[File B]]" >> "File A.md"

# Add backlink from B to A
echo "- [[File A]]" >> "File B.md"
```

**Check if already bidirectional:**

```bash
# Check A links to B and B links to A
A_TO_B=$(grep -c "\[\[File B\]\]" "File A.md")
B_TO_A=$(grep -c "\[\[File A\]\]" "File B.md")

if [ $A_TO_B -gt 0 ] && [ $B_TO_A -gt 0 ]; then
  echo "✅ Bidirectional link exists"
fi
```

## Link Analysis

### Count Links in File

```bash
grep -o '\[\[[^]]*\]\]' "file.md" | wc -l
```

### Find Most Linked Files

```bash
# Find files with most outgoing links
for file in $(find . -name "*.md"); do
  count=$(grep -o '\[\[[^]]*\]\]' "$file" | wc -l)
  echo "$count $file"
done | sort -rn | head -10
```

### Find Orphaned Files (No Incoming Links)

```bash
# Files that no other file links to
for file in $(find . -name "*.md"); do
  name=$(basename "$file" .md)
  if ! grep -r "\[\[${name}\]\]" --include="*.md" . | grep -v "$file" | grep -q .; then
    echo "Orphan: $file"
  fi
done
```

## Link Patterns by File Type

### MOC Files (100 - MOCs/)

MOCs typically have:
- Many outgoing links (to notes they organize)
- Section headings organizing links by theme
- Few or no incoming links from other MOCs

**Example MOC structure:**

```markdown
# SRE Concepts MOC

## Reliability Patterns

- [[Circuit Breaker]]
- [[Bulkhead Pattern]]
- [[Exponential Backoff]]

## Monitoring

- [[Golden Signals]]
- [[RED Method]]
- [[USE Method]]

## Related MOCs

- [[Incident Management MOC]]
- [[Observability MOC]]
```

### Note Files (200 - Notes/)

Notes typically have:
- Link to 1-3 MOCs in frontmatter
- 2-5 related note links
- Focused, atomic content

**Example note linking:**

```markdown
---
mocs:
  - [[SRE Concepts MOC]]
  - [[Reliability Patterns MOC]]
---

# Circuit breakers prevent cascading failures

[Content...]

## Related

- [[Bulkhead Pattern]]
- [[Exponential Backoff]]
- [[Graceful Degradation]]
```

### Reference Files (300 - Reference/)

References typically have:
- Link to relevant MOCs
- Links to related references
- External source links (URLs)

**Example reference linking:**

```markdown
---
source: https://example.com/article
mocs:
  - [[SRE Concepts MOC]]
---

# Error Budget Calculations

[Content with formulas...]

## Related

- [[Implementing Service Level Objectives-Hidalgo]]
- [[SLOs]]
```

## Error Handling

### Broken Link Detection

When validating links, categorize issues:

1. **Missing file:** Target doesn't exist
   ```
   ⚠️  [[Circuit Breaker]] → File not found
   Options:
   A) Create stub file
   B) Remove link
   C) Leave as placeholder
   ```

2. **Ambiguous target:** Multiple files match
   ```
   ⚠️  [[Error Budget]] matches:
   - 300 - Reference/SRE-Concepts/Error Budget.md
   - 200 - Notes/Error Budget.md
   ```

3. **Typo or rename:** Similar files exist
   ```
   ⚠️  [[Curcuit Breaker]] not found
   Did you mean: [[Circuit Breaker]]?
   ```

### Safe Link Insertion

Before inserting links:

1. **Check file is writable:** Not locked by Obsidian
2. **Backup content:** In case of corruption
3. **Validate syntax:** Ensure proper formatting
4. **Check duplicates:** Don't add twice
5. **Verify result:** Read file after write to confirm

## Integration with Other Utilities

**Link parser provides data for:**
- **vault-scanner**: Validates links against vault index
- **moc-matcher**: Analyzes link patterns to suggest MOCs
- **content-analyzer**: Uses links to understand topics
- **discover-links**: Finds missing connections

**Link parser needs:**
- **vault-scanner**: File list to validate link targets

## Best Practices

1. **Always validate** before adding links
2. **Check for duplicates** to avoid redundancy
3. **Use consistent formatting** (no extra spaces)
4. **Add to appropriate section** (MOCs in frontmatter, related notes in ## Related)
5. **Report broken links** to user for decision
6. **Maintain bidirectional links** when appropriate
7. **Clean up** empty sections after removal
8. **Preserve content** - don't corrupt files

## Usage Pattern

Standard pattern for link operations:

```bash
# 1. Extract existing links
EXISTING_LINKS=$(grep -o '\[\[[^]]*\]\]' "file.md")

# 2. Parse link targets
for link in $EXISTING_LINKS; do
  TARGET=$(echo "$link" | sed 's/\[\[\([^|]*\).*/\1/')

  # 3. Validate target exists
  if ! find . -name "${TARGET}.md" | grep -q .; then
    echo "⚠️  Broken: $link"
  fi
done

# 4. Add new link (check duplicate first)
NEW_LINK="SRE Concepts MOC"
if ! echo "$EXISTING_LINKS" | grep -q "$NEW_LINK"; then
  # Add to appropriate location
  echo "- [[${NEW_LINK}]]" >> "file.md"
fi
```

## Summary

The link parser provides consistent link handling by:
- Extracting links from content
- Validating link targets exist
- Finding backlinks (who links here)
- Inserting links in appropriate locations
- Removing links and cleaning up
- Detecting broken links
- Supporting bidirectional linking

All commands should use these patterns for consistent link management.
