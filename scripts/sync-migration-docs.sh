#!/usr/bin/env bash
# Sync the Axon Framework migration reference docs into the axon4to5-migrate-code skill.
#
# Upstream is the single source of truth. This sync is ONE-WAY and DESTRUCTIVE:
# everything under references/docs/ is regenerated from
# AxonIQ/AxonFramework @ main:docs/reference-guide/modules/migration/pages.
# Local hand-edits are NOT preserved -- fix the docs upstream, then re-run this.
#
# Antora `include::example$...[tag=...]` directives are resolved inline, so each
# generated page is self-contained and readable without the AxonFramework repo.
#
# Usage:
#   scripts/sync-migration-docs.sh                # sync from upstream main
#   scripts/sync-migration-docs.sh --check        # verify only, no writes
#   scripts/sync-migration-docs.sh --from <dir>   # use a local AxonFramework checkout
#   scripts/sync-migration-docs.sh --help
#
# --check exit codes:
#   0  in sync with the recorded commit, and that commit is upstream main HEAD
#   1  drift: a generated file was hand-edited, added or deleted  (CI should fail)
#   2  stale: no drift, but upstream main has moved on            (CI should warn)
#
# Dependencies: git, awk, and sha256sum or shasum. No jq, no Python.

set -euo pipefail

UPSTREAM_URL="https://github.com/AxonIQ/AxonFramework.git"
UPSTREAM_REF="main"
UPSTREAM_PATH="docs/reference-guide/modules/migration"
SKILL_REL="plugins/axoniq-migration/skills/axon4to5-migrate-code"
DOCS_REL="$SKILL_REL/references/docs"
MANIFEST_NAME=".upstream.json"

usage() {
  awk 'NR > 1 && /^#/ { sub(/^# ?/, ""); print; next } NR > 1 { exit }' "$0"
}

die() {
  echo "sync-migration-docs: error: $*" >&2
  exit 1
}

# --- argument parsing ------------------------------------------------------

MODE=sync
FROM=""
while [ $# -gt 0 ]; do
  case "$1" in
    --check) MODE=check ;;
    --from)
      [ $# -ge 2 ] || die "--from requires a directory argument"
      FROM="$2"
      shift
      ;;
    --from=*) FROM="${1#--from=}" ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown argument: $1 (try --help)" ;;
  esac
  shift
done

# --- repo root -------------------------------------------------------------
# Identified by .claude-plugin/marketplace.json, same as .knowledge/scripts/setup-repos.sh.

_dir="$PWD"
while [ "$_dir" != "/" ]; do
  [ -f "$_dir/.claude-plugin/marketplace.json" ] && break
  _dir="$(dirname "$_dir")"
done
[ "$_dir" = "/" ] && die "could not find repo root (looked for .claude-plugin/marketplace.json)"
REPO_ROOT="$_dir"
unset _dir

DOCS_DIR="$REPO_ROOT/$DOCS_REL"
MANIFEST="$DOCS_DIR/$MANIFEST_NAME"

# --- helpers ---------------------------------------------------------------

sha256_of() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    shasum -a 256 "$1" | awk '{print $1}'
  fi
}

# Extract a scalar from the hand-rolled manifest. Key must be unique in the file.
manifest_get() {
  [ -f "$MANIFEST" ] || return 1
  awk -v key="\"$1\":" '
    index($0, key) { line = $0
      sub(/^[^:]*:[ \t]*/, "", line)
      sub(/,$/, "", line)
      gsub(/^"|"$/, "", line)
      print line
      exit
    }' "$MANIFEST"
}

