# Recipe: saga (per-saga decision: migrate or stay AF4)

AF5 has **no `Saga` SPI**. There is no automatic rewrite. But many AF4 sagas — especially the simple "wait for events, dispatch commands, track state in fields" shape — are *technically* migratable to an **event handler with state** pattern: a `@Component` with `@EventHandler` methods + a JPA-backed state repository + a domain-specific scheduler when timeouts are needed.

This recipe runs **per saga**. For each saga, the user chooses one of three outcomes; recipe records the decision and (when the choice is `migrate-to-event-handler-with-state`) hands the saga to the user's editor — there is no automatic transformation, only a worked-example reference.

## Canonical reference

- [../../docs/paths/index.adoc](../../docs/paths/index.adoc) §"What is not yet there" — confirms Saga & Deadline overhaul is in progress; **no automatic Saga migration target**.
- [../../docs/paths/test-fixtures.adoc](../../docs/paths/test-fixtures.adoc) — `SagaTestFixture` has no AF5 replacement yet; testing implications when user picks `accept-stays-af4`.

This recipe holds the per-saga decision flow and the "event handler with state" worked example.

## Two migration shapes — pick by state-storage requirement

AF5 offers **two** event-handler-with-state shapes. Both are valid; pick by how saga state must be persisted.

### Shape A — `@InjectEntity` + event-sourced state (recommended when saga state can be reconstructed from events)

A `@Component` with `@EventHandler` methods receives the saga's state via `@InjectEntity` on a nested **event-sourced** entity. The entity is annotated `@EventSourced` and rebuilds its fields by replaying the same events that drive the saga. No JPA, no separate saga store — state lives in the event stream.

