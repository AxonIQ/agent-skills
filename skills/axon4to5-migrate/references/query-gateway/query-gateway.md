# Recipe: query-gateway (top-of-chain caller)

Atomic migration of ONE class dispatching queries via `QueryGateway` from outside any message handler.

> If the class injects AF4 `Configuration` and reads `queryBus()` / `queryUpdateEmitter()`, use [configuration-reads.md](configuration-reads.md).

**Hard rule — named queries.** Never wrap a dispatch in `GenericQueryMessage` to preserve a named query. The only correct AF5 migration for an AF4 named query is `@Query` on the payload class (`org.axonframework.messaging.queryhandling.annotation.Query`). If AF4 payload was a bare scalar, introduce a record and annotate it.

## Inputs

- `target` — FQ class (required)
- `target_test` — FQ test class (optional)
- `wiring` — `spring-boot` | `framework-config` (pinned)

## Preflight

1. AF5 import `org.axonframework.messaging.queryhandling.gateway.QueryGateway` present?
2. No `org.axonframework.messaging.responsetypes.*` imports?
3. No `ResponseTypes.instanceOf` / `multipleInstancesOf` / `optionalInstanceOf`?
4. No `queryGateway.scatterGather(...)` (removed in AF5; **not** a no-op — flag).
5. Subscription queries pass plain `Class<I>` / `Class<U>`?
6. No bare `.get()` / `.join()` without `.orTimeout(...)` at sync boundaries — most common diff post-recipe, real fix to apply.
7. No AF4 named-query call sites `queryGateway.query("<name>", payload, …)` — apply rewrite even when 1–6 hold.

All clean → `AskUserQuestion`: Skip / Deep verify.

## In scope

ONE class importing AF4 `QueryGateway`, class-level dep, calls `.query(...)` / `.subscriptionQuery(...)` / `.streamingQuery(...)` / `.scatterGather(...)`, NOT a message-handling component.

## FQN cheat sheet

| Element | AF4 | AF5 |
|---|---|---|
| `QueryGateway` | `org.axonframework.queryhandling.QueryGateway` | `org.axonframework.messaging.queryhandling.gateway.QueryGateway` |
| `ResponseType` / `ResponseTypes` | `org.axonframework.messaging.responsetypes.*` | **removed** — use plain `Class<R>` |
| `@Query` (new) | n/a | `org.axonframework.messaging.queryhandling.annotation.Query` |
| `SubscriptionQueryResult` | `org.axonframework.queryhandling.SubscriptionQueryResult` | **split** — `SubscriptionQueryResponse<I,U>` (gateway, payloads) / `SubscriptionQueryResponseMessages` (bus, messages); `org.axonframework.messaging.queryhandling.*` |
| `GenericQueryMessage` | `org.axonframework.queryhandling.GenericQueryMessage` | `org.axonframework.messaging.queryhandling.GenericQueryMessage` — never construct at call sites (see hard rule) |
| `MetaData` | `org.axonframework.messaging.MetaData` | `org.axonframework.messaging.core.Metadata` |

## Procedure

### Step 1 — Locate

Same filter as command-gateway: AF4 `QueryGateway` import AND no handler annotations.

### Step 2 — Update import

`org.axonframework.queryhandling.QueryGateway` → `org.axonframework.messaging.queryhandling.gateway.QueryGateway`.

- **Path A (Spring Boot):** auto-bean from starter; injection unchanged.
- **Path B (framework Configurer):** `config.getComponent(QueryGateway.class)`.

### Step 3 — Named queries (`@Query`)

If AF4 call is `queryGateway.query("queryName", payload, ResponseType…)`:

1. Change call site to typed overload (no name, no `ResponseType`):
   ```java
   queryGateway.query(payload, ResponseClass.class);
   ```
2. Move the name to the payload via `@Query`. Match AF4 string **exactly** — `@Query.name()` becomes the `QualifiedName.localName()` AF5 routes by:
   ```java
   import org.axonframework.messaging.queryhandling.annotation.Query;

   @Query(name = "queryName")
   public record GetXById(String id) { }
   ```
   Set `name` explicitly — AF4 name and class name almost never agree.
3. Bare scalar payload (`String`, enum, …) → introduce a record wrapper, annotate it.
4. **Coupled handler-side edit** (only when payload class changes): update the matching `@QueryHandler(queryName = "<name>")` parameter type to accept the new record. Inseparable from the call-site change:
   ```java
   // before
   @QueryHandler(queryName = "getStatus") PaymentStatus getStatus(String paymentId)
   // after
   @QueryHandler(queryName = "getStatus") PaymentStatus getStatus(GetPaymentStatusQuery query)
   ```

