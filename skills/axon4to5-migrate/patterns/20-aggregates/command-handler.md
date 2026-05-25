# @CommandHandler — Import Move + EventAppender Parameter

The `@CommandHandler` annotation moved to the `messaging.commandhandling.annotation` package. Every `@CommandHandler`
on an aggregate or child entity must also receive an `EventAppender` as its last parameter (see
[aggregate-lifecycle.md](aggregate-lifecycle.md)).

## Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.commandhandling.CommandHandler` | `org.axonframework.messaging.commandhandling.annotation.CommandHandler` |

## Detection

```bash
grep -rn 'import org\.axonframework\.commandhandling\.CommandHandler' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

## Axon Framework 4 Code

```java
import org.axonframework.commandhandling.CommandHandler;

@CommandHandler
public void handle(ShipOrderCommand cmd) {
    AggregateLifecycle.apply(new OrderShippedEvent(orderId));
}
```

## Axon Framework 5 Code

```java
import org.axonframework.messaging.commandhandling.annotation.CommandHandler;
import org.axonframework.messaging.eventhandling.gateway.EventAppender;

@CommandHandler
public void handle(ShipOrderCommand cmd, EventAppender eventAppender) {
    eventAppender.append(new OrderShippedEvent(orderId));
}
```

## Partial migration state (post-OpenRewrite)

OR moves the import to the `messaging.commandhandling.annotation` package but does NOT add the `EventAppender` parameter to handler signatures — the handler body still calls `AggregateLifecycle.apply(...)` (or has been partially rewritten elsewhere). Common half-state:

```java
import org.axonframework.messaging.commandhandling.annotation.CommandHandler;  // import already AF5
// EventAppender NOT imported

@CommandHandler
public void handle(ShipOrderCommand cmd) {                 // signature still AF4 — no EventAppender
    AggregateLifecycle.apply(new OrderShippedEvent(orderId));
}
```

Minimal fix: append `EventAppender eventAppender` as the **last** parameter, add the `org.axonframework.messaging.eventhandling.gateway.EventAppender` import, and rewrite the body per [aggregate-lifecycle.md](aggregate-lifecycle.md). Do NOT touch the already-correct `@CommandHandler` import. Audit:

```bash
grep -rn '@CommandHandler' --include='*.java' --include='*.kt' --include='*.scala' . \
  | grep -v 'EventAppender'
```

## Notes

- **`.messaging.` infix is mandatory** — `org.axonframework.messaging.commandhandling.annotation.CommandHandler`.
  The path `org.axonframework.commandhandling.annotation.CommandHandler` does not exist.
- **`EventAppender` is required on aggregate and child entity handlers** — see [aggregate-lifecycle.md](aggregate-lifecycle.md).
  On non-aggregate components (event handlers, services) `@CommandHandler` is typically not used — apply this
  pattern only when the handler is inside an `@EventSourced`/`@EventSourcedEntity` class.
