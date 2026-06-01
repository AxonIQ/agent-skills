---
id: aggregate
title: Aggregate
description: Migrates a single Axon Framework 4 Aggregate (with commands, events, child entities, primary test class) into an Axon 5 EventSourcedEntity.
order: 1
argument-hint: $SOURCE
---

# Aggregate

> Single AF4 aggregate → AF5 event-sourced entity. Same architecture, no DCB. Preserves the project's wiring style: Spring Boot stays on `@EventSourced` (Path A); native Configurer stays on `@EventSourcedEntity` + module registration (Path B).

## Source

- `$SOURCE` (required) — FQN, file path, or simple class name of an AF4 aggregate. The aggregate is the class annotated `@Aggregate` / `@AggregateRoot` (or, after OpenRewrite, a class already partially on AF5 shape with `@EventSourcingHandler` methods).

## Scope

- `$SOURCE` aggregate class.
- Every command class referenced by `@CommandHandler` first-parameter types on `$SOURCE`.
- Every event class referenced by `@EventSourcingHandler` first-parameter types on `$SOURCE`.
- Every child entity reached via `@AggregateMember` (collection element type or field type).
- For polymorphic aggregates: the abstract base + every concrete subtype declared `@Aggregate` / `@AggregateRoot`.
- The primary test class — `<target>Test` if it exists; direct subclasses found by grepping the supertype name (`extends <target>Test` in Java, `: <target>Test` in Kotlin). Migrate the base test first.
- For `configuration=native`: the Configurer wiring file (typical names `*Configuration`, `*Application`, `*Bootstrap`, per-slice `<Slice>Configuration`; `.java` or `.kt`) — only the `registerEntity(...)` / `EventSourcedEntityModule` lines for `$SOURCE`. Do NOT touch other entities' registrations.

Scope grows during FLOW.md Research; it never shrinks. Sibling aggregates, projectors, sagas, application properties, logging are NEVER in scope.

## Applicable

Surface check on `$SOURCE` before Research. Cheap reads only — annotations, package, presence of method-level markers.

Decision rule (top-down; first match wins):

1. **Saga** — class annotated `@Saga` OR any method annotated `@SagaEventHandler` / `@StartSaga` / `@EndSaga`. → **Rejected** (route to saga recipe).
2. **Projector / event processor** — class annotated `@ProcessingGroup` AND zero `@CommandHandler` methods. → **Rejected** (route to event-processor recipe).
3. **State-stored aggregate** — annotated `@Aggregate` AND `@Entity` (JPA) AND zero `@EventSourcingHandler` methods AND command handlers mutate fields directly (no `apply(...)`). State-stored support is out of scope of this skill. → **Rejected** with NOTES naming `state-stored` as the reason.
4. **Event-sourced aggregate, AF4 shape** — class annotated `@Aggregate` / `@AggregateRoot` AND at least one `@EventSourcingHandler`. → **continue** to Research.
5. **Event-sourced aggregate, partially-migrated** — class already annotated `@EventSourced` / `@EventSourcedEntity` AND at least one `@EventSourcingHandler`. Recipe must tolerate this — partial migration is a valid input. → **continue** to Research; the Success Criteria pre-Apply check decides idempotent-Success vs. continue.
6. **None of the above** — no `@EventSourcingHandler`, no `@Aggregate`-family annotation. → **Rejected** with NOTES naming the failed predicate.

## Blocker

Constructs the recipe cannot migrate on its own. Each entry: what it is + how to detect + why this recipe halts.

**Emission model — all blockers at once.** The recipe scans for every blocker during Research (FLOW.md S3) BEFORE the Plan-Apply loop. If any blocker fires, the recipe emits **one** Blocker result enumerating every detected blocker with its own Options sub-block. The caller resolves each one manually (edits the source, removes the offending construct, redesigns the relationship) and re-invokes the skill. On re-invocation, the recipe re-scans; blockers that no longer match disappear, and the recipe proceeds when none remain. There is no "pre-pinned decision" argument — the caller's only signal is the source state at re-invocation time.

