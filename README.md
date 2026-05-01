# LYT Assistant Plugin

A Claude Code plugin for managing an Obsidian vault using a [Karpathy-style LLM wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) system.

## Overview

The LLM wiki pattern: you curate sources, direct analysis, and ask good questions. The LLM summarizes, cross-references, files, and maintains everything. Obsidian is the IDE; the LLM is the programmer; the wiki is the codebase.

This plugin implements the three core operations — **Ingest**, **Query**, and **Lint** — plus a **Compile** pipeline that chains them together, and supporting skills for note creation, link discovery, research, and project management.

## Skills

| Skill | Operation | Description |
|-------|-----------|-------------|
| `/compile` | Compile | Full pipeline — ingest, validate, and discover links in one pass |
| `/ingest` | Ingest | Process raw sources into wiki articles with propagation to related pages |
| `/query <question>` | Query | Ask questions against the wiki, get synthesized answers with citations — good answers become new pages |
| `/lint` | Lint | Structural + content-level health checks (contradictions, investigation suggestions) |
| `/create-note` | — | Guided creation of wiki articles with classification and indexing |
| `/discover-links` | — | Find missing connections between wiki articles |
| `/research <topic>` | — | Research topics via web/Context7 and create wiki articles |
| `/create-project` | — | Set up project directories with tracking |
| `/archive-project` | — | Complete projects with knowledge extraction into wiki |

## Wiki Structure

Three layers:

| Layer | Owner | Purpose |
|-------|-------|---------|
| `raw/` | User | Immutable sources (clippings, docs, articles) |
| `wiki/` | LLM | Compiled knowledge — the persistent, compounding artifact |
| Schema (skills + CLAUDE.md) | Both | How the wiki structures, conventions, workflows |

```
raw/                      # Immutable sources
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
maturity: stub | draft | mature | canonical
confidence: low | medium | high
sources: ["[[raw/clippings/source.md]]"]
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

## Usage Examples

### Ingest Raw Sources

```
/ingest
```

Scans `raw/` for unprocessed sources, compiles them into wiki articles, and propagates updates to related existing pages — one source can touch many articles.

### Query the Wiki

```
/query how do circuit breakers relate to bulkheads?
```

Searches the wiki, synthesizes an answer with `[[wikilink]]` citations, and offers to save the answer as a new wiki page.

### Lint the Wiki

```
/lint
```

Runs 10 audit dimensions: 8 structural (indexes, links, frontmatter, orphans, staleness, gaps, domain consistency, structure) + 2 content-level (contradiction detection, investigation suggestions).

### Research a Topic

```
/research Little's Law
```

Researches using web search or Context7, creates a structured wiki article with source attribution.

## Architecture

- **skills/** — User-invocable commands (9 skills)
- **lib/** — Shared utilities
  - `analysis.md` — Content classification, topic extraction, domain matching
  - `obsidian-operations.md` — Obsidian CLI operations for vault I/O

## Design Philosophy

- **Karpathy LLM Wiki** — Raw sources, compiled wiki, co-evolved schema
- **Explorations compound** — Good answers become new wiki pages
- **One source, many pages** — Ingest propagates to related articles
- **Interactive workflow** — Suggest, review, execute
- **Zero data loss** — Atomic operations, provenance tracking
- **Parseable logs** — Consistent `## [date] action | title` format

## Requirements

- Obsidian vault with the wiki structure above
- Obsidian running (for CLI operations)
- Claude Code

## Version

1.0.0

## Author

Ian Bartholomew (<ian@ianbartholomew.com>)
