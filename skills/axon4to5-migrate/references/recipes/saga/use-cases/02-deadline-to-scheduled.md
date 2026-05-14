# Use case 02 — DeadlineManager → @Scheduled poller (Spring)

**Why interesting:** AF5 has no `DeadlineManager`. The only viable Spring replacement is a `@Scheduled` polling method that reads expired rows from the JPA state table. Shows how `@DeadlineHandler` methods collapse into one poller and how the JPA state entity stores the timeout timestamp.

## Before (AF4) — deadline-related parts

```java
@Autowired private transient DeadlineManager deadlineManager;

@SagaEventHandler(associationProperty = "paymentReference")
public void on(PaymentPreparedEvent event) {
    // schedule a 30-second timeout; if it fires, reject the payment
    deadlineManager.schedule(Duration.ofSeconds(30), "cancelPayment", event.paymentId());
}

@DeadlineHandler(deadlineName = "cancelPayment")
public void cancelPayment(String paymentId) {
    commandGateway.send(new RejectPaymentCommand(paymentId));
}
```

## After (AF5)

### Changes to PaymentSaga.java

```java
import org.axonframework.messaging.commandhandling.gateway.CommandGateway;
import org.springframework.scheduling.annotation.Scheduled;

@Component
@DisallowReplay
public class PaymentSaga {

    private final CommandGateway commandGateway;      // used by @Scheduled poller only
    private final PaymentStateRepository repository;

    public PaymentSaga(CommandGateway commandGateway, PaymentStateRepository repository) {
        this.commandGateway = commandGateway;
        this.repository = repository;
    }

    // ... other @EventHandler methods use CommandDispatcher parameter, not commandGateway field ...

    @EventHandler
    public void on(PaymentPreparedEvent event) {
        // record the "prepared" timestamp so the poller can detect expiry
        repository.findById(event.paymentReference())
                  .ifPresent(state -> state.prepared(event.paymentId()));
    }

    @Scheduled(fixedDelay = 1000)
    public void cancelLatePayments() {
        long cutoffTime = System.currentTimeMillis() - Duration.ofSeconds(30).toMillis();
        repository.findAllByTimestampLessThanAndStatusIn(
                cutoffTime,
                PaymentState.Status.PREPARED,
                PaymentState.Status.PENDING
        ).forEach(state -> {
            if (state.paymentId() != null) {
                commandGateway.send(new RejectPaymentCommand(state.paymentId()));
            }
        });
    }
}
```

### Changes to PaymentState.java — add `prepared()` + `paymentId` field

```java
private String paymentId;
private long preparedTimestamp;   // set when status transitions to PREPARED

public void prepared(String paymentId) {
    this.paymentId = paymentId;
    this.status = Status.PREPARED;
    this.preparedTimestamp = System.currentTimeMillis();  // starts the clock
}

public String paymentId() { return paymentId; }
```

### PaymentStateRepository — add expiry query

```java
List<PaymentState> findAllByTimestampLessThanAndStatusIn(long timestamp, PaymentState.Status... status);
```

The `timestamp` field to query against should be whichever field tracks "when the timeout started". Use `preparedTimestamp` if timeouts only fire from PREPARED state, or a unified `timestamp` field populated on creation.

## What changed

- `DeadlineManager` field removed; `@Autowired private transient DeadlineManager deadlineManager` deleted.
- `@DeadlineHandler` method removed; its body moves into the `@Scheduled` poller.
- `deadlineManager.schedule(duration, "name", payload)` call removed from the start handler; replaced by storing the current timestamp in the JPA state (`state.prepared(paymentId)`).
- One `@Scheduled(fixedDelay = N)` method replaces all `@DeadlineHandler` methods. `fixedDelay` should be ≤ 1/10 of the shortest deadline duration (e.g. 30s deadline → 1000ms poll).
- The cutoff: `System.currentTimeMillis() - deadlineDuration.toMillis()`.
- `CommandGateway` field **kept** because `@Scheduled` methods are not event handlers and cannot receive `CommandDispatcher` as a parameter.

## Caveats

- `@Scheduled` requires `@EnableScheduling` on the Spring Boot application class (or any `@Configuration` class). The recipe must flag this in Result NOTES if not already present.
- Polling granularity is coarser than `DeadlineManager`. A 30s deadline with 1s poll means ±1s accuracy — acceptable for most business flows but not millisecond-precise retry loops.
- Multiple `@DeadlineHandler` methods (e.g., `cancelPayment`, `retryPayment`) each need their own expiry field + status predicate in the poller or separate `@Scheduled` methods.
- Deadlines re-armed from the DB on startup: existing PREPARED rows will be found by the poller after restart. Ensure the compensating command is idempotent.
- `DeadlineManager.cancelAllWithinScope("name")` (used in some `@EndSaga` handlers to cancel pending deadlines) has no direct equivalent. Dropping deadlines is safe because the poller only fires for in-flight states — when `@EndSaga` deleted the row or set a terminal status, the poller's `statusIn(PREPARED, PENDING)` query skips it automatically.