### B1 — `snapshotTriggerDefinition` on `@Aggregate`

`@Aggregate(snapshotTriggerDefinition = "...")`. AF5's `@EventSourced` / `@EventSourcedEntity` has no portable replacement attribute (see [configuration-migration.adoc](../../docs/paths/aggregates/configuration-migration.adoc) IMPORTANT note). Detect by grepping the `@Aggregate` annotation on `$SOURCE` for `snapshotTriggerDefinition`; also check for the post-OpenRewrite marker `// TODO #LLM: reconfigure snapshot trigger`.

**B1 always fires as a Blocker.** There is currently no verified auto-migration path for snapshot trigger configuration in either `configuration=spring` or `configuration=native`. The `EventSourcedEntityModule.declarative()` builder chain required to wire `SnapshotPolicy` is non-trivial (mandatory intermediate phases before `snapshotPolicy()` is reachable) and the correct pattern has not yet been validated end-to-end. Do NOT attempt auto-migration — always halt with Blocker B1 and let the caller resolve manually.

Recipe-specific Option offered alongside the three defaults (when B1 fires):

- `migrate-snapshotting` — pause; caller manually creates `EventSourcedEntityModule.declarative(...)` registration with the correct `SnapshotPolicy`, removes the companion bean, then re-invokes. See [04-snapshot-blocker.md](use-cases/04-snapshot-blocker.md) for the full worked example.

### B2 — Map-typed `@AggregateMember`

`@AggregateMember Map<K, V>` field. AF5 `@EntityMember` supports `List<Value>` only (see [multi-entity-migration.adoc](../../docs/paths/aggregates/multi-entity-migration.adoc) § "Maps are not supported"). The official migration path is to rewrite the field as `List<Value>` and manage key-based identification either inside the parent entity or through a custom resolver. That rewrite is NOT mechanical inside the recipe's scope:

- The parent's `@EventSourcingHandler` bodies that mutate the map (`put`, `remove`) become list operations + manual id lookups.
- Any command handler that reads `map.get(key)` becomes a list scan with id-equality.
- Readers / projections / tests that observed the map shape — **all outside this recipe's scope** — need parallel updates.

The recipe halts because the redesign cannot be made safely while only seeing the aggregate's file. The caller owns the change. Detect with `grep -nE '@AggregateMember[\\s\\S]{0,200}Map<' <aggregate file>`.

**Recipe-specific Option** offered alongside the three defaults:

- `redesign-map-to-list` — pause this item; caller rewrites the `Map<K, V>` member as `List<V>` plus internal id management (or a custom resolver), updates every reader/projection that observed the map, then re-invokes the skill.

### B3 — `SagaTestFixture` in the target's test class

Only relevant when a `<target>Test` exists in scope. `grep -RnE 'SagaTestFixture' <test class>`. AF5 has no replacement. The recipe halts because the caller must decide whether to leave the saga test on AF4 deps (skip the test class), drop the test, or redesign it for AF5 patterns.

### B4 — `@DeadlineHandler` / `DeadlineManager` on the aggregate

Detect with `grep -RnE '@DeadlineHandler|DeadlineManager|deadlineManager\\.schedule|cancelSchedule|cancelAllWithinScope' <aggregate file> <aggregate package>`. AF5 has no direct deadline successor. The caller decides whether to redesign the deadline flow, remove it, or leave it on AF4 deps.

### Unmet project prerequisites

- Project does not compile pre-recipe — the `axon4to5-isolatedtest` Skill cannot establish a baseline. Surface as Blocker `prerequisite-not-compiling`.

## Out of Scope

