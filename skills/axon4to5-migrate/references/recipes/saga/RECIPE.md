---
id: saga
title: Saga
description: Migrates a single Axon Framework 4 Saga to a stateful @Component event handler with JPA-backed state — full structural rewrite, no AF5 Saga SPI.
order: 7
argument-hint: $SOURCE
---

# Saga

> AF5 removed the Saga SPI entirely. No `@Saga`, no `@SagaEventHandler`, no `SagaLifecycle`, no `DeadlineManager`. This recipe performs a **structural rewrite** — the saga class becomes a `@Component @DisallowReplay` event handler backed by a JPA state entity. New files are always created (state entity + repository). **`DeadlineManager` / `@DeadlineHandler` have no AF5 equivalent** — the recipe migrates all non-deadline code, comments out the deadline parts, and emits `Blocker` for the caller to design the replacement. There is no migration path catalog entry for saga; this recipe is self-contained.

## Source

- `$SOURCE` (required) — FQN, file path, or simple class name of an AF4 saga. The class is annotated `@Saga` (from `org.axonframework.spring.stereotype.Saga` or `org.axonframework.extension.spring.stereotype.Saga`) AND/OR carries at least one `@SagaEventHandler` method.

## Scope

- `$SOURCE` saga class.
- New `<SagaName>State` entity class — created by this recipe in the same package as `$SOURCE`. **Created in `$SOURCE`'s own language** — `.kt` if `$SOURCE` is Kotlin, `.java` if Java.
- New `<SagaName>StateRepository` interface — created by this recipe in the same package as `$SOURCE`, in `$SOURCE`'s language (see above).
- Any existing `*State` / `*StateRepository` files (`.java` or `.kt`) in the same package if already partially created.
- Existing `*SagaTest` / `*Test` (`.java` or `.kt`) in the same package that imports `SagaTestFixture` (AF4) or `AxonTestFixture` (post-OpenRewrite) — **only when B2 option `rewrite-mockito` is chosen**.

Scope grows during Research; never shrinks. Sibling sagas, aggregates, projectors are NOT in scope.

## Blocker

**B1 — `DeadlineManager` / `@DeadlineHandler` present (any configuration)**

`DeadlineManager` field OR `@DeadlineHandler` method detected on `$SOURCE`. AF5 has no `DeadlineManager`. Designing a replacement (e.g., `@Scheduled` poller, `ScheduledExecutorService`) requires project-specific decisions (polling interval, state fields, error handling) that the recipe cannot make automatically.

**Partial migration applies before emitting B1.** The recipe migrates all non-deadline code first (Steps 1–4, 6), then:

1. Comments out every `@DeadlineHandler` method body with a `// TODO AF5: DeadlineManager removed — design replacement (e.g. @Scheduled poller on the state entity)` note.
2. Comments out every `deadlineManager.schedule(...)` / `deadlineManager.cancelAllWithinScope(...)` call site with a similar TODO.
3. Comments out the `DeadlineManager` field declaration.
4. Keeps all imports as comments so the caller can see what was there.

Then emits Blocker B1. The source is in a partially-migrated state — the saga structure is done; only the deadline mechanics need the caller's decision.

**B2 — Existing `*SagaTest` (`.java`/`.kt`) uses `SagaTestFixture` or `AxonTestFixture`**

Detection: `grep -rn "SagaTestFixture\|AxonTestFixture" src/test`. AF4 uses `SagaTestFixture`; OpenRewrite renames it to `AxonTestFixture`. Either form applies to this blocker. Neither supports non-aggregate types in AF5 — the fixture is designed for aggregates only. The test will not compile after the saga rewrite.

**Does NOT block the saga structural rewrite.** Steps 1–6 run first; B2 fires after the main migration is complete and the test file is identified.

Options (in addition to three defaults):
- `skip` *(Recommended)* — leave the test in its current (broken) state; caller rewrites later; queue moves on.
- `rewrite-mockito` — recipe rewrites the test as a plain Mockito unit test: removes `SagaTestFixture` / `AxonTestFixture`, mocks `<SagaName>StateRepository` and `CommandDispatcher`, constructs the saga directly, and uses `ArgumentCaptor` / `verify(...)` assertions. Test file is added to scope.
- `solve-manually` — pause; caller rewrites the test, then re-invokes.

