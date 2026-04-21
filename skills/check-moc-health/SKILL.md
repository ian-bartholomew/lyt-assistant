---
name: check-moc-health
description: This skill should be used when the user asks to "check wiki health", "lint wiki", "health check", "audit wiki", "validate wiki", "check MOC health", "analyze MOC", "validate MOC", "check MOC quality", "audit MOC", "check for broken links", or wants to assess the quality and coverage of the wiki system.
version: 0.2.0
allowed-tools: [Read, Edit, Bash, Grep, Glob, AskUserQuestion]
---

# Wiki Health Check Skill

Audit the wiki system by validating indexes, checking links, enforcing frontmatter, detecting orphans and staleness, finding gaps, and verifying domain consistency.

## Purpose

Maintain wiki quality by performing comprehensive audits that check index coverage, validate links, enforce frontmatter schema, detect orphaned and stale articles, find topic gaps, and verify domain consistency. Ensures the wiki remains an accurate, navigable knowledge base.

## When to Use

Invoke this skill when:

- User explicitly runs `/check-moc-health`
- User mentions checking, linting, auditing, or validating the wiki
- User wants to find broken links in the wiki
- User asks about wiki quality, health, or coverage
- After adding many new articles (to check if indexes need updates)
- As part of regular wiki maintenance

## Workflow Overview

1. **Scan wiki** - Build index of all wiki articles and domain indexes
2. **Index health** - Verify every article appears in at least one domain index
3. **Link validation** - Find broken wikilinks
4. **Frontmatter validation** - Check required fields on all wiki articles
5. **Orphan detection** - Find articles with no incoming links
6. **Staleness detection** - Flag articles with `last_compiled` > 90 days ago
7. **Gap analysis** - Find topics referenced but lacking their own page
8. **Domain consistency** - Verify domain tags match index membership
9. **Present report** - Interactive findings grouped by domain
10. **Execute fixes** - Apply approved improvements
11. **Log results** - Append to `wiki/_log.md`

## Process Flow

### Step 1: Scan Wiki

Build a complete picture of the wiki:

```bash
# Get all wiki articles (excluding indexes, log, and attachments)
ARTICLES=$(find wiki/ -name "*.md" \
  -not -path "wiki/_indexes/*" \
  -not -path "wiki/_attachments/*" \
  -not -path "wiki/_log.md" \
  -not -path "wiki/_index.md" \
  -type f | sort)

# Get all domain indexes
INDEXES=$(find wiki/_indexes/ -name "*.md" -type f | sort)
```

For each article, extract:

- Frontmatter fields (title, domain, maturity, confidence, related, last_compiled)
- All `[[wikilinks]]` in the body
- Filename (kebab-case slug)

For each domain index, extract:

- All `[[wikilinks]]` it contains
- Domain name (from filename or frontmatter)

### Step 2: Index Health

Verify every wiki article appears in at least one domain index.

```
For each article in wiki/:
  Check if article filename appears as a [[wikilink]] in any file under wiki/_indexes/
  If not found in any index: flag as "unindexed"
```

**Report:**

```
Index Health:
  Total articles: 47
  Indexed: 43
  Unindexed: 4

  Unindexed articles:
  - wiki/concepts/backpressure.md (domain: [sre, resilience])
  - wiki/guides/grafana-dashboard-setup.md (domain: [observability])
  - wiki/concepts/toil-budget.md (domain: [sre])
  - wiki/company/deploy-pipeline.md (domain: [infrastructure])
```

### Step 3: Link Validation

Check every `[[wikilink]]` in wiki articles resolves to an existing file.

```
For each article:
  Extract all [[link-target]] references
  For each link target:
    Search for a file matching "link-target.md" anywhere in the vault
    If not found: flag as broken link
```

**Report:**

```
Link Validation:
  Total wikilinks scanned: 203
  Valid: 196
  Broken: 7

  Broken links:
  - wiki/concepts/circuit-breaker-pattern.md line 23: [[rate-limiting]] (no file)
  - wiki/guides/incident-response.md line 15: [[escalation-matrix]] (no file)
  - wiki/concepts/slo-burn-rate.md line 8: [[error-budget-policy]] (no file)
  [... 4 more ...]
```

### Step 4: Frontmatter Validation

All wiki articles must have these required frontmatter fields:

- `title` (string)
- `domain` (list of strings)
- `maturity` (one of: stub, draft, mature, authoritative)
- `confidence` (one of: low, medium, high)
- `last_compiled` (date in YYYY-MM-DD format)

```
For each article:
  Parse YAML frontmatter
  Check each required field exists and has a valid value
  Flag any missing or invalid fields
```

