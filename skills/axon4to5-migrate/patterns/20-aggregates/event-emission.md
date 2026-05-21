# Event Emission in Aggregates

AF4 used a `ThreadLocal`-backed static method `AggregateLifecycle.apply(event)` to publish events from inside
command handlers. AF5 removes `ThreadLocal` entirely; event publishing uses an `EventAppender` parameter injected
into every `@CommandHandler` method.

## Import Mappings

| AF4 | AF5 |
|-----|-----|
| `import static org.axonframework.modelling.command.AggregateLifecycle.apply` | *(remove)* |
| `org.axonframework.modelling.command.AggregateLifecycle` | *(remove)* |
| `org.axonframework.commandhandling.CommandHandler` | `org.axonframework.messaging.commandhandling.annotation.CommandHandler` |
| — | `org.axonframework.messaging.eventhandling.gateway.EventAppender` |

## Detection

```bash
grep -rn 'AggregateLifecycle\.apply\|import.*AggregateLifecycle\|import.*commandhandling\.CommandHandler' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

## Axon Framework 4 Code

```java
import static org.axonframework.modelling.command.AggregateLifecycle.apply;
import org.axonframework.commandhandling.CommandHandler;

@CommandHandler
public void handle(ShipOrderCommand cmd) {
    // validate...
    apply(new OrderShippedEvent(this.orderId, cmd.getAddress()));
}

@CommandHandler
@CreationPolicy(AggregateCreationPolicy.CREATE_IF_MISSING)
public void handle(CreateOrderCommand cmd) {
    apply(new OrderCreatedEvent(cmd.getOrderId()));
}
```

## Axon Framework 5 Code

```java
import org.axonframework.messaging.commandhandling.annotation.CommandHandler;
import org.axonframework.messaging.eventhandling.gateway.EventAppender;

@CommandHandler
public void handle(ShipOrderCommand cmd, EventAppender eventAppender) {
    // validate...
    eventAppender.append(new OrderShippedEvent(this.orderId, cmd.getAddress()));
}

@CommandHandler
@CreationPolicy(AggregateCreationPolicy.CREATE_IF_MISSING)
public void handle(CreateOrderCommand cmd, EventAppender eventAppender) {
    eventAppender.append(new OrderCreatedEvent(cmd.getOrderId()));
}
```

## Rules

1. **Every `@CommandHandler`** on the aggregate and on every child entity gets `EventAppender eventAppender` as
   its **last** parameter — including static factory handlers and constructor handlers.
2. Every `AggregateLifecycle.apply(event)` call becomes `eventAppender.append(event)`.
3. Remove the static import and the regular `AggregateLifecycle` import.

## Notes

- **`.messaging.` infix is mandatory** for both `@CommandHandler` and `EventAppender` — the paths without it
  do not exist.
- **Child entities**: every `@CommandHandler` on a child entity (`@EntityMember`) also needs `EventAppender`.
  The parent aggregate's `EventAppender` is NOT shared.
- **Static factory `@CommandHandler`**: still needs `EventAppender` as last parameter even though the method is static.
- **`EventAppender.append(…)` is one-event-at-a-time** — for multiple events use separate calls:
  `eventAppender.append(e1); eventAppender.append(e2);`
- **grep after migration**: `grep -rn 'AggregateLifecycle' …` — any surviving call is a compile error.
