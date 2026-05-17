---
atom-id: event-sourcing-handler
title: "@EventSourcingHandler — import package move"
af4-symbols: ["org.axonframework.eventsourcing.EventSourcingHandler"]
af5-symbols: ["org.axonframework.eventsourcing.annotation.EventSourcingHandler"]
detect: grep -rn 'import org.axonframework.eventsourcing.EventSourcingHandler' --include='*.java' --include='*.kt' --include='*.scala' .
used-by: [aggregate]
---

# @EventSourcingHandler — Import Package Move

The `@EventSourcingHandler` annotation moved from the root `eventsourcing` package to the `eventsourcing.annotation`
sub-package. Method signatures and behaviour are unchanged.

## Detect

```bash
grep -rn 'import org\.axonframework\.eventsourcing\.EventSourcingHandler' --include='*.java' --include='*.kt' --include='*.scala' .
```

## Transform

**Remove:**
```java
import org.axonframework.eventsourcing.EventSourcingHandler;
```

**Add:**
```java
import org.axonframework.eventsourcing.annotation.EventSourcingHandler;
```

The annotation usage on methods (`@EventSourcingHandler`) is unchanged — only the import changes.

## Full example

```java
// AF4
import org.axonframework.eventsourcing.EventSourcingHandler;

public class Order {
    @EventSourcingHandler
    protected void on(OrderCreatedEvent event) {
        this.orderId = event.getOrderId();
    }
}

// AF5
import org.axonframework.eventsourcing.annotation.EventSourcingHandler;

public class Order {
    @EventSourcingHandler
    protected void on(OrderCreatedEvent event) {
        this.orderId = event.getOrderId();
    }
}
```

## Gotchas

- **OpenRewrite Phase 1 usually fixes this import** — grep before and after to confirm. If already migrated, skip.
- **Do not confuse with `@EventHandler`** — `@EventSourcingHandler` is for aggregate state evolution (applied
  after a command publishes an event). `@EventHandler` is for projectors/processors. Different packages, different
  components.
- **Accessor renames inside handler body** — AF5 events are records: `event.getPayload()` → `event.payload()`,
  `event.getMetaData()` → `event.metadata()`. This is covered by the [[message-accessors]] atom if needed, but
  `@EventSourcingHandler` bodies typically access domain fields directly, not `Message` API methods.

## Used By

- **[[aggregate]]** — common steps (always)
