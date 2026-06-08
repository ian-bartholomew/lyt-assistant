# Deep Research Engine

Reference for the `/research` skill's **deep depth only**. When `DEPTH=deep`, the
information-gathering and verification phases are replaced by a parallel,
cross-checked investigation modeled on Claude Code's bundled `/deep-research`
workflow. `brief` and `standard` do NOT use this engine — they keep the
sequential gather + single fact-checker described in SKILL.md.

The white-paper output format is unchanged. This engine changes only HOW
sources are gathered and HOW claims are verified before synthesis.

## Pipeline

```
decompose topic  ->  parallel research agents  ->  cross-check & vote  ->  synthesize survivors
   (4-6 angles)        (1 Agent per angle)          (drop failures)        (white paper)
```

## Step A: Decompose into sub-questions

Break the topic into **4-6 investigative sub-questions total**. The table below
is a menu of seed angles — pick the ones that fit and add 0-2 topic-specific
angles, landing on 4-6 overall (don't force all six rows):

| Angle | Sub-question shape |
|-------|--------------------|
| Mechanics / definition | What is X and how does it work? |
| Theory / foundations | What principles or math underpin X? Who originated it? |
| Real-world examples | Where is X used in practice? Concrete worked cases? |
| Comparisons | How does X differ from related approaches Y, Z? |
| Limitations / criticisms | When does X fail or not apply? Known criticisms? |
| Topic-specific | (e.g. for a protocol: wire format; for a library: API surface) |

**Pre-flight gate:** show the chosen sub-questions to the user and wait for
approval BEFORE dispatching any agents (the user may add, drop, reword, or
cancel). This gate runs here in Step A — not at SKILL.md Step 5, which is the
later post-synthesis content preview. Spend no fan-out tokens until approved.

## Step B: Parallel fan-out

Dispatch **one research agent per sub-question, all in a single message** (N
`Agent` tool calls together — same parallel-dispatch pattern the skill already
uses for the two reviewers). Exactly one agent per sub-question: N agents = N
sub-questions (so 4-6 agents). Use `subagent_type: general-purpose`. Each agent
runs in isolated context with tools `[WebSearch, WebFetch, Grep]`. Decide the
Context7 question ONCE for the whole run from the original topic: if the topic
is a library/framework/API, give every agent the Context7 tools too; otherwise
no agent gets them. Don't mix per-agent.

**Research-agent prompt template** (substitute `<TOPIC>` and `<SUB_QUESTION>`):

```
You are one of several parallel research agents investigating "<TOPIC>".
Your assigned angle: <SUB_QUESTION>

Search the web and fetch 2-3 authoritative sources that answer your angle.
Prioritize: official docs / standards bodies / peer-reviewed > reputable
engineering blogs / Wikipedia > everything else.

Return ONLY a list of ATOMIC CLAIMS. One fact per claim. For each claim:

- claim: <single factual statement — definition, number, date, formula, attributed position>
- sources: <one or more URLs that directly support this claim>
- tier: <1 | 2 | 3>   (see tier definitions below)
- note: <one line: how strongly the source supports it; any caveat>

Do not synthesize prose. Do not include opinions or claims you could not
source. If you cannot find authoritative support for your angle, return an
empty list and say so.

Source tiers:
- Tier 1: official documentation, standards (RFC/IETF/W3C), peer-reviewed
  academic papers, primary vendor docs.
- Tier 2: reputable engineering sources (Google SRE, AWS Builders' Library,
  Martin Fowler, well-maintained Wikipedia).
- Tier 3: personal blogs, forums, marketing, unverifiable pages.
```

## Step C: Cross-check & vote

Merge every agent's claims into one pool. Group claims that assert the **same
fact** (semantic dedup across agents — different wording, same assertion).
Then rule on each grouped claim:

| Outcome | Rule |
|---------|------|
| **SURVIVES** | Backed by >=2 independent sources, OR by >=1 Tier-1 source and not contradicted by any agent. |
| **CONTRADICTED** | Two agents assert conflicting facts. Keep the side with higher aggregate source authority (more / higher-tier sources). If authority is tied, DROP the claim entirely. |
| **DROPPED** | Single Tier-2/Tier-3 source only with no corroboration; or the losing side of a contradiction. |

Only **SURVIVING** claims proceed to synthesis. Dropped and contradicted-out
claims are removed — **silently, not present in the final document** (no
appendix, no inline warning). The run summary reports counts only, in two
buckets: "survived" and "dropped". CONTRADICTED-out claims count toward
"dropped" (the tally has no separate contradicted bucket).

"Independent sources" means different origins — two pages on the same vendor
docs site, or the same article mirrored, count as one source.

## Step D: Synthesize survivors

Build the white paper (the standard six H2 sections) from the surviving claims
only. Map each sub-question's surviving findings onto the deep Analysis
sub-sections (Mechanics, Theory, Examples, Use Cases, Comparisons, Limitations,
plus any topic-specific threads) — include a sub-section only when its
sub-question yielded surviving claims. Apply the normal numbered `[N]` inline
citations and
`## References` list from the surviving claims' sources. Populate the `sources:`
frontmatter from those same URLs.

## Verification note (interaction with SKILL.md Step 7)

Cross-check voting (Step C) IS the factual verification for deep. Therefore in
SKILL.md Step 7, the standalone fact-checker agent (7b) is **skipped for deep** —
running it again would re-verify already-cross-checked claims. The structure
review (7a) still runs at every depth, deep included.

## Run summary additions

When reporting completion for a deep run, add one line with the vote tally:

```
Cross-check: 23 claims gathered across 5 angles, 18 survived, 5 dropped
```

This is a count only. Do NOT list the dropped claims in the document or the
summary body.
