# MOC Matcher Utility

This utility provides instructions for matching content to relevant Maps of Content (MOCs) in the LYT system.

## Purpose

Provide consistent MOC suggestion and matching across all LYT Assistant commands. Ensures content is properly connected to relevant organizational structures.

## What is a MOC?

A **Map of Content (MOC)** is an organizational note that:
- Lives in `100 - MOCs/`
- Contains links to related notes organized by theme
- Uses sections to group related topics
- Serves as an entry point for exploring a subject area
- Replaces deep folder hierarchies with flexible linking

**Example MOC:**

```markdown
# SRE Concepts MOC

## Reliability Patterns

- [[Circuit Breaker]]
- [[Bulkhead Pattern]]
- [[Exponential Backoff]]

## Service Level Objectives

- [[SLOs]]
- [[SLIs]]
- [[Error Budget]]

## Related MOCs

- [[Incident Management MOC]]
- [[Observability MOC]]
```

## Core Operations

### Find Relevant MOCs for Content

To match content to appropriate MOCs:

#### 1. Extract Content Topics

Using content-analyzer utility:

```bash
# Get topics from content
TOPICS=$(analyze_topics "file.md")
# Example: ["SLO", "error budget", "reliability"]
```

#### 2. Get All MOCs

Using vault-scanner utility:

```bash
# List all MOC files
MOC_FILES=$(find "100 - MOCs" -type f -name "*.md")
```

#### 3. Score Each MOC

For each MOC, calculate relevance score:

**A. Keyword Match Score:**

```bash
# Count how many content topics appear in MOC
for moc in $MOC_FILES; do
  SCORE=0
  for topic in $TOPICS; do
    if grep -qi "$topic" "$moc"; then
      SCORE=$((SCORE + 1))
    fi
  done
  echo "$SCORE $moc"
done
```

**B. Link Overlap Score:**

```bash
# Check if MOC already links to related content
# Extract links from MOC
MOC_LINKS=$(grep -o '\[\[[^]]*\]\]' "$moc" | sed 's/\[\[\([^]]*\)\]\]/\1/')

# Check overlap with content topics
OVERLAP=0
for link in $MOC_LINKS; do
  if echo "$TOPICS" | grep -qi "$link"; then
    OVERLAP=$((OVERLAP + 1))
  fi
done
```

**C. Title Similarity Score:**

```bash
# Compare MOC title with content topics
MOC_TITLE=$(basename "$moc" .md)
for topic in $TOPICS; do
  if echo "$MOC_TITLE" | grep -qi "$topic"; then
    TITLE_MATCH=1
  fi
done
```

#### 4. Rank MOCs by Relevance

Combine scores:

```bash
# Total score = (keyword_matches * 2) + link_overlaps + (title_match * 3)
TOTAL_SCORE=$((KEYWORD_SCORE * 2 + OVERLAP + TITLE_MATCH * 3))
```

Sort by total score, descending.

#### 5. Return Top Matches

Return 2-3 most relevant MOCs with confidence levels:

```json
{
  "suggested_mocs": [
    {
      "name": "SLOs MOC",
      "confidence": "high",
      "score": 8,
      "reason": "Directly discusses SLO concepts (3 keyword matches)"
    },
    {
      "name": "SRE Concepts MOC",
      "confidence": "medium",
      "score": 4,
      "reason": "General SRE topic (1 keyword match, related MOC)"
    }
  ]
}
```

## Confidence Levels

### High Confidence

- Score >= 5
- Multiple keyword matches
- Title directly matches topic
- Clear thematic fit

**Example:** Content about "Error Budgets" → "SLOs MOC" (high confidence)

### Medium Confidence

- Score 2-4
- Some keyword matches
- Related but not primary topic
- Broader categorization

**Example:** Content about "Error Budgets" → "SRE Concepts MOC" (medium confidence)

### Low Confidence

- Score 1
- Weak connection
- Very broad categorization
- Questionable fit

**Example:** Content about "Error Budgets" → "Engineering MOC" (low confidence)

## MOC Creation Suggestions

### Detect Need for New MOC

Suggest creating a new MOC when:

1. **Multiple notes share a topic not covered by existing MOCs:**
   ```bash
   # Count notes with shared topic
   TOPIC="circuit breakers"
   COUNT=$(grep -rl "$TOPIC" "200 - Notes" "300 - Reference" | wc -l)

   if [ $COUNT -ge 3 ]; then
     # Check if MOC exists
     if ! find "100 - MOCs" -name "*circuit*" | grep -q .; then
       echo "💡 Consider creating: 'Reliability Patterns MOC'"
     fi
   fi
   ```

2. **Existing MOC has too many items (>30 links):**
   ```bash
   LINK_COUNT=$(grep -o '\[\[[^]]*\]\]' "moc.md" | wc -l)
   if [ $LINK_COUNT -gt 30 ]; then
     echo "💡 Consider splitting into sub-MOCs"
   fi
   ```

