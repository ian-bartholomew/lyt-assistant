#!/bin/bash
#
# check-structure.sh - Analyze MOC structure and organization
# Usage: ./check-structure.sh [moc-file]
#   If no file specified, checks all MOCs

set -euo pipefail

VAULT_ROOT="${VAULT_ROOT:-$(pwd)}"

check_structure() {
    local file="$1"
    local moc_name=$(basename "$file" .md)

    # Count H1 headings (should be 1)
    h1_count=$(grep -c '^# ' "$file" || echo "0")

    # Count sections (## headings)
    section_count=$(grep -c '^## ' "$file" || echo "0")

    # Check if it has "Related MOCs" section
    has_related_mocs=$(grep -q '^## Related MOCs' "$file" && echo "yes" || echo "no")

    # Check if it has Navigation back to Home
    has_navigation=$(grep -q '\[\[Home\]\]' "$file" && echo "yes" || echo "no")

    # Check for frontmatter
    has_frontmatter=$(head -1 "$file" | grep -q '^---$' && echo "yes" || echo "no")

    echo "**$moc_name**"
    echo "- H1 headings: $h1_count $([ $h1_count -eq 1 ] && echo '✅' || echo '⚠️  (should be 1)')"
    echo "- Sections (H2): $section_count"
    echo "- Frontmatter: $([ "$has_frontmatter" = "yes" ] && echo '✅' || echo '❌')"

    # Skip Related MOCs check for Home.md (it's the entry point)
    if [ "$moc_name" != "Home" ]; then
        echo "- Related MOCs section: $([ "$has_related_mocs" = "yes" ] && echo '✅' || echo '❌')"
        echo "- Navigation to Home: $([ "$has_navigation" = "yes" ] && echo '✅' || echo '❌')"
    else
        echo "- Entry point (no Related MOCs needed) ✅"
    fi

    echo ""
}

# Main execution
cd "$VAULT_ROOT"

echo "# MOC Structure Analysis"
echo ""

if [ $# -eq 1 ]; then
    # Check single MOC
    check_structure "$1"
else
    # Check all MOCs
    for moc in "100 - MOCs"/*.md; do
        [ -f "$moc" ] || continue
        check_structure "$moc"
    done
fi
