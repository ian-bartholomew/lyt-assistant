---
name: research
description: This skill should be used when the user asks to "research a topic", "research [topic]", "create reference note about [topic]", "look up [topic]", or wants to gather information about a subject and create a structured reference note with sources.
version: 0.1.0
argument-hint: <topic>
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob, WebFetch, mcp__plugin_context7_context7__query-docs, AskUserQuestion]
---

# Research Skill

Research topics using web search or Context7 and create well-structured reference notes with proper source attribution, MOC links, and vault integration.

## Purpose

Accelerate learning by automating research for new topics. Gathers information from authoritative sources, synthesizes into structured reference notes, suggests appropriate MOCs and links, and integrates seamlessly into the vault with proper attribution.

## When to Use

Invoke this skill when:
- User explicitly runs `/research <topic>`
- User asks to research, look up, or investigate a topic
- User wants to create a reference note about something new
- User mentions adding external knowledge to vault

## Workflow Overview

1. **Parse topic** - Extract topic from arguments
2. **Research strategy** - Choose web search or Context7
3. **Gather information** - Fetch and synthesize content
4. **Analyze and structure** - Create reference note outline
5. **Suggest organization** - Destination, MOCs, links
6. **Present interactively** - Review and edit
7. **Create file** - Write with proper sources and links

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
  ├─ Yes → Use Context7 for authoritative docs
  └─ No → Use WebFetch for web search
      ├─ Search query: "<topic> SRE" or "<topic> definition"
      ├─ Fetch top 2-3 authoritative results
      └─ Synthesize into structured note
```

**Decision tree:**

```bash
# Check if topic is tech/programming related
if echo "$TOPIC" | grep -qi "react\|kubernetes\|terraform\|python\|javascript"; then
  # Likely library/framework - use Context7
  STRATEGY="context7"
else
  # General topic - use web search
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
ALT_QUERY="${TOPIC} SRE"  # For technical topics

# Step 2: Search (use WebFetch with search URL)
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
# Extract:
# - Definition
# - Key concepts
# - Examples
# - Related topics
```

**Example web search flow:**

```
Researching "Little's Law"...

