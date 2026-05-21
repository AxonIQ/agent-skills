# Use case 01 — JPA state shape (Spring, no deadlines)

**Why interesting:** demonstrates full structural rewrite of an AF4 `@Saga` to `@Component @DisallowReplay` with JPA-backed state. Shows that three things change together: the saga class itself, a new state entity, and a new repository. No deadline handling in this case.

## Before (AF4)

```java
@Saga
public class PaymentSaga {

    @Autowired private transient CommandGateway commandGateway;

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

    @EndSaga
    @SagaEventHandler(associationProperty = "paymentReference")
    public void on(PaymentConfirmedEvent event) {
        commandGateway.send(new ApproveRequestCommand(bikeId, renter));
    }

    @EndSaga
    @SagaEventHandler(associationProperty = "paymentReference")
    public void on(PaymentRejectedEvent event) {
        commandGateway.send(new RejectRequestCommand(bikeId, renter));
    }
}
```

## After (AF5)

### PaymentSaga.java (rewritten)

```java
import org.axonframework.messaging.commandhandling.gateway.CommandDispatcher;
import org.axonframework.messaging.commandhandling.gateway.CommandGateway;
import org.axonframework.messaging.eventhandling.annotation.EventHandler;
import org.axonframework.messaging.eventhandling.replay.annotation.DisallowReplay;
import org.springframework.stereotype.Component;

@Component
@DisallowReplay
public class PaymentSaga {

    private final PaymentStateRepository repository;

    public PaymentSaga(PaymentStateRepository repository) {
        this.repository = repository;
    }

    @EventHandler
    public void on(BikeRequestedEvent event, CommandDispatcher commandDispatcher) {
        repository.save(new PaymentState(event.rentalReference(), event.bikeId(), event.renter()));
        commandDispatcher.send(new PreparePaymentCommand(10, event.rentalReference()));
    }

    @EventHandler
    public void on(PaymentConfirmedEvent event, CommandDispatcher commandDispatcher) {
        repository.findById(event.paymentReference()).ifPresent(state -> {
            state.setStatus(PaymentState.Status.CONFIRMED);
            commandDispatcher.send(new ApproveRequestCommand(state.bikeId(), state.renter()));
        });
    }

    @EventHandler
    public void on(PaymentRejectedEvent event, CommandDispatcher commandDispatcher) {
        repository.findById(event.paymentReference()).ifPresent(state -> {
            state.setStatus(PaymentState.Status.REJECTED);
            commandDispatcher.send(new RejectRequestCommand(state.bikeId(), state.renter()));
        });
    }
}
```

### PaymentState.java (new file — same package)

```java
import jakarta.persistence.Entity;
import jakarta.persistence.Id;

@Entity
public class PaymentState {

    @Id
    private String paymentReference;
    private String bikeId;
    private String renter;
    private Status status;
    private long timestamp;

    public PaymentState() {}

    public PaymentState(String paymentReference, String bikeId, String renter) {
        this.paymentReference = paymentReference;
        this.bikeId = bikeId;
        this.renter = renter;
        this.status = Status.PENDING;
        this.timestamp = System.currentTimeMillis();
    }

    public String paymentReference() { return paymentReference; }
    public String bikeId() { return bikeId; }
    public String renter() { return renter; }
    public Status status() { return status; }
    public void setStatus(Status status) { this.status = status; }

    public enum Status { PENDING, CONFIRMED, REJECTED }
}
```

### PaymentStateRepository.java (new file — same package)

```java
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface PaymentStateRepository extends JpaRepository<PaymentState, String> {
    List<PaymentState> findAllByTimestampLessThanAndStatusIn(long timestamp, PaymentState.Status... status);
}
```

## What changed

- `@Saga` → `@Component @DisallowReplay`
- Saga fields (`bikeId`, `renter`) → fields in `PaymentState` entity
- `@StartSaga @SagaEventHandler(associationProperty = "bikeId")` → `@EventHandler` saves a new `PaymentState` row (the `paymentReference` / correlation key becomes the JPA `@Id`)
- `SagaLifecycle.associateWith("paymentReference", value)` → implicit: the state entity is looked up by the correlation key (`event.paymentReference()`)
- `@EndSaga @SagaEventHandler(...)` → `@EventHandler` updates state status (or deletes row)
- `CommandGateway` field removed; `CommandDispatcher commandDispatcher` added as method parameter on each `@EventHandler`
- Two new files created: `PaymentState.java` (`@Entity`) and `PaymentStateRepository.java` (`JpaRepository`)

## Caveats

- Processor wiring: the migrated `@Component` must be registered as an event processor. For Spring, add a `@Bean EventProcessorDefinition` in the `@Configuration` class (see `projectors-event-processors.adoc`). Without it, the handlers are auto-assigned to the default processor which may conflict with other components.
- `@DisallowReplay` prevents double-processing of state-creating handlers during event replay. Required.
- The JPA entity needs a no-arg constructor for Hibernate (add `public PaymentState() {}`).
- `CommandDispatcher` is injected per-handler by the framework via `ProcessingContext`. Not available in `@Scheduled` methods — use `CommandGateway` field there.
