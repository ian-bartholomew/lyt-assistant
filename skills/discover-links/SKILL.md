---
name: discover-links
description: This skill should be used when the user asks to "discover links", "find missing connections", "find missing links", "connect notes", "link discovery", "find related articles", or wants to identify relationships between existing wiki articles that aren't currently linked.
version: 0.2.0
allowed-tools: [Read, Edit, Grep, Glob, AskUserQuestion]
---

# Discover Links Skill

Find missing connections between wiki articles by analyzing shared topics and suggesting `related:` frontmatter additions, grouped by domain.

## Purpose

Improve wiki connectivity by discovering articles that share topics but don't reference each other. Suggests additions to the `related:` frontmatter field and cross-references in domain indexes. Groups suggestions by domain for efficient review.

## When to Use

Invoke this skill when:

- User explicitly runs `/discover-links`
- User mentions finding, discovering, or creating connections
- User wants to improve wiki linking
- User asks about orphaned or under-connected articles
- After adding new wiki articles (to connect new content)

## Workflow Overview

1. **Scan wiki** - Build topic index for all articles
2. **Find opportunities** - Identify shared topics without links
3. **Group by domain** - Organize suggestions by domain
4. **Present interactively** - Allow review and selection
5. **Update frontmatter** - Add approved `related:` entries
6. **Check index coverage** - Suggest domain index cross-references

## Process Flow

### Step 1: Scan Wiki and Build Topic Index

Get all wiki articles:

```bash
# Get all markdown files in wiki/ (excluding indexes, log, attachments)
ARTICLES=$(find wiki/ -name "*.md" \
  -not -path "wiki/_indexes/*" \
  -not -path "wiki/_attachments/*" \
  -not -path "wiki/_log.md" \
  -not -path "wiki/_index.md" \
  -type f | sort)
```

For each article, extract:

- **Frontmatter fields:** `title`, `domain`, `related`, `maturity`
- **Existing wikilinks:** All `[[kebab-case-target]]` references in body
- **Existing related:** All entries in `related:` frontmatter list
- **Key topics:** Extract from title, headings, body content (technical terms, concepts)

Build a topic-to-articles mapping:

```
Topic: "circuit-breaker" → [circuit-breaker-pattern.md, resilience-patterns.md, api-gateway-patterns.md]
Topic: "error-budget" → [error-budget-policy.md, slo-burn-rate.md, reliability-targets.md]
Topic: "terraform" → [terraform-state-migration.md, infrastructure-as-code.md, deploy-pipeline.md]
```

### Step 2: Find Connection Opportunities

For each topic, find article pairs that:

1. **Share the topic** (both mention it in title, headings, or body)
2. **Don't link to each other** (neither has the other in `related:` or body wikilinks)
3. **Aren't the same file**

```
For each topic:
  For each pair of articles sharing this topic:
    Check if article-a has [[article-b]] in related: or body
    Check if article-b has [[article-a]] in related: or body
    If neither links to the other: flag as connection opportunity
```

### Step 3: Group Suggestions by Domain

Cluster related suggestions using the `domain:` frontmatter of involved articles:

```
Domain: sre (12 connections)
  - circuit-breaker-pattern ↔ bulkhead-pattern (shared: resilience, fault-tolerance)
  - slo-burn-rate ↔ error-budget-policy (shared: slo, reliability)
  - incident-response ↔ postmortem-template (shared: incidents)
  [... 9 more ...]

Domain: observability (5 connections)
  - grafana-dashboard-setup ↔ prometheus-queries (shared: monitoring, metrics)
  - distributed-tracing ↔ opentelemetry-setup (shared: tracing)
  [... 3 more ...]

Domain: infrastructure (3 connections)
  - terraform-state-migration ↔ infrastructure-as-code (shared: terraform)
  [... 2 more ...]
```

### Step 4: Rank and Score

Score each suggestion:

- **High confidence:** Topic appears in headings or title of both articles; articles share multiple topics; articles share domain tags
- **Medium confidence:** Topic appears in body of both articles; single shared topic; related domains
- **Low confidence:** Weak topic overlap; different domains

