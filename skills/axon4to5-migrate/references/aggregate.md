# Recipe: aggregate → `@EventSourced` / `@EventSourcedEntity`

Atomic migration of ONE aggregate class + its commands, events, child entities, and primary test class.

## Inputs

- `target` — FQ aggregate class (required)
- `target_test` — FQ test class (optional; auto = `<target>Test`)
- `wiring` — `spring-boot` | `framework-config` (from pinned decisions)

## Preflight

1. Read [not-supported.md](blockers.md) — run every Detection grep. If a blocker fires, follow its `AskUserQuestion` flow. Do not proceed past Preflight while unresolved.
2. Check compile via `mcp__ide__getDiagnostics` OR `axon4to5-isolatedtest` with `test-sources: []`.
3. If clean AND test class exists → run scoped tests.
4. If green → `AskUserQuestion`: **Skip** *(Recommended)* / **Deep verify** (diff vs AF4 baseline). Proceed only on Deep verify or failure.

## Procedure

### Step 1 — Identify

- target = given FQ class, else first `@Aggregate`/`@AggregateRoot` class with `@EventSourcingHandler` methods.
- commands = first param of every `@CommandHandler` on the aggregate (incl. constructor).
- events = first param of every `@EventSourcingHandler`.
- tests = `<Aggregate>Test` + direct subclasses (`grep -rln "extends <Aggregate>Test"`). Migrate base first.

### Step 2 — Detect variant

- **simple** — no `@AggregateMember`, no concrete `@Aggregate` subclasses.
- **multi-entity** — has any `@AggregateMember` field. Apply step M.
- **polymorphic** — abstract/concrete superclass with `@Aggregate`-annotated subclasses inheriting handlers. Apply step P on base + each subtype.

Variants combine; apply both addenda if both fire.

### Steps 3–14 — Class-level rewrite

3. Each command class: remove `import org.axonframework.modelling.command.TargetAggregateIdentifier`; add `import org.axonframework.modelling.annotation.TargetEntityId`; replace `@TargetAggregateIdentifier` → `@TargetEntityId`.
4. Annotate each command class with `@Command` (`org.axonframework.messaging.commandhandling.annotation.Command`). If `@RoutingKey` on a property → `@Command(routingKey = "<propertyName>")` and remove the `@RoutingKey` annotation + import.
5. Find the `@AggregateIdentifier` field in the aggregate and the `@EventSourcingHandler` that sets it from an event property. That event property is what gets `@EventTag`.
6. Annotate the aggregate-id field in **every** event with `@EventTag(key = "<EntityName>")` — use the entity's simple class name. Without DCB, exactly ONE `@EventTag` per event. Prefer entity type (`"Bike"`) over field name (`"bikeId"`).
7. Annotate each event class with `@Event` (`org.axonframework.messaging.eventhandling.annotation.Event`). `@Revision("x")` → `@Event(version = "x")`; remove `@Revision` annotation + import. Default name = simple class name; default version = `0.0.1`.
8. Remove `@AggregateIdentifier` annotation + import from aggregate. Id field stays as a regular field.
9. Replace import `org.axonframework.eventsourcing.EventSourcingHandler` → `org.axonframework.eventsourcing.annotation.EventSourcingHandler`.
10. Replace import `org.axonframework.commandhandling.CommandHandler` → `org.axonframework.messaging.commandhandling.annotation.CommandHandler`.
11. Annotate aggregate's no-arg constructor with `@EntityCreator` (mandatory in AF5). If absent, add one. Likely already done by OpenRewrite — grep before adding (duplicate constructors compile but signal partial rewrite).
12. Replace `AggregateLifecycle.apply(event)` → `eventAppender.append(event)`. Add `EventAppender eventAppender` as method parameter to every `@CommandHandler`. Remove the static import of `AggregateLifecycle.apply`.
13. Verify `@CreationPolicy` mapping. OpenRewrite removes the annotation; behavior preserved when paired with Step 11's no-arg `@EntityCreator`. Wrong handler shape compiles but fails at test time. Rules:
    - `ALWAYS` → **`static`** `@CommandHandler`. OpenRewrite usually does NOT flip to static — verify.
    - `CREATE_IF_MISSING` → **instance** `@CommandHandler` + no-arg `@EntityCreator` (default post-OpenRewrite). Do NOT switch to static unless AF4 already threw on existing entities.
    - `NEVER` (or absent) → instance `@CommandHandler` (default).
