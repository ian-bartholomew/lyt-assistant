---
name: research
description: This skill should be used when the user asks to "research a topic", "research [topic]", "look up [topic]", or wants to gather information about a subject. Outputs a standalone doc to raw/docs/ for later compilation into the wiki via /compile. Includes automated structure review and fact-checking before finalizing.
version: 0.6.0
argument-hint: [--depth brief|standard|deep] <topic>
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob, WebFetch, WebSearch, Skill, Agent, mcp__plugin_context7_context7__query-docs, mcp__plugin_context7_context7__resolve-library-id, AskUserQuestion]
---

# Research Skill

Research topics using web search or Context7, validate the output for structural quality and factual accuracy, and create standalone source documents in `raw/docs/` formatted as **white papers**. These files are picked up by `/compile` and brought into the wiki.

## Purpose

Accelerate learning by automating research for new topics. Gathers information from authoritative sources, synthesizes into a **white-paper-style document** — Executive Summary, Introduction, Background, Analysis, Conclusion, References — with numbered footnote-style citations and compilation hints. Validates the document through automated structure review and fact-checking, then drops it into `raw/docs/` for the ingest pipeline.

White paper format applies at **every** depth level. Depth controls *length and source count*, not structure: a `brief` is a one-page white paper; `deep` is a full-length one. The reader always sees the same skeleton.

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

## Depth Levels

The `--depth` flag controls how exhaustive the research is:

| Level | Sources | Word Target | Analysis sub-sections | Conclusion length |
|-------|---------|-------------|------------------------|-------------------|
| `brief` | 1-2 | 250-400 | 1 (mechanics) | 1 paragraph |
| `standard` (default) | 2-3 | 500-800 | 2-3 (mechanics, examples, use cases) | 1-2 paragraphs |
| `deep` | 5+ | 1200-2200 | 4-6 (mechanics, theory, examples, comparisons, limitations, edge cases) | 2-3 paragraphs |

All depths share the same six H2 sections (Executive Summary, Introduction, Background, Analysis, Conclusion, References). Only section *length* and the number of *Analysis sub-sections* vary. **Deep research** fetches more sources, explores the topic from multiple angles, and produces a document suitable for thorough study. It also adjusts the structure review minimum word count accordingly.

Usage:

```
/research Little's Law                       # standard (default)
/research --depth brief Little's Law         # quick reference
/research --depth deep Little's Law          # exhaustive
```

## Workflow Overview

1. **Parse topic and depth** - Extract topic and depth level from arguments
2. **Research strategy** - Choose web search or Context7
3. **Gather information** - Fetch and synthesize content
4. **Analyze and structure** - Create document outline with compilation hints
5. **Present for review** - Show content and suggested metadata
6. **Write draft** - Save as `.draft-<topic>.md` in raw/docs/
7. **Validate & review** - Run structure review and fact-checking in parallel
8. **Present findings** - Show combined review report
9. **Fix loop** - Address issues if any, re-review as needed
10. **Finalize** - Rename draft to final filename

## Path Convention

All paths in this skill are relative to the **vault root** (`~/Documents/Work/`), not the wiki directory. When writing files, always resolve paths from the vault root:

- `raw/docs/.draft-topic.md` → `~/Documents/Work/raw/docs/.draft-topic.md`
- `wiki/concepts/topic.md` → `~/Documents/Work/wiki/concepts/topic.md`

**Important:** Write research output to `raw/docs/`, NOT `wiki/raw/docs/`. The `raw/` directory is at the vault root, alongside `wiki/`, not inside it.

## Process Flow

### Step 1: Parse Topic and Depth

Extract topic and depth level from user request:

```bash
# User runs: /research Little's Law
TOPIC="Little's Law"
DEPTH="standard"

# With depth flag: /research --depth deep Little's Law
TOPIC="Little's Law"
DEPTH="deep"

# Or: /research --depth brief "kubernetes service mesh"
TOPIC="kubernetes service mesh"
DEPTH="brief"
```

If no argument provided:

```
What topic would you like to research?

Examples:
- "Little's Law"
- "Circuit Breaker pattern"
- "Terraform state management"

Depth: standard (use --depth brief|standard|deep to change)
```

If user says things like "in depth", "exhaustive", "thorough", or "deep dive" in their request, set `DEPTH="deep"` even without the flag.

