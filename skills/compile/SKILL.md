---
name: compile
description: This skill should be used when the user asks to "compile", "compile sources", "compile raw", "run compilation", "process and compile", "full compile", or wants to run the complete compilation pipeline that ingests sources, validates articles, and discovers links. This is the primary compilation entry point — it chains ingest, validation, and link discovery into a single workflow.
version: 0.1.0
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob, AskUserQuestion, Skill]
---

# Compile Skill

Run the full compilation pipeline: ingest unprocessed sources, validate new articles, and discover missing connections.

## Purpose

Provide a single command that runs the complete knowledge compilation pipeline with quality gates at every step. Chains together ingestion (ingest), validation (lint), and link discovery (discover-links) so the user doesn't have to remember to run each step manually.

## When to Use

Invoke this skill when:

- User explicitly runs `/compile`
- User mentions "compile", "compile sources", "run compilation"
- User wants to process raw sources AND ensure quality in one pass
- User asks for "full compile" or "process and compile"

## When NOT to Use

- If the user only wants to ingest without validation: use `/ingest`
- If the user only wants to check health: use `/lint`
- If the user only wants to find links: use `/discover-links`

## Pipeline Overview

```
Step 1: Ingest    →  Process unprocessed raw/ sources into wiki articles
                     (ingest workflow with quality gates)

Step 2: Validate  →  Run health checks on newly created/modified articles
                     (targeted lint on recent articles only)

Step 3: Link      →  Find missing connections for new articles
                     (targeted discover-links on recent articles only)

Step 4: Report    →  Summary of full pipeline results
```

## Process Flow

### Step 1: Ingest

Run the ingest workflow. This handles:

- Scanning raw/ for unprocessed sources
- Building the article manifest
- Detecting batches
- Source-type-specific compilation
- Dedup checks
- Interactive review
- Reciprocal linking
- Post-compilation validation per article

Track which articles were created or modified during this step.

```
Created articles:
  - wiki/concepts/circuit-breaker-pattern.md (new)
  - wiki/guides/terraform-state-locking.md (new)

Updated articles:
  - wiki/concepts/karpenter.md (added source)

Stubs created:
  - wiki/concepts/rate-limiting.md (stub)
```

If no unprocessed sources are found, skip to Step 2 and run validation on the full wiki instead.

### Step 2: Validate New Articles

Run a **targeted** health check on only the articles created or modified in Step 1. This is faster than a full wiki lint and catches issues while they're fresh.

Checks to run on each new/modified article:

1. **Index coverage** — Is the article listed in the correct domain index?
2. **Link validation** — Do all wikilinks in the article resolve?
3. **Frontmatter completeness** — Are all required fields present and valid?
4. **Maturity/confidence audit** — Does maturity match content depth?
   - \>500 words + 2+ sources → should be at least `developing`
   - <200 words → should be `stub`
   - Well-established facts → confidence should be `high`
5. **Duplicate source check** — Does any other article share >50% of the same `compiled_from` sources?

Present issues grouped by severity:

```
Validation Results (4 articles checked):

  Issues found: 2

  1. wiki/concepts/circuit-breaker-pattern.md
     - Maturity mismatch: marked "draft" but has 520 words and 2 sources
       → Promote to "developing"? [Y/n]

  2. wiki/concepts/rate-limiting.md (stub)
     - Not in any domain index
       → Add to sre index? [Y/n]

  No issues:
  - wiki/guides/terraform-state-locking.md
  - wiki/concepts/karpenter.md (updated)
```

Apply approved fixes immediately.

### Step 3: Discover Links for New Articles

Run a **targeted** link discovery on only the articles created or modified in Step 1. For each new article:

1. Search the manifest for articles sharing the same domain tags
2. Check if bidirectional links exist
3. Suggest missing connections

Present as a compact list:

```
Link Discovery (4 articles checked):

  New connections found: 6

  [[circuit-breaker-pattern]] ↔ [[graceful-degradation]]
    Shared domain: sre, resilience — neither links to the other
    Add bidirectional link? [Y/n]

  [[circuit-breaker-pattern]] ↔ [[timeout-pattern]]
    Shared domain: sre — neither links to the other
    Add bidirectional link? [Y/n]

  [[terraform-state-locking]] ↔ [[terraform-state-management]]
    Shared domain: infrastructure — neither links to the other
    Add bidirectional link? [Y/n]

  [... 3 more ...]

  Apply all? [A/review individually/skip]
```

### Step 4: Final Report

Summarize the entire pipeline run:

```
Compilation Complete

  Ingestion:
    Sources processed: 5 (1 batch of 3 + 2 individual)
    Articles created: 3
    Articles updated: 2
    Stubs created: 1

  Validation:
    Articles checked: 6
    Issues found: 2
    Issues fixed: 2

  Link Discovery:
    Articles checked: 6
    Connections added: 4 (8 reciprocal entries)

  Wiki Status:
    Total articles: 199 (+6)
    Unprocessed sources remaining: 0

  Activity logged to: wiki/_log.md
```

Append a pipeline summary to `wiki/_log.md`:

```markdown
## [2026-04-17] compile | Full Pipeline

- Sources ingested: 5
- Articles created: 3 (circuit-breaker-pattern, terraform-state-locking, rate-limiting)
- Articles updated: 2 (karpenter, terraform-recommended-practices)
- Validation fixes: 2 (maturity promotion, index addition)
- New connections: 4
```

## Options and Flags

The user can scope the compilation:

```
/compile                        — Full pipeline, all unprocessed sources
/compile clippings              — Only process raw/clippings/
/compile daily                  — Only process raw/daily/
/compile support_learnings      — Only process raw/support_learnings/
/compile internal_learnings     — Only process raw/internal_learnings/
/compile docs                   — Only process raw/docs/
/compile --skip-links           — Skip link discovery step
/compile --skip-validate        — Skip validation step
```

When scoped to a source type, only scan that subdirectory for unprocessed sources. Validation and link discovery still run on the resulting articles.

## Error Handling

### Ingest Finds Nothing

```
No unprocessed sources in raw/.

Running validation on recently compiled articles instead...
(checking articles compiled in the last 7 days)
```

### Validation Finds Critical Issues

```
Critical: wiki/concepts/broken-article.md has 5 broken wikilinks

Fix before continuing to link discovery? [Y/skip article/abort]
```

### Pipeline Interruption

If the user cancels mid-pipeline, report what was completed:

```
Pipeline interrupted after Step 1 (Ingest).

Completed:
  - 3 articles compiled
  - Indexes updated

Not yet run:
  - Validation (run /lint to check)
  - Link discovery (run /discover-links to check)
```

## Related Skills

- **/ingest** — The underlying ingestion engine (Step 1)
- **/lint** — Full wiki health check (Step 2 runs a targeted subset)
- **/discover-links** — Full link discovery (Step 3 runs a targeted subset)
- **/create-note** — Create articles manually
- **/research** — Research topics and save to raw/docs/ for compilation

## Summary

The compile skill runs the full compilation pipeline: ingest unprocessed sources with interactive quality gates, validate newly created articles for correctness, and discover missing connections for new content. It chains ingest, lint, and discover-links into a single workflow, scoped to only the articles that changed. Use `/compile` as the primary entry point for processing raw sources into the wiki.
