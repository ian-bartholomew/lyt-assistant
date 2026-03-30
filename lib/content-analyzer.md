# Content Analyzer Utility

This utility provides instructions for analyzing note content to determine its type, topics, and characteristics in the LYT system.

## Purpose

Provide consistent content classification across all LYT Assistant commands. Determines whether content belongs in Notes (200) or Reference (300), extracts topics, and assesses note quality.

## Core Classification: Note vs Reference

The fundamental distinction in LYT:

- **Notes (200 - Notes/)**: Ideas you've internalized, your own synthesis and insights
- **Reference (300 - Reference/)**: Things you look up, external information and documentation

## Classification Heuristics

### Indicators of Note (200 - Notes/)

Strong indicators content is a Note:

1. **First-person language:**
   - "I think...", "In my experience...", "I've learned..."
   - "My understanding is...", "I believe..."

2. **Assertion-style title:**
   - "Circuit breakers prevent cascading failures"
   - "Error budgets decouple reliability from velocity"
   - "Exponential backoff reduces thundering herd"

3. **Personal synthesis:**
   - Connections between concepts
   - Opinion or interpretation
   - Lessons learned from experience

4. **Short and focused:**
   - Single clear idea (atomic)
   - Few paragraphs
   - No extensive code blocks

5. **No external quotes:**
   - Written entirely in your voice
   - No attribution to sources
   - No direct quotes

**Example Note content:**

```markdown
# Circuit breakers prevent cascading failures

When a downstream service fails, continuing to call it wastes
resources and delays failure detection. I've learned that
implementing circuit breakers stops the cascade early.

The pattern is simple: after N failures, stop calling the service
for a timeout period. This gives the failed service time to recover
while protecting the caller from wasted requests.

In my experience, this is one of the most effective reliability
patterns for distributed systems.
```

### Indicators of Reference (300 - Reference/)

Strong indicators content is Reference material:

1. **External content:**
   - Quotes from articles, books, documentation
   - Code snippets from external sources
   - Commands and configuration examples

2. **Definitions from sources:**
   - "According to [source]..."
   - Dictionary-style definitions
   - Technical specifications

3. **How-to instructions:**
   - Step-by-step procedures
   - Runbooks and playbooks
   - Configuration guides

4. **Multiple topics:**
   - Several distinct sections
   - Comprehensive coverage
   - Reference lookup format

5. **Source attribution:**
   - URLs in frontmatter
   - Book citations
   - Author attribution

**Example Reference content:**

```markdown
---
source: https://martinfowler.com/bliki/CircuitBreaker.html
---

# Circuit Breaker Pattern

From Martin Fowler's definition:

"The basic idea behind the circuit breaker is very simple. You wrap a
protected function call in a circuit breaker object, which monitors for
failures."

## Implementation

```python
class CircuitBreaker:
    def __init__(self, failure_threshold, timeout):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        # ... implementation
```

## Configuration

Set these environment variables:
- `CIRCUIT_BREAKER_THRESHOLD=5`
- `CIRCUIT_BREAKER_TIMEOUT=60`
```

## Classification Algorithm

To classify content:

### 1. Check for Strong Note Indicators

```bash
# Look for first-person language
if grep -qi "I think\|I believe\|In my experience\|I've learned" "file.md"; then
  CONFIDENCE="high"
  TYPE="note"
fi

# Check for assertion-style title
TITLE=$(head -n 1 "file.md" | sed 's/^# //')
if echo "$TITLE" | grep -q " \(prevent\|enable\|cause\|reduce\|improve\) "; then
  CONFIDENCE="high"
  TYPE="note"
fi
```

### 2. Check for Strong Reference Indicators

```bash
# Look for source attribution
if grep -q "^source:" "file.md" || grep -qi "according to\|from \[" "file.md"; then
  CONFIDENCE="high"
  TYPE="reference"
fi

# Look for code blocks or commands
if grep -q "^\`\`\`" "file.md"; then
  CONFIDENCE="medium"
  TYPE="reference"
fi

# Look for external quotes
if grep -q "^> " "file.md"; then
  CONFIDENCE="medium"
  TYPE="reference"
fi
```

### 3. Assess Mixed Signals

If both Note and Reference indicators present:

```
Content has:
- First-person language (Note indicator)
- Code blocks (Reference indicator)

This could be:
- Note with examples → likely Note if brief examples
- Reference with commentary → likely Reference if extensive code

Ask user:
"Is this your synthesis/opinion (Note), or documentation/lookup (Reference)?"
```

