---
atom-id: query-payload-record
title: "@QueryHandler(queryName) removal — introduce @Query-annotated top-level payload record"
af4-symbols: ["@QueryHandler(queryName", "org.axonframework.queryhandling.QueryHandler#queryName"]
af5-symbols: ["@Query", "org.axonframework.messaging.queryhandling.annotation.Query"]
detect: grep -rn '@QueryHandler.*queryName' --include='*.java' --include='*.kt' --include='*.scala' .
used-by: [query-handler]
---

# @QueryHandler(queryName) → @Query Payload Record

AF5 routes queries entirely by the first method parameter type. The `queryName` attribute is removed. When AF4
used a named query, introduce a top-level payload record and annotate it with `@Query(name = "…")` matching
the AF4 string exactly.

## When this atom applies

`$SOURCE` has at least one `@QueryHandler(queryName = "…")` method.

## Transform

### Step 1 — Record the queryName

Record the AF4 `queryName` value (e.g., `"findAvailable"`).

### Step 2 — Introduce a top-level payload record

Place as a **separate top-level file** in the project's query API package:

```java
// queries/FindAvailableQuery.java
import org.axonframework.messaging.queryhandling.annotation.Query;

// Add @Query ONLY when simple class name ≠ queryName string (case-sensitive)
// "FindAvailableQuery" ≠ "findAvailable" → annotation required
@Query(name = "findAvailable")
public record FindAvailableQuery(String bikeType) {}
// No-param case: public record FindAvailableQuery() {}
```

**Do NOT nest the record inside the handler class** — query records are shared API; they live in the
project's query API package, not inside the handler.

### Step 3 — Update the handler method

```java
// AF4
@QueryHandler(queryName = "findAvailable")
public Iterable<BikeStatus> findAvailable(String bikeType) {
    return repository.findAllByStatus(BikeStatus.available(bikeType));
}

// AF5
@QueryHandler
public Iterable<BikeStatus> findAvailable(FindAvailableQuery query) {
    return repository.findAllByStatus(BikeStatus.available(query.bikeType()));
}
```

Remove `queryName` attribute. Change the parameter to the record type. Update body references
(`bikeType` → `query.bikeType()`).

### Import

```java
import org.axonframework.messaging.queryhandling.annotation.Query;
```

## Gotchas

- **`@Query` name must match AF4 string exactly (case-sensitive)** — AF5 routes by `@Query.name()`. `FindAvailableQuery` ≠ `"findAvailable"` — always set the annotation when they differ.
- **Top-level class is mandatory** — inner records are not acceptable; the record is shared between dispatch and handler sides.
- **No-param handler** — when AF4 had no parameter, introduce `record FindAllQuery() {}` and declare `FindAllQuery ignored` in the handler.
- **Dispatch side coupling** — this atom changes the handler side only. The dispatch site (`queryGateway.query("name", ...)`) must also move to the payload class — that belongs to the query-gateway recipe (Step 2).

## Used By

- **[[query-handler]]** — Step 2 (when any `@QueryHandler(queryName = "…")` present)
