---
id: query-gateway
title: Query Gateway
description: Migrates a single top-of-chain class dispatching queries via QueryGateway (REST controller, scheduler, MCP callback) to Axon Framework 5.
order: 4
argument-hint: $SOURCE
---

# Query Gateway

> Top-of-chain class (no active `ProcessingContext`) that holds a `QueryGateway` field and dispatches queries. Covers Spring `@RestController`, `@Scheduled`, sync framework callbacks (MCP, Kafka, Camel), and CLI runners.
>
> **Hard rule — named queries**: never construct `GenericQueryMessage` at dispatch sites. Named queries in AF4 (`query("name", payload, R)`) must move the name onto the payload class via `@Query(name = "…")` (`org.axonframework.messaging.queryhandling.annotation.Query`). If AF4 payload was a bare scalar, introduce a record and annotate it.

## Source

- `$SOURCE` (required) — FQN, file path, or simple class name of the top-of-chain class that injects `QueryGateway` and is NOT a message-handling component.

## Scope

- `$SOURCE` class itself.
- Surrounding method return types that need adapting (e.g., blocking `.get()` → `.orTimeout(...).join()`).
- Payload class(es) that need a new `@Query` annotation (only when `$SOURCE` uses named-query dispatch). Handler-side parameter type update is also in scope when payload shape changes (see Toolbox Step 2d).

Scope grows during FLOW.md Research; never shrinks. External helpers returning stale `ResponseType` objects are NOT in scope — flag as follow-up.

## Applicable

Surface check on `$SOURCE` before Research. Cheap reads only.

Decision rule (top-down; first match wins):

1. **Saga** — class annotated `@Saga` OR any method annotated `@SagaEventHandler` / `@StartSaga` / `@EndSaga`. → **Rejected** (route to saga recipe).
2. **Handler class** — any method annotated `@EventHandler` / `@CommandHandler` / `@QueryHandler` / `@SagaEventHandler` / `@MessageHandlerInterceptor`. → **Rejected** with NOTES routing to the appropriate handler recipe.
3. **QueryGateway caller, AF4 shape** — imports `org.axonframework.queryhandling.QueryGateway`. → **continue** to Research.
4. **QueryGateway caller, partially migrated** — imports `org.axonframework.messaging.queryhandling.gateway.QueryGateway`. → **continue** to Research; the Success Criteria pre-Apply check decides idempotent-Success vs. continue.
5. **None of the above** — no `QueryGateway` import. → **Rejected** with NOTES naming the failed predicate.

## Blocker

**Emission model — all blockers at once.** Scans during Research (FLOW.md S3) before the Plan-Apply loop. Emits one Blocker result if any fire.

### B1 — `scatterGather(...)` call

`queryGateway.scatterGather(payload, …)` is **removed in AF5 with no drop-in replacement**. The recipe cannot migrate this call automatically. Detect: `grep -n 'queryGateway\.scatterGather(' <class file>`.

Recipe-specific Option alongside the three defaults:
- `surface-and-defer` — recipe exits; user redesigns the scatter-gather flow (e.g., single broadcast query handler aggregating internally).

### B2 — Custom `ResponseType` subclass

Project defines a class implementing `org.axonframework.messaging.responsetypes.ResponseType<R>`. AF5 removed this SPI; per-callsite plan is required. Detect: `grep -rn 'implements ResponseType'`. Flag for user; recipe cannot auto-migrate.

### Unmet project prerequisites

- Project does not compile pre-recipe → Blocker `prerequisite-not-compiling`.

## Out of Scope

- Handler-resident dispatch (`queryGateway.query(...)` inside `@EventHandler` / `@QueryHandler` bodies) — event-processor recipe owns that.
- `@QueryHandler` classes (the receiving side) — query-handler recipe, except the coupled parameter-type edit in Step 2d.
- `scatterGather(...)` redesign — flag for user; no drop-in.
- External helper classes returning AF4 `ResponseType` objects — flag as follow-up.
- Adding tests when none exist — surface as Learning.
- Logging changes, package renames, formatting.

## References

- [messages.adoc](../../docs/paths/messages.adoc) — *apply-condition:* always. Covers `QueryGateway` package move, `@Query`, `MessageType`, `ResponseType` removal.
- [configuration.adoc](../../docs/paths/configuration.adoc) — *apply-condition:* `configuration=native` AND class obtains `QueryGateway` via `AxonConfiguration.getComponent(QueryGateway.class)`.

## Success Criteria

Extends DEFAULT.md baseline. DEFAULT's three baseline criteria stay in force. Recipe adds:

