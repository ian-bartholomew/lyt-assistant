---
name: lint
description: This skill should be used when the user asks to "lint wiki", "check wiki health", "health check", "audit wiki", "validate wiki", "check for broken links", or wants to assess the quality and coverage of the wiki system. Performs structural and content-level audits.
version: 0.1.0
allowed-tools: [Read, Edit, Bash, Grep, Glob, AskUserQuestion]
---

# Lint Skill

Audit the wiki system across 10 dimensions: 8 structural checks plus 2 content-level checks — contradiction detection and investigation suggestions.

## Purpose

Maintain wiki quality by performing comprehensive audits that check index coverage, validate links, enforce frontmatter schema, detect orphaned and stale articles, find topic gaps, verify domain consistency, surface contradictions between articles in the same domain, and suggest high-value investigations. Ensures the wiki remains accurate, navigable, and intellectually consistent.

## When to Use

Invoke this skill when:

- User explicitly runs `/lint`
- User mentions linting, checking, auditing, or validating the wiki
- User wants to find broken links in the wiki
- User asks about wiki quality, health, or coverage
- After adding many new articles (to check if indexes need updates)
- As part of regular wiki maintenance

## Workflow Overview

1. **Scan wiki** — Build index of all wiki articles and domain indexes
2. **Index health** — Verify every article appears in at least one domain index
3. **Link validation** — Find broken wikilinks
4. **Frontmatter validation** — Check required fields on all wiki articles
5. **Orphan detection** — Find articles with no incoming links
6. **Staleness detection** — Flag articles with `last_compiled` > 90 days ago
7. **Gap analysis** — Find topics referenced but lacking their own page
8. **Domain consistency** — Verify domain tags match index membership
9. **Structure validation** — Check frontmatter block syntax, H1 heading, heading hierarchy, and empty sections
10. **Contradiction detection** — Scan same-domain articles for conflicting claims
11. **Investigation suggestions** — Surface high-value topics worth exploring
12. **Present report** — Combined findings grouped by domain
13. **Execute fixes** — Apply approved improvements
14. **Log results** — Append to `wiki/_log.md`

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

### Step 9: Structure Validation

Check each article's internal structure for correctness.

```
For each article:
  1. Verify frontmatter block syntax:
       - File begins with "---" on its own line
       - Frontmatter block is closed with "---" before any body content
  2. Verify a required H1 heading exists and matches the "title" frontmatter field
  3. Verify heading hierarchy has no skipped levels (e.g., H1 → H3 without H2)
  4. Check for empty sections — headings immediately followed by the next heading
       with no content between them
```

**Report:**

```
Structure Validation:
  Total articles: 47
  Valid: 43
  Issues: 4

  Structure issues:
  - wiki/concepts/backpressure.md: frontmatter block not closed (missing closing "---")
  - wiki/guides/incident-response.md: H1 heading "Incident Response Guide" does not match title "Incident Response"
  - wiki/concepts/slo-burn-rate.md: skipped heading level (H1 → H3 at line 18, no H2 between them)
  - wiki/company/deploy-pipeline.md: empty section "## Rollback Procedure" (no content before next heading)
```

### Step 10: Contradiction Detection

Scan articles in the same domain for conflicting claims. Look for:

- Different definitions of the same term
- Conflicting recommendations ("always use X" vs "avoid X")
- Inconsistent thresholds or numbers
- Contradictory cause-effect claims

**Method:**

```
For each domain with 2+ articles:
  Read all article bodies in that domain
  Identify articles that discuss the same topic, term, or threshold
  Compare the claims:
    - Numerical thresholds (e.g., "50% budget" vs "75% budget")
    - Directives (e.g., "always X" / "never X" / "avoid X")
    - Definitions (e.g., two different definitions of the same term)
    - Cause-effect (e.g., "X causes Y" vs "X prevents Y")
  Flag high-confidence contradictions (direct numerical or directive conflicts)
  Flag medium-confidence contradictions (semantic conflicts requiring interpretation)
```

Auto-fix: None — contradictions require human judgment.

**Report:**

```
Contradiction Detection:
  Domains scanned: 6
  Potential contradictions: 2

  Contradictions:
  - wiki/concepts/error-budget-policy.md vs wiki/concepts/slo-burn-rate.md
    Topic: error budget exhaustion threshold
    Article 1 claims: "halt deployments at 50% budget consumed"
    Article 2 claims: "halt deployments at 75% budget consumed"
    Confidence: high (direct numerical contradiction)

  - wiki/guides/incident-response.md vs wiki/company/on-call-runbook.md
    Topic: escalation timing
    Article 1 claims: "page secondary on-call after 15 minutes unacknowledged"
    Article 2 claims: "escalate to team lead after 10 minutes unacknowledged"
    Confidence: medium (similar directive, conflicting numbers)
```

