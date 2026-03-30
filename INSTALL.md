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
- Obsidian vault following the LYT (Linking Your Thinking) system structure

## Verification

After installation, verify the plugin is working:

### 1. Check Plugin List

```bash
claude plugin list
```

Expected output should show:

```
lyt-assistant@ian-bartholomew-lyt-assistant  0.1.0  enabled
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

- `/lyt-assistant:classify-inbox` - Interactive file classifier for processing inbox items
- `/lyt-assistant:create-note` - Guided creation of properly structured Notes or Reference files
- `/lyt-assistant:discover-links` - Find missing connections between existing notes
- `/lyt-assistant:check-moc-health` - Analyze MOC quality and suggest improvements
- `/lyt-assistant:research` - Research and create well-structured reference notes
- `/lyt-assistant:archive-project` - Archive completed projects
- `/lyt-assistant:create-project` - Create new project structure

### 4. Test a Skill

Try running a skill:

```
/lyt-assistant:check-moc-health
```

The skill should execute successfully without any errors about missing files or scripts.

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

### Marketplace Add Fails

If `claude plugin marketplace add` fails:

1. Verify GitHub repository is accessible:

   ```bash
   curl -I https://github.com/ian-bartholomew/lyt-assistant
   ```

2. Check marketplace.json exists:

   ```bash
   curl https://raw.githubusercontent.com/ian-bartholomew/lyt-assistant/main/.claude-plugin/marketplace.json
   ```

3. Ensure you have network connectivity and GitHub access.

### Scripts Not Found

If the `check-moc-health` skill reports missing scripts:

1. Verify scripts are in the cached plugin:

   ```bash
   ls -la ~/.claude/plugins/cache/ian-bartholomew-lyt-assistant/lyt-assistant/*/skills/check-moc-health/scripts/
   ```

2. Check that scripts are executable:

   ```bash
   chmod +x ~/.claude/plugins/cache/ian-bartholomew-lyt-assistant/lyt-assistant/*/skills/check-moc-health/scripts/*.sh
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