### Recipe-specific structural invariants

For every file in `# Scope`:

1. **No AF4 `QueryGateway` import** — `org.axonframework.queryhandling.QueryGateway` must not appear.
2. **No `ResponseType` / `ResponseTypes.*` wrappers** — no `ResponseTypes.instanceOf`, `multipleInstancesOf`, `optionalInstanceOf`, no `import org.axonframework.messaging.responsetypes.*`.
3. **No named-query string dispatch** — no `queryGateway.query("…"` / `queryGateway.queryMany("…"` (3-arg, first arg `String`) call sites remain.
4. **No bare blocking without timeout** — no `.get()` / `.join()` without preceding `.orTimeout(…)` at synchronous boundaries.
5. **No stale AF4 queryhandling imports** — `org.axonframework.queryhandling.*` (except where replaced by AF5 equivalents).

Aggregation rule: **all match (AND)**.

### Verification

Use `axon4to5-isolatedtest` per DEFAULT.md § Verification. `target-name`: simple class name of `$SOURCE`. `main-sources`: `[$SOURCE file]`. `test-sources`: `[]` (compile-only default) unless an integration test exists.

`extra-deps` baseline: `org.axonframework:axon-messaging`. Add `org.axonframework.extensions.spring:axon-spring-boot-starter` for `configuration=spring`.

## Toolbox

### Step 1 — Import swap

*Apply-condition:* always.

Replace AF4 import:
```
import org.axonframework.queryhandling.QueryGateway;
```
with AF5 import:
```
import org.axonframework.messaging.queryhandling.gateway.QueryGateway;
```

Field type, constructor parameter, and variable name unchanged — only the package moves.

**How gateway is obtained (no code change):**
- **Path A (Spring Boot):** AF5 starter auto-creates the bean. Constructor / `@Autowired` unchanged.
- **Path B (native Configurer):** obtain from live `AxonConfiguration`:
  ```java
  var config       = configurer.start();
  var queryGateway = config.getComponent(QueryGateway.class);
  ```

Also remove stale `org.axonframework.messaging.responsetypes.*` imports at this step if `ResponseTypes` wrappers are being stripped.

### Step 2 — Named queries → `@Query` annotation

*Apply-condition:* `$SOURCE` has any `queryGateway.query("name", payload, …)` or `queryGateway.queryMany("name", payload, …)` call (3-arg form with first arg a `String`).

a. Change call site to typed overload — no string name, no `ResponseType` wrapper:
   ```java
   queryGateway.query(payload, ResponseClass.class);
   // or, for multipleInstancesOf:
   queryGateway.queryMany(payload, ResponseClass.class);
   ```
b. Annotate the payload class with `@Query(name = "<af4 name>")`. Match the AF4 string **exactly** — `@Query.name()` becomes the `QualifiedName.localName()` AF5 routes by:
   ```java
   import org.axonframework.messaging.queryhandling.annotation.Query;

   @Query(name = "queryName")
   public record GetXById(String id) { }
   ```
   **Never** rely on the default (simple class name) — AF4 name and class name almost never agree.
c. **Bare scalar payload** (`String`, enum, `Long`, …) → introduce a new `@Query`-annotated record; field name preserves the original semantics.
d. **Coupled handler-side edit (in scope here, only when payload class changes).** When payload was a bare scalar and a new record is introduced, update the matching `@QueryHandler(queryName = "…")` parameter type to accept the new record. This is the only handler-side edit this recipe touches:
   ```java
   // before
   @QueryHandler(queryName = "getStatus") PaymentStatus getStatus(String paymentId)
   // after
   @QueryHandler(queryName = "getStatus") PaymentStatus getStatus(GetPaymentStatusQuery query)
   ```

### Step 3 — Remove `ResponseType` wrappers

*Apply-condition:* `$SOURCE` uses `ResponseTypes.*` wrappers.

| AF4 | AF5 | Returns |
|---|---|---|
| `query(payload, R.class)` (already `Class` overload) | unchanged — import-only | `CompletableFuture<R>` |
| `query(payload, ResponseTypes.instanceOf(R.class))` | `query(payload, R.class)` | `CompletableFuture<R>` |
| `query(payload, ResponseTypes.optionalInstanceOf(R.class))` | `query(payload, R.class)` — future resolves `null` if absent | `CompletableFuture<R>` (nullable) |
| `query(payload, ResponseTypes.multipleInstancesOf(R.class))` | `queryMany(payload, R.class)` | `CompletableFuture<List<R>>` |
| `query("name", payload, ResponseTypes.instanceOf(R.class))` | `query(payload, R.class)` + `@Query(name="name")` on payload | `CompletableFuture<R>` |
| `query("name", payload, ResponseTypes.multipleInstancesOf(R.class))` | `queryMany(payload, R.class)` + `@Query(name="name")` on payload | `CompletableFuture<List<R>>` |
| `streamingQuery(payload, R.class)` | unchanged — import-only | `Publisher<R>` |
| `scatterGather(...)` | **REMOVED** → Blocker B1 | — |

