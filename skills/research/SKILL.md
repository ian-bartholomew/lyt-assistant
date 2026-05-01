---
name: research
description: This skill should be used when the user asks to "research a topic", "research [topic]", "look up [topic]", or wants to gather information about a subject. Outputs a standalone doc to raw/docs/ for later compilation into the wiki via /compile.
version: 0.3.0
argument-hint: <topic>
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob, WebFetch, mcp__plugin_context7_context7__query-docs, mcp__plugin_context7_context7__resolve-library-id, AskUserQuestion]
---

# Research Skill

Research topics using web search or Context7 and create standalone source documents in `raw/docs/` with proper source attribution. These files are picked up by `/compile` and brought into the wiki.

## Purpose

Accelerate learning by automating research for new topics. Gathers information from authoritative sources, synthesizes into a structured document with source attribution and compilation hints, and drops it into `raw/docs/` for the ingest pipeline.

## When to Use

Invoke this skill when:

- User explicitly runs `/research <topic>`
- User asks to research, look up, or investigate a topic
- User wants to create a wiki article about something new
- User mentions adding external knowledge to the wiki

## Output Location

Research outputs go to `raw/docs/` — the source layer. The `/compile` pipeline picks them up and compiles them into `wiki/` articles with proper indexing, linking, and logging.

```
raw/docs/<topic>.md  →  /compile  →  wiki/<subfolder>/<topic>.md
```

This follows the vault's three-layer architecture: `raw/` (source) → `wiki/` (compiled) → `projects/` (active work).

## Workflow Overview

