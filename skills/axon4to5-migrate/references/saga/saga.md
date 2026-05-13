# Recipe: saga (per-saga decision)

AF5 has **no `Saga` SPI** — no automatic rewrite. Many AF4 sagas (the "wait for events, dispatch commands, track state in fields" shape) are migratable to an event-handler-with-state pattern, but the user is the architect — this recipe surfaces the choice and worked examples.

Runs per saga. For each: pick one of four outcomes; recipe records the decision. When `migrate-to-event-handler-with-state`, the user follows the worked example; the actual rewrite then runs through the `event-processor` recipe.

## Two migration shapes

### Shape A — `@InjectEntity` + `@EventSourced` state

A `@Component` with `@EventHandler` methods receives saga state via `@InjectEntity` on a nested **event-sourced** state class. The entity rebuilds its fields by replaying past events. No JPA, no separate saga store.

**Use when:** state is fully derivable from the events the saga consumes, **and** events all originate from a single bounded context (one event stream, one correlation id).

**Don't use when:** state has fields not in events / cross-context with no shared correlation id / needs deadline replacement.

### Shape B — `@Component` + JPA state + own scheduler

A `@Component` with `@EventHandler` methods writes/reads a JPA-backed `*State` entity through a Spring Data `JpaRepository`. Used when state must be queryable on a timestamp/status index (e.g., to drive a `ScheduledExecutorService` sweep replacing `DeadlineManager`).

**Use when:** needs deadline replacement via own scheduler, fields not in events, or cross-row queries.

## Migration feasibility matrix

| AF4 saga property | Migrate? | Shape |
|---|---|---|
| Reacts to fixed events, dispatches commands, state from those events, single bounded context | **Yes** | A |
| Cross-context: events from multiple contexts / aggregates with no shared correlation id | **Yes** | B (manual repo lookup per handler) |
| Fields not carried by events (external results, computed deadlines) | **Yes** | B |
| Uses `@DeadlineHandler` / `DeadlineManager.schedule(...)` | **Conditional** | B with own `ScheduledExecutorService`, OR stay AF4, OR wait for Axoniq Workflows |
| Heavy `SagaLifecycle.end()` / `@EndSaga` flow control | **Maybe** | Both — translate to state transitions / terminal field |
| Cross-saga coordination, association-property routing across many saga instances | **No** | Process-manager territory — wait for Axoniq Workflows / contact Axoniq |
| Custom `SagaStore` / persistence config | **No** | Saga storage stays AF4; out of scope |

## Inputs

- `target` — FQ saga class (required in single mode; informational from INIT triage)

## Preflight

No "already migrated" path — once ported, the file is an event processor and saga grep won't match. Always proceed to the decision flow.

## Procedure

1. **Detect deadline blocker:**
   ```bash
   grep -RnE '@DeadlineHandler|DeadlineManager|DeadlineMessage|deadlineManager\.schedule|cancelSchedule|cancelAllWithinScope' \
        --include='*.java' --include='*.kt' <saga file> <saga package>
   ```
   Hits → `decisions.deadline-handler-in-saga = present`. Migration not feasible without out-of-band deadline replacement.
2. **Detect saga shape:** `@Saga`, `@SagaEventHandler`, `@StartSaga`, `@EndSaga`, `SagaLifecycle.end(...)` / `.associateWith(...)`. `@SagaEventHandler(associationProperty = "...")` is the strongest signal AF5 has no direct equivalent.
3. **`AskUserQuestion` — choose one:**
   - `migrate-to-event-handler-with-state` *(recommended only when step 1 found NO deadline AND step 2 association mechanics are simple)*. Sub-choice:
     - `shape-a-injected-event-sourced-state` (see Worked example A)
     - `shape-b-jpa-state-with-scheduler` (see Worked example B)
   - `accept-stays-af4` — saga stays AF4; stabilization excludes the files from AF5 build path.
   - `pause-migration` — user removes saga / deadline dep first.
   - `remove-feature-first` — user redesigns as plain projection / handler before resuming.