Notes:
- `query(...)` is **always single-response** in AF5. Multi-response → `queryMany(...)`.
- `ResponseType` / `ResponseTypes` SPI **gone** — drop wrappers and `import static org.axonframework.messaging.responsetypes.ResponseTypes.*;`.
- Custom `ResponseType` subclass in project → Blocker B2.

### Step 4 — Subscription queries

*Apply-condition:* `$SOURCE` uses `queryGateway.subscriptionQuery(...)`.

AF4 `SubscriptionQueryResult` is split in AF5. Top-of-chain callers see the gateway flavour: `SubscriptionQueryResponse<I, U>` (FQN: `org.axonframework.messaging.queryhandling.*`). `initialResult()` is `Flux` in AF5 (not `Mono`) — AF5 supports 0/1/N initial results uniformly.

```java
SubscriptionQueryResponse<R, U> resp = queryGateway.subscriptionQuery(payload, R.class, U.class);
Flux<R> initial = resp.initialResult();   // Flux, not Mono in AF5
Flux<U> updates = resp.updates();
```

If AF4 caller assumed single initial result, collapse with `.next()` / `.singleOrEmpty()`. Call `resp.cancel()` when done.

### Step 5 — Adapt return type and blocking calls

*Apply-condition:* always; shape depends on the calling context.

**Decision rule (top-down; first match wins):**

1. **Method can return `CompletableFuture<R>` (preferred)** — change return type, return the future directly, remove the try-catch block. This applies to Spring MVC controllers, plain service methods, reactive adapters, and any other callers not bound to a sync contract.
   ```java
   // before — blocking
   DwellingReadModel getDwelling(String id) {
       return queryGateway.query(new GetDwellingById(id), DwellingReadModel.class).get();
   }
   // after — async (preferred)
   CompletableFuture<DwellingReadModel> getDwelling(String id) {
       return queryGateway.query(new GetDwellingById(id), DwellingReadModel.class);
   }
   ```
   Add `import java.util.concurrent.CompletableFuture;` when newly introduced.

2. **Method signature is truly constrained to sync** (implements a sync interface, `@KafkaListener`, `@JmsListener`, MCP `SyncResourceSpecification` lambda, Camel route step, `CommandLineRunner`, `@Scheduled void`, `main(...)`) — add `.orTimeout(<d>, <u>).join()`. **Never** bare `.join()` / `.get()` without a preceding `.orTimeout(…)`. Default timeout 30s; adjust when the framework has a shorter request budget.
   ```java
   return queryGateway.query(new GetDwellingById(id), DwellingReadModel.class)
           .orTimeout(30, TimeUnit.SECONDS)
           .join();
   ```
   The existing `catch (Exception e)` still catches `CompletionException` (unchecked). Add `import java.util.concurrent.TimeUnit;`.

- **Spring MVC controller** — already in path 1: return `CompletableFuture<R>` directly. Spring serves async out of the box; no thread is blocked.
- **Reactive return** (`Mono` / `Flux`) — `Mono.fromFuture(queryGateway.query(…, R.class))` for single; `Flux.from(queryGateway.streamingQuery(…, R.class))` for streaming.

### Step 6 — Clean up stale imports

*Apply-condition:* always.

- Remove leftover `org.axonframework.queryhandling.*` AF4 imports.
- Remove `import static org.axonframework.messaging.responsetypes.ResponseTypes.*;` when no longer referenced.
- `QueryExecutionException` FQN moved — update if present.
- Added `CompletableFuture`? Confirm `import java.util.concurrent.CompletableFuture;` present.
- Added `.orTimeout(...).join()`? Confirm `import java.util.concurrent.TimeUnit;` present.

## Use cases

