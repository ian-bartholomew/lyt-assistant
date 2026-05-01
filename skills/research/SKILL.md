---
name: research
description: This skill should be used when the user asks to "research a topic", "research [topic]", "look up [topic]", or wants to gather information about a subject. Outputs a standalone doc to raw/docs/ for later compilation into the wiki via /compile. Includes automated structure review and fact-checking before finalizing.
version: 0.4.0
argument-hint: <topic>
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob, WebFetch, WebSearch, Skill, Agent, mcp__plugin_context7_context7__query-docs, mcp__plugin_context7_context7__resolve-library-id, AskUserQuestion]
---

# Research Skill

Research topics using web search or Context7, validate the output for structural quality and factual accuracy, and create standalone source documents in `raw/docs/`. These files are picked up by `/compile` and brought into the wiki.

## Purpose

Accelerate learning by automating research for new topics. Gathers information from authoritative sources, synthesizes into a structured document with source attribution and compilation hints, validates the document through automated structure review and fact-checking, and drops it into `raw/docs/` for the ingest pipeline.

## When to Use

Invoke this skill when:

- User explicitly runs `/research <topic>`
- User asks to research, look up, or investigate a topic
- User wants to create a wiki article about something new
- User mentions adding external knowledge to the wiki

## Output Location

Research outputs go to `raw/docs/` — the source layer. Documents are written as drafts first (`raw/docs/.draft-<topic>.md`), reviewed by automated validators, then finalized (`raw/docs/<topic>.md`). The `/compile` pipeline picks up finalized files and compiles them into `wiki/` articles.

```
.draft-<topic>.md  →  review & validate  →  <topic>.md  →  /compile  →  wiki/<subfolder>/<topic>.md
```

This follows the vault's three-layer architecture: `raw/` (source) → `wiki/` (compiled) → `projects/` (active work).

## Workflow Overview

1. **Parse topic** - Extract topic from arguments
2. **Research strategy** - Choose web search or Context7
3. **Gather information** - Fetch and synthesize content
4. **Analyze and structure** - Create document outline with compilation hints
5. **Present for review** - Show content and suggested metadata
6. **Write draft** - Save as `.draft-<topic>.md` in raw/docs/
7. **Validate & review** - Run structure review and fact-checking in parallel
8. **Present findings** - Show combined review report
9. **Fix loop** - Address issues if any, re-review as needed
10. **Finalize** - Rename draft to final filename

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

Draft: raw/docs/.draft-littles-law.md

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

### Step 6: Write Draft

Once the user approves the content, write it as a **draft** — not the final file:

```bash
# Write to draft location (dot-prefix hides from /compile scanning)
DRAFT_PATH="raw/docs/.draft-${KEBAB_TOPIC}.md"
```

Use **Write** tool to create the file at `raw/docs/.draft-<kebab-case-topic>.md`.

Example draft content:

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

...
```

### Step 7: Validate & Review

Dispatch two reviewers **in parallel** (single message, both tool calls together):

#### 7a. Structure Review (Skill tool)

Invoke the `/review-structure` skill with the draft file path:

```
Skill: review-structure
Args: raw/docs/.draft-littles-law.md
```

This checks frontmatter completeness, section structure, word count, source attribution, wikilink validity, related articles, and empty sections. Returns a structured report with status (`PASS`, `WARN`, `NEEDS_FIX`).

#### 7b. Fact Checker (Agent tool)

Dispatch via the **Agent** tool with a focused prompt. The agent runs in isolated context with tools `[Read, WebFetch, WebSearch, Grep]`.

**Important:** Before dispatching, substitute `<topic>` in the prompt template below with the actual kebab-case filename (e.g., `littles-law`).

**Agent prompt template:**

```
You are a fact-checker for a research document. Your job is to verify that the
document contains no false information or hallucinations.

Read the document at: raw/docs/.draft-<topic>.md

Phase 1 — Source cross-check:
- Extract all factual claims from the document (definitions, dates, numbers,
  formulas, attributed quotes)
- Re-fetch each URL listed in the `sources` frontmatter field
- For each claim, verify it appears in or is supported by the cited sources
- Flag claims that don't match any source as "unsupported"

Phase 2 — Independent verification:
- Identify the top 3-5 most important factual claims (definitions, formulas,
  dates, numbers — not opinions or examples)
- Run independent web searches to corroborate each claim
- Flag claims that contradict independent sources as "potentially false"
- Flag claims that can't be independently verified as "unverifiable"

For each claim, assign a verdict:
- VERIFIED: matches source AND independently confirmed
- SOURCE_ONLY: matches source, not independently checked (low-risk claims)
- UNSUPPORTED: not traceable to any cited source
- CONTRADICTED: conflicts with independent sources
- UNVERIFIABLE: can't confirm or deny

Report format:

Fact Check: <file-path>

  Claims checked: N
  Source-verified: N
  Independently verified: N

  Issues:
    - Line N: "<claim text>"
      Verdict: <VERDICT> — <explanation>

  Status: <PASS|WARN|NEEDS_FIX>