**Use when:** saga state is derivable purely from past domain events (i.e., the events the saga already listens to carry every field it needs) **and** all those events originate from a single bounded context (one event stream / one aggregate type as the source of truth for the saga's id). This is the common case.

**Don't use when:**
- saga state depends on data **not** in the event stream (external API results, time-based state machines without an event trigger) — go to Shape B.
- the saga is **cross-context**: it consumes events from multiple bounded contexts / multiple aggregate types with no shared correlation id. `@InjectEntity` loads exactly one state entity by one id resolved from the event payload — if every event class carries a different id field with no common entity behind them, the injection model breaks. Go to Shape B (manual repository lookup per event) or split into per-context sagas.

### Shape B — `@Component` + JPA state repository (when state must be queryable or has fields not derivable from events)

A `@Component` with `@EventHandler` methods writes/reads a JPA-backed `*State` entity through a Spring Data `JpaRepository`. Used when state must be queryable on a timestamp/status index (e.g., to drive a `ScheduledExecutorService` sweep replacing `DeadlineManager`).

**Use when:** the saga needs **deadline replacement** via own scheduler, has fields not derivable from the events it consumes, or needs cross-row queries (`findAllByTimestampLessThan...`).

## When migration to event-handler-with-state is feasible

| Saga property | Migrate? | Which shape |
|---|---|---|
| Reacts to a fixed set of events; dispatches commands; tracks status in saga fields that are all carried by those events; events all originate from a single bounded context | **Yes** | **Shape A** (`@InjectEntity` + `@EventSourced` state) — simplest |
| Cross-context saga — consumes events from multiple bounded contexts / aggregate types with no shared correlation id | **Yes** | **Shape B** (manual repository lookup per handler) — Shape A's single-id injection model doesn't fit |
| Tracks fields not carried by the saga's events (external results, computed deadlines) | **Yes** | **Shape B** (JPA `*State` entity + repository) |
| Uses `@DeadlineHandler` / `DeadlineManager.schedule(...)` | **Conditional** | **Shape B** with own `ScheduledExecutorService` + JPA timestamp poll; or keep on AF4, or wait for Axoniq Workflows. Contact Axoniq for consultancy. |
| Heavy use of `SagaLifecycle.end()` / `@EndSaga` flow control | **Maybe** | Both shapes — translate to state transitions (`Status.CANCELLED`, terminal field on the entity); a sweep/handler ignores terminal state |
| Cross-saga coordination, association-property routing across many saga instances | **No** | Process-manager territory; wait for Axoniq Workflows, or contact Axoniq for consultancy |
| Custom `SagaStore` / persistence config | **No** | Saga storage stays AF4; out of scope here |

The recipe never auto-transforms. The user is the architect; this recipe surfaces the choice and the reference shape.

## Goal

Per saga, record one of: `migrate-to-event-handler-with-state` / `accept-stays-af4` / `pause-migration` / `remove-feature-first`. When the user picks migrate, point at the worked example below and exit — the actual rewrite is the user's job, with the example as the reference.

## Inputs

- target: FQ saga class name (required when invoked in single mode; informational when invoked from INIT triage)

## Preflight

There is no "already migrated" path — once a saga has been ported to `@Component` + repository, it's an event processor and the saga grep won't match it any more. Always proceeds straight to the decision flow.

## Procedure

1. Detect deadline blocker (delegates to the same logic as `aggregate/not-supported.md` B5):
   ```bash
   grep -RnE '@DeadlineHandler|DeadlineManager|DeadlineMessage|deadlineManager\.schedule|cancelSchedule|cancelAllWithinScope' \
        --include='*.java' --include='*.kt' <saga file> <saga package>
   ```
   If hits → set `decisions.deadline-handler-in-saga = present`. Migration to event-handler-with-state is **not feasible** without an out-of-band deadline replacement.

2. Detect saga shape signals:
   - `@Saga`, `@SagaEventHandler`, `@StartSaga`, `@EndSaga` annotations.
   - `SagaLifecycle.end(...)` / `SagaLifecycle.associateWith(...)` static calls.
   - `@SagaEventHandler(associationProperty = "...")` association mechanics — the strongest signal that AF5 has no direct equivalent (associations are saga-store concepts).

3. AskUserQuestion — choose one:

   - `migrate-to-event-handler-with-state` *(recommended only when step 1 found NO deadline hit AND step 2 association mechanics are simple)* — recipe exits with a pointer to the worked example below; user re-runs the orchestrator on the rewritten class as an `event-processor` recipe target.
     - Sub-choice — pick the shape:
       - `shape-a-injected-event-sourced-state` — when saga state is fully derivable from the events the saga consumes. See **Worked example A** below.
       - `shape-b-jpa-state-with-scheduler` — when state has fields not derivable from events, or you need to replace deadlines with an own scheduler. See **Worked example B** below.
   - `accept-stays-af4` — saga code stays AF4; will fail to compile under AF5 deps in the affected slice. Stabilization must exclude the saga files from the AF5 build path.
   - `pause-migration` — stop; user removes the saga (or its deadline dependency) first.
   - `remove-feature-first` — user accepts they will redesign the saga as a plain projection / event-handler-with-state before resuming.

4. Append a dated narrative entry to `learnings.md` recording the decision, the saga FQN, and the reason.

5. Emit Output. The orchestrator commits a decision-only record (`recipe: saga`, `decisions: [saga: <choice>]`).

## Worked example A — `@InjectEntity` + event-sourced state (Spring Boot, AF5)

The simpler pattern when saga state is fully derivable from the events the saga consumes. AF5 reconstructs the state entity on-demand by replaying past events (event sourcing), then injects it into the `@EventHandler` method via `@InjectEntity`. No JPA, no separate state table, no manual repository.

### How `@InjectEntity` loads the state entity (single-context only)

When an `@EventHandler` method has an `@InjectEntity SomeState state` parameter, AF5 does the following **per incoming event**, before the handler body runs:

1. **Resolve the entity id from the event payload.** Resolution order (see `InjectEntity.java`):
   1. `@InjectEntity(idProperty = "x")` — read field/getter `x` on the event payload.
   2. `@InjectEntity(idResolver = MyResolver.class)` — call a custom `EntityIdResolver`.
   3. Default `AnnotationBasedEntityIdResolver` — find a `@TargetEntityId`-annotated field/accessor on the event payload.
2. **Load the entity** through the `StateManager` using that id. For an `@EventSourced` entity this means: open the event stream filtered to that id (the tag/stream the entity declared, e.g. `@EventSourced(tagKey = "bikeId")`), call the `@EntityCreator` constructor, replay every matching past event through `@EventSourcingHandler` methods, hand the rebuilt entity to the saga method.
3. **Invoke the handler** with the loaded entity injected as the parameter.

Implication — **the entity is loaded from one stream, identified by one id, sourced from one context**:

- All events the saga consumes must carry the same correlation key (or be reachable from it via `idProperty` / a custom resolver) — otherwise different events would resolve to different entity ids and the saga sees inconsistent state.
- All those events must belong to the same event stream / context that the `@EventSourced` state entity is built from. `@InjectEntity` does not merge streams or fan-in across contexts.
- The state entity replays the events that drive the saga, so every field the saga reads from the entity must come from `@EventSourcingHandler` methods on events in that single stream.

If the saga needs to react to events from another context (say, a `PaymentConfirmedEvent` from a payment-context aggregate alongside a `BikeRequestedEvent` from a rental-context aggregate), one of two things must be true:

- The cross-context events all carry a shared correlation id that maps to one logical state entity (then Shape A still works — both streams are tagged with the same id and the entity is rebuilt by replaying both).
- Or they don't (then go to Shape B and load state manually per handler).

This is why Shape A is documented as "single bounded context, single correlation id, events all derivable into one state entity". `@InjectEntity` is an entity-loading mechanism, not a cross-context join.

### Key annotations

- `@EventHandler` on the saga component method (from `org.axonframework.messaging.eventhandling.annotation`).
- `@InjectEntity` (from `org.axonframework.modelling.annotation`) on the state-entity parameter — AF5 loads the entity using the message's id resolution (see `idProperty` / `@TargetEntityId`).
- `@EventSourced` (from `org.axonframework.extension.spring.stereotype`) on the state-entity class — declares it event-sourced and Spring-discoverable.
- `@EntityCreator` (from `org.axonframework.eventsourcing.annotation.reflection`) on the entity constructor that AF5 calls to instantiate the entity before replay.
- `@EventSourcingHandler` (from `org.axonframework.eventsourcing.annotation`) on entity methods that fold events into entity fields.
- `CommandDispatcher` (from `org.axonframework.messaging.commandhandling.gateway`) as a parameter on the handler method — replaces autowired `CommandGateway` for in-context dispatch.

### AF4 saga (before)

```java
@Saga
public class PaymentSaga {

    @Autowired
    private transient CommandGateway commandGateway;

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

### AF5 migrated component (after)

```java
import org.axonframework.eventsourcing.annotation.EventSourcingHandler;
import org.axonframework.eventsourcing.annotation.reflection.EntityCreator;
import org.axonframework.extension.spring.stereotype.EventSourced;
import org.axonframework.messaging.commandhandling.gateway.CommandDispatcher;
import org.axonframework.messaging.eventhandling.annotation.EventHandler;
import org.axonframework.modelling.annotation.InjectEntity;
import org.springframework.stereotype.Component;

@Component
public class PaymentSaga {

    @EventHandler
    public void on(BikeRequestedEvent event,
                   @InjectEntity PaymentProcessState state,
                   CommandDispatcher commandDispatcher) {
        commandDispatcher.send(new PreparePaymentCommand(10, event.rentalReference()));
    }

    @EventHandler
    public void on(PaymentConfirmedEvent event,
                   @InjectEntity PaymentProcessState state,
                   CommandDispatcher commandDispatcher) {
        commandDispatcher.send(new ApproveRequestCommand(state.bikeId(), state.renter()));
    }

    @EventHandler
    public void on(PaymentRejectedEvent event,
                   @InjectEntity PaymentProcessState state,
                   CommandDispatcher commandDispatcher) {
        commandDispatcher.send(new RejectRequestCommand(state.bikeId(), state.renter()));
    }

    @EventSourced
    public static class PaymentProcessState {

        private String bikeId;
        private String renter;

        @EntityCreator
        PaymentProcessState() { }

        @EventSourcingHandler
        public void handle(BikeRequestedEvent event) {
            this.bikeId = event.bikeId();
            this.renter = event.renter();
        }

        public String bikeId()  { return bikeId; }
        public String renter()  { return renter; }
    }
}
```

### Wiring (no Spring — `EventSourcingConfigurer`)

```java
var paymentProcessState = EventSourcedEntityModule
        .autodetected(String.class, PaymentSaga.PaymentProcessState.class);

PooledStreamingEventProcessorModule sagaProcessor = EventProcessorModule
        .pooledStreaming("SagaProcessor")
        .eventHandlingComponents(c ->
                c.autodetected("PaymentSaga", cfg -> new PaymentSaga())
        ).notCustomized();

var configurer = EventSourcingConfigurer.create()
        .registerEntity(paymentProcessState)
        .modelling(m -> m.messaging(msg -> msg.eventProcessing(ep ->
                ep.pooledStreaming(ps -> ps.processor(sagaProcessor))
        )));
```

With Spring Boot the auto-config discovers the `@EventSourced` entity and the `@Component`-annotated saga automatically; only the processor binding remains explicit.

### Test (AxonTestFixture — replaces `SagaTestFixture`)

```java
class PaymentSagaAxon5Test {

    private AxonTestFixture fixture;

    @BeforeEach
    void setUp() {
        var paymentSaga = EventSourcedEntityModule
                .autodetected(String.class, PaymentSaga.PaymentProcessState.class);

        var commandHandlerModule = CommandHandlingModule.named("PaymentSaga")
                .commandHandlers()
                .autodetectedCommandHandlingComponent(c -> new BikeCommands());

        PooledStreamingEventProcessorModule sagaProcessor = EventProcessorModule
                .pooledStreaming("SagaProcessor")
                .eventHandlingComponents(c ->
                        c.autodetected("PaymentSaga", cfg -> new PaymentSaga()))
                .notCustomized();

        var configurer = EventSourcingConfigurer.create()
                .modelling(c -> c.messaging(m ->
                        m.registerCommandHandlingModule(commandHandlerModule)))
                .registerEntity(paymentSaga)
                .modelling(m -> m.messaging(msg -> msg.eventProcessing(ep ->
                        ep.pooledStreaming(ps -> ps.processor(sagaProcessor)))));

        fixture = AxonTestFixture.with(
                configurer,
                AxonTestFixture.Customization::disableAxonServer
        );
    }

    @AfterEach
    void tearDown() { fixture.stop(); }

    @Test
    void shouldStartSagaOnBikeRequested() {
        fixture.given()
               .events(new BikeRequestedEvent("bikeId", "renter", "payRef"))
               .then()
               .commands(new PreparePaymentCommand(10, "payRef"));
    }
}
```

Note: `SagaTestFixture` has no direct AF5 replacement (see `references/migrated/axon5/bikerental-extended/...` and migration docs). Use `AxonTestFixture` with an `EventSourcingConfigurer` that registers the saga's state entity + a `PooledStreamingEventProcessorModule` wrapping the saga component, then assert with `.given().events(...)` → `.then().commands(...)`.

### What changed vs the AF4 saga (Shape A)

| AF4 saga element | AF5 `@InjectEntity` + event-sourced state replacement |
|---|---|
| `@Saga` + saga store | `@Component` + `@EventSourced` nested state class (no saga store) |
| Saga-state fields (`private String bikeId; private String renter;`) | Same fields on a nested `@EventSourced` state class, reconstructed by `@EventSourcingHandler` from past events |
| `@StartSaga` | First event for that entity id triggers `@EntityCreator` constructor + replay → state implicitly "starts" |
| `@EndSaga` | Drop the annotation; either track a terminal flag in the state, or rely on no further events being routed by id |
| `@SagaEventHandler(associationProperty = "x")` | `@InjectEntity` + `@TargetEntityId` on the message payload's field (or `idProperty = "x"` on `@InjectEntity`) |
| `SagaLifecycle.associateWith("paymentReference", ...)` | The state entity for `paymentReference` is loaded by `@InjectEntity` using the event's id field — no manual association registration |
| Autowired `CommandGateway` (field) | `CommandDispatcher` resolved as a handler-method parameter — scoped to the processing context |
| `SagaTestFixture` | `AxonTestFixture` over an `EventSourcingConfigurer` that registers the state entity + event processor |

### Caveats specific to Shape A

- **Single-context only.** Shape A is **not** for cross-context sagas. `@InjectEntity` loads one state entity by one id resolved from the message — it cannot fan out across events from unrelated contexts. If the saga listens to events from multiple bounded contexts / aggregate types, use Shape B (or split into one Shape A saga per context).
- **Identity in events.** Every event the saga reacts to must carry the entity id used to load the state (or you must configure `@InjectEntity(idProperty = "...")` / a custom `EntityIdResolver`). If the AF4 saga used different association properties on different events (the bike-rental example associated by `bikeId` on `BikeRequestedEvent` and by `paymentReference` afterwards), the migrated state entity needs **one** stable id — either redesign events to carry a single correlation key, or split into two state entities.
- **No deadlines.** This shape has no deadline mechanism. If the saga uses `@DeadlineHandler` / `DeadlineManager`, either pick Shape B (own scheduler) or contact AxonIQ.
- **Replay safety.** Event handlers on the saga component dispatch commands — annotate the component with `@DisallowReplay` (`org.axonframework.messaging.eventhandling.replay.annotation.DisallowReplay`) if a replay would re-emit commands. The state entity's `@EventSourcingHandler` methods are pure folds; they are safe to replay.
- **Storage stays event-sourced.** State has no JPA row; reconstruction cost is "replay all relevant events on every load". Acceptable for short-lived sagas (request → confirm/reject); not acceptable for long-tail sagas with thousands of events per instance — for those use Shape B or snapshots.

## Worked example B — `@Component` + JPA state + own scheduler (Spring Boot, AF5)

A real migrated saga from a bike-rental project. The AF4 `PaymentSaga` (event association by `paymentReference`, deadlines for late-payment cancellation) became a Spring `@Component` with `@EventHandler` methods, a JPA `PaymentState` entity for the per-payment row, and a `ScheduledExecutorService` plus a timestamp-indexed JPA poll **in lieu of `DeadlineManager`**. The deadlines did NOT migrate — they were redesigned as an own scheduler driven by the JPA row's timestamp.

Use the snippets below as a structural reference. The user adapts to their domain — the recipe does NOT auto-rewrite.

### State entity (JPA)

```java
import jakarta.persistence.Entity;
import jakarta.persistence.Id;

@Entity
public class PaymentState {
    @Id
    private String paymentReference;
    private Status status;
    private long timestamp;
    private String paymentId;

    public PaymentState() { }

    public PaymentState(String paymentReference) {
        this.paymentReference = paymentReference;
        this.status = Status.PENDING;
        this.timestamp = System.currentTimeMillis();
    }

    public String paymentReference() { return paymentReference; }
    public Status status() { return status; }
    public String paymentId() { return paymentId; }
    public void prepared(String paymentId) { this.status = Status.PREPARED; this.paymentId = paymentId; }
    public void setStatus(Status status) { this.status = status; }

    public enum Status { PENDING, PREPARED, CONFIRMED, REJECTED, CANCELLED }
}
```

### Repository (Spring Data JPA)

```java
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

@Repository
public interface PaymentStateRepository extends JpaRepository<PaymentState, String> {

    List<PaymentState> findAllByTimestampLessThanAndStatusIn(long timestamp, PaymentState.Status... status);

    @Modifying
    @Transactional(propagation = Propagation.MANDATORY)
    @Query("UPDATE PaymentState p SET p.status = :status WHERE p.paymentReference = :paymentReference")
    void updateStatus(String paymentReference, PaymentState.Status status);

    @Modifying
    @Transactional(propagation = Propagation.MANDATORY)
    @Query("UPDATE PaymentState p SET p.status = :status, p.paymentId = :paymentId WHERE p.paymentReference = :paymentReference")
    void updateStatusAndPaymentId(String paymentReference, String paymentId, PaymentState.Status status);

    @Query("SELECT MIN(p.timestamp) FROM PaymentState p WHERE p.status IN :statuses")
    Optional<Long> findEarliestActiveTimestamp(@Param("statuses") List<PaymentState.Status> statuses);
}
```

### Migrated component (event handler with state)

```java
import org.axonframework.messaging.commandhandling.gateway.CommandDispatcher;
import org.axonframework.messaging.commandhandling.gateway.CommandGateway;
import org.axonframework.messaging.eventhandling.annotation.EventHandler;
import org.axonframework.messaging.eventhandling.replay.annotation.DisallowReplay;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.time.Duration;
import java.util.List;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;

@Component
@DisallowReplay
public class PaymentSaga {

    private static final Duration PAYMENT_TIMEOUT = Duration.ofSeconds(10);

    private final CommandGateway commandGateway;
    private final PaymentStateRepository repository;
    private final ScheduledExecutorService scheduler;
    private final AtomicReference<ScheduledFuture<?>> scheduledCheck = new AtomicReference<>();

    public PaymentSaga(CommandGateway commandGateway,
                       PaymentStateRepository repository,
                       ScheduledExecutorService workerExecutorService) {
        this.commandGateway = commandGateway;
        this.repository = repository;
        this.scheduler = workerExecutorService;
    }

    @EventListener(ApplicationReadyEvent.class)
    public void onApplicationReady() {
        scheduleNextCheck();
    }

    @EventHandler
    public void on(BikeRequestedEvent event, CommandDispatcher commandDispatcher) {
        repository.save(new PaymentState(event.rentalReference()));
        commandDispatcher.send(new PreparePaymentCommand(10, event.rentalReference()));
        ScheduledFuture<?> current = scheduledCheck.get();
        if (current == null || current.isDone()) {
            scheduleNextCheck();
        }
    }

    @EventHandler
    public void on(PaymentConfirmedEvent event, CommandDispatcher commandDispatcher) {
        repository.updateStatus(event.paymentReference(), PaymentState.Status.CONFIRMED);
        commandDispatcher.send(new ApproveRequestCommand(event.paymentReference()));
    }

    @EventHandler
    public void on(PaymentRejectedEvent event, CommandDispatcher commandDispatcher) {
        repository.updateStatus(event.paymentReference(), PaymentState.Status.REJECTED);
        commandDispatcher.send(new RejectRequestCommand(event.paymentReference()));
    }

    @EventHandler
    public void on(PaymentPreparedEvent event) {
        repository.updateStatusAndPaymentId(event.paymentReference(), event.paymentId(), PaymentState.Status.PREPARED);
    }

    @Transactional
    public void cancelLatePayments() {
        long cutoffTime = System.currentTimeMillis() - PAYMENT_TIMEOUT.toMillis();
        repository.findAllByTimestampLessThanAndStatusIn(cutoffTime, PaymentState.Status.PREPARED, PaymentState.Status.PENDING)
                  .forEach(state -> {
                      if (state.paymentId() != null) {
                          commandGateway.send(new RejectPaymentCommand(state.paymentId()));
                      } else {
                          repository.updateStatus(state.paymentReference(), PaymentState.Status.CANCELLED);
                          commandGateway.send(new RejectRequestCommand(state.paymentReference()));
                      }
                  });
        scheduleNextCheck();
    }

    private void scheduleNextCheck() {
        repository.findEarliestActiveTimestamp(List.of(PaymentState.Status.PENDING, PaymentState.Status.PREPARED))
                  .ifPresent(earliestTimestamp -> {
                      long delay = earliestTimestamp + PAYMENT_TIMEOUT.toMillis() - System.currentTimeMillis();
                      scheduledCheck.set(scheduler.schedule(this::cancelLatePayments, Math.max(delay, 0), TimeUnit.MILLISECONDS));
                  });
    }
}
```

### What changed vs the AF4 saga (Shape B)

| AF4 saga element | AF5 event-handler-with-state replacement |
|---|---|
| `@Saga`, `@SagaEventHandler`, `@StartSaga`, `@EndSaga` | `@Component` + `@EventHandler` (AF5 import); state-machine transitions in the JPA row's `Status` column |
| Association property routing (`@SagaEventHandler(associationProperty = "x")`) | Repository lookup by primary key — events must carry the correlation key (`paymentReference` here); load + branch in the handler body |
| `SagaLifecycle.end()` | `repository.updateStatus(ref, Status.<terminal>)` — sweep ignores terminal rows |
| Saga-state fields (`private String paymentRef; private boolean confirmed;`) | JPA `@Entity` with same fields, persisted on every transition |
| `DeadlineManager.schedule(...)` + `@DeadlineHandler` | Own `ScheduledExecutorService` + JPA timestamp poll (`findEarliestActiveTimestamp` + `findAllByTimestampLessThanAndStatusIn`) |
| Saga store config (`SagaConfigurer`, `@SagaStore` bean) | Standard Spring Data JPA repository — no AF5 saga config needed |

### Caveats specific to Shape B

- The component is annotated `@DisallowReplay` because it dispatches commands. Without it, replay re-emits every payment cycle.
- The `ScheduledExecutorService` is **not** persisted across restarts — `onApplicationReady()` re-arms the next sweep from the JPA `MIN(timestamp)` query. Restart is safe; in-flight delays are absorbed by the next poll.
- Timestamp-driven polling is coarser than `DeadlineManager`. Acceptable when the SLA is "minutes, not milliseconds". Surface this trade-off to the user — it is *not* a 1:1 deadline replacement.
- For Path B (framework Configurer, no Spring), substitute Spring Data with a hand-rolled JPA DAO and replace `@Component` / `@Transactional` with the equivalent `EventSourcingConfigurer.componentRegistry(...)` + `EventSourcedEntityModule`-free registration.

## End condition

Never green automatically — there is no compile-time check the recipe can run. The orchestrator commits the user's recorded decision; the actual saga rewrite (when `migrate-to-event-handler-with-state` is picked) is a follow-up the user runs through the `event-processor` recipe afterwards.

## Output

Emit exactly one fenced ```yaml block per the six-variant Output contract
([../output-contract.md](../output-contract.md)). The saga recipe is a
top-level `not-supported` mode — it NEVER emits `result: success` because
this recipe does not produce an AF5 rewrite by itself; the follow-up
rewrite (when the user picks `migrate-to-event-handler-with-state`) runs
under the `event-processor` recipe.

Mapping:

| AskUserQuestion answer | `result:` | `caller-expects.next` |
|---|---|---|
| (not yet answered) | `needs-decision` | `ask-user` |
| `accept-stays-af4` | `blocked` | `record-and-skip` |
| `pause-migration` | `blocked` | `record-and-skip` |
| `remove-feature-first` | `blocked` | `record-and-skip` |
| `migrate-to-event-handler-with-state` | `blocked` | `route-to:event-processor` |

```yaml
result: needs-decision | blocked
target: <FQ saga class | file list | "n/a">
reason: <one short line — e.g. "saga detected; user picked accept-stays-af4" / "saga has @DeadlineHandler — four-way choice required">
decisions:
  saga: <migrate-to-event-handler-with-state | accept-stays-af4 | pause-migration | remove-feature-first | pending>
  shape: <shape-a-injected-event-sourced-state | shape-b-jpa-state-with-scheduler | n/a>   # only when saga = migrate
  deadline-handler-in-saga: <none | present>     # if `present` then shape must be `shape-b-jpa-state-with-scheduler` (or surface as a follow-up)
caller-expects:
  commit: <true | false>
  next: <ask-user | record-and-skip | route-to:event-processor>
notes: |
  Free text — when migrate, name the target component class the user will
  create and the nested state-entity class (Shape A) or JPA entity +
  repository (Shape B); when accept-stays-af4, list which AF4 deps stay;
  for needs-decision, list the verbatim AskUserQuestion options.
```

## Caveats

- Even with `accept-stays-af4`, sagas reference AF4-only types (`SagaConfigurer`, `@StartSaga`, `org.axonframework.modelling.saga.*`). Stabilization MUST exclude these files from the AF5 build path or the project won't compile.
- A saga that depends on `DeadlineManager` cannot be cleanly migrated to the event-handler-with-state pattern without an out-of-band deadline replacement (own scheduler, Spring `@Scheduled`, Quartz, or wait for Axoniq Workflows). Surface this trade-off; do not silently drop the deadlines.
- If AxonIQ Workflows ships with a saga → workflow migration path, this recipe will gain a fourth option (`migrate-to-axoniq-workflow`) and a separate worked example. Until then, contact Axoniq for consultancy on complex sagas.

## When this recipe will be replaced

When AxonIQ ships official workflow support and a saga → workflow migration guide. At that point this recipe gains an `iterative` migration mode for that path; the event-handler-with-state option stays available for the simple case.
