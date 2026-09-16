---
id: saga
title: Saga
description: Migrates an Axon Framework 4 Saga - the caller picks between running it on axon-legacy (recommended, default) and rewriting it as a JPA-state-backed event handler.
order: 7
argument-hint: $SOURCE
---

# Saga

> **Two viable strategies, and the choice is the caller's.** AF5 carries the whole AF4 saga surface forward in the
> `axon-legacy` module - `@Saga`, `@SagaEventHandler`, `@StartSaga`, `@EndSaga`, `SagaLifecycle`, `AssociationValue`,
> every `SagaStore` implementation - under their AF4 package names. A saga can therefore keep running as-is. The
> alternative is to rebuild it as a plain event handler over a JPA state table.
>
> **`axon-legacy` is the recommended default.** It is the only strategy that keeps unfinished AF4 saga instances alive
> and the only place framework deadlines can ever come from. The recipe asks at Blocker B0 and, when it cannot ask
> (`auto=true`), takes `axon-legacy`.
>
> Neither strategy is an AF5-native redesign (Workflow, state from context events, vertical slices). That is a
> different exercise and conflicts with the skill's "same architecture as AF4" goal - flag it in NOTES as the caller's
> follow-up, never start it here.

## Source

- `$SOURCE` (required) - FQN, file path, or simple class name of an AF4 saga. The class is annotated `@Saga`
  (`org.axonframework.spring.stereotype.Saga`) AND/OR carries at least one `@SagaEventHandler` method.

## Scope

Common to both strategies:

- `$SOURCE` saga class.
- The build file of the module owning `$SOURCE` (`pom.xml` / `build.gradle[.kts]`).
- `application.properties` / `application.yaml` entries keyed on `$SOURCE`'s processor name.

Strategy `axon-legacy` additionally:

- `$SOURCE`'s test class when it uses `SagaTestFixture`, plus the test-scoped `axon-legacy-test` dependency.
- **`configuration=native` only:** the configuration class registering `$SOURCE` on a processor.

Strategy `stateful-rewrite` additionally creates and owns:

- New `<SagaName>State` entity class - same package as `$SOURCE`, **in `$SOURCE`'s own language** (`.kt` if `$SOURCE`
  is Kotlin, `.java` if Java).
- New `<SagaName>StateRepository` interface - same package and language.
- Any existing `*State` / `*StateRepository` files in the same package if already partially created.

Scope grows during Research; never shrinks. Sibling sagas, aggregates, projectors are NOT in scope. Before a strategy
is chosen the recipe applies **no edits** - Scope only materialises once B0 is resolved.

## Blocker

### B0 - Strategy decision (the first-run outcome)

**Fires whenever:** live AF4 saga constructs are present on `$SOURCE` **AND** no strategy hint was passed in (first
visit, not a BLOCKER_RESOLUTION re-entry). This is the normal, expected outcome of a first run - not a failure.

The deciding facts are not in the source: whether unfinished AF4 saga instances exist in the saga store, and whether
the AF5 application is meant to keep starting new ones. Only the caller knows them, so the recipe asks.

Recipe-specific Options (in addition to the three baselines `skip` / `revert` / `solve-manually`):

- [ ] **axon-legacy** *(Recommended)* - keep `$SOURCE` exactly as it is and add `org.axonframework:axon-legacy`. The
  class, its association values and its existing saga-store rows are untouched; only lifecycle access, command dispatch
  and collaborator injection change shape. See § Toolbox - strategy `axon-legacy`.
- [ ] **stateful-rewrite** - rebuild `$SOURCE` as a `@Component @DisallowReplay` event handler backed by a new JPA
  state entity + repository. Saga fields become rows; `SagaLifecycle` calls become repository lookups and saves. The
  existing saga-store rows are **abandoned** - any AF4 instance still in flight stops progressing. See § Toolbox -
  strategy `stateful-rewrite`.

**Choosing between them** - `axon-legacy` wins if **any** row applies:

| Caller's situation | Strategy |
|---|---|
| Unfinished AF4 saga instances must run to completion inside the AF5 application | **axon-legacy** |
| The AF5 application should keep starting new saga instances | **axon-legacy** |
| The process needs framework-managed deadlines | **axon-legacy** - AF5 core has no deadline scheduling at all, so `axon-legacy` is the only place it can come from |
| None of the above: nothing in flight to run in-app, only new processes start here, and timeouts will be implemented by hand | **stateful-rewrite** |

`axon-legacy` is marked `(Recommended)` unconditionally, so `auto=true` resolves to it every time. Having a saga in
the codebase at all is itself evidence that instances may be in flight, and `stateful-rewrite` silently strands them -
that is never a safe automatic judgment call.

The baseline **skip** option remains the "defer" path: leave the saga on its AF4 shape and decide later.

### B1 - Deadlines are not ported to `axon-legacy` yet

*Applies to strategy `axon-legacy` only.*

**Fires when:** the chosen strategy is `axon-legacy` AND
`grep -nE '@DeadlineHandler|DeadlineManager|EventScheduler|deadlineManager\.' $SOURCE` matches.