Status rules:
- PASS: all claims are VERIFIED or SOURCE_ONLY
- WARN: any UNVERIFIABLE claims but none UNSUPPORTED or CONTRADICTED
- NEEDS_FIX: any UNSUPPORTED or CONTRADICTED claims
```

### Step 8: Present Findings

Once both reviewers return, merge their reports into a combined summary:

```
Review Results: raw/docs/.draft-littles-law.md

  Structure: PASS (8/8 checks passed)
  Facts: NEEDS_FIX (1 unsupported claim)

  Issues to fix:
    1. [fact] Line 38: "Average response time should be under 200ms"
       UNSUPPORTED — not found in any cited source

  A) Auto-fix issues and re-review
  B) Show full review reports
  C) Accept as-is (finalize with warnings noted)
  D) Cancel (delete draft)
```

If both reviewers return `PASS`:

```
Review Results: raw/docs/.draft-littles-law.md

  Structure: PASS (8/8 checks passed)
  Facts: PASS (6 claims verified)

  No issues found. Ready to finalize.

  A) Finalize (recommended)
  B) Show full review reports
  C) Cancel (delete draft)
```

### Step 9: Fix Loop

If the user selects **"Auto-fix"**:

1. Edit the draft file to address each issue:
   - For unsupported claims: remove the claim or add a source
   - For contradicted claims: correct the information
   - For structural errors: fix frontmatter, add missing sections, expand thin content
   - For empty sections: add content or remove the section
2. Re-run **only the reviewer(s) that reported issues** — don't re-run a reviewer that already passed
3. Present updated findings
4. Repeat until both pass or user selects "Accept as-is"

If the user selects **"Accept as-is"**:

- Proceed to Step 10 with warnings noted in the success report
- The document is finalized despite unresolved warnings

If the user selects **"Cancel"**:

- Delete the draft file: `raw/docs/.draft-<topic>.md`
- Report cancellation, nothing written

### Step 10: Finalize

Rename the draft to its final filename:

```bash
mv raw/docs/.draft-<topic>.md raw/docs/<topic>.md
```

Use **Bash** tool to rename the file.

Report success:

```
Research Complete!

Created: raw/docs/littles-law.md

Content:
- 342 words
- 3 sources cited
- Formula included
- 2 examples provided

Review:
- Structure: PASS
- Facts: PASS (6 claims verified)

Next step: run /compile to bring this into the wiki
```

If accepted with warnings:

```
Research Complete!

Created: raw/docs/littles-law.md (with warnings)

Content:
- 342 words
- 3 sources cited

Review:
- Structure: PASS
- Facts: WARN (1 unverifiable claim accepted)
  - Line 38: "Average response time..." — UNVERIFIABLE

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

### Example 1: Research passes review

```
User: /research Little's Law

Researching "Little's Law"...

Web search strategy
Found 3 authoritative sources
Synthesized 342 words

Create? [Y]

Draft written: raw/docs/.draft-littles-law.md

Reviewing...
  Structure: PASS (8/8)
  Facts: PASS (6 claims verified)

No issues found. Finalizing.

Created: raw/docs/littles-law.md
Next step: run /compile to bring into wiki
```

### Example 2: Research needs fixes

```
User: /research CAP Theorem

Researching "CAP Theorem"...
Found 3 sources, synthesized 410 words.

Create? [Y]

Draft written: raw/docs/.draft-cap-theorem.md

Reviewing...
  Structure: WARN (7/8 — thin at 280 words)
  Facts: NEEDS_FIX (1 unsupported claim)

Issues:
  1. [fact] Line 22: "Proved by Seth Gilbert in 2002"
     UNSUPPORTED — sources say Gilbert & Lynch, not Gilbert alone

A) Auto-fix and re-review

[User selects A]

Fixed: corrected attribution to "Gilbert and Lynch (2002)"
Re-running fact checker...
  Facts: PASS (7 claims verified)

Created: raw/docs/cap-theorem.md
Next step: run /compile to bring into wiki
```

### Example 3: User accepts with warnings

```
User: /research Amdahl's Law

...
Draft written: raw/docs/.draft-amdahls-law.md

Reviewing...
  Structure: PASS (8/8)
  Facts: WARN (1 unverifiable claim)

Issues:
  1. [fact] Line 45: "Commonly cited in cloud architecture"
     UNVERIFIABLE — subjective claim, no definitive source

C) Accept as-is

Created: raw/docs/amdahls-law.md (1 warning noted)
Next step: run /compile to bring into wiki
```

## Related Skills

- **/review-structure** - Standalone structure review (called automatically during research)
- **/create-note** - Create wiki articles from scratch without research
- **/ingest** - Process raw sources into wiki articles
- **/compile** - Full pipeline: ingest + validate + discover links (picks up research docs)

## Summary

The research skill automates topic research by fetching information from authoritative sources (via WebFetch or Context7), synthesizing structured documents with proper frontmatter (title, source_type, date, sources, suggested_domain, suggested_destination, suggested_related), and writing them as drafts to `raw/docs/`. Before finalizing, it runs two automated reviewers in parallel: a structure review skill (`/review-structure`) that validates document quality, and a fact-checker agent that cross-references claims against sources and independent web searches. Issues are presented to the user with options to auto-fix, accept, or cancel. Once both reviewers pass, the draft is finalized to `raw/docs/<topic>.md` for pickup by the `/compile` pipeline.
