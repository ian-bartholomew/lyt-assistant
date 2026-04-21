---
name: query
description: This skill should be used when the user asks to "query the wiki", "ask the wiki", "search wiki", "what does the wiki say about", or wants to ask a question and get a synthesized answer from existing wiki articles with citations. Good answers can be saved as new wiki pages.
version: 0.1.0
argument-hint: <question>
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob, AskUserQuestion]
---

# Query Skill

Search the wiki, synthesize a structured answer with `[[wikilink]]` citations, and optionally save the answer as a new wiki article.

## Purpose

Unlock knowledge already in the vault by asking it a question. The skill extracts key terms from the question, searches wiki articles for relevant content, reads the most relevant sources, and synthesizes a structured answer with citations back to source articles. Good answers compound — they can be saved as new wiki pages, accelerating future queries.

## When to Use

Invoke this skill when:

- User explicitly runs `/query <question>`
- User asks "what does the wiki say about X?"
- User wants a synthesized answer drawn from existing articles
- User asks to "search wiki" or "ask the wiki" a question
- User wants to understand how concepts in the wiki relate to each other

## Vault Structure

This skill reads from a Karpathy-style LLM wiki:

| Folder | Purpose |
|--------|---------|
| `wiki/concepts/` | Atomic concept articles (patterns, principles, definitions) |
| `wiki/guides/` | How-to content, runbooks, operational procedures |
| `wiki/company/` | Company-specific knowledge, internal architecture |
| `wiki/learning/` | Learning paths, study notes, post-mortem reflections |
| `wiki/_indexes/` | Domain index files |
| `wiki/_index.md` | Master wiki index |
| `wiki/_log.md` | Activity log |

## Workflow Overview

1. **Parse question** - Extract question from arguments or prompt for one
2. **Orient on wiki** - Read `wiki/_index.md` to understand what exists
3. **Extract key terms** - Identify the core nouns, verbs, and concepts in the question
4. **Search wiki** - Grep/glob for relevant articles by key term
5. **Rank and read** - Select top 5–8 articles by relevance, read each
6. **Synthesize answer** - Write structured response with `[[wikilink]]` citations
7. **Offer to save** - Ask if the answer should become a new wiki page
8. **Log the query** - Append entry to `wiki/_log.md`

## Process Flow

### Step 1: Parse Question Argument

Extract question from user input:

```bash
# User runs: /query how do circuit breakers relate to bulkheads?
QUESTION="how do circuit breakers relate to bulkheads?"

# Or: /query "what is Little's Law and when should I use it?"
QUESTION="what is Little's Law and when should I use it?"
```

If no argument is provided:

```
What would you like to ask the wiki?

Examples:
- "how do circuit breakers relate to bulkheads?"
- "what patterns help with cascading failures?"
- "how does our deployment pipeline work?"
- "what did we learn from the Q1 incident?"
```

### Step 2: Orient on Wiki

Read the master index to understand available content:

```bash
# Read master index for domain and article overview
cat wiki/_index.md
```

This provides a map of what knowledge exists before searching. If `wiki/_index.md` does not exist, note this and proceed with a direct directory search.

### Step 3: Extract Key Terms

Break the question into searchable terms:

```
Question: "how do circuit breakers relate to bulkheads?"

Key terms:
  - Primary: circuit-breaker, bulkhead
  - Secondary: resilience, fault-tolerance, pattern
  - Contextual: cascading-failure, isolation
```

**Term extraction rules:**

- Identify **primary terms** — the main subjects of the question
- Identify **secondary terms** — related concepts likely to appear in relevant articles
- Identify **contextual terms** — broader domain terms that may appear in tangentially related articles
- Convert multi-word terms to both spaced and hyphenated forms for searching

### Step 4: Search Wiki

Search wiki/ for articles matching extracted terms:

```bash
# Search by primary terms first
grep -rl "circuit.breaker" wiki/ --include="*.md"
grep -rl "bulkhead" wiki/ --include="*.md"

# Search by secondary terms
grep -rl "resilience\|fault.tolerance\|isolation" wiki/ --include="*.md"

# Also check domain indexes for broad coverage
grep -rl "sre\|reliability" wiki/_indexes/ --include="*.md"
```

