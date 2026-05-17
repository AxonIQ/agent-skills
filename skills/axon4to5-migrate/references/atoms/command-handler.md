---
atom-id: command-handler
title: "@CommandHandler — import package move + EventAppender parameter"
af4-symbols: ["org.axonframework.commandhandling.CommandHandler"]
af5-symbols: ["org.axonframework.messaging.commandhandling.annotation.CommandHandler"]
detect: grep -rn 'import org.axonframework.commandhandling.CommandHandler' --include='*.java' --include='*.kt' --include='*.scala' .
used-by: [aggregate]
---

# @CommandHandler — Import Package Move + EventAppender Parameter

The `@CommandHandler` annotation moved to the `messaging.commandhandling.annotation` package. Additionally, every
`@CommandHandler` on an aggregate (or child entity) must receive an `EventAppender` as its last parameter — see
[[event-appender]] for the full `AggregateLifecycle.apply → eventAppender.append` transformation.

## Detect

```bash
grep -rn 'import org\.axonframework\.commandhandling\.CommandHandler' --include='*.java' --include='*.kt' --include='*.scala' .
```

## Import change

**Remove:**
```java
import org.axonframework.commandhandling.CommandHandler;
```

**Add:**
```java
import org.axonframework.messaging.commandhandling.annotation.CommandHandler;
```

⚠️ The **`.messaging.`** infix is mandatory — `org.axonframework.commandhandling.annotation.CommandHandler` (no
`.messaging.`) does not exist.

## Signature change (aggregates only)

Every `@CommandHandler` method on an aggregate or child entity gains `EventAppender eventAppender` as its **last**
parameter. See [[event-appender]] for the complete transformation including replacing `AggregateLifecycle.apply(…)`.

```java
// AF4
@CommandHandler
public void handle(ShipOrderCommand cmd) {
    AggregateLifecycle.apply(new OrderShippedEvent(orderId));
}

// AF5
@CommandHandler
public void handle(ShipOrderCommand cmd, EventAppender eventAppender) {
    eventAppender.append(new OrderShippedEvent(orderId));
}
```

For **static** `@CommandHandler` methods (ALWAYS creation pattern), `EventAppender` is still required:

```java
// AF5 — static creation handler
@CommandHandler
public static Order handle(CreateOrderCommand cmd, EventAppender eventAppender) {
    Order o = new Order();
    eventAppender.append(new OrderCreatedEvent(cmd.getOrderId()));
    return o;
}
```

## Event processors / query handlers (outside aggregates)

`@CommandHandler` on a non-aggregate class (e.g., a REST controller dispatching via the bus directly) only needs
the import change — no `EventAppender` parameter.

## Gotchas

- **`.messaging.` infix** — almost always guessed wrong. Grep after editing to confirm.
- **`EventAppender` import also has `.messaging.` infix** — `org.axonframework.messaging.eventhandling.gateway.EventAppender`.
- **All `@CommandHandler` methods, not just the first one** — each method gets its own `EventAppender` parameter.
- **Constructor `@CommandHandler`** — a constructor annotated `@CommandHandler` also gets `EventAppender eventAppender`
  as its last parameter (after the command parameter).

## Used By

- **[[aggregate]]** — common steps (always), one of the first imports to fix
