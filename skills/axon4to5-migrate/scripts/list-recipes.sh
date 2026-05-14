#!/usr/bin/env bash
# List frontmatter (name + description) of every recipe in references/recipes/.
# Output format (one block per recipe):
#   - file: <relative path>
#     name: <recipe-name>
#     description: <one-line description>
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RECIPES_DIR="$SCRIPT_DIR/../references/recipes"

shopt -s nullglob
for f in "$RECIPES_DIR"/*.md; do
  rel="references/recipes/$(basename "$f")"
  # Extract YAML frontmatter between first two `---` lines
  fm="$(awk 'BEGIN{c=0} /^---[[:space:]]*$/{c++; next} c==1{print} c>=2{exit}' "$f")"
  name="$(printf '%s\n' "$fm" | awk -F': *' '/^name:/{print $2; exit}')"
  # description may span multiple lines after `>-`
  desc="$(printf '%s\n' "$fm" | awk '
    /^description:/{
      sub(/^description:[[:space:]]*/,"")
      if ($0 ~ /^>-?[[:space:]]*$/) { collecting=1; next }
      print; exit
    }
    collecting==1 {
      sub(/^[[:space:]]+/,"")
      if ($0=="") next
      printf "%s ", $0
    }
    END{ if (collecting) print "" }
  ')"
  desc="$(printf '%s' "$desc" | sed 's/[[:space:]]*$//')"
  printf -- "- file: %s\n  name: %s\n  description: %s\n" "$rel" "$name" "$desc"
done
