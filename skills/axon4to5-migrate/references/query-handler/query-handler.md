# Recipe: `@QueryHandler` class

Atomic migration of ONE class that handles queries via methods annotated `@QueryHandler` — typically Spring `@Component` / `@Service` projection or read-model query handler.

## Canonical reference

- [../../docs/paths/messages.adoc](../../docs/paths/messages.adoc) — query annotation moves.
- [../../docs/paths/index.adoc](../../docs/paths/index.adoc) §"Import and package changes" — `@QueryHandler` FQN move.
- [../../docs/paths/interceptors.adoc](../../docs/paths/interceptors.adoc) — when class also carries an interceptor.

Recipe holds the import-only mechanical edit and `queryName` preservation.

## Goal

In the simple case, **import-only** change. Method bodies, parameter lists, return types, the `queryName` attribute, and Spring stereotypes are preserved as-is.

- `@QueryHandler` import: `org.axonframework.queryhandling.QueryHandler` → `org.axonframework.messaging.queryhandling.annotation.QueryHandler`.
- Any sibling AF4 query-handling import (`org.axonframework.queryhandling.*`) on the same class moves under `org.axonframework.messaging.queryhandling.*`.

## Inputs

- target: FQ class name of the `@QueryHandler` host (required)
- target_test: FQ test class name (optional)
- wiring: "spring-boot" | "framework-config" (required, supplied by orchestrator from progress.md Pinned-decisions)

## End condition

1. Zero compile errors in the class itself.
2. If the class has a test, scoped tests pass.

## Output

Emit exactly one fenced ```yaml block per the six-variant Output contract
([../output-contract.md](../output-contract.md)). Schema below shows the
`success` shape with all query-handler `decisions` keys; for the other
five variants copy the matching example from `output-contract.md`.

```yaml
result: success | skipped | rejected | needs-decision | blocked | failed
target: <FQ class>
reason: <one short line — required for every variant except success>
decisions:
  path: <A (Spring Boot) | B (framework Configurer)>     # taken from inputs.wiring
  configurer-registration: <auto-spring | added-explicit | surfaced-for-user>   # Path B only
caller-expects:
  commit: <true | false>
  next: <proceed | ask-user | record-and-skip | halt | route-to:<recipe>>
notes: <optional free text — verbatim AskUserQuestion options for needs-decision>
```

## Preflight

1. `@QueryHandler` already imported from AF5 location?
2. Compile clean?
3. If yes → STOP. `AskUserQuestion`: Skip / Deep verify.

> A class **without an explicit target** is NOT picked autonomously if its only query-handling import is already AF5 — there's no work, autonomous run produces no-op. With explicit target, no-op is still legitimate (recipe just verifies nothing was missed).

## In scope

ONE class — Spring `@Component` / `@Service` (Path A) **or** a plain Java/Kotlin class registered via the framework `Configurer` (Path B) — with at least one method annotated `@QueryHandler` from AF4 location `org.axonframework.queryhandling.QueryHandler`, AND **NOT** also handling other message types via AF4 imports.

## Out of scope

- Class also carries AF4 `@CommandHandler` / `@EventHandler` — run their dedicated recipes first/instead.
  - Exception: if every other annotation is *already* on AF5 import (recipe-pre-migrated), there's nothing for sibling recipes to do; this recipe finishes the unit.

## FQN cheat sheet

| Element | AF4 | AF5 |
|---|---|---|
| `@QueryHandler` | `org.axonframework.queryhandling.QueryHandler` | `org.axonframework.messaging.queryhandling.annotation.QueryHandler` |
| Query-handling core pkg | `org.axonframework.queryhandling` | `org.axonframework.messaging.queryhandling` |
| `QueryExecutionException` | `org.axonframework.queryhandling.QueryExecutionException` | `org.axonframework.messaging.queryhandling.QueryExecutionException` |
| `MetaData` param type | `org.axonframework.messaging.MetaData` | `org.axonframework.messaging.core.Metadata` |
| `@MetaDataValue` param annot | `org.axonframework.messaging.annotation.MetaDataValue` | `org.axonframework.messaging.core.annotation.MetadataValue` |

Note rename: `MetaData` → `Metadata`, `@MetaDataValue` → `@MetadataValue` (capital `D` dropped).

## Procedure

### 1. Locate

If user named target, use it (even if already on AF5 — recipe will verify and close as no-op).

Otherwise:

```bash
grep -RlnE 'org\.axonframework\.queryhandling\.QueryHandler' \
     --include='*.java' --include='*.kt' <target>/src
