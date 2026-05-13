# State, Resume, Commits, Finalize

State lives in `<target>/.axon4to5-migration/`:

```
.axon4to5-migration/
├── index.md
├── progress.md
└── learnings.md
```

Seed these from `assets/*-template.md` on the first phased run. `progress.md`
is the resume source of truth; `learnings.md` is append-only and only for
surprises, non-obvious decisions, and manual fixes.

## Initialize

1. Create the state directory and seed templates.
2. Pin required decisions in this exact order: `license`, `wiring`,
   `build-tool`.
3. Scan project-wide unsupported rows from [routing.md](routing.md), especially
   sagas, and record the user's decision.
4. Commit explicit state files with:
   `chore(af5-migration): initialize migration`.

## Resume

When `progress.md` exists:

1. Read `▶︎ RESUME HERE`.
2. Check `git rev-parse --short HEAD` and `git status --porcelain`.
3. If HEAD moved but the tree is clean, trust the user and continue.
4. If the tree is dirty, ask whether to inspect, let the user clean it, or
   continue from dirty state. Never reset without explicit user approval.
5. Read pinned decisions. Do not ask them again.

## Before Every Commit

Update `progress.md` before staging:

- `▶︎ RESUME HERE` points to the next unit, not the one just finished.
- phase/recipe status reflects the just-finished target;
- commit SHA placeholder or last commit field is ready to update;
- blocker/defer decisions are recorded;
- `learnings.md` has a dated entry when the work exposed a non-obvious issue.

Stage explicit paths only. Include code, `progress.md`, and `learnings.md` in
the same commit when they describe the same change. Use
[commit-cadence.md](commit-cadence.md) for subject lines.

Never use `git add -A`, push, amend, `--no-verify`, or commit on
`main`/`master`.

## Dirty User Work

If unrelated user WIP appears while you are working, pause before committing:

- recommended: stage and commit only the migration files you touched;
- or let the user clean the tree;
- or skip the commit and record the skip.

Do not sweep unrelated files into a migration commit.

## Finalize

After all routing rows are done:

1. For every recorded isolated scope, invoke `axon4to5-isolatedtest` with
   `cleanup: true`.
2. Promote still-needed AF5 deps from isolated scopes into the main build.
3. Remove activation references from scripts, CI, and docs
   (`-P isolated-`, `:testIsolated`, etc.).
4. Run the standard full build with no isolated scope active:
   - Maven: `./mvnw clean verify`
   - Gradle: `./gradlew clean build`
5. If the build fails, classify it as recipe-owned, dependency-promotion, or
   environment/infrastructure. Reopen the recipe or fix deps when traceable;
   otherwise ask the user.
6. When green, set `RESUME HERE = Migration complete` and commit:
   `chore(af5-migration): remove isolated-* scaffolding`.

A completed migration leaves no `isolated-*` profiles/source sets in build
files and no active isolated scope in verification commands.