### Step 4 — Remove `ResponseType` wrappers

| AF4 | AF5 | Returns |
|---|---|---|
| `query(payload, R.class)` (already `Class` overload) | same — import only | `CompletableFuture<R>` |
| `query(payload, ResponseTypes.instanceOf(R.class))` | `query(payload, R.class)` | `CompletableFuture<R>` |
| `query(payload, ResponseTypes.optionalInstanceOf(R.class))` | `query(payload, R.class)` — future resolves `null` if absent | `CompletableFuture<R>` (nullable) |
| `query(payload, ResponseTypes.multipleInstancesOf(R.class))` | `queryMany(payload, R.class)` | `CompletableFuture<List<R>>` |
| `query("name", payload, ResponseTypes.instanceOf(R.class))` | `query(payload, R.class)` + `@Query(name="name")` on payload | `CompletableFuture<R>` |
| `query("name", payload, ResponseTypes.multipleInstancesOf(R.class))` | `queryMany(payload, R.class)` + `@Query(name="name")` on payload | `CompletableFuture<List<R>>` |
| `streamingQuery(payload, R.class)` | same — import only | `Publisher<R>` |
| `scatterGather(...)` | **REMOVED** — flag user; no drop-in | — |

- `query(...)` is **always single-response** in AF5; multi-response → `queryMany(...)`.
- `ResponseType` / `ResponseTypes` SPI gone — drop wrappers and static imports.
- Custom `ResponseType` subclass → flag for user; per-callsite plan needed.

### Step 5 — Subscription queries

AF4 `SubscriptionQueryResult` is **split** in AF5. Top-of-chain callers see the gateway flavour (`SubscriptionQueryResponse<I, U>`). `initialResult()` is `Flux` in AF5 (not `Mono`) because AF5 supports 0/1/N initial results uniformly.

```java
SubscriptionQueryResponse<R, U> resp = queryGateway.subscriptionQuery(payload, R.class, U.class);
Flux<R> initial = resp.initialResult();   // Flux, not Mono
Flux<U> updates = resp.updates();
```

If AF4 caller assumed single initial result, collapse with `.next()` / `.singleOrEmpty()`. Call `resp.cancel()` when done (project-specific).

### Step 6 — Scatter-gather

`queryGateway.scatterGather(payload, …)` is REMOVED in AF5. No drop-in replacement. Flag to user; redesign (single broadcast handler aggregating internally, or domain-specific).

### Step 7 — Adapt surrounding method's return type

- **Spring MVC controller** → return `CompletableFuture<R>` directly; Spring serves async out of the box.
- **Reactive (Mono/Flux)** → `Mono.fromFuture(future)` for `query`, `Flux.from(publisher)` for `streamingQuery`. Reactor extension survives at `extension.reactor`.
- **Blocking caller** (CLI runner, integration test) → `future.orTimeout(<d>, <u>).join()`. Never bare `.join()` / `.get()`.
- **Synchronous framework callback** (MCP resource handler, `@KafkaListener`, `@JmsListener`, Camel route step) — same blocking pattern. Pick timeout consciously (often 30s default).

### Step 8 — Verify nothing else

- Stale AF4 `org.axonframework.queryhandling.*` imports → remove.
- `ResponseTypes` static imports → drop when unused.
- `QueryExecutionException` → update FQN if present.

## End condition

1. Zero compile errors.
2. No `ResponseType` / `ResponseTypes.*` wrappers remain.
3. Return type flows correctly.
4. Compile-only via `axon4to5-isolatedtest`:
   ```
   target-name: <ClassSimpleName>
   main-sources: [<Class>.java]
   test-sources: []
   extra-deps: [axon-messaging]
   ```

## Output

```yaml
result: success | skipped | rejected | needs-decision | blocked | failed
target: <FQ class>
reason: <one short line>
decisions:
  path: A (Spring Boot) | B (framework Configurer)
  query-shape: single | stream | subscription
caller-expects: { commit: <bool>, next: <…> }
notes: <…>
```

## Out of scope

- Handler-resident dispatch → event-processor recipe.
- `scatterGather(...)` removal → flag user; no drop-in.
- `@QueryHandler` classes → query-handler recipe (except the coupled edit in Step 3.4).
