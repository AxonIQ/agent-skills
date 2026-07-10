
# Implementation base

Everything below is normative for code emitted by the type-specific implementation skills. If a type-specific skill conflicts with this base, the type-specific one wins (it is more concrete).

## Where to look up Axon Framework 5 APIs

For all Axon Framework 5 API questions, use the **`axoniq-app-development`** plugin (install it alongside this one from the `axoniq` marketplace). Its `axoniq-app-dev` skill is the authoritative reference for AF5 APIs (commands, events, queries, projections, configuration, testing, interceptors, distributed messaging). Whenever you need annotation attributes, parameter resolution rules, fixture matchers, processor types, or any other framework-level question, **read the matching guide there**:

| Question | Guide (in the `axoniq-app-development` plugin) |
|---|---|
| What does `@Command` / `@Event` / `@Query` / `@CommandHandler` / `@EventHandler` / `@QueryHandler` / `@InjectEntity` / `@EventTag` / etc. accept? | `foundations/annotations.md` |
| Which Maven coordinates do I need? | `getting-started/dependencies.md` |
| How do I write a stateless command handler? | `commands/stateless.md` |
| How do I write a DCB / stateful command handler? | `commands/decision-models-dcb.md` |
| Sourcing condition / append condition / event criteria primitives? | `event-store/primitives.md` |
| How do projections work? Event processors? `@Timestamp`? | `events/handling-projections.md` (processors: `events/processors.md`) |
| Query handling, subscription queries, `QueryUpdateEmitter`? | `queries/query-handling.md` |
| Spring Boot auto-detection? `@EventSourced` stereotype? | `configuration/spring-boot.md` |
| AxonTestFixture details, matchers, async assertions? | `testing/basics.md` (matchers: `testing/matchers.md`; advanced: `testing/advanced.md`) |

This skill (`axoniq-platform`) sits **on top of** that framework reference. It only contains things that are project-specific: the spec-to-code mapping, our package layout, our marker files, our test enhancers, and bugs we've actually hit in this codebase.

## Package layout

```
{{source_directory}}/{{source_path}}/
├── api/
│   ├── events/        all event classes (single source of truth, shared across components)
│   ├── commands/      all commands AND command results
│   └── queries/       all queries AND query results
├── <component_a_snake>/                COMMAND component
│   ├── <ComponentA>State{{file_extension}}        # @EventSourced
│   ├── <ComponentA>CommandHandler{{file_extension}}
│   ├── <Exception>{{file_extension}}              # exceptions live here, not in a separate api/exception
│   └── .axoniq
├── <component_b_snake>/                QUERY component
│   ├── <ComponentB>Entity{{file_extension}}
│   ├── <ComponentB>Repository{{file_e
xtension}}
│   ├── <ComponentB>QueryComponent{{file_extension}}
│   ├── <ComponentB>Controller{{file_extension}}
│   └── .axoniq
├── <component_c_snake>/                EXTERNAL_SYSTEM stub
│   ├── <ComponentC>Service{{file_extension}}
│   └── .axoniq
└── <component_d_snake>/                WORKFLOW component
    ├── <ComponentD>Workflow{{file_extension}}     # @Workflow class with awaitEvent / awaitExecute steps
    └── .axoniq
```

Tests mirror this under `{{source_test_directory}}/{{source_path}}/<component_snake>/`.

**Rules:**
- `<component_snake>` is the `componentId` from the spec, lowercased, with `-` replaced by `_`. Preserve underscores in the package declaration; never collapse them.
- Events are NEVER duplicated. If `BikeRented` is emitted by a COMMAND component and consumed by a QUERY component, the class lives at `<base>.api.events.BikeRented` and both components import the same FQN.
- Exceptions live with the handler that throws them — in the component package, not in `api/exception`.
- The `<component_pkg>/.axoniq` marker is `{ "componentId": "<componentId>" }`. Always create it after writing component files. Never edit it by hand.

## Per-package `.axoniq` marker — write FIRST

Every component package gets a marker file:

```
{{source_directory}}/{{source_path}}/rent_bike/.axoniq
```

Content:
```json
{ "componentId": "rent-bike" }
```

**Write this as the very first file when creating a new component package** — before the state class, command handler, entity, controller, or any other code. The marker is what links the package to the spec component; if it's missing, an interrupted scaffolding run leaves orphan code with no obvious owner. Compile and test failures are expected during early iterations; they don't invalidate the package-to-spec link, so they shouldn't gate marker creation.

