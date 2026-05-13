#!/usr/bin/env bash
# Build the eval fixture bundle.
#
# Reads evals/manifest.tsv (TSV: <source>\t<dest>), copies each <source> from
# the repo root to <dest> in the skill. Verifies every referenced source exists
# AND every dest sits under evals/fixtures/. Use this to refresh the bundle
# after the upstream examples change, OR to inspect what the skill ships with.
#
# Usage (from any CWD — paths resolve to repo root):
#   ./skills/axon4to5-migrate/evals/build.sh        # copy
#   ./skills/axon4to5-migrate/evals/build.sh check  # verify hashes only (no copy)
#
# Exit code: 0 = success, 1 = missing source / out-of-bounds dest / hash drift.

set -u

skill_dir="$(cd "$(dirname "$0")/.." && pwd)"
repo_root="$(cd "$skill_dir/../.." && pwd)"
manifest="$skill_dir/evals/manifest.tsv"
mode="${1:-copy}"

if [ ! -f "$manifest" ]; then
  echo "ERROR: $manifest missing" >&2
  exit 2
fi

copied=0
checked=0
missing=0
drifted=0
escaped=0

while IFS=$'\t' read -r src dst; do
  case "$src" in
    \#*|"") continue ;;
  esac
  # tolerate trailing whitespace / Windows line endings
  src="${src%$'\r'}"; dst="${dst%$'\r'}"
  src="${src%%[[:space:]]*}"; dst="${dst%%[[:space:]]*}"
  [ -z "$src" ] && continue
  [ -z "$dst" ] && { echo "ERROR: manifest row has no dest: $src" >&2; exit 1; }

  case "$dst" in
    evals/fixtures/*) : ;;
    *)
      echo "ERROR: dest escapes evals/fixtures/: $dst" >&2
      escaped=$((escaped + 1))
      continue
      ;;
  esac

  src_abs="$repo_root/$src"
  dst_abs="$skill_dir/$dst"

  if [ ! -f "$src_abs" ]; then
    echo "MISS  source not found: $src" >&2
    missing=$((missing + 1))
    continue
  fi

  if [ "$mode" = "check" ]; then
    if [ ! -f "$dst_abs" ]; then
      echo "DRIFT $dst (dest missing — run without 'check' to copy)"
      drifted=$((drifted + 1))
    elif ! cmp -s "$src_abs" "$dst_abs"; then
      echo "DRIFT $dst (contents differ from source)"
      drifted=$((drifted + 1))
    fi
    checked=$((checked + 1))
  else
    mkdir -p "$(dirname "$dst_abs")"
    cp "$src_abs" "$dst_abs"
    copied=$((copied + 1))
  fi
done < "$manifest"

echo ""
if [ "$mode" = "check" ]; then
  echo "==== checked $checked · missing $missing · drift $drifted ===="
  [ "$missing" -gt 0 ] || [ "$drifted" -gt 0 ] || [ "$escaped" -gt 0 ] && exit 1
else
  echo "==== copied $copied · missing $missing ===="
  [ "$missing" -gt 0 ] || [ "$escaped" -gt 0 ] && exit 1
fi
exit 0
