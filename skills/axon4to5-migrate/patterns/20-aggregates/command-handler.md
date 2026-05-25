# @CommandHandler — Import Move + EventAppender Parameter

The `@CommandHandler` annotation moved to the `messaging.commandhandling.annotation` package. Every `@CommandHandler`
on an aggregate or child entity must also receive an `EventAppender` as its last parameter (see
[aggregate-lifecycle.md](aggregate-lifecycle.md)).

## Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.commandhandling.CommandHandler` | `org.axonframework.messaging.commandhandling.annotation.CommandHandler` |

## Detection

**Pre-migration (AF4 original):**

```bash
grep -rn 'import org\.axonframework\.commandhandling\.CommandHandler' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

**Post-OpenRewrite (partial AF5 shape):**

```bash
grep -rn '@CommandHandler' --include='*.java' --include='*.kt' --include='*.scala' . \
  | grep -v 'EventAppender'   # candidates — review each: legitimately param-less, or missed by OR?
```

Use the AF4 grep during Step 2 Assessment to scope the work. Use the post-OR grep during Step 4 Validate when the compile loop points at this pattern.

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

OR moves the import and (via `ReplaceAggregateLifecycleApply` in `axon4-to-axon5-eventsourcing.yml`) injects `EventAppender` into every handler that called `AggregateLifecycle.apply(...)`. Two AI follow-up cases remain:

- **Handlers that did not emit events in AF4** (validation-only, throw on bad state) are left without `EventAppender` — correct as-is unless you intend to start emitting events.
- **Aggregate handlers whose event emission was indirect** (via a helper method, base class, or `applyEvents(...)` loop OR's predicate didn't catch) — add `EventAppender eventAppender` as the **last** parameter and the `org.axonframework.messaging.eventhandling.gateway.EventAppender` import, then rewrite the body per [aggregate-lifecycle.md](aggregate-lifecycle.md). Do NOT touch the already-correct `@CommandHandler` import.

```bash
grep -rn '@CommandHandler' --include='*.java' --include='*.kt' --include='*.scala' . \
  | grep -v 'EventAppender'   # candidates — review each: legitimately param-less, or missed by OR?
```

## Notes

- **`.messaging.` infix is mandatory** — `org.axonframework.messaging.commandhandling.annotation.CommandHandler`.
  The path `org.axonframework.commandhandling.annotation.CommandHandler` does not exist.
- **`EventAppender` is required on aggregate and child entity handlers** — see [aggregate-lifecycle.md](aggregate-lifecycle.md).
  On non-aggregate components (event handlers, services) `@CommandHandler` is typically not used — apply this
  pattern only when the handler is inside an `@EventSourced`/`@EventSourcedEntity` class.
- **OpenRewrite status:** Partial — `ChangeType` (in `axon4-to-axon5-messaging.yml`) moves the import; `EventAppender` is added only on handlers that called `AggregateLifecycle.apply(...)` — AI adds the parameter on remaining aggregate handlers.