If you're invoked in **extend mode** (marker already present, spec has gained handlers), leave the marker alone — its presence is what made `SKILL.md` dispatch you in the first place.

Don't write anything else into the file — `{ "componentId": "..." }` is the entire contents.

## Imports that are easy to get wrong

The `axoniq-app-development` plugin has the full reference, but two clusters of imports recur enough in this codebase to call out:

**axon-workflow 0.1.0** (NOT covered by the `axoniq-app-development` plugin — that's a separate AxonIQ product):

| Concern | Import |
|---|---|
| `@Workflow` / `@OnFailure` / `@OnCancellation` | `io.axoniq.workflow.runtime.api.annotation.*` |
| `WorkflowStatus` | `io.axoniq.workflow.runtime.api.execution.status.WorkflowStatus` |
| `StepFailedException` | `io.axoniq.workflow.runtime.api.execution.state.StepFailedException` |
| `payloadProperty(...)` | `io.axoniq.workflow.runtime.association.PayloadPropertyValueRetriever.payloadProperty` |
| `SimpleWorkflowContext` / `.equalsTo(...)` | `io.axoniq.workflow.dsl.simple.SimpleWorkflowContext` |
| `Associations.associate(...)` | `io.axoniq.workflow.dsl.api.AssociationsUtils.associate` |

**AxonIQ Platform test enhancers** (this codebase only — not in OSS AF5):

| Concern | Import |
|---|---|
| `AxonServerConfigurationEnhancer` | `io.axoniq.framework.axonserver.connector.configuration.AxonServerConfigurationEnhancer` |
| `AxoniqPlatformEventsourcingConfigurerEnhancer` | `io.axoniq.platform.framework.eventsourcing.AxoniqPlatformEventsourcingConfigurerEnhancer` |

> ⚠️ These are NOT under `org.axonframework.axonserver.connector` or `io.axoniq.console.framework`. Don't guess — the FQNs above are verbatim.

**Event-handler annotations — `@EventHandler` vs `@EventSourcingHandler`** (these are different annotations in different packages, and confusing them is the #1 way new implementations silently break):

| Where you're writing | Annotation | Import |
|---|---|---|
| Inside a COMMAND component's `@EventSourced` state class — rebuilding state from past events | `@EventSourcingHandler` | `org.axonframework.eventsourcing.annotation.EventSourcingHandler` |
| Inside a QUERY component — projecting events into the read model | `@EventHandler` | `org.axonframework.messaging.eventhandling.annotation.EventHandler` |
| Inside an EXTERNAL_SYSTEM stub — reacting to events to call out to the world | `@EventHandler` | `org.axonframework.messaging.eventhandling.annotation.EventHandler` |
| Inside a WORKFLOW component | Neither — use the workflow DSL (`awaitEvent`, etc.) | — |

> ⚠️ **`@EventHandler` inside a state class does nothing.** The framework's event-sourcing path only dispatches to `@EventSourcingHandler`. If you use `@EventHandler` on a state method, the method is never invoked, the state stays at its initial value, every `if (state.isAlready...) throw ...` returns false, and the first command always succeeds — usually with the wrong outcome. Same symptom as the zero-event sourcing bug class. Cross-check imports before declaring a state class complete.

**Common AF5 handler/annotation imports** (the AF4 packages moved — these are the AF5 FQNs the implement skills emit by default, verified from the `axoniq-app-development` plugin's `foundations/annotations.md` and `commands/decision-models-dcb.md` guides):

| Annotation / Class | Import |
|---|---|
| `@Command` (on the message class) | `org.axonframework.messaging.commandhandling.annotation.Command` |
| `@CommandHandler` | `org.axonframework.messaging.commandhandling.annotation.CommandHandler` |
| `@Query` (on the message class) | `org.axonframework.messaging.queryhandling.annotation.Query` |
| `@QueryHandler` | `org.axonframework.messaging.queryhandling.annotation.QueryHandler` |
| `@Event` (on the event class) | `org.axonframework.messaging.eventhandling.annotation.Event` |
| `@EventHandler` (projections / external-system) | `org.axonframework.messaging.eventhandling.annotation.EventHandler` |
| `@EventSourcingHandler` (state-class handlers — see warning above) | `org.axonframework.eventsourcing.annotation.EventSourcingHandler` |
| `@EventSourced` (Spring stereotype — combines `@EventSourcedEntity` + `@Component` for auto-detection; what the skeleton emits) | `org.axonframework.extension.spring.stereotype.EventSourced` |
| `@EventSourcedEntity` (plain framework annotation — use only if you have a non-Spring entry point) | `org.axonframework.eventsourcing.annotation.EventSourcedEntity` |
| `@EntityCreator` | `org.axonframework.eventsourcing.annotation.reflection.EntityCreator` |
| `@EventCriteriaBuilder` | `org.axonframework.eventsourcing.annotation.EventCriteriaBuilder` |
| `@EventTag` (on event property — Kotlin needs `@field:EventTag`) | `org.axonframework.eventsourcing.annotation.EventTag` |
| `@InjectEntity` | `org.axonframework.modelling.annotation.InjectEntity` |
| `@InjectEntityId` | `org.axonframework.eventsourcing.annotation.reflection.InjectEntityId` |
| `@TargetEntityId` | `org.axonframework.modelling.annotation.TargetEntityId` |
| `@Timestamp` (on `Instant` parameter) | `org.axonframework.messaging.eventhandling.annotation.Timestamp` |
| `EventAppender` | `org.axonframework.messaging.eventhandling.gateway.EventAppender` |
| `EventCriteria` | `org.axonframework.messaging.eventstreaming.EventCriteria` |
| `SourcingCondition` | `org.axonframework.eventsourcing.eventstore.SourcingCondition` |

For anything not in the table, look it up in the **`axoniq-app-development`** plugin's `foundations/annotations.md` guide (the full attribute + import reference) before writing. **Never guess an FQN** — the AF4 → AF5 package moves are the #1 source of fabricated imports.

**Forbidden** (Axon Framework 4 patterns): `@AggregateIdentifier`, `@Aggregate`, `AggregateLifecycle.apply(...)`, `org.axonframework.commandhandling.CommandHandler` (the AF4 location — the AF5 annotation lives under `messaging.commandhandling.annotation`). None of these exist or are correct in AF5 — for everything they used to do, see the corresponding AF5 guide in the **`axoniq-app-development`** plugin. **Time-bounded behavior** ("wait N minutes / if X doesn't happen, do Y") is **not** done inside a handler — it's modeled as a `WORKFLOW` component that waits on the relevant event with a timeout. See [implement-workflow-component.md](implement-workflow-component.md).

## Command routing — `@Command(routingKey = "...")` is required

Whenever a command is going to be received by a handler that uses `@InjectEntity`, **the command class must be annotated with `@Command(routingKey = "<fieldName>")`**. The `routingKey` tells the command bus which field to route on in a distributed setup AND tells `@InjectEntity` which field carries the entity ID.

```kotlin
import org.axonframework.messaging.commandhandling.annotation.Command

@Command(routingKey = "rentalId")
data class StartRental(val rentalId: String, val bikeId: String, val customerId: String)
```

Pair the `routingKey` with `@InjectEntity(idProperty = "<sameName>")` on the handler side. They must reference the same field (simple ID case) or `idProperty` must reference a `@TargetEntityId`-annotated method (compound ID case — see below).

See the **`axoniq-app-development`** plugin's `foundations/annotations.md` (`@Command`) and `commands/decision-models-dcb.md` guides for the wider context.

## Decision trees (used by the type-specific implement skills)

### `@EventSourced` `idType`

| Identifier shape | Annotation |
|---|---|
| Single property of type `String` | `@EventSourced` (no `idType`) |
| Single property of non-String type (e.g. UUID, custom ID) | `@EventSourced(idType = MyId::class)` (Kotlin) / `@EventSourced(idType = MyId.class)` (Java) |
| Compound (multi-property) identifier | `@EventSourced(idType = SharedTargetIdentifier::class)` |

> ⚠️ **`@EventSourced` does NOT have a `tagKey` parameter.** The only valid param is `idType`. Tag-matching for the entity is carried by the static `@EventCriteriaBuilder` method on the entity class — that's where `EventCriteria.havingTags(Tag.of("rentalId", id))` lives. **Never** write `@EventSourced(tagKey = "...")` — that parameter doesn't exist; the annotation processor will not warn, but the framework will not load events.

### `@EntityCreator` constructor

```
Is the model used by MORE THAN ONE command?
├─ YES → @EntityCreator constructor()                                   # empty
└─ NO (single command)
    ├─ Simple ID:   @EntityCreator constructor(@InjectEntityId email: String)
    └─ Compound ID: @EntityCreator constructor(@InjectEntityId id: SharedTargetIdentifier)
```

When multiple commands share a model, they MUST all reference one shared `TargetIdentifier` class declared at the package level — not a nested class on each command.

### `@InjectEntity` `idProperty`

| Identifier | `idProperty` value |
|---|---|
| Simple, e.g. command has `email: String` field | `idProperty = "email"` (the property name) |
| Compound, command has `@TargetEntityId fun modelIdentifier(): SharedTargetIdentifier` | `idProperty = "modelIdentifier"` (the **method name, no parentheses**) |

Wrong forms (never emit):
- `@InjectEntityId("email")` — annotation takes no arguments
- Multiple `@InjectEntityId` parameters on one constructor
- `@InjectEntity(idProperty = "modelIdentifier()")` — no parentheses
- `@InjectEntity(idProperty = "roomId")` for a compound ID — must reference the method

## Event namespace — always set `@Event(namespace=, name=)`

Every event class in this codebase **must** be annotated with both `namespace=` and `name=`. The framework uses `"<namespace>.<name>"` as the event's type identifier — both at storage time AND at sourcing time. If `andBeingOneOfTypes(...)` references anything else (e.g. the Java FQN of the event class), sourcing matches nothing.

```kotlin
@Event(namespace = "<project-namespace>", name = "<EventName>")
data class <EventName>(...)
```

**Choosing `<project-namespace>`**: read the project's Maven `<artifactId>` from `pom.xml` (or Gradle `rootProject.name` from `settings.gradle.kts`). It's already kebab-case and stable. Use the same namespace for every event in the project — don't vary per-component.

Example: a project with `<artifactId>rent-bike</artifactId>` writes `@Event(namespace = "rent-bike", name = "RentalCreated")`, and the entity's `andBeingOneOfTypes(...)` references it as `"rent-bike.RentalCreated"`. The two must agree exactly.

If you set `namespace=` on the event but use the FQN string in `andBeingOneOfTypes(...)` (or vice-versa), the entity will silently reconstruct from zero events — same symptom class as forgetting `@EventTag`. See "the #1 silent bug" callout below.

## Tag & EventCriteria rules

Tags are how event-sourced entities find their events. They live in **two places** that must agree, and missing either side means the entity reconstructs from zero events (silently — there's no error).

For the underlying framework story see the **`axoniq-app-development`** plugin's `commands/decision-models-dcb.md` (Step 1 — Tag your events) and `event-store/primitives.md` (`EventCriteria`) guides. The rules below are the project-specific spec → code translation.

### 1. On EVENT class properties — `@EventTag`

Every event property whose `tagKey` is set in the spec **must** be annotated with `@EventTag` on the generated event class. Without this, events written to the store are not tagged, and `EventCriteria.havingTags(...)` finds nothing on replay.

Import: `org.axonframework.eventsourcing.annotation.EventTag`.

In Kotlin, use the **`@field:` use-site target** so the annotation lands on the backing field (not the constructor parameter):

```kotlin
import org.axonframework.eventsourcing.annotation.EventTag
import org.axonframework.messaging.eventhandling.annotation.Event

@Event(namespace = "<project-namespace>", name = "<EventName>")
data class <EventName>(
    @field:EventTag val <taggedProp1>: <Type>,    // tagKey set in messages/events/<EventName>.json
    @field:EventTag val <taggedProp2>: <Type>,    // tagKey set
    val <untaggedProp>: <Type>,                   // NOT tagged — no tagKey in spec
    // ...
)
```

In Java, just `@EventTag`:

```java
@Event(namespace = "<project-namespace>", name = "<EventName>")
public record <EventName>(
    @EventTag <Type> <taggedProp1>,
    @EventTag <Type> <taggedProp2>,
    <Type> <untaggedProp>
    // ...
) {}
```

If the spec's `tagKey` value differs from the property name (e.g. property `rentalId` with `"tagKey": "rental_id"`), set the annotation explicitly: `@field:EventTag("<custom_key>") val <propName>: <Type>`. Default is the property name, which is what you usually want.

### 2. On the entity class — `@EventCriteriaBuilder`

A static method on the entity returns an `EventCriteria` describing which events to pull during reconstruction. The criteria's `havingTags(...)` must reference the **same** tag keys that the events were written with.

```kotlin
import org.axonframework.messaging.eventstreaming.Tag
import org.axonframework.eventsourcing.annotation.EventCriteriaBuilder
import org.axonframework.messaging.eventstreaming.EventCriteria

@EventSourced
class <ComponentName>State {
    companion object {
        @JvmStatic
        @EventCriteriaBuilder
        fun resolveCriteria(<idProp>: <IdType>): EventCriteria =
            EventCriteria
                .havingTags(Tag.of("<tagKey>", <idProp>))
                .andBeingOneOfTypes(
                    "<project-namespace>.<EventName1>",
                    "<project-namespace>.<EventName2>",
                    // ...one entry per event the state evolves on.
                    // String format = "<@Event.namespace>.<@Event.name>" — must match what the events were written with.
                )
    }
}
```

Rules:
- `Tag.of(key, value)` — both arguments required.
- `havingTags(...)` requires at least one tag and **must** be followed by `andBeingOneOfTypes(...)`.
- Tag keys come from the spec's `messages/events/*.json` `properties[].tagKey` fields. Never invent tags. Properties not used for validation should not be tagged.

### Compound identifier

If the entity is keyed by multiple properties, the events must carry **all** as `@EventTag`s, and `havingTags(...)` must include all components:

```kotlin
EventCriteria.havingTags(
    Tag.of("<tagKey1>", id.<part1>),
    Tag.of("<tagKey2>", id.<part2>),
).andBeingOneOfTypes(...)
```

### Zero-event sourcing — the #1 silent bug class

Symptoms: `AxonTestFixture` `given().event(X).when().command(Y)` produces an entity that looks like it loaded zero events — every `@EventSourcingHandler` is skipped, the state is at its initial value, every `if (state.isAlready...) throw ...` returns false, etc. Tests fail with "expected exception X but command succeeded" or "expected event Y but got Z".

Three causes — check all three when this symptom appears:

1. **Missing `@EventTag`** — an event property the spec marks as tagged doesn't actually have `@field:EventTag` (Kotlin) or `@EventTag` (Java) on the event class. Events are written without that tag; `EventCriteria.havingTags(...)` finds nothing.
2. **Wrong event-type string in `andBeingOneOfTypes(...)`** — the string must be `"<namespace>.<name>"` matching `@Event(namespace=, name=)` on the class. If the criteria uses the Java FQN (`com.example.api.events.<EventName>`) but events were written with `@Event(namespace = "rent-bike", name = "RentalCreated")`, the type lookup yields nothing.
3. **Missing `@Event(namespace=, name=)` on the event class itself** — without the annotation the framework defaults to the Java FQN as the type, which then disagrees with whatever string the criteria builder uses. Always set both `namespace=` and `name=`.

## AxonTestFixture base setup

The **`axoniq-app-development`** plugin's `testing/basics.md` guide is the authoritative reference for the fixture API (Given/When/Then, matchers, async `await`, `EventTestUtils`). The setup below is project-specific because it disables AxonIQ Platform's auto-connect enhancers — every component test in this codebase begins with the same scaffolding.

Imports — these specific FQNs are easy to guess wrong, so use them verbatim:

```kotlin
import org.axonframework.test.fixture.AxonTestFixture
import org.axonframework.eventsourcing.configuration.EventSourcingConfigurer
import org.axonframework.eventsourcing.configuration.EventSourcedEntityModule
import org.axonframework.messaging.commandhandling.configuration.CommandHandlingModule
import io.axoniq.framework.axonserver.connector.configuration.AxonServerConfigurationEnhancer
import io.axoniq.platform.framework.eventsourcing.AxoniqPlatformEventsourcingConfigurerEnhancer
```

Class shape:

```kotlin
class <ComponentName>AxonFixtureTest {
    private lateinit var fixture: AxonTestFixture

    @BeforeEach
    fun beforeEach() {
        var configurer = EventSourcingConfigurer.create()
        val stateEntity = EventSourcedEntityModule
            .autodetected(IdType::class.java, <ComponentName>State::class.java)
        val commandHandlingModule = CommandHandlingModule
            .named("<ComponentName>")
            .commandHandlers()
            .autodetectedCommandHandlingComponent { <ComponentName>CommandHandler() }

        configurer = configurer
            .registerEntity(stateEntity)
            .registerCommandHandlingModule(commandHandlingModule)
            .componentRegistry { cr ->
                cr.disableEnhancer(AxonServerConfigurationEnhancer::class.java)
                cr.disableEnhancer(AxoniqPlatformEventsourcingConfigurerEnhancer::class.java)
            }

        fixture = AxonTestFixture.with(configurer)
    }

    @AfterEach
    fun afterEach() { fixture.stop() }
}
```

The Java equivalent is the same shape with JUnit Jupiter's `BeforeEach`/`AfterEach`.

### Pitfall: pass plain event payloads to `fixture.given().event(...)` — NEVER `GenericTaggedEventMessage`

```kotlin
// WRONG — tags are silently lost; entity sourcing finds nothing
fixture.given().event(tagged(<EventName>(...), "<tagKey>", "<value>"))
```

`TaggedEventMessage<E>` does NOT extend `EventMessage`. The fixture's `payload instanceof EventMessage` check is `false`, so the whole tagged wrapper is treated as an opaque payload — the event is stored with no meaningful tags. When `@InjectEntity` later sources by tag, it finds nothing and the entity stays at its initial state.

**Always pass plain payload objects**: `fixture.given().event(<EventName>("rental-1", ...))`. The fixture runs each payload through `AnnotationBasedTagResolver`, which reads `@EventTag` on the payload class and attaches the correct tags automatically. Manual tag construction is neither needed nor correct.

### Required Maven dependency for tests

`AxonTestFixture` lives in `org.axonframework:axon-test`. The skeleton's `pom.xml` should already include it as a `test`-scope dependency. If not (e.g. older skeleton), add:

```xml
<dependency>
    <groupId>org.axonframework</groupId>
    <artifactId>axon-test</artifactId>
    <scope>test</scope>
</dependency>
```

QUERY components do NOT get write-side fixture tests. Spring tests are optional.

## Event handler timestamps — `@Timestamp Instant`

When a projection or external-system handler needs the event's recorded timestamp, the `Instant` parameter **must be annotated `@Timestamp`** — a plain `Instant` parameter without the annotation will fail to resolve at runtime.

```kotlin
import org.axonframework.messaging.eventhandling.annotation.Timestamp
import java.time.Instant

@EventHandler
fun on(event: <EventName>, @Timestamp timestamp: Instant) {
    entity.lastUpdatedAt = timestamp
}
```

(See the **`axoniq-app-development`** plugin's `events/handling-projections.md` guide for the full list of resolved parameters.)

## Kotlin gotchas (every one of these has bitten implementers)

### `private set` on `var` properties of an `@EventSourced` class

The Spring all-open compiler plugin rewrites `@Component`, `@Configuration`, `@EventSourced`, and other Spring stereotypes' classes to be `open`. Combining that with a `var ... private set` produces a warning-or-error about visibility mismatch, depending on toolchain version.

Don't write `private set` on state properties of an `@EventSourced` class. Use a plain `var` (the all-open plugin needs the setter accessible). If you need to lock down mutation, use a non-data class with explicit private fields and an `internal` setter exposed only to the `@EventSourcingHandler` methods.

### `event.payload` vs `event.payload()`

Inside an `eventsSatisfy { ... }` callback, the `events` collection contains entries whose `payload()` is a Java method, not a Kotlin property. Don't write `events.first().payload` — write `events.first().payload()`. Kotlin's property-syntax sugar only triggers for getters whose names start with `get` and have no arguments; the framework's `payload()` does not match that pattern from Kotlin's perspective.

Wrong:
```kotlin
.eventsSatisfy { events ->
    val event = events.first().payload as <EventName>  // ← payload not a property
}
```

Right:
```kotlin
.eventsSatisfy { events ->
    val event = events.first().payload() as <EventName>
}
```

## Compile + run-test commands

Detect the build platform from project root:

| Build | Compile | Run a single test class |
|---|---|---|
| Maven (`pom.xml` present) | `./mvnw -q -DskipTests compile` | `./mvnw -q test -Dtest='<ClassName>'` |
| Gradle (`build.gradle.kts` present) | `./gradlew -q compileJava` (Java) / `./gradlew -q compileKotlin` (Kotlin) | `./gradlew -q test --tests '<FQN>'` |

If both compile and tests pass, the implementation is good — let [SKILL.md](SKILL.md) mark the component as implemented.

If they fail, surface the failures literally. Don't change the contract (commands, events, queries, exceptions) to make tests pass — that is a spec-side concern. Use [refine-spec.md](refine-spec.md) if the spec really is wrong.

## Type-specific skills

After loading this base, dispatch to the right skill based on `componentType`:

- `COMMAND` → [implement-command-component.md](implement-command-component.md)
- `QUERY` → [implement-query-component.md](implement-query-component.md)
- `EXTERNAL_SYSTEM` → [implement-external-system-component.md](implement-external-system-component.md)
- `WORKFLOW` → [implement-workflow-component.md](implement-workflow-component.md)

Each type-specific skill specifies which files to write and which patterns to apply on top of these base rules.
