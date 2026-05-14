# Recipe: debug — triage from build output

Loop: compile → cluster errors by root cause → route ONE high-leverage cluster to a recipe → recompile → re-cluster from fresh evidence.

> Do NOT fix diagnostics line-by-line. ONE missing dep / stale package / unmigrated construct creates dozens of cascade errors. Find the **root cause group** first.

## Inputs

```yaml
target: <project dir>                        # defaults to CWD if it has pom.xml / build.gradle*
scope: <isolated-X scope name>               # optional — only when evidence says compile can't reach migrated scope without it
wiring: spring-boot | framework-config        # pinned (informational)
decisions: { ... }                            # see ## Decision points
```

## Preconditions

- OpenRewrite has run.
- Target is NOT the AxonFramework repo itself.

## Preflight

1. Compile: `./mvnw test-compile -DskipTests` (or `./gradlew testClasses -x test`) — if green → **🔒 await decision** [`already-green`](#already-green).

## Decision points

### already-green

- **Trigger**: detected-at-preflight (only when initial compile is green)
- **Question**: > "Project compile is already green. Skip debug mode?"
- **Options**:
    - `skip` *(Recommended)* — `output { result: skipped }`
    - `force-cluster` — proceed anyway (rare; user wants to inspect even on green)
- **Auto-policy**:
    - `always: skip`
    - `fallback: ask-user`
- **Effect**:
    - `skip` → exit with `result: skipped`.
    - `force-cluster` → continue to Procedure.

### no-progress

- **Trigger**: triggered-in-procedure (only when the same cluster is picked twice in a row without error count dropping)
- **Question**: > "Last cluster routed to recipe `<X>` but error count didn't drop. How to proceed?"
- **Options**:
    - `surface-diagnostic-dump` — show user the raw compiler output; user decides next move
    - `skip-and-stash` — defer this cluster; record in `learnings.md`; pick next cluster
    - `stop` — halt debug loop
- **Auto-policy**:
    - `fallback: ask-user`
- **Effect**:
    - `surface-diagnostic-dump` → emit dump; resume loop next invocation
    - `skip-and-stash` → record stash; pick next cluster
    - `stop` → `output { result: failed, reason: "debug loop made no progress" }`, exit.

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
result: success | skipped | rejected | blocked | failed
target: <project dir>
reason: <one short line>
decisions:
  already-green: skip | force-cluster | n/a
  no-progress: surface-diagnostic-dump | skip-and-stash | stop | n/a
  clusters-handled:
    - cluster: <signature>
      routed-to: <recipe>
      defer: <reason>                # if applicable
files_touched:
  - <any files debug itself edited via "Direct fixes (limited)">
  # Most edits in debug mode happen via delegated recipes — their files_touched are recorded
  # in their own commits, not in this output.
notes: <non-obvious lessons for learnings.md>
```

| State | `result:` |
|---|---|
| Build went green after loop | `success` |
| Already green at Preflight | `skipped` |
| User chose `stop` on `no-progress` | `failed` |
| Build still red, no recipe matches remaining clusters | `failed` |

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
