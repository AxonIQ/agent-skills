# Verification — call shapes

All scoped compile/test work is delegated to the external `axon4to5-isolatedtest` skill (invoked via the Skill tool). Recipes MUST NOT hand-craft `./mvnw -P …` or `./gradlew :test…`.

## `axon4to5-isolatedtest`

```
Skill: axon4to5-isolatedtest
Inputs:
  target-name: <SimpleClassName>            # PascalCase; drives scope id isolated-<TargetName>
  build-file: <abs path to pom.xml | build.gradle(.kts)>
  main-sources: [src/main/java/<…>/<Target>.java, …]   # repo-relative, per-file (no globs)
  test-sources: [src/test/java/<…>/<Target>Test.java]  # [] for compile-only
  extra-deps:  [org.axonframework:axon-modelling:${axon5.version}, …]
  cleanup: false                             # true ONLY on the recipe's last green run before commit
```

Behavior: adds/augments `isolated-<TargetName>` Maven profile / Gradle source-set in `build-file`; runs scoped compile + test; returns counts + scaffolding-status. Idempotent — augments, never replaces. Removes the scope iff `cleanup: true` AND both runs green.

**Multi-module:** pass the abs path to the **module** that owns the target, not the reactor parent pom.

## `axon4to5-openrewrite`

Invoked once from the `openrewrite` recipe:

```
Skill: axon4to5-openrewrite
Arguments: --framework <axon | axoniq> --commit false
```

Mapping: `free-af5` → `--framework axon`; `axoniq-commercial` → `--framework axoniq`. `--commit false` leaves the working tree dirty for the orchestrator to commit.

## Preflight (every iterative recipe)

1. `mcp__ide__getDiagnostics` if available, else `axon4to5-isolatedtest` with `test-sources: []`.
2. If clean AND tests exist, re-invoke with populated `test-sources`.
3. Green → `AskUserQuestion`: **Skip** (recommended) — treat as migrated. **Deep verify** — diff vs AF4 baseline.
4. Proceed only on **Deep verify** or on a failing check.

## Full verify (FINALIZE only)

After all `isolated-*` scopes cleaned out:

```
maven:  ./mvnw -f <target>/pom.xml clean verify
gradle: ./gradlew -p <target> clean build
```
