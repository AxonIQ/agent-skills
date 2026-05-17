---
atom-id: test-fixture
title: "AggregateTestFixture → AxonTestFixture (BDD test DSL migration)"
af4-symbols: ["AggregateTestFixture", "org.axonframework.test.aggregate.AggregateTestFixture"]
af5-symbols: ["AxonTestFixture", "org.axonframework.test.fixture.AxonTestFixture"]
detect: grep -rn 'AggregateTestFixture' --include='*.java' .
used-by: [aggregate]
---

# AggregateTestFixture → AxonTestFixture

AF4 used `AggregateTestFixture<T>` for BDD-style aggregate testing. AF5 replaces it with `AxonTestFixture` which
wraps an `EventSourcingConfigurer` rather than a class reference.

## Detect

```bash
grep -rn 'AggregateTestFixture' --include='*.java' .
```

## Transforms

### 1. Field declaration

**Remove:**
```java
import org.axonframework.test.aggregate.AggregateTestFixture;

private AggregateTestFixture<Order> fixture;
```

**Add:**
```java
import org.axonframework.test.fixture.AxonTestFixture;

private AxonTestFixture fixture;
```

### 2. Setup — @BeforeEach

**Remove:**
```java
@BeforeEach
void setUp() {
    fixture = new AggregateTestFixture<>(Order.class);
}
```

**Add:**
```java
import org.axonframework.eventsourcing.EventSourcingConfigurer;
import org.axonframework.eventsourcing.modules.EventSourcedEntityModule;

@BeforeEach
void setUp() {
    fixture = AxonTestFixture.with(
        EventSourcingConfigurer.create()
            .registerEntity(EventSourcedEntityModule.autodetected(OrderId.class, Order.class))
    );
}
```

`<IdType>` = class of the AF4 `@AggregateIdentifier` field (matches `idType` on `@EventSourced`/`@EventSourcedEntity`).

### 3. Add @AfterEach tearDown

```java
@AfterEach
void tearDown() {
    fixture.stop();
}
```

### 4. Fluent given/when/then DSL

| AF4 | AF5 |
|---|---|
| `fixture.given(events…)` | `fixture.given().events(events…)` |
| `fixture.givenNoPriorActivity()` | `fixture.given().noPriorActivity()` |
| `.when(cmd)` | `.when().command(cmd)` |
| `.expectEvents(events…)` | `.then().events(events…)` |
| `.expectException(Cls.class)` | `.then().exception(Cls.class)` |
| `fixture.given(events…).when(cmd).expectEvents(…)` | `fixture.given().events(events…).when().command(cmd).then().events(…)` |

### 5. Accessor renames inside lambdas

Inside `eventsSatisfy(events -> …)` or similar lambdas, apply [[message-accessors]]:

```java
// AF4
.eventsSatisfy(events -> {
    assertEquals("order-1", events.get(0).getPayload().getOrderId());
})

// AF5
.eventsSatisfy(events -> {
    assertEquals("order-1", ((OrderCreatedEvent) events.get(0).payload()).getOrderId());
})
```

## AF5 Exception Behaviour Flip

With AF5's `@EntityCreator` no-arg constructor, the framework materialises an **empty entity** and runs an instance
handler even when no entity exists. AF4 threw `AggregateNotFoundException` for missing aggregates in this case.

Tests that assert `AggregateNotFoundException` must be updated to expect the **project's domain exception** (the
one that fires from domain rules against empty state). Do NOT invent a new exception — find the existing one.

```java
// AF4
.expectException(AggregateNotFoundException.class)

// AF5 — replace with the domain exception your project throws on empty state
.then().exception(OrderAlreadyCompletedException.class) // example
```

## Gotchas

- **`fixture.stop()` in `@AfterEach` is required** — leaving it out causes resource leaks across test runs.
- **`AxonTestFixture` is not generic** — no type parameter, unlike `AggregateTestFixture<T>`.
- **`EventSourcingConfigurer.create()` with all entity types in the test slice** — if the aggregate under test
  uses `@EntityMember` child entities, register each child entity type in the configurer's `registerEntity(…)` calls.
- **`AggregateNotFoundException` no longer thrown** — do not add a dependency on it; it is gone in AF5. The domain
  rule exception is the correct signal.
- **`SagaTestFixture` — no AF5 replacement** — tests using `SagaTestFixture` cannot be migrated with this atom
  (Blocker B3 in the aggregate recipe). Leave them on AF4 deps or remove the test.

## Used By

- **[[aggregate]]** — Step T (when test class exists AND B3 not fired)
