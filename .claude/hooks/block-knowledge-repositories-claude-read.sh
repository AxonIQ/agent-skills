#!/usr/bin/env bash
# Blocks Read/Glob/Grep operations that would surface CLAUDE.md or SKILL.md
# files inside the repository's .knowledge/repositories directory tree.
#
# Per the project CLAUDE.md: "DO NOT LOAD OTHER CLAUDE.md or skills from
# .knowledge/repositories dirs." This hook enforces that rule deterministically.

set -euo pipefail

input="$(cat)"
tool_name="$(printf '%s' "$input" | jq -r '.tool_name // empty')"

block() {
  echo "Blocked by .claude/hooks/block-knowledge-repositories-claude-read.sh:" >&2
  echo "  $1" >&2
  echo "  Project CLAUDE.md forbids loading CLAUDE.md or SKILL.md from .knowledge/repositories." >&2
  exit 2
}

case "$tool_name" in
  Read)
    file_path="$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty')"
    if [[ "$file_path" == *"/.knowledge/repositories"* ]] && [[ "$file_path" == *"CLAUDE.md" || "$file_path" == *"SKILL.md" ]]; then
      block "Read of $file_path is forbidden."
    fi
    ;;
  Glob)
    pattern="$(printf '%s' "$input" | jq -r '.tool_input.pattern // empty')"
    path="$(printf '%s' "$input" | jq -r '.tool_input.path // empty')"
    if { [[ "$pattern" == *"CLAUDE.md"* ]] || [[ "$pattern" == *"SKILL.md"* ]]; } && \
       { [[ "$pattern" == *".knowledge/repositories"* ]] || [[ "$path" == *"/.knowledge"* || "$path" == *"/.knowledge/repositories"* ]]; }; then
      block "Glob targeting CLAUDE.md/SKILL.md under .knowledge/repositories is forbidden (pattern=$pattern path=$path)."
    fi
    ;;
esac

exit 0