- Sibling aggregates, projectors, sagas.
- `application.properties` / `application.yaml` / Spring config beans (except the narrow Path B registration line for `$SOURCE` itself).
- Logging changes, package renames, formatting changes.
- DCB introduction or `AggregateBasedEventStorageEngine` swap.
- Adding new tests when `target_test` does not exist (surface "no test coverage" as a Learning instead).
- Resolving cross-recipe interactions (e.g. "the projector still receives events") — orchestrator territory.

## References

Inherits the catalog baseline (see DEFAULT.md § Toolbox baseline). Recipe-specific entries — each is a markdown link to the actual file under `references/docs/paths/`, followed by its apply-condition:

- [aggregates/index.adoc](../../docs/paths/aggregates/index.adoc) — *apply-condition:* always.
- [aggregates/configuration-migration.adoc](../../docs/paths/aggregates/configuration-migration.adoc) — *apply-condition:* always (different sections of this file cover Path A `@EventSourced` annotation choice and Path B `EventSourcedEntityModule` registration; the recipe picks the relevant sub-section based on `configuration` argument).
- [aggregates/multi-entity-migration.adoc](../../docs/paths/aggregates/multi-entity-migration.adoc) — *apply-condition:* scope contains at least one `@AggregateMember` field.
- [aggregates/polymorphism-migration.adoc](../../docs/paths/aggregates/polymorphism-migration.adoc) — *apply-condition:* `$SOURCE` is abstract `@AggregateRoot` OR has concrete `@Aggregate` subclasses in the same module.
- [messages.adoc](../../docs/paths/messages.adoc) — *apply-condition:* any command or event class in scope (always for this recipe).
- [test-fixtures.adoc](../../docs/paths/test-fixtures.adoc) — *apply-condition:* `<target>Test` exists in scope AND blocker B3 did not fire.

The orchestrator never reads these — the recipe consults them at FLOW.md S3 (Read References) and re-consults at S6 (Plan Migration).

## Success Criteria

Extends DEFAULT.md baseline. The DEFAULT.md three baseline criteria (compile-clean, tests green via `axon4to5-isolatedtest`, no silent behavioural regressions) remain in force. Recipe adds:

### Recipe-specific structural invariants

For every file in `# Scope`:

1. **No AF4 imports survive** — none of these substrings appear in any in-scope file (caught by grep on the file body):
   - `org.axonframework.modelling.command.AggregateIdentifier`
   - `org.axonframework.modelling.command.CreationPolicy`
   - `org.axonframework.modelling.command.AggregateLifecycle`
   - `org.axonframework.modelling.command.AggregateMember`
   - `org.axonframework.modelling.command.AggregateRoot`
   - `org.axonframework.modelling.command.TargetAggregateIdentifier`
   - `org.axonframework.spring.stereotype.Aggregate`
   - `import org.axonframework.commandhandling.CommandHandler;`
   - `import org.axonframework.eventsourcing.EventSourcingHandler;`
   - `import static org.axonframework.modelling.command.AggregateLifecycle`

2. **Entity stereotype emitted explicitly** — `$SOURCE` carries either `@EventSourced(tagKey = "...", idType = <Id>.class)` (Path A, configuration=spring) OR `@EventSourcedEntity(tagKey = "...", idType = <Id>.class)` (Path B, configuration=native). `tagKey` and `idType` are **always** emitted literally — never relying on framework defaults — so renames don't silently break tag routing.

3. **`@EntityCreator` present** — on at least one constructor of `$SOURCE` (typically the no-arg). For polymorphic subtypes, on at least one constructor of each concrete subtype.

4. **`EventAppender` threaded through every `@CommandHandler`** — every method annotated `@CommandHandler` on `$SOURCE` (or child entities) carries an `EventAppender` parameter; every `AggregateLifecycle.apply(...)` body has been rewritten to `eventAppender.append(...)`.

5. **Polymorphic shape** (only when applicable, see Step P) — the abstract base carries `@EventSourcedEntity(concreteTypes = { Sub1.class, ... })`; concrete subtypes carry NO class-level `@EventSourced` / `@EventSourcedEntity`.