### 4. Determine Confidence Level

- **High confidence:** Clear indicators, no ambiguity
- **Medium confidence:** Some indicators, slight ambiguity
- **Low confidence:** Mixed signals, need clarification

## Topic Extraction

To identify main themes and topics:

### Extract Keywords

```bash
# Get all words, lowercase, count frequency
tr '[:upper:]' '[:lower:]' < "file.md" |
  tr -cs '[:alpha:]' '\n' |
  sort | uniq -c | sort -rn |
  head -20
```

### Identify Technical Terms

Look for patterns:

- Capitalized terms: "SLO", "SRE", "API"
- Hyphenated terms: "error-budget", "circuit-breaker"
- Compound terms: "service level objective", "error budget"

```bash
# Extract technical terms (capitalized, hyphenated, multi-word)
grep -o '[A-Z][A-Z][A-Z]*' "file.md" | sort | uniq
grep -o '[a-z]*-[a-z]*' "file.md" | sort | uniq
```

### Group into Themes

Common SRE themes:

- **Reliability:** SLO, SLI, error budget, availability
- **Observability:** metrics, logs, traces, monitoring
- **Incident management:** incident, postmortem, on-call
- **Performance:** latency, throughput, capacity
- **Deployment:** release, rollback, canary, feature flag

```bash
# Count occurrences of theme keywords
RELIABILITY=$(grep -ic "slo\|sli\|error budget\|availability" "file.md")
OBSERVABILITY=$(grep -ic "metric\|log\|trace\|monitor" "file.md")
INCIDENT=$(grep -ic "incident\|postmortem\|on-call" "file.md")
```

### Suggest Topics Array

Return structured topics:

```json
{
  "topics": ["error budgets", "SLOs", "reliability"],
  "themes": ["Reliability", "SRE Concepts"],
  "confidence": "high"
}
```

## Atomicity Assessment

To check if note is focused on single concept:

### Count Main Ideas

```bash
# Count H2 headings (main sections)
SECTIONS=$(grep -c "^## " "file.md")

# If more than 3-4 sections, might not be atomic
if [ $SECTIONS -gt 4 ]; then
  echo "⚠️  Multiple topics detected ($SECTIONS sections)"
  echo "Consider splitting into separate notes"
fi
```

### Check Length

```bash
# Count words (excluding frontmatter)
WORDS=$(sed '/^---$/,/^---$/d' "file.md" | wc -w)

# Notes should be brief (200-500 words ideal)
if [ $WORDS -gt 500 ]; then
  echo "ℹ️  Long content ($WORDS words) - might be Reference material"
fi
```

### Assess Focus

- **Single concept:** One clear idea, unified theme
- **Multiple concepts:** Several distinct ideas, could be split
- **Comprehensive:** Reference-style coverage, belongs in 300

## Title Suggestions

For Notes, suggest assertion-style titles:

### Generate Assertion from Content

Pattern: `[Subject] [verb] [outcome]`

Examples:
- "Circuit breakers prevent cascading failures"
- "Error budgets enable feature velocity"
- "Exponential backoff reduces load spikes"
- "Graceful degradation maintains user experience"

### Extract Key Claim

Look for:
1. Main assertion in first paragraph
2. Thesis statement
3. Conclusion summary

```bash
# Extract first sentence as potential title
FIRST_SENTENCE=$(sed -n '/^[^#]/p' "file.md" | head -n 1)
```

### Convert to Title Case

```bash
# Convert sentence to title
echo "$FIRST_SENTENCE" |
  awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) tolower(substr($i,2))}1'
```

## Suggest Destination Folder

Based on classification and topics:

### For Notes (200 - Notes/)

Notes go directly in `200 - Notes/` (flat structure):

```
200 - Notes/Circuit breakers prevent cascading failures.md
200 - Notes/Error budgets enable feature velocity.md
```

### For References (300 - Reference/)

References go in topic-specific subfolders:

**Analyze topics to suggest subfolder:**

```json
{
  "topics": ["terraform", "infrastructure"],
  "suggested_folder": "300 - Reference/terraform/"
}

{
  "topics": ["SLO", "error budget"],
  "suggested_folder": "300 - Reference/SRE-Concepts/"
}

{
  "topics": ["book summary", "SRE"],
  "suggested_folder": "300 - Reference/Reading/Book-Summaries/"
}
```

