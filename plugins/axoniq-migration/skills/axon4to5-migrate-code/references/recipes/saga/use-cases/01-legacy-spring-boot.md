# Use case 01 - Spring Boot saga onto `axon-legacy`

**Why interesting:** the canonical case. The saga class survives - same annotations, same association values, same
saga-store rows. Four things change: lifecycle calls, command dispatch, the injected collaborator, and
`@ProcessingGroup`. The first two come from the OpenRewrite legacy pass; the last two are this recipe's manual work.

**Apply-condition:** B0 resolved to `axon-legacy` AND `configuration=spring` AND `$SOURCE` has no `DeadlineManager`
/ `@DeadlineHandler`.

## Before (AF4)

```java
@Saga
@ProcessingGroup("rentals")
public class PaymentSaga {

    @Autowired private transient CommandGateway commandGateway;
    @Autowired private transient PricingService pricingService;

    private String bikeId;
    private String renter;

    @StartSaga
    @SagaEventHandler(associationProperty = "bikeId")
    public void on(BikeRequestedEvent event) {
        this.bikeId = event.bikeId();
        this.renter = event.renter();
        SagaLifecycle.associateWith("paymentReference", event.rentalReference());
        commandGateway.send(new PreparePaymentCommand(pricingService.priceFor(event.bikeId()),
                                                     event.rentalReference()));
    }

    @EndSaga
    @SagaEventHandler(associationProperty = "paymentReference")
    public void on(PaymentConfirmedEvent event) {
        commandGateway.sendAndWait(new ApproveRequestCommand(bikeId, renter));
    }
}
```

## After (AF5, `axon-legacy`)

```java
@Saga
@Namespace("rentals")
public class PaymentSaga {

    private String bikeId;
    private String renter;

    @StartSaga
    @SagaEventHandler(associationProperty = "bikeId")
    public void on(BikeRequestedEvent event,
                   SagaLifecycle sagaLifecycle,
                   CommandDispatcher commandDispatcher,
                   PricingService pricingService) {
        this.bikeId = event.bikeId();
        this.renter = event.renter();
        sagaLifecycle.associateWith("paymentReference", event.rentalReference());
        commandDispatcher.send(new PreparePaymentCommand(pricingService.priceFor(event.bikeId()),
                                                        event.rentalReference()));
    }

    @EndSaga
    @SagaEventHandler(associationProperty = "paymentReference")
    public void on(PaymentConfirmedEvent event, CommandDispatcher commandDispatcher) {
        FutureUtils.joinAndUnwrap(
                commandDispatcher.send(new ApproveRequestCommand(bikeId, renter)).getResultMessage()
        );
    }
}
```

Imports: `SagaLifecycle` keeps `org.axonframework.modelling.saga.SagaLifecycle`; `CommandDispatcher` is
`org.axonframework.messaging.commandhandling.gateway.CommandDispatcher`; `FutureUtils` is
`org.axonframework.common.FutureUtils`; `Namespace` is `org.axonframework.messaging.core.annotation.Namespace`.

## What changed, and who did it

| Change | Done by |
|---|---|
| `axon-legacy` added to the module's build file | OpenRewrite (`Axon4ToAxon5Legacy`) |
| `SagaLifecycle.associateWith(...)` -> `sagaLifecycle.associateWith(...)` + parameter | OpenRewrite |
| `CommandGateway` field -> `CommandDispatcher` parameter; field and `@Autowired` deleted | OpenRewrite |
| `sendAndWait(...)` -> `FutureUtils.joinAndUnwrap(...send(...).getResultMessage())` | OpenRewrite |
| `PricingService` field -> handler parameter (Step 4) | **this recipe** |
| `@ProcessingGroup("rentals")` -> `@Namespace("rentals")` (Step 6) | rename by OpenRewrite; **value preservation verified by this recipe** |

## Build file

```xml
<dependency>
    <groupId>org.axonframework</groupId>
    <artifactId>axon-legacy</artifactId>
</dependency>
<dependency>
    <groupId>org.axonframework</groupId>
    <artifactId>axon-legacy-test</artifactId>
    <scope>test</scope>
</dependency>
```

`axon-legacy` next to `axon-spring-boot-starter` is all the wiring there is - autoconfiguration discovers the
component-scanned `@Saga` bean, gives it a processor named after `@Namespace` ("rentals"), and resolves a `SagaStore`
from the context (`JpaSagaStore` when an `EntityManagerFactory` is present). `axon-legacy-test` is only needed because
of the test below.

## The existing test keeps its fixture, and gains an `@AfterEach`

```java
class PaymentSagaTest {

    private final SagaTestFixture<PaymentSaga> fixture = new SagaTestFixture<>(PaymentSaga.class);

    @AfterEach                      // <-- the one required change
    void tearDown() {
        fixture.close();
    }

    @Test
    void preparesPaymentOnRequest() {
        fixture.givenNoPriorActivity()
               .whenPublishingA(new BikeRequestedEvent("bike-1", "renter-1", "rental-1"))
               .expectDispatchedCommands(new PreparePaymentCommand(10, "rental-1"));
    }
}
```

`axon-legacy-test` ports `SagaTestFixture` under its AF4 package `org.axonframework.test.saga`, given-when-then API
included. Do NOT rewrite this to `AxonTestFixture`.

The `@AfterEach` is not optional. In AF5 the fixture runs a started `AxonConfiguration` with a live event processor and
implements `AutoCloseable`; the AF4 fixture held nothing that needed stopping. Without the close, the test still
compiles and still passes - the processor simply keeps running after it.

## What did NOT happen

- No state entity, no repository, no `@Component` / `@EventHandler` rewrite - the saga keeps its AF4 shape.
- `@StartSaga` left in place. The saga still creates new instances; stopping that is the caller's drainage decision.
- The `bikeId` / `renter` fields left in place - that is the saga's own state, and it is what the `SagaStore`
  serializes.
- `@ProcessingGroup`'s value not touched. `"rentals"` is the token-store key; renaming it would strand in-flight sagas.

## NOTES to emit

Name the drainage follow-up, and flag that `PricingService` moved from a field to a handler parameter - Axon now
resolves it per invocation instead of Spring injecting it once.