Sort domains by:

1. Total connections in domain
2. Average confidence of connections
3. Number of high-confidence suggestions

### Step 5: Present Grouped Suggestions

Show top domains first:

```
Scanning wiki for connection opportunities...

Found 20 potential connections across 4 domains:

--- Domain: sre (12 connections) ---

High confidence:
1. [[circuit-breaker-pattern]] ↔ [[bulkhead-pattern]]
   Shared topics: resilience, fault-tolerance, microservices
   Neither article references the other.

2. [[slo-burn-rate]] ↔ [[error-budget-policy]]
   Shared topics: slo, reliability, error-budget
   Neither article references the other.

Medium confidence:
3. [[incident-response]] ↔ [[postmortem-template]]
   Shared topics: incidents
   incident-response has no related: field.

[... more ...]

Actions for sre domain:
A) Add all 12 connections to related: frontmatter
B) Review individually
C) Skip domain
```

### Step 6: Handle User Selection

#### Option A: Apply All in Domain

For each connection pair, add bidirectional `related:` entries:

```
Applying 12 connections in sre domain...

Updated related: frontmatter:
  wiki/concepts/circuit-breaker-pattern.md — added [[bulkhead-pattern]]
  wiki/concepts/bulkhead-pattern.md — added [[circuit-breaker-pattern]]
  wiki/concepts/slo-burn-rate.md — added [[error-budget-policy]]
  wiki/concepts/error-budget-policy.md — added [[slo-burn-rate]]
  [...]

12 connections applied (24 related: entries added).
```

#### Option B: Review Individually

Present each suggestion one by one:

```
Connection 1 of 12 (sre domain):

  [[circuit-breaker-pattern]] ↔ [[bulkhead-pattern]]

  Shared topics: resilience, fault-tolerance, microservices

  circuit-breaker-pattern.md current related:
    - "[[retry-pattern]]"
    - "[[timeout-pattern]]"

  bulkhead-pattern.md current related:
    - "[[load-shedding]]"

  Add bidirectional link?
  A) Yes — add to both
  B) One-way only (A → B)
  C) One-way only (B → A)
  D) Skip
```

#### Option C: Skip Domain

Move to next domain.

### Step 7: Update Frontmatter

For each approved connection, update the `related:` field in YAML frontmatter:

```yaml
# Before
related:
  - "[[retry-pattern]]"
  - "[[timeout-pattern]]"

# After
related:
  - "[[retry-pattern]]"
  - "[[timeout-pattern]]"
  - "[[bulkhead-pattern]]"
```

Use the Edit tool to modify frontmatter. Preserve existing entries. Use kebab-case wikilinks.

**Verify no duplicates:**

```
Before adding [[bulkhead-pattern]] to circuit-breaker-pattern.md:
  Check related: field does not already contain [[bulkhead-pattern]]
  Check body does not already contain [[bulkhead-pattern]]
  If duplicate found: skip silently
```

**Handle missing related: field:**

If an article has no `related:` field in frontmatter, add it:

```yaml
# Before
---
title: Incident Response
domain: [sre]
maturity: mature
confidence: high
last_compiled: 2026-03-15
---

# After
---
title: Incident Response
domain: [sre]
maturity: mature
confidence: high
related:
  - "[[postmortem-template]]"
last_compiled: 2026-03-15
---
```

### Step 8: Check Domain Index Cross-References

After updating article frontmatter, check if domain indexes should be updated:

```
Domain index cross-reference check:

  wiki/_indexes/resilience.md:
    Contains [[circuit-breaker-pattern]] but not [[bulkhead-pattern]]
    Suggest adding [[bulkhead-pattern]] to resilience index? [Y/n]

  wiki/_indexes/sre.md:
    Both articles already present. No change needed.
```

### Step 9: Report Summary

After processing all domains:

