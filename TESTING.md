# LYT Assistant Plugin - Testing Guide

This guide provides comprehensive test cases for validating the LYT Assistant plugin functionality.

## Prerequisites

1. **Backup your vault** or test on a copy
2. **LYT folder structure** exists:
   - `000 - Inbox/`
   - `100 - MOCs/`
   - `200 - Notes/`
   - `300 - Reference/`
   - `400 - Archive/` (optional)

## Test Suite Overview

- **Test 1:** Plugin Discovery and Loading
- **Test 2:** `/classify-inbox` - Basic Classification
- **Test 3:** `/classify-inbox` - Interactive Editing
- **Test 4:** `/create-note` - From Inbox
- **Test 5:** `/create-note` - From Scratch
- **Test 6:** `/discover-links` - Find Connections
- **Test 7:** `/check-moc-health` - MOC Audit
- **Test 8:** `/research` - Web Search
- **Test 9:** Error Handling
- **Test 10:** Integration Testing

---

## Test 1: Plugin Discovery and Loading

### Objective
Verify plugin is discovered and skills are loaded.

### Steps

1. Run Claude Code from vault directory:
   ```bash
   cd /path/to/your/vault
   cc
   ```

2. Check available skills:
   ```
   /help
   ```

### Expected Results

✅ Plugin loaded message appears
✅ Five skills visible in help:
   - `/classify-inbox`
   - `/create-note`
   - `/discover-links`
   - `/check-moc-health`
   - `/research`

### Pass Criteria

- All 5 skills listed
- No error messages during load

---

## Test 2: `/classify-inbox` - Basic Classification

### Objective
Verify inbox file classification and movement.

### Setup

Create test files in inbox:

```bash
# Test file 1: Clear Note
cat > "000 - Inbox/circuit-breaker-thought.md" << 'EOF'
# Circuit Breaker Thoughts

I think circuit breakers are essential for preventing cascading failures
in distributed systems. In my experience, they're one of the most effective
reliability patterns.

The pattern is simple: after N failures, stop calling the service for a
timeout period. This protects both the caller and the failing service.
EOF

# Test file 2: Clear Reference
cat > "000 - Inbox/terraform-commands.md" << 'EOF'
# Terraform Commands

Common terraform commands:

```bash
terraform init
terraform plan
terraform apply
terraform destroy
```

## State Management

View state:
```bash
terraform state list
terraform state show <resource>
```
EOF
```

### Test Steps

1. Run classification:
   ```
   /classify-inbox
   ```

2. For first file (circuit-breaker-thought.md):
   - **Expected classification:** Note (high confidence)
   - **Expected destination:** `200 - Notes/`
   - **Expected title suggestion:** "Circuit breakers prevent cascading failures"
   - **Expected MOCs:** Reliability-related MOCs

3. Select **Option A: Accept and move**

4. For second file (terraform-commands.md):
   - **Expected classification:** Reference (high confidence)
   - **Expected destination:** `300 - Reference/terraform/` or similar
   - **Expected MOCs:** Terraform MOC (if exists)

5. Select **Option A: Accept and move**

### Expected Results

✅ File 1 renamed and moved to `200 - Notes/Circuit breakers prevent cascading failures.md`
✅ File 2 moved to appropriate Reference subfolder
✅ Both files have frontmatter added:
   ```yaml
   ---
   tags: [...]
   created: 2026-03-27
   mocs: [...]
   ---
   ```
✅ Links added to Related sections
✅ Inbox is empty
✅ Summary report shows: 2 files processed, 2 moved

### Verification Commands

```bash
# Check Note was moved
ls "200 - Notes/"*circuit*

# Check Reference was moved
find "300 - Reference" -name "*terraform*"

# Check frontmatter
head -10 "200 - Notes/Circuit breakers prevent cascading failures.md"

# Verify inbox empty
ls "000 - Inbox/"
```

### Pass Criteria

- Files moved to correct destinations
- Frontmatter created with proper fields
- Links added (at least MOCs)
- No file corruption
- Original content preserved

---

## Test 3: `/classify-inbox` - Interactive Editing

### Objective
Test interactive editing of suggestions.

### Setup

