# Example: Classify Inbox Output

This example shows typical output from the `/classify-inbox` skill.

## User Input

```
/classify-inbox
```

## Output

```
Found 2 files in inbox. Processing first file: "Error Budget Calculations.md"

📄 Content Analysis:
- Type: Reference (Confidence: High)
- Topics: error budgets, SLOs, reliability math
- Word count: 342
- Reasoning: Contains formulas and lookup information

📁 Suggested Destination:
   300 - Reference/SRE-Concepts/

🗺️  Suggested MOCs:
  - [[SLOs MOC]] (high confidence)
  - [[SRE Concepts MOC]] (medium confidence)

🔗 Suggested Related Links:
  - [[Implementing Service Level Objectives-Hidalgo]] (book notes)
  - [[SLO Calculations]] (related reference)

💡 New MOC Opportunity: No

Would you like to:
A) Accept and move (recommended)
B) Edit destination folder
C) Edit links
D) Skip this file
E) Cancel operation

User: A

✅ Moved to: 300 - Reference/SRE-Concepts/Error Budget Calculations.md
✅ Added 2 MOC links to frontmatter
✅ Added 2 related links to Related section
✅ Updated frontmatter with metadata

---

Processing file 2 of 2: "thoughts on circuit breakers.md"

📄 Content Analysis:
- Type: Note (Confidence: High)
- Topics: circuit breakers, fault tolerance, reliability
- First-person synthesis detected
- Suggested title: "Circuit breakers prevent cascading failures"
- Reasoning: Personal insights in your own voice

📁 Suggested Destination:
   200 - Notes/

🗺️  Suggested MOCs:
  - [[Reliability Patterns MOC]] (high confidence)
  - [[SRE Concepts MOC]] (medium confidence)

🔗 Suggested Related Links:
  - [[Bulkhead Pattern]] (related pattern)
  - [[Graceful Degradation]] (related concept)

Would you like to:
A) Accept (including title change)
B) Keep original title
C) Edit destination
D) Edit links
E) Skip this file

User: A

✅ Renamed to: "Circuit breakers prevent cascading failures.md"
✅ Moved to: 200 - Notes/Circuit breakers prevent cascading failures.md
✅ Added 2 MOC links to frontmatter
✅ Added 2 related links
✅ Created proper frontmatter

---

📊 Inbox Processing Complete

Processed: 2 files
Moved: 2 files
- Notes: 1
- References: 1
Links added: 8
MOCs updated: 3

✅ Inbox is now clean!

Next steps:
- Run /discover-links to find additional connections
- Review MOCs for new content coverage
```

## Resulting Files

### File 1: 300 - Reference/SRE-Concepts/Error Budget Calculations.md

```markdown
---
tags: [error-budget, slo, reliability]
created: 2026-03-26
type: external
mocs:
  - [[SLOs MOC]]
  - [[SRE Concepts MOC]]
---

# Error Budget Calculations

[Original content preserved]

## Related

- [[Implementing Service Level Objectives-Hidalgo]]
- [[SLO Calculations]]
```

### File 2: 200 - Notes/Circuit breakers prevent cascading failures.md

```markdown
---
tags: [circuit-breaker, reliability, fault-tolerance]
created: 2026-03-26
mocs:
  - [[Reliability Patterns MOC]]
  - [[SRE Concepts MOC]]
---

# Circuit breakers prevent cascading failures

[Original content preserved]

## Related

- [[Bulkhead Pattern]]
- [[Graceful Degradation]]
```
