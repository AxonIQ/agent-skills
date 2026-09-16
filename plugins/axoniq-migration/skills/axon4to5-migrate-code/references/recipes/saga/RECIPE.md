---
id: saga
title: Saga
description: Keeps an Axon Framework 4 Saga running on AF5 via axon-legacy - verifies the OpenRewrite legacy pass, moves injected collaborators to handler parameters, preserves the processor name.
order: 7
argument-hint: $SOURCE
---

# Saga

> **AF5 keeps AF4 sagas running through `axon-legacy`.** `@Saga`, `@SagaEventHandler`, `@StartSaga`, `@EndSaga`,
> `SagaLifecycle`, `AssociationValue` and every `SagaStore` implementation are ported to the `axon-legacy` module under
> their AF4 package names. A running saga is **not** rewritten: it keeps its class, its association values and its
> existing saga-store rows, so in-flight business processes drain normally.
>
> This recipe is therefore **mechanical, not a design decision**. The bulk of the code change is done by the
> `Axon4ToAxon5Legacy` OpenRewrite sub-recipe (pre-step 2 of the orchestrator); this recipe verifies that pass landed
> and fills the gaps OpenRewrite cannot close.
>
> **Out of scope by design: replacing the saga with an AF5-native process.** That is a redesign (Workflow, state in a
> repository, vertical slices), not a migration, and it conflicts with the skill's "same architecture as AF4" goal.
> Flag it in NOTES as the caller's follow-up; never start it here.

## Source

- `$SOURCE` (required) - FQN, file path, or simple class name of an AF4 saga. The class is annotated `@Saga`
  (`org.axonframework.spring.stereotype.Saga`) AND/OR carries at least one `@SagaEventHandler` method.

## Scope

- `$SOURCE` saga class.
- The build file of the module owning `$SOURCE` (`pom.xml` / `build.gradle[.kts]`) - `axon-legacy` dependency.
- `$SOURCE`'s test class when it uses `SagaTestFixture` - plus the test-scoped `axon-legacy-test` dependency.
- **`configuration=native` only:** the configuration class registering `$SOURCE` on a processor.
- `application.properties` / `application.yaml` entries keyed on `$SOURCE`'s processor name.

Scope grows during Research; never shrinks. Sibling sagas, aggregates, projectors are NOT in scope.

## Blocker

### B1 - Deadlines are not ported to `axon-legacy`

**Fires when:** `grep -nE '@DeadlineHandler|DeadlineManager|EventScheduler|deadlineManager\.' $SOURCE` matches.

