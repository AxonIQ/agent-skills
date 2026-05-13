---
name: axon4to5-migrate
description: >-
  Migrate an Axon Framework 4 Spring Boot or plain Configurer project to Axon
  Framework 5 while preserving AF4 architecture, legacy event storage, and
  existing behavior. Supports phased, single-target, and debug use.
argument-hint: "[<file path or FQ class> | debug | phased]"
disable-model-invocation: true
---

# Axon 4 -> 5 Migration

Read [references/playbook.md](references/playbook.md). It is the whole skill.

## Non-Negotiables

- Code migration only. Never generate SQL, DDL, data-copy, token-store, replay,
  or snapshot-row migration.
- Preserve AF4 architecture: no DCB, no new workflow model, no wiring style
  switch unless the user explicitly decides that outside this skill.
- Pin `license`, `wiring`, and `build-tool` before any recipe.
- Use `axon4to5-openrewrite` for the bulk rewrite and `axon4to5-isolatedtest`
  for per-target verification. Do not duplicate either skill.
- Commit explicit paths only; never `git add -A`, push, amend, `--no-verify`,
  or commit on `main`/`master`.

## Modes

| Input | Mode | Action |
|---|---|---|
| empty / `phased` | phased | Resume from `.axon4to5-migration/progress.md`, then run playbook order. |
| file or FQCN | single | Resolve one source file, route it by the playbook table, run one target. |
| `debug` | debug | Compile once, route the largest error cluster, repeat until green/blocked. |

If a file/FQCN cannot be resolved, stop. Do not fall back to phased mode.

## Done

Final build is green with no `isolated-*` scope left:

- Maven: `./mvnw clean verify`
- Gradle: `./gradlew clean build`