Count hits per file to produce a relevance ranking:

```bash
# Count how many key terms appear in each candidate file
grep -c "circuit.breaker\|bulkhead\|resilience\|fault.tolerance" wiki/concepts/circuit-breaker-pattern.md
```

Present search summary:

```
Searching wiki for: circuit breaker, bulkhead, resilience...

Found 6 potentially relevant articles:
  - wiki/concepts/circuit-breaker-pattern.md (4 hits)
  - wiki/concepts/bulkhead-pattern.md (3 hits)
  - wiki/concepts/graceful-degradation.md (2 hits)
  - wiki/concepts/cascading-failures.md (2 hits)
  - wiki/guides/resilience-patterns-guide.md (1 hit)
  - wiki/learning/q1-incident-review.md (1 hit)

Reading top articles...
```

### Step 5: Rank and Read Articles

Select the top 5–8 articles by hit count, prioritizing:

1. **High hit count** — more key term matches means more relevant
2. **Mature articles** — prefer `maturity: mature` or `canonical` over `stub`
3. **Concepts first** — conceptual articles usually answer "how/why" questions better than guides
4. **Guides for operational questions** — prefer guides for "how do I..." questions

Read each selected article fully:

```bash
# Read top articles
cat wiki/concepts/circuit-breaker-pattern.md
cat wiki/concepts/bulkhead-pattern.md
# ... up to 8 articles
```

**If fewer than 3 relevant articles found:**

```
Only 2 relevant articles found. The wiki may not have deep coverage of this topic.

Proceeding with available articles. Consider running /research to expand coverage.
```

### Step 6: Synthesize Answer

Write a structured answer from the content of the read articles.

#### Answer Format

```
## Answer: How do circuit breakers relate to bulkheads?

[2–4 sentence synthesis of the relationship or concept]

### Key Points

- [Key point 1 drawn from [[source-article]]]
- [Key point 2 drawn from [[source-article]]]
- [Key point 3 drawn from [[source-article]]]

### How They Differ

[Contrast or nuance, if the question asks for comparison]

### How They Work Together

[Synthesis of relationship, if applicable]

### Sources

- [[circuit-breaker-pattern]]
- [[bulkhead-pattern]]
- [[graceful-degradation]]
- [[cascading-failures]]

### Gaps

The wiki doesn't currently cover:
- [Missing concept or angle not covered by existing articles]
- [Suggested topic for /research or /create-note]
```

**Answer quality guidelines:**

- Lead with a direct answer to the question — don't bury the lede
- Use `[[wikilink]]` citations inline when citing a specific article's claim
- Keep the answer focused on what was asked — don't summarize every source
- Surface gaps honestly — if the wiki lacks coverage, say so
- Keep language concise and factual, matching the wiki's tone

### Step 7: Offer to Save as Wiki Page

After presenting the answer, always offer to save it:

```
---

Save this answer as a wiki page?

This answer synthesizes 4 articles and would make a useful standalone reference.

Suggested:
  Type: concept
  Title: "Circuit Breaker and Bulkhead Relationship"
  Filename: circuit-breaker-bulkhead-relationship.md
  Destination: wiki/concepts/circuit-breaker-bulkhead-relationship.md
  Domains: [sre, resilience]
  Sources: [[circuit-breaker-pattern]], [[bulkhead-pattern]], ...

A) Save with these settings
B) Edit settings before saving
C) Don't save
```

**If user chooses A or B:**

Follow the create-note frontmatter flow:

1. Determine type (concept/guide/company/learning)
2. Generate kebab-case filename
3. Assign domain tags
4. Set `sources:` to the `[[wikilink]]` citations used in the answer
5. Set `related:` to the cited articles
6. Set `maturity: draft` and `confidence: medium`
7. Write the file using **Write** tool
8. Update domain indexes in `wiki/_indexes/`
9. Log to `wiki/_log.md` as `query-save`

