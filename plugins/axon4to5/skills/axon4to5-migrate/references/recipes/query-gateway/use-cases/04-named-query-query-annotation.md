# 04 — Named query: string dispatch → `@Query`-annotated payload class

**Why this case is interesting:** AF4's named-query overload `query("name", payload, ResponseType)` is removed in AF5. The correct migration is NOT to construct `GenericQueryMessage` — it is to move the name onto the payload class via `@Query(name = "…")`. When payload was a bare scalar, a new record must be introduced, which also requires a coupled handler-side parameter-type change.

**Apply-condition:** `$SOURCE` has `queryGateway.query("name", payload, …)` or `queryGateway.queryMany("name", payload, …)` calls.

## Two sub-cases

### A — Payload class already exists (annotation-only)

Payload classes (`FindOneBike`, `FindAllBikes`) already exist as dedicated records. Only `@Query` annotation added; handler signatures unchanged.

**Before (AF4 dispatch):**
```java
import org.axonframework.messaging.responsetypes.ResponseTypes;
import org.axonframework.queryhandling.QueryGateway;

@GetMapping("/bikes")
public CompletableFuture<List<BikeStatus>> findAll() {
    return queryGateway.query("findAll", new FindAllBikes(), ResponseTypes.multipleInstancesOf(BikeStatus.class));
}

@GetMapping("/bikes/{bikeId}")
public CompletableFuture<BikeStatus> findOne(@PathVariable String bikeId) {
    return queryGateway.query("findOne", new FindOneBike(bikeId), BikeStatus.class);
}
```

**Before (payload classes):**
```java
public record FindAllBikes() {}
public record FindOneBike(String bikeId) {}
```

**After (AF5 dispatch):**
```java
import org.axonframework.messaging.queryhandling.gateway.QueryGateway;

@GetMapping("/bikes")
public CompletableFuture<List<BikeStatus>> findAll() {
    return queryGateway.queryMany(new FindAllBikes(), BikeStatus.class);
}

@GetMapping("/bikes/{bikeId}")
public CompletableFuture<BikeStatus> findOne(@PathVariable String bikeId) {
    return queryGateway.query(new FindOneBike(bikeId), BikeStatus.class);
}
```

**After (payload classes):**
```java
import org.axonframework.messaging.queryhandling.annotation.Query;

@Query(name = "findAll")
public record FindAllBikes() {}

@Query(name = "findOne")
public record FindOneBike(String bikeId) {}
```

Handler-side `@QueryHandler(queryName = "findAll")` stays unchanged — routing matches via `@Query(name = "findAll")`.

### B — Bare scalar payload (introduce record + handler edit)

**Before (AF4):**
```java
// dispatch
queryGateway.query("getStatus", paymentId, PaymentStatus.class)

// handler
@QueryHandler(queryName = "getStatus")
public PaymentStatus getStatus(String paymentId) { ... }
```

**After (AF5):**
```java
// new payload record
import org.axonframework.messaging.queryhandling.annotation.Query;

@Query(name = "getStatus")
public record GetPaymentStatusQuery(String paymentId) {}

// dispatch
queryGateway.query(new GetPaymentStatusQuery(paymentId), PaymentStatus.class)

// handler (coupled edit — in scope)
@QueryHandler(queryName = "getStatus")
public PaymentStatus getStatus(GetPaymentStatusQuery query) {
    return ... query.paymentId() ...;
}
```

## Caveats

- **`@Query.name()` must match AF4 string exactly.** The default is the simple class name; AF4 names almost never match. Always set `name` explicitly.
- **`queryMany` for `multipleInstancesOf`.** The named-form `query("findAll", ...)` with `multipleInstancesOf` becomes `queryMany(new FindAllBikes(), R.class)`.
- **Never construct `GenericQueryMessage` at dispatch sites** to "preserve" the name. This scatters routing keys across dispatch sites instead of centralising them on the payload class.
- **Handler-side edit is in scope only when payload class changes** (scalar → record). When payload was already a dedicated class, only the `@Query` annotation is added — handlers unchanged.
