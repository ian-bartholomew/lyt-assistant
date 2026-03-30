#!/bin/bash
#
# check-plain-text.sh - Find plain text items that could be wikilinks
# Usage: ./check-plain-text.sh [moc-file]
#   If no file specified, checks all MOCs

set -euo pipefail

VAULT_ROOT="${VAULT_ROOT:-$(pwd)}"

# Function to extract plain text items (list items without [[ ]])
extract_plain_text_items() {
    local file="$1"

    # Find lines that start with "- " but don't contain [[ ]]
    # Exclude lines that are just section headers or obvious non-note references
    grep -n '^\s*- [A-Z]' "$file" | grep -v '\[\[' | while IFS=: read -r line_num content; do
        # Clean up the content
        content=$(echo "$content" | sed 's/^\s*- //')
        # Skip if it's a description or looks like prose
        # (contains colon with space, em dash, ellipsis, or sentence structure)
        if ! echo "$content" | grep -qE '(:\s|—|\.{3}|\. |, and)'; then
            echo "$line_num: $content"
        fi
    done
}

# Check a single MOC
check_moc() {
    local moc_file="$1"
    local moc_name=$(basename "$moc_file" .md)

    plain_items=$(extract_plain_text_items "$moc_file")

    if [ -n "$plain_items" ]; then
        echo "## $moc_name"
        echo ""
        echo "📝 **Plain text items (should these be wikilinks?):**"
        echo ""
        echo "$plain_items"
        echo ""
    fi
}

# Main execution
cd "$VAULT_ROOT"

if [ $# -eq 1 ]; then
    # Check single MOC
    check_moc "$1"
else
    # Check all MOCs
    found_any=false
    for moc in "100 - MOCs"/*.md; do
        [ -f "$moc" ] || continue
        output=$(check_moc "$moc")
        if [ -n "$output" ]; then
            found_any=true
            echo "$output"
            echo "---"
            echo ""
        fi
    done

    if [ "$found_any" = false ]; then
        echo "✅ No plain text items found - all references are properly wikilinked!"
    fi
fi
