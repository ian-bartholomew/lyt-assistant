---
name: research
description: This skill should be used when the user asks to "research a topic", "research [topic]", "create wiki article about [topic]", "look up [topic]", or wants to gather information about a subject and create a structured wiki article with sources.
version: 0.2.0
argument-hint: <topic>
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob, WebFetch, mcp__plugin_context7_context7__query-docs, mcp__plugin_context7_context7__resolve-library-id, AskUserQuestion]
---

# Research Skill

Research topics using web search or Context7 and create well-structured wiki articles with proper source attribution, domain indexing, and activity logging.

## Purpose

Accelerate learning by automating research for new topics. Gathers information from authoritative sources, synthesizes into structured wiki articles, assigns domain tags, updates indexes, and integrates seamlessly into the vault with proper attribution.

## When to Use

Invoke this skill when:

- User explicitly runs `/research <topic>`
- User asks to research, look up, or investigate a topic
- User wants to create a wiki article about something new
- User mentions adding external knowledge to the wiki

## Vault Structure

This skill creates articles in a Karpathy-style LLM wiki:

| Folder | Purpose |
|--------|---------|
| `wiki/concepts/` | Atomic concept articles (patterns, principles, definitions) |
| `wiki/guides/` | How-to content, runbooks, operational procedures |
| `wiki/_indexes/` | Domain index files |
| `wiki/_index.md` | Master index |
| `wiki/_log.md` | Activity log |

## Workflow Overview

1. **Parse topic** - Extract topic from arguments
2. **Research strategy** - Choose web search or Context7
3. **Gather information** - Fetch and synthesize content
4. **Analyze and structure** - Create wiki article outline
5. **Suggest organization** - Destination subfolder, domain tags, related links
6. **Present interactively** - Review and edit
7. **Create article** - Write with proper frontmatter and sources
8. **Update indexes and log** - Maintain wiki infrastructure

## Process Flow

### Step 1: Parse Topic Argument

Extract topic from user request:

```bash
# User runs: /research Little's Law
TOPIC="Little's Law"

# Or: /research "kubernetes service mesh"
TOPIC="kubernetes service mesh"
```

If no argument provided:

```
What topic would you like to research?

Examples:
- "Little's Law"
- "Circuit Breaker pattern"
- "Terraform state management"
```

### Step 2: Determine Research Strategy

Choose appropriate research method:

```
Is topic a programming library/framework/API?
  |-- Yes -> Use Context7 for authoritative docs
  |-- No -> Use WebFetch for web search
      |-- Search query: "<topic> SRE" or "<topic> definition"
      |-- Fetch top 2-3 authoritative results
      |-- Synthesize into structured article
```

**Decision tree:**

```bash
# Check if topic is tech/programming related
if echo "$TOPIC" | grep -qi "react\|kubernetes\|terraform\|python\|javascript"; then
  STRATEGY="context7"
else
  STRATEGY="websearch"
fi
```

**Always confirm with user:**

```
Topic: "Little's Law"

Research strategy:
- Web search (general topic)

Or would you prefer:
- Context7 (if this is a library/framework)

Proceed with web search? [Y/n]
```

### Step 3: Gather Information

#### Strategy A: Web Search

Use **WebFetch** tool to search and retrieve content:

```bash
# Step 1: Construct search query
QUERY="${TOPIC} definition"
ALT_QUERY="${TOPIC} SRE"

# Step 2: Search
RESULTS=$(web_search "$QUERY")

# Step 3: Identify authoritative sources
# Prioritize:
# - Wikipedia (definitions, overview)
# - Academic papers (.edu, .org)
# - Authoritative blogs (martinfowler.com, SRE blogs)
# - Official documentation

# Step 4: Fetch top 2-3 results
for url in $TOP_URLS; do
  CONTENT=$(WebFetch "$url")
  SOURCES+=("$url")
done

# Step 5: Synthesize key information
```

**Example web search flow:**

```
Researching "Little's Law"...

Searching web sources...
Found: Wikipedia (https://en.wikipedia.org/wiki/Little%27s_law)
Found: ACM article (https://dl.acm.org/...)
Found: SRE blog (https://sre.google/...)

Synthesizing information...
```