🔍 Searching web sources...
✅ Found: Wikipedia (https://en.wikipedia.org/wiki/Little%27s_law)
✅ Found: ACM article (https://dl.acm.org/...)
✅ Found: SRE blog (https://sre.google/...)

📚 Synthesizing information...
```

#### Strategy B: Context7 (Libraries/Frameworks)

Use **Context7** MCP tool:

```bash
# Query Context7 for library documentation
LIBRARY_ID=$(resolve_library_id "$TOPIC")
DOCS=$(query_docs "$LIBRARY_ID" "overview getting started")
```

**Example Context7 flow:**

```
Researching "React hooks"...

📚 Using Context7 for authoritative documentation...
✅ Retrieved: React official docs
✅ Retrieved: Hooks API reference

📝 Synthesizing documentation...
```

### Step 4: Synthesize and Structure Content

Create structured reference note from gathered information:

#### 4a. Extract Key Information

From sources, extract:

- **Definition:** Clear, concise explanation
- **Key Concepts:** Main ideas and terminology
- **Formula/Syntax:** If applicable (e.g., Little's Law: L = λW)
- **Examples:** Practical applications
- **Use Cases:** When to use / when not to use
- **Related Topics:** Connected concepts

#### 4b. Create Note Outline

```markdown
# [Topic Title]

## Overview

[Brief definition and context]

## Key Concepts

[Main ideas explained]

## Formula/Syntax

[If applicable - formulas, code syntax, etc.]

## Examples

[Practical examples]

## Use Cases

[When and how to apply]

## Related Topics

[Connected concepts]

## References

[Source links]
```

#### 4c. Write Synthesized Content

Generate clear, concise content:

```markdown
# Little's Law

## Overview

Little's Law relates queue length, arrival rate, and wait time in queueing theory.
Formulated by John Little in 1961, it's fundamental for capacity planning and
performance analysis in distributed systems.

## Formula

```
L = λW
```

Where:
- L = average number of items in system
- λ = average arrival rate
- W = average wait time

## Examples

### Web Server Capacity

If requests arrive at 100/sec (λ) and average response time is 0.5sec (W):
- L = 100 × 0.5 = 50 concurrent requests

This tells us the system needs capacity for 50 concurrent connections.

## Use Cases

- **Capacity planning:** Determine required system resources
- **Performance analysis:** Understand queue behavior
- **SLO setting:** Calculate target latencies from load

## Related Topics

- Queue theory
- Performance modeling
- Capacity planning
- Latency budgets

## References

- https://en.wikipedia.org/wiki/Little%27s_law
- https://dl.acm.org/doi/10.1145/...
```

### Step 5: Analyze Topics and Suggest Organization

Use **lib/content-analyzer.md** to extract topics:

```bash
TOPICS=$(extract_topics "$SYNTHESIZED_CONTENT")
# Example: ["queueing theory", "performance", "capacity planning"]
```

#### 5a. Suggest Destination Folder

Match topics to existing Reference subfolders:

```bash
# Get Reference structure
REF_STRUCTURE=$(find "300 - Reference" -type d)

# Match topics to folders
# "queueing theory" + "performance" → "300 - Reference/SRE-Concepts/"
# "terraform" → "300 - Reference/terraform/"
```

**Present suggestion:**

```
📁 Suggested Location:
   300 - Reference/SRE-Concepts/Little's Law.md

Rationale: Best match for topics (performance, capacity planning)

Available alternatives:
- 300 - Reference/Math/
- 300 - Reference/Laws-and-Principles/
```

#### 5b. Suggest MOCs

Use **lib/moc-matcher.md**:

```bash
# Match topics to MOCs
MOCS=$(find_relevant_mocs "$TOPICS")
```

**Present suggestions:**

```
🗺️  Suggested MOCs:
  - [[Laws & Principles MOC]] (high confidence)
  - [[SRE Concepts MOC]] (medium confidence)
```

#### 5c. Find Related Notes

Search vault for related content:

```bash
# Search for related terms
for term in $TOPICS; do
  grep -rl "$term" "200 - Notes" "300 - Reference" --include="*.md"
done
```

**Present suggestions:**

```
🔗 Suggested Related Links:
  - [[Latency, throughput, goodput]] (related concept)
  - [[Capacity Planning]] (related practice)
```

### Step 6: Present Complete Summary Interactively

Show preview:

```
📝 Research Summary:

Topic: Little's Law
Strategy: Web search
Sources: 3 (Wikipedia, ACM, Google SRE)

📄 Content Preview:
Little's Law relates queue length, arrival rate, and wait time...
[Formula: L = λW]
[Use cases: capacity planning, performance analysis...]

📁 Suggested Location:
   300 - Reference/SRE-Concepts/Little's Law.md

🗺️  Suggested MOCs:
  - [[Laws & Principles MOC]]
  - [[SRE Concepts MOC]]

🔗 Additional Links:
  - [[Latency, throughput, goodput]]
  - [[Capacity Planning]]

Would you like to:
A) Create with these settings (recommended)
B) Edit location
C) Edit MOCs
D) Edit related links
E) Edit content
F) Show full content preview
G) Cancel
```

### Step 7: Handle User Editing

#### Option B: Edit Location

```
Current: 300 - Reference/SRE-Concepts/

Choose destination:
1. 300 - Reference/SRE-Concepts/
2. 300 - Reference/Laws-and-Principles/
3. 300 - Reference/Math/
4. [Custom path]

Select (1-4):
```

#### Option C: Edit MOCs

```
Suggested MOCs:
1. [[Laws & Principles MOC]]
2. [[SRE Concepts MOC]]

Actions:
- Keep all (default)
- Remove: [enter numbers: 2]
- Add: [enter MOC names]
```

#### Option E: Edit Content

```
Opening content for review...

[Show full content]

Edit directly? [Y/n]

Or provide feedback and I'll revise.
```

### Step 8: Create File with Proper Attribution

Once approved, create file:

```markdown
---
tags: [queueing-theory, performance, capacity-planning]
created: 2026-03-26
type: external
sources:
  - https://en.wikipedia.org/wiki/Little%27s_law
  - https://dl.acm.org/doi/10.1145/...
  - https://sre.google/workbook/...
mocs:
  - [[Laws & Principles MOC]]
  - [[SRE Concepts MOC]]
---

# Little's Law

[Synthesized content]

## Related

- [[Latency, throughput, goodput]]
- [[Capacity Planning]]
```

Use **Write** tool to create file.

### Step 9: Report Success

```
✅ Research Complete!