**Article frontmatter template for saved answers:**

```markdown
---
title: [Synthesized Answer Title]
domain: [tag1, tag2]
maturity: draft
confidence: medium
sources:
  - "[[circuit-breaker-pattern]]"
  - "[[bulkhead-pattern]]"
related:
  - "[[circuit-breaker-pattern]]"
  - "[[bulkhead-pattern]]"
  - "[[graceful-degradation]]"
last_compiled: YYYY-MM-DD
---

# [Synthesized Answer Title]

[Synthesized answer content from the query]

## Sources

- [[circuit-breaker-pattern]]
- [[bulkhead-pattern]]
```

### Step 8: Log the Query

Append an entry to `wiki/_log.md`:

**Query only (not saved):**

```markdown
## [2026-04-21] query | how do circuit breakers relate to bulkheads?

- Articles read: circuit-breaker-pattern, bulkhead-pattern, graceful-degradation, cascading-failures
- Answer: synthesized (not saved)
```

**Query saved as page:**

```markdown
## [2026-04-21] query-save | how do circuit breakers relate to bulkheads?

- Articles read: circuit-breaker-pattern, bulkhead-pattern, graceful-degradation, cascading-failures
- Saved: wiki/concepts/circuit-breaker-bulkhead-relationship.md
- Domain: sre, resilience
```

If `wiki/_log.md` does not exist, create it:

```markdown
---
title: Wiki Compile Log
type: log
---

# Wiki Compile Log

## [2026-04-21] query | how do circuit breakers relate to bulkheads?

- Articles read: circuit-breaker-pattern, bulkhead-pattern, graceful-degradation
- Answer: synthesized (not saved)
```

## Search Strategy

### Term Extraction

Extract key terms from the question before searching:

| Question type | Primary terms | Secondary terms |
|---------------|--------------|-----------------|
| "how does X relate to Y?" | X, Y | shared domains, parent concepts |
| "what is X?" | X | domain terms, synonyms |
| "how do I X?" | action verbs, tool names | domain terms |
| "why does X happen?" | X | causes, effects, domains |
| "what did we learn from X?" | event/project name | outcome terms |

### Ranking Heuristics

1. **Hit count** — more term matches = more relevant
2. **Maturity** — `canonical` > `mature` > `draft` > `stub`
3. **Article type** — match to question type (concept for "what/why", guide for "how")
4. **Recency** — prefer more recently compiled articles when relevance is equal
5. **Domain match** — articles from the same domain as the question topic

### Reading Limit

Read a maximum of 8 articles. If more than 8 are relevant:

```
Found 12 relevant articles. Reading top 8 by relevance score.

Skipped (lower relevance):
  - wiki/concepts/retry-patterns.md
  - wiki/learning/platform-q2-review.md
  - wiki/company/on-call-runbook.md
  - wiki/guides/kubernetes-pod-disruption.md
```

## Answer Format

Every answer must include these sections:

### Required Sections

| Section | Content |
|---------|---------|
| **Answer** (heading) | Direct 2–4 sentence response to the question |
| **Key Points** | Bulleted takeaways with inline `[[wikilink]]` citations |
| **Sources** | List of `[[wikilink]]` articles consulted |
| **Gaps** | Topics the wiki doesn't yet cover relevant to the question |

### Optional Sections (include when relevant)

| Section | When to include |
|---------|----------------|
| **How They Differ** | Comparison questions |
| **How They Work Together** | Relationship questions |
| **When to Use** | Practical application questions |
| **Steps** | How-to questions |
| **Examples** | Questions that benefit from illustration |

### Citation Style

Use inline `[[wikilinks]]` when citing a specific article's content:

```
The circuit breaker acts as a proxy that monitors for failures
([[circuit-breaker-pattern]]), while the bulkhead isolates failure
domains to prevent spread ([[bulkhead-pattern]]).
```

Do not footnote citations — inline wikilinks are the citation mechanism.

## Save-as-Page Flow

When the user wants to save the answer as a wiki page:

### Determine Type

| Answer type | Wiki type |
|-------------|-----------|
| Explains a relationship between concepts | concept |
| Explains what something is | concept |
| Step-by-step procedure from wiki synthesis | guide |
| Summary of company-specific info | company |
| Reflection on lessons or experiences | learning |

### Suggest Filename

Convert the answer title to kebab-case:

```bash
# "Circuit Breaker and Bulkhead Relationship"
# -> circuit-breaker-bulkhead-relationship.md
```

### Set Sources and Related

- `sources:` — the `[[wikilinks]]` of articles the answer was drawn from
- `related:` — same list (these are the core connections)
- Add additional related links via wiki search if relevant articles weren't already cited

### Update Domain Indexes

For each domain tag assigned, update or create the index in `wiki/_indexes/`:

```bash
# Check if domain index exists
ls wiki/_indexes/resilience.md 2>/dev/null
```

Add the new article under the appropriate type heading (Concepts, Guides, Company, Learning).

### Log as query-save

Use `query-save` in the log entry (not `query`) to distinguish saved answers from query-only sessions.

## Log Format

### Query Only

```markdown
## [YYYY-MM-DD] query | <Question text>

- Articles read: <article-name>, <article-name>, ...
- Answer: synthesized (not saved)
```

### Query Saved

```markdown
## [YYYY-MM-DD] query-save | <Question text>

- Articles read: <article-name>, <article-name>, ...
- Saved: wiki/<type>/<filename>.md
- Domain: <tag1>, <tag2>
```

## Error Handling

### No Relevant Articles Found

```
Searched wiki for: circuit breaker, bulkhead, resilience

No relevant articles found.

The wiki doesn't yet cover this topic.

Options:
A) Run /research to gather external information on this topic
B) Run /create-note to write a stub article
C) Ask a different question
```

### Fewer Than 3 Articles Found

```
Only 2 relevant articles found for: "bulkhead pattern"

Proceeding with limited sources — answer may be incomplete.

Consider running /research to expand wiki coverage on this topic.
```

### Empty Wiki

```
wiki/ appears to be empty or has no articles yet.

The wiki needs content before it can answer questions.

Options:
A) Run /ingest to process raw sources
B) Run /research to create articles on a topic
C) Run /create-note to write the first article manually
```

### Vague Question

```
Question is too broad: "how does everything work?"

A focused question will get a better answer.

Examples of focused questions:
- "how do circuit breakers prevent cascading failures?"
- "what is the difference between SLO and SLA?"
- "what did we learn from the payment outage?"

Rephrase your question:
```

### wiki/_index.md Missing

```
wiki/_index.md not found — skipping orientation step.

Proceeding with direct search across wiki/ directories.
```

Continue with Step 3 (key term extraction) without the orientation context.

## Best Practices

1. **Read the index first** — orientation prevents blind searching
2. **Extract terms before searching** — structured term extraction beats ad-hoc grep
3. **Rank by hits, not just existence** — more hits means more relevant
4. **Prefer mature articles** — stub articles have thin content; weight mature/canonical higher
5. **Be direct in the answer** — answer first, explain second
6. **Cite inline** — `[[wikilinks]]` in the body are more useful than a footer list alone
7. **Surface gaps** — tell the user what's missing; it seeds future /research runs
8. **Offer to save thoughtfully** — only suggest saving if the answer has genuine standalone value
9. **Log every query** — `wiki/_log.md` is the audit trail for what has been asked
10. **Cap at 8 articles** — reading more degrades synthesis quality

## Usage Examples

### Example 1: Query Only

