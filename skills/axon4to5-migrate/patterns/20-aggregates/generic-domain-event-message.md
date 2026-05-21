# GenericDomainEventMessage Removal

AF4 exposed `GenericDomainEventMessage` for constructing event messages with aggregate metadata (type,
sequence). AF5 removes this class — aggregate events are appended through `EventAppender` which sets the
aggregate context automatically. Where direct `GenericDomainEventMessage` construction was used (typically
in test setup or infrastructure code), use `GenericEventMessage` instead.

## Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.messaging.eventhandling.GenericDomainEventMessage` | `org.axonframework.messaging.eventhandling.GenericEventMessage` |
| `org.axonframework.domain.GenericDomainEventMessage` | `org.axonframework.messaging.eventhandling.GenericEventMessage` |

## Detection

```bash
grep -rn 'GenericDomainEventMessage' --include='*.java' --include='*.kt' --include='*.scala' .
```

## Axon Framework 4 Code

```java
import org.axonframework.messaging.eventhandling.GenericDomainEventMessage;

// In test setup — constructing a past event
GenericDomainEventMessage<OrderCreatedEvent> message =
    new GenericDomainEventMessage<>("Order", orderId.toString(), 0,
        new OrderCreatedEvent(orderId));
```

## Axon Framework 5 Code

```java
import org.axonframework.messaging.eventhandling.GenericEventMessage;

// GenericEventMessage — aggregate context is not required in AF5 event construction
GenericEventMessage<OrderCreatedEvent> message =
    new GenericEventMessage<>(new OrderCreatedEvent(orderId));
```

## Notes

- In **aggregate code**, you never construct event messages directly — use `EventAppender.append(event)` instead.
- In **test fixtures** (`AxonTestFixture`), pass the plain event object to `given().events(...)` — no wrapper needed.
- In **infrastructure / replay** code that reads raw events, use `GenericEventMessage` if a wrapper is still required.
- `GenericDomainEventMessage` carried `aggregateType` and `sequenceNumber`; `GenericEventMessage` does not.
  If your code reads those fields, revisit whether you still need them in AF5.
