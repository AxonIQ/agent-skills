# 03 — QueryUpdateEmitter: constructor injection → method parameter

**Why this case is interesting:** AF4 `QueryUpdateEmitter` was a Spring-managed bean injected via constructor. AF5 injects it as a method-level parameter directly into each `@EventHandler` method that emits updates. Additionally, the `emit()` signature changed from a 2-arg form (predicate on `QueryMessage`) to a 3-arg form (query payload class + predicate on payload + update).

**Apply-condition:** `$SOURCE` has `QueryUpdateEmitter` as a constructor dependency.

---

## Before (AF4) — from bike-rental-extended

```java
package io.axoniq.demo.bikerental.rental.query;

import org.axonframework.eventhandling.EventHandler;
import org.axonframework.queryhandling.QueryHandler;
import org.axonframework.queryhandling.QueryUpdateEmitter;
import org.springframework.stereotype.Component;

@Component
public class BikeStatusSubscriptionProjection {

    private final BikeStatusRepository bikeStatusRepository;
    private final QueryUpdateEmitter updateEmitter;

    public BikeStatusSubscriptionProjection(BikeStatusRepository bikeStatusRepository,
                                            QueryUpdateEmitter updateEmitter) {
        this.bikeStatusRepository = bikeStatusRepository;
        this.updateEmitter = updateEmitter;
    }

    @EventHandler
    public void on(BikeRegisteredEvent event) {
        var bikeStatus = new BikeStatus(event.getBikeId(), event.getBikeType(), event.getLocation());
        bikeStatusRepository.save(bikeStatus);
        updateEmitter.emit(q -> "findAll".equals(q.getQueryName()), bikeStatus);
    }

    @QueryHandler
    public Iterable<BikeStatus> findAll(FindAllBikes query) {
        return bikeStatusRepository.findAll();
    }
}
```

## After (AF5)

```java
package io.axoniq.demo.bikerental.rental.query;

import org.axonframework.messaging.eventhandling.annotation.EventHandler;
import org.axonframework.messaging.queryhandling.QueryUpdateEmitter;
import org.axonframework.messaging.queryhandling.annotation.QueryHandler;
import org.springframework.stereotype.Component;

@Component
public class BikeStatusSubscriptionProjection {

    private final BikeStatusRepository bikeStatusRepository;

    public BikeStatusSubscriptionProjection(BikeStatusRepository bikeStatusRepository) {
        this.bikeStatusRepository = bikeStatusRepository;
    }

    @EventHandler
    public void on(BikeRegisteredEvent event, QueryUpdateEmitter updateEmitter) {
        var bikeStatus = new BikeStatus(event.bikeId(), event.bikeType(), event.location());
        bikeStatusRepository.save(bikeStatus);
        updateEmitter.emit(FindAllBikes.class, q -> true, bikeStatus);
    }

    @QueryHandler
    public Iterable<BikeStatus> findAll(FindAllBikes query) {
        return bikeStatusRepository.findAll();
    }
}
```

## What changed

- `private final QueryUpdateEmitter updateEmitter` field removed.
- Constructor: `QueryUpdateEmitter updateEmitter` param removed; body assignment removed.
- `@EventHandler on(BikeRegisteredEvent event)` → `on(BikeRegisteredEvent event, QueryUpdateEmitter updateEmitter)` — QUE injected as method param.
- `updateEmitter.emit(q -> "findAll".equals(q.getQueryName()), bikeStatus)` (2-arg) → `updateEmitter.emit(FindAllBikes.class, q -> true, bikeStatus)` (3-arg).
  - First arg: query payload class (`FindAllBikes.class`) identifies which subscription query to update.
  - Second arg: predicate now receives the payload `FindAllBikes q` directly (not the `QueryMessage` envelope). Use `q -> true` when all subscribers of that query type should receive the update; use a narrowing predicate (e.g. `q -> q.bikeId().equals(event.bikeId())`) for targeted updates.
- Imports updated:
  - `org.axonframework.queryhandling.QueryUpdateEmitter` → `org.axonframework.messaging.queryhandling.QueryUpdateEmitter`
  - `org.axonframework.eventhandling.EventHandler` → `org.axonframework.messaging.eventhandling.annotation.EventHandler` (fixed on touched method)
  - `org.axonframework.queryhandling.QueryHandler` → `org.axonframework.messaging.queryhandling.annotation.QueryHandler`

## Caveats

- **Predicate parameter type change**: AF4 predicate `Predicate<QueryMessage<Q,?>>` receives the full message envelope. AF5 predicate `Predicate<Q>` receives the payload directly. Rewrite any predicate that accessed message-level fields like `q.getQueryName()`, `q.getMetaData()`.
- **Multiple @EventHandler methods**: If multiple event handlers emit updates, each gets a `QueryUpdateEmitter updateEmitter` parameter independently.
- **@EventHandler import side effect**: This recipe fixes `@EventHandler` import only on methods physically modified for QUE injection. Untouched @EventHandler methods retain their AF4 imports — event-processor recipe handles those.