Created: 300 - Reference/SRE-Concepts/Little's Law.md

Content:
- 342 words
- 3 sources cited
- Formula included
- 2 examples provided

Vault Integration:
- Added to [[Laws & Principles MOC]]
- Added to [[SRE Concepts MOC]]
- 2 related links added
- Proper frontmatter with sources

Next steps:
- Review and refine content in Obsidian
- Add personal notes/insights
- Link from related notes
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
- Connect to related topics

**DON'T:**
- Copy/paste large blocks (copyright)
- Include marketing fluff
- Add opinion without labeling
- Omit sources
- Over-complicate simple concepts

### Attribution

Always include:
- `sources:` in frontmatter (URLs)
- Reference section with links
- `type: external` for external content

## Special Cases

### Topic Not Found

```
🔍 Researching "Obscure Internal Tool"...

⚠️  No authoritative sources found

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
🔍 Researching "CAP Theorem"...

⚠️  Found conflicting explanations across sources

Multiple interpretations exist. I'll:
- Include most authoritative definition (ACM)
- Note alternative interpretations
- Cite all sources

Proceed? [Y/n]
```

### Topic Already Exists

```
⚠️  Note already exists: "Little's Law.md"

Options:
A) Update existing note with new sources
B) Create separate version
C) Cancel
D) Review existing note
```

### Library-Specific Research (Context7)

```
Researching "React useEffect hook"...

📚 Using Context7 for official docs...

✅ Retrieved React documentation

Note: This is library-specific content.
Consider creating in:
- 300 - Reference/Frontend/React/
- 300 - Reference/Tools/JavaScript/

Choose destination?
```

## Error Handling

### Network/Fetch Failure

```
❌ Failed to fetch: https://example.com/article

Options:
A) Continue with available sources (2/3)
B) Retry failed fetch
C) Cancel research
```

### Context7 Not Available

```
⚠️  Context7 unavailable for this library

Falling back to web search...

Or cancel and research manually?
```

### Invalid Topic

```
❌ Topic too vague: "stuff"

Please provide specific topic:
- Good: "Circuit Breaker pattern"
- Good: "Kubernetes service mesh"
- Bad: "stuff", "things", "that"
```

## Best Practices

1. **Be specific** - Clear topic names get better results
2. **Verify sources** - Check authority and recency
3. **Synthesize, don't copy** - Original writing
4. **Cite thoroughly** - All sources in frontmatter
5. **Add examples** - Make content practical
6. **Connect to vault** - Link to related notes
7. **Review before creating** - Check content quality
8. **Update existing notes** - Don't duplicate
9. **Use Context7 for tech** - Better than web for docs
10. **Follow up** - Add personal insights later

## Integration with Utilities

This skill uses shared utilities:

- **lib/content-analyzer.md** - Extract topics, suggest folder
- **lib/moc-matcher.md** - Suggest relevant MOCs
- **lib/vault-scanner.md** - Find related notes
- **lib/frontmatter.md** - Create proper attribution
- **lib/link-parser.md** - Add links

## Usage Examples

### Example 1: General Topic Research

```
User: /research Little's Law

Researching "Little's Law"...

🔍 Web search strategy
✅ Found 3 authoritative sources
📝 Synthesized 342 words

📁 Location: 300 - Reference/SRE-Concepts/
🗺️  MOCs: [[Laws & Principles MOC]]

Create? [Y]

✅ Created with sources cited
```

### Example 2: Library Documentation

```
User: /research React hooks

Researching "React hooks"...

📚 Using Context7 (library detected)
✅ Retrieved official React docs

📁 Location: 300 - Reference/Frontend/React/
🗺️  MOCs: [[React MOC]], [[Frontend MOC]]

Create? [Y]

✅ Created with documentation
```

### Example 3: Topic Already Exists

```
User: /research Circuit Breaker

⚠️  "Circuit Breaker.md" already exists

Options:
D) Review existing note

[Shows existing note]

Note has basic info. Add new sources? [Y]

✅ Updated with 2 new sources
```

## Related Skills

- **/create-note** - Create from scratch without research
- **/classify-inbox** - Process researched content from inbox

## Summary

The research skill automates topic research by fetching information from authoritative sources, synthesizing structured reference notes with proper attribution, and integrating seamlessly into the vault with appropriate MOC links and related connections.