3. **Topic is subcategory of existing MOC:**
   ```bash
   # If "SRE Concepts MOC" has section "## Reliability Patterns"
   # with 10+ items, suggest: "Reliability Patterns MOC"
   ```

### Suggest MOC Name

Generate MOC names following patterns:

**Pattern 1: Topic + MOC**
- "Reliability Patterns MOC"
- "Incident Management MOC"
- "Observability MOC"

**Pattern 2: Broad Category + MOC**
- "SRE Concepts MOC"
- "Engineering Principles MOC"
- "Laws & Principles MOC"

**Pattern 3: Domain + MOC**
- "Terraform MOC"
- "Kubernetes MOC"
- "Databases MOC"

```bash
# Generate from topics
TOPIC="reliability patterns"
MOC_NAME=$(echo "$TOPIC" | sed 's/.*/\L&/; s/\b\w/\U&/g') MOC"
# Output: "Reliability Patterns MOC"
```

### Check if Subcategory of Existing MOC

Before suggesting new MOC:

```bash
# Check if topic is section in existing MOC
for moc in $(find "100 - MOCs" -name "*.md"); do
  if grep -q "^## .*$TOPIC" "$moc"; then
    echo "ℹ️  '$TOPIC' is already a section in $(basename $moc)"
    echo "Consider adding to existing MOC rather than creating new one"
  fi
done
```

## MOC Patterns

### Primary vs Secondary MOCs

**Primary MOC:** Direct, strong relationship
- Add to frontmatter `mocs:` field
- High confidence match

**Secondary MOC:** Related but not central
- Mention in content or "Related MOCs" section
- Medium/low confidence match

### MOC Hierarchies

MOCs can link to other MOCs:

```markdown
# SRE Concepts MOC

## Sub-domains

- [[Reliability Patterns MOC]]
- [[Observability MOC]]
- [[Incident Management MOC]]

## Related

- [[Engineering Principles MOC]]
```

**When matching:**
- Suggest specific sub-MOC first
- Then suggest parent MOC
- Don't suggest both if one is clearly better

### Home/Index MOCs

Some vaults have a "Home" or "Index" MOC:

```markdown
# Home

## Main Areas

- [[SRE MOC]]
- [[Development MOC]]
- [[Management MOC]]
```

**Don't suggest Home MOC** unless content is truly top-level organizational.

## Matching Strategies

### Strategy 1: Keyword-Based

Simple and fast, works for most cases:

```bash
# Extract keywords from content
KEYWORDS=$(get_keywords "file.md")

# Match against MOC titles and content
for moc in $MOC_FILES; do
  for keyword in $KEYWORDS; do
    if grep -qi "$keyword" "$moc"; then
      # Score match
    fi
  done
done
```

**Pros:** Fast, straightforward
**Cons:** Misses semantic relationships

### Strategy 2: Link-Based

Use existing link structure:

```bash
# Get links from content
CONTENT_LINKS=$(grep -o '\[\[[^]]*\]\]' "file.md")

# Find MOCs that also link to those targets
for moc in $MOC_FILES; do
  MOC_LINKS=$(grep -o '\[\[[^]]*\]\]' "$moc")
  OVERLAP=$(comm -12 <(echo "$CONTENT_LINKS") <(echo "$MOC_LINKS") | wc -l)
done
```

**Pros:** Leverages existing structure
**Cons:** Only works if content has links

### Strategy 3: Semantic Similarity

Use related terms and concepts:

```bash
# Define term relationships
SRE_TERMS="slo sli error-budget availability reliability"
INCIDENT_TERMS="incident postmortem on-call pager runbook"
OBSERVABILITY_TERMS="metrics logs traces monitoring alerting"

# Match content to term groups
if echo "$CONTENT" | grep -qi "$SRE_TERMS"; then
  SUGGEST="SRE Concepts MOC"
fi
```

**Pros:** Catches semantic relationships
**Cons:** Requires term mapping

## Output Format

Standard MOC matching output:

```json
{
  "suggested_mocs": [
    {
      "name": "SLOs MOC",
      "path": "100 - MOCs/SLOs MOC.md",
      "confidence": "high",
      "reason": "Directly discusses SLO concepts (3 keyword matches)",
      "score": 8
    },
    {
      "name": "SRE Concepts MOC",
      "path": "100 - MOCs/SRE Concepts MOC.md",
      "confidence": "medium",
      "reason": "General SRE topic (1 keyword match, related parent MOC)",
      "score": 4
    }
  ],
  "create_new_moc": false,
  "new_moc_suggestion": null
}
```

When new MOC should be created:

```json
{
  "suggested_mocs": [],
  "create_new_moc": true,
  "new_moc_suggestion": {
    "name": "Reliability Patterns MOC",
    "reason": "3+ notes about reliability patterns, no existing MOC",
    "notes_to_include": [
      "200 - Notes/Circuit breakers prevent cascading failures.md",
      "200 - Notes/Bulkhead pattern isolates failures.md",
      "300 - Reference/SRE-Concepts/Exponential Backoff.md"
    ]
  }
}
```