**Report:**

```
Frontmatter Validation:
  Total articles: 47
  Valid: 41
  Issues: 6

  Frontmatter issues:
  - wiki/concepts/backpressure.md: missing "confidence" field
  - wiki/guides/grafana-dashboard-setup.md: missing "last_compiled" field
  - wiki/concepts/toil-budget.md: "maturity" has invalid value "wip" (expected: stub|draft|mature|authoritative)
  - wiki/company/deploy-pipeline.md: missing "domain" field
  [... 2 more ...]
```

### Step 5: Orphan Detection

Find wiki articles with no incoming links from other wiki articles or indexes.

```
For each article:
  Count how many other files contain [[article-slug]] as a wikilink
  If count == 0: flag as orphan
```

**Report:**

```
Orphan Detection:
  Total articles: 47
  Well-connected: 39
  Orphans (no incoming links): 8

  Orphaned articles:
  - wiki/concepts/backpressure.md (0 incoming links)
  - wiki/concepts/toil-budget.md (0 incoming links)
  [... 6 more ...]
```

### Step 6: Staleness Detection

Flag articles where `last_compiled` is more than 90 days ago.

```
For each article:
  Read last_compiled from frontmatter
  Calculate days since last_compiled
  If > 90 days: flag as stale
```

**Report:**

```
Staleness Detection:
  Fresh (< 30 days): 28
  Aging (30-90 days): 12
  Stale (> 90 days): 7

  Stale articles:
  - wiki/concepts/circuit-breaker-pattern.md (last compiled 2025-12-15 — 124 days ago)
  - wiki/guides/terraform-state-migration.md (last compiled 2025-11-20 — 149 days ago)
  [... 5 more ...]
```

### Step 7: Gap Analysis

Find topics that are referenced in wiki articles (as wikilinks or in `related:` frontmatter) but don't have their own page.

```
For each broken link or unresolved related entry:
  If the target looks like it belongs in wiki/ (kebab-case, topical name):
    Flag as a gap — a topic that should have its own article
```

**Report:**

```
Gap Analysis:
  Topic gaps detected: 5

  Topics referenced but lacking a page:
  - "rate-limiting" — referenced by 3 articles
  - "escalation-matrix" — referenced by 2 articles
  - "error-budget-policy" — referenced by 4 articles
  - "canary-deployment" — referenced by 1 article
  - "feature-flag-rollout" — referenced by 1 article
```

### Step 8: Domain Consistency

Verify that each article's `domain:` frontmatter tags match the domain indexes it appears in.

```
For each article:
  Get domain tags from frontmatter (e.g., [sre, resilience])
  Get which indexes actually list this article
  Flag mismatches:
    - Article claims domain "resilience" but does not appear in resilience index
    - Article appears in "observability" index but domain field doesn't include it
```

**Report:**

```
Domain Consistency:
  Consistent: 40
  Mismatches: 7

  Domain mismatches:
  - wiki/concepts/circuit-breaker-pattern.md
    Frontmatter domains: [sre, resilience]
    Indexed in: [sre]
    Missing from index: resilience

  - wiki/guides/grafana-dashboard-setup.md
    Frontmatter domains: [observability]
    Indexed in: [observability, infrastructure]
    Extra index: infrastructure (not in domain field)
```

### Step 9: Present Comprehensive Report

Combine all findings, grouped by domain:

```
Wiki Health Check — 2026-04-17

Overall:  43/47 articles healthy (91%)

  Index Health:      43/47 indexed
  Link Validation:   196/203 links valid (7 broken)
  Frontmatter:       41/47 valid (6 issues)
  Orphans:           8 articles with no incoming links
  Staleness:         7 articles stale (> 90 days)
  Gaps:              5 topics need pages
  Consistency:       7 domain mismatches

--- By Domain ---

sre (18 articles):
  Broken links: 2
  Stale: 3
  Orphans: 1
  Gaps: error-budget-policy, rate-limiting

observability (12 articles):
  All healthy

resilience (8 articles):
  Unindexed: 1
  Broken links: 1

[... other domains ...]

Actions:
A) Auto-fix all (add to indexes, create stubs for gaps, fix frontmatter)
B) Fix critical issues only (broken links, missing indexes)
C) Review each issue individually
D) Generate report only (no changes)
```

### Step 10: Execute Fixes

#### Auto-fix: Add Missing Articles to Indexes

For each unindexed article, add it to the appropriate domain index based on its `domain:` frontmatter:

```bash
# Add [[backpressure]] to wiki/_indexes/sre.md and wiki/_indexes/resilience.md
```

