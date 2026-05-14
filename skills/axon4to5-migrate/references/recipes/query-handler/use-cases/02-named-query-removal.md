# 02 — Named query removal: queryName attribute → payload record

**Why this case is interesting:** AF4 used string-based `queryName` routing (`@QueryHandler(queryName = "findAll")`). AF5 routes exclusively by the first method parameter type — the payload class IS the routing key. Every handler with `queryName` must receive a dedicated payload record, and every bare-param or no-param handler signature must be updated.

**Apply-condition:** `$SOURCE` has any `@QueryHandler(queryName = "…")`.

---

## Before (AF4) — from bike-rental-extended

```java
package io.axoniq.demo.bikerental.rental.query;

import org.axonframework.queryhandling.QueryHandler;
import org.springframework.stereotype.Component;

@Component
public class RentalBikeQueryProjection {

    private final BikeStatusRepository bikeStatusRepository;

    public RentalBikeQueryProjection(BikeStatusRepository bikeStatusRepository) {
        this.bikeStatusRepository = bikeStatusRepository;
    }

    @QueryHandler(queryName = "findAll")
    public Iterable<BikeStatus> findAll() {
        return bikeStatusRepository.findAll();
    }

    @QueryHandler(queryName = "findAvailable")
    public Iterable<BikeStatus> findAvailable(String bikeType) {
        return bikeStatusRepository.findAllByBikeTypeAndStatus(bikeType, RentalStatus.AVAILABLE);
    }

    @QueryHandler(queryName = "findOne")
    public BikeStatus findOne(String bikeId) {
        return bikeStatusRepository.findById(bikeId).orElse(null);
    }
}
```

## After (AF5)

```java
package io.axoniq.demo.bikerental.rental.query;

import org.axonframework.messaging.queryhandling.annotation.Query;
import org.axonframework.messaging.queryhandling.annotation.QueryHandler;
import org.springframework.stereotype.Component;

@Component
public class RentalBikeQueryProjection {

    private final BikeStatusRepository bikeStatusRepository;

    public RentalBikeQueryProjection(BikeStatusRepository bikeStatusRepository) {
        this.bikeStatusRepository = bikeStatusRepository;
    }

    @QueryHandler
    public Iterable<BikeStatus> findAll(FindAllQuery ignored) {
        return bikeStatusRepository.findAll();
    }

    @QueryHandler
    public Iterable<BikeStatus> findAvailable(FindAvailableQuery query) {
        return bikeStatusRepository.findAllByBikeTypeAndStatus(query.bikeType(), RentalStatus.AVAILABLE);
    }

    @QueryHandler
    public BikeStatus findOne(FindOneQuery query) {
        return bikeStatusRepository.findById(query.bikeId()).orElse(null);
    }

}
```

**Separate query class files** (in the project's query API package, e.g. `rental/api/`):

```java
@Query(name = "findAll")
public record FindAllQuery() {}

@Query(name = "findAvailable")
public record FindAvailableQuery(String bikeType) {}

@Query(name = "findOne")
public record FindOneQuery(String bikeId) {}
```

> These records are **not** inner classes of `RentalBikeQueryProjection`. They live in a shared API package so both the handler and the dispatch site (query-gateway recipe) can reference them.

## What changed

- `@QueryHandler(queryName = "…")` → `@QueryHandler` (attribute removed on all three methods).
- `org.axonframework.queryhandling.QueryHandler` → `org.axonframework.messaging.queryhandling.annotation.QueryHandler`.
- `org.axonframework.messaging.queryhandling.annotation.Query` import added.
- Three payload records introduced as inner records: `FindAllQuery`, `FindAvailableQuery`, `FindOneQuery`.
- Each record carries `@Query(name = "…")` matching the original AF4 `queryName` string (case-sensitive matching required; "FindAllQuery" ≠ "findAll" so annotation is mandatory).
- `findAll()` no-param → `findAll(FindAllQuery ignored)` — marker record as required first parameter.
- `findAvailable(String bikeType)` → `findAvailable(FindAvailableQuery query)` — bare scalar wrapped; body updated `bikeType` → `query.bikeType()`.
- `findOne(String bikeId)` → `findOne(FindOneQuery query)` — same pattern; `bikeId` → `query.bikeId()`.

## Caveats

- **Dispatch side coupling**: The `queryGateway.query("findAll", ...)` calls elsewhere MUST also be updated (query-gateway recipe, use-case 04). Handler and dispatch sides must agree on payload class.
- **@Query annotation omittable if names match**: If the record simple name happens to equal the AF4 queryName string exactly (case-sensitive), `@Query` is not required. In practice this rarely happens because Java class names are typically PascalCase while AF4 query names were camelCase.
- **Records must be top-level**: Always create query records as separate top-level classes in the project's query API package — never as inner classes of the handler. They are shared API used by both handler and dispatch sides.
