#!/bin/bash
#
# check-links.sh - Validate all wikilinks in MOCs
# Usage: ./check-links.sh [moc-file]
#   If no file specified, checks all MOCs

set -euo pipefail

VAULT_ROOT="${VAULT_ROOT:-$(pwd)}"

# Extract all wikilinks from a file
extract_links() {
    local file="$1"
    grep -o '\[\[[^]]*\]\]' "$file" 2>/dev/null | sed 's/\[\[\([^|]*\).*/\1/' | sort -u
}

# Check if a note exists anywhere in vault
file_exists() {
    local target="$1"
    # Search in Notes, Reference, and MOCs
    find "$VAULT_ROOT/200 - Notes" "$VAULT_ROOT/300 - Reference" "$VAULT_ROOT/100 - MOCs" \
        -type f -name "${target}.md" 2>/dev/null | head -1
}

# Find broken links in a MOC
check_moc() {
    local moc_file="$1"
    local moc_name=$(basename "$moc_file" .md)

    echo "## $moc_name"
    echo ""

    local total_links=0
    local broken_links=0
    local broken_list=""

    while IFS= read -r link; do
        [ -z "$link" ] && continue
        total_links=$((total_links + 1))
        if ! file_exists "$link" >/dev/null 2>&1; then
            broken_links=$((broken_links + 1))
            broken_list="${broken_list}- [[${link}]]\n"
        fi
    done < <(extract_links "$moc_file")

    echo "**Total wikilinks:** $total_links"
    echo "**Valid:** $((total_links - broken_links))"
    echo "**Broken:** $broken_links"
    echo ""

    if [ $broken_links -gt 0 ]; then
        echo "⚠️ **Broken links found:**"
        echo -e "$broken_list"
    else
        echo "✅ All links valid"
    fi
    echo ""
}

# Main execution
cd "$VAULT_ROOT"

if [ $# -eq 1 ]; then
    # Check single MOC
    check_moc "$1"
else
    # Check all MOCs
    for moc in "100 - MOCs"/*.md; do
        [ -f "$moc" ] || continue
        check_moc "$moc"
        echo "---"
        echo ""
    done
fi