4. Append dated entry to `learnings.md` (decision + FQN + reason).
5. Emit Output. Orchestrator commits a decision-only record.

## Worked example A — `@InjectEntity` + event-sourced state

`@InjectEntity SomeState` parameter: AF5 resolves the entity id from the event payload (`@InjectEntity(idProperty = "x")`, custom `EntityIdResolver`, or default `@TargetEntityId`), loads the entity via `StateManager` (opens its event stream, calls `@EntityCreator`, replays past `@EventSourcingHandler` events), then invokes the handler. **Single-context only** — `@InjectEntity` loads one entity by one id, no cross-stream merge.

### AF4 saga (before)

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

    @EndSaga @SagaEventHandler(associationProperty = "paymentReference")
    public void on(PaymentConfirmedEvent event) {
        commandGateway.send(new ApproveRequestCommand(bikeId, renter));
    }
    @EndSaga @SagaEventHandler(associationProperty = "paymentReference")
    public void on(PaymentRejectedEvent event) {
        commandGateway.send(new RejectRequestCommand(bikeId, renter));
    }
}
```

### AF5 migrated (after)

```java
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
        @EntityCreator PaymentProcessState() { }
        @EventSourcingHandler
        public void handle(BikeRequestedEvent e) { this.bikeId = e.bikeId(); this.renter = e.renter(); }
        public String bikeId() { return bikeId; }
        public String renter() { return renter; }
    }
}
```

Imports: `@EventHandler` from `org.axonframework.messaging.eventhandling.annotation`, `@InjectEntity` from `org.axonframework.modelling.annotation`, `@EventSourced` from `org.axonframework.extension.spring.stereotype`, `@EntityCreator` from `org.axonframework.eventsourcing.annotation.reflection`, `@EventSourcingHandler` from `org.axonframework.eventsourcing.annotation`, `CommandDispatcher` from `org.axonframework.messaging.commandhandling.gateway`.

### Wiring (Path B — framework Configurer)

```java
var state = EventSourcedEntityModule.autodetected(String.class, PaymentSaga.PaymentProcessState.class);
var sagaProcessor = EventProcessorModule.pooledStreaming("SagaProcessor")
    .eventHandlingComponents(c -> c.autodetected("PaymentSaga", cfg -> new PaymentSaga()))
    .notCustomized();

EventSourcingConfigurer.create()
    .registerEntity(state)
    .modelling(m -> m.messaging(msg -> msg.eventProcessing(ep ->
        ep.pooledStreaming(ps -> ps.processor(sagaProcessor)))));
```

Path A (Spring Boot) auto-config discovers the `@EventSourced` entity + `@Component` saga; only processor binding remains explicit.

### Test (`AxonTestFixture`)

```java
fixture = AxonTestFixture.with(configurer, AxonTestFixture.Customization::disableAxonServer);
// ...
fixture.given().events(new BikeRequestedEvent("bikeId", "renter", "payRef"))
       .then().commands(new PreparePaymentCommand(10, "payRef"));
```

`SagaTestFixture` has no direct AF5 replacement.

### AF4 → AF5 mapping (Shape A)

| AF4 element | AF5 replacement |
|---|---|
| `@Saga` + saga store | `@Component` + nested `@EventSourced` state class (no saga store) |
| Saga-state fields | Same fields on nested `@EventSourced` state, rebuilt by `@EventSourcingHandler` |
| `@StartSaga` | First event for that entity id triggers `@EntityCreator` + replay |
| `@EndSaga` | Drop; track terminal flag in state, or rely on no further events routed by id |
| `@SagaEventHandler(associationProperty = "x")` | `@InjectEntity` + `@TargetEntityId` on payload field (or `idProperty = "x"`) |
| `SagaLifecycle.associateWith(...)` | One stable id per state entity — events carry it |
| Autowired `CommandGateway` | `CommandDispatcher` parameter on handler |
| `SagaTestFixture` | `AxonTestFixture` over configurer registering state entity + processor |

### Caveats (Shape A)

- **Single-context only.** If saga consumes events from multiple bounded contexts with no shared correlation id, use Shape B or split.
- **Identity in events.** If AF4 saga associated by different properties on different events, redesign events to carry one correlation key OR split into two state entities.
- **No deadlines.** If `@DeadlineHandler` / `DeadlineManager` present, use Shape B or contact AxonIQ.
- **Replay safety.** Annotate the saga `@DisallowReplay` if a replay would re-emit commands. State entity's `@EventSourcingHandler` methods are pure folds — safe to replay.
- **Reconstruction cost.** Acceptable for short-lived sagas (request → confirm/reject); not for long-tail sagas with thousands of events.

## Worked example B — `@Component` + JPA state + own scheduler

When state has non-event fields OR needs deadline replacement.

### JPA state

```java
@Entity
public class PaymentState {
    @Id private String paymentReference;
    private Status status;
    private long timestamp;
    private String paymentId;

