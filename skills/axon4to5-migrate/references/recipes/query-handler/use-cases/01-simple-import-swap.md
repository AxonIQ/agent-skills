# 01 — Simple @QueryHandler class: import-only swap

**Why this case is interesting:** Projection classes that already use typed query payload classes (no string `queryName`, no `QueryUpdateEmitter`) need only the `@QueryHandler` import package to change. Everything else — annotations, parameters, method bodies — stays byte-identical.

**Apply-condition:** `$SOURCE` has `@QueryHandler` with proper payload-class parameters, no `queryName` attribute, no `QueryUpdateEmitter` dependency.

---

## Before (AF4)

```java
package io.axoniq.demo.bikerental.rental.query;

import org.axonframework.queryhandling.QueryHandler;
import org.springframework.stereotype.Component;

@Component
public class BikeStatusHandler {

    private final BikeStatusRepository bikeStatusRepository;

    public BikeStatusHandler(BikeStatusRepository bikeStatusRepository) {
        this.bikeStatusRepository = bikeStatusRepository;
    }

    @QueryHandler
    public Iterable<BikeStatus> findAll(FindAllBikes query) {
        return bikeStatusRepository.findAll();
    }

    @QueryHandler
    public BikeStatus findOne(FindBikeById query) {
        return bikeStatusRepository.findById(query.bikeId()).orElse(null);
    }
}
```

## After (AF5)

```java
package io.axoniq.demo.bikerental.rental.query;

import org.axonframework.messaging.queryhandling.annotation.QueryHandler;
import org.springframework.stereotype.Component;

@Component
public class BikeStatusHandler {

    private final BikeStatusRepository bikeStatusRepository;

    public BikeStatusHandler(BikeStatusRepository bikeStatusRepository) {
        this.bikeStatusRepository = bikeStatusRepository;
    }

    @QueryHandler
    public Iterable<BikeStatus> findAll(FindAllBikes query) {
        return bikeStatusRepository.findAll();
    }

    @QueryHandler
    public BikeStatus findOne(FindBikeById query) {
        return bikeStatusRepository.findById(query.bikeId()).orElse(null);
    }
}
```

## What changed

- `org.axonframework.queryhandling.QueryHandler` → `org.axonframework.messaging.queryhandling.annotation.QueryHandler`
- Everything else: unchanged.
