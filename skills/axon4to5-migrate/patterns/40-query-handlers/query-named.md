# Named Query — @QueryHandler(queryName) → @Query Payload Record

AF4 allowed routing queries by a `queryName` string. AF5 routes entirely by the first method parameter type —
the `queryName` attribute is removed. When AF4 used a named query, introduce a top-level payload record.

## Import Mappings

| AF4 | AF5 |
|-----|-----|
| `@QueryHandler(queryName = "…")` attribute | *(remove attribute)* |
| — | `org.axonframework.messaging.queryhandling.annotation.Query` (only when class name ≠ queryName) |

## Detection

```bash
grep -rn '@QueryHandler.*queryName' --include='*.java' --include='*.kt' --include='*.scala' .
```

## Axon Framework 4 Code

```java
@QueryHandler(queryName = "findAvailable")
public Iterable<BikeStatus> findAvailable(String bikeType) {
    return repository.findAllByStatus(BikeStatus.available(bikeType));
}
```

## Axon Framework 5 Code

Introduce a payload record in the query API package:

```java
// queries/FindAvailableQuery.java
import org.axonframework.messaging.queryhandling.annotation.Query;

// Add @Query ONLY when simple class name ≠ queryName string (case-sensitive)
// "FindAvailableQuery" ≠ "findAvailable" → annotation required
@Query(name = "findAvailable")
public record FindAvailableQuery(String bikeType) {}
```

Update the handler:

```java
@QueryHandler
public Iterable<BikeStatus> findAvailable(FindAvailableQuery query) {
    return repository.findAllByStatus(BikeStatus.available(query.bikeType()));
}
```

## Notes

- **Do NOT nest the record inside the handler class** — query records are shared API; place them in the
  project's query API package.
- **`@Query` is only needed when the record's simple class name does not equal the `queryName` string
  (case-sensitive).** If they match, the annotation is optional.
- No-param queries: `public record FindAvailableQuery() {}` — the record still needs to exist even with
  no fields.
- **OpenRewrite status:** None — no OR rule rewrites `@QueryHandler(queryName = "…")` into a `@Query` payload record; AI introduces the record and updates the handler signature.
