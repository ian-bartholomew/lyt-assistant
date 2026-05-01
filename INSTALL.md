# Installation Guide

## Quick Install (GitHub)

Install the LYT Assistant plugin directly from GitHub:

```bash
# Add the GitHub marketplace
claude plugin marketplace add github:ian-bartholomew/lyt-assistant

# Install the plugin
claude plugin install lyt-assistant@ian-bartholomew-lyt-assistant

# Reload plugins (or restart Claude Code)
claude reload-plugins
```

The plugin will now auto-load in every Claude Code session without needing the `--plugin-dir` flag!

## Requirements

- Claude Code CLI installed
- Git access to GitHub
- Obsidian vault following the Karpathy-style LLM wiki structure (raw/, wiki/, projects/)
- Python 3.12+ (`python3 --version`)
- [uv](https://docs.astral.sh/uv/) package manager (`uv --version`)

## Post-Install Setup

### 1. Configure Vault Path

Create the vault config so scripts know where your Obsidian vault lives:

```bash
mkdir -p ~/.local/share/lyt-assistant
echo '{"vault_dir": "~/Documents/Work"}' > ~/.local/share/lyt-assistant/vault-config.json
```

Replace `~/Documents/Work` with your actual vault path.

### 2. Remove Old Hooks (if upgrading from claude-memory-compiler)

If you previously used the standalone `claude-memory-compiler` repo with hooks in `~/.claude/settings.json`, **remove those hook entries** to prevent double-firing:

Remove the `SessionStart`, `SessionEnd`, and `PreCompact` entries that reference `claude-memory-compiler` from `~/.claude/settings.json`. The plugin now provides these hooks natively.

### 3. Migrate State (if upgrading)

If you have existing compilation state from `claude-memory-compiler`:

```bash
cp ~/Dev/claude-memory-compiler/scripts/state.json ~/.local/share/lyt-assistant/
cp ~/Dev/claude-memory-compiler/scripts/last-flush.json ~/.local/share/lyt-assistant/
```

This preserves your ingestion history and cost tracking. **Skipping this will cause all sources to be recompiled.**

### 4. Remove Old Global Skills (if upgrading)

If you previously used `support-learnings` or `internal-channel-learnings` as global skills:

```bash
rm -rf ~/.claude/skills/support-learnings
rm -rf ~/.claude/skills/internal-channel-learnings
```

These are now bundled in the plugin as `/lyt-assistant:support-learnings` and `/lyt-assistant:internal-channel-learnings`.

## Verification

After installation, verify the plugin is working:

### 1. Check Plugin List

```bash
claude plugin list
```

Expected output should show:

```
lyt-assistant@ian-bartholomew-lyt-assistant  2.0.0  enabled
```

### 2. Start Claude Code

Navigate to your Obsidian vault and start Claude Code without any flags:

```bash
cd /path/to/your/obsidian/vault
claude
```

### 3. Verify Skills Are Available

In the Claude Code session, type:

```
/help
```

You should see all LYT Assistant skills listed:

- `/lyt-assistant:compile` - Full compilation pipeline (ingest + validate + discover links)
- `/lyt-assistant:ingest` - Process raw sources into wiki articles
- `/lyt-assistant:query` - Ask questions against the wiki with synthesized answers
- `/lyt-assistant:lint` - Structural and content-level wiki health checks
- `/lyt-assistant:review-structure` - Standalone structural quality review for any .md file
- `/lyt-assistant:support-learnings` - Extract learnings from Slack support channels
- `/lyt-assistant:internal-channel-learnings` - Extract learnings from internal Slack channels
- `/lyt-assistant:create-note` - Guided creation of wiki articles with classification
- `/lyt-assistant:discover-links` - Find missing connections between wiki articles
- `/lyt-assistant:research` - Research topics with depth control, validation, and fact-checking
- `/lyt-assistant:create-project` - Create new project structure
- `/lyt-assistant:archive-project` - Archive completed projects

### 4. Verify Hooks

The SessionStart hook should have injected wiki context at the start of your session. Check the system prompt for "Knowledge Base Index" context.

### 5. Test a Skill

Try running a skill:

```
/lyt-assistant:lint
```

The skill should execute successfully and report on wiki health.

## Troubleshooting

### Plugin Not Listed

If the plugin doesn't appear in `claude plugin list`:

```bash
# Try reloading plugins
claude reload-plugins

# Check installed plugins registry
cat ~/.claude/plugins/installed_plugins.json | grep -A 10 "lyt-assistant"
```

### Skills Not Appearing

If skills don't show up in `/help`:

1. Verify the plugin is enabled:

   ```bash
   claude plugin list
   ```

2. Check the cache directory exists:

   ```bash
   ls -la ~/.claude/plugins/cache/ian-bartholomew-lyt-assistant/lyt-assistant/
   ```

3. Try reinstalling:

   ```bash
   claude plugin reinstall lyt-assistant@ian-bartholomew-lyt-assistant
   claude reload-plugins
   ```

### Hooks Not Firing

If the SessionStart hook doesn't inject context:

1. Check Python and uv are installed:

   ```bash
   python3 --version  # Should be 3.12+
   uv --version
   ```

2. Test the hook script manually:

   ```bash
   echo '{}' | UV_PROJECT_ENVIRONMENT=~/.local/share/lyt-assistant/.venv uv run --directory /path/to/plugin python /path/to/plugin/scripts/session-start.py
   ```

3. Check logs for errors:

   ```bash
   cat ~/.local/share/lyt-assistant/flush.log
   ```

4. Restart Claude Code (hooks load at session start).

### Skills Report Missing Files

If a skill reports missing files or scripts:

1. Verify the plugin cache structure:

   ```bash
   ls -la ~/.claude/plugins/cache/ian-bartholomew-lyt-assistant/lyt-assistant/*/skills/
   ```

2. Try reinstalling the plugin:

   ```bash
   claude plugin reinstall lyt-assistant@ian-bartholomew-lyt-assistant
   claude reload-plugins
   ```

## Updating the Plugin

To update to the latest version after changes are pushed to GitHub:

```bash
# Pull latest version
claude plugin update lyt-assistant@ian-bartholomew-lyt-assistant

# Or force reinstall
claude plugin reinstall lyt-assistant@ian-bartholomew-lyt-assistant
claude reload-plugins
```

## Uninstalling

To remove the plugin:

```bash
claude plugin uninstall lyt-assistant@ian-bartholomew-lyt-assistant
```

State files at `~/.local/share/lyt-assistant/` are preserved. Remove them manually if desired.

## Development Workflow

If you're developing the plugin locally, you can use both approaches:

1. **Development mode** (immediate feedback):

   ```bash
   claude --plugin-dir /path/to/lyt-assistant
   ```

   Changes to skill files are immediately visible without reinstalling.

2. **Installed mode** (production):

   ```bash
   claude
   ```

   Plugin auto-loads from GitHub cache. Use this to test the published version.

The `--plugin-dir` flag takes precedence in a session, so you can test local changes while having the GitHub version installed.

## Support

For issues, questions, or contributions:

- GitHub Issues: <https://github.com/ian-bartholomew/lyt-assistant/issues>
- Repository: <https://github.com/ian-bartholomew/lyt-assistant>

## License

MIT License - See [LICENSE](LICENSE) file for details.
