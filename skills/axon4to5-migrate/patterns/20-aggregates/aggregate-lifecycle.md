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

## Partial migration state (post-OpenRewrite)

OR does not rewrite `AggregateLifecycle.apply(...)` call sites — they remain after the bulk pass, sometimes mixed with hand-edited handlers that already use `eventAppender.append(...)`. Common half-state in one class:

```java
@CommandHandler
public void handleA(CmdA cmd, EventAppender eventAppender) {
    eventAppender.append(new EventA());          // already migrated
}

@CommandHandler
public void handleB(CmdB cmd) {                  // EventAppender param missing
    AggregateLifecycle.apply(new EventB());      // still AF4
}
```

Minimal fix: for each handler still calling `AggregateLifecycle.apply(...)`, add the `EventAppender eventAppender` parameter (per [command-handler.md](command-handler.md)) and rewrite only the `apply(...)` lines that are still there. Do NOT re-rewrite handlers already using `eventAppender.append(...)`. Once every site is converted, drop the `AggregateLifecycle` import.

```bash
grep -rn 'AggregateLifecycle\.apply\|import .*AggregateLifecycle' --include='*.java' --include='*.kt' --include='*.scala' .
```

## Notes

- **`.messaging.` infix is mandatory** — `org.axonframework.messaging.eventhandling.gateway.EventAppender`. The path without `.messaging.` does not exist.
- **Do not call `AggregateLifecycle.markDeleted()`** — there is no AF5 equivalent; remove the call entirely.
