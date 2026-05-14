# Recipe: query-handler

Atomic migration of ONE class with `@QueryHandler` methods. In the simple case, **import-only** change.

## Inputs

```yaml
target: <FQ class>                          # required
target_test: <FQ test class>                # optional
wiring: spring-boot | framework-config       # pinned
decisions: { ... }                           # see ## Decision points
```

## Preflight

1. `@QueryHandler` already from AF5 location? Compile clean? → **🔒 await decision** [`skip-or-deep-verify`](#skip-or-deep-verify).
2. Class also handles other AF4 message types via AF4 imports (`@CommandHandler` / `@EventHandler` from AF4 packages)? → `output { result: rejected, route_to: <handler recipe>, reason: "other AF4 handlers on class — run their recipes first" }`, exit. Exception: if all other annotations are already AF5 imports, this recipe finishes the unit.

## Decision points

### skip-or-deep-verify

- **Trigger**: triggered-in-procedure (only when Preflight finds clean compile + AF5 import already in place)
- **Question**: > "Class appears already migrated. Skip or deep-verify?"
- **Options**:
    - `skip` *(Recommended)* — `output { result: skipped }`
    - `deep-verify` — diff vs AF4 baseline; continue if silent loss detected
- **Auto-policy**:
    - `pinned.resolver_mode == "automatic": skip`
    - `fallback: ask-user`
- **Effect**:
    - `skip` → exit with `result: skipped`
    - `deep-verify` → continue to Procedure

## In scope

ONE class — Spring `@Component`/`@Service` (Path A) OR plain class registered via Configurer (Path B) — with at least one `@QueryHandler` from AF4 location `org.axonframework.queryhandling.QueryHandler`. NOT also handling other AF4 message types (run their recipes first; exception: if all other annotations are already AF5, this recipe finishes the unit).

## FQN cheat sheet

| Element | AF4 | AF5 |
|---|---|---|
| `@QueryHandler` | `org.axonframework.queryhandling.QueryHandler` | `org.axonframework.messaging.queryhandling.annotation.QueryHandler` |
| `QueryExecutionException` | `org.axonframework.queryhandling.QueryExecutionException` | `org.axonframework.messaging.queryhandling.QueryExecutionException` |
| `MetaData` | `org.axonframework.messaging.MetaData` | `org.axonframework.messaging.core.Metadata` |
| `@MetaDataValue` | `org.axonframework.messaging.annotation.MetaDataValue` | `org.axonframework.messaging.core.annotation.MetadataValue` |

Note rename: `MetaData` → `Metadata`, `@MetaDataValue` → `@MetadataValue` (capital D dropped).

## Procedure

### Step 1 — Locate

User-named target (allow no-op verify on already-migrated), else grep for AF4 `@QueryHandler` import.

### Step 2 — Update import

`org.axonframework.queryhandling.QueryHandler` → `org.axonframework.messaging.queryhandling.annotation.QueryHandler`.

### Step 3 — Sibling AF4 query-handling imports

Move any other `org.axonframework.queryhandling.*` import on this class to `org.axonframework.messaging.queryhandling.*`.

### Step 4 — Preserve everything else

- Method bodies, params, return types — keep.
- `queryName` attribute on `@QueryHandler` — keep (same member in AF5).
- Return type / `ResponseType` — preserved; same first-parameter-is-payload contract.
- Spring stereotypes — keep.
- Query payload type + annotations — keep.

### Step 5 — Parameter resolution sweep

AF5 still resolves: `Metadata`, `@MetadataValue` params, full `Message`, active `ProcessingContext` (AF5 replacement for AF4 `UnitOfWork`).

- `MetaData` param type → rename import to `org.axonframework.messaging.core.Metadata` + rename type ref.
- `@MetaDataValue("k") X x` → rename import to `org.axonframework.messaging.core.annotation.MetadataValue` + rename annotation.
- `UnitOfWork` param → out of scope; flag for user (`ProcessingContext` migration is separate).

### Step 6 — Verify nothing else

- `QueryExecutionException` try/catch — update FQN.
- Stale AF4 `org.axonframework.queryhandling.*` imports — remove.
- `QueryUpdateEmitter` usage on the class — out of scope, flag for user.

### Path A — Spring Boot

Class stays a Spring stereotype; `MessageHandlerLookup` auto-discovers `@QueryHandler` methods. No registration code required — Steps 2–6 are sufficient.

### Path B — framework Configurer

AF4: `configurer.registerQueryHandler(c -> new CourseStatsQueryHandler(repo));`

AF5 — build a `QueryHandlingModule` and register it:

```java
import org.axonframework.messaging.queryhandling.configuration.QueryHandlingModule;

configurer.registerQueryHandlingModule(
    QueryHandlingModule.named("get-course-stats-by-id")
        .queryHandlers()
        .autodetectedQueryHandlingComponent(
            cfg -> new CourseStatsQueryHandler(cfg.getComponent(CourseStatsRepository.class))));
```

- `autodetectedQueryHandlingComponent` scans the instance for `@QueryHandler` methods.
- Module name (`"get-course-stats-by-id"`) is local — descriptive label; need not match anything else.
- Dependencies → `cfg.getComponent(<DepType>.class)`; register upstream via `componentRegistry(cr -> cr.registerComponent(<DepType>.class, c -> ...))`.

If the bootstrap chain registers the AF4 form, replace in place. If you can't locate the bootstrap, set `decisions.configurer-registration = surfaced-for-user` and emit `notes` describing the snippet for the user.

## End condition

1. Zero compile errors in the class.
2. If test class exists, scoped tests pass via `axon4to5-isolatedtest`:
   ```
   target-name: <ClassSimpleName>
   main-sources: [<Class>.java]
   test-sources: [<Class>Test.java]    # [] if none
   extra-deps: [axon-messaging, axon-test]
   ```

## Output

```yaml
result: success | skipped | rejected | blocked | failed
target: <FQ class>
reason: <one short line>
decisions:
  path: A (Spring Boot) | B (framework Configurer)
  configurer-registration: auto-spring | added-explicit | surfaced-for-user   # Path B
files_touched:
  - <repo-relative path>
route_to: <handler recipe>      # only on rejected
notes: <free text>
```

## Reference pairs (AF4 → AF5)

Bundled in [evals/fixtures/](../evals/fixtures/):

- **Pure import-only rewrite, Spring `@Component`:** `axon4/heroes/GetDwellingByIdQueryHandler.java` ↔ `axon5/heroes/GetDwellingByIdQueryHandler.java`.
- **Dual-role class (`@QueryHandler` + `@EventHandler` on the same class):** `axon4/heroes/GetAllDwellingsQueryHandler.java` ↔ `axon5/heroes/GetAllDwellingsQueryHandler.java`.