#### Auto-fix: Create Stubs for Broken Links

For each broken link that represents a gap, create a stub article:

```yaml
---
title: Rate Limiting
domain: [sre, resilience]
maturity: stub
confidence: low
related:
  - "[[circuit-breaker-pattern]]"
last_compiled: 2026-04-17
---

# Rate Limiting

*This article is a stub. It was auto-generated because 3 articles reference this topic.*

## Referenced By

- [[circuit-breaker-pattern]]
- [[load-shedding]]
- [[api-gateway-patterns]]
```

Place stubs in the appropriate wiki subfolder (concepts/, guides/, company/).

#### Auto-fix: Repair Frontmatter

For articles with missing fields, add defaults:

- Missing `confidence`: set to `low`
- Missing `last_compiled`: set to today's date
- Missing `domain`: infer from which index contains the article, or set to `[uncategorized]`
- Invalid `maturity`: prompt user to choose valid value

#### Manual Review

Walk through each issue one by one:

```
Issue 1 of 27:
  Unindexed: wiki/concepts/backpressure.md
  Domains: [sre, resilience]

  Actions:
  A) Add to sre and resilience indexes
  B) Skip
  C) Change domain tags
```

### Step 11: Log Results

Append results to `wiki/_log.md`:

```markdown
## [2026-04-17] lint | Wiki Health Check

- **Articles scanned:** 47
- **Issues found:** 27
- **Issues fixed:** 23
- **Remaining:** 4 (manual review needed)
- Breakdown:
  - Index: 4 unindexed → 4 added to indexes
  - Links: 7 broken → 5 stubs created, 2 skipped
  - Frontmatter: 6 invalid → 6 fixed
  - Orphans: 8 detected → flagged for review
  - Stale: 7 articles → flagged for recompilation
  - Gaps: 5 topics → 5 stubs created
  - Consistency: 7 mismatches → 7 resolved
```

## Special Cases

### Healthy Wiki

```
Wiki Health Check — 2026-04-17

All 47 articles healthy.

  Index Health:      47/47 indexed
  Link Validation:   203/203 links valid
  Frontmatter:       47/47 valid
  Orphans:           0
  Staleness:         0 stale
  Gaps:              0
  Consistency:       All domains consistent

No issues found. The wiki is in great shape.
```

### Empty Wiki

```
No wiki articles found in wiki/

The wiki is empty. Start by creating articles with /create-note
or by archiving a project with /archive-project (which extracts knowledge).
```

### No Domain Indexes

```
No domain indexes found in wiki/_indexes/

Creating default index structure...

Created:
- wiki/_indexes/sre.md
- wiki/_indexes/observability.md
- wiki/_indexes/infrastructure.md

Re-running health check...
```

### Too Many Issues

```
Found 83 issues across 47 articles.

Processing in stages:
A) Fix critical issues first (broken links, missing indexes)
B) Fix all automatically
C) Generate report for manual review
```

## Error Handling

### Wiki Directory Not Found

```
wiki/ directory not found.

The wiki system has not been initialized.
Create the wiki structure? [Y/n]
```

### Index File Corrupted

```
Cannot parse wiki/_indexes/sre.md — invalid markdown structure.

Options:
A) Rebuild index from article domain tags
B) Skip this index
C) Show file contents for manual review
```

### Frontmatter Parse Error

```
Cannot parse frontmatter in wiki/concepts/backpressure.md

The YAML frontmatter may be malformed. Skipping this file.
```

## Best Practices

1. **Run regularly** - Weekly or after bulk wiki changes
2. **Prioritize broken links** - These degrade navigation immediately
3. **Fix frontmatter first** - Valid metadata enables all other checks
4. **Review orphans carefully** - Some may be intentionally standalone
5. **Address staleness** - Stale articles erode trust in the wiki
6. **Fill gaps** - Even stubs are better than broken links
7. **Keep domains consistent** - Tags and indexes must agree
8. **Log every run** - The wiki log provides audit history
9. **Auto-fix when safe** - Index additions and stub creation are low-risk
10. **Manual review when uncertain** - Domain changes and deletions need judgment

## Related Skills

- **/discover-links** - Find connections between wiki articles
- **/classify-inbox** - Process raw items into wiki
- **/create-note** - Create wiki articles for detected gaps
- **/archive-project** - Extract project knowledge into wiki

## Summary

The wiki health check skill performs comprehensive audits of the wiki system by validating indexes, links, frontmatter, orphans, staleness, gaps, and domain consistency. Provides interactive fixing with detailed reporting, logs all results to `wiki/_log.md`, and can auto-fix low-risk issues like missing index entries and stub creation.
