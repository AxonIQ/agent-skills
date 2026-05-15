# 07 — Test fixture migration (`AggregateTestFixture` → `AxonTestFixture`)

**Why this case is interesting:** The fixture API surface changes shape: `new AggregateTestFixture<>(Type.class)` → `AxonTestFixture.with(<configurer>)`, the given/when/then DSL becomes fluent (`.given().events(...)`, `.when().command(...)`, `.then().events(...)`), and AF5 record-style accessors (`payload()` / `metaData()`) replace AF4 getters. Most importantly: assertion expectations flip in two specific cases — `AggregateNotFoundException` (instance handlers) and `EntityAlreadyExistsForCreationalCommandHandlerException` (static handlers) — and silently flipping these masks real behavioural regressions.

**Apply-condition:** `<target>Test` exists in `# Scope` AND uses `AggregateTestFixture`. (Skipped entirely when Blocker B3 fires — i.e. the test class uses `SagaTestFixture`; the recipe halts before reaching the test-fixture migration step.)

## Before (AF4)

```java
import org.axonframework.test.aggregate.AggregateTestFixture;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class CalendarTest {

    private AggregateTestFixture<Calendar> fixture;

    @BeforeEach
    void setUp() {
        fixture = new AggregateTestFixture<>(Calendar.class);
    }

    @Test
    void startsDayOne() {
        fixture.givenNoPriorActivity()
               .when(new StartDay("cal-1", 1, 1, 1))
               .expectEvents(DayStarted.event("cal-1", 1, 1, 1));
    }

    @Test
    void finishesCurrentDay() {
        fixture.given(DayStarted.event("cal-1", 1, 1, 1))
               .when(new FinishDay("cal-1", 1, 1, 1))
               .expectEvents(DayFinished.event("cal-1", 1, 1, 1));
    }

    @Test
    void finishWithoutStartedThrows() {
        fixture.givenNoPriorActivity()
               .when(new FinishDay("cal-1", 1, 1, 1))
               .expectException(AggregateNotFoundException.class);    // ← AF4 reflexive expectation
    }
}
```

## After (AF5)

```java
import org.axonframework.eventsourcing.configuration.EventSourcingConfigurer;
import org.axonframework.eventsourcing.configuration.EventSourcedEntityModule;
import org.axonframework.test.fixture.AxonTestFixture;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class CalendarTest {

    private AxonTestFixture fixture;

    @BeforeEach
    void setUp() {
        fixture = AxonTestFixture.with(
                EventSourcingConfigurer.create()
                        .registerEntity(EventSourcedEntityModule.autodetected(CalendarId.class, Calendar.class))
        );
    }

    @AfterEach
    void tearDown() {
        fixture.stop();
    }

    @Test
    void startsDayOne() {
        fixture.given().noPriorActivity()
               .when().command(new StartDay("cal-1", 1, 1, 1))
               .then().events(DayStarted.event("cal-1", 1, 1, 1));
    }

    @Test
    void finishesCurrentDay() {
        fixture.given().events(DayStarted.event("cal-1", 1, 1, 1))
               .when().command(new FinishDay("cal-1", 1, 1, 1))
               .then().events(DayFinished.event("cal-1", 1, 1, 1));
    }

    @Test
    void finishWithoutStartedFailsDomainRule() {
        // AF5 with no-arg @EntityCreator materialises an empty Calendar;
        // the instance handler runs and the domain rule fires — NOT AggregateNotFoundException.
        fixture.given().noPriorActivity()
               .when().command(new FinishDay("cal-1", 1, 1, 1))
               .then().exception(CanOnlyFinishCurrentDay.Violation.class);   // ← project's domain exception
    }
}
```

## What changed

- Type: `AggregateTestFixture<Calendar>` → `AxonTestFixture`. The generic parameter is gone; the entity is given to the configurer instead.
- Imports:
  - `org.axonframework.test.aggregate.AggregateTestFixture` → `org.axonframework.test.fixture.AxonTestFixture`
  - Add `org.axonframework.eventsourcing.configuration.EventSourcingConfigurer`
  - Add `org.axonframework.eventsourcing.configuration.EventSourcedEntityModule`
- `@BeforeEach`: `new AggregateTestFixture<>(Calendar.class)` → `AxonTestFixture.with(EventSourcingConfigurer.create().registerEntity(EventSourcedEntityModule.autodetected(<IdType>.class, <Entity>.class)))`.
- Add `@AfterEach fixture.stop()` — the AF5 fixture holds resources that must be released.
- Fluent DSL transforms:
  - `fixture.given(events…)` → `fixture.given().events(events…)`
  - `fixture.givenNoPriorActivity()` → `fixture.given().noPriorActivity()`
  - `.when(cmd)` → `.when().command(cmd)`
  - `.expectEvents(events…)` → `.then().events(events…)`
  - `.expectException(Cls.class)` → `.then().exception(Cls.class)`
- Inside `eventsSatisfy(events -> …)` lambdas (and similar event-inspecting closures): `events.get(0).payload()` / `.metaData()` instead of `getPayload()` / `getMetaData()`.

## AF5 exception flips — silent migration risk

**Always re-check these two cases** when migrating a test class:

| AF4 expectation | AF5 reality | Fix |
|---|---|---|
| `expectException(AggregateNotFoundException.class)` on an **instance** `@CommandHandler` | AF5 + no-arg `@EntityCreator` materialises an empty entity, instance handler runs against null state, any project domain rule fires instead. | Replace with the project's existing domain exception (e.g. `CanOnlyFinishCurrentDay.Violation`). DO NOT invent a new exception type. |
| Test that should succeed but now throws `EntityAlreadyExistsForCreationalCommandHandlerException` | A previously-`@CreationPolicy(ALWAYS)` handler was migrated to **static** `@CommandHandler` — AF5 framework rejects re-creation. | Re-check the static-vs-instance choice (see use case 03 decision table). For `CREATE_IF_MISSING` semantics, use instance + no-arg `@EntityCreator`, not static. |

## Caveats

- **Do NOT silently weaken assertions.** A flipped expectation that matches AF5 reality counts as Success only when the underlying behaviour is preserved. Replacing `expectException(AggregateNotFoundException)` with `expectSuccessfulHandlerExecution()` is a regression mask.
- **The fixture's identifier type matters.** `EventSourcedEntityModule.autodetected(<IdType>.class, ...)` MUST match the `idType` declared on the entity's `@EventSourced` / `@EventSourcedEntity`. Mismatched types fail at fixture-construction time — usually quickly surfaced.
- **`@AfterEach fixture.stop()` is non-optional.** Forgetting it leaks the embedded event store between tests; subtle ordering-dependent failures appear later.
- **`SagaTestFixture` is unrelated.** If the test class also uses `SagaTestFixture`, the recipe emits Blocker B3 (no AF5 saga fixture replacement) — only happens if a saga test was incorrectly placed alongside an aggregate test.