`axon-legacy` ports the saga and saga-store APIs but **not** `DeadlineManager`, `@DeadlineHandler` or the event
scheduler (upstream issue #5006). The `org.axonframework.deadline.*` imports do not resolve on AF5, so the saga cannot
compile as-is, and the timeout's replacement (mechanism, interval, cancellation, error handling) carries business
meaning the recipe cannot invent.

Recipe-specific Options alongside the three baselines:

- [ ] **comment-out-deadlines** - migrate the rest of the saga onto `axon-legacy` and comment out the `DeadlineManager`
  field, every `deadlineManager.schedule(...)` / `cancelSchedule(...)` / `cancelAllWithinScope(...)` call site, every
  `@DeadlineHandler` method and the `org.axonframework.deadline.*` imports, each marked
  `// TODO AF5: no deadline support in axon-legacy yet (#5006) - design the replacement`. The saga compiles and keeps
  receiving events, **but its timeouts silently stop firing** - a real behavioural regression until the caller wires a
  scheduler of their own.
- [ ] **skip** *(Recommended)* - leave `$SOURCE` on its AF4 shape. The saga (and its deadlines) drain in an AF4
  deployment kept alive alongside the AF5 application, per `sagas.adoc` § "Migrating an application with running
  sagas". Queue moves on.

Mark **skip** `(Recommended)` so `auto=true` never silently disables a live timeout.

### B2 - AF4 processor name cannot be determined

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

- `axon-legacy` does not resolve for the project's Axon 5 version - surface as Blocker
  `prerequisite-legacy-unavailable`, naming the resolved Axon version. Saga support landed in `axon-legacy` 5.4.0.
- Project does not compile pre-recipe - surface as Blocker `prerequisite-not-compiling`.

## Out of Scope

- **Replacing the saga with an AF5-native process** (Workflow, state in a repository, vertical slices). See the banner.
- Removing `@StartSaga` - that stops new saga instances from being created and only makes sense once an AF5
  replacement handles the same trigger event. Behaviour-preserving default: leave it, flag it (see § Result).
- Designing a deadline replacement (see B1).
- Retiring the saga, its store table or its rows once drained.
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
4. **None of the above** -> **Rejected**.

Predicate 3 matches both an untouched AF4 saga and one the OpenRewrite legacy pass already rewrote - the annotations
are identical in AF4 and `axon-legacy`. Step 1 of the Toolbox tells the two apart.

## Success Criteria

Extends DEFAULT.md baseline. For `$SOURCE` and every in-scope file:

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

Aggregation rule: **all match (AND)** - DEFAULT.md baseline AND criteria 1-6.

### Verification

Invoke `axon4to5-isolatedtest` per the DEFAULT.md template. Two recipe-specific inputs:

- `extra-deps: [org.axonframework:axon-legacy]`, plus `org.axonframework:axon-legacy-test` when a `SagaTestFixture`
  test is in scope. The isolated scope inherits the module's dependencies, so this is usually already satisfied by the
  `axon-legacy` entry the OpenRewrite legacy pass added - pass it explicitly only when the isolated compile reports
  `package org.axonframework.modelling.saga does not exist`.
- `test-sources` **includes** the saga's `SagaTestFixture` test. Unlike an AF4 aggregate fixture, it survives the
  migration: `axon-legacy-test` ports `SagaTestFixture` under its AF4 package `org.axonframework.test.saga`. Its
  deadline-related methods (`whenTimeElapses`, `expectScheduledDeadline`, ...) throw `UnsupportedOperationException` -
  see § Gotchas.

## References

- [sagas.adoc](../../docs/paths/sagas.adoc) - *apply-condition:* always. The `axon-legacy` module, Spring Boot
  autoconfiguration, processor assignment, saga-store selection, behaviour changes from AF4, and the drainage strategy.
- [openrewrite-code-conversion.adoc](../../docs/openrewrite-code-conversion.adoc) - *apply-condition:* Step 1 finds an
  AF4 construct the legacy OpenRewrite pass should have rewritten. Names what the automated pass covers.
- [messages.adoc](../../docs/paths/messages.adoc) - *apply-condition:* handler bodies still call `getPayload()` /
  `getMetaData()`.
- [projectors-event-processors.adoc](../../docs/paths/projectors-event-processors.adoc) - *apply-condition:*
  `configuration=native`, or processor properties for `$SOURCE`'s processor are in scope.

## Toolbox

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

`FutureUtils` is `org.axonframework.common.FutureUtils`. Do **not** return the future from the handler - see
Step 5.

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

### Step 8 - Tests

*Apply-condition:* a test class in scope uses `SagaTestFixture`.

Add `org.axonframework:axon-legacy-test` in test scope. `SagaTestFixture` keeps its AF4 package
(`org.axonframework.test.saga`) and its given-when-then API, so the test compiles and runs unchanged. Do not rewrite it
to `AxonTestFixture`.

## Use cases

- [01-spring-boot-legacy-module.md](use-cases/01-spring-boot-legacy-module.md) - *apply-condition:*
  `configuration=spring` AND `$SOURCE` has no deadline constructs. Full before/after: lifecycle, command dispatch,
  injected collaborator, `@ProcessingGroup`, and the surviving `SagaTestFixture` test.
- [02-native-configurer-sagas.md](use-cases/02-native-configurer-sagas.md) - *apply-condition:*
  `configuration=native`. Registering the saga with `Sagas.of(...)` and a `SagaStore` component.
- [03-deadline-blocker.md](use-cases/03-deadline-blocker.md) - *apply-condition:* `$SOURCE` injects `DeadlineManager`
  or has `@DeadlineHandler` methods (B1 fires).
- [04-rejected-not-a-saga.md](use-cases/04-rejected-not-a-saga.md) - *apply-condition:* `$SOURCE` is an aggregate or
  projector (Applicable predicate 1 or 2 fires; routing reference only).

## Gotchas

- **The saga class is not rewritten.** `@Saga`, `@SagaEventHandler`, `@StartSaga`, `@EndSaga` and `AssociationValue`
  all keep their AF4 package names in `axon-legacy`. If you find yourself creating a state entity or swapping
  `@SagaEventHandler` for `@EventHandler`, you have left the recipe - that is a redesign, see § Out of Scope.
- **`SagaLifecycle` is an interface in AF5.** The AF4 statics are gone, so a missed static call is a compile error, not
  a runtime surprise. Grep is a reliable check.
- **OpenRewrite only moves the gateway fields.** Every other injected collaborator is Step 4's manual work; the
  automated pass leaves it untouched and the saga then NPEs at runtime rather than failing to compile.
- **Dropping `@ProcessingGroup` loses events.** See Step 6. This is the single highest-risk edit in the recipe.
- **`@StartSaga` is deprecated but still functional.** A ported `@StartSaga` handler keeps creating new instances. That
  is the behaviour-preserving default; removing it is the caller's drainage decision, taken once an AF5 replacement
  handles the same trigger event.
- **A saga's processor starts at the head of the stream.** It ignores events published before it first started -
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
- **`SagaTestFixture` survives via `axon-legacy-test`**, but its deadline and event-scheduler methods throw
  `UnsupportedOperationException` ("...not supported: deadlines and the event scheduler have not been ported into
  axon-legacy yet"). A saga test that calls `whenTimeElapses(...)` fails at runtime, not at compile time - pair it with
  B1.
- **A `SagaStore` bean is resolved by convention.** User `SagaStore` bean, else `JpaSagaStore` (an
  `EntityManagerFactory` is present), else `JdbcSagaStore` (a `DataSource` is present), else `InMemorySagaStore`.
  `@Saga(sagaStore = "beanName")` overrides it per saga type. An in-memory fallback silently loses in-flight sagas on
  restart - check the project actually has the JPA/JDBC store it had on AF4.
- **Declaring a `<sagaBeanName>$$Registrar` bean disables discovery for that saga** - and, as an AF4 behaviour ported
  unchanged, aborts discovery for every saga after it in bean-definition order.

## Result

Inherits DEFAULT.md baseline.

### Success

Say **"return SUCCESS"**, then **MUST emit** the result block (schema: FLOW.md § Result). `Recipe:` field is
`axon4to5-saga`. NOTES must state:

1. The saga now runs on `axon-legacy` - it was **not** redesigned.
2. **Drainage is the caller's follow-up**: `@StartSaga` is still active, so new instances keep being created. Removing
   it (once an AF5-native implementation handles the same trigger event) is what stops them; existing instances then
   run to completion and the legacy saga, its store table and the `axon-legacy` dependency can be retired. Point at
   `sagas.adoc` § "Migrating an application with running sagas".
3. Any collaborator moved from a field to a handler parameter (Step 4) - a runtime-behaviour change worth review.

### Blocker

Say **"return BLOCKER"**, then **MUST emit** the result block. `Recipe:` field is `axon4to5-saga`. NOTES name the
blocker (B1 deadlines / B2 processor name / a prerequisite) and its location.

Example (deadlines):

```
return BLOCKER

> **Result:** 🚧 Blocker
> **Source:** `com.example.paymentsaga.PaymentSagaWithDeadline`
> **Recipe:** axon4to5-saga
>
> **Notes:** B1 - `axon-legacy` ports the saga APIs but not deadlines (#5006). `PaymentSagaWithDeadline` injects `DeadlineManager` at `:24` and declares `@DeadlineHandler(deadlineName = "cancelPayment")` at `:58`; `org.axonframework.deadline.*` does not resolve on AF5. Everything else in this saga is a clean legacy-module migration. Recommend `skip` - draining this saga in an AF4 deployment keeps the timeout working, whereas commenting it out leaves the saga running with its compensation silently disabled.
>
> **Learnings:**
> ## YYYY-MM-DD - `PaymentSagaWithDeadline`'s 30s timeout drives compensation, not cleanup
> **Trigger:** blocker
> **Where:** `com.example.paymentsaga.PaymentSagaWithDeadline:58`
> **Surprise:** Project-specific: the deadline is not a housekeeping sweep but the only path that cancels an unpaid rental, and `SagaLifecycle.end()` is reached from the deadline handler alone. Commenting it out would leave saga rows that never terminate.
> **Resolution:** Halted with Options; recommended `skip`. No edits applied.
>
> **Options:**
> - [ ] **skip** *(Recommended)* - leave the saga on its AF4 shape; drain it in the AF4 deployment; queue moves on.
> - [ ] **comment-out-deadlines** - migrate onto `axon-legacy` and comment out the deadline code with `// TODO AF5:` markers. The saga compiles and receives events, but its timeouts stop firing until you wire a scheduler.
> - [ ] **revert** - no edits applied yet; equivalent to skip.
> - [ ] **solve-manually** - pause; caller designs the timeout replacement by hand, then re-invokes.
```

### Rejected

Say **"return REJECTED"**, then **MUST emit** the result block. `Recipe:` field is `axon4to5-saga`. NOTES must name the
failed `# Applicable` predicate (1 aggregate / 2 event-processor / 4 unrecognised) and the sister recipe to route to.

### Failure

Say **"return FAILURE"**, then **MUST emit** the result block. NOTES list failing Success Criteria + the last
grep/compiler error verbatim. Common failure shape: `package org.axonframework.modelling.saga does not exist` - the
`axon-legacy` dependency did not reach the module that owns `$SOURCE` (check the module's own build file, not the
reactor parent).