## Validation

### Check MOC Exists

Before suggesting:

```bash
MOC_NAME="SRE Concepts MOC"
if ! find "100 - MOCs" -name "${MOC_NAME}.md" | grep -q .; then
  echo "⚠️  MOC doesn't exist: $MOC_NAME"
  echo "Options:"
  echo "A) Suggest different MOC"
  echo "B) Create new MOC"
fi
```

### Verify MOC is Appropriate

Check MOC isn't:
- Too broad (Home, Index)
- Too specific (single note topic)
- Deprecated/archived

```bash
# Check if MOC is in archive
if find "400 - Archive" -name "${MOC_NAME}.md" | grep -q .; then
  echo "⚠️  MOC is archived, not suggesting"
fi
```

## Edge Cases

### No MOCs Exist

If vault has no MOCs:

```
ℹ️  No MOCs found in vault.

MOCs help organize content. Consider creating:
- "Home MOC" - Main entry point
- "[Topic] MOC" - For your main subject areas
```

### Too Many Matches (All Low Confidence)

If many MOCs match weakly:

```
📊 Multiple potential MOCs (all low confidence):
- SRE Concepts MOC
- Engineering MOC
- Observability MOC

Unable to determine best fit. Which MOC is most relevant?
```

### No Matches Found

If no MOC matches:

```
📊 No existing MOCs match this content.

Topics: [reliability, patterns]

Options:
A) Create new MOC: "Reliability Patterns MOC"
B) Add to broader MOC: "SRE Concepts MOC"
C) Skip MOC linking for now
```

### Ambiguous Topic

If content spans multiple domains:

```
📊 Content relates to multiple domains:
- Primary: SLOs (high confidence → "SLOs MOC")
- Secondary: Incident Management (medium confidence → "Incident Management MOC")

Add to both MOCs?
```

## Integration with Other Utilities

**MOC matcher provides data for:**
- **classify-inbox**: Suggests MOCs for inbox files
- **create-note**: Suggests MOCs for new notes
- **research**: Suggests MOCs for researched topics
- **discover-links**: Identifies orphaned content missing MOC links

**MOC matcher uses:**
- **vault-scanner**: Gets list of all MOCs
- **content-analyzer**: Gets topics and themes from content
- **link-parser**: Analyzes existing link structures

## Best Practices

1. **Suggest 2-3 MOCs** - Primary and related
2. **Include confidence levels** - Help user decide
3. **Explain reasoning** - Why this MOC?
4. **Check MOC exists** - Don't suggest nonexistent MOCs
5. **Prefer specific over general** - "SLOs MOC" before "SRE Concepts MOC"
6. **Detect new MOC needs** - When topic has no home
7. **Respect hierarchies** - Sub-MOC before parent MOC
8. **Avoid over-tagging** - 1-3 MOCs max per note
9. **Consider link overlap** - Existing connections matter
10. **Ask when ambiguous** - User knows intent

## Usage Pattern

Standard pattern for MOC matching:

```bash
# 1. Analyze content for topics
TOPICS=$(analyze_content_topics "file.md")

# 2. Get all MOCs
MOC_FILES=$(find "100 - MOCs" -type f -name "*.md")

# 3. Score each MOC
MATCHES=()
for moc in $MOC_FILES; do
  SCORE=0

  # Keyword matches
  for topic in $TOPICS; do
    if grep -qi "$topic" "$moc"; then
      SCORE=$((SCORE + 2))
    fi
  done

  # Title match
  MOC_TITLE=$(basename "$moc" .md)
  if echo "$MOC_TITLE" | grep -qi "$TOPICS"; then
    SCORE=$((SCORE + 3))
  fi

  # Store if score > 0
  if [ $SCORE -gt 0 ]; then
    MATCHES+=("$SCORE|$moc")
  fi
done

# 4. Sort and select top matches
TOP_MOCS=$(echo "${MATCHES[@]}" | tr ' ' '\n' | sort -rn | head -3)

# 5. Determine confidence
for match in $TOP_MOCS; do
  SCORE=$(echo "$match" | cut -d'|' -f1)
  MOC=$(echo "$match" | cut -d'|' -f2)

  if [ $SCORE -ge 5 ]; then
    CONFIDENCE="high"
  elif [ $SCORE -ge 2 ]; then
    CONFIDENCE="medium"
  else
    CONFIDENCE="low"
  fi

  echo "🗺️  $MOC (confidence: $CONFIDENCE, score: $SCORE)"
done

# 6. Check if new MOC needed
if [ ${#MATCHES[@]} -eq 0 ]; then
  echo "💡 Consider creating new MOC for: $TOPICS"
fi
```

## Summary

The MOC matcher provides consistent MOC suggestions by:
- Analyzing content topics and themes
- Scoring MOCs by relevance
- Ranking matches by confidence
- Detecting need for new MOCs
- Suggesting appropriate MOC names
- Respecting MOC hierarchies
- Handling edge cases gracefully

All commands should use these patterns for consistent MOC matching.
