---
id: saga
title: Saga
description: Migrates a single Axon Framework 4 Saga — AF5 removed the Saga SPI, so there is no canonical path; the recipe proposes strategies + a recommendation and the caller picks.
order: 7
argument-hint: $SOURCE
---

# Saga

> **AF5 removed the Saga SPI entirely.** No `@Saga`, no `@SagaEventHandler`, no `SagaLifecycle`, no `DeadlineManager`. **There is no single, mechanical migration path** — how to re-express an AF4 saga depends on what the saga actually does (pure correlation + command dispatch, time-driven deadlines, multi-context coordination). The recipe therefore does NOT silently apply one rewrite. It researches the saga's surface, **proposes the viable strategies with a recommendation derived from the detected signals (chiefly: are `@DeadlineHandler` / `DeadlineManager` present?), and surfaces the choice as a decision** (Blocker B0 → Options). The orchestrator asks the caller (`AskUserQuestion`) or, in `auto=true`, picks the `(Recommended)` option. Only after a strategy is chosen does the recipe execute it. There is no migration-path catalog entry for sagas; the recipe is self-contained.

## Source

- `$SOURCE` (required) — FQN, file path, or simple class name of an AF4 saga. The class is annotated `@Saga` (from `org.axonframework.spring.stereotype.Saga` or `org.axonframework.extension.spring.stereotype.Saga`) AND/OR carries at least one `@SagaEventHandler` method.

## Scope

- `$SOURCE` saga class.
- **Under the `stateful-rewrite` strategy only**, the recipe also creates and owns:
  - New `<SagaName>State` entity class — same package as `$SOURCE`, **in `$SOURCE`'s own language** (`.kt` if `$SOURCE` is Kotlin, `.java` if Java).
  - New `<SagaName>StateRepository` interface — same package and language.
  - Any existing `*State` / `*StateRepository` files (`.java` / `.kt`) in the same package if already partially created.

Scope grows during Research; never shrinks. Sibling sagas, aggregates, projectors are NOT in scope. Before a strategy is chosen, the recipe applies **no edits** — Scope only materialises once the caller picks a migration strategy.

## Blocker

### B0 — Strategy decision (the primary outcome of this recipe)

**Fires whenever:** live AF4 saga constructs are present on `$SOURCE` (i.e. it is not already migrated) **AND** no strategy hint was passed in (first visit, not a BLOCKER_RESOLUTION re-entry). This is the normal, expected outcome of a first run — not a failure.

There is no canonical AF5 replacement for a saga, so the recipe cannot pick the approach on the caller's behalf. It emits B0 with the candidate strategies as **Options** and a **recommendation** in NOTES. The orchestrator surfaces the list (`AskUserQuestion` when `auto=false`; auto-picks the `(Recommended)` option when `auto=true`).

Recipe-specific Options (in addition to the three baselines `skip` / `revert` / `solve-manually`):

