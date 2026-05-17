---
atom-id: command-dispatcher
title: "In-handler command dispatch — CommandGateway field → CommandDispatcher method parameter"
af4-symbols: ["CommandGateway", "commandGateway.sendAndWait", "commandGateway.send", "org.axonframework.commandhandling.gateway.CommandGateway"]
af5-symbols: ["CommandDispatcher", "commandDispatcher.send", "org.axonframework.messaging.commandhandling.gateway.CommandDispatcher"]
detect: grep -rn 'CommandGateway' --include='*.java' . # then filter: classes with @EventHandler that call commandGateway
used-by: [event-processor]
---

# In-Handler Command Dispatch — CommandGateway → CommandDispatcher

AF4 injected `CommandGateway` as a class-level field in event processors that needed to dispatch commands from
inside `@EventHandler` methods. AF5 replaces this with `CommandDispatcher` injected as a **method parameter** —
the framework automatically binds it to the active `ProcessingContext`.

⚠️ This atom applies to **in-handler dispatch only** (event processors, sagas-as-processors). Top-of-chain
dispatchers (REST controllers, CLI runners, MCP tools) keep `CommandGateway` — those are handled by the
command-gateway recipe.

## Detect

```bash
# Find classes that inject CommandGateway AND have @EventHandler methods
grep -rln 'CommandGateway' --include='*.java' . \
  | xargs grep -l '@EventHandler'
```

## Transform

### Step 1 — Remove class-level field

```java
// AF4
@ProcessingGroup("orders")
public class OrderAutomation {

    private final CommandGateway commandGateway;

    public OrderAutomation(CommandGateway commandGateway) {
        this.commandGateway = commandGateway;
    }
    // …
}

// AF5 — field and constructor injection removed
@Namespace("orders")
public class OrderAutomation {
    // No CommandGateway field
    // …
}
```

### Step 2 — Add `CommandDispatcher` as method parameter

```java
// AF4
@EventHandler
public void on(MoneyTransferredEvent event) {
    try {
        commandGateway.sendAndWait(new CreditAccountCommand(event.getTargetAccount(), event.getAmount()));
    } catch (Exception e) {
        commandGateway.sendAndWait(new DebitAccountCommand(event.getSourceAccount(), event.getAmount())); // compensation
    }
}

// AF5
@EventHandler
public CompletableFuture<?> on(MoneyTransferredEvent event, CommandDispatcher commandDispatcher) {
    return commandDispatcher.send(new CreditAccountCommand(event.getTargetAccount(), event.getAmount()))
            .getResultMessage()
            .thenApply(m -> (Message) m)
            .exceptionallyCompose(err ->
                    commandDispatcher.send(new DebitAccountCommand(event.getSourceAccount(), event.getAmount()))
                            .resultAs(Message.class));
}
```

### Import

```java
import org.axonframework.messaging.commandhandling.gateway.CommandDispatcher;
import java.util.concurrent.CompletableFuture;
```

## Key API differences

| AF4 | AF5 |
|---|---|
| `commandGateway.sendAndWait(cmd)` | `commandDispatcher.send(cmd).getResultMessage()` → `CompletableFuture` |
| `commandGateway.send(cmd)` | `commandDispatcher.send(cmd)` |
| try/catch around `sendAndWait` | `.exceptionallyCompose(err -> …)` on the future |
| Returns the result synchronously | Returns `CompletableFuture<? extends Message>` |

## Prefer `.resultAs(Message.class)` over `.getResultMessage()`

`.resultAs(Message.class)` returns `CompletableFuture<Message>` (no wildcard) and avoids a cast when used in
`.exceptionallyCompose(…)`:

```java
commandDispatcher.send(cmd).resultAs(Message.class)
```

## Gotchas

- **`sendAndWait` → async is a semantic change**, not just a rename. AF4 try/catch around `sendAndWait`
  (compensation logic) becomes `.exceptionallyCompose(…)`. Forgetting this means compensation silently stops.
- **`CompletableFuture<? extends Message>` from `getResultMessage()`** — the wildcard type cannot be directly
  passed to `exceptionallyCompose` without a cast; use `.thenApply(m -> (Message) m)` before chaining, or use
  `.resultAs(Message.class)`.
- **Method return type** — handler methods that dispatch commands must return `CompletableFuture<?>` (or a narrower
  type). Framework propagates the future correctly.
- **`CommandDispatcher` only works inside a `ProcessingContext`** — it cannot be used from a REST endpoint or any
  code outside a message handler. For those cases, keep `CommandGateway`.
- **Do not use `CommandGateway` AND `CommandDispatcher` side-by-side in the same class** — remove the
  `CommandGateway` field entirely when converting to `CommandDispatcher`.

## Used By

- **[[event-processor]]** — Step 4 (when `$SOURCE` has a `CommandGateway` field + in-handler dispatch)