14. Apply variant addenda from Step 2 if they fired (steps M / P below).

### Step M — Multi-entity (`@AggregateMember` → `@EntityMember`)

- Replace import `org.axonframework.modelling.command.AggregateMember` → `org.axonframework.modelling.entity.annotation.EntityMember`.
- Replace `@AggregateMember` → `@EntityMember`.
- **Map-typed `@AggregateMember` is a breaking change.** Surface via `AskUserQuestion` per [not-supported.md](blockers.md) B3 BEFORE rewriting.
- Field-type members and Collection-of-entity members migrate 1:1.
- Each child entity also needs `@EventSourcedEntity(tagKey = …)` and `@EntityCreator` per Steps 11 + Path A/B below.

### Step P — Polymorphic (`concreteTypes`)

- Keep base class abstract; remove `@Aggregate`/`@AggregateRoot` from base (handlers stay inherited).
- Add `@EventSourcedEntity(concreteTypes = { Sub1.class, Sub2.class, … })` OR `@EventSourced(concreteTypes = …)` on the base.
- Concrete subtypes do **NOT** carry `@EventSourcedEntity` themselves — discovered through base.
- All inherited `@EventSourcingHandler` methods stay on base. Subtype-specific handlers stay on subtypes.

### Path A — Spring Boot (`wiring == spring-boot`)

A.1. `@Aggregate` (`org.axonframework.spring.stereotype.Aggregate`) → `@EventSourced` (`org.axonframework.extension.spring.stereotype.EventSourced`).
A.2. Configure `@EventSourced`:
- `tagKey` — equals `@EventTag(key = ...)` on events; default = entity simple class name (omit if matching).
- `idType` — set when AF4 `@AggregateIdentifier` field is NOT `String`. Default `String.class`. Mismatched type → silent identifier failure.
- `concreteTypes` — only for polymorphism (step P).

⚠️ `snapshotTriggerDefinition` / caching attributes NOT portable. Preflight resolved the snapshotting decision ([not-supported.md](blockers.md) B1) — if `accept-drop`, omit the attribute.

### Path B — framework Configurer (`wiring == framework-config`)

B.1. `@Aggregate`/`@AggregateRoot` (AF4) → `@EventSourcedEntity` (`org.axonframework.eventsourcing.annotation.EventSourcedEntity`). Remove the AF4 import.
B.2. Configure attributes — same `tagKey` / `idType` / `concreteTypes` semantics as Path A.
B.3. Register entity in the project's `Configurer` setup. Typical file names: `*Configuration.java`, `*Application.java`, `*Bootstrap.java`, or per-slice `<Slice>Configuration.java`.

```java
EventSourcingConfigurer.create()
    .registerEntity(EventSourcedEntityModule.autodetected(IdType.class, Entity.class))
    .registerCommandHandlingModule(...)
    .start();
```

The `IdType` must match the `idType` on `@EventSourcedEntity`. For per-slice projects, add inside the slice's `static EventSourcingConfigurer configure(EventSourcingConfigurer)` method.

B.4. If the project's command handler lives in a separate class and isn't registered, add via `CommandHandlingModule.autodetectedCommandHandlingComponent(...)`. If you cannot locate the configurer file, emit `result: needs-decision` — annotation rewrites from Steps 3–14 + B.1–B.2 still get committed.

## Test fixture migration

Skip if no test class.

T.1. Migrate base test first, then subclasses.
T.2. Replace `AggregateTestFixture` with `AxonTestFixture`:
- import: `org.axonframework.test.aggregate.AggregateTestFixture` → `org.axonframework.test.fixture.AxonTestFixture`.
- field type: `AggregateTestFixture<?>` → `AxonTestFixture`.
- `@BeforeEach`: `new AggregateTestFixture<>(<Aggregate>.class)` → `AxonTestFixture.with(<configurer>)` where configurer is:
  ```java
  EventSourcingConfigurer.create()
                         .registerEntity(EventSourcedEntityModule.autodetected(IdType.class, Aggregate.class))
  ```
- Add `@AfterEach tearDown() { fixture.stop(); }`.

