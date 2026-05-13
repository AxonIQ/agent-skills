#!/usr/bin/env bash
# Evals runner for axon4to5-migrate.
#
# Usage:
#   ./skills/axon4to5-migrate/evals/run.sh                # run all cases
#   ./skills/axon4to5-migrate/evals/run.sh aggregate      # run cases matching "aggregate"
#
# Each evals/cases/<name>.case file has the format:
#
#   recipe: <recipe-name>
#   af4: <repo-relative path under .knowledge/repositories/axon-examples/>
#   af5: <repo-relative path under .knowledge/repositories/axon-examples/>
#   require: <literal substring that MUST appear in af5>
#   forbid:  <literal substring that MUST NOT appear in af5>
#
# Lines starting with `#` are comments. Blank lines are ignored.
#
# Exit code: 0 = every case passed; 1 = at least one failure.

set -u

evals_dir="$(cd "$(dirname "$0")" && pwd)"
repo_root="$(cd "$evals_dir/../../.." && pwd)"
examples_root="$repo_root/.knowledge/repositories/axon-examples"

filter="${1:-}"

if [ ! -d "$examples_root" ]; then
  echo "ERROR: examples root not found at $examples_root" >&2
  exit 2
fi

pass=0
fail=0
skip=0
failed_names=()

for case_file in "$evals_dir/cases"/*.case; do
  [ -f "$case_file" ] || continue
  name="$(basename "$case_file" .case)"

  if [ -n "$filter" ] && [[ "$name" != *"$filter"* ]]; then
    continue
  fi

  af4=""
  af5=""
  requires=()
  forbids=()

  while IFS= read -r raw_line || [ -n "$raw_line" ]; do
    line="${raw_line%$'\r'}"
    case "$line" in
      \#*|"") continue ;;
      af4:*)     af4="${line#af4:}"; af4="${af4# }" ;;
      af5:*)     af5="${line#af5:}"; af5="${af5# }" ;;
      recipe:*)  : ;;
      require:*) requires+=("${line#require:}") ;;
      forbid:*)  forbids+=("${line#forbid:}") ;;
      *)         echo "WARN  $name: unrecognized line: $line" >&2 ;;
    esac
  done < "$case_file"

  if [ -z "$af5" ]; then
    echo "SKIP  $name (no af5: target — informational case)"
    skip=$((skip + 1))
    continue
  fi

  af5_path="$examples_root/$af5"
  if [ ! -f "$af5_path" ]; then
    echo "FAIL  $name"
    echo "      missing AF5 reference: $af5"
    fail=$((fail + 1))
    failed_names+=("$name")
    continue
  fi

  if [ -n "$af4" ]; then
    af4_path="$examples_root/$af4"
    if [ ! -f "$af4_path" ]; then
      echo "FAIL  $name"
      echo "      missing AF4 baseline: $af4"
      fail=$((fail + 1))
      failed_names+=("$name")
      continue
    fi
  fi

  problems=()

  for pattern in "${requires[@]:-}"; do
    [ -z "$pattern" ] && continue
    pattern_trim="${pattern# }"
    if ! grep -qF -- "$pattern_trim" "$af5_path"; then
      problems+=("missing in af5: $pattern_trim")
    fi
  done

  for pattern in "${forbids[@]:-}"; do
    [ -z "$pattern" ] && continue
    pattern_trim="${pattern# }"
    if grep -qF -- "$pattern_trim" "$af5_path"; then
      problems+=("forbidden pattern present in af5: $pattern_trim")
    fi
  done

  if [ "${#problems[@]}" -eq 0 ]; then
    echo "PASS  $name"
    pass=$((pass + 1))
  else
    echo "FAIL  $name"
    for p in "${problems[@]}"; do
      echo "      $p"
    done
    fail=$((fail + 1))
    failed_names+=("$name")
  fi
done

echo ""
echo "==== $pass passed · $fail failed · $skip skipped ===="

if [ "$fail" -gt 0 ]; then
  echo "Failed: ${failed_names[*]}"
  exit 1
fi
exit 0
