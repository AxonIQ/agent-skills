# @EventSourcingHandler — Import Package Move

`@EventSourcingHandler` moved to a new package in AF5. The annotation's behavior is unchanged — it marks
methods that apply events to rebuild aggregate state from the event stream.

## Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.eventsourcing.EventSourcingHandler` | `org.axonframework.eventsourcing.annotation.EventSourcingHandler` |

## Detection

```bash
grep -rn 'import org.axonframework.eventsourcing.EventSourcingHandler' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

## Axon Framework 4 Code

```java
import org.axonframework.eventsourcing.EventSourcingHandler;

@EventSourcingHandler
public void on(OrderCreatedEvent event) {
    this.orderId = new OrderId(event.orderId());
}
```

## Axon Framework 5 Code

```java
import org.axonframework.eventsourcing.annotation.EventSourcingHandler;

@EventSourcingHandler
public void on(OrderCreatedEvent event) {
    this.orderId = new OrderId(event.orderId());
}
```

## Notes

- **Only the import changes** — the annotation itself, its semantics, and method signatures are identical.
- **`.annotation.` infix added** — `org.axonframework.eventsourcing.**annotation**.EventSourcingHandler`.
- Methods inside `@EventSourcingHandler` that call `event.getPayload()` / `event.getMetaData()` should be updated
  to `event.payload()` / `event.metaData()` — see [message-accessors pattern](../30-event-handlers/message-accessors.md).
