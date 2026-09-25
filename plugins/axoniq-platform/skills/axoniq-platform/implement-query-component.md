
# Implementing a QUERY component

A QUERY component maintains a JPA-backed read model that listens to events and exposes data over query handlers and a REST API. It does NOT emit events and is NOT event-sourced.

**Always load [implementation-base.md](implementation-base.md) first** — it has the package layout, marker-file rules, and the "no Axon 4" rule. For framework-level API details consult the **`axoniq-app-development`** plugin (install it alongside this one from the `axoniq` marketplace):

- `events/handling-projections.md` — `@EventHandler` semantics, parameter resolution (`@Timestamp`, `@MetadataValue`, `QueryUpdateEmitter`); processor types (`SubscribingEventProcessor` vs `PooledStreamingEventProcessor`) in `events/processors.md`
- `queries/query-handling.md` — `@QueryHandler`, `QueryGateway.query` / `queryMany`, subscription queries
- `foundations/annotations.md` — `@Query`, `@EventHandler`, `@QueryHandler` attribute reference
- `configuration/spring-boot.md` — auto-detection of `@Component` handlers

## Inputs

- `projectId` and `workspaceId` from `./.axoniq` at the repo root.
- `componentId` provided by [SKILL.md](SKILL.md).
- Component spec fetched via MCP: `get_component_details(projectId, componentId)` — returns `queryHandlers`, `eventHandlers`, and message references inline.
- Referenced message schemas: the message references come back in the same response; resolve full message shapes from `get_project(projectId).messages` and look them up by name. Don't read or write spec files on disk.

[SKILL.md](SKILL.md) picks the component as eligible in one of two modes:

- **Fresh implementation**: MCP component status is `APPROVED` and no `<component_pkg>/.axoniq` marker exists locally. Write all files; create the marker as the first step.
- **Extend mode**: marker exists, but the spec (re-fetched via MCP) has `queryHandlers` or `eventHandlers` the existing code doesn't reflect. Read the existing component class + entity + repository + controller. **Add** new `@EventHandler` / `@QueryHandler` methods, new entity fields (with a flagged note about migration), new controller endpoints. Don't rewrite existing files unless their spec definition changed — flag conflicts to the user first. Marker stays.

## Bean naming

All Spring beans declared by this component must have a unique name to avoid collisions across components:

```
{{uniqueBeanName}} = camelCase(componentName) + ClassName
```

Examples for component `available-bikes-view` (camelCase: `availableBikesView`):
- `availableBikesViewQueryComponent`
- `availableBikesViewEntity`
- `availableBikesViewRepository`
- `availableBikesViewController`

## Files to write

`<component_pkg>` = `{{source_directory}}/{{source_path}}/<componentId-as-snake>/`.

1. **Marker — write this FIRST** → `<component_pkg>/.axoniq` containing `{ "componentId": "<componentId>" }`. See [implementation-base.md](implementation-base.md) for the rationale. In extend mode the marker already exists — leave it alone.

2. **Queries and query results** → `{{source_directory}}/{{source_path}}/api/queries/<MessageName>{{file_extension}}`
   - One file per query and per query result.
   - Property types from the supported set only.

3. **Referenced events** — events the component listens to live in `{{source_directory}}/{{source_path}}/api/events/`. Do NOT redefine them. If a needed event class doesn't exist on disk yet (because no COMMAND component has been implemented yet that emits it), create the class there now using the spec's message definition (including `@Event(namespace = "<project-namespace>", name = "<EventName>")`); future COMMAND implementations will reuse it.

4. **JPA entity** → `<component_pkg>/<ComponentName>Entity{{file_extension}}`
   ```kotlin
   @Entity(name = "{{uniqueBeanName}}Entity")
   @Table(name = "<plural_snake>")
   data class <ComponentName>Entity(
       @Id @Column(name = "<id_col>", nullable = false)
       val id: String,
       // other columns
   )
   ```
   - Use `jakarta.persistence.*` imports.

5. **JPA repository** → `<component_pkg>/<ComponentName>Repository{{file_extension}}`
   ```kotlin
   @Repository("{{uniqueBeanName}}Repository")
   interface <ComponentName>Repository : JpaRepository<<ComponentName>Entity, <IdType>> {
       fun findByXxx(...): List<<ComponentName>Entity>  // as needed
   }
   ```

6. **Component class** → `<component_pkg>/<ComponentName>QueryComponent{{file_extension}}`
   ```kotlin
   @Component("{{uniqueBeanName}}QueryComponent")
   class <ComponentName>QueryComponent(private val repo: <ComponentName>Repository) {
       @EventHandler
       fun on(event: <Event>) { /* idempotent update */ }

       @QueryHandler
       fun handle(query: <Query>): <QueryResult> { /* read from repo */ }
   }
   ```
   - `@EventHandler` methods MUST be idempotent — events may be replayed.
   - `@QueryHandler` methods read only; never emit events or commands.
   - If a handler needs the event's recorded timestamp, take an `Instant` parameter annotated with `@Timestamp` — a plain `Instant` will fail to resolve. See [implementation-base.md](implementation-base.md#event-handler-timestamps---timestamp-instant).

7. **REST controller** → `<component_pkg>/<ComponentName>Controller{{file_extension}}`
   ```kotlin
   @RestController
   @RequestMapping("/api/<plural-kebab>")
   @Tag(name = "<ComponentName>", description = "...")
   class <ComponentName>Controller(private val queryGateway: QueryGateway) {

       @GetMapping("/...")
       @Operation(summary = "...")
       fun get(...): CompletableFuture<<QueryResult>> =
           queryGateway.query(<Query>(...), <QueryResult>::class.java)
   }
   ```
   - Use OpenAPI `@Tag`, `@Operation`, parameter `@Parameter` annotations for documentation.

## What QUERY components do NOT generate

- No `@EventSourced` state class — queries aren't event-sourced.
- No `EventAppender` — queries don't emit events.
- No exceptions in the spec sense — query handlers return data or empty results, not domain exceptions.
- No write-side AxonTestFixture tests — those are for COMMAND components only.

## Tests (required)

Write one unit test class per QUERY component at `{{source_test_directory}}/{{source_path}}/<componentId-as-snake>/<ComponentName>QueryComponentTest{{file_extension}}`. [SKILL.md](SKILL.md) only marks a component implemented once its tests pass, and an untested projection is the one that silently drifts from the spec on the next change.

Test the component class directly, without Spring and without a database: construct `<ComponentName>QueryComponent` with a repository test double (a Mockito mock, or a small map-backed fake when handlers read back what they wrote), call the `@EventHandler` methods with event payloads, then call the `@QueryHandler` methods and assert on the returned result objects.

Cover, per component:
- every `@EventHandler`: the entity it creates or updates, and that applying the same event twice leaves the same state (idempotency);
- every `@QueryHandler`: a populated result and the empty / not-found case;
- the filter the spec describes for list queries (only available bikes, only this customer's rentals, ...).

Don't use `@SpringBootTest` or `@DataJpaTest` here: the skeleton has no test database, and the Axon Server connector on the classpath would try to connect. Controller tests are optional.

## When to stop and ask

- A required event class doesn't exist anywhere and the spec doesn't fully define it — flag it.
- The query result schema clashes with an existing JPA entity.
- The component package already exists with a different `componentId` in `.axoniq`.
- Compile fails after writing files.

## Boundaries

- Don't touch other components' packages.
- Don't redefine events; reference shared events from `<base>.api.events`.
- Don't modify the per-package `.axoniq` of any component other than this one.
- Don't import from Axon Framework 4.
