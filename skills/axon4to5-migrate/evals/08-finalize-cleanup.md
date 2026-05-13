# Scenario 08 — FINALIZE removes every isolated-* scope

## Starting state

- Every routing-table row in `{iterative, one-shot}` shows status `done` in `progress.md`.
- Build files (`pom.xml` or `build.gradle(.kts)`) contain three `isolated-<X>` profiles / source-sets (`isolated-Faculty`, `isolated-Calendar`, `isolated-StudentProjection`).
- Scripts / CI / docs reference `-P isolated-…` (Maven) or `:testIsolated…` (Gradle) — left over from per-target runs.

## User input

```
/axon4to5-migrate
```

(continues phased; orchestrator detects no row pending → enters FINALIZE)

## Expected behavior

1. For each isolated scope recorded in `progress.md` per-phase plan:
   - Invoke `axon4to5-isolatedtest` Skill tool with `target-name: <X>` and `cleanup: true`.
2. After all cleanups, AF5 deps from those scopes are promoted into main deps; duplicate `${axon5.version}` placeholders are deduped; activation refs in scripts / CI / docs are removed.
3. Run the full build with NO scope active:
   - maven → `./mvnw -f <target>/pom.xml clean verify`
   - gradle → `./gradlew -p <target> clean build`
4. If red, classify failure (recipe / missed dep promotion / env). NEVER silently re-enable an `isolated-*` scope.
5. On green: `progress.md` rewritten ("Migration complete"), ONE commit `chore(af5-migration): remove isolated-* scaffolding`, recommend `/clear`.

## Pass / fail signals

- ✅ Pass: zero `isolated-*` profiles / source-sets / activation refs remain in any build file; full build green; one final commit.
- ❌ Fail: orchestrator hand-crafts `./mvnw -P` invocations during cleanup; a leftover `isolated-*` profile survives the final commit; FINALIZE runs even though some rows are still `pending`.

## Why this matters

Per-target scopes are scaffolding. Leaving them behind means the project ships with two parallel build configurations — CI confusion, developer confusion, and a "smell" that suggests the migration is incomplete.
