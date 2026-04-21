# Analysis Library

This utility provides instructions for content classification, topic extraction, domain index matching, and thematic grouping. Uses Obsidian CLI (via **lib/obsidian-operations.md**) for all vault queries.

## Wiki Article Classification

Content is classified into one of four types based on what question it answers:

| Type | Question it answers | Destination | Examples |
|------|---------------------|-------------|---------|
| concept | What is X? | wiki/concepts/ | Patterns, principles, definitions |
| guide | How do I X? | wiki/guides/ | Runbooks, tutorials, procedures |
| company | How does our org do X? | wiki/company/ | Internal systems, team processes |
| learning | What did I learn from X? | wiki/learning/ | Post-mortems, course notes |

### Classification Heuristics

**Concept indicators:**

1. **Defines or explains something:** "X is...", "X means...", "X works by..."
2. **Assertion-style or descriptive title:** "Circuit breakers prevent cascading failures", "Error Budget Pattern"
3. **Personal synthesis:** Connections between concepts, interpretation, distilled understanding
4. **Atomic scope:** Single clear idea, few paragraphs, no step-by-step procedures
5. **No external source attribution:** Written in the author's voice, not quoting docs

**Guide indicators:**

1. **Action-oriented title:** "How to deploy...", "Setting up...", "Debugging X"
2. **Step-by-step structure:** Numbered steps, prerequisites, commands to run
3. **Procedural content:** Runbooks, tutorials, configuration walkthroughs
4. **Imperative language:** "Run...", "Navigate to...", "Set the value to..."
5. **Code blocks or commands:** Practical execution details

**Company indicators:**

1. **References internal systems or teams:** Specific team names, internal tool names, org-specific processes
2. **Org-specific context:** "Our process is...", "The FES Platform team...", "In our environment..."
3. **Internal URLs or docs:** Links to internal wikis, tickets, or dashboards
4. **Process ownership:** Describes who owns or is responsible for something

**Learning indicators:**

1. **Contextual or reflective title:** "Lessons from...", "What I learned in...", "Post-mortem:"
2. **First-person reflection:** "I learned...", "We discovered...", "In retrospect..."
3. **Time-bound or event-bound:** Related to a specific incident, course, book, or project
4. **Takeaways section:** Explicit lessons, next steps, or action items from experience

### Classification Algorithm

To classify content:

1. Read file content: `obsidian read file="Note Name"`
2. Check for concept indicators (assertion title, personal synthesis, atomic scope)
3. Check for guide indicators (step-by-step, imperative language, procedures)
4. Check for company indicators (internal references, org-specific context)
5. Check for learning indicators (reflective, contextual title, first-person lessons)
6. If multiple types present, assess which dominates
7. Assign confidence level

### Handling Ambiguity

When confidence is low, present to the user:

```
This content has mixed signals:
- Has step-by-step instructions (guide indicator)
- Has personal reflection (learning indicator)

Help me decide:
1. Is this primarily a procedure to follow (guide), or a record of what you learned (learning)?
2. Is this meant for your org specifically (company), or broadly applicable (concept/guide)?
3. Will you look this up to execute it, or to recall an insight?
```

Use **AskUserQuestion** to get their decision.

### Content That Spans Multiple Types

Some content legitimately covers multiple types. When this occurs:

- **Prefer the dominant purpose** — what will the reader primarily do with this?
- **Split if distinctly separable** — a guide with a "Lessons Learned" section can be split into a guide + a learning article
- **Use tags** to cross-reference when a single article genuinely serves two purposes (e.g., a concept article that also explains an internal company usage)

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

- **Under 500 words:** Good for a wiki article (focused)
- **Over 500 words:** May need splitting
- **Under 50 words:** Very brief — could be a placeholder or needs expansion

## Title Generation

### For Concepts (Assertion-Style or Descriptive)

Assertion pattern: `[Subject] [verb] [outcome]`

Examples:

- "Circuit breakers prevent cascading failures"
- "Error budgets enable feature velocity"
- "Exponential backoff reduces thundering herd"

Descriptive pattern: `[Topic] [Pattern/Principle/Concept]`

Examples:

- "Circuit Breaker Pattern"
- "Error Budget Principle"

### For Guides (Action-Oriented)

Pattern: `How to [verb] [subject]` or `[Verb]ing [subject]`

Examples:

- "How to Deploy a Canary Release"
- "Setting Up Terraform State Backend"
- "Debugging Kafka Consumer Lag"

### For Company (Descriptive)

Use the system, process, or team name directly:

- "FES Platform On-Call Process"
- "Internal Deployment Pipeline"
- "Team Incident Response Runbook"

### For Learning (Contextual)

Pattern: `Lessons from [X]` or `What I Learned from [X]`

Examples:

- "Lessons from the July 2024 Outage"
- "What I Learned from the SRE Course"
- "Post-Mortem: Database Migration Failure"

## Destination Suggestion

### Wiki Articles

Articles go in wiki subfolders by type:

| Type | Destination |
|------|-------------|
| concept | `wiki/concepts/<kebab-case-title>.md` |
| guide | `wiki/guides/<kebab-case-title>.md` |
| company | `wiki/company/<kebab-case-title>.md` |
| learning | `wiki/learning/<kebab-case-title>.md` |

Example:

```
wiki/concepts/circuit-breakers-prevent-cascading-failures.md
wiki/guides/how-to-deploy-a-canary-release.md
wiki/company/fes-platform-on-call-process.md
wiki/learning/lessons-from-the-july-2024-outage.md
```

To check existing wiki structure for matching articles:

```bash
obsidian folders folder="wiki"
```

### Projects

Projects go in `projects/<kebab-case-name>/`.

If project-like content is detected (action items, task lists, goals, deadlines), suggest using `/create-project` for proper hub creation.

## Domain Index Matching

### Algorithm

For a piece of content with extracted topics:

1. **Get all domain indexes:**

   ```bash
   obsidian files folder="wiki/_indexes" ext=md
   ```

2. **For each index, calculate score:**

   **A. Keyword match (weight: 2x):** Read index content with `obsidian read file="Index Name"`. Count how many content topics appear in the index.

   **B. Domain tag match (weight: 3x):** Check if the index's domain tags overlap with the content's tags or detected themes.

   **C. Related article overlap (weight: 1x):** Get index links with `obsidian links file="Index Name"`. Count how many link targets overlap with content topics.

   **Total:** `(keyword_matches * 2) + (domain_tag_matches * 3) + related_article_overlaps`

3. **Assign confidence:**
   - **High (score >= 5):** Multiple keyword matches, clear thematic fit
   - **Medium (score 2-4):** Some matches, related but not primary
   - **Low (score 1):** Weak connection

4. **Return top 2-3 matches** with confidence and reasoning.

### Presentation Format

```
Suggested domain indexes:
  - [[SLOs Index]] (high confidence) — 3 keyword matches, domain tag match
  - [[SRE Concepts Index]] (medium confidence) — 1 keyword match, related article overlap
```

### New Domain Index Detection

Suggest creating a new domain index when:

1. **3+ articles share domain tags with no existing index covering that domain:**

   ```bash
   obsidian search query="reliability patterns" total
   ```

   If count >= 3 and no index covers this domain, suggest creation.

2. **Existing index is too large:**

   ```bash
   obsidian links file="Big Index" total
   ```

   If > 30 entries, suggest splitting into sub-indexes.

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

## Integration with Skills

This library handles analysis logic. For all vault I/O, use **lib/obsidian-operations.md** commands. All skills reference this library for content classification, topic extraction, and domain matching.