#### Strategy B: Context7 (Libraries/Frameworks)

Use **Context7** MCP tools:

```bash
# Resolve library ID
LIBRARY_ID=$(resolve_library_id "$TOPIC")

# Query documentation
DOCS=$(query_docs "$LIBRARY_ID" "overview getting started")
```

**Example Context7 flow:**

```
Researching "React hooks"...

Using Context7 for authoritative documentation...
Retrieved: React official docs
Retrieved: Hooks API reference

Synthesizing documentation...
```

### Step 4: Synthesize and Structure Content

Create structured wiki article from gathered information:

#### 4a. Extract Key Information

From sources, extract:

- **Definition:** Clear, concise explanation
- **Key Concepts:** Main ideas and terminology
- **Formula/Syntax:** If applicable
- **Examples:** Practical applications
- **Use Cases:** When to use / when not to use
- **Related Topics:** Connected concepts

#### 4b. Determine Wiki Subfolder

| Subfolder | Content Type |
|-----------|-------------|
| `wiki/concepts/` | Patterns, principles, definitions, theories |
| `wiki/guides/` | How-to content, tutorials, operational procedures |

**Decision:** If the content primarily explains what something IS, use `concepts/`. If it explains how to DO something, use `guides/`.

#### 4c. Create Article Outline

```markdown
---
title: [Topic Title]
domain: [domain-tags]
maturity: draft
confidence: medium
sources:
  - "https://source-url-1"
  - "https://source-url-2"
related:
  - "[[related-article-one]]"
  - "[[related-article-two]]"
last_compiled: YYYY-MM-DD
---

# [Topic Title]

## Overview

[Brief definition and context]

## Key Concepts

[Main ideas explained]

## Formula/Syntax

[If applicable]

## Examples

[Practical examples]

## Use Cases

[When and how to apply]

## Related

- [[related-article-one]]
- [[related-article-two]]
```

#### 4d. Generate Kebab-Case Filename

Convert the topic title to a kebab-case filename:

```bash
# "Little's Law" -> "littles-law.md"
# "Circuit Breaker Pattern" -> "circuit-breaker-pattern.md"
# "Kubernetes Service Mesh" -> "kubernetes-service-mesh.md"
```

### Step 5: Suggest Organization

#### 5a. Suggest Destination

```
Suggested Destination:
   wiki/concepts/littles-law.md

Rationale: Describes a principle/theory — fits concepts/

Alternative:
   wiki/guides/ (if this were a how-to)
```

#### 5b. Suggest Domain Tags

Analyze content and suggest domain tags:

```
Suggested Domains: [sre, performance, capacity-planning]

These will be used for indexing in wiki/_indexes/
```

#### 5c. Find Related Articles

Search wiki for related content:

```bash
# Search for related terms in existing wiki articles
grep -rl "performance\|capacity\|queueing" wiki/ --include="*.md"
```

**Present suggestions:**

```
Suggested Related Articles:
  - [[capacity-planning-guide]]
  - [[latency-throughput-goodput]]
```

### Step 6: Present Complete Summary Interactively

Show preview:

```
Research Summary:

Topic: Little's Law
Strategy: Web search
Sources: 3 (Wikipedia, ACM, Google SRE)

Content Preview:
Little's Law relates queue length, arrival rate, and wait time...
[Formula: L = lambda * W]
[Use cases: capacity planning, performance analysis...]

Destination: wiki/concepts/littles-law.md

Domain Tags: [sre, performance, capacity-planning]

Related Articles:
  - [[capacity-planning-guide]]
  - [[latency-throughput-goodput]]

Would you like to:
A) Create with these settings (recommended)
B) Edit destination subfolder
C) Edit domain tags
D) Edit related links
E) Edit content
F) Show full content preview
G) Cancel
```

### Step 7: Handle User Editing

#### Option B: Edit Destination

```
Current: wiki/concepts/

Choose destination:
1. wiki/concepts/
2. wiki/guides/

Select (1-2):
```

#### Option C: Edit Domain Tags

```
Current domains: [sre, performance, capacity-planning]

Actions:
- Keep all (default)
- Remove: [enter tags]
- Add: [enter tags]
```

#### Option D: Edit Related Links

