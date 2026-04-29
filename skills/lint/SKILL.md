---
name: lint
description: This skill should be used when the user asks to "lint wiki", "check wiki health", "health check", "audit wiki", "validate wiki", "check for broken links", or wants to assess the quality and coverage of the wiki system.
version: 0.3.0
allowed-tools: [Read, Edit, Bash, Grep, Glob, AskUserQuestion]
---

# Wiki Health Check Skill

Audit the wiki system by validating indexes, checking links, enforcing frontmatter, detecting orphans and staleness, finding gaps, verifying domain consistency, auditing maturity/confidence accuracy, detecting duplicate content, and validating source attribution.

## Purpose

Maintain wiki quality by performing comprehensive audits that check index coverage, validate links, enforce frontmatter schema, detect orphaned and stale articles, find topic gaps, and verify domain consistency. Ensures the wiki remains an accurate, navigable knowledge base.

## When to Use

Invoke this skill when:

- User explicitly runs `/lint`
- User mentions checking, linting, auditing, or validating the wiki
- User wants to find broken links in the wiki
- User asks about wiki quality, health, or coverage
- After adding many new articles (to check if indexes need updates)
- As part of regular wiki maintenance

## Architecture

This skill has two layers:

1. **`lint.py`** — The Python script at `~/Dev/claude-memory-compiler/scripts/lint.py` that runs deterministic checks against the actual files. It produces a report at `reports/lint-YYYY-MM-DD.md`. This is the source of truth for structural issues (broken links, orphans, stale articles, missing backlinks, sparse articles).

2. **This skill** — Reads the lint report, runs additional checks that `lint.py` doesn't cover (maturity audit, duplicate detection, source attribution, index/domain consistency), and presents interactive fixes for all issues.

**Always run `lint.py` first**, then layer on the additional checks. Never re-implement what lint.py already does — read its output instead.

## Workflow Overview

1. **Run lint.py** - Execute the Python script to get the structural report
2. **Read lint report** - Parse the generated report for errors, warnings, suggestions
3. **Additional checks** - Run checks lint.py doesn't cover (index health, domain consistency, maturity audit, duplicate detection, source attribution)
4. **Present combined report** - Interactive findings grouped by severity and domain
5. **Execute fixes** - Apply approved improvements
6. **Log results** - Append to `wiki/_log.md`

## Process Flow

### Step 1: Run lint.py

Run the Python lint script to get the baseline structural report:

```bash
uv run --directory ~/Dev/claude-memory-compiler python ~/Dev/claude-memory-compiler/scripts/lint.py --structural-only
```

The script resolves the vault location from `scripts/vault-config.json` (currently `~/Documents/Work`), so it works regardless of your current working directory.

This runs 6 checks:

- Broken links (errors)
- Orphan pages (warnings)
- Orphan sources / uncompiled logs (warnings)
- Stale articles / source hash changes (warnings)
- Missing backlinks (suggestions)
- Sparse articles <200 words (suggestions)

The report is saved to `~/Dev/claude-memory-compiler/reports/lint-YYYY-MM-DD.md`.

### Step 2: Read and Parse Lint Report

Read the latest lint report:

```bash
REPORT=$(ls -t ~/Dev/claude-memory-compiler/reports/lint-*.md | head -1)
```

Parse the report into structured categories:

- Count errors, warnings, suggestions
- Group broken links by target (e.g., `[[sli-slo-sla]]` broken in 8 articles → one fix creates the article)
- Group orphan pages by domain
- Identify auto-fixable missing backlinks

Present a summary before diving into additional checks:

```
Lint Report Summary (from lint.py):
  96 errors (broken links)
  34 warnings (orphans, stale, uncompiled)
  569 suggestions (missing backlinks, sparse articles)

  Top broken link targets:
    [[sli-slo-sla]] — referenced by 12 articles (creating this article fixes 12 errors)
    [[core-infrastructure]] — referenced by 5 articles
    [[monitoring-and-integrations]] — referenced by 5 articles
    [[cloudflare-zones-and-waf]] — referenced by 7 articles
    [[fes-service-deployment]] — referenced by 6 articles

  Continue with additional checks? [Y/n]
```

### Step 3: Additional Checks (beyond lint.py)

