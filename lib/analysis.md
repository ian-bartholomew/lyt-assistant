# Analysis Library

This utility provides instructions for content classification, topic extraction, MOC matching, and thematic grouping. Uses Obsidian CLI (via **lib/obsidian-operations.md**) for all vault queries.

## Note vs Reference Classification

The fundamental distinction in LYT:

- **Notes (200 - Notes/)**: Ideas you've internalized, your own synthesis and insights
- **Reference (300 - Reference/)**: Things you look up, external information and documentation

### Heuristic Rules

**Strong Note indicators:**

1. **First-person language:** "I think...", "In my experience...", "I've learned...", "My understanding is..."
2. **Assertion-style title:** "Circuit breakers prevent cascading failures", "Error budgets decouple reliability from velocity"
3. **Personal synthesis:** Connections between concepts, opinion, interpretation, lessons learned
4. **Short and focused:** Single clear idea (atomic), few paragraphs
5. **No external quotes:** Written entirely in the author's voice

**Strong Reference indicators:**

1. **External content:** Quotes from articles/books/docs, code snippets, commands, configuration examples
2. **Source attribution:** "According to [source]...", URLs, book citations, author names
3. **How-to instructions:** Step-by-step procedures, runbooks, configuration guides
4. **Multiple topics:** Several distinct sections, comprehensive coverage, reference lookup format
5. **Code blocks:** Extensive code examples or configuration

### Classification Algorithm

To classify content:

1. Read file content: `obsidian read file="Note Name"`
2. Check for Note indicators (first-person language, assertion title, personal synthesis)
3. Check for Reference indicators (source attribution, code blocks, external quotes)
4. If both present, assess which dominates
5. Assign confidence level

### Confidence Levels

- **High:** Clear indicators, no ambiguity. Single type dominates.
- **Medium:** Some indicators of both types, but one is stronger. Proceed with suggestion but note the ambiguity.
- **Low:** Mixed signals, roughly equal. Ask the user to clarify.

### Handling Ambiguity

When confidence is low, present to the user:

```
This content has mixed signals:
- Has first-person language (Note indicator)
- Has code blocks (Reference indicator)

Help me decide:
1. Is this your synthesis/opinion (Note), or documentation/lookup (Reference)?
2. Will this need regular updates from external sources?
3. Do you reference this for lookup, or is it an insight?
```

Use **AskUserQuestion** to get their decision.

### Project Detection

Content may also be a Project (150 - Projects/). Project indicators:

- Action items, task lists, deadlines
- Goal or deliverable descriptions
- "Need to", "we should", "by [date]"
- Multiple phases or milestones

If project detected, suggest using `/create-project` for proper hub creation.

## Topic Extraction

### Extract Keywords from Content

Read content with `obsidian read`, then identify:

1. **Technical terms:** Capitalized acronyms (SLO, SRE, API), hyphenated terms (error-budget, circuit-breaker)
2. **Domain terms:** Compound phrases (service level objective, error budget, circuit breaker)
3. **Heading terms:** Words from H2/H3 headings (use `obsidian outline file="Note" format=md`)

### Vault-Wide Term Frequency

To check how prevalent a topic is across the vault:

```bash
obsidian search query="error budget" total
```

This replaces the old `grep -r "term" | wc -l` pattern.

### Theme Grouping

Common themes to detect (extend based on vault content):

- **Reliability:** SLO, SLI, error budget, availability, uptime
- **Observability:** metrics, logs, traces, monitoring, alerting
- **Incident management:** incident, postmortem, on-call, pager, runbook
- **Performance:** latency, throughput, capacity, scalability
- **Deployment:** release, rollback, canary, feature flag

Match extracted topics to themes for grouping suggestions.

## Atomicity Assessment

Notes should cover a single concept. To assess:

### Count Sections

```bash
obsidian outline file="Note" total
```

If more than 4 headings, the note may cover multiple topics. Suggest splitting:

```
Multiple topics detected ([count] sections).
Consider splitting into separate notes:
- Note 1: [First topic from headings]
- Note 2: [Second topic from headings]
```

### Check Length

```bash
obsidian wordcount file="Note" words
```

- **Under 500 words:** Good for a Note (focused)
- **Over 500 words:** May be Reference material or needs splitting
- **Under 50 words:** Very brief — could be a placeholder or needs expansion

## Title Generation

### For Notes (Assertion-Style)

Pattern: `[Subject] [verb] [outcome]`

Examples:

- "Circuit breakers prevent cascading failures"
- "Error budgets enable feature velocity"
- "Exponential backoff reduces thundering herd"
- "Graceful degradation maintains user experience"