```
Suggested related:
1. [[capacity-planning-guide]]
2. [[latency-throughput-goodput]]

Actions:
- Keep all
- Remove specific (enter numbers)
- Add additional (enter kebab-case article names)
```

#### Option E: Edit Content

```
Opening content for review...

[Show full content]

Edit directly? [Y/n]

Or provide feedback and I'll revise.
```

### Step 8: Create Article with Proper Attribution

Once approved, write the wiki article:

```markdown
---
title: Little's Law
domain: [sre, performance, capacity-planning]
maturity: draft
confidence: medium
sources:
  - "https://en.wikipedia.org/wiki/Little%27s_law"
  - "https://dl.acm.org/doi/10.1145/..."
  - "https://sre.google/workbook/..."
related:
  - "[[capacity-planning-guide]]"
  - "[[latency-throughput-goodput]]"
last_compiled: 2026-04-17
---

# Little's Law

## Overview

Little's Law relates queue length, arrival rate, and wait time in queueing theory.
Formulated by John Little in 1961, it's fundamental for capacity planning and
performance analysis in distributed systems.

## Formula

```

L = lambda * W

```

Where:
- L = average number of items in system
- lambda = average arrival rate
- W = average wait time

## Examples

### Web Server Capacity

If requests arrive at 100/sec (lambda) and average response time is 0.5sec (W):
- L = 100 * 0.5 = 50 concurrent requests

This tells us the system needs capacity for 50 concurrent connections.

## Use Cases

- **Capacity planning:** Determine required system resources
- **Performance analysis:** Understand queue behavior
- **SLO setting:** Calculate target latencies from load

## Related

- [[capacity-planning-guide]]
- [[latency-throughput-goodput]]
```

Use **Write** tool to create the file.

### Step 9: Update Wiki Infrastructure

#### 9a. Update Domain Indexes

For each domain tag, find or create the index file in `wiki/_indexes/`:

```bash
# e.g., for domain "sre"
INDEX_FILE="wiki/_indexes/sre.md"
```

If the index exists, append the new article. If not, create it:

```markdown
---
title: SRE Domain Index
domain: sre
last_updated: 2026-04-17
---

# SRE

## Concepts

- [[littles-law]] — Little's Law

## Guides

[entries here]
```

Add the article under the section matching its subfolder (Concepts or Guides).

#### 9b. Update Master Index

If the article introduces a new domain not yet in `wiki/_index.md`, add it:

```markdown
## Domains

- [[wiki/_indexes/sre|SRE]]
- [[wiki/_indexes/performance|Performance]]
```

#### 9c. Append to Activity Log

Add entry to `wiki/_log.md`:

```markdown
## [2026-04-17] research | Little's Law

- Sources: 3 (Wikipedia, ACM, Google SRE)
- Destination: `wiki/concepts/littles-law.md`
- Domain: sre, performance, capacity-planning
- Maturity: draft
```

### Step 10: Report Success

```
Research Complete!

Created: wiki/concepts/littles-law.md

Content:
- 342 words
- 3 sources cited
- Formula included
- 2 examples provided

Wiki Integration:
- Domain indexes updated: sre, performance, capacity-planning
- Related links: 2
- Activity logged to wiki/_log.md

Next steps:
- Review and refine content in Obsidian
- Add personal insights
- Promote maturity when confident (draft -> developing -> mature)
```

## Research Quality Guidelines

### Source Selection

Prioritize authoritative sources:

1. **Official documentation** (highest authority)
2. **Academic papers** (.edu, research institutions)
3. **Wikipedia** (good for definitions and overviews)
4. **Reputable blogs** (Martin Fowler, Google SRE, etc.)
5. **Books** (O'Reilly, Packt, etc.)

Avoid:

- Random blog posts
- Forums/Reddit (unless verified)
- Outdated content (>5 years for tech)
- Marketing content

### Content Synthesis

**DO:**

- Synthesize information in clear, concise language
- Include practical examples
- Cite sources in frontmatter
- Extract key formulas/code
- Connect to related articles via kebab-case wikilinks

**DON'T:**

- Copy/paste large blocks (copyright)
- Include marketing fluff
- Add opinion without labeling
- Omit sources
- Over-complicate simple concepts

### Attribution

Always include:

- `sources:` in frontmatter (URLs for external, `[[raw/...]]` wikilinks for local)
- `last_compiled:` date
- `maturity: draft` for new articles
- `confidence:` level based on source quality

## Special Cases

### Topic Not Found

```
Researching "Obscure Internal Tool"...

No authoritative sources found

Options:
A) Create blank template (you fill in content)
B) Try different search terms
C) Cancel

Suggested alternative searches:
- "Internal Tool documentation"
- "Internal Tool SRE"
```

### Multiple Conflicting Sources

```
Researching "CAP Theorem"...

Found conflicting explanations across sources

Multiple interpretations exist. I'll:
- Include most authoritative definition (ACM)
- Note alternative interpretations
- Cite all sources

Proceed? [Y/n]
```

### Topic Already Exists in Wiki

```
Article already exists: wiki/concepts/littles-law.md

Options:
A) Update existing article with new sources
B) Create separate version
C) Cancel
D) Review existing article
```

If updating, add new sources, refresh content, and update `last_compiled`.

### Library-Specific Research (Context7)

```
Researching "React useEffect hook"...

Using Context7 for official docs...
Retrieved React documentation

Note: Library-specific content.
Suggested destination: wiki/guides/react-use-effect.md
Domain: [frontend, react]

Create? [Y]
```

## Error Handling

### Network/Fetch Failure

```
Failed to fetch: https://example.com/article

Options:
A) Continue with available sources (2/3)
B) Retry failed fetch
C) Cancel research
```

### Context7 Not Available

```
Context7 unavailable for this library

Falling back to web search...

Or cancel and research manually?
```

### Invalid Topic

```
Topic too vague: "stuff"

Please provide specific topic:
- Good: "Circuit Breaker pattern"
- Good: "Kubernetes service mesh"
- Bad: "stuff", "things", "that"
```

### Missing Wiki Infrastructure

```
wiki/_indexes/ not found — creating it now.
wiki/_log.md not found — creating it now.
```

Automatically create missing infrastructure and continue.

## Best Practices

1. **Be specific** - Clear topic names get better results
2. **Verify sources** - Check authority and recency
3. **Synthesize, don't copy** - Original writing
4. **Cite thoroughly** - All sources in frontmatter
5. **Add examples** - Make content practical
6. **Connect via related links** - Use kebab-case wikilinks
7. **Review before creating** - Check content quality
8. **Update existing articles** - Don't duplicate
9. **Use Context7 for tech** - Better than web for library docs
10. **Start as draft** - Promote maturity over time

## Usage Examples

### Example 1: General Topic Research

```
User: /research Little's Law

Researching "Little's Law"...

Web search strategy
Found 3 authoritative sources
Synthesized 342 words

Destination: wiki/concepts/littles-law.md
Domains: [sre, performance, capacity-planning]

Create? [Y]

Created wiki/concepts/littles-law.md
Updated indexes: sre, performance, capacity-planning
Logged to wiki/_log.md
```

### Example 2: Library Documentation

```
User: /research React hooks

Researching "React hooks"...

Using Context7 (library detected)
Retrieved official React docs

Destination: wiki/guides/react-hooks.md
Domains: [frontend, react]

Create? [Y]

Created wiki/guides/react-hooks.md
Updated indexes: frontend, react
Logged to wiki/_log.md
```

### Example 3: Topic Already Exists

```
User: /research Circuit Breaker

Existing article found: wiki/concepts/circuit-breaker-pattern.md

Options:
D) Review existing article

[Shows existing article]

Article has basic info. Add new sources? [Y]

Updated wiki/concepts/circuit-breaker-pattern.md
  - Added 2 new sources
  - Updated last_compiled
Logged to wiki/_log.md
```

## Related Skills

- **/create-note** - Create from scratch without research
- **/ingest** - Ingest raw sources into wiki articles

## Summary

The research skill automates topic research by fetching information from authoritative sources (via WebFetch or Context7), synthesizing structured wiki articles with proper frontmatter (title, domain, maturity, confidence, sources, related, last_compiled), placing them in the appropriate wiki subfolder (concepts/ or guides/), updating domain indexes in `wiki/_indexes/`, and logging activity to `wiki/_log.md`.
