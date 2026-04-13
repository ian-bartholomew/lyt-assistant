---
name: research
description: This skill should be used when the user asks to "research a topic", "research [topic]", "create reference note about [topic]", "look up [topic]", or wants to gather information about a subject and create a structured reference note with sources.
version: 0.2.0
argument-hint: <topic>
allowed-tools: [Bash, Edit, WebFetch, mcp__plugin_context7_context7__query-docs, AskUserQuestion]
---

# Research Skill

Research topics using web search or Context7 and create well-structured reference notes with proper source attribution, MOC links, and vault integration.

For advanced Obsidian markdown syntax (callouts, embeds, block references), follow the `obsidian:obsidian-markdown` skill.

## Purpose

Accelerate learning by automating research for new topics. Gathers information from authoritative sources, synthesizes into structured reference notes, suggests appropriate MOCs and links, and integrates seamlessly into the vault with proper attribution.

## When to Use

Invoke this skill when:

- User explicitly runs `/research <topic>`
- User asks to research, look up, or investigate a topic
- User wants to create a reference note about something new
- User mentions adding external knowledge to vault

## Workflow Overview

1. **Pre-flight check** - Verify Obsidian is running
2. **Parse topic** - Extract topic from arguments
3. **Check existing content** - See if topic already exists
4. **Research strategy** - Choose web search or Context7
5. **Gather information** - Fetch and synthesize content
6. **Analyze and structure** - Create reference note outline
7. **Suggest organization** - Destination, MOCs, links
8. **Present interactively** - Review and edit
9. **Create file** - Write with proper sources and links

## Libraries

This skill uses:

- **lib/obsidian-operations.md** — All CLI-based vault operations
- **lib/analysis.md** — Content classification, topic extraction, MOC matching

## Process Flow

### Step 0: Pre-flight Check

Before any vault operations, verify Obsidian is running:

```bash
obsidian vault
```

If this fails, present to the user:

```
Obsidian doesn't appear to be running. This plugin requires an open Obsidian vault.

Options:
A) Open Obsidian and retry
B) Cancel
```

Use **AskUserQuestion** to get their choice. Do not proceed until the pre-flight check passes.

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

### Step 2: Check for Existing Content

Before researching, check if the topic already exists in the vault:

```bash
# Search for the topic
obsidian search query="$TOPIC" limit=5
```

If matches found:

```
⚠️  Found existing notes about "$TOPIC":
1. [file 1]
2. [file 2]

Options:
A) Update existing note with new sources
B) Create separate new version
C) Review existing note first
D) Cancel
```

Use **AskUserQuestion** to get their decision. If they choose A, read the existing note and plan to enhance it. If C, show them the content with `obsidian read file="..."` before continuing.

### Step 3: Determine Research Strategy

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

```
Is the topic a specific programming library, framework, or API?
  ├─ Yes (React, Kubernetes, Terraform, Python, etc.) → Use Context7
  └─ No (general concept, SRE practice, theory) → Use web search
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

### Step 4: Gather Information

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

### Step 5: Synthesize and Structure Content

Create structured reference note from gathered information:

#### 5a. Extract Key Information

From sources, extract:

- **Definition:** Clear, concise explanation
- **Key Concepts:** Main ideas and terminology
- **Formula/Syntax:** If applicable (e.g., Little's Law: L = λW)
- **Examples:** Practical applications
- **Use Cases:** When to use / when not to use
- **Related Topics:** Connected concepts

#### 5b. Create Note Outline

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

#### 5c. Write Synthesized Content

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

### Step 6: Analyze Topics and Suggest Organization

Use **lib/analysis.md** to extract topics from the synthesized content. Identify:

1. **Technical terms:** Capitalized acronyms (SLO, SRE), hyphenated terms (error-budget)
2. **Domain terms:** Compound phrases (service level objective, capacity planning)
3. **Heading terms:** Words from H2/H3 headings

Example extracted topics: `["queueing theory", "performance", "capacity planning"]`

#### 6a. Suggest Destination Folder

Match topics to existing Reference subfolders:

```bash
# Get Reference structure
obsidian folders folder="300 - Reference"

# Match topics to folder names
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