**Unmet project prerequisites**

- Project does not compile pre-recipe — surface as Blocker `prerequisite-not-compiling`.

## Out of Scope

- Sibling sagas, aggregates, projectors.
- Cross-saga correlation redesign (if the saga coordinated multiple bounded contexts — note in NOTES; caller designs the state schema).
- Event-store or token-store changes.
- Processor namespace / YAML wiring beyond `@EnableScheduling` flag.
- Logging, formatting, package renames.

## Applicable

Surface check on `$SOURCE`. Cheap reads only.

Decision rule (top-down; first match wins):

1. **Aggregate** — class annotated `@Aggregate` / `@AggregateRoot` AND has `@EventSourcingHandler`. → **Rejected** (route to aggregate recipe).
2. **Event-processor** — class annotated `@ProcessingGroup` / `@Namespace` AND has `@EventHandler` (not `@SagaEventHandler`). → **Rejected** (route to event-processor recipe).
3. **Saga AF4 shape** — class annotated `@Saga` OR any method annotated `@SagaEventHandler` / `@StartSaga` / `@EndSaga`. → **continue**.
4. **Already migrated** — no `@Saga`, no `@SagaEventHandler`, class is `@Component @DisallowReplay` with `@EventHandler` methods. → **continue** (Success Criteria pre-Apply check decides idempotent-Success vs. continue).
5. **None of the above** — no saga or event-handler marker found. → **Rejected**.

## Success Criteria

Extends DEFAULT.md baseline. Recipe-specific structural invariants:

For `$SOURCE` and every in-scope file:

**When B1 (DeadlineManager) is NOT in scope** — all of the following must hold:

1. **No live AF4 saga constructs** on `$SOURCE`. None of the following appear as uncommented code:
   - `org.axonframework.spring.stereotype.Saga` import
   - `org.axonframework.extension.spring.stereotype.Saga` import
   - `org.axonframework.modelling.saga.SagaEventHandler` import
   - `org.axonframework.modelling.saga.StartSaga` / `EndSaga` / `SagaLifecycle` imports
   - `@Saga`, `@SagaEventHandler`, `@StartSaga`, `@EndSaga` annotations (not commented)

2. **`@Component @DisallowReplay` present** at class level on `$SOURCE`. Imports:
   - `org.springframework.stereotype.Component`
   - `org.axonframework.messaging.eventhandling.replay.annotation.DisallowReplay`

3. **AF5 `@EventHandler` import** present: `org.axonframework.messaging.eventhandling.annotation.EventHandler`.

4. **State entity file exists** — a `*State` file (`.java`/`.kt`) in the same package with `@Entity` and `@Id` on the primary key field.

5. **Repository file exists** — a `*StateRepository` file (`.java`/`.kt`) extending `JpaRepository<StateClass, IdType>` (Java `extends`, Kotlin `:`) in the same package.

**When B1 (DeadlineManager) IS in scope** — recipe emits Blocker after partial migration (criteria 1–5 above still apply to the non-deadline parts; deadline criteria are not checked since Blocker halts before Success verification).

Aggregation rule: **all match (AND)** — DEFAULT.md baseline AND this section's checks (scoped to non-deadline parts when B1 applies).

### Verification

First, run `grep -rn "SagaTestFixture\|AxonTestFixture" src/test`. If found → B2 applies (see § Blocker); choose option before proceeding to verification.

When B2 option is `rewrite-mockito` and the test was rewritten: invoke `axon4to5-isolatedtest` with the saga class + rewritten test file. Both must compile and tests must pass green.

When B2 option is `skip` or no test file exists: `axon4to5-isolatedtest` with `test-sources: []` (compile-only). Surface "no test coverage" as a Learning. Compile-clean check still applies — grep for lingering AF4 imports as a proxy before concluding Success.

## References

No saga migration path exists in the docs catalog. Recipe is self-contained.