```bash
cat > "000 - Inbox/ambiguous-content.md" << 'EOF'
# Database Indexing

Database indexes improve query performance but have tradeoffs.

Here's how to create an index in PostgreSQL:

```sql
CREATE INDEX idx_name ON table_name(column_name);
```

I've found that over-indexing can hurt write performance significantly.
EOF
```

### Test Steps

1. Run classification:
   ```
   /classify-inbox
   ```

2. Content has both Note and Reference indicators

3. Test **Option B: Edit destination**:
   - Should show list of available folders
   - Select different destination
   - Confirm change applied

4. Test **Option C: Edit links**:
   - Should show suggested links
   - Remove one link
   - Add a custom link
   - Confirm changes applied

### Expected Results

✅ Can edit destination successfully
✅ Can modify link suggestions
✅ Changes reflected in final file
✅ File created with edited settings

### Pass Criteria

- Editing works without errors
- Final file reflects edits
- No data loss during editing

---

## Test 4: `/create-note` - From Inbox

### Objective
Create structured note from existing inbox content.

### Setup

```bash
cat > "000 - Inbox/unstructured-thoughts.md" << 'EOF'
Some random thoughts about error budgets...

Error budgets let us balance reliability and velocity. When you have budget
remaining, you can push features faster. When budget is depleted, focus on
reliability.

This decouples the reliability conversation from feature work.
EOF
```

### Test Steps

1. Run:
   ```
   /create-note
   ```

2. Select **Option A: I have content in inbox**

3. Select the unstructured-thoughts.md file

4. Review analysis:
   - Should classify as Note
   - Should suggest assertion-style title
   - Should suggest MOCs

5. Select **Option A: Create with these settings**

### Expected Results

✅ Note classified correctly (Note vs Reference)
✅ Assertion-style title generated
✅ Proper frontmatter created
✅ MOCs suggested and added
✅ Related links added
✅ File created in correct location

### Pass Criteria

- Classification correct
- Title follows "X verbs Y" pattern
- Frontmatter has all fields
- Links added appropriately

---

## Test 5: `/create-note` - From Scratch

### Objective
Create note from topic without existing content.

### Test Steps

1. Run:
   ```
   /create-note
   ```

2. Select **Option C: Start from scratch**

3. Enter topic:
   ```
   Graceful degradation maintains user experience
   ```

4. Review suggestions:
   - Type: Note
   - Destination: 200 - Notes/
   - MOCs: Reliability-related

5. Accept and create

### Expected Results

✅ Template created with placeholder content
✅ Proper structure (frontmatter, heading, sections)
✅ MOCs linked
✅ File ready for content addition

### Pass Criteria

- Template structure correct
- Frontmatter valid
- File created in right location
- Message about filling in content

---

## Test 6: `/discover-links` - Find Connections

### Objective
Find missing connections between existing notes.

### Setup

Create related notes without links:

```bash
cat > "200 - Notes/Note A.md" << 'EOF'
---
tags: [reliability]
---

# Note About Circuit Breakers

Circuit breakers prevent cascading failures...
EOF

cat > "200 - Notes/Note B.md" << 'EOF'
---
tags: [reliability]
---

# Note About Bulkhead Pattern

Bulkhead patterns isolate failures...
EOF

cat > "200 - Notes/Note C.md" << 'EOF'
---
tags: [reliability]
---

# Note About Retry Logic

Retry logic with exponential backoff...
EOF
```

### Test Steps

1. Run:
   ```
   /discover-links
   ```

2. Review grouped suggestions:
   - Should detect "Reliability" theme
   - Should suggest connections between A, B, C

3. Select **Option A: Apply all connections** for the group

### Expected Results

✅ Notes grouped by theme (Reliability)
✅ Multiple connection opportunities found
✅ Links added to Related sections
✅ Summary shows number of links added

### Verification

```bash
# Check links added
grep "## Related" "200 - Notes/Note A.md"
grep "\[\[Note B\]\]" "200 - Notes/Note A.md"
```

### Pass Criteria

- Connections detected correctly
- Grouping makes sense
- Links added bidirectionally (when appropriate)
- No duplicate links created

---

## Test 7: `/check-moc-health` - MOC Audit

### Objective
Audit MOC for broken links and missing coverage.

### Setup

Create test MOC with issues:

```bash
cat > "100 - MOCs/Test MOC.md" << 'EOF'
# Test MOC

## Section One

- [[Existing Note]]
- [[Broken Link 1]]
- [[Broken Link 2]]

## Section Two

- [[Another Existing Note]]
EOF

# Create referenced notes
echo "# Existing Note" > "200 - Notes/Existing Note.md"
echo "# Another Existing Note" > "200 - Notes/Another Existing Note.md"

# Create orphan that should be in MOC
cat > "200 - Notes/Orphan Note.md" << 'EOF'
---
tags: [test-topic]
---

# Orphan Note

This mentions test-topic but isn't linked from Test MOC.
EOF
```

### Test Steps

1. Run:
   ```
   /check-moc-health Test MOC
   ```

2. Review audit report:
   - Structure: Should pass
   - Broken links: Should find 2 (Broken Link 1, Broken Link 2)
   - Coverage: Should find orphan note

3. Select **Option A: Create missing notes**

4. Verify stub files created

### Expected Results

✅ Broken links detected: 2
✅ Orphaned notes found: 1
✅ Structure audit passes
✅ Option to create stubs offered
✅ Stubs created with proper frontmatter

### Verification

```bash
# Check stubs created
ls "200 - Notes/Broken Link 1.md"
ls "200 - Notes/Broken Link 2.md"

# Check frontmatter
grep "mocs:" "200 - Notes/Broken Link 1.md"
```

### Pass Criteria

- All broken links detected
- Orphans identified correctly
- Stubs created with proper structure
- MOC updated if requested
- No false positives

---

## Test 8: `/research` - Web Search

### Objective
Research topic and create reference note.

### Test Steps

1. Run:
   ```
   /research Little's Law
   ```

2. Confirm research strategy (web search)

3. Review synthesized content:
   - Definition present
   - Formula/examples included
   - Sources cited

4. Review suggestions:
   - Destination folder
   - MOCs
   - Related links

5. Select **Option A: Create with these settings**

### Expected Results

✅ Web search executed (or simulated)
✅ Content synthesized with structure:
   - Overview
   - Key concepts
   - Formula (if applicable)
   - Examples
   - Related topics
   - References section
✅ Frontmatter includes:
   - `type: external`
   - `sources: [...]` with URLs
✅ File created with proper structure
✅ MOCs linked

### Verification

```bash
# Check file created
ls "300 - Reference"/*/*Little\'s\ Law.md

# Check sources in frontmatter
grep "sources:" -A 3 [path-to-file]

# Check References section
grep "## References" [path-to-file]
```

### Pass Criteria

- Content is coherent and structured
- Sources properly cited
- Not just copy-paste from web
- Proper frontmatter with type and sources
- Related links appropriate

---

## Test 9: Error Handling

### Objective
Verify graceful error handling.

### Test Cases

#### 9.1: Empty Inbox

```
/classify-inbox
```

**Expected:** ✅ "Inbox is clean! No files to process."

#### 9.2: Missing LYT Directories

```bash
# Temporarily rename folder
mv "100 - MOCs" "100 - MOCs.backup"

/classify-inbox
```

**Expected:** ⚠️ Warning about missing LYT structure

```bash
# Restore
mv "100 - MOCs.backup" "100 - MOCs"
```

#### 9.3: File Conflict

```bash
# Create existing file
echo "# Existing" > "200 - Notes/Test Note.md"

# Create duplicate in inbox
echo "# Test Note" > "000 - Inbox/Test Note.md"

/classify-inbox
```

**Expected:** ⚠️ Conflict detected, options offered (rename, skip, etc.)

#### 9.4: Invalid MOC Name

```
/check-moc-health NonexistentMOC
```

**Expected:** ❌ Error with list of available MOCs

#### 9.5: Research Topic Not Found

```
/research XYZ123InvalidTopic
```

**Expected:** ⚠️ No sources found, options to retry or cancel

### Pass Criteria

- No crashes or exceptions
- Clear error messages
- Recovery options offered
- No data corruption
- User can proceed or cancel

---

## Test 10: Integration Testing

### Objective
Test complete workflow across multiple skills.

### Scenario: New Topic Flow

1. **Research a topic:**
   ```
   /research Circuit Breaker pattern
   ```
   - Creates reference note in `300 - Reference/`

