# 03 — ResponseType wrapper removal + `queryMany`

**Why this case is interesting:** AF4 required wrapping response types in `ResponseTypes.instanceOf(R.class)` / `multipleInstancesOf(R.class)`. AF5 removed this SPI entirely. The `multipleInstancesOf` case is a double change: remove wrapper AND rename method to `queryMany`.

**Apply-condition:** `$SOURCE` uses `ResponseTypes.instanceOf(...)` / `multipleInstancesOf(...)` / `optionalInstanceOf(...)`.

## Before (AF4)

```java
package com.example.bikes.api;

import com.example.bikes.query.BikeStatus;
import org.axonframework.messaging.responsetypes.ResponseTypes;
import org.axonframework.queryhandling.QueryGateway;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.concurrent.CompletableFuture;

@RestController
@RequestMapping("/bikes")
class BikeStatusController {

    private final QueryGateway queryGateway;

    BikeStatusController(QueryGateway queryGateway) {
        this.queryGateway = queryGateway;
    }

    @GetMapping("/{bikeId}")
    CompletableFuture<BikeStatus> findOne(@PathVariable String bikeId) {
        return queryGateway.query(
                new FindBikeById(bikeId),
                ResponseTypes.instanceOf(BikeStatus.class)
        );
    }

    @GetMapping
    CompletableFuture<List<BikeStatus>> findAll() {
        return queryGateway.query(
                new FindAllBikes(),
                ResponseTypes.multipleInstancesOf(BikeStatus.class)
        );
    }
}
```

## After (AF5)

```java
package com.example.bikes.api;

import com.example.bikes.query.BikeStatus;
import org.axonframework.messaging.queryhandling.gateway.QueryGateway;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.concurrent.CompletableFuture;

@RestController
@RequestMapping("/bikes")
class BikeStatusController {

    private final QueryGateway queryGateway;

    BikeStatusController(QueryGateway queryGateway) {
        this.queryGateway = queryGateway;
    }

    @GetMapping("/{bikeId}")
    CompletableFuture<BikeStatus> findOne(@PathVariable String bikeId) {
        return queryGateway.query(new FindBikeById(bikeId), BikeStatus.class);
    }

    @GetMapping
    CompletableFuture<List<BikeStatus>> findAll() {
        return queryGateway.queryMany(new FindAllBikes(), BikeStatus.class);
    }
}
```

## What changed

- AF4 import → AF5 import.
- `import org.axonframework.messaging.responsetypes.ResponseTypes;` removed.
- `ResponseTypes.instanceOf(BikeStatus.class)` → `BikeStatus.class`.
- `query(..., ResponseTypes.multipleInstancesOf(BikeStatus.class))` → `queryMany(..., BikeStatus.class)`.
- Method return types unchanged (`CompletableFuture<BikeStatus>`, `CompletableFuture<List<BikeStatus>>`).

## Caveats

- `query(...)` is **always single-response** in AF5. Any AF4 site using `multipleInstancesOf` MUST use `queryMany(...)` — using `query(...)` with a `Class<R>` would compile but return only the first result.
- `optionalInstanceOf(R.class)` → `query(payload, R.class)`. The future resolves to `null` if no result — callers must handle null.
- Custom `ResponseType` subclass in the project → Blocker B2; do not attempt to strip mechanically.
