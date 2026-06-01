#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <plugin-name|--all>" >&2
  exit 2
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

sync_plugin() {
  local plugin="$1"
  local plugin_dir="$repo_root/plugins/$plugin"
  local manifest="$plugin_dir/skills.txt"
  local target_dir="$plugin_dir/skills"

  if [[ ! -d "$plugin_dir" ]]; then
    echo "plugin not found: $plugin" >&2
    exit 1
  fi

  if [[ ! -f "$manifest" ]]; then
    echo "skill manifest not found: $manifest" >&2
    exit 1
  fi

  mkdir -p "$target_dir"

  find "$target_dir" -mindepth 1 -maxdepth 1 -exec rm -rf {} +

  while IFS= read -r skill || [[ -n "$skill" ]]; do
    [[ -z "$skill" || "$skill" =~ ^# ]] && continue

    local source_dir="$repo_root/skills/$skill"
    if [[ ! -d "$source_dir" ]]; then
      echo "skill not found: $skill" >&2
      exit 1
    fi

    cp -R "$source_dir" "$target_dir/$skill"
  done < "$manifest"

  echo "synced plugin skills: $plugin"
}

if [[ "$1" == "--all" ]]; then
  found=false
  for manifest in "$repo_root"/plugins/*/skills.txt; do
    [[ -e "$manifest" ]] || continue
    found=true
    sync_plugin "$(basename "$(dirname "$manifest")")"
  done
  if [[ "$found" == false ]]; then
    echo "no plugin skill manifests found" >&2
    exit 1
  fi
else
  sync_plugin "$1"
fi