- [messages.adoc](../../docs/paths/messages.adoc) — *apply-condition:* always. Covers `getPayload()` / `getMetaData()` → `payload()` / `metaData()` accessor renames inside event handler bodies.
- [projectors-event-processors.adoc](../../docs/paths/projectors-event-processors.adoc) — *apply-condition:* processor wiring is in scope (caller needs to register the migrated component as an event processor via `EventProcessorDefinition` or `MessagingConfigurer`). Informational — out of scope for this recipe; flag in Result NOTES.

## Toolbox

### Step 1 — Class-level annotation swap (always)

*Apply-condition:* always.

1. Remove `@Saga` annotation and its import (`org.axonframework.spring.stereotype.Saga` / `org.axonframework.extension.spring.stereotype.Saga`).
2. Add `@Component` (`org.springframework.stereotype.Component`).
3. Add `@DisallowReplay` (`org.axonframework.messaging.eventhandling.replay.annotation.DisallowReplay`).
4. Remove `@Autowired` on `CommandGateway` / `DeadlineManager` fields (will be constructor-injected or removed).

### Step 2 — Create JPA state entity (always)

*Apply-condition:* always (state entity is required; create if absent).

Name: `<SagaName>State` (e.g. `PaymentSaga` → `PaymentState`). Place in the same package as `$SOURCE`.

Required structure:
```java
@Entity
public class <Name>State {
    @Id
    private <IdType> <correlationKey>;   // the saga's primary association key
    // additional correlation fields and business state fields
    private Status status;
    private long timestamp;              // creation or "prepared" time — used by @Scheduled cutoff

    public <Name>State() {}             // Hibernate no-arg constructor (required)

    public <Name>State(<IdType> <key>, ...) {
        this.<key> = <key>;
        // assign other fields
        this.status = Status.PENDING;
        this.timestamp = System.currentTimeMillis();
    }

    // record-style accessors + setStatus(Status)

    public enum Status { PENDING, /* states matching AF4 saga lifecycle */, CONFIRMED, REJECTED }
}
```

Derive fields from the saga's fields + `@SagaEventHandler(associationProperty)` values.

### Step 3 — Create JPA repository (always)

*Apply-condition:* always.

```java
@Repository
public interface <Name>StateRepository extends JpaRepository<<Name>State, <IdType>> {
    List<<Name>State> findAllByTimestampLessThanAndStatusIn(long timestamp, <Name>State.Status... status);
}
```

Add `findAllByTimestampLessThanAndStatusIn` — required if the caller later designs an `@Scheduled` poller; harmless when no deadline was present.

> The Step 2/3 templates show Java. When `$SOURCE` is Kotlin, emit the Kotlin equivalent instead (`.kt` file, `interface <Name>StateRepository : JpaRepository<...>`, `data class`/`class` for the `@Entity`) — same annotations and JPA contract. Match `$SOURCE`'s language; never add a `.java` file to a Kotlin saga's package.

### Step 4 — Migrate event handlers (always)

*Apply-condition:* always.

Mapping:

| AF4 | AF5 |
|-----|-----|
| `@StartSaga @SagaEventHandler(associationProperty = "X")` | `@EventHandler` — body saves new state row; first param is the event |
| `@SagaEventHandler(associationProperty = "X")` | `@EventHandler` — body looks up state by `event.X()` |
| `@EndSaga @SagaEventHandler(associationProperty = "X")` | `@EventHandler` — body updates state to terminal status |
| `SagaLifecycle.associateWith("key", value)` | REMOVE — state lookup uses the event's natural field; no explicit association needed |
| `SagaLifecycle.removeAssociationWith(...)` | REMOVE |
| `SagaLifecycle.end()` | REMOVE — call `repository.deleteById(...)` or set terminal status instead |
| `SagaLifecycle.associateWith("secondaryKey", value)` | Store `value` in the state entity so future handlers can look it up |

Every `@EventHandler` that dispatches commands gets `CommandDispatcher commandDispatcher` as a method parameter (AF5 style). Remove the class-level `CommandGateway` field.

### Step 5 — Comment out DeadlineManager / @DeadlineHandler (when B1 in scope)

*Apply-condition:* `DeadlineManager` field OR `@DeadlineHandler` method detected on `$SOURCE`.

Do NOT remove deadline code. Comment it out and annotate it for the caller:

1. Comment out the `DeadlineManager` field:
   ```java
   // TODO AF5: DeadlineManager removed — design replacement (e.g. @Scheduled poller on the state entity)
   // private transient DeadlineManager deadlineManager;
   ```
2. Comment out every `deadlineManager.schedule(...)` / `deadlineManager.cancelAllWithinScope(...)` call site (inline in the handler body).
3. Comment out every `@DeadlineHandler` method (entire method, including the annotation):
   ```java
   // TODO AF5: @DeadlineHandler has no AF5 equivalent — implement as @Scheduled poller or manual scheduler
   // @DeadlineHandler(deadlineName = "...")
   // public void <name>(...) { ... }
   ```
4. Keep the `org.axonframework.deadline.*` imports as comments so the caller knows what was there.

After commenting out, proceed to emit Blocker B1 — do NOT attempt Step 6 for these constructs.

### Step 6 — Constructor injection (always)

*Apply-condition:* always.

Replace `@Autowired` field injection with constructor injection for all remaining dependencies (`CommandGateway`, `PaymentStateRepository`, etc.):

```java
public <SagaName>(CommandGateway commandGateway, <Name>StateRepository repository) {
    this.commandGateway = commandGateway;
    this.repository = repository;
}
```

## Use cases

- [01-jpa-state-shape-spring.md](use-cases/01-jpa-state-shape-spring.md) — *apply-condition:* `$SOURCE` has no `DeadlineManager` (simple saga with `@StartSaga` / `@EndSaga` / `SagaLifecycle.associateWith`).
- [02-deadline-blocker-comment-out.md](use-cases/02-deadline-blocker-comment-out.md) — *apply-condition:* `$SOURCE` injects `DeadlineManager` OR has `@DeadlineHandler` methods (partial migration + Blocker B1 approach).
- [03-rejected-not-a-saga.md](use-cases/03-rejected-not-a-saga.md) — *apply-condition:* `$SOURCE` is an aggregate or projector (Applicable predicate 1 or 2 fires; for routing reference only).

## Gotchas

- **`@DisallowReplay` is mandatory.** Without it, a full replay re-fires every `@EventHandler` on the migrated component and creates duplicate state rows. `@DisallowReplay` blocks the processor during replay so the JPA state is only built from live events.
- **`CommandDispatcher` vs `CommandGateway`.** In-handler dispatch uses `CommandDispatcher` as a method parameter. If the caller later adds an `@Scheduled` poller, that method is NOT an event handler — it must use a `CommandGateway` field (constructor-injected). Having both in the same class is correct.
- **`SagaLifecycle.associateWith("secondaryKey", value)` → store in state entity.** If the AF4 saga added a second association key (e.g., `paymentReference` added after a `bikeId` start), store `value` as a field on the state entity in the start handler. Subsequent handlers look it up via `repository.findById(event.paymentReference())` — no Axon-level routing needed.
- **`DeadlineManager.cancelAllWithinScope(...)` in `@EndSaga` handlers** — comment it out along with the other deadline calls. The caller's `@Scheduled` replacement will naturally skip terminal-status rows via the `statusIn(PENDING, PREPARED)` query predicate.
- **Processor wiring out of scope but important.** The migrated `@Component` needs an `EventProcessorDefinition` (Spring) or `MessagingConfigurer.eventProcessing(...)` (native) to register as an event processor. Without it, handlers may be auto-assigned to the default processor. Flag in Result NOTES with a pointer to `projectors-event-processors.adoc`.
- **No-arg JPA constructor.** Hibernate requires a no-arg constructor on `@Entity` classes. Always generate `public <Name>State() {}`.
- **`@Saga` in AF4 had two common import paths:** `org.axonframework.spring.stereotype.Saga` (older) and `org.axonframework.extension.spring.stereotype.Saga` (newer Extension model). Grep for both; both must be removed.
- **Saga fields become repository lookups.** Instance fields like `private String bikeId; private String renter;` stored between event invocations are replaced by fields on the JPA entity. Every handler that reads those fields must look up the entity first.
- **`@EntityScan(basePackageClasses = {SagaEntry.class})` fails to compile after saga removal.** `org.axonframework.modelling.saga.repository.jpa.SagaEntry` was removed with the Saga SPI. Replace with the new state entity class (`<SagaName>State.class`). For modules that don't depend on the module containing the state entity (e.g., a microservices application class), use `basePackages = "..."` (string-based package scan) instead of a class reference to avoid a cross-module compile dependency.
## Result

