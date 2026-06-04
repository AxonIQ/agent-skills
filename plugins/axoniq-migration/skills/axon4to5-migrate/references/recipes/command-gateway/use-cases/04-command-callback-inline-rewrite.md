# 04 — Inline `CommandCallback` lambda → `.onSuccess(...).onError(...)`

**Why this case is interesting:** AF4's `CommandGateway.send(cmd, CommandCallback)` accepted a callback for async success/failure handling. The `CommandCallback` SPI is removed in AF5. Inline lambdas passed at call sites can be mechanically rewritten to the `CommandResult` fluent chain (`.onSuccess(...).onError(...)`). Classes that fully implement `CommandCallback` as a separate type are Blocker B1 and cannot be handled here.

**Apply-condition:** `$SOURCE` passes an inline lambda or anonymous class as `CommandCallback` argument to `commandGateway.send(cmd, callback)` at one or more call sites.

## Before (AF4)

```java
package com.example.notifications.api;

import com.example.notifications.commands.SendNotificationCommand;
import org.axonframework.commandhandling.CommandCallback;
import org.axonframework.commandhandling.CommandMessage;
import org.axonframework.commandhandling.CommandResultMessage;
import org.axonframework.commandhandling.gateway.CommandGateway;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/notifications")
class NotificationController {

    private final CommandGateway commandGateway;

    NotificationController(CommandGateway commandGateway) {
        this.commandGateway = commandGateway;
    }

    @PostMapping("/{recipientId}")
    void notify(@PathVariable String recipientId) {
        commandGateway.send(
                new SendNotificationCommand(recipientId),
                (CommandCallback<SendNotificationCommand, Void>) (msg, result) -> {
                    if (result.isExceptional()) {
                        System.err.println("Failed: " + result.exceptionResult().getMessage());
                    } else {
                        System.out.println("Sent to " + recipientId);
                    }
                }
        );
    }
}
```

## After (AF5)

```java
package com.example.notifications.api;

import com.example.notifications.commands.SendNotificationCommand;
import org.axonframework.messaging.commandhandling.gateway.CommandGateway;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/notifications")
class NotificationController {

    private final CommandGateway commandGateway;

    NotificationController(CommandGateway commandGateway) {
        this.commandGateway = commandGateway;
    }

    @PostMapping("/{recipientId}")
    void notify(@PathVariable String recipientId) {
        commandGateway.send(new SendNotificationCommand(recipientId))
                      .onSuccess(result -> System.out.println("Sent to " + recipientId))
                      .onError(error -> System.err.println("Failed: " + error.getMessage()));
    }
}
```

## What changed

- `CommandGateway` import: AF4 package → AF5 package.
- `CommandCallback`, `CommandMessage`, `CommandResultMessage` imports removed (SPI gone).
- `send(cmd, callback)` → `send(cmd).onSuccess(...).onError(...)`.
- The inline lambda's two-arg form `(msg, result) -> { if (result.isExceptional()) ... }` split into two single-arg lambdas.

## Caveats

- **Preserve error semantics.** The AF4 callback's `isExceptional()` path maps to `onError(Throwable error -> ...)`. Do NOT silently drop the error branch — that is a behavioural regression.
- **`onSuccess` and `onError` are terminal** — `CommandResult` fluent chain. `onSuccess(...)` receives the typed result (or `null` for `Void`); `onError(...)` receives the `Throwable`. Both return `CommandResult` so they can be chained.
- **Blocker B1 boundary** — if the class itself `implements CommandCallback` rather than passing a lambda, stop and emit Blocker B1. The error semantics and design intent of the full implementation are outside what the recipe can safely infer.
- **`void` method stays `void`** — since the call result is consumed via the fluent chain, the surrounding method return type does not need to change unless the caller wants to compose on the result.