    public PaymentState() { }
    public PaymentState(String ref) {
        this.paymentReference = ref;
        this.status = Status.PENDING;
        this.timestamp = System.currentTimeMillis();
    }
    public enum Status { PENDING, PREPARED, CONFIRMED, REJECTED, CANCELLED }
    // getters + transition methods
}
```

### Repository (Spring Data JPA)

```java
@Repository
public interface PaymentStateRepository extends JpaRepository<PaymentState, String> {
    List<PaymentState> findAllByTimestampLessThanAndStatusIn(long ts, PaymentState.Status... s);
    @Modifying @Transactional(propagation = Propagation.MANDATORY)
    @Query("UPDATE PaymentState p SET p.status = :s WHERE p.paymentReference = :r")
    void updateStatus(String r, PaymentState.Status s);
    @Query("SELECT MIN(p.timestamp) FROM PaymentState p WHERE p.status IN :statuses")
    Optional<Long> findEarliestActiveTimestamp(@Param("statuses") List<PaymentState.Status> statuses);
}
```

### Migrated component

```java
@Component
@DisallowReplay
public class PaymentSaga {
    private static final Duration PAYMENT_TIMEOUT = Duration.ofSeconds(10);
    private final CommandGateway commandGateway;
    private final PaymentStateRepository repository;
    private final ScheduledExecutorService scheduler;
    private final AtomicReference<ScheduledFuture<?>> scheduledCheck = new AtomicReference<>();

    public PaymentSaga(CommandGateway cg, PaymentStateRepository r, ScheduledExecutorService s) { … }

    @EventListener(ApplicationReadyEvent.class)
    public void onApplicationReady() { scheduleNextCheck(); }

    @EventHandler
    public void on(BikeRequestedEvent e, CommandDispatcher cd) {
        repository.save(new PaymentState(e.rentalReference()));
        cd.send(new PreparePaymentCommand(10, e.rentalReference()));
        ScheduledFuture<?> cur = scheduledCheck.get();
        if (cur == null || cur.isDone()) scheduleNextCheck();
    }
    @EventHandler
    public void on(PaymentConfirmedEvent e, CommandDispatcher cd) {
        repository.updateStatus(e.paymentReference(), PaymentState.Status.CONFIRMED);
        cd.send(new ApproveRequestCommand(e.paymentReference()));
    }
    // ... etc.

    @Transactional
    public void cancelLatePayments() {
        long cutoff = System.currentTimeMillis() - PAYMENT_TIMEOUT.toMillis();
        repository.findAllByTimestampLessThanAndStatusIn(cutoff, PENDING, PREPARED).forEach(s -> {
            if (s.paymentId() != null) commandGateway.send(new RejectPaymentCommand(s.paymentId()));
            else {
                repository.updateStatus(s.paymentReference(), Status.CANCELLED);
                commandGateway.send(new RejectRequestCommand(s.paymentReference()));
            }
        });
        scheduleNextCheck();
    }

