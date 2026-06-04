# 03 — Scheduler / runner: `sendAndWait` → import-only

**Why this case is interesting:** `@Scheduled` methods, `CommandLineRunner`, and `ApplicationRunner` callers cannot accept a `CompletableFuture` — they run to completion and return `void`. In AF5 `sendAndWait` still exists and the call site is functionally unchanged. The only required edit is the `CommandGateway` import package swap. This is the simplest migration shape: one import line changes, nothing else.

**Apply-condition:** `$SOURCE` is a `@Scheduled` method or `CommandLineRunner` / `ApplicationRunner` using `commandGateway.sendAndWait(...)` (caller cannot accept a future).

## Before (AF4)

```java
package com.example.jobs;

import com.example.jobs.commands.ProcessPendingOrdersCommand;
import org.axonframework.commandhandling.gateway.CommandGateway;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
class ScheduledOrderProcessor {

    private final CommandGateway commandGateway;

    ScheduledOrderProcessor(CommandGateway commandGateway) {
        this.commandGateway = commandGateway;
    }

    @Scheduled(fixedDelay = 60_000)
    void processOrders() {
        commandGateway.sendAndWait(new ProcessPendingOrdersCommand());
    }
}
```

## After (AF5)

```java
package com.example.jobs;

import com.example.jobs.commands.ProcessPendingOrdersCommand;
import org.axonframework.messaging.commandhandling.gateway.CommandGateway;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
class ScheduledOrderProcessor {

    private final CommandGateway commandGateway;

    ScheduledOrderProcessor(CommandGateway commandGateway) {
        this.commandGateway = commandGateway;
    }

    @Scheduled(fixedDelay = 60_000)
    void processOrders() {
        commandGateway.sendAndWait(new ProcessPendingOrdersCommand());
    }
}
```

## What changed

- `CommandGateway` import: `org.axonframework.commandhandling.gateway.CommandGateway` → `org.axonframework.messaging.commandhandling.gateway.CommandGateway`.
- Everything else unchanged — `sendAndWait`, field, constructor, method body.

## Caveats

- **Do NOT introduce `CompletableFuture` here** — `@Scheduled void` methods must not return a future. If you force `send(cmd, Void.class)` and block via `.join()`, you introduce a blocking call on the scheduler thread that may exceed the fixed-delay period. Keep `sendAndWait`.
- **Same applies to `CommandLineRunner.run(...)` and `ApplicationRunner.run(...)`** — callers that run to completion and return `void`; prefer `sendAndWait`.
- **`sendAndWait(cmd, timeout, unit)` is gone in AF5** — if the source uses the three-argument form, rewrite to `send(cmd, Void.class).orTimeout(timeout, unit).join()` to preserve the blocking + timeout semantic (always with a timeout — never bare `.join()`).
