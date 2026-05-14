#!/usr/bin/env bash
# List each recipe's surface: name, description, and the `## Applicable` predicates.
# Recipes live in references/recipes/<name>/RECIPE.md (subdirs starting with `_` are skipped).
# Output format (one block per recipe):
#   - file: <relative path>
#     name: <recipe-name>
#     description: <one-line description>
#     applicable: |
#       <verbatim content of `## Applicable` section, indented; "(none)" if missing>
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RECIPES_DIR="$SCRIPT_DIR/../references/recipes"

shopt -s nullglob
for d in "$RECIPES_DIR"/*/; do
  dname="$(basename "$d")"
  # Skip dirs starting with underscore — those are infrastructure (_template/)
  case "$dname" in _*) continue;; esac
  f="$d/RECIPE.md"
  [ -f "$f" ] || continue
  rel="references/recipes/$dname/RECIPE.md"

  # Extract YAML frontmatter between first two `---` lines
  fm="$(awk 'BEGIN{c=0} /^---[[:space:]]*$/{c++; next} c==1{print} c>=2{exit}' "$f")"
  name="$(printf '%s\n' "$fm" | awk -F': *' '/^name:/{print $2; exit}')"
  desc="$(printf '%s\n' "$fm" | awk '
    /^description:/{
      sub(/^description:[[:space:]]*/,"")
      if ($0 ~ /^>-?[[:space:]]*$/) { collecting=1; next }
      print; exit
    }
    collecting==1 {
      # Stop on next top-level YAML key (non-indented, non-empty line)
      if ($0 !~ /^[[:space:]]/ && $0 != "") exit
      sub(/^[[:space:]]+/,"")
      if ($0=="") next
      printf "%s ", $0
    }
    END{ if (collecting) print "" }
  ')"
  desc="$(printf '%s' "$desc" | sed 's/[[:space:]]*$//')"

  # Extract `## Applicable` section body (lines until next `## ` header or EOF)
  applicable="$(awk '
    /^## Applicable[[:space:]]*$/ { collecting=1; next }
    collecting && /^## / { exit }
    collecting { print }
  ' "$f")"
  # Trim leading/trailing blank lines
  applicable="$(printf '%s' "$applicable" | awk 'NF{p=1} p' | awk 'BEGIN{RS=""}{print}')"
  if [ -z "$applicable" ]; then
    applicable="(none)"
  fi

  printf -- "- file: %s\n  name: %s\n  description: %s\n  applicable: |\n" "$rel" "$name" "$desc"
  printf '%s\n' "$applicable" | sed 's/^/    /'
done