### Step 2: Determine Research Strategy

Choose appropriate research method:

```
Is topic a programming library/framework/API?
  |-- Yes -> Use Context7 for authoritative docs
  |-- No -> Use WebFetch for web search
      |-- Search query: "<topic> SRE" or "<topic> definition"
      |-- Fetch sources (count varies by depth)
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

**Source count by depth:**

| Depth | Sources to fetch | Search queries |
|-------|-----------------|----------------|
| `brief` | 1-2 | 1 query: `"<topic> definition"` |
| `standard` | 2-3 | 2 queries: `"<topic> definition"`, `"<topic> SRE"` |
| `deep` | 5+ | 3+ queries: definition, SRE, history, comparisons, criticisms |

```bash
# Step 1: Construct search queries (varies by depth)
QUERIES=("${TOPIC} definition")
if [ "$DEPTH" != "brief" ]; then
  QUERIES+=("${TOPIC} SRE")
fi
if [ "$DEPTH" = "deep" ]; then
  QUERIES+=("${TOPIC} history" "${TOPIC} vs" "${TOPIC} criticism limitations")
fi

# Step 2: Search and fetch
# Prioritize: official docs > academic > Wikipedia > reputable blogs
# Fetch SOURCE_COUNT results based on depth

# Step 3: Synthesize key information
```

For **deep** research, cast a wider net: look for alternative perspectives, historical context, criticisms, and comparisons to related concepts.

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

Organize what you extract around the white-paper sections so synthesis maps cleanly onto the template.

**For every depth, extract material that feeds each section:**

- **Executive Summary** — the top-line takeaway: what the topic *is*, why it matters, and the one thing the reader should remember.
- **Introduction** — the problem or question this topic addresses, plus scope (what's in and out).
- **Background** — prior art, history, originating people/papers, terminology a reader needs before the analysis.
- **Analysis** — mechanics and behavior. The bulk of the document. Sub-sections scale with depth (see below).
- **Conclusion** — synthesis: practical implications, when to reach for this, what the analysis means.

**Analysis sub-sections by depth:**

| Depth | Sub-sections to extract |
|-------|--------------------------|
| `brief` | Mechanics only (definition, formula/syntax if any, one example) |
| `standard` | Mechanics, examples, use cases |
| `deep` | Mechanics, theory/foundations, multiple worked examples, comparisons to related concepts, limitations & criticisms, edge cases & common misconceptions |

For **deep** research, treat each Analysis sub-section as a mini-essay: extract enough material that each one carries 200-400 words on its own.

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

The `depth` field is recorded in frontmatter so the structure review can adjust its word count thresholds.

```markdown
---
title: [Topic Title]
source_type: research
depth: standard  # brief | standard | deep
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
```

**White paper template (all depths):**

Every research document uses the same six H2 sections. Length and the number of Analysis sub-sections scale with depth — section *names* do not.

```markdown
# [Topic Title]

## Executive Summary

[3-5 sentence abstract. State what the paper covers, why it matters, and the
top takeaway. A skim-reader should be able to stop here and walk away with
the core idea.]

## Introduction

[Frame the problem or question this paper addresses. State scope explicitly
(what's in, what's out). 1-2 paragraphs. End with what the reader will get
from the rest of the document.]

## Background

[Prior art, history, terminology. Set the stage so the Analysis section
lands. Cite origins and key contributors with inline numbered markers [1].
Length scales with depth — one paragraph for brief, several for deep.]

## Analysis

[Core body of the paper. Break into numbered sub-headings for distinct
threads. Every factual claim carries an inline numbered citation [N].]

### 1. Mechanics

[How the topic works — definition, formula/syntax, behavior. Always present.]

### 2. Examples

[Worked examples and real-world cases. Standard and deep.]

### 3. Use Cases

[When and how to apply. Standard and deep.]

### 4. Comparisons

[Relation to similar concepts; what makes this different. Deep only.]

### 5. Limitations

[Known criticisms, edge cases, common misconceptions, when it does not
apply. Deep only.]

## Conclusion

[Synthesize the analysis. Practical implications. When should a reader
reach for this? 1-3 paragraphs by depth.]

## References