```

### 2. Update import

`org.axonframework.queryhandling.QueryHandler` → `org.axonframework.messaging.queryhandling.annotation.QueryHandler`.

### 3. Update sibling AF4 query-handling imports

Move any other `org.axonframework.queryhandling.*` import on this class under `org.axonframework.messaging.queryhandling.*` matching the AF5 module reorganisation.

### 4. Preserve everything else

- Method bodies, parameter lists, return types — keep as-is.
- `queryName` attribute on `@QueryHandler` — keep as-is (same `queryName()` member in AF5).
- Return type / `ResponseType` — preserved; AF5 keeps the same first-parameter-is-payload contract.
- Spring stereotypes (`@Component`, `@Service`, `@RestController`) — keep as-is.
- Query payload type and its annotations — keep as-is.

### 5. Parameter resolution sweep

Parameter resolvers in AF5 still cover: `Metadata`, `@MetadataValue` params, the full `Message`, and the active `ProcessingContext` (AF5 replacement for AF4 `UnitOfWork` param).

- `MetaData` parameter type → rewrite import to `org.axonframework.messaging.core.Metadata` (and rename type ref).
- `@MetaDataValue("k") X x` parameter → rewrite annotation import to `org.axonframework.messaging.core.annotation.MetadataValue` and rename to `@MetadataValue`.
- `UnitOfWork` parameter → out of scope (flag for user — `ProcessingContext` migration is separate).

### 6. Verify nothing else

- `QueryExecutionException` try/catch — update FQN if present.
- Stale AF4 `org.axonframework.queryhandling.*` imports — remove.
- `QueryUpdateEmitter` (subscription-query) usage on the class — out of scope, flag for user.

### Path A — Spring Boot

Use when `inputs.wiring == "spring-boot"`. The class is a Spring stereotype (`@Component` / `@Service`); `MessageHandlerLookup` discovers the `@QueryHandler` methods at startup. No registration code required — Steps 2–6 are sufficient.

### Path B — framework Configurer

Use when `inputs.wiring == "framework-config"`. The class is a plain Java/Kotlin class registered explicitly via the framework `Configurer`.

AF4 typical:
```java
configurer.registerQueryHandler(c -> new CourseStatsQueryHandler(repository));
```

AF5 canonical — build a `QueryHandlingModule`, then register it on the configurer:

```java
import org.axonframework.messaging.queryhandling.configuration.QueryHandlingModule;

QueryHandlingModule getCourseStatsByIdHandler = QueryHandlingModule
        .named("get-course-stats-by-id")
        .queryHandlers()
        .autodetectedQueryHandlingComponent(
                cfg -> new CourseStatsQueryHandler(cfg.getComponent(CourseStatsRepository.class)))
        .build();

configurer.registerQueryHandlingModule(getCourseStatsByIdHandler);
```

Or inline (the registration method also accepts a `ModuleBuilder<QueryHandlingModule>` — `.build()` becomes optional):

```java
configurer.registerQueryHandlingModule(
        QueryHandlingModule.named("get-course-stats-by-id")
                .queryHandlers()
                .autodetectedQueryHandlingComponent(
                        cfg -> new CourseStatsQueryHandler(cfg.getComponent(CourseStatsRepository.class))));
```

`autodetectedQueryHandlingComponent` scans the supplied instance for `@QueryHandler` methods (the AF5 import set by Step 2) and registers each one. The module name (`"get-course-stats-by-id"` above) is local — pick something descriptive; it does NOT need to match anything else.

Dependencies that the handler needs (repositories, services) are pulled from the configuration via `cfg.getComponent(<DepType>.class)` — register those upstream in the bootstrap with `componentRegistry(cr -> cr.registerComponent(<DepType>.class, c -> ...))`.

If the project's existing Configurer chain already registers the AF4 form, replace it in place. If not, add the new registration to the bootstrap file. If you cannot locate the bootstrap file, set `decisions.configurer-registration = surfaced-for-user` and emit Output `notes` describing the snippet the user must add.

## Verify (against End condition)

Invoke the external `axon4to5-isolatedtest` skill (see [../verification.md](../verification.md)):

```
Skill: axon4to5-isolatedtest
Inputs:
  target-name: <ClassSimpleName>
  build-file: <target>/pom.xml | <target>/build.gradle(.kts)
  main-sources:
    - src/main/java/<…>/<Class>.java
  test-sources:
    - src/test/java/<…>/<Class>Test.java        # omit (pass []) if no test class
  extra-deps:
    - org.axonframework:axon-messaging:${axon5.version}
    - org.axonframework:axon-test:${axon5.version}        # only when test-sources present
  cleanup: false                                 # true on the recipe's last successful run
```

## Examples

See [examples/](examples/).
