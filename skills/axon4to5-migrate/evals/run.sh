#!/usr/bin/env bash
# Evals runner for axon4to5-migrate.
#
# Reads each evals/cases/<name>.case and verifies the bundled AF5 fixture
# satisfies the require: / forbid: pattern set.
#
# Case file format:
#   recipe:  <recipe-name>                 # informational
#   af4:     <path under evals/fixtures/>  # informational (baseline)
#   af5:     <path under evals/fixtures/>  # required — file is grepped
#   require: <literal substring>           # must appear in af5
#   forbid:  <literal substring>           # must NOT appear in af5
#
# Usage:
#   ./skills/axon4to5-migrate/evals/run.sh             # all cases
#   ./skills/axon4to5-migrate/evals/run.sh aggregate   # filter by name substring
#
# Exit code: 0 = every case passed, 1 = at least one failure.
#
# Fixtures are bundled by `evals/build.sh`. If `evals/build.sh check` reports
# drift, refresh by running `evals/build.sh` from the repo root.

set -u

evals_dir="$(cd "$(dirname "$0")" && pwd)"
skill_dir="$(cd "$evals_dir/.." && pwd)"
filter="${1:-}"

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

  af5=""
  requires=()
  forbids=()

  while IFS= read -r raw_line || [ -n "$raw_line" ]; do
    line="${raw_line%$'\r'}"
    case "$line" in
      \#*|"") continue ;;
      af5:*)     af5="${line#af5:}"; af5="${af5# }" ;;
      af4:*|recipe:*) : ;;
      require:*) requires+=("${line#require:}") ;;
      forbid:*)  forbids+=("${line#forbid:}") ;;
      *)         echo "WARN  $name: unrecognized line: $line" >&2 ;;
    esac
  done < "$case_file"

  if [ -z "$af5" ]; then
    echo "SKIP  $name (no af5: target)"
    skip=$((skip + 1))
    continue
  fi

  af5_path="$skill_dir/$af5"
  if [ ! -f "$af5_path" ]; then
    echo "FAIL  $name"
    echo "      missing fixture: $af5 (run evals/build.sh)"
    fail=$((fail + 1))
    failed_names+=("$name")
    continue
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
