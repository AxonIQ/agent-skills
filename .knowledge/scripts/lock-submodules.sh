#!/usr/bin/env bash
# Lock every submodule as fetch-only: disable the push URL and install a
# pre-push hook that refuses pushes. Safe to re-run.
#
# Usage:  bash .knowledge/scripts/lock-submodules.sh
# Run from the superproject root.

set -euo pipefail

if [ ! -f .gitmodules ]; then
  echo "error: run from the superproject root (no .gitmodules here)" >&2
  exit 1
fi

git submodule foreach --quiet '
  git remote set-url --push origin DISABLED

  HOOK="$(git rev-parse --git-path hooks/pre-push)"
  mkdir -p "$(dirname "$HOOK")"
  cat > "$HOOK" <<EOF
#!/bin/sh
echo "Pushes are disabled in this submodule (.knowledge/ is fetch-only)." >&2
exit 1
EOF
  chmod +x "$HOOK"

  echo "locked: $name"
'

echo "All submodules locked (push URL = DISABLED, pre-push hook installed)."