Extract the main claim from the first paragraph or conclusion. Simplify to assertion form.

### For References (Descriptive)

Use the topic name directly:

- "Terraform State Management Guide"
- "Circuit Breaker Pattern"
- "PostgreSQL Performance Tuning"

## Destination Suggestion

### Notes

Notes go flat in `200 - Notes/`:

```
200 - Notes/Circuit breakers prevent cascading failures.md
```

### References

References go in topic-specific subfolders. Match topics to existing structure:

```bash
obsidian folders folder="300 - Reference"
```

Compare extracted topics against folder names. Suggest the closest match:

```
Suggested destination: 300 - Reference/SRE-Concepts/
```

If no good match exists, offer options:

```
Topics [new-topic] don't match existing folders.

Options:
A) Create new folder: "300 - Reference/new-topic/"
B) Place in closest match: "300 - Reference/SRE-Concepts/"
C) Specify custom location
```

### Projects

Projects go in `150 - Projects/`.

## MOC Matching

### Algorithm

For a piece of content with extracted topics:

1. **Get all MOCs:**

   ```bash
   obsidian files folder="100 - MOCs" ext=md
   ```

2. **For each MOC, calculate score:**

   **A. Keyword match (weight: 2x):** Read MOC content with `obsidian read file="MOC Name"`. Count how many content topics appear in the MOC.

   **B. Link overlap (weight: 1x):** Get MOC links with `obsidian links file="MOC Name"`. Count how many link targets overlap with content topics.

   **C. Title match (weight: 3x):** Check if MOC title contains any content topic.

   **Total:** `(keyword_matches * 2) + link_overlaps + (title_match * 3)`

3. **Assign confidence:**
   - **High (score >= 5):** Multiple keyword matches, clear thematic fit
   - **Medium (score 2-4):** Some matches, related but not primary
   - **Low (score 1):** Weak connection

4. **Return top 2-3 matches** with confidence and reasoning.

### Presentation Format

```
Suggested MOCs:
  - [[SLOs MOC]] (high confidence) — 3 keyword matches, title match
  - [[SRE Concepts MOC]] (medium confidence) — 1 keyword match, parent MOC
```

### New MOC Detection

Suggest creating a new MOC when:

1. **3+ notes share an uncovered topic:**

   ```bash
   obsidian search query="reliability patterns" total
   ```

   If count >= 3 and no MOC covers this topic, suggest creation.

2. **Existing MOC is too large:**

   ```bash
   obsidian links file="Big MOC" total
   ```

   If > 30 links, suggest splitting into sub-MOCs.

3. **Topic is a subsection of existing MOC** with 10+ items — suggest extracting to its own MOC.

### MOC Naming

Follow patterns:

- Topic + MOC: "Reliability Patterns MOC"
- Category + MOC: "SRE Concepts MOC"
- Domain + MOC: "Terraform MOC"

### Validation

Before suggesting a MOC:

- Verify it exists: `obsidian file file="MOC Name"`
- Verify it's not archived: check it's in `100 - MOCs/`, not `400 - Archive/`
- Don't suggest "Home" or "Index" MOCs unless content is top-level organizational

## Thematic Grouping (for Link Discovery)

### Co-occurrence Analysis

For discovering missing links between notes:

1. Build a topic index by reading files and extracting topics
2. For each pair of files sharing topics but not linking to each other, record a suggestion
3. Group suggestions by theme using the theme categories above

### Confidence Scoring

For each link suggestion:

```bash
# Keyword frequency in target file
obsidian search:context query="term" format=json

# Check if term appears in headings
obsidian outline file="Note" format=md
```

Score: `keyword_frequency + (heading_match * 2) + (same_folder * 1)`

Thresholds:

- **High (>= 5):** Strong topical overlap
- **Medium (2-4):** Related content
- **Low (1):** Weak connection

### Filtering

Skip suggestions where:

- Topic mentioned only once in passing
- File already has > 15 links (over-linked)
- Files are in completely different domains

```bash
obsidian links file="Note" total
```

If > 15, note the file is already well-connected and only show high-confidence suggestions.

## Integration with Obsidian Operations

This library handles analysis logic. For all vault I/O, use **lib/obsidian-operations.md** commands:

- Read content: `obsidian read`
- Scan vault: `obsidian files`, `obsidian folders`
- Check links: `obsidian links`, `obsidian backlinks`
- Search: `obsidian search`
- Get structure: `obsidian outline`, `obsidian wordcount`

## Context

This is Task 2 in the migration plan. This library will be referenced by all 7 skills alongside `lib/obsidian-operations.md` (created in Task 1).