```
Link Discovery Complete

  Domains reviewed: 4
  Connections added: 18 (36 related: entries)
  Articles updated: 22
  Index updates suggested: 3

  By domain:
  - sre: 12 connections
  - observability: 3 connections
  - infrastructure: 2 connections
  - company: 1 connection

  Next steps:
  - Run /check-moc-health to verify wiki health
  - Review newly connected articles in Obsidian graph view
```

## Topic Extraction Logic

### Identify Topics from Articles

Extract topics using multiple signals:

1. **Title:** Split kebab-case filename into terms
2. **Frontmatter domain:** Use as topic category
3. **Headings:** Extract H2/H3 heading text
4. **Body keywords:** Match against known technical term patterns
5. **Existing related:** Leverage existing connections to infer topics

### Co-occurrence Analysis

Find terms that frequently appear together across articles:

```
For each pair of terms:
  Count how many articles contain both terms
  High co-occurrence (3+ articles) → strong thematic connection
  Use co-occurrence to boost confidence of connection suggestions
```

### Filter Low-Quality Suggestions

Skip suggestions if:

- Topic appears only once in passing in one of the articles
- Articles are in completely different domains with no overlap
- One article already has 10+ entries in `related:`
- Both articles have `maturity: stub` (stubs linking to stubs adds noise)

## Special Cases

### No Missing Links Found

```
No missing connections found.

Your wiki is well-linked.

Stats:
- Total articles: 47
- Average related: entries per article: 3.8
- Well-connected: 94%
```

### Too Many Suggestions

If more than 40 suggestions:

```
Found 52 potential connections across 6 domains.

Options:
A) Show high-confidence only (18 connections)
B) Process one domain at a time
C) Show all (will take a while)
```

### Orphaned Articles (No Links At All)

Detect articles with zero incoming or outgoing links:

```
Found 3 orphaned articles (no links in or out):

- wiki/concepts/backpressure.md
  Domain: [sre, resilience]
  No related: field, no incoming wikilinks

- wiki/guides/log-aggregation-setup.md
  Domain: [observability]
  No related: field, no incoming wikilinks

Options:
A) Find connections for orphans (prioritized search)
B) Flag for manual review
C) Skip
```

### Articles with Extensive Links

If an article already has many related entries:

```
wiki/concepts/microservices-patterns.md already has 12 related: entries.

Adding more may reduce signal quality.
Only suggest high-confidence connections? [Y/n]
```

## Error Handling

### Read Permission Errors

```
Cannot read wiki/concepts/locked-file.md

Skipping this file. Continue? [Y/n]
```

### Frontmatter Parse Error

```
Cannot parse frontmatter in wiki/concepts/malformed.md

Skipping this file from link discovery.
Flag for /check-moc-health to investigate? [Y/n]
```

### Empty Wiki

```
No wiki articles found in wiki/

The wiki is empty. Start by creating articles with /create-note
or by archiving a project with /archive-project (which extracts knowledge).
```

## Best Practices

1. **Start with high-confidence suggestions** - Quick wins that clearly belong
2. **Review before applying** - Especially for batch operations
3. **Prefer bidirectional links** - If A relates to B, B relates to A
4. **Don't over-link** - Quality over quantity in `related:` fields
5. **Group by domain** - Easier to review thematically
6. **Use kebab-case wikilinks** - Consistent with wiki naming convention
7. **Check index coverage** - New connections may warrant index updates
8. **Preserve existing entries** - Never remove existing `related:` entries
9. **Skip stubs linking to stubs** - Wait until articles have substance
10. **Run after adding content** - Best time is after batch article creation

## Related Skills

- **/classify-inbox** - Add links when processing new raw items
- **/check-moc-health** - Find orphans and validate wiki structure
- **/create-note** - Create articles for detected gaps
- **/archive-project** - Extract project knowledge with proper linking

## Summary

The discover-links skill finds missing connections between wiki articles by analyzing shared topics and suggesting `related:` frontmatter additions. Groups suggestions by domain for efficient review, supports bidirectional linking, and checks domain index coverage. Improves wiki connectivity systematically without touching article body content.
