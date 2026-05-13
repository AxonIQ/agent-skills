# Commit cadence

One commit per item, on the user's current branch (never `main`/`master`), never pushed (user controls remote).

## `result:` → commit

| `result:` | Commit | Subject |
|---|---|---|
| `success` | code + `progress.md` (+ `learnings.md` if dirty) | per recipe — see table below |
| `skipped` / `rejected` / `needs-decision` / `failed` | none | — |
| `blocked` with edits (comment-out + TODO) | code + `progress.md` + `learnings.md` | per recipe |
| `blocked` decision-only (no edits) | `progress.md` Pinned-decisions only | `docs(af5-migration): record decision on <recipe>/<target>` |

## Subjects

| Outcome | Subject line |
|---|---|
| INIT | `chore(af5-migration): initialize migration` |
| openrewrite done | `chore(af5-migration): apply OpenRewrite recipe <name>@<version>` |
| aggregate item | `refactor(af5-migration): migrate aggregate <SimpleName> to AF5` |
| event-processor item | `refactor(af5-migration): migrate event handler <SimpleName> to AF5` |
| command-gateway item | `refactor(af5-migration): migrate command dispatch in <SimpleName> to AF5` |
| query-gateway item | `refactor(af5-migration): migrate query dispatch in <SimpleName> to AF5` |
| query-handler item | `refactor(af5-migration): migrate query handler <SimpleName> to AF5` |
| interceptors item | `refactor(af5-migration): migrate interceptor <SimpleName> to AF5` |
| event-storage-engine | `feat(af5-migration): wire AggregateBased{Jpa,AxonServer}EventStorageEngine` |
| Stabilization fix | `fix(af5-migration): <one-line>` |
| FINALIZE | `chore(af5-migration): remove isolated-* scaffolding` |

## Persistence checklist (before every commit)

- [ ] `progress.md` **▶︎ RESUME HERE** points at the *next* unit (exact recipe + verify command).
- [ ] Recipe status table + per-recipe plan rows updated for just-finished item.
- [ ] `learnings.md` has a dated entry for any non-obvious lesson or blocker.
- [ ] Commit includes both code AND `progress.md` rewrite.

## Command shape

```bash
git -C <target> add <explicit-paths> .axon4to5-migration/
git -C <target> commit -m "<subject>

<body — verification command used, anything a reviewer needs>
"
```

**Never** `git add -A`, `git commit --amend`, `git push`, `--no-verify`, or `Co-Authored-By:` lines.

## Dirty tree mid-run

If `git status --porcelain` shows files the orchestrator did not touch, `AskUserQuestion` (see SKILL.md "Dirty working tree on resume"): stage-only-migration-files / let-user-clean-up / skip-this-commit.
