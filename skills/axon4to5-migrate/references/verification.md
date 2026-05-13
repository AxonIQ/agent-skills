# Verification — delegated entirely to external skills

This skill does NOT own per-target build-scoping or bulk-migration mechanics. Both responsibilities are delegated to installed external skills, invoked via the **Skill tool** (or its host-equivalent). Recipes MUST NOT hand-craft `./mvnw -P …`, `./gradlew :test…`, `rewrite-maven-plugin:run`, or any other build-tool invocation — that would defeat the delegation and re-introduce build-tool quirks this skill stopped owning.

| Need | External skill | When to invoke |
|---|---|---|
| Bulk Axon 4 → 5 OpenRewrite migration (Migration Phase #1) | `axon4to5-openrewrite` | Once per project, from the `openrewrite` recipe. Driven by license decision (`--framework axon` or `--framework axoniq`). |
| Per-target scoped compile / scoped test for ONE migrated class | `axon4to5-isolatedtest` | Every iterative recipe (`aggregate`, `event-processor`, `command-gateway`, `query-gateway`, `query-handler`, `event-storage-engine`) AND every preflight / debug compile-only check. |

Each recipe's `## Verify` section spells out the exact inputs to pass; this file describes the contract and the call shape.

## `axon4to5-isolatedtest` — call shape

**Always** invoke via the Skill tool. Pass a structured input block:

```
Skill: axon4to5-isolatedtest
Inputs:
  target-name: <SimpleClassName>            # PascalCase Java identifier; drives scope id isolated-<TargetName>
  build-file: <absolute path to pom.xml | build.gradle(.kts)>
  main-sources:                              # repo-relative paths under src/main/{java,kotlin}
    - src/main/java/<…>/<Target>.java
    - src/main/java/<…>/<TargetHelper>.java
  test-sources:                              # repo-relative paths under src/test/{java,kotlin}; pass [] for compile-only run
    - src/test/java/<…>/<Target>Test.java
  extra-deps:                                # AF5 coordinates needed only in this scope; rare
    - org.axonframework:axon-modelling:${axon5.version}
  cleanup: false                             # true ONLY on the recipe's last successful run before commit
```

What the external skill does:

- Adds (or augments) an `isolated-<TargetName>` Maven profile / Gradle source-set + Test task in the supplied `build-file`.
- Scopes compilation to the union of `main-sources` ∪ `test-sources` (plus the transitive references the compiler pulls in — see "transitive references leak" in the skill's own docs).
- Runs the test classes only.
- Returns: compile result, test counts (`Tests run: N, Failures: M` style), the exact copy-paste compile + test commands, and a **scaffolding status** field (`kept` vs `removed`).
- Is idempotent — re-invoking with the same `target-name` augments the scope's include list, never replaces it.
- Removes the scope from the build file iff `cleanup: true` AND both compile and test runs are green.

Recipes read the report and decide their own End condition. They never parse Maven/Gradle log lines directly.

### Re-invocation rules

- **First pass**: pass the minimal `main-sources` / `test-sources`. The external skill names any file the compiler needed but couldn't find — copy those names into a follow-up invocation.
- **Augmenting**: a follow-up call with an extended source list merges into the existing scope, deduped. Sibling scopes are untouched.
- **Cleanup**: invoke a final time with `cleanup: true` ONLY when both compile and tests are green AND the migration runner is ready to commit. On red runs the external skill leaves the scope in place so the user can iterate.

## `axon4to5-openrewrite` — call shape

Invoked once from the `openrewrite` recipe (Migration Phase #1):

```
Skill: axon4to5-openrewrite
Arguments: --framework <axon | axoniq> --commit false
```

Mapping from pinned license to `--framework`:

| Pinned license (`progress.md` Pinned-decisions) | `--framework` value |
|---|---|
| `free-af5` | `axon` |
| `axoniq-commercial` | `axoniq` |

`--commit false` keeps the migration runner in charge of the commit (per [commit-cadence.md](commit-cadence.md)); the external skill leaves the working tree modified for the migration runner to stage and commit with the conventional message.

What the external skill does:

- Detects build tool (Maven vs Gradle).
- Resolves and pins the recipe artifact version.
- Bumps the build wrapper on `Unsupported class file major version` errors.
- Surfaces specific failure routes (`Could not find artifact …`, recipe parse errors, etc.) with a one-line summary the migration runner forwards verbatim.

Recipes never invent Maven/Gradle invocations for this phase.

## Pre-flight check — has the work already been done?

Before invoking ANY iterative recipe's procedure, run its preflight. Pattern:

1. Use `mcp__ide__getDiagnostics` for the target file(s) if available.
2. If diagnostics are unavailable, invoke `axon4to5-isolatedtest` with `test-sources: []` for a compile-only signal.
3. If compile is clean AND a test class exists, invoke `axon4to5-isolatedtest` again with `test-sources` populated.
4. If green → STOP. Ask the user via `AskUserQuestion`:
   - **Skip** — treat as already migrated, move on.
   - **Deep verify** — diff current source against AF4 baseline (`git log` / `git show`) to confirm nothing was silently lost (dropped `snapshotTriggerDefinition`, missing `@EventTag`, lost `@CreationPolicy` semantics).
5. Only proceed to the procedure if user picks **Deep verify**, or step 2/3 reported failures.

> Running a full procedure against an already-migrated class wastes context and risks double-edits.

## Full verify (stabilization / FINALIZE only)

At FINALIZE every `isolated-*` scope has been cleaned out via repeated `axon4to5-isolatedtest` invocations with `cleanup: true`. The migration runner then runs the project's standard build directly — this is the only place this skill ever shells out to Maven/Gradle by hand, and only because the build is project-wide, not per-target:

```bash
./mvnw -f <target>/pom.xml clean verify       # Maven path
./gradlew -p <target> clean build              # Gradle path
```

Green = migration done. Any `isolated-*` scope still in a build file at this point is a smell — see SKILL.md FINALIZE step.

## End-condition shape (every recipe defines its own)

A recipe's End condition is a concrete check — not "feels migrated". Every iterative recipe expresses it as an `axon4to5-isolatedtest` invocation that must return green:

- **Aggregate**: green scoped run with `target-name: <AggregateSimpleName>`, `main-sources` covering aggregate + commands + events + child entities, `test-sources` covering the aggregate's test class + subclasses, `extra-deps` including `axon-modelling`, `axon-eventsourcing`, `axon-test`.
- **EventProcessor**: green scoped run with `target-name: <ProcessorSimpleName>`, `main-sources` = the projector, `test-sources` = its test class (if any), `extra-deps` including `axon-messaging`, `axon-modelling`, `axon-test`.
- **CommandGateway / QueryGateway / QueryHandler / configuration-reads**: green compile-only scoped run with the migrated class as the only entry in `main-sources` and `test-sources: []`, `extra-deps` including `axon-messaging` (+ `axon-configuration` for configuration-reads).
- **EventStorageEngine**: green compile-only scoped run with the configuration class in `main-sources` and `extra-deps` covering `axon-eventsourcing` plus the backend (`axon-eventsourcing-jpa` OR `axon-server-connector`).

Recipes state their End condition in their first section. They reach it by calling `axon4to5-isolatedtest` — never by parsing raw build output.
