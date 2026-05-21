# Use case 02 — DeadlineManager → Blocker with partial migration (comment out)

**Why interesting:** AF5 has no `DeadlineManager`. The recipe migrates the full saga structure (class, event handlers, state entity, repository) but cannot design the deadline replacement — that is a project-specific decision. Deadline code is commented out with TODO markers, and Blocker B1 is emitted so the caller can choose the replacement strategy.

## Before (AF4) — deadline-bearing saga

```java
@Saga
public class PaymentSagaWithDeadline {

    @Autowired private transient CommandGateway commandGateway;
    @Autowired private transient DeadlineManager deadlineManager;

    private String bikeId;
    private String renter;

    @StartSaga
    @SagaEventHandler(associationProperty = "bikeId")
    public void on(BikeRequestedEvent event) {
        this.bikeId = event.bikeId();
        this.renter = event.renter();
        SagaLifecycle.associateWith("paymentReference", event.rentalReference());
        commandGateway.send(new PreparePaymentCommand(10, event.rentalReference()));
    }

    @SagaEventHandler(associationProperty = "paymentReference")
    public void on(PaymentPreparedEvent event) {
        deadlineManager.schedule(Duration.ofSeconds(30), "cancelPayment", event.paymentId());
    }

    @EndSaga
    @SagaEventHandler(associationProperty = "paymentReference")
    public void on(PaymentConfirmedEvent event) {
        commandGateway.send(new ApproveRequestCommand(bikeId, renter));
    }

    @DeadlineHandler(deadlineName = "cancelPayment")
    public void cancelPayment(String paymentId) {
        commandGateway.send(new RejectPaymentCommand(paymentId));
    }
}
```

## After (AF5) — partial migration, deadline code commented out

```java
import org.axonframework.messaging.commandhandling.gateway.CommandDispatcher;
import org.axonframework.messaging.commandhandling.gateway.CommandGateway;
import org.axonframework.messaging.eventhandling.annotation.EventHandler;
import org.axonframework.messaging.eventhandling.replay.annotation.DisallowReplay;
import org.springframework.stereotype.Component;
// import org.axonframework.deadline.DeadlineManager;            // TODO AF5: removed — no equivalent
// import org.axonframework.deadline.annotation.DeadlineHandler; // TODO AF5: removed — no equivalent

@Component
@DisallowReplay
public class PaymentSagaWithDeadline {

    private final CommandGateway commandGateway;
    private final PaymentSagaWithDeadlineStateRepository repository;

    // TODO AF5: DeadlineManager removed — design replacement (e.g. @Scheduled poller on state entity)
    // private transient DeadlineManager deadlineManager;

    public PaymentSagaWithDeadline(CommandGateway commandGateway,
                                   PaymentSagaWithDeadlineStateRepository repository) {
        this.commandGateway = commandGateway;
        this.repository = repository;
    }

    @EventHandler
    public void on(BikeRequestedEvent event, CommandDispatcher commandDispatcher) {
        repository.save(new PaymentSagaWithDeadlineState(event.rentalReference(), event.bikeId(), event.renter()));
        commandDispatcher.send(new PreparePaymentCommand(10, event.rentalReference()));
    }

    @EventHandler
    public void on(PaymentPreparedEvent event) {
        repository.findById(event.paymentReference())
                  .ifPresent(state -> {
                      state.setStatus(PaymentSagaWithDeadlineState.Status.PREPARED);
                      // TODO AF5: schedule 30s deadline — deadlineManager.schedule(...) removed
                      // deadlineManager.schedule(Duration.ofSeconds(30), "cancelPayment", event.paymentId());
                  });
    }

    @EventHandler
    public void on(PaymentConfirmedEvent event, CommandDispatcher commandDispatcher) {
        repository.findById(event.paymentReference())
                  .ifPresent(state -> {
                      state.setStatus(PaymentSagaWithDeadlineState.Status.CONFIRMED);
                      commandDispatcher.send(new ApproveRequestCommand(state.bikeId(), state.renter()));
                  });
    }

    // TODO AF5: @DeadlineHandler has no AF5 equivalent — implement as @Scheduled poller or manual scheduler
    // @DeadlineHandler(deadlineName = "cancelPayment")
    // public void cancelPayment(String paymentId) {
    //     commandGateway.send(new RejectPaymentCommand(paymentId));
    // }
}
```

## What changed

- `@Saga` → `@Component @DisallowReplay` (saga structure fully migrated)
- `@SagaEventHandler` → `@EventHandler` with JPA repository lookup
- `SagaLifecycle.associateWith(...)` → implicit via `repository.save(new ...State(...))`
- `@EndSaga` → `@EventHandler` + `state.setStatus(CONFIRMED)`
- **`DeadlineManager` field commented out** with TODO
- **`deadlineManager.schedule(...)` call commented out** with TODO
- **`@DeadlineHandler` method commented out** with TODO block
- `CommandGateway` field kept (constructor-injected) — needed if caller adds `@Scheduled` poller later
- Two new files created: `PaymentSagaWithDeadlineState.java`, `PaymentSagaWithDeadlineStateRepository.java`
- Recipe emits **Blocker B1** — source is partially migrated; caller decides on deadline replacement

## What the caller should do next (solve-manually option)

1. Decide on a deadline replacement strategy. Common options:
   - **`@Scheduled` poller** (Spring): add `@Scheduled(fixedDelay = 1000)` method querying `findAllByTimestampLessThanAndStatusIn(cutoff, Status.PREPARED, Status.PENDING)`. Add `@EnableScheduling` to the Spring Boot app.
   - **`ScheduledExecutorService`** (native or Spring): wire manually; same polling logic applies.
2. Uncomment and adapt the TODO-marked blocks.
3. Re-invoke the saga recipe — it will re-check and proceed to Success.

## Caveats

- `CommandGateway` field is kept because the future `@Scheduled` poller cannot receive `CommandDispatcher` as a method parameter (pollers are not event handlers). This is intentional.
- The state entity already has a `timestamp` field and `findAllByTimestampLessThanAndStatusIn` repository method — ready to be used by the caller's `@Scheduled` poller.
- `DeadlineManager.cancelAllWithinScope(...)` in `@EndSaga` handlers is also commented out. The caller's poller will naturally skip terminal-status rows via `statusIn(PENDING, PREPARED)` predicate.