1. <Source title or publisher> — <URL>
2. <Source title or publisher> — <URL>
```

**Sub-section selection by depth:**

| Depth | Analysis sub-sections to include |
|-------|----------------------------------|
| `brief` | 1. Mechanics only |
| `standard` | 1. Mechanics, 2. Examples, 3. Use Cases |
| `deep` | All five sub-sections (Mechanics, Examples, Use Cases, Comparisons, Limitations) plus any topic-specific threads (e.g. Theory, Edge Cases) |

Drop sub-sections that don't apply rather than padding with empty content. Empty sections fail the structure review.

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

#### 4f. Citation Style

The white paper format uses **numbered footnote-style citations**. The body carries inline `[N]` markers; the `## References` section at the bottom lists each source with title and URL, numbered to match.

**Rules:**

- Every factual claim (definitions, formulas, dates, attributed positions, statistics) carries an inline `[N]` marker at the end of the sentence.
- Numbers are assigned in order of first appearance. Reuse the same number on subsequent references to the same source.
- A claim drawn from multiple sources stacks markers: `[1][3]`.
- Opinions, examples you constructed, and obvious common knowledge do not need citations.
- The `## References` section is the human-readable rendering. The `sources:` frontmatter field still contains the bare URL list (machine-readable, used by the fact-checker and `/compile`).

**Worked mini-example:**

```markdown
## Background

Little's Law was first proven by John Little in 1961 [1]. The law states that
the long-term average number of customers in a stationary system equals the
long-term average arrival rate multiplied by the average time a customer
spends in the system [1][2].

## References

1. Little, J. D. C. — "A Proof for the Queuing Formula: L = λW" (1961) — https://www.jstor.org/stable/167570
2. Wikipedia — "Little's law" — https://en.wikipedia.org/wiki/Little%27s_law
```

### Step 5: Present Summary for Review

Show preview before writing:

```
Research Summary:

Topic: Little's Law
Depth: standard
Strategy: Web search
Sources: 3 (Wikipedia, ACM, Google SRE)

Format: white paper
Sections: Executive Summary, Introduction, Background,
          Analysis (Mechanics, Examples, Use Cases),
          Conclusion, References
Word count target: 500-800

Content Preview:
Executive Summary: Little's Law relates queue length, arrival rate, and
wait time (L = λW) and is the foundational identity behind capacity planning
and performance analysis in queueing systems...

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

Example draft content (standard depth):

```markdown
---
title: Little's Law
source_type: research
depth: standard
date: 2026-05-01
sources:
  - "https://en.wikipedia.org/wiki/Little%27s_law"
  - "https://www.jstor.org/stable/167570"
  - "https://sre.google/workbook/..."
suggested_domain: [sre, performance, capacity-planning]
suggested_destination: concepts
suggested_related:
  - "[[capacity-planning-guide]]"
  - "[[latency-throughput-goodput]]"
---

# Little's Law

## Executive Summary

Little's Law states that the long-term average number of items in a stationary
queueing system equals the average arrival rate multiplied by the average time
each item spends in the system: L = λW [1]. It is the foundational identity
behind capacity planning and queue-based performance analysis, and applies to
any stable system regardless of its internal scheduling discipline [2].

## Introduction

Capacity planning and latency analysis in distributed systems repeatedly hit
the same question: how do throughput, concurrency, and response time relate?
This paper introduces Little's Law, the simple identity that ties those three
quantities together, and explains where it applies and where it breaks down.

## Background

Little's Law was first proven by John Little in 1961 [1]. Prior work in
queueing theory had observed the relationship empirically; Little's
contribution was a proof that held independently of arrival-time
distributions or service disciplines [1].

## Analysis

### 1. Mechanics

L = λ × W, where L is average concurrency in the system, λ is average
arrival rate, and W is average time spent in the system [1][2]...

### 2. Examples

Worked example: an API handles 100 RPS with a 50ms average response time,
so average in-flight requests = 100 × 0.05 = 5 [3]...

### 3. Use Cases

Capacity planning: pick a thread-pool size that matches your expected
arrival rate and target latency [3]...

## Conclusion

Little's Law gives operators a back-of-the-envelope tool that holds under
remarkably weak assumptions. Reach for it whenever two of the three
quantities are known and the third is the unknown — but verify the system
is in steady state before trusting the result.

## References