These checks cover what `lint.py` does NOT check. Run them after reading the lint report.

#### 3a. Index Health

Verify every wiki article appears in at least one domain index file (`wiki/_indexes/*.md`).

```
For each article in wiki/:
  Check if article slug appears as a [[wikilink]] in any file under wiki/_indexes/
  If not found: flag as "unindexed"
```

#### 3b. Domain Consistency

Verify that each article's `domain:` frontmatter tags match the domain indexes it appears in.

```
For each article:
  Get domain tags from frontmatter (e.g., [sre, resilience])
  Get which indexes actually list this article
  Flag mismatches:
    - Article claims domain "resilience" but does not appear in resilience index
    - Article appears in "observability" index but domain field doesn't include it
```

#### 3c. Frontmatter Validation

`lint.py` does not check frontmatter. All wiki articles must have these required fields:

- `title` (string)
- `domain` (list of strings)
- `maturity` (one of: stub, draft, developing, mature)
- `confidence` (one of: low, medium, high)
- `compiled_from` (list of source paths, e.g., `["raw/daily/2026-04-21.md"]`)
- `related` (list of wikilinks, minimum 2 entries)
- `last_compiled` (date in YYYY-MM-DD format)

#### 3d. Maturity/Confidence Audit

Check whether each article's `maturity` and `confidence` levels accurately reflect its content depth.

```
For each article:
  Count words in body (excluding frontmatter)
  Count number of compiled_from sources
  Compare against maturity/confidence:

  Flag if:
    - maturity is "draft" but word count > 500 AND sources >= 2
      → Should be at least "developing"
    - maturity is "developing" or "mature" but word count < 200
      → Should be "stub"
    - maturity is "stub" but word count > 300
      → Should be at least "draft"
    - confidence is "medium" or "high" but sources < 2
      → Confidence may be overstated
    - confidence is "low" but sources >= 3 and maturity is "mature"
      → Confidence is likely understated
```

**Report:**

```
Maturity/Confidence Audit:
  Accurate: 38
  Mismatches: 9

  Maturity mismatches:
  - wiki/concepts/galls-law.md: marked "draft" (420 words, 2 sources) → suggest "developing"
  - wiki/company/deploy-pipeline.md: marked "developing" (89 words) → suggest "stub"
  - wiki/concepts/rate-limiting.md: marked "draft" (312 words) → suggest "draft" (OK, borderline)

  Confidence mismatches:
  - wiki/concepts/datadog-idp.md: marked "medium" (3177 words, 5 sources) → suggest "high"
  - wiki/learning/steve-jobs-highlights.md: marked "medium" (17 words, 1 source) → suggest "low"
```

#### 3e. Duplicate Content Detection

Find articles with overlapping `compiled_from` sources, which may indicate duplicate or near-duplicate content.

```
For each pair of articles:
  Compare their compiled_from lists
  Calculate overlap: shared_sources / min(sources_a, sources_b)
  If overlap > 50%: flag for merge review

Also check for articles with very similar titles:
  Normalize titles (lowercase, remove common words)
  Flag pairs with > 70% token overlap
```

**Report:**

```
Duplicate Content Detection:
  Unique articles: 45
  Potential duplicates: 2 pairs

  Overlapping sources:
  - wiki/concepts/ssm-parameter-self-service.md (7 sources)
    wiki/concepts/datadog-idp.md (5 sources)
    Shared sources: 3 (60% overlap)
    → Review: merge SSM section out of datadog-idp into ssm-parameter-self-service?

  Similar titles:
  - wiki/concepts/terraform-recommended-practices.md
    wiki/concepts/terraform-operations-best-practices.md
    Title similarity: 75%
    → Review: are these distinct topics or should they merge?
```

#### 3f. Source Attribution Quality

Validate that `compiled_from` paths follow the standard format and that index metadata is consistent.

```
For each article:
  Check compiled_from entries use the standard raw/<type>/<file> format:
    Valid: "raw/daily/2026-04-21.md", "raw/clippings/karpathy-tweet.md"
    Invalid: "daily/2026-04-21.md" (missing raw/ prefix)
    Invalid: "#fes-platform-support Slack" (informal reference, not a file path)

  If an article has a "sources:" field instead of "compiled_from:":
    Flag as using deprecated field name

Check _index.md metadata:
  Parse article count from header (e.g., "Total articles: 186")
  Count actual articles in wiki/
  Flag if counts don't match

Check domain index article counts:
  For each domain index, count listed articles
  Compare against articles with that domain in frontmatter
  Flag mismatches
```

