---
name: knowledge:add-repository
description: Add a reference repository under .knowledge/repositories. Clones it locally (shallow), writes a per-repo detail markdown file with frontmatter, updates the type-level INDEX.md catalog, and registers the repo in setup-repos.sh. Use this whenever the user wants to add a reference repository, external repo, migrated application example, framework reference, or any git repository as a tracked reference - even if they don't say "submodule" explicitly. Triggers on phrases like "add this repo", "add a reference", "include this repository", "track this repo as", "add as submodule", "add migrated example", "add reference application".
---

# Add Reference Repository to `.knowledge/repositories`

## Goal

Clone a repository locally under `.knowledge/repositories/<type>/...` and produce
**two** documentation artifacts:

1. A **per-repo detail file** (`<type>_<path-joined-by-underscores>.md`) with
   YAML frontmatter and a body shaped by the repo's type.
2. A **type-level `INDEX.md`** entry — a short, scannable catalog row with a
   `Keywords:` field that links to the detail file.

Why the split: a single growing `INDEX.md` per type stops being read in full
once it gets long, and important context near the bottom is missed. The
detail files carry the long content; the index stays short so Claude can scan
it reliably and pick which detail file to open.

## When to use

The user wants to add an external git repository as a local reference. Common
phrasings — trigger on any of these even if "submodule" isn't said:

- "add this repository as a reference"
- "add this repo to knowledge"
- "track this repo at branch X"
- "add migrated example axon4/foo and axon5/foo"
- "add reference application"
- "include this repository"

## Repository types

Three types are supported. Each has its own template and INDEX shape:

| `repo_type`        | What it is                                          | Where it lives                                                |
| ------------------ | --------------------------------------------------- | ------------------------------------------------------------- |
| `axonframework`    | A clone of an Axon Framework source tree            | `.knowledge/repositories/axonframework/<RepoName>/`           |
| `axon-examples`    | A migrated example application (axon4 ↔ axon5 pair) | `.knowledge/repositories/axon-examples/{axon4,axon5}/<app>/`  |
| `ai-bestpractices` | General reference (prompt eng, agent loops, etc.)   | `.knowledge/repositories/ai-bestpractices/<repo>/`            |

## Inputs (gather from the user)

**Always required:**

- `url` — git URL of the repository.
- `repo_type` — one of `axonframework`, `axon-examples`, `ai-bestpractices`.
- `repo_path` — relative to repo root, under `.knowledge/repositories/<type>/`.
- `purpose` — 1–3 sentences. Used in the detail file and the INDEX one-liner.
- `keywords` — 3–7 short, discriminative terms. Ask if not volunteered.
  These appear in both frontmatter and `INDEX.md`'s `Keywords:` line, so
  they should be the kind of words a future search would actually use.

**Optional, but ask when relevant:**

- `branch` — passed to `git clone --branch`.
- `commit` — short hash to pin. Checked out after clone.
- `feature_highlights` / `key_paths` / `description` — body content.
- `highlights` — curated callouts the user wants surfaced to AI agents
  (documentation URLs, files to start with, things to skip). Ask for at
  least one bullet when creating a new detail file; only leave the
  `## Highlights` section as `- _none_` if the user explicitly declines.

**`axon-examples` additionally requires:**

