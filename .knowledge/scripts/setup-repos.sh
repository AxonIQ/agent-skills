#!/usr/bin/env bash
# Fetch knowledge reference repositories for skill development.
#
# These repositories are gitignored in the superproject and are only needed
# when developing or updating skills. End users installing skills do NOT need
# to run this script.
#
# Usage:  bash .knowledge/scripts/setup-repos.sh [--update]
#   --update  Pull the latest commits on each repo's tracked branch
#             (instead of skipping repos that are already present).
#
# Can be run from anywhere inside (or outside) the repository tree.

set -uo pipefail

# Change to the repo root, identified by the presence of .claude-plugin/marketplace.json.
_dir="$PWD"
while [ "$_dir" != "/" ]; do
  [ -f "$_dir/.claude-plugin/marketplace.json" ] && break
  _dir="$(dirname "$_dir")"
done
if [ "$_dir" = "/" ]; then
  echo "error: could not find repo root (looked for .claude-plugin/marketplace.json)" >&2
  exit 1
fi
cd "$_dir"
unset _dir

UPDATE=false
for arg in "$@"; do
  case "$arg" in
    --update) UPDATE=true ;;
    *) echo "Unknown argument: $arg" >&2; exit 1 ;;
  esac
done

WARNINGS=()

clone_or_update() {
  local url="$1" path="$2" branch="${3:-}"

  if [ -d "$path/.git" ]; then
    if [ "$UPDATE" = true ]; then
      echo "update: $path"
      local err_file
      err_file=$(mktemp)
      local fetch_ref="${branch:-HEAD}"
      if ! git -C "$path" fetch --depth 1 origin "$fetch_ref" 2>"$err_file"; then
        WARNINGS+=("warn: could not fetch $path — $(cat "$err_file")")
        rm -f "$err_file"
        return
      fi
      rm -f "$err_file"
      if [ -n "$branch" ]; then
        if ! git -C "$path" reset --hard "origin/$branch" 2>"$err_file"; then
          WARNINGS+=("warn: could not reset $path to origin/$branch — $(cat "$err_file")")
          rm -f "$err_file"
          return
        fi
        rm -f "$err_file"
      else
        if ! git -C "$path" reset --hard FETCH_HEAD 2>"$err_file"; then
          WARNINGS+=("warn: could not reset $path to FETCH_HEAD — $(cat "$err_file")")
          rm -f "$err_file"
          return
        fi
        rm -f "$err_file"
      fi
    else
      echo "skip (already present): $path"
    fi
    return
  fi

  mkdir -p "$(dirname "$path")"
  local clone_cmd=(git clone --depth 1 --single-branch)
  [ -n "$branch" ] && clone_cmd+=(--branch "$branch")
  clone_cmd+=("$url" "$path")

  local err_file
  err_file=$(mktemp)
  if ! "${clone_cmd[@]}" 2>"$err_file"; then
    rm -rf "$path" 2>/dev/null || true
    WARNINGS+=("warn: could not clone $path — $(cat "$err_file")")
    rm -f "$err_file"
    return
  fi
  rm -f "$err_file"

  git -C "$path" remote set-url --push origin DISABLED
  echo "cloned: $path"
}

# --- axonframework ---
clone_or_update \
  https://github.com/AxonIQ/AxonFramework.git \
  .knowledge/repositories/axonframework/AxonFramework5 \
  main

clone_or_update \
  https://github.com/AxonIQ/AxonFramework.git \
  .knowledge/repositories/axonframework/AxonFramework4 \
  axon-4.13.x

clone_or_update \
  https://github.com/AxonIQ/axoniq-framework.git \
  .knowledge/repositories/axonframework/AxoniqFramework \
  main

clone_or_update \
  https://github.com/AxonIQ/extension-workflow.git \
  .knowledge/repositories/axonframework/extension-workflow \
  main

clone_or_update \
  https://github.com/AxonIQ/extension-data-protection.git \
  .knowledge/repositories/axonframework/extension-data-protection

# --- axon-examples (axon4) ---
clone_or_update \
  https://github.com/smcvb/gamerental.git \
  .knowledge/repositories/axon-examples/axon4/gamerental \
  main

clone_or_update \
  https://github.com/MateuszNaKodach/bike-rental-extended.git \
  .knowledge/repositories/axon-examples/axon4/bike-rental-extended \
  af4

clone_or_update \
  https://github.com/AxonIQ/auction-house-axon-observability-demo.git \
  .knowledge/repositories/axon-examples/axon4/auction-house \
  migration-ready/af5

clone_or_update \
  https://github.com/MateuszNaKodach/Cinema.EventSourcing.VerticalSlice.Kotlin.Axon4.Spring.git \
  .knowledge/repositories/axon-examples/axon4/cinema

clone_or_update \
  https://github.com/MateuszNaKodach/HeroesOfDomainDrivenDesign.EventSourcing.Java.Axon.Spring.git \
  .knowledge/repositories/axon-examples/axon4/heroes \
  master

# --- axon-examples (axon5) ---
clone_or_update \
  https://github.com/smcvb/gamerental.git \
  .knowledge/repositories/axon-examples/axon5/gamerental \
  af5/5.1.0-demo-day

clone_or_update \
  https://github.com/MateuszNaKodach/bike-rental-extended.git \
  .knowledge/repositories/axon-examples/axon5/bike-rental-extended \
  af5

clone_or_update \
  https://github.com/MateuszNaKodach/HeroesOfDomainDrivenDesign.EventSourcing.Java.Axon.Spring.git \
  .knowledge/repositories/axon-examples/axon5/heroes \
  af5-migrated

# --- ai-bestpractices ---
clone_or_update \
  https://github.com/anthropics/claude-cookbooks.git \
  .knowledge/repositories/ai-bestpractices/anthropics-claude-cookbooks \
  main

clone_or_update \
  https://github.com/anthropics/skills.git \
  .knowledge/repositories/ai-bestpractices/anthropics-skills \
  main

clone_or_update \
  https://github.com/obra/superpowers.git \
  .knowledge/repositories/ai-bestpractices/obra-superpowers \
  main

clone_or_update \
  https://github.com/simonw/claude-skills.git \
  .knowledge/repositories/ai-bestpractices/simonw-claude-skills \
  main

clone_or_update \
  https://github.com/supabase/agent-skills.git \
  .knowledge/repositories/ai-bestpractices/supabase-agent-skills \
  main

clone_or_update \
  https://github.com/vercel-labs/agent-skills.git \
  .knowledge/repositories/ai-bestpractices/vercel-labs-agent-skills \
  main

echo ""
if [ ${#WARNINGS[@]} -gt 0 ]; then
  echo "Completed with warnings:" >&2
  for w in "${WARNINGS[@]}"; do
    echo "  $w" >&2
  done
  echo "" >&2
fi
echo "Done. Knowledge repositories are ready under .knowledge/repositories/ (skipped repos listed above, if any)."
