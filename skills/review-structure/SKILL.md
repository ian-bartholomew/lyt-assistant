---
name: review-structure
description: This skill should be used when a markdown article needs structural quality validation — checking frontmatter, sections, word count, wikilinks, and source attribution. Works on any .md file in raw/docs/ or wiki/. Called by /research after drafting, and reusable by /ingest and /compile.
version: 0.1.0
argument-hint: <file-path>
allowed-tools: [Read, Grep, Glob]
---

# Review Structure Skill

Validate the structural quality of a markdown article. Read-only — reports issues but does not modify the file.

## Purpose

Ensure articles meet minimum structural quality before they enter the wiki pipeline. Checks frontmatter completeness, section structure, word count, source attribution, wikilink validity, and related article references. Returns a structured report with pass/fail status.

## When to Use

Invoke this skill when:

- Called by `/research` after writing a draft to `raw/docs/.draft-<topic>.md`
- Called by `/ingest` after compiling a wiki article
- Called by `/compile` during its validation step
- User explicitly runs `/review-structure <file-path>`

## Input

A single file path to a `.md` file. Can be:

- `raw/docs/.draft-<topic>.md` — research draft awaiting review
- `raw/docs/<topic>.md` — finalized research doc
- `wiki/concepts/<topic>.md` — compiled wiki article
- `wiki/guides/<topic>.md` — compiled wiki article
- Any other `.md` file in the vault

## Checks

Run all 8 checks in order. Collect all errors and warnings before reporting.

### Check 1: Frontmatter Completeness

Read the file and parse YAML frontmatter (content between first `---` and second `---`).

**Detect file type by frontmatter fields present:**

If `source_type` field exists → **raw/docs file** (research output). Required fields:

| Field | Type | Required |
|-------|------|----------|
| `title` | string | yes |
| `source_type` | string | yes |
| `date` | YYYY-MM-DD string | yes |
| `sources` | list of strings | yes |
| `suggested_domain` | list of strings | yes |
| `suggested_destination` | string (one of: concepts, guides, company, learning) | yes |
| `suggested_related` | list of wikilink strings | yes |

If `maturity` field exists → **wiki file** (compiled article). Required fields:

| Field | Type | Required |
|-------|------|----------|
| `title` | string | yes |
| `domain` | list of strings | yes |
| `maturity` | string (one of: stub, draft, developing, mature) | yes |
| `confidence` | string (one of: low, medium, high) | yes |
| `compiled_from` | list of strings | yes |
| `related` | list of wikilink strings | yes |
| `last_compiled` | YYYY-MM-DD string | yes |

For each missing or invalid field, report as **error**.

### Check 2: Title/Heading Match

Compare the `title` frontmatter field to the first `# H1` heading in the body.

- If they match (case-insensitive): pass
- If they differ: **warning** — report both values
- If no H1 heading exists: **error** — article has no title heading

### Check 3: Section Structure

Scan for `## H2` headings in the body (after frontmatter).

- Must have a section named "Overview" (or "Summary" or "Introduction"): **error** if missing
- Must have at least 2 other `## H2` sections with content beneath them: **error** if fewer than 2

### Check 4: Word Count

Count words in the body (everything after the closing `---` of frontmatter). Exclude code blocks (``` fenced blocks).

- < 200 words: **error** — "Body is only N words (minimum: 200)"
- 200-299 words: **warning** — "Body is N words (thin — consider expanding)"
- >= 300 words: pass

### Check 5: Source Attribution

Check the `sources:` field in frontmatter.

- Has at least 1 entry: pass
- Empty list or missing: **error** — "No sources cited"

For each source entry, check format:

- If URL (starts with `http`): pass
- If wikilink (contains `[[`): pass
- Otherwise: **warning** — "Source format unclear: <value>"

### Check 6: Wikilink Validity

Extract all `[[wikilinks]]` from the body text (not frontmatter).

For each wikilink, search for a matching file:

```
Glob for: wiki/**/<link-target>.md
Also check: raw/**/<link-target>.md
```

- If found: pass
- If not found: **warning** — "Broken wikilink: [[<target>]] — no matching file"

### Check 7: Related Articles

Check the related field (`suggested_related:` for raw/docs files, `related:` for wiki files).

- Has at least 2 entries: pass
- Has 1 entry: **warning** — "Only 1 related article — consider adding more"
- Has 0 entries or field missing: **warning** — "No related articles listed"

### Check 8: No Empty Sections

Scan each `## H2` heading. Check that there is at least one line of non-whitespace content before the next heading (or end of file).

- All sections have content: pass
- Any section is empty: **error** — "Empty section: ## <heading name>"

## Output Format

After running all checks, produce a structured report:

```
Structure Review: <file-path>

  Checks: <passed>/<total> passed

  Errors (must fix):
    - [Check 1] Missing required field: "suggested_domain"
    - [Check 3] No "Overview" section found
    - [Check 8] Empty section: "## Formula/Syntax"

  Warnings (consider fixing):
    - [Check 2] Title mismatch: frontmatter "Little's Law" vs heading "Littles Law"
    - [Check 4] Body is 280 words (thin — consider expanding)
    - [Check 6] Broken wikilink: [[capacity-planning-guide]] — no matching file

  Status: NEEDS_FIX
```

**Status values:**

- `PASS` — no errors, no warnings
- `WARN` — no errors, but has warnings
- `NEEDS_FIX` — has at least 1 error

## Error Handling

### File Not Found

```
File not found: <file-path>

Cannot run structure review on a file that doesn't exist.
```

### Not a Markdown File

```
File is not a .md file: <file-path>

Structure review only works on markdown files.
```

### No Frontmatter

```
No YAML frontmatter found in: <file-path>

The file must start with --- followed by YAML fields and a closing ---.
This is an error — all wiki and research documents require frontmatter.

Status: NEEDS_FIX
```

### Unrecognized File Type

If frontmatter exists but has neither `source_type` nor `maturity`:

```
Cannot determine file type from frontmatter in: <file-path>

Expected either:
  - source_type field (raw/docs research output)
  - maturity field (wiki compiled article)

Falling back to basic checks only (word count, sections, empty sections).
```

Run checks 2-4 and 8 only. Skip frontmatter-specific checks (1, 5, 7). Report as warning.

## Best Practices

1. **Read-only** — never modify the file being reviewed
2. **Report everything** — collect all issues before reporting, don't stop at first error
3. **Be specific** — include line numbers or field names in error messages
4. **Adapt to file type** — detect raw/docs vs wiki format automatically
5. **Severity matters** — errors block finalization, warnings are informational

## Related Skills

- **/research** — calls this skill to review drafts before finalizing
- **/ingest** — can call this skill to validate compiled articles
- **/compile** — can call this skill during validation step
- **/lint** — full wiki health check (broader scope than this skill)