- [ ] **stateful-rewrite** — rebuild the saga as a `@Component @DisallowReplay` event-handler backed by a new JPA state entity + repository (see § Toolbox). State that lived in saga fields becomes rows in the state entity; `SagaLifecycle` association/lifecycle calls become explicit repository lookups/saves; in-handler dispatch moves to a `CommandDispatcher` parameter. If `@DeadlineHandler` / `DeadlineManager` are present, the deadline code is commented out with `// TODO AF5:` markers and reported as required follow-up (AF5 has no scheduler equivalent — the replacement, e.g. an `@Scheduled` poller on the state entity's timestamp, is a project decision the recipe cannot make).

The baseline **skip** option is the natural "defer" path: leave the saga on its AF4 shape now and redesign later.

**Recommendation heuristics** — the recipe MUST state which option it recommends and why, derived from the saga's surface:

| Detected signal | Recommended option | Why |
|---|---|---|
| No `@DeadlineHandler` / `DeadlineManager`; saga only correlates events and dispatches commands | **stateful-rewrite** *(Recommended)* | Mechanical, fully automatable; safe to auto-apply. |
| `@DeadlineHandler` / `DeadlineManager` present | **skip** *(Recommended)* | Deadline replacement needs project-specific design (interval, error handling, scheduler mechanism). Auto-applying a rewrite would leave commented-out, non-functional timeout logic. Caller should choose `stateful-rewrite` explicitly if they accept the manual scheduler follow-up. |
| Multi-context coordination / unclear state ownership / the saga is really a candidate for redesign | **solve-manually** *(Recommended)* | The "same architecture as AF4" goal does not hold cleanly; a human should decide the AF5 shape. |

Mark exactly one Option `(Recommended)` per the table so `auto=true` resolves deterministically.

### Unmet project prerequisites

- Project does not compile pre-recipe — surface as Blocker `prerequisite-not-compiling`.

## Out of Scope

- Sibling sagas, aggregates, projectors.
- Cross-saga / cross-context correlation redesign (note in NOTES; caller designs the state schema).
- Designing the deadline replacement mechanism (poller interval, scheduler, error handling) — recipe comments out deadline code and flags it; the design is the caller's.
- Event-store or token-store changes.
- Processor namespace / YAML wiring beyond an `@EnableScheduling` flag.
- Rewriting existing saga tests — see § Gotchas (fixture-based saga tests do not survive; flagged as follow-up, not silently rewritten).
- Logging, formatting, package renames.

## Applicable

Surface check on `$SOURCE`. Cheap reads only.

Decision rule (top-down; first match wins):

1. **Aggregate** — class annotated `@Aggregate` / `@AggregateRoot` AND has `@EventSourcingHandler`. → **Rejected** (route to aggregate recipe).
2. **Event-processor** — class annotated `@ProcessingGroup` / `@Namespace` AND has `@EventHandler` (not `@SagaEventHandler`). → **Rejected** (route to event-processor recipe).
3. **Saga AF4 shape** — class annotated `@Saga` OR any method annotated `@SagaEventHandler` / `@StartSaga` / `@EndSaga`. → **continue**.
4. **Already migrated** — no `@Saga`, no `@SagaEventHandler`, class is `@Component @DisallowReplay` with `@EventHandler` methods. → **continue** (no live AF4 constructs → B0 does NOT fire; Success Criteria pre-Apply check decides idempotent-Success).
5. **None of the above** — no saga or event-handler marker found. → **Rejected**.

## Success Criteria

Success Criteria are evaluated **only once a strategy is chosen and the recipe is executing it** (a BLOCKER_RESOLUTION re-entry carrying a strategy hint), or when `$SOURCE` is already migrated (Applicable predicate 4 → idempotent check). On a first visit with no strategy chosen, the recipe returns Blocker B0 before reaching this section.

Extends DEFAULT.md baseline. The checks below apply to the **`stateful-rewrite`** strategy.

For `$SOURCE` and every in-scope file:

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

When deadlines were present, the commented-out deadline code is exempt from criterion 1 (it is non-code); criteria 1–5 apply to the live, non-deadline parts. The deadline follow-up is reported in NOTES, not failed.

Aggregation rule: **all match (AND)** — DEFAULT.md baseline AND criteria 1–5.

### Verification

Run `grep -rn "SagaTestFixture\|AxonTestFixture" src/test`. If an existing saga test uses either fixture, it will not compile after the rewrite (neither supports non-aggregate types in AF5). **Do not block on it** — exclude it from `test-sources` (compile the saga + new files only), flag "saga test needs manual rewrite" as a `no-test-coverage` Learning, and proceed. Invoke `axon4to5-isolatedtest` with `test-sources: []` (compile-only). Compile-clean check still applies — grep for lingering AF4 imports as a proxy before concluding Success.

## References

No saga migration path exists in the docs catalog. Recipe is self-contained.

- [messages.adoc](../../docs/paths/messages.adoc) — *apply-condition:* always. Covers `getPayload()` / `getMetaData()` → `payload()` / `metaData()` accessor renames inside event handler bodies.
- [projectors-event-processors.adoc](../../docs/paths/projectors-event-processors.adoc) — *apply-condition:* processor wiring is in scope (caller needs to register the migrated component as an event processor via `EventProcessorDefinition` or `MessagingConfigurer`). Informational — out of scope for this recipe; flag in Result NOTES.

## Toolbox

The procedures below execute **only when the chosen strategy is `stateful-rewrite`** (B0 resolved to that option, re-entered with the hint). For `skip` / `revert` / `solve-manually` the recipe applies no edits.

### Step 1 — Class-level annotation swap

1. Remove `@Saga` annotation and its import (`org.axonframework.spring.stereotype.Saga` / `org.axonframework.extension.spring.stereotype.Saga`).
2. Add `@Component` (`org.springframework.stereotype.Component`).
3. Add `@DisallowReplay` (`org.axonframework.messaging.eventhandling.replay.annotation.DisallowReplay`).
4. Remove `@Autowired` on `CommandGateway` / `DeadlineManager` fields (will be constructor-injected or removed).

### Step 2 — Create JPA state entity

Name: `<SagaName>State` (e.g. `PaymentSaga` → `PaymentState`). Place in the same package as `$SOURCE`.

Required structure:
```java
@Entity
public class <Name>State {
    @Id
    private <IdType> <correlationKey>;   // the saga's primary association key
    // additional correlation fields and business state fields
    private Status status;
    private long timestamp;              // creation or "prepared" time — used by a deadline-replacement poller

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

### Step 3 — Create JPA repository

```java
@Repository
public interface <Name>StateRepository extends JpaRepository<<Name>State, <IdType>> {
    List<<Name>State> findAllByTimestampLessThanAndStatusIn(long timestamp, <Name>State.Status... status);
}
```

Add `findAllByTimestampLessThanAndStatusIn` — required if the caller later designs a deadline-replacement poller; harmless when no deadline was present.

> The Step 2/3 templates show Java. When `$SOURCE` is Kotlin, emit the Kotlin equivalent instead (`.kt` file, `interface <Name>StateRepository : JpaRepository<...>`, `data class`/`class` for the `@Entity`) — same annotations and JPA contract. Match `$SOURCE`'s language; never add a `.java` file to a Kotlin saga's package.

### Step 4 — Migrate event handlers

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

### Step 5 — Comment out DeadlineManager / @DeadlineHandler (when deadlines present)

*Apply-condition:* `DeadlineManager` field OR `@DeadlineHandler` method detected on `$SOURCE`.

AF5 has no scheduler equivalent and the recipe cannot design the replacement. Do NOT remove deadline code — comment it out, annotate it, and report it as required follow-up in NOTES:

1. Comment out the `DeadlineManager` field:
   ```java
   // TODO AF5: DeadlineManager removed — design replacement (e.g. @Scheduled poller on the state entity's timestamp)
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

The structural migration still succeeds; the deadline replacement is a follow-up the caller owns. (This is why, at B0, a deadline-bearing saga is recommended `skip` unless the caller explicitly accepts this follow-up.)

### Step 6 — Constructor injection

Replace `@Autowired` field injection with constructor injection for all remaining dependencies (`CommandGateway`, `PaymentStateRepository`, etc.):

```java
public <SagaName>(CommandGateway commandGateway, <Name>StateRepository repository) {
    this.commandGateway = commandGateway;
    this.repository = repository;
}
```

## Use cases

- [01-jpa-state-shape-spring.md](use-cases/01-jpa-state-shape-spring.md) — *apply-condition:* strategy = `stateful-rewrite` AND `$SOURCE` has no `DeadlineManager` (simple saga with `@StartSaga` / `@EndSaga` / `SagaLifecycle.associateWith`).
- [02-deadline-blocker-comment-out.md](use-cases/02-deadline-blocker-comment-out.md) — *apply-condition:* strategy = `stateful-rewrite` AND `$SOURCE` injects `DeadlineManager` OR has `@DeadlineHandler` methods (rewrite + comment-out + deadline follow-up).
- [03-rejected-not-a-saga.md](use-cases/03-rejected-not-a-saga.md) — *apply-condition:* `$SOURCE` is an aggregate or projector (Applicable predicate 1 or 2 fires; for routing reference only).

## Gotchas

- **The first run of this recipe is a decision, not an edit.** A first visit on an AF4 saga always returns Blocker B0 with strategy Options + a recommendation; no source files change until the caller picks a strategy. Do not "helpfully" start rewriting before B0 is resolved.
- **Deadlines drive the recommendation.** Presence of `@DeadlineHandler` / `DeadlineManager` flips the recommendation from `stateful-rewrite` to `skip`, because the timeout replacement is a genuine project decision (interval, scheduler, error handling) the recipe cannot make. `stateful-rewrite` is still offered for callers who accept the manual follow-up.
- **`@DisallowReplay` is mandatory** (stateful-rewrite). Without it, a full replay re-fires every `@EventHandler` and creates duplicate state rows. `@DisallowReplay` blocks the processor during replay so the JPA state is only built from live events.
- **`CommandDispatcher` vs `CommandGateway`.** In-handler dispatch uses `CommandDispatcher` as a method parameter. If the caller later adds a deadline-replacement poller, that method is NOT an event handler — it must use a `CommandGateway` field (constructor-injected). Having both in the same class is correct.
- **`SagaLifecycle.associateWith("secondaryKey", value)` → store in state entity.** A second association key (e.g. `paymentReference` added after a `bikeId` start) becomes a field on the state entity set in the start handler; subsequent handlers look it up via `repository.findById(event.paymentReference())` — no Axon-level routing needed.
- **`DeadlineManager.cancelAllWithinScope(...)` in `@EndSaga` handlers** — comment it out with the other deadline calls. A poller replacement naturally skips terminal-status rows via a `statusIn(PENDING, PREPARED)` query predicate.
- **Processor wiring out of scope but important.** The migrated `@Component` needs an `EventProcessorDefinition` (Spring) or `MessagingConfigurer.eventProcessing(...)` (native) to register as an event processor. Flag in Result NOTES with a pointer to `projectors-event-processors.adoc`.
- **No-arg JPA constructor.** Hibernate requires a no-arg constructor on `@Entity` classes. Always generate `public <Name>State() {}`.
- **`@Saga` had two common import paths:** `org.axonframework.spring.stereotype.Saga` (older) and `org.axonframework.extension.spring.stereotype.Saga` (newer Extension model). Grep for both; both must be removed.
- **Saga fields become repository lookups.** Instance fields stored between event invocations are replaced by fields on the JPA entity. Every handler that reads those fields must look up the entity first.
- **Existing saga tests do not survive.** `SagaTestFixture` (AF4) / `AxonTestFixture` (post-OpenRewrite) do not support non-aggregate types in AF5. After a `stateful-rewrite`, such a test will not compile — exclude it from the isolated-test compile, flag "saga test needs manual rewrite" as a `no-test-coverage` Learning, and leave the test for the caller (a Mockito unit test mocking the repository + `CommandDispatcher` is the usual replacement). Do NOT silently rewrite it.
- **`@EntityScan(basePackageClasses = {SagaEntry.class})` fails to compile after saga removal.** `org.axonframework.modelling.saga.repository.jpa.SagaEntry` was removed with the Saga SPI. Replace with the new state entity class (`<SagaName>State.class`). For modules that don't depend on the module containing the state entity, use `basePackages = "..."` (string-based scan) to avoid a cross-module compile dependency.

## Result

Inherits DEFAULT.md baseline.

### Blocker (B0 — strategy decision, the primary first-run outcome)

Say **"return BLOCKER"**, then **MUST emit** the result block (schema: FLOW.md § Result). `Recipe:` field is `axon4to5-saga`. NOTES state that AF5 removed the Saga SPI so there is no canonical path, summarise the saga's detected signals (deadlines? command dispatch? coordination?), and **name the recommended option and why**. The Options block lists the recipe-specific `stateful-rewrite` option plus the three baselines, with exactly one marked `(Recommended)` per the heuristics table.

Example (no deadlines — recommend stateful-rewrite):

```
return BLOCKER

> **Result:** 🚧 Blocker
> **Source:** `com.example.paymentsaga.PaymentSaga`
> **Recipe:** axon4to5-saga
>
> **Notes:** AF5 removed the Saga SPI — no canonical migration path. `PaymentSaga` only correlates events (`bikeId`) and dispatches commands; no `@DeadlineHandler` / `DeadlineManager` detected. Recommend a stateful-rewrite (mechanical, fully automatable). Choose a strategy before the recipe applies any edits.
>
> **Learnings:**
> ## YYYY-MM-DD — Saga strategy is a caller decision (no AF5 Saga SPI)
> **Trigger:** blocker
> **Where:** `com.example.paymentsaga.PaymentSaga`
> **Surprise:** AF5 has no Saga SPI; the recipe cannot pick the AF5 shape unilaterally.
> **Resolution:** Halted with strategy Options; recommended `stateful-rewrite` (no deadlines). No edits applied yet.
>
> **Options:**
> - [ ] **stateful-rewrite** *(Recommended)* — rebuild as `@Component @DisallowReplay` event handler backed by a new JPA `PaymentState` entity + repository; in-handler dispatch via `CommandDispatcher`.
> - [ ] **skip** — leave `PaymentSaga` on its AF4 shape; redesign later; queue moves on.
> - [ ] **revert** — no edits applied yet; equivalent to skip.
> - [ ] **solve-manually** — pause; caller designs the AF5 shape by hand, then re-invokes.
```

Example (deadlines present — recommend skip):

```
return BLOCKER

> **Result:** 🚧 Blocker
> **Source:** `com.example.paymentsaga.PaymentSagaWithDeadline`
> **Recipe:** axon4to5-saga
>
> **Notes:** AF5 removed the Saga SPI — no canonical migration path. `PaymentSagaWithDeadline` injects `DeadlineManager` and has `@DeadlineHandler(deadlineName = "cancelPayment")`. AF5 has no scheduler equivalent; the timeout replacement (interval, mechanism, error handling) is a project decision. Recommend `skip` (defer) — or `stateful-rewrite` if you accept that the deadline code is commented out with TODOs for a follow-up `@Scheduled` poller you design.
>
> **Learnings:**
> ## YYYY-MM-DD — Deadline-bearing saga has no automatic AF5 path
> **Trigger:** blocker
> **Where:** `com.example.paymentsaga.PaymentSagaWithDeadline:12`
> **Surprise:** AF5 removed both the Saga SPI and `DeadlineManager`; the timeout replacement cannot be auto-designed.
> **Resolution:** Halted with strategy Options; recommended `skip`. No edits applied yet.
>
> **Options:**
> - [ ] **skip** *(Recommended)* — leave the saga on its AF4 shape; design the AF5 process + timeout replacement deliberately; queue moves on.
> - [ ] **stateful-rewrite** — rebuild as `@Component @DisallowReplay` + JPA state; deadline code is commented out with `// TODO AF5:` markers and reported as required follow-up (you design the `@Scheduled`/scheduler replacement).
> - [ ] **revert** — no edits applied yet; equivalent to skip.
> - [ ] **solve-manually** — pause; caller designs the AF5 shape + timeout replacement by hand, then re-invokes.
```

### Success (after `stateful-rewrite` is chosen and executed)

Say **"return SUCCESS"**, then **MUST emit** the result block (schema: FLOW.md § Result). `Recipe:` field is `axon4to5-saga`. NOTES must name the two new files created (state entity + repository). Flag in NOTES: (a) processor wiring not handled — caller should add `EventProcessorDefinition` per `projectors-event-processors.adoc`; (b) if deadlines were present, the commented-out deadline code is a **required follow-up** — the caller must design the replacement (e.g. `@Scheduled` poller + `@EnableScheduling`); (c) any existing saga test was left for manual rewrite (`no-test-coverage` Learning).

### Rejected

Say **"return REJECTED"**, then **MUST emit** the result block (schema: FLOW.md § Result). `Recipe:` field is `axon4to5-saga`. NOTES must name the failed `# Applicable` predicate (1 aggregate / 2 event-processor / 5 unrecognised) and the sister recipe to route to.

### Failure

Say **"return FAILURE"**, then **MUST emit** the result block (schema: FLOW.md § Result). NOTES list failing Success Criteria + last grep/compiler error verbatim. LEARNINGS nearly always present — common failure shape: AF4 import survived the rewrite (grep for `org.axonframework.modelling.saga` after edit).
