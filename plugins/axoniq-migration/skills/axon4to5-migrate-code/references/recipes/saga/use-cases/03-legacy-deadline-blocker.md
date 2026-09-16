# Use case 03 - Saga with deadlines: Blocker B1

**Why interesting:** `axon-legacy` ports the saga APIs but **not** `DeadlineManager`, `@DeadlineHandler` or the event
scheduler (upstream issue #5006). Everything else about the saga is a clean legacy-module migration - the deadline is
the one part that cannot come along, and its replacement is a design decision the recipe cannot make.

**Apply-condition:** B0 resolved to `axon-legacy` AND
`grep -nE '@DeadlineHandler|DeadlineManager|EventScheduler|deadlineManager\.' $SOURCE` matches. Under
`stateful-rewrite` a deadline is not a blocker - see [05-rewrite-deadline-comment-out.md](05-rewrite-deadline-comment-out.md).

## The saga

```java
@Saga
public class PaymentSagaWithDeadline {

    @Autowired private transient CommandGateway commandGateway;
    @Autowired private transient DeadlineManager deadlineManager;

    private String bikeId;
    private String deadlineId;

    @StartSaga
    @SagaEventHandler(associationProperty = "bikeId")
    public void on(BikeRequestedEvent event) {
        this.bikeId = event.bikeId();
        SagaLifecycle.associateWith("paymentReference", event.rentalReference());
        this.deadlineId = deadlineManager.schedule(Duration.ofSeconds(30), "cancelPayment");
        commandGateway.send(new PreparePaymentCommand(10, event.rentalReference()));
    }

    @DeadlineHandler(deadlineName = "cancelPayment")
    public void onTimeout() {
        commandGateway.send(new RejectRequestCommand(bikeId));
        SagaLifecycle.end();
    }
}
```

## Why this halts

`org.axonframework.deadline.DeadlineManager` and `org.axonframework.deadline.annotation.DeadlineHandler` do not exist
on AF5 and are not in `axon-legacy`, so the file does not compile once the AF4 dependencies are gone. Both
continuations are legitimate and they differ in what breaks:

| Option | Saga runs on AF5 | Timeout still fires |
|---|---|---|
| `skip` *(Recommended)* | no - drains in the AF4 deployment | yes |
| `comment-out-deadlines` | yes | **no** - until the caller wires a scheduler |

`skip` is recommended precisely because the alternative is a **silent** behavioural regression: the saga keeps
receiving events and looks healthy while its compensation path is dead. Under `auto=true` the orchestrator takes the
recommendation, so a deadline-bearing saga is never auto-disabled.

## Under `comment-out-deadlines`

The `axon-legacy` Toolbox steps apply as usual; additionally, comment out - never delete - each of:

```java
// TODO AF5: no deadline support in axon-legacy yet (#5006) - design the replacement
// @Autowired private transient DeadlineManager deadlineManager;

// TODO AF5: no deadline support in axon-legacy yet (#5006)
// this.deadlineId = deadlineManager.schedule(Duration.ofSeconds(30), "cancelPayment");

// TODO AF5: no deadline support in axon-legacy yet (#5006) - reimplement as a scheduled sweep sending a command
// @DeadlineHandler(deadlineName = "cancelPayment")
// public void onTimeout() { ... }
```

Keep the `org.axonframework.deadline.*` imports as comments too, so the caller can see what was there. Commented-out
code is exempt from Success Criterion 2's static-`SagaLifecycle` grep - it is not code.

`sagas.adoc` § "Migrating deadlines" describes the AF5 replacement shape: a scheduling library of the caller's choice
plus a `CommandGateway` field (that method is not an event handler, so it cannot take a `CommandDispatcher`
parameter), with an idempotent command handler absorbing a deadline that fires for a process that already moved on.

## The saga's test breaks at runtime, not at compile time

`axon-legacy-test` declares the AF4 deadline fixture methods so an AF4 test suite still compiles, but the bodies throw:

```
UnsupportedOperationException: [whenTimeElapses] is not supported: deadlines and the event scheduler have not been
ported into axon-legacy yet, see #5006. Everything else the Axon Framework 4 saga fixture offered works.
```

So a `SagaTestFixture` test calling `whenTimeElapses(...)` / `expectScheduledDeadline(...)` compiles green and fails
red. Report it in NOTES together with the B1 decision; the other assertions in the same fixture are unaffected.

## What did NOT happen

- No `@Scheduled` poller, no state entity, no scheduler bean - designing the replacement is explicitly out of scope.
- No deadline code deleted. Commenting out preserves the intent for whoever designs the replacement.