1. **Parse topic** - Extract topic from arguments
2. **Research strategy** - Choose web search or Context7
3. **Gather information** - Fetch and synthesize content
4. **Analyze and structure** - Create document outline with compilation hints
5. **Present for review** - Show content and suggested metadata
6. **Write to raw/docs/** - Save as standalone source document

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

Create structured document from gathered information:

#### 4a. Extract Key Information

From sources, extract:

- **Definition:** Clear, concise explanation
- **Key Concepts:** Main ideas and terminology
- **Formula/Syntax:** If applicable
- **Examples:** Practical applications
- **Use Cases:** When to use / when not to use
- **Related Topics:** Connected concepts

#### 4b. Determine Compilation Hints

Suggest where the compile pipeline should place this:

| Destination | Content Type |
|-------------|-------------|
| `concepts` | Patterns, principles, definitions, theories |
| `guides` | How-to content, tutorials, operational procedures |
| `company` | Company-specific tools, processes, architecture |
| `learning` | Study notes, book summaries, course material |

**Decision:** If the content primarily explains what something IS → `concepts`. If it explains how to DO something → `guides`.

#### 4c. Create Document with Frontmatter

```markdown
---
title: [Topic Title]
source_type: research
date: YYYY-MM-DD
sources:
  - "https://source-url-1"
  - "https://source-url-2"
suggested_domain: [domain-tags]
suggested_destination: concepts  # or guides, company, learning
suggested_related:
  - "[[related-article-one]]"
  - "[[related-article-two]]"
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
```

#### 4d. Generate Kebab-Case Filename

Convert the topic title to a kebab-case filename:

```bash
# "Little's Law" -> "littles-law.md"
# "Circuit Breaker Pattern" -> "circuit-breaker-pattern.md"
# "Kubernetes Service Mesh" -> "kubernetes-service-mesh.md"
```

#### 4e. Find Related Articles

Search wiki for related content:

```bash
# Search for related terms in existing wiki articles
grep -rl "performance\|capacity\|queueing" wiki/ --include="*.md"
```

### Step 5: Present Summary for Review

Show preview before writing:

```
Research Summary:

Topic: Little's Law
Strategy: Web search
Sources: 3 (Wikipedia, ACM, Google SRE)

Content Preview:
Little's Law relates queue length, arrival rate, and wait time...
[Formula: L = lambda * W]
[Use cases: capacity planning, performance analysis...]

Output: raw/docs/littles-law.md

Compilation hints:
  Suggested destination: concepts
  Suggested domains: [sre, performance, capacity-planning]
  Suggested related: [[capacity-planning-guide]], [[latency-throughput-goodput]]

Would you like to:
A) Create with these settings (recommended)
B) Edit content
C) Show full content preview
D) Cancel
```

### Step 6: Write to raw/docs/

Once approved, write the document:

```markdown
---
title: Little's Law
source_type: research
date: 2026-05-01
sources:
  - "https://en.wikipedia.org/wiki/Little%27s_law"
  - "https://dl.acm.org/doi/10.1145/..."
  - "https://sre.google/workbook/..."
suggested_domain: [sre, performance, capacity-planning]
suggested_destination: concepts
suggested_related:
  - "[[capacity-planning-guide]]"
  - "[[latency-throughput-goodput]]"
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
```

Use **Write** tool to create the file at `raw/docs/<kebab-case-topic>.md`.

### Step 7: Report Success

```
Research Complete!

Created: raw/docs/littles-law.md

Content:
- 342 words
- 3 sources cited
- Formula included
- 2 examples provided

Next step: run /compile to bring this into the wiki
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
- Suggest related articles via kebab-case wikilinks

**DON'T:**

- Copy/paste large blocks (copyright)
- Include marketing fluff
- Add opinion without labeling
- Omit sources
- Over-complicate simple concepts

### Attribution

Always include:

- `sources:` in frontmatter with URLs
- `date:` when the research was conducted
- `source_type: research` to signal pre-synthesized content to the ingest pipeline

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

### Topic Already Exists

Check both `raw/docs/` (uncompiled research) and `wiki/` (already compiled):

```
# Check for uncompiled research
find raw/docs/ -name "*littles-law*" -type f

# Check for compiled wiki article
find wiki/ -name "*littles-law*" -type f
```

If found in `raw/docs/`:

```
Uncompiled research already exists: raw/docs/littles-law.md

Options:
A) Update with new sources (add to existing doc)
B) Replace entirely
C) Cancel
D) Review existing doc
```

If found in `wiki/`:

```
Compiled article already exists: wiki/concepts/littles-law.md

Options:
A) Create updated research doc (will merge during next /compile)
B) Cancel
C) Review existing article
```

### Library-Specific Research (Context7)

```
Researching "React useEffect hook"...

Using Context7 for official docs...
Retrieved React documentation

Note: Library-specific content.
Suggested destination: guides
Suggested domains: [frontend, react]

Create at raw/docs/react-use-effect.md? [Y]
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

### Missing raw/docs/ Directory

```
raw/docs/ not found — creating it now.
```

Automatically create and continue.

## Best Practices

1. **Be specific** - Clear topic names get better results
2. **Verify sources** - Check authority and recency
3. **Synthesize, don't copy** - Original writing
4. **Cite thoroughly** - All sources in frontmatter
5. **Add examples** - Make content practical
6. **Suggest related links** - Use kebab-case wikilinks in suggested_related
7. **Review before creating** - Check content quality
8. **Check for existing content** - Don't duplicate research
9. **Use Context7 for tech** - Better than web for library docs
10. **Run /compile after** - Research docs need compilation to enter the wiki

## Usage Examples

### Example 1: General Topic Research

```
User: /research Little's Law

Researching "Little's Law"...

Web search strategy
Found 3 authoritative sources
Synthesized 342 words

Output: raw/docs/littles-law.md
Suggested destination: concepts
Suggested domains: [sre, performance, capacity-planning]

Create? [Y]

Created raw/docs/littles-law.md
Next step: run /compile to bring into wiki
```

### Example 2: Library Documentation

```
User: /research React hooks

Researching "React hooks"...

Using Context7 (library detected)
Retrieved official React docs

Output: raw/docs/react-hooks.md
Suggested destination: guides
Suggested domains: [frontend, react]

Create? [Y]

Created raw/docs/react-hooks.md
Next step: run /compile to bring into wiki
```

### Example 3: Topic Already Exists

```
User: /research Circuit Breaker

Existing article found: wiki/concepts/circuit-breaker-pattern.md

Options:
A) Create updated research doc (will merge during next /compile)

[User selects A]

Created raw/docs/circuit-breaker-pattern.md
  - 2 new sources added
  - Will merge with existing article during /compile
```

## Related Skills

- **/create-note** - Create wiki articles from scratch without research
- **/ingest** - Process raw sources into wiki articles
- **/compile** - Full pipeline: ingest + validate + discover links (picks up research docs)

## Summary

The research skill automates topic research by fetching information from authoritative sources (via WebFetch or Context7), synthesizing structured documents with proper frontmatter (title, source_type, date, sources, suggested_domain, suggested_destination, suggested_related), and writing them to `raw/docs/`. These files are then picked up by the `/compile` pipeline, which handles wiki placement, indexing, linking, and logging.
