# Changelog

All notable changes to the LYT Assistant plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 2.18.1 (2026-06-09)

- Use the ${CLAUDE_SKILL_DIR} substitution (with announced-dir fallback) for
  script invocations in meeting-action-items and support-learnings.

## 2.18.0 (2026-06-09)

- support-learnings: consult the EOD shared thread cache
  (/tmp/eod-fes-support-cache.json) for thread bodies, falling back to live
  Slack reads per thread. Adds vendored fes_support_cache.py helper.

## 2.17.0 (2026-06-09)

- meeting-action-items 0.8.0: deterministic core script (meeting_action_items.py).
  list/apply subcommands, per-item atomic state writes, AskUserQuestion triage.
  Removes the TTY-dependent bash read/EDITOR loop. State schema unchanged.

## [2.16.0] - 2026-06-08

### Changed

- `/research --depth deep` now uses a **Deep Research Engine** (`lib/deep-research.md`) modeled on Claude Code's bundled `/deep-research`: it decomposes the topic into 4-6 sub-questions, gates on a sub-question preview, fans out one parallel research agent per sub-question, cross-checks every gathered claim across the agents' independent sources, and synthesizes only the claims that survive a consensus vote. Claims that fail cross-checking are dropped silently (counts reported in the run summary). `brief` and `standard` are unchanged.
- For `deep`, the standalone fact-checker agent (Step 7b) is skipped — cross-check voting already verifies claims against multiple independent sources. The structure review (7a) still runs at every depth. Research skill version `0.6.0` -> `0.7.0`.

## [2.13.0] - 2026-05-12

### Removed

- `/start-of-day` moved out of this plugin into user-private skills (`~/.claude/skills/start-of-day/`). It was tied to the user's personal Todoist setup, not the LYT/wiki workflow.
- `/end-of-day` moved out of this plugin into user-private skills (`~/.claude/skills/end-of-day/`). The sibling skills it orchestrates (`compile`, `meeting-action-items`, `support-learnings`, `internal-channel-learnings`, `meeting-ingest`) remain in this plugin and are now invoked as `lyt-assistant:<name>` from the relocated skill.

## [2.12.0] - 2026-05-12

### Changed

- `/meeting-action-items` now runs as part of `/end-of-day` (new Step 5, after the meeting-ingest join), instead of as Step 1 of `/start-of-day`. Action items from each day's meetings are reviewed while the meetings are still fresh, rather than the following morning.
- `/start-of-day` is now a single-step routine (today + overdue, with edit loop). Its skill version bumps to `0.2.0` and `Skill` is removed from `allowed-tools`.

## [0.1.0] - 2026-03-27

### Added

#### Core Skills

- **`/classify-inbox`** - Interactive inbox file classifier with intelligent destination suggestions
- **`/create-note`** - Guided note creation with proper LYT structure
- **`/discover-links`** - Automatic link discovery grouped by theme
- **`/check-moc-health`** - Comprehensive MOC auditing and maintenance
- **`/research <topic>`** - Topic research with web search and Context7 integration

#### Shared Utilities

- `vault-scanner.md` - Vault traversal and indexing operations
- `link-parser.md` - Obsidian wiki-link extraction and manipulation
- `frontmatter.md` - YAML frontmatter operations
- `content-analyzer.md` - Note vs Reference classification
- `moc-matcher.md` - MOC relevance matching

#### Documentation

- Complete README with usage examples
- Comprehensive TESTING.md with 10 test cases
- Example outputs for classify-inbox and check-moc-health
- CHANGELOG for version tracking

#### Features

- Interactive workflow with AskUserQuestion integration
- Content analysis using heuristics for Note vs Reference classification
- MOC suggestion based on topic matching
- Link discovery with automatic grouping
- Broken link detection and stub file creation
- Source attribution for research notes
- Frontmatter management with standard fields
- Error handling for common edge cases

### Design Principles

- Progressive disclosure (lean SKILL.md, detailed lib/ utilities)
- DRY architecture (shared utilities across all skills)
- Interactive editing before execution
- Zero data loss with atomic operations
- Comprehensive error handling

### Technical Details

- Plugin version: 0.1.0
- Total files: 16
- Skills: 5 user-invocable commands
- Shared utilities: 5 reference documents
- Examples: 2 complete workflow examples
- Total documentation: ~15,000 words

### Author

- Ian Bartholomew (<ian@ianbartholomew.com>)

### Notes

- Initial release
- Designed for Obsidian vaults using LYT system
- Requires Claude Code with Read, Write, Edit, Bash, Grep, Glob, WebFetch, AskUserQuestion tools
- Optional: Context7 MCP integration for library documentation

---

## [Unreleased]

### Planned Features

- `/refactor-note` - Convert Reference to Note with guided transformation
- `/archive-stale` - Automated archival of old content
- `/sync-backlinks` - Ensure bidirectional linking consistency
- `--dry-run` mode for all commands
- Bulk operations (classify entire inbox with review)
- Template system for different note types
- Integration with weekly review process
- Vault health statistics and analytics

### Potential Improvements

- Performance optimization for large vaults (>500 files)
- Advanced semantic similarity for link matching
- Multi-language support for content analysis
- Customizable classification rules
- Plugin settings configuration
- Export/import MOC structures
- Automated testing framework

---

## Version History

- **0.1.0** (2026-03-27) - Initial release with 5 core skills
