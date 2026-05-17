---
atom-id: saga-event-handler
title: "@SagaEventHandler/@StartSaga/@EndSaga → @EventHandler + JPA state lookup; SagaLifecycle removed"
af4-symbols: ["@SagaEventHandler", "@StartSaga", "@EndSaga", "SagaLifecycle", "org.axonframework.modelling.saga.SagaEventHandler", "org.axonframework.modelling.saga.StartSaga", "org.axonframework.modelling.saga.EndSaga", "org.axonframework.modelling.saga.SagaLifecycle"]
af5-symbols: ["@EventHandler", "org.axonframework.messaging.eventhandling.annotation.EventHandler"]
detect: grep -rn 'SagaEventHandler\|StartSaga\|EndSaga\|SagaLifecycle' --include='*.java' .
used-by: [saga]
---

# @SagaEventHandler → @EventHandler + JPA State Lookup

AF5 removed the Saga SPI. `@SagaEventHandler`, `@StartSaga`, `@EndSaga`, and `SagaLifecycle.*` are all gone.
Each handler becomes a plain `@EventHandler` that manages state via a JPA entity (created by the saga recipe's
Steps 2–3).

## Annotation mapping

| AF4 | AF5 |
|-----|-----|
| `@StartSaga @SagaEventHandler(associationProperty = "X")` | `@EventHandler` — body creates and saves a new state entity |
| `@SagaEventHandler(associationProperty = "X")` | `@EventHandler` — body loads state by `event.X()` |
| `@EndSaga @SagaEventHandler(associationProperty = "X")` | `@EventHandler` — body loads state and sets terminal status (or deletes) |

## SagaLifecycle replacements

| AF4 | AF5 |
|-----|-----|
| `SagaLifecycle.associateWith("key", value)` | REMOVE — state lookup uses the event's natural field |
| `SagaLifecycle.removeAssociationWith("key", value)` | REMOVE |
| `SagaLifecycle.end()` | REMOVE — set terminal status on state entity, or call `repository.deleteById(...)` |
| `SagaLifecycle.associateWith("secondaryKey", value)` | Store `value` as a field on the state entity |

## Import changes

Remove:
```java
import org.axonframework.modelling.saga.SagaEventHandler;
import org.axonframework.modelling.saga.StartSaga;
import org.axonframework.modelling.saga.EndSaga;
import org.axonframework.modelling.saga.SagaLifecycle;
```

Add:
```java
import org.axonframework.messaging.eventhandling.annotation.EventHandler;
```

## Transform example — start handler

```java
// AF4
@StartSaga
@SagaEventHandler(associationProperty = "orderId")
public void on(OrderPlacedEvent event) {
    SagaLifecycle.associateWith("orderId", event.orderId());
    commandGateway.sendAndWait(new ReservePaymentCommand(event.orderId(), event.amount()));
}

// AF5
@EventHandler
public CompletableFuture<?> on(OrderPlacedEvent event, CommandDispatcher commandDispatcher) {
    repository.save(new PaymentState(event.orderId(), event.amount()));
    return commandDispatcher.send(new ReservePaymentCommand(event.orderId(), event.amount()));
}
```

## Transform example — middle handler

```java
// AF4
@SagaEventHandler(associationProperty = "orderId")
public void on(PaymentReservedEvent event) {
    SagaLifecycle.end();
}

// AF5
@EventHandler
public void on(PaymentReservedEvent event) {
    PaymentState state = repository.findById(event.orderId()).orElseThrow();
    state.setStatus(PaymentState.Status.CONFIRMED);
    repository.save(state);
}
```

## In-handler command dispatch

Every `@EventHandler` that dispatches commands gets `CommandDispatcher commandDispatcher` as a method
parameter — see [[command-dispatcher]] atom for the full field-removal + async dispatch transformation.

## Gotchas

- **All four imports must be removed** — `SagaEventHandler`, `StartSaga`, `EndSaga`, and `SagaLifecycle`. A single lingering import causes a compile error.
- **AF4 saga fields become repository lookups** — instance fields like `private String bikeId;` are replaced by fields on the JPA entity. Every handler that read those fields must load the entity first.
- **`SagaLifecycle.associateWith("secondaryKey", value)`** — store `value` as a field on the JPA state entity in the start handler; subsequent handlers look it up via `repository.findById(event.secondaryKey())`.
- **`associationProperty` → event field accessor** — the AF4 `associationProperty` string told the framework which field to use for routing. In AF5, the handler reads `event.X()` directly and uses it to look up the state entity.
- **Message accessor renames** — if handler bodies use `event.getPayload()` / `event.getMetaData()`, apply [[message-accessors]] atom.

## Used By

- **[[saga]]** — Step 4 (always)
