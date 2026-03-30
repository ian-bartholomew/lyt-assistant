#!/bin/bash
#
# check-all.sh - Run comprehensive MOC health checks
# Usage: ./check-all.sh
#   Runs all health check scripts and generates a summary

set -euo pipefail

VAULT_ROOT="${VAULT_ROOT:-$(pwd)}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "╔════════════════════════════════════════════╗"
echo "║     MOC Health Check - Full Analysis      ║"
echo "╔════════════════════════════════════════════╗"
echo ""
echo "Vault: $VAULT_ROOT"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "═══════════════════════════════════════════════"
echo ""

# 1. Structure Analysis
echo "## 1. Structure Analysis"
echo ""
"$SCRIPT_DIR/check-structure.sh"
echo ""
echo "═══════════════════════════════════════════════"
echo ""

# 2. Link Validation
echo "## 2. Link Validation"
echo ""
"$SCRIPT_DIR/check-links.sh"
echo ""
echo "═══════════════════════════════════════════════"
echo ""

# 3. Plain Text Items
echo "## 3. Plain Text Items (Potential Wikilinks)"
echo ""
"$SCRIPT_DIR/check-plain-text.sh"
echo ""
echo "═══════════════════════════════════════════════"
echo ""

# Summary
echo "## Summary"
echo ""

total_mocs=$(find "$VAULT_ROOT/100 - MOCs" -name "*.md" -type f | wc -l | tr -d ' ')
echo "- Total MOCs analyzed: $total_mocs"

total_links=0
for moc in "$VAULT_ROOT/100 - MOCs"/*.md; do
    count=$(grep -o '\[\[[^]]*\]\]' "$moc" 2>/dev/null | wc -l | tr -d ' ')
    total_links=$((total_links + count))
done
echo "- Total wikilinks: $total_links"

echo ""
echo "✅ Health check complete!"
echo ""
echo "To check a specific MOC:"
echo "  ./check-links.sh '100 - MOCs/SRE Concepts MOC.md'"
echo "  ./check-plain-text.sh '100 - MOCs/SRE Concepts MOC.md'"
echo "  ./check-structure.sh '100 - MOCs/SRE Concepts MOC.md'"