# Emit "<relpath> <sha256>" for every entry in the manifest's "files" object.
manifest_files() {
  [ -f "$MANIFEST" ] || return 1
  awk '
    /"files"[ \t]*:[ \t]*\{/ { inside = 1; next }
    inside && /^[ \t]*\}/ { inside = 0 }
    inside {
      line = $0
      gsub(/^[ \t]*"/, "", line)
      sub(/",$/, "", line); sub(/"$/, "", line)
      n = index(line, "\": \"")
      if (n > 0) printf "%s %s\n", substr(line, 1, n - 1), substr(line, n + 4)
    }' "$MANIFEST"
}

# --- the include resolver --------------------------------------------------
# Streams one .adoc page, replacing each `include::example$<path>[...]` with the
# tagged region(s) of the referenced Java file. Any include it cannot fully
# satisfy is a hard error: silent content loss is the only real risk of inlining.

read -r -d '' RESOLVER <<'AWK' || true
function fail(msg) {
  printf("sync-migration-docs: %s:%d: %s\n", PAGE, FNR, msg) > "/dev/stderr"
  failed = 1
  exit 1
}

# Name inside a `// tag::NAME[]` / `// end::NAME[]` marker.
function marker_name(line, kind,   s, rest, e) {
  s = index(line, kind "::") + length(kind) + 2
  rest = substr(line, s)
  e = index(rest, "[")
  return substr(rest, 1, e - 1)
}

/^include::/ {
  line = $0
  sub(/[ \t\r]+$/, "", line)

  if (line !~ /^include::example\$/)
    fail("unsupported include family (only example$ is implemented): " line)
  if (substr(line, length(line), 1) != "]")
    fail("malformed include, expected a trailing ']': " line)

  rest = substr(line, length("include::example$") + 1)
  b = index(rest, "[")
  if (b == 0) fail("malformed include, missing '[': " line)
  target = substr(rest, 1, b - 1)
  attrs = substr(rest, b + 1, length(rest) - b - 1)

  # Attributes: only tag=/tags=/indent=0 are known to occur upstream.
  split("", want); split("", seen)
  tagspec = ""; have_tag = 0; indent = ""
  na = split(attrs, parts, ",")
  for (i = 1; i <= na; i++) {
    p = parts[i]
    eq = index(p, "=")
    if (eq == 0) fail("malformed include attribute '" p "' in: " line)
    k = substr(p, 1, eq - 1)
    v = substr(p, eq + 1)
    if (k == "tag" || k == "tags") {
      if (have_tag) fail("multiple tag specs in: " line)
      tagspec = v; have_tag = 1
    } else if (k == "indent") {
      if (v != "0") fail("unsupported indent=" v " (only indent=0 is implemented): " line)
      indent = v
    } else {
      fail("unsupported include attribute '" k "' (only tag/tags/indent are implemented): " line)
    }
  }
  if (!have_tag) fail("include without tag= or tags=, would inline a whole file: " line)

  f = EXAMPLES "/" target
  if ((getline probe < f) < 0) fail("example file not found: " target)
  close(f)

  nt = split(tagspec, tl, ";")
  for (i = 1; i <= nt; i++) { want[tl[i]] = 1; seen[tl[i]] = 0 }

  # Collect every region of every wanted tag, in file order. Several upstream
  # files reuse a tag name twice and Asciidoctor concatenates the regions.
  # All tag/end marker lines are dropped, wanted or not, as Asciidoctor does.
  active = 0; cnt = 0
  split("", out)
  while ((getline l < f) > 0) {
    sub(/\r$/, "", l)
    if (l ~ /\/\/[ \t]*tag::[A-Za-z0-9_.-]+\[\][ \t]*$/) {
      name = marker_name(l, "tag")
      if (name in want) { active++; seen[name] = 1 }
      continue
    }
    if (l ~ /\/\/[ \t]*end::[A-Za-z0-9_.-]+\[\][ \t]*$/) {
      name = marker_name(l, "end")
      if (name in want && active > 0) active--
      continue
    }
    if (active > 0) out[++cnt] = l
  }
  close(f)

  for (i = 1; i <= nt; i++)
    if (!seen[tl[i]]) fail("tag '" tl[i] "' not found in " target)
  if (cnt == 0) fail("tag(s) '" tagspec "' matched no lines in " target)

  # indent=0 normalizes the COMBINED block, not each region: upstream indents
  # some regions on purpose so that both land flush left after normalization.
  if (indent == "0") {
    minind = -1
    for (i = 1; i <= cnt; i++) {
      if (out[i] ~ /^[ \t]*$/) continue
      match(out[i], /^[ \t]*/)
      if (minind < 0 || RLENGTH < minind) minind = RLENGTH
    }
    if (minind > 0)
      for (i = 1; i <= cnt; i++) out[i] = substr(out[i], minind + 1)
  }

  for (i = 1; i <= cnt; i++) print out[i]
  next
}

{ print }

END { if (failed) exit 1 }
AWK

# --- --check ---------------------------------------------------------------

do_check() {
  [ -f "$MANIFEST" ] || die "no manifest at $DOCS_REL/$MANIFEST_NAME -- run the sync first"

  local recorded drift=0 listed_tmp
  recorded="$(manifest_get commit)"
  [ -n "$recorded" ] || die "manifest has no source.commit"

  listed_tmp="$(mktemp)"

  while read -r rel want_sha; do
    [ -n "$rel" ] || continue
    echo "$rel" >> "$listed_tmp"
    if [ ! -f "$DOCS_DIR/$rel" ]; then
      echo "drift: deleted since last sync: $DOCS_REL/$rel" >&2
      drift=1
      continue
    fi
    local have_sha
    have_sha="$(sha256_of "$DOCS_DIR/$rel")"
    if [ "$have_sha" != "$want_sha" ]; then
      echo "drift: hand-edited since last sync: $DOCS_REL/$rel" >&2
      drift=1
    fi
  done < <(manifest_files)

  while IFS= read -r abs; do
    local rel="${abs#"$DOCS_DIR"/}"
    if ! grep -qxF "$rel" "$listed_tmp"; then
      echo "drift: untracked file, not produced by the sync: $DOCS_REL/$rel" >&2
      drift=1
    fi
  done < <(find "$DOCS_DIR" -type f ! -name "$MANIFEST_NAME" | sort)

  rm -f "$listed_tmp"

  # A changed generator invalidates the output even when every checksum still
  # matches: re-running would now produce something different.
  local recorded_gen current_gen
  recorded_gen="$(manifest_get generator_sha256)"
  current_gen="$(sha256_of "$0")"
  if [ -n "$recorded_gen" ] && [ "$recorded_gen" != "$current_gen" ]; then
    echo "drift: $(basename "$0") changed since the last sync, so the generated output is out of date" >&2
    drift=1
  fi

  if [ "$drift" -ne 0 ]; then
    echo "" >&2
    echo "references/docs is generated. Do not edit it by hand:" >&2
    echo "  fix the content upstream in AxonIQ/AxonFramework, then run scripts/sync-migration-docs.sh" >&2
    return 1
  fi

  echo "ok: all generated files match the manifest (commit ${recorded:0:12})"

  local head
  head="$(git ls-remote "$UPSTREAM_URL" "$UPSTREAM_REF" 2>/dev/null | awk '{print $1}')" || head=""
  if [ -z "$head" ]; then
    echo "note: could not reach $UPSTREAM_URL, skipped the staleness check" >&2
    return 0
  fi
  if [ "$head" != "$recorded" ]; then
    echo "stale: upstream $UPSTREAM_REF is now ${head:0:12}, docs were synced from ${recorded:0:12}" >&2
    echo "       run scripts/sync-migration-docs.sh to refresh" >&2
    return 2
  fi
  echo "ok: up to date with upstream $UPSTREAM_REF"
  return 0
}

if [ "$MODE" = check ]; then
  set +e
  do_check
  rc=$?
  set -e
  exit $rc
fi

# --- acquire the source ----------------------------------------------------

TMPDIR_CLONE=""
cleanup() { [ -n "$TMPDIR_CLONE" ] && rm -rf "$TMPDIR_CLONE"; }
trap cleanup EXIT INT TERM

SOURCE_OVERRIDE=null
DIRTY=false

if [ -n "$FROM" ]; then
  [ -d "$FROM/.git" ] || die "--from $FROM is not a git checkout"
  CHECKOUT="$(cd "$FROM" && pwd)"
  SHA="$(git -C "$CHECKOUT" rev-parse HEAD)"
  REF="$(git -C "$CHECKOUT" rev-parse --abbrev-ref HEAD)"
  if [ -n "$(git -C "$CHECKOUT" status --porcelain)" ]; then DIRTY=true; fi
  SOURCE_OVERRIDE="\"$CHECKOUT\""
  echo "WARNING: --from is not a canonical sync." >&2
  echo "  source:  $CHECKOUT (ref $REF, commit ${SHA:0:12}, dirty=$DIRTY)" >&2
  echo "  This checkout may lag or differ from $UPSTREAM_URL $UPSTREAM_REF." >&2
  echo "  Re-run without --from before committing the result." >&2
  echo "" >&2
else
  TMPDIR_CLONE="$(mktemp -d)"
  CHECKOUT="$TMPDIR_CLONE/AxonFramework"
  echo "fetching $UPSTREAM_URL ($UPSTREAM_REF, sparse: $UPSTREAM_PATH)"
  git clone --quiet --depth 1 --filter=blob:none --sparse --branch "$UPSTREAM_REF" \
    "$UPSTREAM_URL" "$CHECKOUT"
  git -C "$CHECKOUT" sparse-checkout set --cone "$UPSTREAM_PATH"
  SHA="$(git -C "$CHECKOUT" rev-parse HEAD)"
  REF="$UPSTREAM_REF"
fi

COMMIT_DATE="$(git -C "$CHECKOUT" log -1 --format=%cI "$SHA")"
SRC="$CHECKOUT/$UPSTREAM_PATH"
PAGES="$SRC/pages"
EXAMPLES="$SRC/examples"

# Preconditions: a wrong sparse spec must say so plainly, not produce 87
# unresolved-include errors or, worse, code-less pages.
[ -d "$PAGES" ] || die "no pages/ under $UPSTREAM_PATH -- wrong path or bad checkout"
[ -d "$EXAMPLES" ] || die "no examples/ under $UPSTREAM_PATH -- sparse checkout did not deliver it"
[ -n "$(find "$PAGES" -name '*.adoc' -print -quit)" ] || die "pages/ contains no .adoc files"
[ -n "$(find "$EXAMPLES" -name '*.java' -print -quit)" ] || die "examples/ contains no .java files"

echo "source:  ${SHA:0:12} ($COMMIT_DATE)"
echo "pages:   $(find "$PAGES" -name '*.adoc' | wc -l | tr -d ' ')  examples: $(find "$EXAMPLES" -name '*.java' | wc -l | tr -d ' ')"

# --- generate into a staging dir ------------------------------------------
# Nothing touches references/docs until every page has resolved cleanly.

STAGE="$(mktemp -d)"
cleanup() {
  [ -n "$TMPDIR_CLONE" ] && rm -rf "$TMPDIR_CLONE"
  [ -n "${STAGE:-}" ] && rm -rf "$STAGE"
  return 0
}

# The banner deliberately carries NO commit SHA: that would make every page differ
# on every sync, drowning the real content changes. Provenance lives in the manifest.
BANNER_1="// AUTO-GENERATED by scripts/sync-migration-docs.sh from AxonIQ/AxonFramework"
BANNER_2="// $UPSTREAM_PATH/pages -- DO NOT EDIT. Fix it upstream, then re-run the sync."

count=0
while IFS= read -r page; do
  rel="${page#"$PAGES"/}"
  out="$STAGE/$rel"
  mkdir -p "$(dirname "$out")"
  {
    echo "$BANNER_1"
    echo "$BANNER_2"
  } > "$out"
  awk -v EXAMPLES="$EXAMPLES" -v PAGE="$rel" "$RESOLVER" "$page" >> "$out" \
    || die "failed to resolve includes in $rel (references/docs left untouched)"
  count=$((count + 1))
done < <(find "$PAGES" -name '*.adoc' | sort)

[ "$count" -gt 0 ] || die "no pages generated"

# Belt and braces: the resolver only rewrites line-start includes, so prove that
# no include:: survived anywhere before we overwrite the committed docs.
if grep -rn 'include::' "$STAGE" >&2; then
  die "unresolved include:: directives remain (references/docs left untouched)"
fi
if grep -rnE 'tag::|end::' "$STAGE" >&2; then
  die "tag markers leaked into the output (references/docs left untouched)"
fi

# --- swap in ---------------------------------------------------------------
# Mirror semantics: wipe first, so pages deleted upstream disappear here too.

rm -rf "$DOCS_DIR"
mkdir -p "$DOCS_DIR"
(cd "$STAGE" && find . -type f | sed 's|^\./||' | while IFS= read -r rel; do
  mkdir -p "$DOCS_DIR/$(dirname "$rel")"
  cp "$STAGE/$rel" "$DOCS_DIR/$rel"
done)

# --- provenance + checksum manifest ---------------------------------------

SYNCED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
{
  echo "{"
  echo "  \"source\": {"
  echo "    \"repo\": \"$UPSTREAM_URL\","
  echo "    \"ref\": \"$REF\","
  echo "    \"commit\": \"$SHA\","
  echo "    \"commit_date\": \"$COMMIT_DATE\","
  echo "    \"path\": \"$UPSTREAM_PATH\","
  echo "    \"source_override\": $SOURCE_OVERRIDE,"
  echo "    \"dirty\": $DIRTY"
  echo "  },"
  echo "  \"synced_at\": \"$SYNCED_AT\","
  echo "  \"generator\": \"scripts/sync-migration-docs.sh\","
  echo "  \"generator_sha256\": \"$(sha256_of "$0")\","
  echo "  \"files\": {"
  first=true
  while IFS= read -r abs; do
    rel="${abs#"$DOCS_DIR"/}"
    [ "$first" = true ] || echo ","
    first=false
    printf '    "%s": "%s"' "$rel" "$(sha256_of "$abs")"
  done < <(find "$DOCS_DIR" -type f ! -name "$MANIFEST_NAME" | sort)
  echo ""
  echo "  }"
  echo "}"
} > "$MANIFEST"

echo "synced:  $count pages -> $DOCS_REL"

# --- SKILL.md catalog warning ---------------------------------------------
# Warn only. The catalog table is prose the maintainer owns; the script must not
# rewrite SKILL.md behind their back.

SKILL_MD="$REPO_ROOT/$SKILL_REL/SKILL.md"
if [ -f "$SKILL_MD" ]; then
  missing=""
  while IFS= read -r abs; do
    rel="${abs#"$DOCS_DIR"/}"
    grep -qF "references/docs/$rel" "$SKILL_MD" || missing="$missing  $rel"$'\n'
  done < <(find "$DOCS_DIR/paths" -type f -name '*.adoc' 2>/dev/null | sort)
  if [ -n "$missing" ]; then
    echo "" >&2
    echo "warning: these migration paths are not listed in the SKILL.md catalog table:" >&2
    printf '%s' "$missing" >&2
    echo "  Add them to '## References/Docs: Migration paths catalog' so recipes can reach them." >&2
  fi
fi
