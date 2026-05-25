# 06 — Spring REST controller: import-only change

**Why this case is interesting:** The simplest AF4→AF5 path. The controller already uses the `Class<R>` overload of `query(...)` — AF5 kept this overload. Only the `QueryGateway` import package changes.

**Apply-condition:** `$SOURCE` is a Spring `@RestController` AND all `query(...)` calls use `Class<R>` (no `ResponseType` wrapper, no named-query string).

## Before (AF4)

```java
package com.example.dwellings.api;

import com.example.dwellings.read.DwellingReadModel;
import org.axonframework.queryhandling.QueryGateway;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.concurrent.CompletableFuture;

@RestController
@RequestMapping("/dwellings")
class DwellingRestController {

    private final QueryGateway queryGateway;

    DwellingRestController(QueryGateway queryGateway) {
        this.queryGateway = queryGateway;
    }

    @GetMapping("/{dwellingId}")
    CompletableFuture<DwellingReadModel> getDwelling(@PathVariable String dwellingId) {
        return queryGateway.query(new GetDwellingById(dwellingId), DwellingReadModel.class);
    }
}
```

## After (AF5)

```java
package com.example.dwellings.api;

import com.example.dwellings.read.DwellingReadModel;
import org.axonframework.messaging.queryhandling.gateway.QueryGateway;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.concurrent.CompletableFuture;

@RestController
@RequestMapping("/dwellings")
class DwellingRestController {

    private final QueryGateway queryGateway;

    DwellingRestController(QueryGateway queryGateway) {
        this.queryGateway = queryGateway;
    }

    @GetMapping("/{dwellingId}")
    CompletableFuture<DwellingReadModel> getDwelling(@PathVariable String dwellingId) {
        return queryGateway.query(new GetDwellingById(dwellingId), DwellingReadModel.class);
    }
}
```

## What changed

- `org.axonframework.queryhandling.QueryGateway` → `org.axonframework.messaging.queryhandling.gateway.QueryGateway`
- Body, field, constructor, and method signature **unchanged**

## Caveats

- If the AF4 call had used `ResponseTypes.instanceOf(DwellingReadModel.class)` instead of `DwellingReadModel.class`, the wrapper must be stripped — see use-case 03.
- The controller returns `CompletableFuture<DwellingReadModel>` — Spring MVC serves async futures natively. No blocking concern here.
