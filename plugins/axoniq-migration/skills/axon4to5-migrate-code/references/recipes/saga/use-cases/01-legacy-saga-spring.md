# Use case 01 - Existing Spring saga on legacy APIs

An AF4 saga uses two association keys and fire-and-forget command dispatch. The upgrade preserves both; it does not create a new JPA state model.

## Before (AF4, relevant fragment)

```java
@Saga
@ProcessingGroup("payments")
public class PaymentSaga {
    @Autowired
    private transient CommandGateway commandGateway;
    private String bikeId;

    @StartSaga
    @SagaEventHandler(associationProperty = "bikeId")
    public void on(BikeRequestedEvent event) {
        bikeId = event.bikeId();
        SagaLifecycle.associateWith("paymentReference", event.rentalReference());
        commandGateway.send(new PreparePaymentCommand(event.rentalReference()));
    }

    @EndSaga
    @SagaEventHandler(associationProperty = "paymentReference")
    public void on(PaymentConfirmedEvent event) {
        commandGateway.send(new ApproveRequestCommand(bikeId));
    }
}
```

## After (Axoniq Framework 5.4.0, relevant fragment)

```java
import org.axonframework.messaging.commandhandling.gateway.CommandDispatcher;
import org.axonframework.messaging.core.annotation.Namespace;
import org.axonframework.modelling.saga.EndSaga;
import org.axonframework.modelling.saga.SagaEventHandler;
import org.axonframework.modelling.saga.SagaLifecycle;
import org.axonframework.modelling.saga.StartSaga;
import org.axonframework.spring.stereotype.Saga;

@Saga
@Namespace("payments")
public class PaymentSaga {
    private String bikeId;

    @StartSaga
    @SagaEventHandler(associationProperty = "bikeId")
    public void on(BikeRequestedEvent event, SagaLifecycle lifecycle,
                   CommandDispatcher commandDispatcher) {
        bikeId = event.bikeId();
        lifecycle.associateWith("paymentReference", event.rentalReference());
        commandDispatcher.send(new PreparePaymentCommand(event.rentalReference()));
    }

    @EndSaga
    @SagaEventHandler(associationProperty = "paymentReference")
    public void on(PaymentConfirmedEvent event, CommandDispatcher commandDispatcher) {
        commandDispatcher.send(new ApproveRequestCommand(bikeId));
    }
}
```

Use `io.axoniq.framework:axoniq-legacy`, `axoniq-legacy-test` (test scope), and `axoniq-spring-boot-starter` for this baseline. These fragments assume the application's existing event and command classes. Preserve the saga's package and serialized fields; preserve the `payments` processor's existing token and store configuration.

Keep existing `SagaTestFixture<PaymentSaga>` tests and close the fixture after each test. Assert creation, association with `paymentReference`, command dispatch, and completion. Also test an AF4-persisted instance after restart before deployment; a newly constructed fixture does not establish persistence compatibility.

`@StartSaga` remains during source adaptation. The later workflow cutover controls when new saga starts stop.
