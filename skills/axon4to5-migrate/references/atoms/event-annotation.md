---
atom-id: event-annotation
title: "Event classes — @Event annotation + @EventTag + @Revision removal"
af4-symbols: ["@Revision", "org.axonframework.serialization.Revision"]
af5-symbols: ["@Event", "@EventTag", "org.axonframework.messaging.eventhandling.annotation.Event", "org.axonframework.eventsourcing.annotation.EventTag"]
detect: grep -rn '@EventSourcingHandler' --include='*.java' . | xargs grep -ln 'getOrderId\|apply(' # find event classes
used-by: [aggregate]
---

# Event Classes — @Event + @EventTag + @Revision Removal

AF4 event classes were plain POJOs (optionally with `@Revision` for versioning). AF5 requires a class-level `@Event`
annotation, a property carrying `@EventTag` to enable aggregate-stream filtering, and replaces `@Revision` with
`@Event(version = "…")`.

## Detect event classes in scope

Identify them by inspecting `@EventSourcingHandler` first-parameter types on the aggregate. Each of those types is
an event class in scope.

## Transform

### 1. Add `@Event` to the class

```java
// AF4
public class OrderCreatedEvent {
    private final OrderId orderId;
    private final String customerId;
}

// AF5
import org.axonframework.messaging.eventhandling.annotation.Event;

@Event
public class OrderCreatedEvent {
    private final OrderId orderId;
    private final String customerId;
}
```

### 2. Add `@EventTag` to the aggregate-identifying property

Identify which property the AF4 `@AggregateIdentifier` field was set **from** inside an `@EventSourcingHandler`:

```java
// AF4 @EventSourcingHandler on aggregate:
@EventSourcingHandler
protected void on(OrderCreatedEvent event) {
    this.orderId = event.getOrderId();  // ← orderId is the property to tag
}
```

Then annotate that property on the event class:

```java
import org.axonframework.eventsourcing.annotation.EventTag;

@Event
public class OrderCreatedEvent {

    @EventTag(key = "Order")          // key = tagKey from @EventSourced on the aggregate
    private final OrderId orderId;

    private final String customerId;
}
```

**Without DCB, exactly one `@EventTag` per event.**

### 3. `@Revision` → `@Event(version = "…")`

**Remove:**
```java
import org.axonframework.serialization.Revision;

@Revision("2")
public class OrderCreatedEvent { … }
```

**Replace with:**
```java
@Event(version = "2")
public class OrderCreatedEvent { … }
```

## Imports

| AF5 annotation | Import |
|---|---|
| `@Event` | `org.axonframework.messaging.eventhandling.annotation.Event` |
| `@EventTag` | `org.axonframework.eventsourcing.annotation.EventTag` |

## `@EventTag` key rule

The `key` in `@EventTag(key = "…")` must match the `tagKey` in `@EventSourced(tagKey = "…")` on the aggregate
**exactly** (case-sensitive). Mismatch means the event is not associated with the aggregate stream and the entity
cannot be sourced.

## Multiple aggregates sharing the same event

When an event is published by more than one aggregate type (e.g., `OrderCreatedEvent` used by both `Order` and
`TrialOrder`), the event needs one `@EventTag` per aggregate type. Use DCB in that scenario — this recipe preserves
the **without-DCB** path, so if you encounter this, raise it as a blocker rather than silently adding multiple
`@EventTag` annotations.

## Gotchas

- **`@EventTag` key is case-sensitive** — must equal the `tagKey` on `@EventSourced`/`@EventSourcedEntity`.
- **Without DCB = exactly one `@EventTag`** — adding two breaks aggregate-stream isolation.
- **`@Revision` is fully gone in AF5** — the import does not exist; OpenRewrite usually removes it. Grep to confirm.
- **Events outside aggregate scope** — events referenced only by projectors or sagas are migrated by those recipes.
  Do not add `@Event` / `@EventTag` to events outside the current aggregate's scope.

## Used By

- **[[aggregate]]** — common steps, Step: "Events" (for each event class in scope)
