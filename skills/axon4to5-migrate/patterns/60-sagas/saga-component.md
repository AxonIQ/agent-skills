# Saga Migration — @Saga → @Component @DisallowReplay

AF4 used the `@Saga` annotation (both `org.axonframework.spring.stereotype.Saga` for Spring and
`org.axonframework.modelling.saga.Saga` for SPI). AF5 replaces this with a regular Spring `@Component`
annotated `@DisallowReplay`, backed by JPA persistence. The `@SagaEventHandler` annotation is replaced
by `@EventHandler`.

## Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.spring.stereotype.Saga` | *(remove)* |
| `org.axonframework.modelling.saga.Saga` | *(remove)* |
| `org.axonframework.modelling.saga.SagaEventHandler` | `org.axonframework.messaging.eventhandling.annotation.EventHandler` |
| `org.axonframework.modelling.saga.StartSaga` | *(remove — use `@EventHandler` for start)* |
| `org.axonframework.modelling.saga.EndSaga` | *(remove — close via lifecycle method)* |
| `org.axonframework.modelling.saga.SagaLifecycle` | *(remove)* |
| — | `@Component`, `@DisallowReplay` |

## Detection

```bash
grep -rn '@Saga\|import.*stereotype.Saga\|import.*modelling.saga' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

## Axon Framework 4 Code

```java
import org.axonframework.spring.stereotype.Saga;
import org.axonframework.modelling.saga.SagaEventHandler;
import org.axonframework.modelling.saga.StartSaga;
import org.axonframework.modelling.saga.EndSaga;
import org.axonframework.modelling.saga.SagaLifecycle;

@Saga
public class OrderFulfillmentSaga {

    @SagaEventHandler(associationProperty = "orderId")
    @StartSaga
    public void on(OrderPlacedEvent event) {
        SagaLifecycle.associateWith("orderId", event.orderId());
        // dispatch command...
    }

    @SagaEventHandler(associationProperty = "orderId")
    @EndSaga
    public void on(OrderDeliveredEvent event) {
        SagaLifecycle.end();
    }
}
```

## Axon Framework 5 Code

```java
import org.springframework.stereotype.Component;
import org.axonframework.messaging.eventhandling.annotation.EventHandler;
import org.axonframework.messaging.eventhandling.replay.annotation.DisallowReplay;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "order_fulfillment_saga")
@Component
@DisallowReplay
public class OrderFulfillmentSaga {

    @Id
    private String orderId;

    // JPA-persisted state fields
    private String status;

    protected OrderFulfillmentSaga() { } // JPA required

    @EventHandler
    public CompletableFuture<?> on(OrderPlacedEvent event, CommandDispatcher commandDispatcher) {
        this.orderId = event.orderId();
        this.status = "STARTED";
        // save via repository, then dispatch...
        return commandDispatcher.send(new ProcessPaymentCommand(event.orderId()))
            .getResultMessage();
    }

    @EventHandler
    public void on(OrderDeliveredEvent event) {
        this.status = "COMPLETED";
        // save final state
    }
}
```

## Architecture change: JPA persistence

AF5 sagas are **JPA entities** — the framework no longer manages saga state via its own store. You must:
1. Annotate the saga class with `@Entity` and `@Table`.
2. Add an `@Id` field for the correlation key.
3. Add a `protected` no-arg constructor for JPA.
4. Persist state changes manually using a Spring Data repository.
5. Load saga state in `@EventHandler` methods using the repository.

## Notes

- **`@SagaEventHandler(associationProperty = …)` → plain `@EventHandler`** — AF5 routes events to processors
  by namespace; load the saga state from JPA using the event's correlation field.
- **`SagaLifecycle.associateWith(…)` removed** — no equivalent; correlation is handled by the JPA lookup.
- **`SagaLifecycle.end()` removed** — mark the saga "done" via a field and stop persisting it, or delete the
  JPA entity.
- **`@StartSaga` / `@EndSaga` removed** — lifecycle is now expressed through JPA entity existence.
- **Deadline Manager (`@DeadlineHandler`)** — no AF5 equivalent yet; this is a blocker if used.
- **`SagaTestFixture` removed** — no AF5 test fixture replacement; tests using it cannot be automatically migrated.
