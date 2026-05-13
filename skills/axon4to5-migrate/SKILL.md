---
name: axon4to5-migrate
description: >-
  Migrate a Spring Boot or plain-Configurer Axon Framework 4 project to Axon
  Framework 5 while preserving AF4 architecture and legacy event storage.
  Supports phased, single-target, and debug modes.
argument-hint: "[<file path or FQ class> | debug | phased]"
disable-model-invocation: true
---

# Axon 4 → 5 Migration

Migrate code only. Preserve the project's existing architecture:

- no DCB unless the user explicitly chooses it outside this skill;
- no new architectural patterns;
- legacy event storage stays readable;
- Spring Boot projects stay Spring Boot;
- plain `Configurer` projects stay direct AF5 builder/configurer code.

SQL, data movement, token-store migration, snapshot-row migration, and replay
operations are out of scope. If a recipe offers a `move-to-*` path, that means
"rewrite code to point at that backend"; the user owns schema and data work.

## Load First

Read these before touching the target project:

1. [references/routing.md](references/routing.md) — mode dispatch, phase order,
   target discovery, single-file routing, and project-wide unsupported features.
2. [references/state.md](references/state.md) — `progress.md`, resume,
   pinned decisions, commits, and final cleanup.
3. [references/recipe-contract.md](references/recipe-contract.md) — how to run
   a recipe and interpret its `result:`.

Then load only the recipe file(s) needed for the current target. Do not preload
all recipes.

## Modes

Default mode is `phased`.

| User input | Mode | What to do |
|---|---|---|
| empty or `phased` | phased | Resume from `.axon4to5-migration/progress.md`; if absent, initialize it; run recipes in routing order. |
| `debug` | debug | Build once without isolated scopes, cluster compile errors, route the best next target, repeat until green or blocked. |
| file path or FQ class | single | Resolve the file, route it using [routing.md](references/routing.md), ensure pinned decisions exist, run exactly one recipe target. |

If the input looks like a file/FQCN but cannot be resolved, stop and surface the
bad target. Do not silently fall back to phased mode.

## Simple Runner

Keep control flow flat:

1. Resolve mode and project root.
2. Load or create state via [state.md](references/state.md).
3. Pick one recipe row and one target from [routing.md](references/routing.md).
4. Run that recipe using [recipe-contract.md](references/recipe-contract.md).
5. Handle the recipe `result:` with the table below.
6. Update `progress.md`, commit explicit paths only when the table says to, and
   move to the next target.

Recipe result handling:

| `result:` | Runner action |
|---|---|
| `success` | Commit changed code plus `.axon4to5-migration/progress.md` and `learnings.md` if updated. |
| `skipped` | No commit; mark the target done if appropriate. |
| `rejected` | No commit; route to `caller-expects.next` if it names another recipe. |
| `needs-decision` | Ask the user using the recipe's options; pin the answer; rerun or defer. |
| `blocked` | Record the blocker; commit only if the recipe intentionally left TODO/commented code or state changes. |
| `failed` | Stop normal migration; surface the reason and offer debug mode, pause, or stop. |

Branch only on `result:`. Do not infer state from legacy fields such as
`needs-user-decision`, `recipe-status`, or `skip`.

## Required Project Checks

Before any recipe runs, pin these decisions in `progress.md` in this order:

1. `license`: `free-af5` or `axoniq-commercial`. Ask once. Recommend
   `axoniq-commercial` when the project uses commercial-only dependencies or
   AF4 features not yet in free AF5 (`@Saga`, upcasters, replay, Mongo DLQ,
   `axon-mongo`, `axon-kafka`, `axon-amqp`, `axon-tracing-opentelemetry`, or
   `org.axoniq.*`). Otherwise recommend `free-af5`.
2. `wiring`: `spring-boot` or `framework-config`. Detect from dependencies,
   `@SpringBootApplication`, Axon `@Bean`s, or direct `Configurer` use. Ask once
   only if ambiguous.
3. `build-tool`: `maven` or `gradle`. Detect from `pom.xml` /
   `build.gradle(.kts)`. Ask once if both exist. Halt if neither exists.

Recipes read these pinned decisions. They must not re-detect or re-prompt.

## External Skills

Invoke these skills instead of duplicating their mechanics:

- `axon4to5-openrewrite` — bulk OpenRewrite pass. Called by the `openrewrite`
  recipe with `--framework axon` for `free-af5` or `--framework axoniq` for
  `axoniq-commercial`, always with commit disabled because this runner owns
  migration commits.
- `axon4to5-isolatedtest` — per-target Maven profile / Gradle source set for
  compile and test isolation. Iterative recipes call it with `target-name`,
  source lists, optional `extra-deps`, and `cleanup`.

The final project build is the only direct build command this skill runs:

- Maven: `./mvnw clean verify`
- Gradle: `./gradlew clean build`

## Hard Rules

- Never run a recipe before `license`, `wiring`, and `build-tool` are pinned.
- Never emit SQL, DDL, schema migrations, or persisted-data copy steps.
- Never delete unsupported AF4 wiring silently. Comment it with
  `TODO[AF5 migration: <blocker-key>]`, record the blocker, and preserve the
  audit trail.
- Never hand-write `isolated-*` build scopes; call `axon4to5-isolatedtest`.
- Never run full `verify`/`build` between early phases; use isolated scopes
  until final cleanup.
- Never use `git add -A`, push, amend, `--no-verify`, or commit on
  `main`/`master`.
- Never mix user WIP into migration commits. Stage explicit paths only.

## Reference Index

Core:

- [references/routing.md](references/routing.md)
- [references/state.md](references/state.md)
- [references/recipe-contract.md](references/recipe-contract.md)
- [references/output-contract.md](references/output-contract.md)
- [references/verification.md](references/verification.md)
- [references/commit-cadence.md](references/commit-cadence.md)
- [references/source-access.md](references/source-access.md)

Recipes:

- [references/openrewrite.md](references/openrewrite.md)
- [references/aggregate/aggregate.md](references/aggregate/aggregate.md)
- [references/event-processor/event-processor.md](references/event-processor/event-processor.md)
- [references/command-gateway/command-gateway.md](references/command-gateway/command-gateway.md)
- [references/query-gateway/query-gateway.md](references/query-gateway/query-gateway.md)
- [references/query-handler/query-handler.md](references/query-handler/query-handler.md)
- [references/interceptors/interceptors.md](references/interceptors/interceptors.md)
- [references/event-storage-engine/event-storage-engine.md](references/event-storage-engine/event-storage-engine.md)
- [references/debug/debug.md](references/debug/debug.md)
- [references/saga/saga.md](references/saga/saga.md)

Canonical Axon migration docs live under [docs/](docs/). Recipes link to the
specific docs they need.
