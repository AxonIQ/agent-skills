# Recipe: aggregate → `@EventSourced` / `@EventSourcedEntity`

Atomic migration of ONE aggregate class + its commands, events, child entities, and primary test class.

## Inputs

```yaml
target: <FQ aggregate class>                                # required
target_test: <FQ test class>                                # optional; defaults to <target>Test
wiring: spring-boot | framework-config                       # pinned project decision
decisions: { ... }                                           # populated across re-resolutions; see ## Decision points
```

## Preflight

1. **Read [blockers.md](blockers.md)** for the four blocker entries this recipe surfaces (B1, B4, B2, B3). For each entry in `## Decision points` below with `trigger: detected-at-preflight`, run its Detection grep against the target + its package.
2. For any trigger that fires AND whose key is **not** already in `inputs.decisions` → **🔒 await decision** for that key.
3. Idempotency check: `mcp__ide__getDiagnostics` on the target, OR `axon4to5-isolatedtest` with `test-sources: []`. If compile is clean AND `target_test` exists, run scoped tests too.
4. If green AND no blocker fired → **🔒 await decision** [`skip-or-deep-verify`](#skip-or-deep-verify).
5. Otherwise → continue to Procedure.

## AF5 imports — exact FQNs (copy-paste, do NOT shorten)

These FQNs are **non-obvious** — every AF5 package has a `.annotation` / `.annotation.reflection` / `.messaging.` infix that a guess almost certainly misses. Use these literal lines; do not paraphrase.

```java
// Used by every aggregate, both paths:
import org.axonframework.eventsourcing.annotation.EventSourcingHandler;
import org.axonframework.eventsourcing.annotation.reflection.EntityCreator;        // ⚠ note .reflection. — NOT eventsourcing.annotation.EntityCreator
import org.axonframework.messaging.commandhandling.annotation.CommandHandler;       // ⚠ note .messaging. — NOT commandhandling.annotation.CommandHandler
import org.axonframework.messaging.eventhandling.gateway.EventAppender;             // ⚠ note .messaging. — NOT eventhandling.gateway.EventAppender

// Path A (Spring Boot) stereotype:
import org.axonframework.extension.spring.stereotype.EventSourced;                  // NOT spring.stereotype.EventSourced — package is .extension.spring.

// Path B (framework Configurer) stereotype:
import org.axonframework.eventsourcing.annotation.EventSourcedEntity;

// On every event class:
import org.axonframework.eventsourcing.annotation.EventTag;
import org.axonframework.messaging.eventhandling.annotation.Event;                  // ⚠ note .messaging.

// On every command class:
import org.axonframework.modelling.annotation.TargetEntityId;
import org.axonframework.messaging.commandhandling.annotation.Command;              // ⚠ note .messaging.

// Multi-entity (Step M):
import org.axonframework.modelling.entity.annotation.EntityMember;
```

The 4 ⚠-flagged paths are routinely missed by agents working from "general AF5 knowledge". **Match the strings literally.**

## Decision points

### snapshotting

- **Trigger**: detected-at-preflight
- **Detection**:
    ```
    grep -RnE 'snapshotTriggerDefinition|Snapshotter|SnapshotTriggerDefinition' <aggregate file> <aggregate package>
    ```
    Also inspect the `@Aggregate` annotation directly for `snapshotTriggerDefinition = "..."`. After OpenRewrite has run, also check for the `// TODO #LLM: reconfigure snapshot trigger …` marker the bulk recipe leaves behind.
- **Question**: > "Aggregate `<name>` declares `snapshotTriggerDefinition`. AF5 has no portable equivalent yet. How do you want to handle it?"
- **Options**:
    - `accept-drop` — drop the attribute from `@EventSourced` / `@EventSourcedEntity`; no snapshotting until AF5 ships the API.
    - `pause-migration` — stop; user removes/relocates the snapshot config first.
    - `remove-feature-first` — user deletes snapshot config now; re-introduces later.
- **Auto-policy**:
    - `fallback: ask-user` (snapshotting is too project-specific to default)
- **Effect on Procedure**:
    - `accept-drop` → continue; do NOT carry `snapshotTriggerDefinition` to the AF5 annotation in Step A.1 / B.1.
    - `pause-migration` / `remove-feature-first` → `output { result: blocked, reason: "snapshotting deferred", notes: "see blockers.md#B1" }`, exit.
- **Reference**: [blockers.md#B1](blockers.md#B1).

### deadline-handler

- **Trigger**: detected-at-preflight
- **Detection**:
    ```
    grep -RnE '@DeadlineHandler|DeadlineManager|DeadlineMessage|deadlineManager\.schedule|cancelSchedule|cancelAllWithinScope' <aggregate file> <aggregate package>
    ```
    Also inspect constructor params for `DeadlineManager`.
- **Question**: > "Aggregate uses `@DeadlineHandler` / `DeadlineManager`. AF5 has no direct successor. How do you want to handle it?"
- **Options**:
    - `accept-stays-af4` — deadline code stays AF4; the slice won't compile under AF5 deps until AF5 ships a replacement or the user redesigns. Surface in `Output.notes`.
    - `pause-migration` *(Recommended)* — stop; user removes/replaces the deadline flow first.
    - `remove-feature-first` — user redesigns now; recipe exits.
- **Auto-policy**:
    - `fallback: ask-user`
- **Effect on Procedure**:
    - `accept-stays-af4` → proceed with Steps 3–14 + Path A/B; do NOT touch `@DeadlineHandler` methods or `DeadlineManager` injection sites; surface in `Output.notes`.
    - `pause-migration` / `remove-feature-first` → `output { result: blocked }`, exit.
- **Reference**: [blockers.md#B4](blockers.md#B4).

### map-typed-aggregate-member

- **Trigger**: triggered-in-procedure (Step M only, when `@AggregateMember` is `Map<K, V>`-typed)
- **Detection**:
    ```
    grep -nE '@AggregateMember[\s\S]{0,200}Map<' <aggregate file>
    ```
- **Question**: > "Aggregate has a `Map<K, V>`-typed `@AggregateMember`. AF5 `@EntityMember` does not support the same shape. How do you want to handle it?"
- **Options**:
    - `surface-and-defer` *(Recommended)* — emit `output { result: blocked }` noting the Map-typed member; user redesigns to `List` / `Set` first.
    - `pause-migration` — stop; user redesigns now.
- **Auto-policy**:
    - `fallback: ask-user`
- **Effect on Procedure**:
    - either choice → `output { result: blocked }`, exit. No edits.
- **Reference**: [blockers.md#B2](blockers.md#B2).

### saga-test-fixture

- **Trigger**: detected-at-preflight (only when `target_test` exists)
- **Detection**:
    ```
    grep -RnE 'SagaTestFixture' <test class>
    ```
- **Question**: > "Aggregate's test class uses `SagaTestFixture`. AF5 has no replacement. How do you want to handle it?"
- **Options**:
    - `surface-and-skip-test` *(Recommended)* — leave the saga test on AF4 deps; skip the Test fixture migration block.
    - `pause-migration` — stop.
- **Auto-policy**:
    - `fallback: ask-user`
- **Effect on Procedure**:
    - `surface-and-skip-test` → run Steps 3–14 + Path A/B; SKIP Test fixture migration (T.1–T.5).
    - `pause-migration` → `output { result: blocked }`, exit.
- **Reference**: [blockers.md#B3](blockers.md#B3).

### skip-or-deep-verify

- **Trigger**: triggered-in-procedure (only when Preflight step 3 finds compile + tests green AND no blocker fired)
- **Detection**: n/a (decision arises from successful Preflight, not a grep)
- **Question**: > "Target appears already migrated (clean compile + green tests). Skip or deep-verify against AF4 baseline?"
- **Options**:
    - `skip` *(Recommended)* — treat as already migrated; `output { result: skipped }`.
    - `deep-verify` — `git log` / `git show` to confirm nothing was silently lost (dropped `snapshotTriggerDefinition`, missing `@EventTag`, lost `@CreationPolicy` semantics).
- **Auto-policy**:
    - `pinned.resolver_mode == "automatic": skip`
    - `fallback: ask-user`
- **Effect on Procedure**:
    - `skip` → `output { result: skipped, reason: "target already on AF5 — preflight idempotent" }`, exit.
    - `deep-verify` → continue to Procedure.

## Procedure

### Step 1 — Identify

- target = given FQ class, else first `@Aggregate`/`@AggregateRoot` class with `@EventSourcingHandler` methods.
- commands = first param of every `@CommandHandler` on the aggregate (incl. constructor).
- events = first param of every `@EventSourcingHandler`.
- tests = `<target>Test` + direct subclasses (`grep -rln "extends <target>Test"`). Migrate base first.

### Step 2 — Detect variant

- **simple** — no `@AggregateMember`, no concrete `@Aggregate` subclasses.
- **multi-entity** — has any `@AggregateMember` field. Apply Step M.
- **polymorphic** — abstract/concrete superclass with `@Aggregate`-annotated subclasses inheriting handlers. Apply Step P on base + each subtype.

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
11. Annotate the aggregate's no-arg constructor with `@EntityCreator` (mandatory in AF5). If absent, add one. Likely already done by OpenRewrite — grep before adding (duplicate constructors compile but signal partial rewrite).
    Required import (the `.reflection.` infix is mandatory):
    ```java
    import org.axonframework.eventsourcing.annotation.reflection.EntityCreator;
    ```
12. Replace `AggregateLifecycle.apply(event)` → `eventAppender.append(event)`. Add `EventAppender eventAppender` as method parameter to every `@CommandHandler`. Remove the static import of `AggregateLifecycle.apply`.
    Required import (the `.messaging.` infix is mandatory):
    ```java
    import org.axonframework.messaging.eventhandling.gateway.EventAppender;
    ```
13. Verify `@CreationPolicy` mapping. OpenRewrite removes the annotation; behavior preserved when paired with Step 11's no-arg `@EntityCreator`. Wrong handler shape compiles but fails at test time. Rules:
    - `ALWAYS` → **`static`** `@CommandHandler`. OpenRewrite usually does NOT flip to static — verify.
    - `CREATE_IF_MISSING` → **instance** `@CommandHandler` + no-arg `@EntityCreator` (default post-OpenRewrite). Do NOT switch to static unless AF4 already threw on existing entities.
    - `NEVER` (or absent) → instance `@CommandHandler` (default).
14. Apply variant addenda from Step 2 if they fired (Step M / Step P below).

### Step M — Multi-entity (`@AggregateMember` → `@EntityMember`)

- Replace import `org.axonframework.modelling.command.AggregateMember` → `org.axonframework.modelling.entity.annotation.EntityMember`.
- Replace `@AggregateMember` → `@EntityMember`.
- **Map-typed members**: 🔒 await decision [`map-typed-aggregate-member`](#map-typed-aggregate-member). On any answer → `output { result: blocked }`, exit (no edits to Map-typed members).
- Field-type members and Collection-of-entity members migrate 1:1.
- Each child entity also needs `@EventSourcedEntity(tagKey = …)` and `@EntityCreator` per Step 11 + Path A/B below.

### Step P — Polymorphic (`concreteTypes`)

- Keep base class abstract; remove `@Aggregate`/`@AggregateRoot` from base (handlers stay inherited).
- Add `@EventSourcedEntity(concreteTypes = { Sub1.class, Sub2.class, … })` OR `@EventSourced(concreteTypes = …)` on the base.
- Concrete subtypes do **NOT** carry `@EventSourcedEntity` themselves — discovered through base.
- All inherited `@EventSourcingHandler` methods stay on base. Subtype-specific handlers stay on subtypes.

### Path A — Spring Boot (`wiring == spring-boot`)

A.1. `@Aggregate` (`org.axonframework.spring.stereotype.Aggregate`) → `@EventSourced` (`org.axonframework.extension.spring.stereotype.EventSourced`). If `decisions.snapshotting == "accept-drop"` (always — other values exited at Preflight), do NOT carry the `snapshotTriggerDefinition` attribute over.

A.2. Configure `@EventSourced`:
- `tagKey` — equals `@EventTag(key = ...)` on events; default = entity simple class name (omit if matching).
- `idType` — set when AF4 `@AggregateIdentifier` field is NOT `String`. Default `String.class`. Mismatched type → silent identifier failure.
- `concreteTypes` — only for polymorphism (Step P).

### Path B — framework Configurer (`wiring == framework-config`)

B.1. `@Aggregate`/`@AggregateRoot` (AF4) → `@EventSourcedEntity` (`org.axonframework.eventsourcing.annotation.EventSourcedEntity`). Remove the AF4 import. Same `snapshotTriggerDefinition` drop as Path A.

B.2. Configure attributes — same `tagKey` / `idType` / `concreteTypes` semantics as Path A.

B.3. Register the entity in the project's `Configurer` setup. Typical file names: `*Configuration.java`, `*Application.java`, `*Bootstrap.java`, or per-slice `<Slice>Configuration.java`.

```java
EventSourcingConfigurer.create()
    .registerEntity(EventSourcedEntityModule.autodetected(IdType.class, Entity.class))
    .registerCommandHandlingModule(...)
    .start();
```

The `IdType` must match the `idType` on `@EventSourcedEntity`. For per-slice projects, add inside the slice's `static EventSourcingConfigurer configure(EventSourcingConfigurer)` method.

B.4. If the project's command handler lives in a separate class and isn't registered, add via `CommandHandlingModule.autodetectedCommandHandlingComponent(...)`. If you cannot locate the configurer file, emit `output { result: blocked, reason: "configurer file not found; please register entity manually" }` — annotation rewrites from Steps 3–14 + B.1–B.2 still get committed (record them in `files_touched`).

## Test fixture migration

Skip if `target_test` doesn't exist OR `decisions.saga-test-fixture == "surface-and-skip-test"`.

T.1. Migrate base test first, then subclasses.

T.2. Replace `AggregateTestFixture` with `AxonTestFixture`:
- import: `org.axonframework.test.aggregate.AggregateTestFixture` → `org.axonframework.test.fixture.AxonTestFixture`.
- field type: `AggregateTestFixture<?>` → `AxonTestFixture`.
- `@BeforeEach`: `new AggregateTestFixture<>(<target>.class)` → `AxonTestFixture.with(<configurer>)` where configurer is:
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

1. Test class (if any not skipped) passes via `axon4to5-isolatedtest`:
    ```yaml
    target-name: <AggregateSimpleName>
    build-file: <module>/pom.xml | build.gradle(.kts)
    main-sources: [<aggregate + commands + events + child entities>]
    test-sources: [<test class + subclass tests>]
    extra-deps: [axon-modelling, axon-eventsourcing, axon-test]    # +axon-spring for Path A
    cleanup: false                                                  # true on final green run
    ```
2. Zero compile errors across the in-scope files.

If no test class OR test fixture migration was skipped → condition is just (2).

## Output

```yaml
result: success | skipped | rejected | blocked | failed
target: <FQ aggregate>
reason: <one short line>                      # required for everything except success
decisions:
  path: A (Spring Boot) | B (framework Configurer)
  variant: simple | multi-entity | polymorphic
  creation-policy: NEVER | ALWAYS-handled | ALWAYS-static-factory
  test-fixture: migrated | none | skipped
  snapshotting: accept-drop | pause-migration | remove-feature-first     # always present after Preflight
  deadline-handler: none | accept-stays-af4 | pause-migration | remove-feature-first
  map-typed-aggregate-member: none | surface-and-defer | pause-migration
  saga-test-fixture: none | surface-and-skip-test | pause-migration
files_touched:
  - <repo-relative path>
  - ...
notes: <free text — cite blockers.md#B<n> when blocked>
```

## Subagent guidelines

Aggregates are independent — different files, different tests, different scope entries. Subagent fan-out is **read-only analysis** per aggregate; apply / verify / commit stay serial (shared build file).

```yaml
subagent_type: general-purpose
isolation: none
parallelism: per-item
on_unexpected_condition: keep-edits-and-fail
prompt-framing: |
  READ-ONLY analysis of ONE aggregate. Do NOT edit / commit / run mvn.
  Return: variant, blocker triggers (with file:line), CreationPolicy per handler,
  project-specific empty-state exception (matching the project's style),
  test-method assertions to replace AggregateNotFoundException,
  full main-sources / test-sources for axon4to5-isolatedtest.
```

**Eligibility**: fan-out is allowed only AFTER every entry in `## Decision points` is resolved in the main session (because all four entries have `fallback: ask-user`). The orchestrator runs Preflight in the main session, resolves the four decisions interactively (or via pinned state), then spawns subagents for the mechanical rewrite portion.

## Reference pairs (AF4 → AF5)

Bundled in [evals/fixtures/](../evals/fixtures/):

- **Simple aggregate, Spring Boot, JPA backend, snapshot blocker B1:** `axon4/heroes/Dwelling.java` ↔ `axon5/heroes/Dwelling.java`. Four more aggregates in the same project follow the same shape: `Calendar.java`, `Astrologers.java`, `ResourcesPool.java`, `Army.java`.
- **Simple aggregate, Spring Boot, Axon Server backend:** `axon4/gamerental/Game.java` ↔ `axon5/gamerental/Game.java`.

> Multi-entity (`@AggregateMember` → `@EntityMember`) and polymorphic (`concreteTypes`) variants have **no concrete reference pair** in the bundled examples. Follow the Step M / Step P mechanical edits without a worked-example sanity-check.

## Caveats

- After OpenRewrite some IDE LSPs report phantom `cannot resolve` errors for package-private types referenced from sub-package tests. javac + build tool are truth — if the scoped run is green, the migration is fine. Don't chase phantom LSP errors with extra `public` modifiers.