**Report:**

```
Source Attribution:
  Valid compiled_from: 40
  Issues: 7

  Format issues:
  - wiki/concepts/fes-platform-support-patterns.md: informal source "#fes-platform-support Slack (2026-04-28 threads)"
    → Should reference raw/support_learnings/2026-04-28.md
  - wiki/concepts/terraform-tagging-strategy.md: has both "sources:" and "compiled_from:" fields
    → Migrate "sources:" to "compiled_from:" and remove duplicate

  Index metadata:
  - _index.md says "Total articles: 186" but actual count is 193
    → Update _index.md header
  - _indexes/sre.md lists 89 articles but 95 articles have domain: sre
    → 6 articles missing from sre index
```

### Step 4: Present Combined Report

Combine lint.py findings with additional check findings into a single report:

```
Wiki Health Check — 2026-04-29

=== From lint.py ===
  Broken links:      96 errors
  Orphan pages:      21 warnings
  Orphan sources:    2 warnings (uncompiled logs)
  Stale articles:    11 warnings
  Missing backlinks: 551 suggestions
  Sparse articles:   18 suggestions (<200 words)

  Top broken link targets (creating these fixes the most errors):
    [[sli-slo-sla]] — 12 articles      (create stub → fix 12 errors)
    [[cloudflare-zones-and-waf]] — 7    (create stub → fix 7 errors)
    [[fes-service-deployment]] — 6
    [[core-infrastructure]] — 5
    [[monitoring-and-integrations]] — 5

=== Additional checks ===
  Index health:      8 unindexed articles
  Domain consistency: 7 mismatches
  Frontmatter:       6 missing/invalid fields
  Maturity audit:    9 mismatches
  Duplicates:        2 potential pairs
  Attribution:       7 source format issues

Actions:
A) Fix high-impact first (create top 5 stub articles → resolves ~40 broken links)
B) Auto-fix all safe issues (indexes, frontmatter, maturity, attribution)
C) Review each issue individually
D) Generate report only (no changes)
```

### Step 5: Execute Fixes

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

#### Auto-fix: Promote/Demote Maturity

For articles with maturity mismatches:

- Stub with >300 words → promote to `draft`
- Draft with >500 words + 2+ sources → promote to `developing`
- Developing/mature with <200 words → demote to `stub`

Present each change for approval before applying.

#### Auto-fix: Standardize Source Attribution

- Rename `sources:` field to `compiled_from:` in articles using the deprecated name
- Prefix bare paths with `raw/` where missing (e.g., `daily/file.md` → `raw/daily/file.md`)
- Update `_index.md` article count to match reality

#### Auto-fix: Flag Duplicates for Manual Merge

Duplicates require human judgment — don't auto-merge. Instead:

```
Potential duplicate pair flagged:
  wiki/concepts/ssm-parameter-self-service.md
  wiki/concepts/datadog-idp.md (section 3.2)

  Action needed: manually review and decide which is the canonical article.
  The overlapping content should live in one place, with the other linking to it.
```

### Step 6: Log Results

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
  - Maturity: 9 mismatches → 7 promoted, 2 skipped
  - Duplicates: 2 pairs → flagged for manual merge
  - Attribution: 7 issues → 5 fixed, 2 need manual review
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

- **/compile** - Full compilation pipeline (runs targeted lint after ingestion)
- **/discover-links** - Find connections between wiki articles
- **/ingest** - Process raw items into wiki
- **/create-note** - Create wiki articles for detected gaps
- **/archive-project** - Extract project knowledge into wiki

## Summary

The wiki health check skill performs comprehensive audits of the wiki system by validating indexes, links, frontmatter, orphans, staleness, gaps, domain consistency, maturity/confidence accuracy, duplicate content, and source attribution quality. Provides interactive fixing with detailed reporting, logs all results to `wiki/_log.md`, and can auto-fix low-risk issues like missing index entries, stub creation, and maturity promotions.