### Step 11: Investigation Suggestions

Based on gaps, stubs, and domain coverage, surface high-value topics worth investigating.

**Criteria:**

- **High-value gaps**: Topics referenced by 3+ articles but lacking a page
- **Stale stubs**: Stubs with `last_compiled` older than 30 days (stubs signal intent; long-stale stubs signal neglect)
- **Under-represented domains**: Domains with fewer articles than cross-references suggest they warrant

**Method:**

```
For each gap from Step 7:
  Count how many articles reference it
  If count >= 3: flag as high-value gap

For each article with maturity: stub:
  Calculate days since last_compiled
  If > 30 days: flag as stale stub

For each domain:
  Count articles in domain
  Count cross-references into domain from other domains
  If cross-references >> articles: flag as under-represented
```

**Report:**

```
Investigation Suggestions:
  High-value gaps: 2
  Stale stubs: 2
  Under-represented domains: 1

  Suggested topics to investigate:
  - "error-budget-policy" — referenced by 4 articles, no page exists (high priority)
  - "rate-limiting" — referenced by 3 articles, no page exists
  - wiki/concepts/canary-deployment.md — stub created 45 days ago, never fleshed out
  - wiki/concepts/feature-flag-rollout.md — stub created 62 days ago, never fleshed out
  - Domain "resilience" — 3 articles but 12 inbound cross-references; likely under-documented
```

### Step 12: Present Combined Report

Combine all findings with structural and content sections:

```
Wiki Lint — 2026-04-21

Overall:  43/47 articles healthy (91%)

  Structural:
    Index Health:      43/47 indexed
    Link Validation:   196/203 links valid (7 broken)
    Frontmatter:       41/47 valid (6 issues)
    Orphans:           8 articles with no incoming links
    Staleness:         7 articles stale (> 90 days)
    Gaps:              5 topics need pages
    Consistency:       7 domain mismatches
    Structure:         4 articles with structural issues

  Content:
    Contradictions:    2 potential (review needed)
    Investigations:    5 topics suggested

--- By Domain ---

sre (18 articles):
  Broken links: 2
  Stale: 3
  Orphans: 1
  Gaps: error-budget-policy, rate-limiting
  Contradictions: 1 (error-budget-policy vs slo-burn-rate)

observability (12 articles):
  All healthy

resilience (8 articles):
  Unindexed: 1
  Broken links: 1
  Under-represented: 3 articles, 12 inbound cross-references

[... other domains ...]

Actions:
A) Auto-fix all (add to indexes, create stubs, fix frontmatter)
B) Fix critical issues only (broken links, missing indexes)
C) Review each issue individually
D) Review contradictions
E) Start suggested investigations
F) Generate report only (no changes)
```

Use **AskUserQuestion** to present this report and prompt the user for an action.

### Step 13: Execute Fixes

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
last_compiled: 2026-04-21
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

#### Auto-fix: Repair Domain Mismatches

For each domain mismatch:

- If article claims a domain but isn't in the index: add the article to that domain index
- If article is in an index but doesn't claim that domain: update the frontmatter `domain:` field to include it

#### Manual Review (Option C)

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

#### Review Contradictions (Option D)

Walk through each contradiction pair:

```
Contradiction 1 of 2:
  wiki/concepts/error-budget-policy.md vs wiki/concepts/slo-burn-rate.md
  Topic: error budget exhaustion threshold
  Article 1: "halt deployments at 50% budget consumed"
  Article 2: "halt deployments at 75% budget consumed"

  Actions:
  A) Edit error-budget-policy.md to reconcile
  B) Edit slo-burn-rate.md to reconcile
  C) Flag both articles with a contradiction note
  D) Skip (leave as-is)
```

#### Start Suggested Investigations (Option E)

For each suggested investigation topic, present options:

```
Investigation 1 of 5:
  Topic: "error-budget-policy" (referenced by 4 articles)

  Actions:
  A) Create stub now (quick placeholder)
  B) Run /research on this topic
  C) Skip
```

### Step 14: Log Results

Append results to `wiki/_log.md`:

```markdown
## [2026-04-21] lint | Wiki Health Check

- **Articles scanned:** 47
- **Structural issues:** 25 found, 21 fixed
- **Contradictions:** 2 potential (flagged)
- **Investigations suggested:** 5 topics
- **Remaining:** 4 (manual review needed)
- Breakdown:
  - Index: 4 unindexed → 4 added to indexes
  - Links: 7 broken → 5 stubs created, 2 skipped
  - Frontmatter: 6 invalid → 6 fixed
  - Orphans: 8 detected → flagged for review
  - Stale: 7 articles → flagged for recompilation
  - Gaps: 5 topics → 5 stubs created
  - Consistency: 7 mismatches → 7 resolved
  - Structure: 4 issues → flagged for manual review
  - Contradictions: 2 flagged → awaiting human review
  - Investigations: 5 suggested → 1 stub created, 4 queued
```

