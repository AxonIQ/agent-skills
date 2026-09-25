#!/usr/bin/env bash
# Blocks Edit/Write/NotebookEdit against generated documentation.
#
# plugins/axoniq-migration/skills/axon4to5-migrate-code/references/docs/ is a one-way
# mirror of AxonIQ/AxonFramework produced by scripts/sync-migration-docs.sh. Hand-edits
# there are silently destroyed by the next sync, so this hook stops them being made.
#
# The sync script itself writes via plain shell redirection and cp, not via these tools,
# so it is unaffected.

set -euo pipefail

input="$(cat)"
tool_name="$(printf '%s' "$input" | jq -r '.tool_name // empty')"

case "$tool_name" in
  Edit|Write|NotebookEdit) ;;
  *) exit 0 ;;
esac

file_path="$(printf '%s' "$input" | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty')"

if [[ "$file_path" == *"/axon4to5-migrate-code/references/docs/"* ]]; then
  echo "Blocked by .claude/hooks/block-generated-docs-edit.sh:" >&2
  echo "  $file_path is generated, not source." >&2
  echo "  It mirrors docs/reference-guide/modules/migration/pages in AxonIQ/AxonFramework." >&2
  echo "  To change it: fix the content upstream, then run scripts/sync-migration-docs.sh." >&2
  echo "  Hand-authored notes belong in references/recipes/ instead." >&2
  exit 2
fi

exit 0
