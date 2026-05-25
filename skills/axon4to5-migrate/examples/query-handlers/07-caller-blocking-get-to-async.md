# 07 — Blocking `.get()` call: prefer async upgrade; fallback to `.orTimeout().join()` when constrained

**Why this case is interesting:** AF4 code often calls `.get()` on the `CompletableFuture` returned by `queryGateway.query(...)`. AF5 still returns `CompletableFuture<R>`, so the preferred fix is to stop blocking entirely — change the method return type to `CompletableFuture<R>` and return the future directly. The `.orTimeout().join()` pattern is a fallback only when the method signature is truly constrained by a sync framework contract.

**Apply-condition:** `$SOURCE` has bare `.get()` or `.join()` without `.orTimeout(...)` on a `queryGateway.query(...)` result.

---

## Path A — Method can return `CompletableFuture<R>` (preferred)

Use when the method is a plain service method, Spring MVC endpoint, or any caller whose signature is not locked to a sync return by an external framework contract.

### Before (AF4)

```java
package com.example.dwellings;

import org.axonframework.queryhandling.QueryGateway;
import org.springframework.stereotype.Component;

@Component
class DwellingsQueryService {

    private final QueryGateway queryGateway;

    DwellingsQueryService(QueryGateway queryGateway) {
        this.queryGateway = queryGateway;
    }

    DwellingReadModel getDwelling(String dwellingId) {
        try {
            return queryGateway.query(new GetDwellingById(dwellingId), DwellingReadModel.class).get();
        } catch (Exception e) {
            throw new RuntimeException("Query failed", e);
        }
    }
}
```

### After (AF5 — preferred)

```java
package com.example.dwellings;

import org.axonframework.messaging.queryhandling.gateway.QueryGateway;
import org.springframework.stereotype.Component;

import java.util.concurrent.CompletableFuture;

@Component
class DwellingsQueryService {

    private final QueryGateway queryGateway;

    DwellingsQueryService(QueryGateway queryGateway) {
        this.queryGateway = queryGateway;
    }

    CompletableFuture<DwellingReadModel> getDwelling(String dwellingId) {
        return queryGateway.query(new GetDwellingById(dwellingId), DwellingReadModel.class);
    }
}
```

### What changed

- AF4 import → AF5 import.
- Method return type `DwellingReadModel` → `CompletableFuture<DwellingReadModel>`.
- `import java.util.concurrent.CompletableFuture;` added.
- Body simplified: return the future directly — no `.get()`, no try-catch.

---

## Path B — Method signature constrained to sync return (fallback)

Use only when the method implements a sync contract that cannot be changed: a sync interface method, `@KafkaListener`, `@JmsListener`, MCP `SyncResourceSpecification` lambda, Camel route step, `CommandLineRunner.run(...)`, `@Scheduled void`, `main(String[])`.

### Before (AF4)

```java
// implements SomeSyncInterface { SomeResult fetchResult(String id); }
@Override
public SomeResult fetchResult(String id) {
    try {
        return queryGateway.query(new GetSomething(id), SomeResult.class).get();
    } catch (Exception e) {
        throw new RuntimeException(e);
    }
}
```

### After (AF5 — sync-constrained fallback)

```java
import java.util.concurrent.TimeUnit;

@Override
public SomeResult fetchResult(String id) {
    try {
        return queryGateway.query(new GetSomething(id), SomeResult.class)
                .orTimeout(30, TimeUnit.SECONDS)
                .join();
    } catch (Exception e) {
        throw new RuntimeException(e);
    }
}
```

### What changed

- AF4 import → AF5 import.
- `.get()` → `.orTimeout(30, TimeUnit.SECONDS).join()`.
- `import java.util.concurrent.TimeUnit;` added.
- The existing `catch (Exception e)` still catches `CompletionException` (unchecked, extends `RuntimeException`).

---

## Caveats

- **Never use `.orTimeout().join()` when the method can go async.** It is a fallback for genuinely constrained callers, not a universal fix.
- **30-second timeout is a default.** Shorten when the surrounding framework has a tighter SLA.
- **Callers of the migrated method** (Path A) will need to handle `CompletableFuture<R>` — check that callers compile after the return type change.