- `variant` — `axon4` or `axon5`.
- `app_name` — the application name shared across variants.
- `language` — `Kotlin` or `Java`. Ask if missing.
- `build_tool` — `maven` or `gradle`. Ask if missing.
- `architecture` — optional (e.g. `Vertical Slice`, `Hexagonal`).
- For the `axon5` side: `migration_notes` — inline notes about choices,
  alternatives, limitations. The kind of thing a migration skill should
  learn from (e.g. "PaymentSaga migrated using repository-based state
  instead of workflow extension"; "Deadlines not migrated — no Axon 5
  equivalent without Workflow extension").
- When pairing two sides: branches/commits to compare for the Migration
  Diff callout. The skill **must ask** for these if not provided — the
  callout is meaningless without them.

## Filename and path derivation

Detail filename = type-dir + `_` + submodule path joined by `_`, with `.md`.

| Submodule path                                         | Detail filename                              |
| ------------------------------------------------------ | -------------------------------------------- |
| `.knowledge/repositories/axonframework/AxonFramework5` | `axonframework_AxonFramework5.md`            |
| `.knowledge/repositories/axon-examples/axon4/order`    | `axon-examples_axon4_order.md`               |
| `.knowledge/repositories/axon-examples/axon5/order`    | `axon-examples_axon5_order.md`               |
| `.knowledge/repositories/ai-bestpractices/cookbook`    | `ai-bestpractices_cookbook.md`               |

Both files (detail + INDEX) sit **inside the type directory**, alongside the
submodule(s).

The detail file MUST NOT be named `CLAUDE.md` or `SKILL.md` — those are
blocked by `.claude/hooks/block-knowledge-repositories-claude-read.sh` and
would become unreadable.

## Workflow

1. **Verify working directory.** Run from repo root. If `git status` shows
   unrelated unstaged changes that might get swept into the commit, warn the
   user and ask whether to continue.

2. **Clone the repository (shallow).**
   ```bash
   git clone --depth 1 --single-branch [--branch <branch>] <url> <repo_path>
   ```
   Omit `--branch` when no branch was specified (clones the default branch).
   Prefer `--depth 1` to keep the local checkout small; contributors who need
   full history can `git -C <path> fetch --unshallow` afterwards.

3. **Lock as fetch-only.** `.knowledge/repositories/` is read-only by policy
   (see `.knowledge/README.md`). Disable the push URL immediately after cloning:
   ```bash
   git -C <repo_path> remote set-url --push origin DISABLED
   ```
   Verify with `git -C <repo_path> remote -v` — the `(push)` line must
   read `DISABLED`.

4. **Pin to commit if requested.**
   ```bash
   git -C <repo_path> checkout <commit>
   ```
   Prefer `git -C <path>` over `cd <path> && … && cd -` — it can't leak
   `cwd` state into your next Bash call. The detached-HEAD warning is
   normal — ignore it. **Never use bare `cd <repo_path>`** inside
   this skill; the same rule applies to fetch/checkout in the retarget
   sub-workflow below.

5. **Write the per-repo detail file.** Read the template for this repo type:
   - `axonframework` → `references/templates-axonframework.md`
   - `axon-examples` → `references/templates-axon-examples.md`
   - `ai-bestpractices` → `references/templates-ai-bestpractices.md`

   Fill in the frontmatter and body sections. Every detail file must include
   a `## Highlights` section (use `- _none_` only if the user explicitly
   declines to add one).

6. **Update the type-level `INDEX.md`.** Read
   `references/index-entry-templates.md` for the per-type entry shape. Read
   the existing `INDEX.md` first to preserve order and the established
   pattern. If the file is missing or empty, write the standard AI-agent
   header (see the templates file) and append the new entry below it.

7. **(axon-examples only) Pair with the counterpart if it exists.**
   - If the counterpart variant's detail file is already present, update the
     counterpart's frontmatter to reflect the new pairing:
     - On the axon4 source: append the new axon5 filename to `migrated_to`
       (promote to a list if it was scalar and a second target now exists).
     - On the axon5 target: set `migrated_from` to the axon4 source filename.
   - `migrated_from` is **always a single scalar** — a migration has exactly
     one source.
   - `migrated_to` is **a list** — one source can have many migration
     strategies. Use scalar form only when there's exactly one target.
   - Update the application's INDEX entry to list the new variant bullet.
   - If both sides now exist and the Migration Diff callout is missing,
     write it using the branches/commits the user provided. **If the user
     hasn't provided them, ask before writing the callout.**

8. **Register in `setup-repos.sh`.**

   Append a `clone_or_update` call to `.knowledge/scripts/setup-repos.sh`
   following the established pattern — one call per path, with the correct
   branch (or none if default):
   ```bash
   clone_or_update \
     <url> \
     <repo_path> \
     [<branch>]
   ```
   No `.gitignore` change needed — `.knowledge/repositories/` is already
   ignored as a whole.

9. **Commit.** Selective `git add` — never `git add .` or `-A`. Stage:
   - `git add -f` for the new/updated detail file(s) and `INDEX.md` —
     `.knowledge/repositories/` is globally gitignored, so `-f` is required.
   - `git add` (no `-f`) for `.knowledge/scripts/setup-repos.sh`.
   Commit message focused on what was added and why, without any Claude Code
   attribution (user's standing rule).

10. **Report.** Tell the user:
    - Repository path and tracked ref (branch/commit).
    - Detail file path created.
    - INDEX.md section updated.
    - For axon-examples: which counterpart side links were updated, if any.
    - Commit hash.

## Sub-workflow: Retarget a repository's tracked branch

The user asks to change the `branch` an existing repository tracks
("retarget AxonFramework5 to feat/5.1-openrewrite", "switch this
repo to branch X", "follow main now"). Don't re-run the full add
workflow — make a focused three-touch update:

1. **Move the local repo to the new branch.**
   ```bash
   git -C <repo_path> fetch origin <new-branch>
   git -C <repo_path> checkout <new-branch>
   ```
   Use `git -C` — see step 4 above.
2. **Update the detail file's frontmatter.** Change `branch:` to the new
   branch. Keywords usually don't need to change; revisit Highlights only
   if the new branch implies a different audience.
3. **Update the INDEX entry's branch label.** The `branch \`…\`` segment
   in the `[Details](...)` line must match the new frontmatter.
4. **Update `setup-repos.sh`.** Find the `clone_or_update` call for this
   path and change its branch argument.

Commit all together (`setup-repos.sh`, the detail file, `INDEX.md`) with
a message like `knowledge: retarget <RepoName> to <new-branch>`. Selective
`git add` as in step 8. Report the new tracked branch and the current HEAD
commit hash.

## Sub-workflow: Back-fill detail file for an already-cloned repository

A repository directory exists under `.knowledge/repositories/` but has
no per-repo detail file (legacy state, or cloned manually outside this
skill). The main "path already exists → fail loudly" rule does NOT apply
here — only to fresh adds that would overwrite.

Procedure:

1. **Confirm** the directory exists and has a `.git` folder. If either is
   missing, fall back to the main workflow (full add) instead.
2. **Skip the clone and pin** (no `git clone`, no checkout).
   **Still run step 3 (lock the push URL)** — idempotent, and important
   for repos cloned manually outside this skill that may still have a
   live push URL.
3. **Check `setup-repos.sh`.** If the path is not already listed in
   `.knowledge/scripts/setup-repos.sh`, add it (step 8 of the main
   workflow).
4. **Resume at step 5** — write the detail file from the template,
   filling `branch:` from `setup-repos.sh` and reading the working tree
   for `key paths`.
5. **Step 6** — add the INDEX entry as normal.
6. **Step 9** — commit the detail file, INDEX update, and any changes to
   `setup-repos.sh`. The local repo directory is untouched.
7. **Report** that this was a back-fill (not a clone) so the user knows
   no clone operation occurred.

## MUST do

- Read the existing `INDEX.md` and the relevant template file before
  writing — preserve established order and pattern.
- Keep `migrated_from`/`migrated_to` cross-links bidirectional and
  consistent. If A's `migrated_to` lists B, then B's `migrated_from` must
  equal A.
- Surface `language` and `build_tool` (axon-examples) on every variant
  bullet in `INDEX.md` so readers can choose without opening detail files.
- Ask for branches/commits before writing the Migration Diff callout.
- Ask for `keywords` if the user hasn't volunteered any.
- Ask for at least one `## Highlights` bullet on every new detail file.
- Lock the push URL (`git -C <path> remote set-url --push origin DISABLED`)
  immediately after cloning. Also run this in the back-fill sub-workflow —
  it's idempotent and protects manually-cloned repos.
- Append the `clone_or_update` call to `setup-repos.sh` — required for the
  repo to be reproducible on fresh checkouts.

## MUST NOT do

- Do NOT add Claude Code attribution in commit messages.
- Do NOT use `git add .` or `git add -A`.
- Do NOT silently overwrite an existing detail file or repository directory —
  fail loudly and ask the user how to proceed.
- Do NOT name the detail file `CLAUDE.md` or `SKILL.md` — blocked by hook.
- Do NOT skip the `INDEX.md` update; a repo without an index entry is
  incomplete work.
- Do NOT bundle unrelated changes into the commit. **Exception:** on the
  very first use of this skill in a repo, the skill's own scaffolding
  (`SKILL.md`, hooks, `.knowledge/README.md`, empty type-level
  `INDEX.md` files, and any repos added during the same bootstrap
  pass) may legitimately be uncommitted. Bundling them into a single
  "init knowledge repositories" commit is acceptable — selective `git
  add` still applies (no `.`/`-A`), but the staged set will be larger
  than a steady-state add. From the second invocation onward, the rule
  is strict: only files this skill touched belong in the commit.
- Do NOT `cd <repo_path>` inside the skill — use `git -C <path>`.
  The `cd` form leaks `cwd` across subsequent Bash calls in the same
  session.

## Edge cases

- **Same upstream URL, different paths** — fully supported. Common for
  `axon4/<app>` and `axon5/<app>` pointing at the same upstream repository.
- **Detached HEAD after `git checkout <commit>`** — normal. Ignore the warning.
- **`INDEX.md` does not exist or is empty** — create it with the standard
  AI-agent header (see `references/index-entry-templates.md`) and append
  the new entry.
- **Repository directory already present at path** — fail loudly. Do not
  overwrite or re-clone.
- **Detail file already present** — fail loudly with `diff` guidance. Do
  not silently overwrite.
- **Clone fails (network/auth)** — surface the error verbatim, do not retry
  silently. Ask the user to verify URL/auth.
- **Only one side of an axon-examples pair exists** — that's fine. Document
  the present side, mark the counterpart as `_migration pending_` in the
  INDEX entry, and leave the cross-link frontmatter absent (or as an empty
  list) until the counterpart is added.
- **Repository present but no detail file** — recovery, not an error. Use
  the "Back-fill detail file for an already-cloned repository" sub-workflow
  above. Do not re-clone.
- **User asks to change a repository's tracked branch** — use the
  "Retarget a repository's tracked branch" sub-workflow above. Do not
  remove and re-clone.
- **Bootstrap commit (first use in repo)** — see the MUST NOT
  "exception" note. Bundling skill scaffolding + first repository into
  one init commit is the only sanctioned exception to the
  no-unrelated-changes rule.
- **Tracked branch is force-pushed upstream** — `git fetch` will print
  `forced update`. This is benign for an in-flight feature branch, but
  the report to the user MUST mention it.

## Done when

- The repository is cloned at the requested ref under
  `.knowledge/repositories/<type>/...`.
- Its `origin` push URL is `DISABLED` (verify with
  `git -C <repo_path> remote -v`).
- `.knowledge/scripts/setup-repos.sh` contains a `clone_or_update` call
  for this path with the correct branch.
- The per-repo detail file exists with full frontmatter and the type's
  required body sections, including `## Highlights`.
- The type-level `INDEX.md` has the standard AI-agent header and a new
  entry with a `Keywords:` line linking to the detail file.
- For axon-examples: counterpart cross-links are updated and bidirectional;
  Migration Diff callout is present iff both sides exist.
- A single focused commit captures all of the above.
- The user has been told the commit hash, detail file path, and INDEX
  section the entry landed in.

## References (load only what the current task needs)

- `references/templates-axonframework.md` — per-repo template for framework refs.
- `references/templates-axon-examples.md` — per-repo template for paired
  axon4/axon5 example apps, including migration-pair frontmatter rules.
- `references/templates-ai-bestpractices.md` — per-repo template for general
  AI/best-practices references.
- `references/index-entry-templates.md` — `INDEX.md` entry snippets and the
  standard AI-agent header for every type.
