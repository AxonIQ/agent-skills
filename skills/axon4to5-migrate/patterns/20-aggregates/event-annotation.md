# Event Class Annotations

AF5 requires event classes (records or regular classes) to carry the `@Event` annotation. The `@EventTag`
annotation on the routing field replaces the implicit `AggregateIdentifier` link. `@Revision` collapses
into `@Event(version = N)`.

## Import Mappings

| AF4 | AF5 |
|-----|-----|
| *(no class annotation)* | `org.axonframework.messaging.eventhandling.annotation.Event` |
| *(no field annotation for routing on events)* | `org.axonframework.eventsourcing.annotation.EventTag` |
| `@Revision("N")` | `@Event(version = N)` (attribute on `@Event`) |

## Detection

```bash
# Find event classes (usually records in the events/ package)
grep -rn '@Revision\|import.*eventhandling\.Event' --include='*.java' --include='*.kt' --include='*.scala' .
# Events without @Event annotation — after OpenRewrite; look for record/class in events packages
```

## Axon Framework 4 Code

```java
// No class-level annotation; revision via @Revision
@Revision("1")
public record OrderShippedEvent(
    String orderId,
    String address
) { }

// Plain event, no revision
public record OrderCreatedEvent(
    String orderId
) { }
```

## Axon Framework 5 Code

```java
import org.axonframework.messaging.eventhandling.annotation.Event;
import org.axonframework.eventsourcing.annotation.EventTag;

// With version
@Event(version = 1)
public record OrderShippedEvent(
    @EventTag(key = "Order")
    String orderId,
    String address
) { }

// Without version (default)
@Event
public record OrderCreatedEvent(
    @EventTag(key = "Order")
    String orderId
) { }
```

## Notes

- **`@Event` is required** — events without it are not recognized by AF5 handlers.
- **`@EventTag`** marks the field whose value is used as the aggregate routing key. Its `key` attribute must match
  the `tagKey` on the aggregate's `@EventSourced` annotation.
- **Every event type** routed to a specific aggregate must have `@EventTag` on the routing field, or the framework
  cannot match events to aggregate instances.
- **`@Revision("N")` → `@Event(version = N)`** — the version is now an `int` attribute, not a string annotation.
- **Pure value events** (not tied to any aggregate) still need `@Event`; they do not need `@EventTag`.
- **OpenRewrite status:** Full — `AddEventAnnotation` (in `axon4-to-axon5-eventsourcing.yml`) adds `@Event` to event payload types and migrates `@Revision("N")` → `@Event(version = "N")`; `AddEventTagAnnotation` (in `axon4-to-axon5-modelling.yml`) adds `@EventTag(key = "<EntitySimpleName>")` to the routing field.
- **Reference source:** `examples/java/af5/src/main/java/com/dddheroes/heroesofddd/armies/events/ArmyEvent.java`.