Inherits DEFAULT.md baseline.

### Success

Say **"return SUCCESS"**, then **MUST emit** the result block (schema: FLOW.md § Result). `Recipe:` field is `axon4to5-saga`. NOTES must name the two new files created (state entity + repository). Flag in NOTES: (a) processor wiring not handled — caller should add `EventProcessorDefinition` per `projectors-event-processors.adoc`; (b) `@EnableScheduling` addition needed if `@Scheduled` was introduced; (c) no test coverage (saga fixtures rarely ship tests — Learning).

### Blocker

Say **"return BLOCKER"**, then **MUST emit** the result block (schema: FLOW.md § Result). `Recipe:` field is `axon4to5-saga`. NOTES name the detected blocker(s) + location. Options block per detected blocker with their respective options.

B1 and B2 may fire in the same run — emit one combined Blocker result with separate Options sub-sections.

Example (B1 — DeadlineManager + native):

```
return BLOCKER

> **Result:** 🚧 Blocker
> **Source:** `com.example.paymentsaga.PaymentSaga`
> **Recipe:** axon4to5-saga
>
> **Notes:** 1 blocker detected. B1 (DeadlineManager + native config) at `PaymentSaga.java:12` — `@Autowired private transient DeadlineManager deadlineManager` and `@DeadlineHandler(deadlineName = "cancelPayment")`. AF5 has no DeadlineManager. Native projects cannot use `@Scheduled`; a custom `ScheduledExecutorService` replacement must be wired manually.
>
> **Options:**
>
> _For B1 (DeadlineManager):_
> - [ ] **skip** — keep `PaymentSaga` in its partially-migrated state (saga structure done, deadline code commented); queue moves on.
> - [ ] **revert** — undo all edits; restore pre-recipe state.
> - [ ] **solve-manually** — implement the deadline replacement (e.g., `@Scheduled` poller using the JPA state entity's timestamp field), uncomment the commented-out TODO blocks, and re-invoke.
```

Example (B2 — existing test uses `AxonTestFixture`):

```
return BLOCKER

> **Result:** 🚧 Blocker
> **Source:** `com.example.paymentsaga.PaymentSaga`
> **Recipe:** axon4to5-saga
>
> **Notes:** 1 blocker detected. B2 (existing saga test uses AxonTestFixture) at `PaymentSagaTest.java:36` — `new AxonTestFixture(PaymentSaga.class)`. `AxonTestFixture` does not support non-aggregate types in AF5. Structural saga rewrite is complete; only the test requires a decision.
>
> **Options:**
>
> _For B2 (SagaTestFixture / AxonTestFixture in existing test):_
> - [ ] **skip** *(Recommended)* — leave `PaymentSagaTest` in its current broken state; caller rewrites later; queue moves on.
> - [ ] **rewrite-mockito** — recipe rewrites `PaymentSagaTest` as a plain Mockito unit test (mocked repository + `CommandDispatcher`, direct construction, `ArgumentCaptor` assertions). Test file added to scope.
> - [ ] **revert** — undo all edits including the saga rewrite; restore pre-recipe state.
> - [ ] **solve-manually** — pause; caller rewrites the test, then re-invokes.
```

### Rejected

Say **"return REJECTED"**, then **MUST emit** the result block (schema: FLOW.md § Result). `Recipe:` field is `axon4to5-saga`. NOTES must name the failed `# Applicable` predicate (1 aggregate / 2 event-processor / 5 unrecognised) and the sister recipe to route to.

### Failure

Say **"return FAILURE"**, then **MUST emit** the result block (schema: FLOW.md § Result). NOTES list failing Success Criteria + last grep/compiler error verbatim. LEARNINGS nearly always present — common failure shape: AF4 import survived the rewrite (grep for `org.axonframework.modelling.saga` after edit).
