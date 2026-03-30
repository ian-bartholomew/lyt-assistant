# LYT Assistant Plugin

A comprehensive Claude Code plugin for managing an Obsidian vault using the Linking Your Thinking (LYT) note-taking system.

## Overview

This plugin provides intelligent classification, link discovery, MOC health checking, note creation assistance, and automated research capabilities for managing a knowledge base organized with the LYT system.

## Features

### User Commands

- **`/classify-inbox`** - Interactive file classifier for processing inbox items
- **`/create-note`** - Guided creation of properly structured Notes or Reference files
- **`/discover-links`** - Find missing connections between existing notes
- **`/check-moc-health`** - Analyze MOC quality and suggest improvements
- **`/research <topic>`** - Research and create well-structured reference notes

## LYT System Structure

The plugin expects your vault to follow the LYT folder structure:

- **000 - Inbox/** - Capture zone for all new content (temporary)
- **100 - MOCs/** - Maps of Content for navigation and topic organization
- **200 - Notes/** - Atomic concept notes in your own words
- **300 - Reference/** - Configs, runbooks, book notes, and external materials
- **400 - Archive/** - Stale or superseded content

## Installation

See [INSTALL.md](INSTALL.md) for detailed installation instructions.

**Quick install from GitHub:**

```bash
claude plugin marketplace add github:ian-bartholomew/lyt-assistant
claude plugin install lyt-assistant@ian-bartholomew-lyt-assistant
```

## Usage Examples

### Process Inbox Files

```bash
/classify-inbox
```

Analyzes each inbox file and suggests:

- Destination folder (Notes vs Reference)
- Relevant MOC links
- Related notes to cross-link

### Create a New Note

```bash
/create-note
```

Guides you through creating a properly structured note with appropriate links and frontmatter.

### Find Missing Connections

```bash
/discover-links
```

Scans your vault for notes that mention similar topics but aren't linked together, grouped by theme.

### Check MOC Health

```bash
/check-moc-health
```

Analyzes a MOC for:

- Broken links
- Missing coverage (orphaned notes)
- Stale references

### Research a Topic

```bash
/research Little's Law
```

Researches the topic using web search, creates a structured reference note with sources, and suggests relevant MOCs and links.

## Architecture

The plugin uses a shared utility architecture:

- **Skills/** - User-invocable commands
- **lib/** - Shared utilities for consistent behavior
  - `vault-scanner.md` - Vault traversal and indexing
  - `link-parser.md` - Link extraction and manipulation
  - `frontmatter.md` - YAML frontmatter operations
  - `content-analyzer.md` - Classify Note vs Reference types
  - `moc-matcher.md` - Match content to relevant MOCs

## Design Philosophy

- **Interactive workflow** - Suggest, edit, execute pattern
- **Zero data loss** - Atomic operations with rollback support
- **DRY architecture** - Shared utilities ensure consistency
- **User control** - Review and edit all suggestions before execution

## Requirements

- Obsidian vault following LYT system structure
- Claude Code with access to Read, Write, Edit, Grep, Glob, Bash, WebFetch tools

## Version

Current version: 0.1.0

## Author

Ian Bartholomew (<ian@ianbartholomew.com>)