T.3. Convert each test to fluent given/when/then:
- `fixture.given(events…)` → `fixture.given().events(events…)`
- `fixture.givenNoPriorActivity()` → `fixture.given().noPriorActivity()`
- `.when(cmd)` → `.when().command(cmd)`
- `.expectEvents(events…)` → `.then().events(events…)`
- `.expectException(Cls.class)` → `.then().exception(Cls.class)`
- Inside `eventsSatisfy(events -> …)` lambdas: `events.get(0).payload()` / `.metaData()` (AF5 record-style — NOT `getPayload()` / `getMetaData()`).

T.4. Adjust assertions for AF5 semantics:
- `AggregateNotFoundException` is **NOT** thrown for instance handlers in AF5. With no-arg `@EntityCreator` the framework materializes empty entity, so handler runs and any domain rule against empty state surfaces instead. Replace with the project's existing exception/rule that fires on empty state (do NOT invent a new exception type).
- Static (creational) handlers throw `EntityAlreadyExistsForCreationalCommandHandlerException` when entity already exists. Seeing this in a test that should succeed → re-check Step 13 (static vs instance).

T.5. Run migrated tests. Failures → re-check Step 13 (handler shape) and T.4 (exception expectations).

## End condition

1. Test class (if any) passes via `axon4to5-isolatedtest`:
```
target-name: <AggregateSimpleName>
build-file: <module>/pom.xml | build.gradle(.kts)
main-sources: [<aggregate + commands + events + child entities>]
test-sources: [<test class + subclass tests>]
extra-deps: [axon-modelling, axon-eventsourcing, axon-test]    # +axon-spring for Path A
cleanup: false                                                  # true on final green run
```
2. Zero compile errors across the in-scope files.

If no test class → condition is just (2).

## Output

```yaml
result: success | skipped | rejected | needs-decision | blocked | failed
target: <FQ aggregate>
reason: <one short line — required for everything except success>
decisions:
  path: A (Spring Boot) | B (framework Configurer)
  variant: simple | multi-entity | polymorphic
  creation-policy: NEVER | ALWAYS-handled | ALWAYS-static-factory
  test-fixture: migrated | none
  snapshotting: none | accept-drop | pause-migration | remove-feature-first     # B1
  map-typed-aggregate-member: none | surface-and-defer | pause-migration         # B3
  saga-test-fixture-flagged: none | surface-and-skip-test | pause-migration      # B4
  deadline-handler: none | accept-stays-af4 | pause-migration | remove-feature-first   # B5
notes: <verbatim AskUserQuestion options for needs-decision>
```

## Subagent guidelines

Aggregates are independent — different files, different tests, different scope entries. Fan out **read-only** analysis per aggregate; apply / verify / commit stay serial (shared build file).

```yaml
subagent_type: general-purpose
isolation: none
parallelism: per-item
prompt-framing: |
  READ-ONLY analysis of ONE aggregate. Do NOT edit / commit / run mvn.
  Return: variant, blockers (with file:line), CreationPolicy per handler,
  project-specific empty-state exception (matching project's style),
  test-method assertions to replace AggregateNotFoundException,
  full main-sources / test-sources for axon4to5-isolatedtest.
```

## Caveats

- After OpenRewrite some IDE LSPs report phantom `cannot resolve` errors for package-private types referenced from sub-package tests. javac + build tool are truth — if the scoped run is green, the migration is fine. Don't chase phantom LSP errors with extra `public` modifiers.

## Reference pairs (AF4 → AF5)

Bundled in [evals/fixtures/](../evals/fixtures/):

- **Simple aggregate, Spring Boot, JPA backend, snapshot blocker B1:** `axon4/heroes/Dwelling.java` ↔ `axon5/heroes/Dwelling.java`. Four more aggregates in the same project follow the same shape: `Calendar.java`, `Astrologers.java`, `ResourcesPool.java`, `Army.java`.
- **Simple aggregate, Spring Boot, Axon Server backend:** `axon4/gamerental/Game.java` ↔ `axon5/gamerental/Game.java`.

> Multi-entity (`@AggregateMember` → `@EntityMember`) and polymorphic (`concreteTypes`) variants have **no concrete reference pair** in the bundled examples. Follow the Step M / Step P mechanical edits in [## Procedure](#procedure) above without a worked-example sanity-check.