2. **Create personal insight:**
   ```
   /create-note
   ```
   - Start from scratch
   - Topic: "Circuit breakers prevent cascading failures"
   - Creates note in `200 - Notes/`

3. **Discover connections:**
   ```
   /discover-links
   ```
   - Should find connection between reference and note
   - Adds links

4. **Check MOC health:**
   ```
   /check-moc-health Reliability MOC
   ```
   - Should suggest adding new notes to MOC
   - Add them

5. **Process additional content:**
   ```
   /classify-inbox
   ```
   - Add more related content
   - Verify links to existing notes

### Expected Results

✅ Complete workflow executes without errors
✅ All files properly linked
✅ MOC updated with new content
✅ Bidirectional links where appropriate
✅ No orphaned content
✅ Consistent frontmatter across all files

### Pass Criteria

- No errors in multi-skill workflow
- Content properly integrated
- Links are coherent and bidirectional
- MOC remains organized
- Vault structure intact

---

## Performance Testing

### Test Large Vault

Create test vault with:
- 50+ notes in `200 - Notes/`
- 100+ references in `300 - Reference/`
- 10+ MOCs

Run skills and measure:
- **Scan time:** Should be < 3 seconds for 150 files
- **Classification time:** Should be < 2 seconds per file
- **Link discovery:** Should complete < 10 seconds

### Pass Criteria

- No timeouts
- Reasonable performance
- No memory issues

---

## Regression Testing

After any plugin changes:

1. Run **Test 2** (basic classification)
2. Run **Test 6** (link discovery)
3. Run **Test 7** (MOC health)
4. Run **Test 9.1-9.3** (error handling)

All should pass without changes.

---

## Test Results Template

```markdown
# Test Results - [Date]

## Test 1: Plugin Discovery
- Status: ✅ Pass / ❌ Fail
- Notes:

## Test 2: Basic Classification
- Status: ✅ Pass / ❌ Fail
- Notes:

## Test 3: Interactive Editing
- Status: ✅ Pass / ❌ Fail
- Notes:

## Test 4: Create from Inbox
- Status: ✅ Pass / ❌ Fail
- Notes:

## Test 5: Create from Scratch
- Status: ✅ Pass / ❌ Fail
- Notes:

## Test 6: Discover Links
- Status: ✅ Pass / ❌ Fail
- Notes:

## Test 7: MOC Health
- Status: ✅ Pass / ❌ Fail
- Notes:

## Test 8: Research
- Status: ✅ Pass / ❌ Fail
- Notes:

## Test 9: Error Handling
- Status: ✅ Pass / ❌ Fail
- Notes:

## Test 10: Integration
- Status: ✅ Pass / ❌ Fail
- Notes:

## Overall Result
- Tests Passed: X/10
- Tests Failed: Y/10
- Overall: ✅ Pass / ⚠️ Partial / ❌ Fail
```

---

## Known Limitations

1. **Web search simulation:** `/research` may need actual WebFetch implementation
2. **Large vaults:** Performance may degrade with >500 files
3. **Complex markdown:** Some edge cases in link parsing
4. **Obsidian-specific:** Plugin links may not work in other markdown editors

---

## Troubleshooting

### Skills Not Loading

**Check:** Plugin directory location
```bash
ls .claude-plugin/lyt-assistant/plugin.json
```

**Fix:** Ensure in correct location relative to working directory

### Skills Not Triggering

**Check:** Description trigger phrases
```bash
grep "description:" .claude-plugin/lyt-assistant/skills/*/SKILL.md
```

**Fix:** Ensure trigger phrases match user input

### File Operations Failing

**Check:** Permissions
```bash
ls -la "000 - Inbox/"
```

**Fix:** Ensure files are not locked by Obsidian

### Links Not Added

**Check:** Frontmatter parsing
```bash
head -20 [file]
```

**Fix:** Ensure valid YAML frontmatter

---

## Next Steps After Testing

1. **Document issues** found during testing
2. **Iterate on fixes** for failed tests
3. **Performance tune** if needed
4. **Create user guide** based on test scenarios
5. **Publish to marketplace** when ready

---

## Contact

For issues or questions about testing:
- Email: ian@ianbartholomew.com
- Plugin: lyt-assistant v0.1.0