```
User: /query how do circuit breakers relate to bulkheads?

Parsing question...
Key terms: circuit-breaker, bulkhead, resilience, fault-tolerance

Reading wiki/_index.md...
Searching wiki/ for relevant articles...
  - wiki/concepts/circuit-breaker-pattern.md (4 hits)
  - wiki/concepts/bulkhead-pattern.md (3 hits)
  - wiki/concepts/graceful-degradation.md (2 hits)
  - wiki/concepts/cascading-failures.md (1 hit)

Reading 4 articles...

---

## Answer: How do circuit breakers relate to bulkheads?

Both circuit breakers ([[circuit-breaker-pattern]]) and bulkheads
([[bulkhead-pattern]]) are resilience patterns that prevent cascading
failures in distributed systems, but they operate at different levels.
Circuit breakers detect failure in a single dependency and stop calling
it temporarily. Bulkheads partition the system so that a failure in one
pool of resources cannot exhaust resources needed by other pools.

### Key Points

- Circuit breakers act as proxies — they open when a dependency fails
  and close again when recovery is detected ([[circuit-breaker-pattern]])
- Bulkheads enforce resource isolation — each downstream dependency gets
  its own thread pool or connection pool ([[bulkhead-pattern]])
- They are complementary: circuit breakers respond to failure, bulkheads
  contain its spread ([[cascading-failures]])
- Together they form the foundation of a resilient service mesh
  ([[graceful-degradation]])

### How They Work Together

A circuit breaker trips when errors exceed a threshold, preventing
further load on a degraded service. A bulkhead ensures that load
generated while waiting for the circuit to close doesn't bleed into
unrelated service pools. Using both together provides defense in depth.

### Sources

- [[circuit-breaker-pattern]]
- [[bulkhead-pattern]]
- [[graceful-degradation]]
- [[cascading-failures]]

### Gaps

The wiki doesn't currently cover:
- Specific implementation patterns in Java (Hystrix, Resilience4j)
- How to tune circuit breaker thresholds for high-traffic services

---

Save this answer as a wiki page? [Y/n]: n

Logged to wiki/_log.md
```

### Example 2: Query Saved as Wiki Page

```
User: /query what patterns help prevent cascading failures?

Parsing question...
Key terms: cascading-failure, pattern, resilience, isolation

Searching wiki/ for relevant articles...
  - wiki/concepts/cascading-failures.md (5 hits)
  - wiki/concepts/circuit-breaker-pattern.md (3 hits)
  - wiki/concepts/bulkhead-pattern.md (3 hits)
  - wiki/concepts/graceful-degradation.md (2 hits)
  - wiki/concepts/exponential-backoff.md (1 hit)
  - wiki/guides/resilience-patterns-guide.md (1 hit)

Reading 6 articles...

---

## Answer: What patterns help prevent cascading failures?

[synthesized answer with citations...]

### Sources

- [[cascading-failures]]
- [[circuit-breaker-pattern]]
- [[bulkhead-pattern]]
- [[graceful-degradation]]
- [[exponential-backoff]]

---

Save this answer as a wiki page? [Y/n]: Y

Suggested:
  Type: concept
  Title: "Patterns for Preventing Cascading Failures"
  Filename: patterns-for-preventing-cascading-failures.md
  Destination: wiki/concepts/patterns-for-preventing-cascading-failures.md
  Domains: [sre, resilience]

A) Save with these settings
B) Edit settings before saving
C) Don't save

> A

Created: wiki/concepts/patterns-for-preventing-cascading-failures.md
Updated: wiki/_indexes/sre.md
Updated: wiki/_indexes/resilience.md
Logged: wiki/_log.md (query-save)

Next steps:
- Review article in Obsidian and refine
- Promote maturity when confident (draft -> mature)
- Run /discover-links to find additional connections
```

## Related Skills

- **/create-note** — create new wiki articles from scratch or existing content
- **/ingest** — process raw sources (clippings, notes) into wiki articles
- **/research** — research topics from external sources and create new articles
- **/discover-links** — find missing connections between existing wiki articles

## Summary

The query skill searches the wiki for articles relevant to a question, reads the top 5–8 most relevant sources, and synthesizes a structured answer with inline `[[wikilink]]` citations. Good answers can be saved as new wiki pages via the create-note frontmatter flow. Every query is logged to `wiki/_log.md`. The skill surfaces gaps in wiki coverage to seed future `/research` and `/create-note` runs — ensuring that knowledge compounds over time.