## Special Cases

### Healthy Wiki

```
Wiki Lint — 2026-04-21

All 47 articles healthy.

  Structural:
    Index Health:      47/47 indexed
    Link Validation:   203/203 links valid
    Frontmatter:       47/47 valid
    Orphans:           0
    Staleness:         0 stale
    Gaps:              0
    Consistency:       All domains consistent
    Structure:         47/47 valid

  Content:
    Contradictions:    0 detected
    Investigations:    0 suggested

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

Re-running lint...
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

The YAML frontmatter may be malformed. Skipping this file and flagging for manual review.
```

### Contradiction Scan Fails

```
Contradiction scan could not complete for domain "sre" — too many articles to compare in one pass.

Scanning in batches by subdomain...
```

## Best Practices

1. **Run regularly** — Weekly or after bulk wiki changes
2. **Prioritize broken links** — These degrade navigation immediately
3. **Fix frontmatter first** — Valid metadata enables all other checks
4. **Review orphans carefully** — Some may be intentionally standalone
5. **Address staleness** — Stale articles erode trust in the wiki
6. **Fill gaps** — Even stubs are better than broken links
7. **Keep domains consistent** — Tags and indexes must agree
8. **Never auto-fix contradictions** — Always require human judgment on conflicting claims
9. **Prioritize high-value investigations** — Topics referenced by 3+ articles are likely foundational
10. **Log every run** — The wiki log provides audit history
11. **Auto-fix when safe** — Index additions and stub creation are low-risk
12. **Manual review when uncertain** — Domain changes and deletions need judgment

## Usage Examples

### Example 1: Full Audit with Auto-fix

```
User: /lint

Wiki Lint — 2026-04-21

Overall:  43/47 articles healthy (91%)

  Structural:
    Index Health:      43/47 indexed
    ...

  Content:
    Contradictions:    2 potential (review needed)
    Investigations:    5 topics suggested

Actions:
A) Auto-fix all
...

[User selects A]

Auto-fixing:
  ✓ Added 4 articles to domain indexes
  ✓ Created 5 stubs for broken links
  ✓ Fixed 6 frontmatter issues
  ✓ Resolved 7 domain mismatches
  ✗ Structure issues flagged (require manual review)
  ✗ Contradictions skipped (require human judgment)

Remaining:
  - 2 contradictions flagged for review
  - 8 orphans flagged for review

Logged to: wiki/_log.md
```

### Example 2: Contradiction Review

```
User: /lint
[User selects D — Review contradictions]

Contradiction 1 of 2:
  wiki/concepts/error-budget-policy.md vs wiki/concepts/slo-burn-rate.md
  Topic: error budget exhaustion threshold
  Article 1: "halt deployments at 50% budget consumed"
  Article 2: "halt deployments at 75% budget consumed"

  Actions:
  A) Edit error-budget-policy.md to reconcile
  B) Edit slo-burn-rate.md to reconcile
  C) Flag both articles with a contradiction note
  D) Skip

[User selects C]

Added contradiction note to both articles.
```

### Example 3: Starting Investigations

```
User: /lint
[User selects E — Start suggested investigations]

Investigation 1 of 5:
  Topic: "error-budget-policy" (referenced by 4 articles)

  Actions:
  A) Create stub now
  B) Run /research on this topic
  C) Skip

[User selects B]

Launching /research for "error-budget-policy"...
```

### Example 4: Report Only

```
User: check wiki health

[User selects F — Generate report only]

Report saved to wiki/_log.md. No changes made.
```

## Related Skills

- **/ingest** — Process raw sources into wiki articles
- **/discover-links** — Find connections between wiki articles
- **/create-note** — Create wiki articles for detected gaps
- **/archive-project** — Extract project knowledge into wiki
- **/research** — Research a topic and create a wiki article

## Summary

The lint skill performs comprehensive 10-dimension audits of the wiki system. Eight structural checks (index coverage, link validity, frontmatter, orphans, staleness, gaps, domain consistency, structure) are paired with two content-level checks: contradiction detection (scanning same-domain articles for conflicting claims, thresholds, or directives) and investigation suggestions (surfacing high-value topics referenced by multiple articles but lacking a page). Provides interactive fixing with a combined report, logs all results to `wiki/_log.md`, and can auto-fix low-risk issues while flagging contradictions for human judgment.