6. **Multi-entity shape** (only when applicable, see Step M) — `@AggregateMember` → `@EntityMember` 1:1; child entities have NO class-level `@EventSourced` / `@EventSourcedEntity` (reached via parent); child has `@EntityCreator` and uses `EventAppender` in its own `@CommandHandler` methods.

7. **Path B registration** (only when `configuration=native`) — the Configurer file contains `EventSourcedEntityModule.autodetected(<IdType>.class, <Entity>.class)` for `$SOURCE` registered through `configurer.modelling().registerEventSourcedEntity(...)` or equivalent.

Aggregation rule: **all match (AND)** — DEFAULT.md baseline AND this section's checks.

### Verification

Use the `axon4to5-isolatedtest` Skill per DEFAULT.md § Verification. `target-name` is the simple class name of `$SOURCE`. `main-sources` enumerate every file in `# Scope`. `test-sources` enumerate `<target>Test` and its subclass tests when present; otherwise `[]`.

`extra-deps` baseline: `org.axonframework:axon-modelling`, `org.axonframework:axon-eventsourcing`, `org.axonframework:axon-test`. Add `org.axonframework.extensions.spring:axon-spring-boot-starter` (or the AxonIQ commercial coordinate) when `configuration=spring`.

## Toolbox

### Path A — Spring Boot (`configuration=spring`)

*Apply-condition:* `configuration=spring`.

1. Replace AF4 `@Aggregate` (`org.axonframework.spring.stereotype.Aggregate`) with AF5 `@EventSourced` (`org.axonframework.extension.spring.stereotype.EventSourced`). The `.extension.spring.` infix is mandatory — `org.axonframework.spring.stereotype.EventSourced` does not exist.
2. Emit attributes **always explicitly**:
   ```java
   @EventSourced(tagKey = "<EntityName>", idType = <IdType>.class)
   public class <EntityName> { ... }
   ```
   - `tagKey` — convey the *entity type*, e.g. `"Bike"`, not the field name `"bikeId"`. Always written even if it equals the framework default (simple class name) — renames otherwise break routing silently.
   - `idType` — set to the type of the AF4 `@AggregateIdentifier` field. Default is `String.class`; mismatched type → silent identifier-resolution failure.
   - If `snapshotTriggerDefinition` was present AND the companion bean was translatable, the B1 auto-migration path in Research already handled the annotation change and module registration — this step has nothing extra to do for the attribute. If the companion bean was NOT translatable, B1 fired as Blocker and the recipe never reached this step; after the caller resolves and re-invokes, the attribute is gone and this step proceeds normally.

### Path B — Native Configurer (`configuration=native`)

*Apply-condition:* `configuration=native`.

1. Replace AF4 `@Aggregate` / `@AggregateRoot` with AF5 `@EventSourcedEntity` (`org.axonframework.eventsourcing.annotation.EventSourcedEntity`). Same `tagKey` / `idType` rules as Path A.
2. Locate the project's Configurer wiring file (typical names: `*Configuration`, `*Application`, `*Bootstrap`, per-slice `<Slice>Configuration`; `.java` or `.kt`). Add registration:
   ```java
   EventSourcingConfigurer.create()
       .registerEntity(EventSourcedEntityModule.autodetected(<IdType>.class, <Entity>.class))
       .registerCommandHandlingModule(...)
       .start();
   ```
   Or, for per-slice projects, inside the slice's `static EventSourcingConfigurer configure(EventSourcingConfigurer)` method. `<IdType>` must match the `idType` on `@EventSourcedEntity`.
3. If the project's command handler lives in a separate class and is not registered, add via `CommandHandlingModule.autodetectedCommandHandlingComponent(...)`. If the configurer file cannot be located → emit Blocker `configurer-file-not-found` with NOTES naming the failed search.

