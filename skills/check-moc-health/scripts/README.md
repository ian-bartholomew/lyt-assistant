# MOC Health Check Scripts

Bash scripts for analyzing the health of Maps of Content (MOCs) in your LYT vault.

## Overview

These scripts validate MOC structure, check link integrity, and identify opportunities for improvement.

## Scripts

### `check-all.sh` - Comprehensive Analysis
Runs all health checks and generates a complete report.

```bash
./scripts/moc-health/check-all.sh
```

**Output:**
- Structure analysis (heading hierarchy, sections, navigation)
- Link validation (broken links detection)
- Plain text items (potential wikilinks)
- Summary statistics

---

### `check-links.sh` - Link Validation
Validates all wikilinks and reports broken references.

```bash
# Check all MOCs
./scripts/moc-health/check-links.sh

# Check specific MOC
./scripts/moc-health/check-links.sh "100 - MOCs/SRE Concepts MOC.md"
```

**Output:**
- Total wikilinks per MOC
- Valid vs broken link count
- List of broken links with line numbers

---

### `check-plain-text.sh` - Plain Text Detection
Finds list items that could be converted to wikilinks.

```bash
# Check all MOCs
./scripts/moc-health/check-plain-text.sh

# Check specific MOC
./scripts/moc-health/check-plain-text.sh "100 - MOCs/Observability MOC.md"
```

**Output:**
- Plain text items (not wikilinked)
- Line numbers for easy location
- Suggestions for potential notes

---

### `check-structure.sh` - Structure Analysis
Analyzes MOC organization and structure.

```bash
# Check all MOCs
./scripts/moc-health/check-structure.sh

# Check specific MOC
./scripts/moc-health/check-structure.sh "100 - MOCs/Home.md"
```

**Output:**
- H1 heading count (should be 1)
- Section count (H2 headings)
- Frontmatter presence
- Related MOCs section
- Navigation to Home

---

## Usage Examples

### Quick Health Check
```bash
cd /path/to/vault
./scripts/moc-health/check-all.sh
```

### Check Links Only
```bash
./scripts/moc-health/check-links.sh
```

### Find Wikilink Opportunities
```bash
./scripts/moc-health/check-plain-text.sh
```

### Analyze Specific MOC
```bash
./scripts/moc-health/check-structure.sh "100 - MOCs/SRE Concepts MOC.md"
./scripts/moc-health/check-links.sh "100 - MOCs/SRE Concepts MOC.md"
./scripts/moc-health/check-plain-text.sh "100 - MOCs/SRE Concepts MOC.md"
```

---

## Environment Variables

### `VAULT_ROOT`
Override the vault root directory (defaults to current directory).

```bash
VAULT_ROOT=/path/to/vault ./scripts/moc-health/check-all.sh
```

---

## What Each Script Checks

### Link Validation (`check-links.sh`)
- ✅ All `[[wikilinks]]` resolve to actual files
- ✅ Searches in `100 - MOCs`, `200 - Notes`, `300 - Reference`
- ❌ Reports missing target files

### Plain Text Detection (`check-plain-text.sh`)
- Finds list items starting with `- [A-Z]`
- Filters out prose (descriptions with `: `, `—`, `...`)
- Suggests potential notes to create

### Structure Analysis (`check-structure.sh`)
- **H1 count:** Should be exactly 1
- **Sections:** Counts `## ` headings
- **Frontmatter:** Checks for YAML frontmatter
- **Related MOCs:** Validates cross-linking
- **Navigation:** Ensures link back to Home (except Home itself)

---

## Integration with LYT Assistant

These scripts are used by the `/lyt-assistant:check-moc-health` skill.

You can also call them directly:
```bash
# From command line
./scripts/moc-health/check-all.sh

# From Claude Code with Bash tool
Bash: cd /path/to/vault && ./scripts/moc-health/check-all.sh
```

---

## Expected MOC Structure

Good MOCs should have:

```markdown
---
tags: [moc, topic]
created: YYYY-MM-DD
---

# MOC Title

Brief description of what this MOC covers.

## Section 1
- [[Note 1]]
- [[Note 2]]

## Section 2
- [[Note 3]]
- [[Note 4]]

## Related MOCs
- [[Related MOC 1]]
- [[Related MOC 2]]

---

## Navigation

**Back to**: [[Home]]
```

---

## Troubleshooting

### "Permission denied"
```bash
chmod +x scripts/moc-health/*.sh
```

### "VAULT_ROOT not found"
Run from vault root or set `VAULT_ROOT`:
```bash
cd /path/to/vault
./scripts/moc-health/check-all.sh
```

Or:
```bash
VAULT_ROOT=/path/to/vault ./scripts/moc-health/check-all.sh
```

### "No MOCs found"
Ensure you're in the vault root and `100 - MOCs/` directory exists.

---

## Output Formats

All scripts output markdown-formatted text that can be:
- Viewed in terminal
- Saved to a file: `./check-all.sh > report.md`
- Piped to other tools: `./check-links.sh | grep "Broken"`

---

## Maintenance

Run these scripts:
- **Weekly:** During inbox processing
- **Monthly:** Full health check
- **Before MOC updates:** Validate structure
- **After bulk changes:** Ensure link integrity

---

## Related Skills

- `/lyt-assistant:check-moc-health` - Interactive MOC health analysis
- `/lyt-assistant:discover-links` - Find missing connections
- `/lyt-assistant:classify-inbox` - Process inbox items

---

**Created:** 2026-03-27
**Vault:** LYT Knowledge System
