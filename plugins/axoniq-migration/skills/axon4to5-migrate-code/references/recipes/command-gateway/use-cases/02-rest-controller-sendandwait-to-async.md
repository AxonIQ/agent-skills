# 02 — Spring REST controller: `sendAndWait` → preferred async `send(cmd, R.class)`

**Why this case is interesting:** `sendAndWait` still exists in AF5 and can be kept (import-only change). But inside a Spring `@RestController`, blocking the request thread is unnecessary — Spring dispatches `CompletableFuture<R>` method results asynchronously with no behavioural change to the caller. Preferred migration: upgrade the method return type from `R` to `CompletableFuture<R>` and swap to `send(cmd, R.class)`. If the surrounding code cannot accept a future, the fallback is import-only.

**Apply-condition:** `$SOURCE` is a Spring `@RestController` AND uses `commandGateway.sendAndWait(cmd, R.class)` (or `sendAndWait(cmd)`) where the surrounding method can return a `CompletableFuture`.

## Before (AF4)

```java
package com.example.capacity.api;

import com.example.capacity.commands.ReserveCapacityCommand;
import com.example.capacity.dto.ReservationResult;
import org.axonframework.commandhandling.gateway.CommandGateway;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/capacity")
class CapacityRestController {

    private final CommandGateway commandGateway;

    CapacityRestController(CommandGateway commandGateway) {
        this.commandGateway = commandGateway;
    }

    @PutMapping("/{courseId}")
    ReservationResult reserveCapacity(
            @PathVariable String courseId,
            @RequestParam int seats
    ) {
        return commandGateway.sendAndWait(
                new ReserveCapacityCommand(courseId, seats),
                ReservationResult.class
        );
    }
}
```

## After (AF5) — preferred: async

```java
package com.example.capacity.api;

import com.example.capacity.commands.ReserveCapacityCommand;
import com.example.capacity.dto.ReservationResult;
import org.axonframework.messaging.commandhandling.gateway.CommandGateway;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.concurrent.CompletableFuture;

@RestController
@RequestMapping("/capacity")
class CapacityRestController {

    private final CommandGateway commandGateway;

    CapacityRestController(CommandGateway commandGateway) {
        this.commandGateway = commandGateway;
    }

    @PutMapping("/{courseId}")
    CompletableFuture<ReservationResult> reserveCapacity(
            @PathVariable String courseId,
            @RequestParam int seats
    ) {
        return commandGateway.send(
                new ReserveCapacityCommand(courseId, seats),
                ReservationResult.class
        );
    }
}
```

## What changed

- `CommandGateway` import: AF4 package → AF5 package.
- Method return type: `ReservationResult` → `CompletableFuture<ReservationResult>`.
- `sendAndWait(cmd, ReservationResult.class)` → `send(cmd, ReservationResult.class)`.
- `import java.util.concurrent.CompletableFuture;` added.

## Caveats

- **Fallback (keep blocking):** if the caller requires a synchronous result (e.g. integration test asserting on the return value, or the controller is part of a chain that expects a direct type), keep `sendAndWait(...)` and change only the import. `sendAndWait` still exists in AF5.
- **`send(cmd, R.class)` shorthand** — convenience for `send(cmd).resultAs(R.class)`. Prefer when no metadata is involved.
- **Spring serves `CompletableFuture<R>` async** — same HTTP response, no thread blocking. The HTTP client observes no difference; the server thread is freed immediately.
- **`sendAndWait(cmd, timeout, unit)` overload is GONE in AF5** — if the source uses this three-argument form, rewrite to `send(cmd, R.class).orTimeout(timeout, unit)` (future, preferred) or append `.join()` to preserve blocking (always with a timeout — never bare `.join()` without one).