### Common steps (always — both paths)

*Apply-condition:* always.

1. **Commands** — for each command class in `# Scope`:
   - remove `import org.axonframework.modelling.command.TargetAggregateIdentifier`; add `import org.axonframework.modelling.annotation.TargetEntityId`; replace `@TargetAggregateIdentifier` with `@TargetEntityId`.
   - annotate the class with `@Command` (`org.axonframework.messaging.commandhandling.annotation.Command`). `@RoutingKey` on a property → `@Command(routingKey = "<propertyName>")` + remove `@RoutingKey`.
2. **Events** — for each event class in `# Scope`:
   - identify the property the AF4 `@AggregateIdentifier` field is set from inside an `@EventSourcingHandler` — that's the property that must carry `@EventTag(key = "<EntityName>")`. Without DCB, exactly one `@EventTag` per event.
   - annotate the class with `@Event` (`org.axonframework.messaging.eventhandling.annotation.Event`). `@Revision("x")` → `@Event(version = "x")`; remove `@Revision`.
3. **Aggregate body**:
   - remove `@AggregateIdentifier` annotation + import; the id field stays as a plain field.
   - replace import `org.axonframework.eventsourcing.EventSourcingHandler` → `org.axonframework.eventsourcing.annotation.EventSourcingHandler`.
   - replace import `org.axonframework.commandhandling.CommandHandler` → `org.axonframework.messaging.commandhandling.annotation.CommandHandler`.
   - annotate the no-arg constructor with `@EntityCreator` (`org.axonframework.eventsourcing.annotation.reflection.EntityCreator` — the `.reflection.` infix is mandatory). Grep before adding — OpenRewrite often already added it; duplicates compile but signal partial state.
   - replace `AggregateLifecycle.apply(event)` → `eventAppender.append(event)` body-by-body; add `EventAppender eventAppender` (`org.axonframework.messaging.eventhandling.gateway.EventAppender` — the `.messaging.` infix is mandatory) as the last parameter of every `@CommandHandler`. Remove the static import of `AggregateLifecycle.apply`.
4. **`@CreationPolicy` mapping** (per `aggregates/index.adoc` § Removal of `@CreationPolicy`). OpenRewrite drops the annotation; verify the resulting handler shape matches the original semantics:
   - `ALWAYS` → make the `@CommandHandler` **static**. OpenRewrite usually does NOT flip to `static` — verify.
   - `CREATE_IF_MISSING` → instance `@CommandHandler` + no-arg `@EntityCreator` (default post-OpenRewrite). Domain rule against empty state runs instead of the AF4 `AggregateNotFoundException` path — re-check the surrounding domain invariants don't NPE on null state.
   - `NEVER` (or absent) → instance `@CommandHandler` (default).

### Step M — Multi-entity (`@AggregateMember` → `@EntityMember`)

*Apply-condition:* scope contains at least one `@AggregateMember` field.

1. Replace import `org.axonframework.modelling.command.AggregateMember` → `org.axonframework.modelling.entity.annotation.EntityMember`.
2. Replace `@AggregateMember` → `@EntityMember`. For collection-of-entity fields keep `routingKey = "<childIdProperty>"`.
3. **Map-typed members** — emit Blocker B2, exit. No edits to Map-typed members.
4. Each child entity gets `@EntityCreator` and uses `EventAppender` in its own `@CommandHandler` methods. Child entities do NOT get class-level `@EventSourced` / `@EventSourcedEntity` — they are discovered through the parent.

### Step P — Polymorphic (`concreteTypes`)

*Apply-condition:* `$SOURCE` is abstract `@AggregateRoot` OR has concrete `@Aggregate` subclasses inheriting handlers.