If no good match exists:

```
Topics don't match existing folders well.

Options:
A) Create new folder: "300 - Reference/[new-topic]/"
B) Place in closest match: "300 - Reference/SRE-Concepts/"
C) Specify custom location
```

#### 6b. Suggest MOCs

Use **lib/analysis.md** MOC matching algorithm:

```bash
# 1. Get all MOCs
obsidian files folder="100 - MOCs" ext=md

# 2. For each MOC, calculate score:
#    - Read MOC content: obsidian read file="MOC Name"
#    - Count keyword matches (weight 2x)
#    - Get MOC links: obsidian links file="MOC Name"
#    - Count link overlaps (weight 1x)
#    - Check title match (weight 3x)

# 3. Return top 2-3 with confidence
```

**Present suggestions:**

```
🗺️  Suggested MOCs:
  - [[Laws & Principles MOC]] (high confidence) — title match, 3 keyword matches
  - [[SRE Concepts MOC]] (medium confidence) — 1 keyword match
```

#### 6c. Find Related Notes

Search vault for related content:

```bash
# Search for each topic term
for term in $TOPICS; do
  obsidian search query="$term" path="200 - Notes" limit=3
  obsidian search query="$term" path="300 - Reference" limit=3
done
```

**Present suggestions:**

```
🔗 Suggested Related Links:
  - [[Latency, throughput, goodput]] (related concept)
  - [[Capacity Planning]] (related practice)
```

### Step 7: Present Complete Summary Interactively

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
  - [[Laws & Principles MOC]] (high confidence)
  - [[SRE Concepts MOC]] (medium confidence)

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

### Step 8: Handle User Editing

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

### Step 9: Create File with Proper Attribution

Once approved, create the file:

```bash
# 1. Create file with content
obsidian create path="300 - Reference/SRE-Concepts/Little's Law.md" content="# Little's Law\n\n[Synthesized content]\n\n## Related\n\n- [[Latency, throughput, goodput]]\n- [[Capacity Planning]]" silent

# 2. Set all properties
obsidian property:set name="tags" value="queueing-theory,performance,capacity-planning" type=list file="Little's Law"
obsidian property:set name="created" value="2026-04-13" type=date file="Little's Law"
obsidian property:set name="type" value="external" file="Little's Law"
obsidian property:set name="sources" value="https://en.wikipedia.org/wiki/Little%27s_law,https://dl.acm.org/doi/10.1145/...,https://sre.google/workbook/..." type=list file="Little's Law"
obsidian property:set name="mocs" value="[[Laws & Principles MOC]],[[SRE Concepts MOC]]" type=list file="Little's Law"
```

The resulting file will have:

```yaml
---
tags: [queueing-theory, performance, capacity-planning]
created: 2026-04-13
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

### Step 10: Report Success

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

### Obsidian Not Running

If `obsidian vault` fails:

```
Obsidian doesn't appear to be running. This plugin requires an open Obsidian vault.

Options:
A) Open Obsidian and retry
B) Cancel
```

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

### File Creation Failure

If `obsidian create` fails:

```
❌ Failed to create file: [error message]

This could mean:
- File already exists (use overwrite option)
- Invalid path or filename
- Obsidian vault is not accessible

Options:
A) Retry with different name/path
B) Show me the content so I can create manually
C) Cancel
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

## Usage Examples

### Example 1: General Topic Research

```
User: /research Little's Law

Pre-flight check...
✅ Obsidian vault active

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

Pre-flight check...
✅ Obsidian vault active

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

Pre-flight check...
✅ Obsidian vault active

⚠️  Found existing note: "Circuit Breaker.md"

Options:
D) Review existing note

[Shows existing content via obsidian read]

Note has basic info. Add new sources? [Y]

🔍 Gathering new sources...
✅ Found 2 additional authoritative sources

Updated frontmatter with new sources.
```

## Related Skills

- **/create-note** - Create from scratch without research
- **/classify-inbox** - Process researched content from inbox

## Summary

The research skill automates topic research by fetching information from authoritative sources, synthesizing structured reference notes with proper attribution, and integrating seamlessly into the vault with appropriate MOC links and related connections using Obsidian CLI commands.
