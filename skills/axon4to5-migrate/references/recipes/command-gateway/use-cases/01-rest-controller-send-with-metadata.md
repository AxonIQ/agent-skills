# 01 — Spring REST controller: `send(cmd, metadata)` → `.resultAs(Void.class)`

**Why this case is interesting:** The most common and most surprising migration for REST controllers. AF4's `commandGateway.send(cmd, metadata)` returned `CompletableFuture<Void>` — so returning it from a `CompletableFuture<Void>` controller method compiled fine. In AF5 the same call returns `CommandResult`, which is NOT assignable to `CompletableFuture`. Without the `.resultAs(Void.class)` fix, the migration looks complete (import changed, method signature unchanged) but does not compile.

**Apply-condition:** `$SOURCE` is a Spring `@RestController` AND uses `commandGateway.send(cmd, metadata)` whose result flows into `CompletableFuture<Void>` or `CompletableFuture<R>`.

## Before (AF4)

```java
package com.example.orders.api;

import com.example.orders.commands.CreateOrderCommand;
import com.example.orders.shared.RequestContext;
import org.axonframework.commandhandling.gateway.CommandGateway;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.concurrent.CompletableFuture;

@RestController
@RequestMapping("/orders")
class OrderRestController {

    private final CommandGateway commandGateway;

    OrderRestController(CommandGateway commandGateway) {
        this.commandGateway = commandGateway;
    }

    @PostMapping
    CompletableFuture<Void> createOrder(
            @RequestHeader("X-User-Id") String userId,
            @RequestBody OrderRequest body
    ) {
        var command = new CreateOrderCommand(body.orderId(), body.product());
        return commandGateway.send(command, RequestContext.with(userId));
    }
}
```

## After (AF5)

```java
package com.example.orders.api;

import com.example.orders.commands.CreateOrderCommand;
import com.example.orders.shared.RequestContext;
import org.axonframework.messaging.commandhandling.gateway.CommandGateway;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.concurrent.CompletableFuture;

@RestController
@RequestMapping("/orders")
class OrderRestController {

    private final CommandGateway commandGateway;

    OrderRestController(CommandGateway commandGateway) {
        this.commandGateway = commandGateway;
    }

    @PostMapping
    CompletableFuture<Void> createOrder(
            @RequestHeader("X-User-Id") String userId,
            @RequestBody OrderRequest body
    ) {
        var command = new CreateOrderCommand(body.orderId(), body.product());
        return commandGateway.send(command, RequestContext.with(userId))
                             .resultAs(Void.class);
    }
}
```

## What changed

- `CommandGateway` import: `org.axonframework.commandhandling.gateway.CommandGateway` → `org.axonframework.messaging.commandhandling.gateway.CommandGateway`.
- `return commandGateway.send(command, context)` → appended `.resultAs(Void.class)`.
- Field type, constructor, and parameter name unchanged.

## Caveats

- **`CommandResult` is NOT `CompletableFuture`** — the AF4 `send(cmd, metadata)` returned `CompletableFuture<Void>` and could be `return`ed directly from a `CompletableFuture<Void>` method. AF5 returns `CommandResult`, so `.resultAs(Void.class)` is required. Forgetting this is the most common silent compile failure.
- **Metadata helper migration is a separate step** — if `RequestContext.with(userId)` (or equivalent) returns AF4 `org.axonframework.messaging.MetaData`, the file will still fail to compile after this recipe's edits. Flag the helper in NOTES as a follow-up; do NOT attempt to migrate it from inside this recipe.
- **`CompletableFuture` import already present** — since the method return type was `CompletableFuture<Void>` in AF4, the import is already there. No new import needed.
