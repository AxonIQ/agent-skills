# AggregateLifecycle.apply() → EventAppender.append()

AF4 used a `ThreadLocal`-backed static method `AggregateLifecycle.apply(event)` to publish events from inside
`@CommandHandler` methods. AF5 removes `ThreadLocal` entirely — an `EventAppender` is injected as a method
parameter into every `@CommandHandler`.

## Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.modelling.command.AggregateLifecycle` | *(remove)* |
| `static org.axonframework.modelling.command.AggregateLifecycle.apply` | *(remove)* |
| — | `org.axonframework.messaging.eventhandling.gateway.EventAppender` |

## Detection

```bash
grep -rn 'AggregateLifecycle\.apply\|import.*AggregateLifecycle' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

## Axon Framework 4 Code

```java
import static org.axonframework.modelling.command.AggregateLifecycle.apply;

@CommandHandler
public void handle(ShipOrderCommand cmd) {
    apply(new OrderShippedEvent(orderId, cmd.getAddress()));
}
```

## Axon Framework 5 Code

```java
import org.axonframework.messaging.eventhandling.gateway.EventAppender;

@CommandHandler
public void handle(ShipOrderCommand cmd, EventAppender eventAppender) {
    eventAppender.append(new OrderShippedEvent(orderId, cmd.getAddress()));
}
```

## Rules

1. Every `@CommandHandler` on the aggregate (and child entities) gets `EventAppender eventAppender` as its **last** parameter.
2. Every `AggregateLifecycle.apply(event)` becomes `eventAppender.append(event)`.
3. Remove both the static import and the regular import for `AggregateLifecycle`.
4. Static `@CommandHandler` factory methods also receive `EventAppender` as a parameter — static methods can receive injected parameters.

## Notes

- **`.messaging.` infix is mandatory** — `org.axonframework.messaging.eventhandling.gateway.EventAppender`. The path without `.messaging.` does not exist.
- **Do not call `AggregateLifecycle.markDeleted()`** — there is no AF5 equivalent; remove the call entirely.
