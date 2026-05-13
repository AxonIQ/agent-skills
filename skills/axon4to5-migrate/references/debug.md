# Recipe: debug — triage from build output

Loop: compile → cluster errors by root cause → route ONE high-leverage cluster to a recipe → recompile → re-cluster from fresh evidence.

> Do NOT fix diagnostics line-by-line. ONE missing dep / stale package / unmigrated construct creates dozens of cascade errors. Find the **root cause group** first.

## Inputs

- `target` — project dir (defaults to CWD if it has `pom.xml`/`build.gradle*`).
- `scope` — optional `isolated-<X>` only when evidence says the build can't reach the migrated scope without it.

## Preconditions

- OpenRewrite has run.
- Target is NOT the AxonFramework repo itself.

## Preflight

`./mvnw test-compile -DskipTests` (or `./gradlew testClasses -x test`) — if green → `result: skipped`.

## Procedure

### Step 1 — Compile (source of truth)

Use main + test compilation:

```bash
# Maven
./mvnw test-compile -DskipTests -DfailIfNoTests=false -Dsurefire.failIfNoSpecifiedTests=false
# Gradle
./gradlew testClasses -x test
```

If a prior recipe left an `isolated-<X>` scope AND the full compile is blocked by intentionally unmigrated code, re-invoke `axon4to5-isolatedtest` to retry the scoped compile. Don't treat a stale scope as truth — re-invoke with an extended source list if it excludes needed files.

### Step 2 — Normalize diagnostics

For each diagnostic capture: file:line, module/source set, error kind, symbol/type/method/package, nearby context, primary vs cascading.

Non-Java build failures (build-tool, JDK, dependency resolution, profile-scope) → classify separately. Do NOT route to construct migration recipes.

### Step 3 — Cluster by root cause

Group by the **smallest migration action that removes the largest cascade**. Good clusters share one of: same source file/construct, same missing AF4 package/type, same stale gateway/handler API, same test fixture API, same configuration API, same event-store API, same build-tool problem.

Example: `AggregateLifecycle.apply`, `AggregateTestFixture`, missing `@Command`, missing `@EventTag` around the same aggregate → ONE aggregate cluster, not four.

Common shapes:
- **Same missing symbol** across many files → ONE root cause.
- **Same call-site shape** (`incompatible types: CommandResult cannot be converted to CompletableFuture` repeated) → command gateway not migrated.
- **Same annotation** (`cannot find symbol: @QueryHandler`) → query handler not migrated.
- **Same import** (`org.axonframework.config.Configuration`) → topic-nested configuration-reads file not yet applied.

### Step 4 — Pick ONE cluster and route

Priority:
1. Build/JDK/dependency/profile issues preventing meaningful Java diagnostics.
2. Dependency or `isolated-*` scope gaps hiding intended target scope.
3. Construct roots creating many cascades.
4. Production sources before test sources when both fail independently.
5. Test fixtures tied to an already-migrated construct.
6. Isolated stale imports / obvious leftovers.

Routing:

| Cluster shape | Route to |
|---|---|
| `cannot find symbol: @QueryHandler` (AF4) | [../query-handler/query-handler.md](query-handler.md) |
| `@Aggregate`, `@AggregateRoot`, `@AggregateIdentifier`, `@TargetAggregateIdentifier` | [../aggregate/aggregate.md](aggregate.md) |
| `@ProcessingGroup`, `@EventHandler` (AF4) | [../event-processor/event-processor.md](event-processor.md) |
| `CommandResult cannot be converted to CompletableFuture` | [../command-gateway/command-gateway.md](command-gateway.md) |
| `ResponseType`, `multipleInstancesOf` | [../query-gateway/query-gateway.md](query-gateway.md) |
| `EventProcessingConfiguration` lookups (`eventProcessor` / `tokenStore` / `sequencedDeadLetterProcessor`) | [../event-processor/configuration-reads.md](config-reads.md) |
| `org.axonframework.config.Configuration` used for `commandBus()` | [../command-gateway/configuration-reads.md](config-reads.md) |
| `org.axonframework.config.Configuration` used for `queryBus()` / `queryUpdateEmitter()` | [../query-gateway/configuration-reads.md](config-reads.md) |
| `ConfigurerModule`, `DefaultConfigurer.defaultConfiguration`, `implements Lifecycle`, `EventStorageEngine`, `JpaEventStorageEngine`, `EmbeddedEventStore` | [../event-storage-engine/event-storage-engine.md](event-storage-engine.md) |
| `EventProcessingConfigurer` not resolved | [../event-processor/event-processor.md](event-processor.md) (Steps 10–11) |
| Stale/wrong `isolated-*` scope (compiler pulls unrelated transitive files) | re-invoke `axon4to5-isolatedtest` with corrected `main-sources` / `test-sources` (it augments idempotently) |

### Step 5 — Recompile

If error count dropped → cluster was correct → repeat Step 2 with fresh evidence.
If unchanged or grew → recipe didn't reach the actual root cause → re-cluster.

### Step 6 — Stop conditions

- Build green → done.
- Next cluster blocked on missing product intent / unsupported AF5 feature → stop with concrete diagnosis.
- Only manual/out-of-scope errors remain → record in `learnings.md`, defer.
- Same cluster picked twice without progress → `AskUserQuestion`: surface diagnostic dump / skip-and-stash / stop.

## Direct fixes (limited)

Edit directly ONLY when no sibling recipe owns the construct AND the fix is small, mechanical, verified by compilation:
- stale imports left after a sibling migration,
- obvious package/class rename leftovers,
- small dependency / plugin / profile / wrapper-command fixes,
- deleting an unused import after a delegated fix.

NEVER directly rewrite a construct that has a dedicated sibling recipe.

## End condition

Build green for the chosen scope: main + test compile OK with no `isolated-*` scope active, OR user accepts a known-deferred subset (decision-only commit).

## Output

```yaml
result: success | skipped | needs-decision | failed
target: <project dir>
reason: <one short line>
decisions:
  clusters-handled:
    - cluster: <signature>
      routed-to: <recipe>
      defer: <reason>                # if applicable
notes: <non-obvious lessons for learnings.md>
```

| State | `result:` | `next:` |
|---|---|---|
| Build went green | `success` | `proceed` |
| Already green at Preflight | `skipped` | `proceed` |
| "No progress" stop (same cluster twice) | `needs-decision` | `ask-user` |
| Build still red, no recipe matches | `failed` | `halt` |

## Report format (for triage/handoff)

```markdown
## Compile Command
`<command>` -> `<green|failed|blocked>`

## Queue
1. `<group id>` -> `<route>`
   Root cause: `<short hypothesis>`
   Evidence: `<files/classes + representative diagnostics>`
   Action: `<delegate to recipe X on class Y>` or `<small direct fix>`

## Current Action
Delegating `<group id>` to `<recipe>` because `<reason>`.

## Blocked / Manual
- `<cluster>`: `<why no recipe/direct fix applies>`
```

## Anti-patterns

- Fixing one error line at a time without clustering.
- Ignoring active `isolated-*` scope(s) — runs unrelated AF4 code into the compile.
- Running `./mvnw verify` instead of `test-compile` — runtime errors hide compile root causes.
- Editing outside the cluster's scope to "tidy up".
- Routing non-Java build failures (JDK / dependency / plugin) to construct recipes.
- Directly rewriting a construct that has a dedicated sibling recipe.