- [01-rest-controller-import-only.md](use-cases/01-rest-controller-import-only.md) — *apply-condition:* `$SOURCE` is a Spring `@RestController` AND already uses `Class<R>` overload of `query(...)` (no `ResponseType` wrapper, no named query string).
- [02-blocking-get-to-async.md](use-cases/02-blocking-get-to-async.md) — *apply-condition:* `$SOURCE` has bare `.get()` or `.join()` without `.orTimeout(...)` on a `queryGateway.query(...)` result. Path A (preferred): upgrade method return type to `CompletableFuture<R>`. Path B (fallback): add `.orTimeout().join()` when method signature is sync-constrained.
- [03-response-type-wrapper-removal.md](use-cases/03-response-type-wrapper-removal.md) — *apply-condition:* `$SOURCE` uses `ResponseTypes.instanceOf(...)` / `multipleInstancesOf(...)` / `optionalInstanceOf(...)` wrappers.
- [04-named-query-query-annotation.md](use-cases/04-named-query-query-annotation.md) — *apply-condition:* `$SOURCE` has `queryGateway.query("name", payload, …)` or `queryGateway.queryMany("name", payload, …)` call (3-arg named form).
- [05-rejected-handler-class.md](use-cases/05-rejected-handler-class.md) — *apply-condition:* `$SOURCE` has any method annotated `@EventHandler` / `@QueryHandler` (predicate 2 fires).

## Gotchas

- **`ResponseType` / `ResponseTypes` SPI gone** — most common compile error post-import-swap. Every `ResponseTypes.instanceOf(R.class)` wrapper must become plain `R.class`. `multipleInstancesOf` means `queryMany`.
- **Named-query string overload removed** — `query("name", payload, R)` does not exist in AF5. Never wrap in `GenericQueryMessage` — put the name on the payload class via `@Query`.
- **`@Query` name must match AF4 string exactly** — AF5 routes by `@Query.name()` as `QualifiedName.localName()`. Default is the simple class name, which almost never matches the AF4 string. Set `name` explicitly.
- **`query(...)` is always single-response in AF5** — multi-response callers that used `ResponseTypes.multipleInstancesOf` must switch to `queryMany(...)`.
- **`initialResult()` is `Flux` not `Mono` in AF5** — callers that assumed a single initial result via `.block()` / `.get()` on the `Mono` must collapse with `.next()` / `.singleOrEmpty()`.
- **Bare `.get()` / `.join()` — prefer async upgrade first** — if the method can return `CompletableFuture<R>`, change the return type and return the future directly (no blocking at all). Only use `.orTimeout(<d>, <u>).join()` when the method signature is truly constrained to a sync return (implements sync interface, `@KafkaListener`, MCP sync callback, etc.).
- **`scatterGather(...)` removed with no drop-in** — this is always Blocker B1; do not attempt partial migration.
- **`QueryGateway` stays `QueryGateway`** — never swap to any dispatcher variant inside this recipe.

## Result

Inherits DEFAULT.md baseline.

### Success

Say **"return SUCCESS"**, then emit result block. `Recipe:` field is `axon4to5-query-gateway`. Include as Learning: any flagged follow-ups (stale `ResponseType` helper, `scatterGather` blocked and deferred).

### Blocker

Say **"return BLOCKER"**, then emit result block. `Recipe:` field is `axon4to5-query-gateway`. NOTES name each detected blocker.

Example (B1 — scatterGather):

```
return BLOCKER

> **Result:** 🚧 Blocker
> **Source:** `com.example.RecommendationController`
> **Recipe:** axon4to5-query-gateway
>
> **Notes:** 1 blocker detected. `RecommendationController.java:34` calls `queryGateway.scatterGather(...)` — removed in AF5 with no drop-in replacement. User must redesign (e.g., single broadcast query handler aggregating internally).
>
> **Options:**
>
> _For B1 (scatterGather removed):_
> - [ ] **surface-and-defer** — recipe exits; user redesigns the scatter-gather flow.
> - [ ] **skip** — keep `$SOURCE` in current partial state; queue moves on.
> - [ ] **revert** — undo recipe edits; restore pre-recipe state.
> - [ ] **solve-manually** — pause; caller redesigns, then re-invokes.
```

### Rejected

Say **"return REJECTED"**, then emit result block. `Recipe:` field is `axon4to5-query-gateway`. NOTES name the failed predicate and route to the appropriate sister recipe.

Example:

```
return REJECTED

> **Result:** ⏭️ Rejected
> **Source:** `com.example.DwellingQueryHandler`
> **Recipe:** axon4to5-query-gateway
>
> **Notes:** Applicable predicate 2 failed — class has `@QueryHandler` methods. This is a query-handling component, not a top-of-chain caller. Route to the query-handler recipe.
```

### Failure

Say **"return FAILURE"**, then emit result block. NOTES: failing Success Criteria + last error verbatim. LEARNINGS nearly always present.