    private void scheduleNextCheck() {
        repository.findEarliestActiveTimestamp(List.of(PENDING, PREPARED)).ifPresent(earliest -> {
            long delay = earliest + PAYMENT_TIMEOUT.toMillis() - System.currentTimeMillis();
            scheduledCheck.set(scheduler.schedule(this::cancelLatePayments, Math.max(delay, 0), TimeUnit.MILLISECONDS));
        });
    }
}
```

### AF4 → AF5 mapping (Shape B)

| AF4 | AF5 |
|---|---|
| `@Saga`, `@SagaEventHandler`, `@StartSaga`, `@EndSaga` | `@Component` + `@EventHandler` + state-machine transitions in JPA `Status` column |
| `associationProperty` routing | Repository lookup by primary key — events carry the correlation key |
| `SagaLifecycle.end()` | `repository.updateStatus(ref, Status.<terminal>)` — sweep ignores terminal rows |
| Saga-state fields | JPA `@Entity` with same fields |
| `DeadlineManager.schedule(...)` + `@DeadlineHandler` | Own `ScheduledExecutorService` + JPA timestamp poll |
| Saga store config (`SagaConfigurer`, `@SagaStore`) | Standard Spring Data JPA repository |

### Caveats (Shape B)

- Component is `@DisallowReplay` — replay would re-emit every payment cycle.
- `ScheduledExecutorService` is NOT persisted across restarts — `onApplicationReady()` re-arms from JPA `MIN(timestamp)`. Restart safe; in-flight delays absorbed by next poll.
- Timestamp-driven polling is coarser than `DeadlineManager`. OK for "minutes, not milliseconds". Surface trade-off — NOT a 1:1 deadline replacement.
- For Path B (no Spring) substitute a hand-rolled JPA DAO.

## End condition

Never green automatically — no compile-time check the recipe can run. Orchestrator commits the recorded decision; actual saga rewrite (when `migrate-to-event-handler-with-state`) runs as a follow-up through the `event-processor` recipe.

## Output

| AskUserQuestion answer | `result:` | `next:` |
|---|---|---|
| (not yet answered) | `needs-decision` | `ask-user` |
| `accept-stays-af4` / `pause-migration` / `remove-feature-first` | `blocked` | `record-and-skip` |
| `migrate-to-event-handler-with-state` | `blocked` | `route-to:event-processor` |

This recipe NEVER emits `result: success` — the rewrite is the user's job + the event-processor recipe runs afterwards.

```yaml
result: needs-decision | blocked
target: <FQ saga class | "n/a">
reason: <one short line>
decisions:
  saga: migrate-to-event-handler-with-state | accept-stays-af4 | pause-migration | remove-feature-first | pending
  shape: shape-a-injected-event-sourced-state | shape-b-jpa-state-with-scheduler | n/a       # only when migrate
  deadline-handler-in-saga: none | present                                                    # if present, shape MUST be B (or surface follow-up)
caller-expects: { commit: <bool>, next: ask-user | record-and-skip | route-to:event-processor }
notes: |
  When migrate: name target component class + nested state entity (Shape A) or JPA entity + repo (Shape B).
  When accept-stays-af4: list which AF4 deps stay.
  When needs-decision: list verbatim AskUserQuestion options.
```

## Caveats

- Even with `accept-stays-af4`, sagas reference AF4-only types — stabilization MUST exclude these files from AF5 build path, or the project won't compile.
- A saga using `DeadlineManager` cannot cleanly migrate without out-of-band deadline replacement (own scheduler / Spring `@Scheduled` / Quartz / Axoniq Workflows). Never silently drop deadlines.
- When AxonIQ Workflows ships with a saga → workflow migration path, this recipe will gain a fourth option (`migrate-to-axoniq-workflow`).

## Reference pairs (AF4 → AF5)

- **`PaymentSaga` with `@DeadlineHandler` → `@Component` + JPA state + `@Scheduled` (Shape B):** `axon4/bike-rental-extended/rental/.../paymentsaga/PaymentSaga.java` ↔ `axon5/bike-rental-extended/rental/.../paymentsaga/PaymentSaga.java`. AF5 side also adds `PaymentState.java` + `PaymentStateRepository.java` in the same package. The recipe itself NEVER produces this rewrite — it surfaces the four-way decision; the user (or a follow-up `event-processor` recipe run) produces the AF5 code.