1. Keep the base class abstract; remove `@Aggregate` / `@AggregateRoot` and its import from the base.
2. Add `@EventSourcedEntity(concreteTypes = { Sub1.class, Sub2.class, ... })` (Path B) OR `@EventSourced(concreteTypes = ...)` (Path A) to the base.
3. Concrete subtypes do NOT carry `@EventSourced` / `@EventSourcedEntity` — discovered through the base.
4. Inherited `@EventSourcingHandler` methods stay on the base. Subtype-specific handlers stay on subtypes. Both base and subtypes use `EventAppender` in their `@CommandHandler` methods.
5. Each concrete subtype carries `@EntityCreator` on one constructor.

### T — Test fixture migration

*Apply-condition:* `target_test` exists in `# Scope` AND Blocker B3 did not fire (no `SagaTestFixture` usage in the test class).

1. Migrate base test first, then any subclasses.
2. Replace `AggregateTestFixture` with `AxonTestFixture`:
   - import `org.axonframework.test.aggregate.AggregateTestFixture` → `org.axonframework.test.fixture.AxonTestFixture`.
   - field type `AggregateTestFixture<?>` → `AxonTestFixture`.
   - `@BeforeEach` body — `new AggregateTestFixture<>(<target>.class)` → `AxonTestFixture.with(<configurer>)` where `<configurer>` is:
     ```java
     EventSourcingConfigurer.create()
         .registerEntity(EventSourcedEntityModule.autodetected(<IdType>.class, <Entity>.class))
     ```
   - add `@AfterEach tearDown() { fixture.stop(); }`.
3. Fluent given/when/then:
   - `fixture.given(events…)` → `fixture.given().events(events…)`
   - `fixture.givenNoPriorActivity()` → `fixture.given().noPriorActivity()`
   - `.when(cmd)` → `.when().command(cmd)`
   - `.expectEvents(events…)` → `.then().events(events…)`
   - `.expectException(Cls.class)` → `.then().exception(Cls.class)`
   - inside `eventsSatisfy(events -> …)` lambdas: `events.get(0).payload()` / `.metaData()` (AF5 record-style — NOT `getPayload()` / `getMetaData()`).
4. **AF5 exception flips** — `AggregateNotFoundException` is NOT thrown for instance handlers in AF5 with no-arg `@EntityCreator`. The framework materialises an empty entity and runs the handler — any project domain rule against empty state surfaces instead. Replace the assertion with the project's existing exception/rule on empty state (do NOT invent a new exception type). Static creational handlers throw `EntityAlreadyExistsForCreationalCommandHandlerException` when the entity already exists.

## Use cases

Each entry is a markdown link to the full before/after example, followed by its apply-condition.

- [01-spring-boot-straight.md](use-cases/01-spring-boot-straight.md) — *apply-condition:* `configuration=spring` AND no `@AggregateMember` AND no polymorphism AND no `snapshotTriggerDefinition`.
- [02-native-configurer-straight.md](use-cases/02-native-configurer-straight.md) — *apply-condition:* `configuration=native` AND no `@AggregateMember` AND no polymorphism AND no `snapshotTriggerDefinition`.
- [03-constructor-command-handler.md](use-cases/03-constructor-command-handler.md) — *apply-condition:* `$SOURCE` has at least one `@CommandHandler` constructor (creation via annotated constructor, not `@CreationPolicy`).
- [04-snapshot-blocker.md](use-cases/04-snapshot-blocker.md) — *apply-condition:* `$SOURCE` has `snapshotTriggerDefinition` attribute on `@Aggregate`.
- [05-multi-entity.md](use-cases/05-multi-entity.md) — *apply-condition:* scope contains at least one `@AggregateMember` field (any collection shape — `List`, `Set`, or `Map`).
- [06-polymorphic.md](use-cases/06-polymorphic.md) — *apply-condition:* `$SOURCE` is abstract `@AggregateRoot` with concrete `@Aggregate` subclasses.
- [07-test-fixture.md](use-cases/07-test-fixture.md) — *apply-condition:* `<target>Test` exists AND uses `AggregateTestFixture`.
- [08-rejected-projector.md](use-cases/08-rejected-projector.md) — *apply-condition:* `$SOURCE` annotated `@ProcessingGroup` AND zero `@CommandHandler` methods.

