# AggregateTestFixture → AxonTestFixture

AF4 used `AggregateTestFixture<T>` for BDD-style aggregate testing. AF5 replaces it with `AxonTestFixture`
which wraps an `EventSourcingConfigurer` rather than a bare class reference.

## Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.test.aggregate.AggregateTestFixture` | `org.axonframework.test.fixture.AxonTestFixture` |
| — | `org.axonframework.eventsourcing.configuration.EventSourcingConfigurer` |
| — | `org.axonframework.eventsourcing.configuration.EventSourcedEntityModule` |

## Detection

```bash
grep -rn 'AggregateTestFixture' --include='*.java' --include='*.kt' --include='*.scala' .
```

## Axon Framework 4 Code

```java
import org.axonframework.test.aggregate.AggregateTestFixture;

class OrderTest {

    private AggregateTestFixture<Order> fixture;

    @BeforeEach
    void setUp() {
        fixture = new AggregateTestFixture<>(Order.class);
    }

    @Test
    void shouldShipOrder() {
        fixture.given(new OrderCreatedEvent("order-1"))
               .when(new ShipOrderCommand("order-1", "123 Main St"))
               .expectEvents(new OrderShippedEvent("order-1", "123 Main St"));
    }
}
```

## Axon Framework 5 Code

```java
import org.axonframework.test.fixture.AxonTestFixture;
import org.axonframework.eventsourcing.configuration.EventSourcingConfigurer;
import org.axonframework.eventsourcing.configuration.EventSourcedEntityModule;

class OrderTest {

    private AxonTestFixture fixture;

    @BeforeEach
    void setUp() {
        fixture = AxonTestFixture.with(
            EventSourcingConfigurer.create()
                .registerEntity(EventSourcedEntityModule.autodetected(OrderId.class, Order.class))
        );
    }

    @AfterEach
    void tearDown() {
        fixture.stop();  // required — prevents resource leaks
    }

    @Test
    void shouldShipOrder() {
        fixture.given().events(new OrderCreatedEvent("order-1"))
               .when().command(new ShipOrderCommand("order-1", "123 Main St"))
               .then().events(new OrderShippedEvent("order-1", "123 Main St"));
    }
}
```

## Fluent DSL changes

| AF4 | AF5 |
|-----|-----|
| `fixture.given(events…)` | `fixture.given().events(events…)` |
| `fixture.givenNoPriorActivity()` | `fixture.given().noPriorActivity()` |
| `.when(cmd)` | `.when().command(cmd)` |
| `.expectEvents(events…)` | `.then().events(events…)` |
| `.expectException(Cls.class)` | `.then().exception(Cls.class)` |
| `.expectNoEvents()` | `.then().noEvents()` |

## Exception behavior change

With AF5's `@EntityCreator` no-arg constructor, the framework materializes an **empty entity** before replaying.
AF4 threw `AggregateNotFoundException` for missing aggregates; AF5 does not — tests that asserted
`AggregateNotFoundException` must be updated to expect the **project's domain exception** thrown from
validation on empty state.

```java
// AF4
.expectException(AggregateNotFoundException.class)

// AF5 — replace with the domain exception thrown by your domain rules
.then().exception(OrderNotFoundException.class)
```

## Partial migration state (post-OpenRewrite)

OR renames the type to `AxonTestFixture` and rewrites the fluent DSL, but the **Java**-only `AddAxonTestFixtureTearDown` recipe is conservative: it skips Kotlin sources and any class that already has an `@AfterEach`. The `MigrateAggregateTestFixtureSetup` recipe also may leave a raw `new AxonTestFixture(...)` constructor when it could not infer the id type. Common half-state:

```java
private AxonTestFixture fixture;   // type already renamed

@BeforeEach
void setUp() {
    fixture = new AxonTestFixture<>(Order.class);   // still AF4-shape constructor
}
// no @AfterEach tearDown() — fixture.stop() missing
```

Minimal fix: replace the constructor with the `EventSourcingConfigurer.create().registerEntity(EventSourcedEntityModule.autodetected(OrderId.class, Order.class))` builder shown in the AF5 example, drop the `<…>` type argument, and add the `@AfterEach tearDown() { fixture.stop(); }` if absent. Do NOT rename `AxonTestFixture` back to `AggregateTestFixture`. Audit:

```bash
grep -rn 'new AxonTestFixture\|AxonTestFixture<' --include='*.java' --include='*.kt' --include='*.scala' .
grep -rLn 'fixture\.stop()' --include='*.java' --include='*.kt' --include='*.scala' \
  $(grep -rln 'AxonTestFixture' --include='*.java' --include='*.kt' --include='*.scala' .)
```

## Notes

- **`fixture.stop()` in `@AfterEach` is required** — omitting it causes resource leaks across test runs.
- **`AxonTestFixture` is not generic** — no type parameter, unlike `AggregateTestFixture<T>`.
- **Child entities**: if the aggregate uses `@EntityMember` child entities, register each type in the configurer's
  `registerEntity(…)` calls.
- **`SagaTestFixture` removed** — no AF5 replacement; tests using it cannot be automatically migrated (blocker).
- **OpenRewrite status:** Partial — OR (in `axon4-to-axon5-test.yml`) renames the type via `ChangeType`, rewrites the fluent DSL (`MigrateAxonTestFixtureFluentApi`), regenerates setup (`MigrateAggregateTestFixtureSetup`), and adds a Java `@AfterEach tearDown()` (`AddAxonTestFixtureTearDown`); AI completes Kotlin tear-down, fills setup the recipe could not infer (`new AxonTestFixture(...)` left over), and replaces `AggregateNotFoundException` with the domain exception.