`axon-legacy` ports the saga and saga-store APIs but **not** `DeadlineManager`, `@DeadlineHandler` or the event
scheduler (upstream issue #5006). The `org.axonframework.deadline.*` imports do not resolve on AF5, so the saga cannot
compile as-is, and the timeout's replacement carries business meaning the recipe cannot invent.

Recipe-specific Options alongside the three baselines:

- [ ] **comment-out-deadlines** - migrate the rest of the saga onto `axon-legacy` and comment out the `DeadlineManager`
  field, every `deadlineManager.schedule(...)` / `cancelSchedule(...)` / `cancelAllWithinScope(...)` call site, every
  `@DeadlineHandler` method and the `org.axonframework.deadline.*` imports, each marked
  `// TODO AF5: no deadline support in axon-legacy yet (#5006) - design the replacement`. The saga compiles and keeps
  receiving events, **but its timeouts silently stop firing** until the caller wires a scheduler.
- [ ] **skip** *(Recommended)* - leave `$SOURCE` on its AF4 shape. The saga and its deadlines drain in an AF4
  deployment kept alive alongside the AF5 application, per `sagas.adoc` § "Migrating an application with running
  sagas". Queue moves on.

Mark **skip** `(Recommended)` so `auto=true` never silently disables a live timeout.

Under `stateful-rewrite` this blocker does **not** fire: accepting hand-built timeouts is part of choosing that
strategy. Deadline code is commented out by Step 5 of that Toolbox and reported as required follow-up.

### B2 - AF4 processor name cannot be determined

*Applies to strategy `axon-legacy` only.*

**Fires when:** `$SOURCE` carried **no** `@ProcessingGroup`, **and** a grep for
`assignProcessingGroup|SagaConfiguration|registerSaga` across configuration classes matches `$SOURCE`'s type or a
group name that is not `<SimpleName>Processor`.

Token stores are keyed on the processor name. In AF5 a legacy saga's processor is named `<SimpleName>Processor` unless
`@Namespace` overrides it. If the AF4 deployment used a different name and the recipe cannot read it from the source,
the migrated processor starts at the head of the stream and **every event published before that token was written is
never delivered to the sagas still running** - silent data loss for in-flight processes.

Recipe-specific Option alongside the three baselines:

- [ ] **name-processor** - caller supplies the AF4 processor name; the recipe re-enters and adds
  `@Namespace("<name>")` to `$SOURCE`.

Leave **skip** as the implicit recommendation - guessing a token key is never safe to auto-apply.

### Unmet project prerequisites

- Strategy `axon-legacy` chosen but `axon-legacy` does not resolve for the project's Axon 5 version - surface as
  Blocker `prerequisite-legacy-unavailable`, naming the resolved Axon version. Saga support landed in `axon-legacy`
  5.4.0.
- Project does not compile pre-recipe - surface as Blocker `prerequisite-not-compiling`.

## Out of Scope

- **AF5-native process redesign** - Workflow, state from context events, vertical slices. See the banner.
- Removing `@StartSaga` - that stops new saga instances from being created. Under `axon-legacy` it is left in place:
  behaviour-preserving, and exactly what a caller who chose that strategy to keep starting instances wants. Under
  `stateful-rewrite` the annotation disappears with the rest of the AF4 surface.
- Designing the deadline replacement mechanism (poller interval, scheduler, error handling).
- Retiring the saga, its store table or its rows once drained.
- Cross-saga / cross-context correlation redesign (note in NOTES; the caller designs the state schema).
- Sibling sagas, aggregates, projectors.
- Event-store or token-store schema changes.
- Logging, formatting, package renames.

## Applicable

Surface check on `$SOURCE`. Cheap reads only.

Decision rule (top-down; first match wins):

1. **Aggregate** - `@Aggregate` / `@AggregateRoot` AND `@EventSourcingHandler`. -> **Rejected** (route to aggregate
   recipe).
2. **Event-processor** - `@ProcessingGroup` / `@Namespace` AND `@EventHandler`, no `@SagaEventHandler`. -> **Rejected**
   (route to event-processor recipe).
3. **Saga AF4 shape** - `@Saga` OR any method annotated `@SagaEventHandler` / `@StartSaga` / `@EndSaga`. -> **continue**.
4. **Already rewritten** - no `@Saga`, no `@SagaEventHandler`, class is `@Component @DisallowReplay` with
   `@EventHandler` methods. -> **continue** (no live AF4 constructs, so B0 does NOT fire; the Success Criteria
   pre-Apply check decides idempotent-Success).
5. **None of the above** -> **Rejected**.

Predicate 3 matches both an untouched AF4 saga and one the OpenRewrite legacy pass already rewrote - the annotations
are identical in AF4 and `axon-legacy`. Step 1 of the `axon-legacy` Toolbox tells the two apart.

## Success Criteria

Success Criteria are evaluated **only once a strategy is chosen and the recipe is executing it** (a
BLOCKER_RESOLUTION re-entry carrying a strategy hint), or when `$SOURCE` is already migrated (Applicable predicate 4).
On a first visit with no strategy chosen, the recipe returns Blocker B0 before reaching this section.

Extends DEFAULT.md baseline. Aggregation rule: **all match (AND)** - DEFAULT.md baseline AND the criteria for the
chosen strategy.

### Strategy `axon-legacy`

1. **`axon-legacy` on the module's compile classpath**, and `axon-legacy-test` on its test classpath when a
   `SagaTestFixture` test is in scope.
2. **No static `SagaLifecycle` calls.** `grep -nE '(^|[^.\w])SagaLifecycle\.(associateWith|removeAssociationWith|end|associationValues)' $SOURCE`
   returns nothing. AF5's `SagaLifecycle` is an interface - every call goes through a handler parameter.
3. **No injected messaging or collaborator fields.** `$SOURCE` declares no `CommandGateway`, `EventGateway`,
   `QueryGateway` or `@Autowired` / `@Inject` field. AF5 does not inject into legacy saga fields.
4. **No `@ProcessingGroup`.** If the AF4 class carried one, an `@Namespace` with **the identical value** is present
   (`org.axonframework.messaging.core.annotation.Namespace`).
5. **Every `@SagaEventHandler` returns `void`** (or Kotlin `Unit`). No `CompletableFuture`, `Mono`, `Publisher`.
6. **`configuration=spring`:** `$SOURCE` is `public`, has an accessible no-argument constructor, and is
   component-scanned (or declared by a `@Scope("prototype")`-annotated `@Bean` method).
   **`configuration=native`:** `$SOURCE` is registered through `Sagas.of($SOURCE.class)` on an event processor, and a
   `SagaStore` component is registered.
7. **Every `SagaTestFixture` is closed.** For each test class in scope constructing a `SagaTestFixture`, either an
   `@AfterEach` calls `close()` / `stop()` on it, or it is held in a try-with-resources block. Verify with
   `grep -nE 'new SagaTestFixture' <test>` and match each hit against a `close()` / `stop()` / try-with-resources.

### Strategy `stateful-rewrite`

1. **No live AF4 saga constructs** on `$SOURCE`. None of the following appear as uncommented code:
   `org.axonframework.spring.stereotype.Saga`, `org.axonframework.modelling.saga.SagaEventHandler`,
   `org.axonframework.modelling.saga.StartSaga` / `EndSaga` / `SagaLifecycle` imports, or the `@Saga` /
   `@SagaEventHandler` / `@StartSaga` / `@EndSaga` annotations.
2. **`@Component @DisallowReplay` present** at class level (`org.springframework.stereotype.Component`,
   `org.axonframework.messaging.eventhandling.replay.annotation.DisallowReplay`).
3. **AF5 `@EventHandler` import** present: `org.axonframework.messaging.eventhandling.annotation.EventHandler`.
4. **State entity file exists** - a `*State` file (`.java`/`.kt`) in the same package with `@Entity` and `@Id` on the
   primary key field.
5. **Repository file exists** - a `*StateRepository` file extending `JpaRepository<StateClass, IdType>` (Java
   `extends`, Kotlin `:`) in the same package.

When deadlines were present, the commented-out deadline code is exempt from criterion 1 (it is not code); criteria 1-5
apply to the live parts. The deadline follow-up is reported in NOTES, not failed.

### Verification

Invoke `axon4to5-isolatedtest` per the DEFAULT.md template.

**Strategy `axon-legacy`** - two recipe-specific inputs:

- `extra-deps: [org.axonframework:axon-legacy]`, plus `org.axonframework:axon-legacy-test` when a `SagaTestFixture`
  test is in scope. The isolated scope inherits the module's dependencies, so this is usually already satisfied by the
  `axon-legacy` entry the OpenRewrite legacy pass added - pass it explicitly only when the isolated compile reports
  `package org.axonframework.modelling.saga does not exist`.
- `test-sources` **includes** the saga's `SagaTestFixture` test. It survives the migration: `axon-legacy-test` ports
  `SagaTestFixture` under its AF4 package `org.axonframework.test.saga`. Its deadline-related methods
  (`whenTimeElapses`, `expectScheduledDeadline`, ...) throw `UnsupportedOperationException` - see § Gotchas.

**Strategy `stateful-rewrite`** - run `grep -rn "SagaTestFixture\|AxonTestFixture" src/test`. An existing saga test
will not compile after the rewrite (the rewritten class is no longer a saga, so `SagaTestFixture` has nothing to
drive). **Do not block on it** - exclude it from `test-sources` (compile the saga + new files only), flag "saga test
needs manual rewrite" as a `no-test-coverage` Learning, and proceed. Invoke with `test-sources: []` (compile-only) and
grep for lingering AF4 imports as a proxy before concluding Success.

## References

- [sagas.adoc](../../docs/paths/sagas.adoc) - *apply-condition:* always. The `axon-legacy` module, Spring Boot
  autoconfiguration, processor assignment, saga-store selection, behaviour changes from AF4, the AF4-to-AF5 concept
  mapping, and the drainage strategy.
- [openrewrite-code-conversion.adoc](../../docs/openrewrite-code-conversion.adoc) - *apply-condition:* strategy
  `axon-legacy` AND Step 1 finds an AF4 construct the legacy OpenRewrite pass should have rewritten.
- [messages.adoc](../../docs/paths/messages.adoc) - *apply-condition:* always. Covers `getPayload()` / `getMetaData()`
  -> `payload()` / `metaData()` accessor renames inside handler bodies.
- [test-fixtures.adoc](../../docs/paths/test-fixtures.adoc) - *apply-condition:* a test class using `SagaTestFixture`
  or `AxonTestFixture` is in scope.
- [projectors-event-processors.adoc](../../docs/paths/projectors-event-processors.adoc) - *apply-condition:*
  `configuration=native`, or processor properties for `$SOURCE`'s processor are in scope, or strategy
  `stateful-rewrite` (the rewritten `@Component` needs registering as an event processor).

## Toolbox

The procedures below execute **only after B0 resolved to a strategy** and apply only to that strategy. For `skip` /
`revert` / `solve-manually` the recipe applies no edits.

---

## Toolbox - strategy `axon-legacy`

### Step 1 - Establish what the OpenRewrite legacy pass already did

The orchestrator's pre-step 2 runs `Axon4ToAxon5Legacy` as part of `UpgradeAxon4ToAxon5` / `UpgradeAxon4ToAxoniq5`. It
adds `axon-legacy` when saga types are detected and rewrites lifecycle + command dispatch. Grep `$SOURCE` for its
output:

| Grep | Pass landed | Pass did NOT land |
|---|---|---|
| `SagaLifecycle.` with a class-name select | absent | present |
| `SagaLifecycle` as a `@SagaEventHandler` parameter | present (when the saga uses lifecycle calls) | absent |
| `CommandGateway` field | absent | present |
| `CommandDispatcher` as a `@SagaEventHandler` parameter | present (when the saga dispatches) | absent |

If the pass did not land (`skip-openrewrite=true`, or a recipe artifact older than the one carrying
`Axon4ToAxon5Legacy`), apply Steps 2 and 3 by hand - they reproduce it exactly. Record a `project-shape` Learning
naming which case held.

### Step 2 - Static `SagaLifecycle` -> handler parameter

AF5's `SagaLifecycle` is a `ProcessingContext`-scoped **interface**; the AF4 `ThreadLocal`-backed statics are gone.
Add a `SagaLifecycle` parameter to every `@SagaEventHandler` that uses lifecycle operations and re-target the calls.
Reuse an existing `SagaLifecycle` parameter if one is already declared.

```java
// AF4
@SagaEventHandler(associationProperty = "rentalId")
public void on(PaymentPrepared event) {
    SagaLifecycle.associateWith("paymentId", event.paymentId());
    SagaLifecycle.end();
}

// AF5 (axon-legacy)
@SagaEventHandler(associationProperty = "rentalId")
public void on(PaymentPrepared event, SagaLifecycle sagaLifecycle) {
    sagaLifecycle.associateWith("paymentId", event.paymentId());
    sagaLifecycle.end();
}
```

Import stays `org.axonframework.modelling.saga.SagaLifecycle`. Applies to `associateWith`, `removeAssociationWith`,
`end` and `associationValues`, including static-imported forms.

### Step 3 - `CommandGateway` field -> `CommandDispatcher` parameter

Add `CommandDispatcher commandDispatcher` (`org.axonframework.messaging.commandhandling.gateway.CommandDispatcher`) to
every dispatching `@SagaEventHandler`, then delete the field and its injection once no reference remains.

| AF4 call | AF5 replacement | Semantics |
|---|---|---|
| `commandGateway.send(cmd)` | `commandDispatcher.send(cmd)` | fire-and-forget, unchanged |
| `commandGateway.sendAndWait(cmd)` | `FutureUtils.joinAndUnwrap(commandDispatcher.send(cmd).getResultMessage())` | stays synchronous; the original exception type is preserved |

`FutureUtils` is `org.axonframework.common.FutureUtils`. Do **not** return the future from the handler - see Step 5.

### Step 4 - Remaining injected collaborators -> handler parameters

*Apply-condition:* `$SOURCE` declares any field beyond the saga's own state - a service, a repository, a clock.

AF5 has no `ResourceInjector` / `SpringResourceInjector`: nothing is injected into a legacy saga's fields. **OpenRewrite
does not do this step** - it only knows the gateway types. For each such field, add it as a parameter to every
`@SagaEventHandler` that uses it, then delete the field and any `@Autowired` / `@Inject` annotation and constructor
injection. Axon resolves the parameter the same way it does for any other event handler, including Spring beans.

Fields holding the saga's **own state** stay - that is the serialized saga instance, and it is what the `SagaStore`
persists.

### Step 5 - Keep handlers synchronous

*Apply-condition:* a `@SagaEventHandler` returns anything other than `void` / `Unit`.

A legacy saga's handler must complete on the invoking thread so the `SagaStore` update runs inside that thread's
transaction; a handler returning incomplete asynchronous work fails with `SagaExecutionException`. Join the result
inside the handler and return `void`. AF4 ignored saga handler return values, so joining is behaviour-preserving.

### Step 6 - `@ProcessingGroup` -> `@Namespace`, value unchanged

*Apply-condition:* `$SOURCE` carried `@ProcessingGroup`, or B2 was resolved with `name-processor`.

```java
// AF4: @Saga @ProcessingGroup("orders")
@Saga
@Namespace("orders")
public class OrderSaga { /* ... */ }
```

`@Namespace` is `org.axonframework.messaging.core.annotation.Namespace`. **The value must be carried over verbatim** -
it is the processor name the existing token is keyed on. Dropping the annotation renames the processor to
`<SimpleName>Processor`, the AF4 token is not found, and in-flight sagas lose every event published before the new
token is written.

Two saga classes sharing a `@Namespace` value share one processor, reproducing the AF4 processing-group behaviour. A
saga and an ordinary event handler resolving to the same processor name fail startup with
`DuplicateModuleRegistrationException`.

### Step 7 - Wiring

**`configuration=spring`** - nothing to write. Autoconfiguration activates once `axon-legacy` sits next to
`axon-spring-boot-starter`; a component-scanned `@Saga` class is discovered, gets its own pooled streaming processor
and a saga store resolved from the context. Verify only Success Criterion 6: the class is `public`, has an accessible
no-arg constructor, and is component-scanned (a plain `@Bean` method ignores the `@Scope("prototype")` that `@Saga`
requires - annotate the bean method with `@Scope("prototype")` when the class cannot be scanned).

Properties targeting the saga's processor need bracket notation, because relaxed binding lowercases a dotted key and
then silently fails to match the mixed-case derived name:

```properties
axon.eventhandling.processors[OrderSagaProcessor].mode=subscribing
```

**`configuration=native`** - register the saga as an ordinary `EventHandlingComponent` built by
`Sagas.of($SOURCE.class)` (`org.axonframework.modelling.saga.configuration.Sagas`), and register a `SagaStore`
component:

```java
MessagingConfigurer.create()
                   .componentRegistry(cr -> cr.registerComponent(SagaStore.class, c -> new InMemorySagaStore()))
                   .eventProcessing(processing -> processing.subscribing(
                           subscribing -> subscribing.defaultProcessor(
                                   "orders",
                                   components -> components.declarative("Saga[OrderSaga]", Sagas.of(OrderSaga.class)))));
```

Keep the AF4 processor name as the processor name here too - same token-store reasoning as Step 6.

### Step 8 - Tests: keep `SagaTestFixture`, add `close()`

*Apply-condition:* a test class in scope uses `SagaTestFixture`.

Add `org.axonframework:axon-legacy-test` in test scope. `SagaTestFixture` keeps its AF4 package
(`org.axonframework.test.saga`) and its given-when-then API. **Keep using it** - do NOT rewrite the test to
`AxonTestFixture`.

**One change is mandatory: the fixture must be closed.** New in AF5, `SagaTestFixture` runs a started
`AxonConfiguration` holding a live event processor; AF4's fixture held nothing that needed stopping. The class now
implements `AutoCloseable` (`close()`, aliased by `stop()`). An unclosed fixture leaves that processor running past the
end of the test.

Add an `@AfterEach` to **every** test class that constructs a `SagaTestFixture`:

```java
class PaymentSagaTest {

    private final SagaTestFixture<PaymentSaga> fixture = new SagaTestFixture<>(PaymentSaga.class);

    @AfterEach
    void tearDown() {
        fixture.close();
    }

    // @Test methods unchanged
}
```

`org.junit.jupiter.api.AfterEach`. When the fixture is a local variable rather than a field, a try-with-resources
block is equivalent and needs no `@AfterEach` - `close()` runs even when the test fails, which is the point.

Apply this to every fixture in the class, not just the first: a test class holding two fixtures needs both closed.

---

## Toolbox - strategy `stateful-rewrite`

### Step 1 - Class-level annotation swap

1. Remove `@Saga` and its import (`org.axonframework.spring.stereotype.Saga`).
2. Add `@Component` (`org.springframework.stereotype.Component`).
3. Add `@DisallowReplay` (`org.axonframework.messaging.eventhandling.replay.annotation.DisallowReplay`).
4. Remove `@Autowired` on `CommandGateway` / `DeadlineManager` fields (constructor-injected or removed below).

### Step 2 - Create JPA state entity

Name: `<SagaName>State` (e.g. `PaymentSaga` -> `PaymentState`). Same package as `$SOURCE`.

```java
@Entity
public class <Name>State {
    @Id
    private <IdType> <correlationKey>;   // the saga's primary association key
    // additional correlation fields and business state fields
    private Status status;
    private long timestamp;              // creation or "prepared" time - used by a deadline-replacement poller

    public <Name>State() {}              // Hibernate no-arg constructor (required)

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

### Step 3 - Create JPA repository

```java
@Repository
public interface <Name>StateRepository extends JpaRepository<<Name>State, <IdType>> {
    List<<Name>State> findAllByTimestampLessThanAndStatusIn(long timestamp, <Name>State.Status... status);
}
```

`findAllByTimestampLessThanAndStatusIn` is required if the caller later designs a deadline-replacement poller;
harmless when no deadline was present.

> The Step 2/3 templates show Java. When `$SOURCE` is Kotlin, emit the Kotlin equivalent instead (`.kt` file,
> `interface <Name>StateRepository : JpaRepository<...>`, `class` for the `@Entity`) - same annotations and JPA
> contract. Match `$SOURCE`'s language; never add a `.java` file to a Kotlin saga's package.

### Step 4 - Migrate event handlers

| AF4 | AF5 |
|-----|-----|
| `@StartSaga @SagaEventHandler(associationProperty = "X")` | `@EventHandler` - body saves new state row; first param is the event |
| `@SagaEventHandler(associationProperty = "X")` | `@EventHandler` - body looks up state by `event.X()` |
| `@EndSaga @SagaEventHandler(associationProperty = "X")` | `@EventHandler` - body updates state to terminal status |
| `SagaLifecycle.associateWith("key", value)` | REMOVE - state lookup uses the event's natural field |
| `SagaLifecycle.removeAssociationWith(...)` | REMOVE |
| `SagaLifecycle.end()` | REMOVE - call `repository.deleteById(...)` or set terminal status instead |
| `SagaLifecycle.associateWith("secondaryKey", value)` | Store `value` in the state entity so future handlers can look it up |

Every `@EventHandler` that dispatches commands gets `CommandDispatcher commandDispatcher` as a method parameter.
Remove the class-level `CommandGateway` field.

### Step 5 - Comment out DeadlineManager / @DeadlineHandler (when deadlines present)

*Apply-condition:* `DeadlineManager` field OR `@DeadlineHandler` method detected on `$SOURCE`.

Hand-built timeouts are the accepted premise of this strategy, but the recipe cannot design the replacement. Do NOT
remove deadline code - comment it out, annotate it, and report it as required follow-up in NOTES:

1. Comment out the `DeadlineManager` field:
   ```java
   // TODO AF5: DeadlineManager removed - design replacement (e.g. @Scheduled poller on the state entity's timestamp)
   // private transient DeadlineManager deadlineManager;
   ```
2. Comment out every `deadlineManager.schedule(...)` / `cancelAllWithinScope(...)` call site, inline in the handler.
3. Comment out every `@DeadlineHandler` method, annotation included.
4. Keep the `org.axonframework.deadline.*` imports as comments so the caller knows what was there.

The structural migration still succeeds; the deadline replacement is a follow-up the caller owns.

### Step 6 - Constructor injection

Replace `@Autowired` field injection with constructor injection for the remaining dependencies
(`CommandGateway`, `<Name>StateRepository`, ...):

```java
public <SagaName>(CommandGateway commandGateway, <Name>StateRepository repository) {
    this.commandGateway = commandGateway;
    this.repository = repository;
}
```

## Use cases

- [01-legacy-spring-boot.md](use-cases/01-legacy-spring-boot.md) - *apply-condition:* strategy `axon-legacy` AND
  `configuration=spring` AND no deadline constructs. Lifecycle, command dispatch, injected collaborator,
  `@ProcessingGroup`, and the surviving `SagaTestFixture` test.
- [02-legacy-native-configurer.md](use-cases/02-legacy-native-configurer.md) - *apply-condition:* strategy
  `axon-legacy` AND `configuration=native`. Registering the saga with `Sagas.of(...)` and a `SagaStore` component.
- [03-legacy-deadline-blocker.md](use-cases/03-legacy-deadline-blocker.md) - *apply-condition:* strategy `axon-legacy`
  AND `$SOURCE` has deadline constructs (B1 fires).
- [04-rewrite-jpa-state-spring.md](use-cases/04-rewrite-jpa-state-spring.md) - *apply-condition:* strategy
  `stateful-rewrite` AND `$SOURCE` has no `DeadlineManager` (simple saga with `@StartSaga` / `@EndSaga` /
  `SagaLifecycle.associateWith`).
- [05-rewrite-deadline-comment-out.md](use-cases/05-rewrite-deadline-comment-out.md) - *apply-condition:* strategy
  `stateful-rewrite` AND `$SOURCE` injects `DeadlineManager` OR has `@DeadlineHandler` methods.
- [06-rejected-not-a-saga.md](use-cases/06-rejected-not-a-saga.md) - *apply-condition:* `$SOURCE` is an aggregate or
  projector (Applicable predicate 1 or 2 fires; routing reference only).

## Gotchas

### Both strategies

- **The first run of this recipe is a decision, not an edit.** A first visit on an AF4 saga always returns Blocker B0
  with the strategy Options; no source file changes until the caller picks. Do not "helpfully" start editing first.
- **`stateful-rewrite` abandons the saga store.** Rows written by AF4 are never read again - any instance still in
  flight stops progressing, silently. That is why `axon-legacy` is the unconditional recommendation and the `auto=true`
  choice: the recipe cannot see the saga store's contents.
- **AF5 core has no deadline scheduling at all.** `DeadlineManager` / `@DeadlineHandler` exist only in the AF4 surface
  that `axon-legacy` carries forward, and they are not ported there yet (#5006). So "I need framework deadlines" always
  routes to `axon-legacy`, and today still lands on B1.
- **`CommandDispatcher` vs `CommandGateway`.** In-handler dispatch uses `CommandDispatcher` as a method parameter. A
  scheduled poller or any other non-handler method is NOT an event handler - it must use a constructor-injected
  `CommandGateway` field. Having both in one class is correct.
- **`@Saga` had two common import paths** in AF4 codebases: `org.axonframework.spring.stereotype.Saga` (the one
  `axon-legacy` carries forward) and `org.axonframework.extension.spring.stereotype.Saga`. Grep for both.

### Strategy `axon-legacy`

- **The saga class is not rewritten.** `@Saga`, `@SagaEventHandler`, `@StartSaga`, `@EndSaga` and `AssociationValue`
  all keep their AF4 package names. If you find yourself creating a state entity here, you picked the wrong strategy.
- **`SagaLifecycle` is an interface in AF5.** The AF4 statics are gone, so a missed static call is a compile error, not
  a runtime surprise. Grep is a reliable check.
- **OpenRewrite only moves the gateway fields.** Every other injected collaborator is Step 4's manual work; the
  automated pass leaves it untouched and the saga then NPEs at runtime rather than failing to compile.
- **Dropping `@ProcessingGroup` loses events.** See Step 6. This is the single highest-risk edit in the recipe.
- **`@StartSaga` is deprecated but still functional.** A ported `@StartSaga` handler keeps creating new instances -
  which is the point if that is why the strategy was chosen. Removing it is the caller's drainage decision.
- **A saga's processor starts at the head of the stream.** It ignores events published before it first started,
  matching the AF4 `TrackingEventProcessor` default for sagas. No `axon.eventhandling.processors.<name>.*` property
  changes that; a replay needs an explicit initial token via `SagaProcessorDefinition`.
- **`initial-segment-count` does not apply to a saga's processor** - it starts with one segment; raise it with a
  `SagaProcessorDefinition`. Segments do not split the stream: every segment reads every event and keeps only the
  sagas it owns.
- **`mode=subscribing` in a multi-instance deployment gives every instance its own copy of the same saga** - a
  subscribing processor has no segments and no token store. Keep sagas pooled.
- **Dead-letter queues have no effect for a saga's processor**, even when enabled by name.
- **`SagaEntry` and `AssociationValueEntry` keep their AF4 FQN** (`org.axonframework.modelling.saga.repository.jpa`),
  so an existing `@EntityScan(basePackageClasses = SagaEntry.class)` still compiles and still resolves. Spring Boot
  registers both with the persistence unit automatically when a `JpaSagaStore` is selected.
- **`SagaTestFixture` survives via `axon-legacy-test` but must now be closed.** It runs a started `AxonConfiguration`
  with a live event processor and implements `AutoCloseable`; AF4's fixture did not. The test still compiles without
  an `@AfterEach`, so nothing points at the omission - it shows up later as processors left running across the suite.
  See Step 8.
- **`SagaTestFixture`'s deadline and event-scheduler methods throw** `UnsupportedOperationException` ("...not supported:
  deadlines and the event scheduler have not been ported into axon-legacy yet"). A saga test that calls
  `whenTimeElapses(...)` fails at runtime, not at compile time - pair it with B1.
- **A `SagaStore` bean is resolved by convention.** User `SagaStore` bean, else `JpaSagaStore` (an
  `EntityManagerFactory` is present), else `JdbcSagaStore` (a `DataSource` is present), else `InMemorySagaStore`.
  `@Saga(sagaStore = "beanName")` overrides it per saga type. An in-memory fallback silently loses in-flight sagas on
  restart - check the project actually has the JPA/JDBC store it had on AF4.
- **Declaring a `<sagaBeanName>$$Registrar` bean disables discovery for that saga** - and, as an AF4 behaviour ported
  unchanged, aborts discovery for every saga after it in bean-definition order.

### Strategy `stateful-rewrite`

- **`@DisallowReplay` is mandatory.** Without it, a full replay re-fires every `@EventHandler` and creates duplicate
  state rows. `@DisallowReplay` blocks the processor during replay so the JPA state is built from live events only.
- **`SagaLifecycle.associateWith("secondaryKey", value)` becomes a state field.** A second association key (e.g. a
  `paymentReference` added after a `bikeId` start) is set in the start handler; later handlers look it up via
  `repository.findById(event.paymentReference())` - no Axon-level routing needed.
- **Saga fields become repository lookups.** Instance fields that survived between event invocations become fields on
  the JPA entity. Every handler that reads them must look the entity up first.
- **No-arg JPA constructor.** Hibernate requires one on `@Entity` classes. Always generate `public <Name>State() {}`.
- **`DeadlineManager.cancelAllWithinScope(...)` in `@EndSaga` handlers** - comment it out with the other deadline
  calls. A poller replacement naturally skips terminal-status rows via a `statusIn(PENDING, PREPARED)` predicate.
- **Processor wiring is out of scope but important.** The rewritten `@Component` needs an `EventProcessorDefinition`
  (Spring) or `MessagingConfigurer.eventProcessing(...)` (native) to register as an event processor. Flag in NOTES with
  a pointer to `projectors-event-processors.adoc`.
- **Existing saga tests do not survive.** The rewritten class is no longer a saga, so `SagaTestFixture` has nothing to
  drive. Exclude the test from the isolated-test compile, flag "saga test needs manual rewrite" as a
  `no-test-coverage` Learning, and leave it for the caller (a Mockito unit test mocking the repository +
  `CommandDispatcher` is the usual replacement). Do NOT silently rewrite it.
- **`@EntityScan(basePackageClasses = SagaEntry.class)` becomes meaningless** once the saga store is abandoned.
  Replace with the new state entity class (`<SagaName>State.class`). For modules that don't depend on the module
  containing the state entity, use `basePackages = "..."` (string-based scan) to avoid a cross-module compile
  dependency.

## Result

Inherits DEFAULT.md baseline.

### Blocker (B0 - strategy decision, the primary first-run outcome)

Say **"return BLOCKER"**, then **MUST emit** the result block (schema: FLOW.md § Result). `Recipe:` field is
`axon4to5-saga`. NOTES summarise the saga's detected signals (deadlines? command dispatch? `@ProcessingGroup`?), state
that `axon-legacy` is recommended, and name the fact the caller must supply: whether unfinished AF4 instances have to
run in this application and whether it should keep starting new ones.

```
return BLOCKER

> **Result:** 🚧 Blocker
> **Source:** `com.example.paymentsaga.PaymentSaga`
> **Recipe:** axon4to5-saga
>
> **Notes:** Strategy decision. `PaymentSaga` correlates on `bikeId` / `paymentReference`, dispatches commands, and has no `@DeadlineHandler` / `DeadlineManager`. Recommend **axon-legacy**: it keeps the class and its existing saga-store rows, so anything still in flight finishes normally. Pick `stateful-rewrite` only if no unfinished AF4 instance needs to run in this application, the AF5 app only starts new processes, and you will implement timeouts yourself. No edits applied until you choose.
>
> **Learnings:**
> ## YYYY-MM-DD - `PaymentSaga` correlates on two keys and has no deadlines
> **Trigger:** blocker
> **Where:** `com.example.paymentsaga.PaymentSaga`
> **Surprise:** Project-specific shape: a second association key (`paymentReference`) is added at runtime via `SagaLifecycle.associateWith`, so a `stateful-rewrite` here would need that key as a state-entity field rather than the `@Id`. Worth knowing before the strategy is picked, not after.
> **Resolution:** Recommended `axon-legacy`; no edits applied until the caller picks.
>
> **Options:**
> - [ ] **axon-legacy** *(Recommended)* - add `axon-legacy`; keep `PaymentSaga` as-is; lifecycle and dispatch move to handler parameters; existing saga-store rows keep working.
> - [ ] **stateful-rewrite** - rebuild as `@Component @DisallowReplay` over a new JPA `PaymentState` entity + repository. Abandons the existing saga-store rows.
> - [ ] **skip** - leave `PaymentSaga` on its AF4 shape; decide later; queue moves on.
> - [ ] **revert** - no edits applied yet; equivalent to skip.
> - [ ] **solve-manually** - pause; caller decides and edits by hand, then re-invokes.
```

For B1 (deadlines) and B2 (processor name), NOTES name the blocker and its location and carry that blocker's own
Options; B1's example lives in [03-legacy-deadline-blocker.md](use-cases/03-legacy-deadline-blocker.md).

### Success

Say **"return SUCCESS"**, then **MUST emit** the result block. `Recipe:` field is `axon4to5-saga`. NOTES must name the
strategy executed, plus:

**`axon-legacy`:**
1. The saga now runs on `axon-legacy` - it was **not** redesigned.
2. Any collaborator moved from a field to a handler parameter (Step 4) - a runtime-behaviour change worth review.
3. If the caller's plan is drainage, `@StartSaga` is still active and still creates instances; removing it is what
   stops them. Point at `sagas.adoc` § "Migrating an application with running sagas".

**`stateful-rewrite`:**
1. The two new files created (state entity + repository).
2. Processor wiring not handled - the caller should add an `EventProcessorDefinition` per
   `projectors-event-processors.adoc`.
3. Existing saga-store rows are now orphaned; any AF4 instance still in flight has stopped progressing.
4. If deadlines were present, the commented-out deadline code is a **required follow-up**.
5. Any existing saga test was left for manual rewrite (`no-test-coverage` Learning).

### Rejected

Say **"return REJECTED"**, then **MUST emit** the result block. `Recipe:` field is `axon4to5-saga`. NOTES must name the
failed `# Applicable` predicate (1 aggregate / 2 event-processor / 5 unrecognised) and the sister recipe to route to.

### Failure

Say **"return FAILURE"**, then **MUST emit** the result block. NOTES list failing Success Criteria + the last
grep/compiler error verbatim. Common failure shapes: under `axon-legacy`, `package org.axonframework.modelling.saga
does not exist` - the dependency did not reach the module that owns `$SOURCE` (check the module's own build file, not
the reactor parent); under `stateful-rewrite`, an AF4 saga import surviving the rewrite (grep for
`org.axonframework.modelling.saga` after the edit).