## Gotchas

- **OpenRewrite leaves phantom LSP errors** — package-private types referenced from sub-package tests sometimes show `cannot resolve` in the IDE but compile fine via `javac` / the build tool. If the `axon4to5-isolatedtest` Skill returns green, the migration is fine. Do NOT chase phantom LSP errors by adding `public` modifiers.
- **Default `tagKey` is invisible** — the framework defaults `tagKey` to the entity's simple class name. Agents routinely forget to write it when names coincide, leaving the contract invisible to readers and breaking on rename. Always emit `tagKey = "<EntityName>"` literally.
- **Default `idType` is `String.class`** — if the AF4 `@AggregateIdentifier` field is NOT a `String`, omitting `idType` causes silent identifier-resolution failure. Always emit explicitly when the id is not `String`.
- **`@EntityCreator` import has `.reflection.` infix** — the path is `org.axonframework.eventsourcing.annotation.reflection.EntityCreator`, NOT `org.axonframework.eventsourcing.annotation.EntityCreator`. The shorter path does not exist; the LLM almost always guesses wrong.
- **`@CommandHandler` import has `.messaging.` infix** — `org.axonframework.messaging.commandhandling.annotation.CommandHandler`, NOT `org.axonframework.commandhandling.annotation.CommandHandler`.
- **`EventAppender` import has `.messaging.` infix** — `org.axonframework.messaging.eventhandling.gateway.EventAppender`, NOT `org.axonframework.eventhandling.gateway.EventAppender`.
- **`@EventSourced` Spring stereotype is in the `.extension.spring.` package** — `org.axonframework.extension.spring.stereotype.EventSourced`, NOT `org.axonframework.spring.stereotype.EventSourced`.
- **Constructor-based command handlers (no `@CreationPolicy`)** — when the AF4 creation command is handled by an annotated constructor, the AF5 shape typically becomes either a static `@CommandHandler` factory (Pattern: ALWAYS-creation) OR a `@EntityCreator` constructor that receives the creation event. See `aggregates/index.adoc` § `@EntityCreator` patterns (1, 2, 3). Pick Pattern 3 (creation-from-origin-event) when the AF4 constructor copied fields directly from the command — it is the smallest behavioural diff.
- **Idempotent re-runs** — if the source is already on AF5 shape (e.g. previously migrated and re-fed to the recipe), the pre-Apply Success Criteria check fires on FLOW.md S5 and the recipe returns Success with `NOTES: edits=none (idempotent)`. No retry. No AskUserQuestion.

## Result

Inherits DEFAULT.md baseline. Recipe-specific augmentations per outcome:

### Success

Say **"return SUCCESS"**, then **MUST emit** the result block (schema: FLOW.md § Result). `Recipe:` field is `axon4to5-aggregate`. NOTES per DEFAULT.md baseline (which Success Criteria passed, retries used, idempotent / edits=none when applicable).

### Blocker

Say **"return BLOCKER"**, then **MUST emit** the result block (schema: FLOW.md § Result). `Recipe:` field is `axon4to5-aggregate`. The recipe emits **one** Blocker result aggregating every detected blocker (see § Blocker, "Emission model — all blockers at once"). NOTES enumerate each detected blocker with its file:line. The Options block has one sub-section per detected blocker — each sub-section lists the three DEFAULT.md baselines (skip / revert / solve-manually) plus any recipe-specific options the blocker entry declared.

Example — single blocker (B1):