1. Little, J. D. C. — "A Proof for the Queuing Formula: L = λW" (1961) — https://www.jstor.org/stable/167570
2. Wikipedia — "Little's law" — https://en.wikipedia.org/wiki/Little%27s_law
3. Google SRE Workbook — "Non-abstract Large System Design" — https://sre.google/workbook/...
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
- 612 words (standard depth)
- White paper format: 6 sections, 3 Analysis sub-sections
- 3 sources cited (inline + References)

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
- 612 words (standard depth)
- White paper format: 6 sections, 3 Analysis sub-sections
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

### Example 1: Standard depth (default)

```
User: /research Little's Law

Researching "Little's Law" (standard depth)...

Web search strategy
Found 3 authoritative sources
Synthesized 612 words in white paper format

Sections: Executive Summary, Introduction, Background,
          Analysis (Mechanics, Examples, Use Cases),
          Conclusion, References

Create? [Y]

Draft written: raw/docs/.draft-littles-law.md

Reviewing...
  Structure: PASS (8/8)
  Facts: PASS (6 claims verified)

No issues found. Finalizing.

Created: raw/docs/littles-law.md
Next step: run /compile to bring into wiki
```

### Example 2: Brief depth

```
User: /research --depth brief retry backoff

Researching "retry backoff" (brief)...

Found 2 authoritative sources
Synthesized 320 words in white paper format

Sections: Executive Summary, Introduction, Background,
          Analysis (Mechanics), Conclusion, References

Create? [Y]

Draft written: raw/docs/.draft-retry-backoff.md

Reviewing...
  Structure: PASS (8/8)
  Facts: PASS (3 claims verified)

Created: raw/docs/retry-backoff.md
Next step: run /compile to bring into wiki
```

### Example 3: Deep research

```
User: /research --depth deep Little's Law

Researching "Little's Law" (deep)...

Searching: definition, history, comparisons, criticisms...
Found 6 authoritative sources (Wikipedia, JSTOR, MIT OCW, Google SRE, ...)
Synthesized 1,820 words in white paper format

Sections: Executive Summary, Introduction, Background,
          Analysis (Mechanics, Theory, Examples, Comparisons,
                    Limitations), Conclusion, References (6)

Create? [Y]

Draft written: raw/docs/.draft-littles-law.md

Reviewing...
  Structure: PASS (8/8)
  Facts: NEEDS_FIX (1 unsupported claim)

Issues:
  1. [fact] Line 58: "Universally applicable to all queueing systems"
     CONTRADICTED — sources note it requires steady-state assumption

A) Auto-fix and re-review

[User selects A]

Fixed: added steady-state caveat to Limitations sub-section
Re-running fact checker...
  Facts: PASS (12 claims verified)

Created: raw/docs/littles-law.md
Next step: run /compile to bring into wiki
```

### Example 4: Natural language triggers deep

```
User: I want to do a deep dive on circuit breakers

Researching "circuit breakers" (deep — inferred from "deep dive")...
Found 5 authoritative sources...
```

## Related Skills

- **/review-structure** - Standalone structure review (called automatically during research)
- **/create-note** - Create wiki articles from scratch without research
- **/ingest** - Process raw sources into wiki articles
- **/compile** - Full pipeline: ingest + validate + discover links (picks up research docs)

## Summary

The research skill automates topic research by fetching information from authoritative sources (via WebFetch or Context7) and synthesizing **white-paper-style documents** into `raw/docs/`. Every output uses the same six H2 sections — Executive Summary, Introduction, Background, Analysis, Conclusion, References — with numbered footnote-style inline citations (`[1]`, `[2]`) anchored in the References list. Frontmatter (title, source_type, depth, date, sources, suggested_domain, suggested_destination, suggested_related) supports the downstream `/compile` pipeline. The `--depth` flag controls *length and analysis breadth*, not structure: `brief` (250-400 words, 1-2 sources, one Analysis sub-section), `standard` (500-800 words, 2-3 sources, three Analysis sub-sections, default), or `deep` (1200-2200 words, 5+ sources, five-plus Analysis sub-sections covering theory, comparisons, and limitations). Before finalizing, it runs two automated reviewers in parallel: a structure review skill (`/review-structure`) that validates document quality with depth-aware thresholds, and a fact-checker agent that cross-references claims against sources and independent web searches. Issues are presented to the user with options to auto-fix, accept, or cancel. Once both reviewers pass, the draft is finalized to `raw/docs/<topic>.md` for pickup by the `/compile` pipeline.
