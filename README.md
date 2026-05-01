# LYT Assistant Plugin

A Claude Code plugin for managing an Obsidian vault using a [Karpathy-style LLM wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) system. Automatically captures conversations, extracts Slack channel knowledge, compiles raw sources into structured wiki articles, and maintains wiki health.

## Overview

The LLM wiki pattern: you curate sources, direct analysis, and ask good questions. The LLM summarizes, cross-references, files, and maintains everything. Obsidian is the IDE; the LLM is the programmer; the wiki is the codebase.

This plugin provides the complete pipeline: **automatic conversation capture** via hooks, **Slack channel extraction** skills, the three core operations — **Ingest**, **Query**, and **Lint** — a **Compile** pipeline that chains them together, and supporting skills for note creation, link discovery, research, and project management.

## Skills

| Skill | Operation | Description |
|-------|-----------|-------------|
| `/compile` | Compile | Full pipeline — ingest, validate, and discover links in one pass |
| `/ingest` | Ingest | Process raw sources into wiki articles with propagation to related pages |
| `/query <question>` | Query | Ask questions against the wiki, get synthesized answers with citations — good answers become new pages |
| `/lint` | Lint | Structural + content-level health checks (contradictions, investigation suggestions) |
| `/support-learnings` | Capture | Extract learnings from Slack support channels into raw/ sources |
| `/internal-channel-learnings` | Capture | Extract learnings from internal Slack channels into raw/ sources |
| `/create-note` | — | Guided creation of wiki articles with classification and indexing |
| `/discover-links` | — | Find missing connections between wiki articles |
| `/research <topic>` | — | Research topics via web/Context7 and create wiki articles |
| `/create-project` | — | Set up project directories with tracking |
| `/archive-project` | — | Complete projects with knowledge extraction into wiki |

## Hooks (Automatic)

The plugin registers three hooks that fire automatically during every Claude Code session:

| Hook | Event | Description |
|------|-------|-------------|
| SessionStart | Session begins | Injects wiki index and recent daily log into conversation context |
| SessionEnd | Session ends | Extracts conversation knowledge into daily log via background process |
| PreCompact | Before compaction | Captures context before auto-summarization to prevent knowledge loss |

## Wiki Structure

Three layers:

| Layer | Owner | Purpose |
|-------|-------|---------|
| `raw/` | User | Immutable sources (clippings, docs, articles, Slack extracts) |
| `wiki/` | LLM | Compiled knowledge — the persistent, compounding artifact |
| Schema (skills + CLAUDE.md) | Both | How the wiki structures, conventions, workflows |

```
raw/                      # Immutable sources
├── daily/                # AI conversation logs (auto-captured by hooks)
├── clippings/            # Web clips (Obsidian Web Clipper)
├── support_learnings/    # Slack support channel extracts
├── internal_learnings/   # Internal channel extracts
├── docs/                 # RFCs, proposals
└── daily_notes/          # Brief work notes
wiki/
├── concepts/             # Atomic concept articles (What is X?)
├── guides/               # How-to and operational guides (How do I X?)
├── company/              # Company-specific knowledge (How does our org do X?)
├── learning/             # Learning paths and study notes (What did I learn from X?)
├── _indexes/             # Domain index files
├── _index.md             # Master wiki index
└── _log.md               # Activity log (append-only, parseable)
projects/                 # Active project workspaces
archive/                  # Completed projects
```

### Frontmatter Schema

All wiki articles use:

```yaml
title: Article Title
domain: [sre, resilience]
maturity: stub | draft | developing | mature | canonical
confidence: low | medium | high
compiled_from: ["raw/clippings/source.md"]
related: ["[[kebab-case-article]]"]
last_compiled: 2026-04-21
```

### Activity Log

All operations log to `wiki/_log.md` with parseable prefixes:

```
## [2026-04-21] ingest | Circuit Breaker Pattern
## [2026-04-21] query | How do circuit breakers relate to bulkheads?
## [2026-04-21] lint | Wiki Health Check
## [2026-04-21] create | New Article Title
```

## Installation

See [INSTALL.md](INSTALL.md) for detailed installation instructions.

```bash
claude plugin marketplace add github:ian-bartholomew/lyt-assistant
claude plugin install lyt-assistant@ian-bartholomew-lyt-assistant
```

## Architecture

- **skills/** — User-invocable commands (11 skills)
- **scripts/** — Python automation
  - `compile.py` — Automated LLM compiler (background, via Claude Agent SDK)
  - `lint.py` — Structural health checks (7 checks, generates reports)
  - `query.py` — CLI query engine
  - `flush.py` — Background memory extraction from conversations
  - `session-start.py`, `session-end.py`, `pre-compact.py` — Session lifecycle hooks
  - `config.py`, `utils.py` — Shared configuration and helpers
- **hooks/** — Plugin hook definitions (`hooks.json`)
- **lib/** — Shared utilities
  - `analysis.md` — Content classification, topic extraction, domain matching
  - `obsidian-operations.md` — Obsidian CLI operations for vault I/O
  - `agents-schema.md` — Compilation context for Agent SDK scripts

### State Directory

Runtime state lives at `~/.local/share/lyt-assistant/` (outside the plugin directory):

- `state.json` — Ingestion tracking, cost history
- `vault-config.json` — Vault path configuration
- `reports/` — Lint reports
- `.venv/` — Python virtual environment

## Design Philosophy

- **Karpathy LLM Wiki** — Raw sources, compiled wiki, co-evolved schema
- **Automatic capture** — Conversations and Slack threads become raw sources without manual effort
- **Explorations compound** — Good answers become new wiki pages
- **One source, many pages** — Ingest propagates to related articles
- **Interactive workflow** — Suggest, review, execute
- **Zero data loss** — Atomic operations, provenance tracking
- **Parseable logs** — Consistent `## [date] action | title` format

## Requirements

- Obsidian vault with the wiki structure above
- Obsidian running (for CLI operations)
- Claude Code
- Python 3.12+ and [uv](https://docs.astral.sh/uv/) (for automated scripts and hooks)

## Version

2.0.0

## Author

Ian Bartholomew (<ian@ianbartholomew.com>)