```
return BLOCKER

> **Result:** 🚧 Blocker
> **Source:** `com.dddheroes.heroesofddd.creaturerecruitment.write.dwelling.Dwelling`
> **Recipe:** axon4to5-aggregate
>
> **Notes:** 1 blocker detected. Caller must resolve before re-invoking.
>
> 1. **B1 (snapshotTriggerDefinition)** at `Dwelling.java:27` — `@Aggregate(snapshotTriggerDefinition = "dwellingSnapshotTrigger")`. AF5's `@EventSourced` / `@EventSourcedEntity` has no portable replacement attribute (see [configuration-migration.adoc](../../docs/paths/aggregates/configuration-migration.adoc) IMPORTANT note).
>
> **Options:**
>
> _For B1 (snapshot):_
> - [ ] **migrate-snapshotting** — pause; manually create `EventSourcedEntityModule.declarative(...)` registration with `SnapshotPolicy`, remove companion bean, then re-invoke. See [04-snapshot-blocker.md](use-cases/04-snapshot-blocker.md).
> - [ ] **skip** — leave `Dwelling` in its current partial state; queue moves on.
> - [ ] **revert** — undo this recipe's edits; restore the pre-recipe `@Aggregate(snapshotTriggerDefinition = "...")` form.
> - [ ] **solve-manually** — pause; caller removes the `snapshotTriggerDefinition` attribute (and the matching bean) without replacing it, then re-invokes.
```

Example — multiple blockers (B1 + B4 detected together):

```
return BLOCKER

> **Result:** 🚧 Blocker
> **Source:** `com.example.shipment.ShipmentWithSnapshot`
> **Recipe:** axon4to5-aggregate
>
> **Notes:** 2 blockers detected. Caller must resolve ALL before re-invoking.
>
> 1. **B1 (snapshotTriggerDefinition)** at `ShipmentWithSnapshot.java:14` — `@Aggregate(snapshotTriggerDefinition = "shipmentSnapshotTrigger")`. AF5 has no portable replacement attribute.
> 2. **B4 (deadline handler)** at `ShipmentWithSnapshot.java:42` — `@DeadlineHandler` method `onOverdue` plus `DeadlineManager` injection at `:24`. AF5 has no direct deadline successor.
>
> **Options:**
>
> _For B1 (snapshot):_
> - [ ] **migrate-snapshotting** — pause; manually create `EventSourcedEntityModule.declarative(...)` with `SnapshotPolicy`, remove companion bean, re-invoke.
> - [ ] **skip** — keep partial state; queue moves on.
> - [ ] **revert** — restore the pre-recipe `@Aggregate(snapshotTriggerDefinition = "...")` form.
> - [ ] **solve-manually** — pause; caller drops the attribute (and bean) without replacing it, re-invokes.
>
> _For B4 (deadline):_
> - [ ] **skip** — same.
> - [ ] **revert** — same; restore the `@DeadlineHandler` + `DeadlineManager` shape.
> - [ ] **solve-manually** — pause; caller redesigns or removes the deadline flow and re-invokes.
```

### Rejected

Say **"return REJECTED"**, then **MUST emit** the result block (schema: FLOW.md § Result). `Recipe:` field is `axon4to5-aggregate`. NOTES must name the failed `# Applicable` predicate (1 saga / 2 projector / 3 state-stored / 6 unrecognised). When a sister recipe handles the source, mention it in NOTES (e.g. "route to event-processor recipe").

Example:

```
return REJECTED

> **Result:** ⏭️ Rejected
> **Source:** `com.dddheroes.heroesofddd.creaturerecruitment.read.DwellingReadModelProjector`
> **Recipe:** axon4to5-aggregate
>
> **Notes:** Applicable predicate 2 failed — class is annotated `@ProcessingGroup` with zero `@CommandHandler` methods; this is a projector, not an aggregate. Route to the event-processor recipe.
```

### Failure

Say **"return FAILURE"**, then **MUST emit** the result block (schema: FLOW.md § Result). NOTES must list failing Success Criteria + the last error verbatim. LEARNINGS nearly always present — record the hypothesis the next iteration starts from.
