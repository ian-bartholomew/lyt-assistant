# Changelog

All notable changes to the LYT Assistant plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- Ian Bartholomew (ian@ianbartholomew.com)

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