**Common Reference subfolders:**

- `SRE-Concepts/` - Core SRE principles
- `terraform/` - Infrastructure as Code
- `Reading/Book-Summaries/` - Book notes
- `Tools/` - Tool documentation
- `Incident-Management/` - Runbooks, procedures
- `Databases/` - Database-related docs

### Match to Existing Structure

```bash
# Get list of existing Reference subfolders
find "300 - Reference" -type d -mindepth 1 | sort

# Suggest closest match based on topics
# Example: topics contain "database" → suggest "300 - Reference/Databases/"
```

## Output Format

Standard output structure for classification:

```json
{
  "type": "reference",
  "confidence": "high",
  "reasoning": "Contains external quotes and code blocks",
  "topics": ["error budgets", "SLOs", "reliability"],
  "themes": ["Reliability", "SRE Concepts"],
  "suggested_destination": "300 - Reference/SRE-Concepts/",
  "suggested_title": "Error Budget Calculations",
  "atomicity": "single_concept",
  "word_count": 342
}
```

## Edge Cases

### Ambiguous Content

When indicators conflict:

```
📄 Content Analysis:
- Has first-person language (Note indicator)
- Has extensive code (Reference indicator)
- Mixed style

Help me decide:
1. Is this your synthesis/opinion, or documentation?
2. Will this content need regular updates from external sources?
3. Do you reference this for lookup, or is it an insight?
```

### Hybrid Content

Some content might be both:

```
Option A: Split into separate files
  - Note: "Your insight about X"
  - Reference: "Documentation for X"

Option B: Choose primary type
  - If mainly insight → Note
  - If mainly lookup → Reference
```

### New Topic Without Folder

If topics don't match existing Reference structure:

```
⚠️  Topics ["new-topic"] don't match existing folders

Options:
A) Create new folder: "300 - Reference/new-topic/"
B) Place in closest match: "300 - Reference/SRE-Concepts/"
C) Specify custom location
```

## Integration with Other Utilities

**Content analyzer provides data for:**
- **classify-inbox**: Determines destination folder
- **create-note**: Suggests title and structure
- **moc-matcher**: Topics feed into MOC suggestions

**Content analyzer uses:**
- **vault-scanner**: Existing Reference folder structure
- **frontmatter**: Type and source fields help classification

## Best Practices

1. **Check multiple indicators** - Don't rely on single signal
2. **Consider context** - Same content might differ by use case
3. **Assess confidence** - Report when uncertain
4. **Ask user when ambiguous** - Better than wrong classification
5. **Respect existing structure** - Suggest folders that exist
6. **Maintain atomicity** - Notes should be focused
7. **Generate good titles** - Assertions for Notes, descriptive for Reference
8. **Extract meaningful topics** - Not just word frequency
9. **Use themes** - Group topics into broader categories
10. **Preserve user intent** - User knows their purpose best

## Usage Pattern

Standard pattern for content analysis:

```bash
# 1. Read file content
CONTENT=$(cat "file.md")

# 2. Check for Note indicators
if echo "$CONTENT" | grep -qi "I think\|I've learned\|In my experience"; then
  TYPE="note"
  CONFIDENCE="high"
  REASONING="Contains first-person synthesis"
fi

# 3. Check for Reference indicators
if echo "$CONTENT" | grep -q "^source:\|^\`\`\`\|^> "; then
  TYPE="reference"
  CONFIDENCE="high"
  REASONING="Contains external content and code"
fi

# 4. Extract topics
TOPICS=$(extract_topics "$CONTENT")

# 5. Suggest destination
if [ "$TYPE" = "note" ]; then
  DEST="200 - Notes/"
else
  DEST=$(suggest_reference_folder "$TOPICS")
fi

# 6. Present to user
echo "📄 Content Analysis:"
echo "- Type: $TYPE (Confidence: $CONFIDENCE)"
echo "- Topics: $TOPICS"
echo "- Suggested destination: $DEST"
echo "- Reasoning: $REASONING"
```

## Summary

The content analyzer provides consistent classification by:
- Distinguishing Note from Reference material
- Extracting topics and themes
- Assessing note atomicity
- Suggesting appropriate titles
- Recommending destination folders
- Reporting confidence levels
- Handling ambiguous content

All commands should use these patterns for consistent content analysis.
