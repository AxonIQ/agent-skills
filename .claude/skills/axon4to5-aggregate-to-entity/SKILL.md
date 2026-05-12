---
name: axon4to5-aggregate-to-entity
description: >
  Migrate ONE Axon Framework 4 `@Aggregate` / `@AggregateRoot` class — together
  with its associated commands, events, and snapshot trigger — to the Axon
  Framework 5 event-sourced entity form (`@EventSourced` for Spring Boot or
  `@EventSourcedEntity` for plain Axon Configuration). Use when the user says
  "migrate aggregate", "convert @Aggregate to entity", "@Aggregate to
  @EventSourced", or names a single aggregate class to migrate. Covers every
  topic from the aggregate migration path plus the message-model and
  snapshotting migration paths: imports & package changes, entity
  configuration, static factory methods, the three `@EntityCreator` patterns,
  `EventAppender` vs `AggregateLifecycle`, `@AggregateMember` →
  `@EntityMember`, polymorphic aggregate hierarchies, command/event message
  annotations (`@TargetAggregateIdentifier` → `@TargetEntityId`, `@Revision`
  → `@Event(version=...)`, `@RoutingKey` → `@Command(routingKey=...)`,
  `@EventTag` on event aggregate-identifier fields), and snapshot trigger
  → `SnapshotPolicy` on `EventSourcedEntityModule`. Atomic — exactly one
  aggregate root per run; its directly-bound commands, events, and snapshot
  trigger bean travel with it. Behavior-preserving: AF4 semantics retained,
  no DCB introduced, legacy aggregate-based event store kept. Recognizes the
  AF4 candidate in either Spring Boot or plain Axon Configuration source;
  output flavor is controlled by `--configuration-mode` (default
  `spring-boot`). Event-sourced aggregates only — state-stored aggregates
  (AF4 `@Aggregate` whose state lives in JPA/JDBC rather than an event
  stream) are out of scope; the skill stops with an explicit message when
  one is detected.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(git diff:*), AskUserQuestion
argument-hint: "[--configuration-mode=spring-boot|axon-configuration] [target class FQN or file path]"
---

# Aggregate → Event-Sourced Entity

## Goal

Transform exactly one AF4 event-sourced aggregate class (and its child
entities, if any) into its AF5 event-sourced entity form, preserving AF4
semantics.

**Done when**:

- diff produced (or zero diff — the candidate may already be on AF5 form
  thanks to a prior pass), and the human reviewer accepts the result;
- if the candidate has unit tests of its own, those tests still pass on
  the touched class alone. A red full project build is **not** a failure
  of this skill — peer constructs are expected to be on AF4 mid-migration.

**Idempotency.** Prior tooling (OpenRewrite recipes, manual edits, an
earlier run of this skill) may have applied some or all of the target
form. Step 5 below checks the candidate against the AF5 target shape
**first** and short-circuits with zero diff if the goal is already
reached.

## What this migrates

- **From**: AF4 class annotated with `@Aggregate` (Spring stereotype,
  `org.axonframework.spring.stereotype.Aggregate`) or `@AggregateRoot`
  (core, `org.axonframework.modelling.command.AggregateRoot`) **whose
  state is reconstructed from events via `@EventSourcingHandler`
  methods** — i.e. event-sourced aggregates. Includes any child entities
  marked with `@AggregateMember` and polymorphic aggregate hierarchies
  registered with `withSubtypes(...)`.
- **To**: AF5 event-sourced entity:
  - `--configuration-mode=spring-boot` → `@EventSourced` from
    `org.axonframework.extension.spring.stereotype.EventSourced`.
  - `--configuration-mode=axon-configuration` → `@EventSourcedEntity` from
    `org.axonframework.eventsourcing.annotation.EventSourcedEntity`, plus
    explicit registration via `EventSourcedEntityModule.declarative(...)`
    (or `.autodetected(...)`) on the `EventSourcingConfigurer`.
- **Scope per run**: exactly one aggregate root class plus the messages
  and snapshot trigger bound to it:
  - **Child entities** reachable from the root via `@AggregateMember` —
    inseparable from the root's behavior.
  - **Command classes** appearing as the first parameter of the root's
    (or its children's / subtypes') `@CommandHandler` methods — they
    carry `@TargetAggregateIdentifier`, `@Revision`, `@RoutingKey` that
    must be migrated to keep routing working.
  - **Event classes** appearing as the first parameter of the root's
    `@EventSourcingHandler` methods (and any non-creation events
    `apply(...)`ed by command handlers) — they need `@EventTag` on the
    aggregate-identifier field so AF5 can keep the aggregate-based
    streaming model.
  - **Snapshot trigger bean** referenced by `@Aggregate(snapshotTriggerDefinition=...)`
    — migrated to a `SnapshotPolicy` on the entity module (or
    surfaced as a required follow-up when the target mode is
    `spring-boot`).
- **Languages**: Java, Kotlin (translate as needed). The skill rewrites
  annotations and imports **in place** — it does not convert Kotlin
  `data class` to Java records or vice versa.

### Not supported: state-stored aggregates

A state-stored aggregate is an AF4 `@Aggregate` whose state is **not**
reconstructed from events — usually marked with JPA annotations
(`@Entity`, `@Id`) and registered with a custom `Repository<T>` (often a
`GenericJpaRepository`) instead of an event-sourcing repository, with **no**
`@EventSourcingHandler` methods on the class. AF5 has no drop-in
replacement: entities in AF5 are event-sourced by design.

If step 4 identifies the candidate as state-stored, **stop**: report the
finding to the human via `AskUserQuestion`, do not edit anything, and
suggest re-running once the aggregate has been converted to event-sourced
form (or proceeding manually). This skill is not the place to invent a
state-stored migration path.

## Arguments

Parse from `$ARGUMENTS`:

| Argument | Values | Default | Meaning |
|----------|--------|---------|---------|
| `--configuration-mode` | `spring-boot` \| `axon-configuration` | `spring-boot` | Target AF5 wiring flavor |
| positional | class name, FQN, or file path | (empty) | Pin the candidate; otherwise selection rule applies |

The source flavor is **not** an argument. All four AF4-source × AF5-target
combinations are valid.

## Selection rule

1. If the user names a target (class name, FQN, file path) in
   `$ARGUMENTS`, resolve it with `Glob`/`Grep` and use that file. If it
   resolves to more than one file, ask the human via `AskUserQuestion`.
2. Otherwise, `Grep` for the AF4 source pattern:
   `@(Aggregate|AggregateRoot)\b` across `**/*.{java,kt}` and take the
   **first** match by lexical file path.
3. Never migrate more than one root candidate per run.

## Procedure

1. **Parse arguments.** Read `$ARGUMENTS`. Resolve `--configuration-mode`
   (default `spring-boot`) and any positional target. Echo the resolved
   values back to the human so the choice is visible.

2. **Select and read the relevant migration-path doc(s).** Consult the
   References routing table below and load **only** the rows whose load
   condition matches this run. Do not paraphrase from memory.

3. **Locate the candidate.** Use `Grep` with pattern
   `@(Aggregate|AggregateRoot)\b` over `**/*.{java,kt}` and apply the
   selection rule above.

4. **Classify the candidate.** Read the candidate file and a small
   radius around it to determine:

   - **Source flavor.** Use this table (recognition rules from
     `references/docs/`):

     | AF4 form | What to look for |
     |----------|------------------|
     | Spring Boot | Import `org.axonframework.spring.stereotype.Aggregate`; class is component-scanned; surrounding `@SpringBootApplication`. |
     | plain Axon | Import `org.axonframework.modelling.command.AggregateRoot` and/or explicit registration on `AggregateConfigurer` / `Configurer`; no Spring stereotype. |

   - **Event-sourcing check.** The class must have at least one
     `@EventSourcingHandler` method. If it instead carries JPA
     annotations (`@Entity`, `@Id`) and is registered with a
     state-stored repository (e.g. `GenericJpaRepository`) and has
     **no** `@EventSourcingHandler` methods, this is **state-stored** —
     stop per the "Not supported" section above.

   - **Multi-entity check.** Search the candidate file (and its package)
     for `@AggregateMember` fields. If present, expect to migrate them
     alongside the root — see "Topic 6" below. Note any `@EntityId`
     annotations on child-entity fields.

   - **Polymorphism check.** Look for any of:
     - `AggregateConfigurer.defaultConfiguration(<Root>.class).withSubtypes(...)`
       in surrounding configuration code (plain Axon form);
     - sibling classes annotated with `@Aggregate` that `extends` this
       class (Spring form).
     If found, mark this as polymorphic — see "Topic 7" below.

   - **Bound commands/events.** For every `@CommandHandler` method on
     the root (and its children/subtypes), record the type of the
     **first parameter** — that is the command class to migrate in
     Topic 8. For every `@EventSourcingHandler` method, record the
     **first parameter** type — that is the event class to migrate.
     Also walk command-handler bodies and collect each `apply(...)`
     argument type (non-creation events emitted by the aggregate). The
     skill resolves these types with `Grep`/`Glob` and migrates each
     file once — multiple handlers referencing the same class still
     produce a single edit.

   - **Snapshot trigger.** If the AF4 `@Aggregate` has a
     `snapshotTriggerDefinition = "<beanName>"` attribute, resolve that
     bean: `Grep` for `@Component("<beanName>")`, `@Bean
     "<beanName>"`, or a class extending
     `EventCountSnapshotTriggerDefinition` /
     `AggregateLoadTimeSnapshotTriggerDefinition`. Record the trigger
     type and its numeric threshold — Topic 9 needs both to derive the
     `SnapshotPolicy`.

5. **Check whether the goal is already reached.** Compare the candidate
   against the AF5 target shape for the chosen `--configuration-mode`:

   - target `spring-boot`: class already annotated with `@EventSourced`
     (from `org.axonframework.extension.spring.stereotype.EventSourced`),
     uses `@EntityCreator`, `EventAppender`, AF5 `@CommandHandler` /
     `@EventSourcingHandler` imports, no `@AggregateIdentifier`, no
     `@AggregateMember`, no `AggregateLifecycle.apply`.
   - target `axon-configuration`: class annotated with
     `@EventSourcedEntity`; explicit
     `EventSourcedEntityModule.declarative(...)` /
     `.autodetected(...)` registration in surrounding configuration code.

   Outcomes:

   - **Fully migrated** — report "already on AF5 target form, nothing to
     do" and jump to step 8 with an empty diff. Success.
   - **Partially migrated** — record which parts already match; step 6
     edits only what is still on AF4 form.
   - **Not migrated** — proceed normally.

6. **Apply the transformation** — work through every topic that applies
   (see "Transformation instructions" below). Skip any sub-step step 5
   marked as already complete. Use `Edit` for in-place changes.

7. **Show the diff.** Run `git diff <changed-files>` and summarize:

   - Files touched (or "none — already migrated")
   - Imports added/removed (per topic 1)
   - Source flavor → target flavor (e.g. `Spring Boot → spring-boot`)
   - Which topics applied (1, 2, 3, 4, 5, 6, 7)
   - Dropped AF4 attributes (`snapshotTriggerDefinition`, `@CreationPolicy`,
     `@EntityId` on child entities, `withSubtypes(...)` registration) —
     these are intentionally dropped, surface them so the human can
     confirm intent.
   - Behavior preserved / behavior intentionally changed (should be none).

8. **Stop and hand control to the human via `AskUserQuestion`** with
   options *Accept* / *Reject* / *Adjust*. Do not rely on `mvn compile`
   / `gradle build` as a success signal.

The skill stops here. Version control, running the app, and sequencing
the next migration are out of scope.

> **Fallback only**: if the loaded `.adoc` files and the transformation
> instructions leave a genuine gap (unknown shape, ambiguous target),
> surface the gap to the human and stop. Do not invent missing
> knowledge.

## Transformation instructions

Each topic below maps 1:1 to a section of the aggregate migration index
(`references/docs/aggregates/index.adoc`). The .adoc files are the
source of truth; the bullets here are the LLM-side guardrails the doc
alone does not cover. Treat the **class-body** changes as the same
regardless of source/target flavor; **wiring** changes depend on the
flavor pair (matrix at the end of each topic).

### Topic 1 — Imports & package changes (always applies)

Per `index.adoc#import-and-package-changes`:

- `org.axonframework.commandhandling.CommandHandler` →
  `org.axonframework.messaging.commandhandling.annotation.CommandHandler`
- `org.axonframework.eventsourcing.EventSourcingHandler` →
  `org.axonframework.eventsourcing.annotation.EventSourcingHandler`

Also remove these AF4-only imports when the matching annotation /
helper is gone after later topics:

- `org.axonframework.modelling.command.AggregateIdentifier`
- `org.axonframework.modelling.command.AggregateLifecycle` (+ static
  `.apply` import)
- `org.axonframework.modelling.command.AggregateMember`
- `org.axonframework.modelling.command.EntityId`
- `org.axonframework.modelling.command.AggregateCreationPolicy`
- `org.axonframework.modelling.command.CreationPolicy`
- `org.axonframework.spring.stereotype.Aggregate`

### Topic 2 — Entity configuration (always applies)

Class-level annotation swap:

| `--configuration-mode` | Replacement |
|------------------------|-------------|
| `spring-boot` | `@EventSourced` (`org.axonframework.extension.spring.stereotype.EventSourced`). Attributes on the AF4 `@Aggregate` (`snapshotTriggerDefinition`, `repository`, `cache`, `commandTargetResolver`) are **not** supported and must be dropped — surface them in the diff so the human can re-introduce equivalents separately (per `configuration-migration.adoc` IMPORTANT box). |
| `axon-configuration` | `@EventSourcedEntity` (`org.axonframework.eventsourcing.annotation.EventSourcedEntity`). |

Wiring matrix (per source × target):

| AF4 source → AF5 target | Wiring change |
|-------------------------|---------------|
| Spring Boot → `spring-boot` | Annotation swap is enough — component scan still picks the class up via `@EventSourced`. |
| Spring Boot → `axon-configuration` | Remove the Spring stereotype, ensure the class is no longer component-scanned, and register it explicitly: `configurer.modelling().registerEventSourcedEntity(EventSourcedEntityModule.declarative(<IdType>.class, <Entity>.class))` on an `EventSourcingConfigurer`. |
| plain Axon → `spring-boot` | Add `@EventSourced` and ensure the class lives under a component-scanned package. Drop the explicit `AggregateConfigurer` / `Configurer` registration. |
| plain Axon → `axon-configuration` | Replace the AF4 `AggregateConfigurer.defaultConfiguration(<Root>.class)` registration with `EventSourcedEntityModule.declarative(<IdType>.class, <Root>.class)` on the `EventSourcingConfigurer`. |

### Topic 3 — Static factory methods for creation (always applies when an AF4 creation `@CommandHandler` constructor exists)

AF4 instantiates aggregates via an annotated constructor. AF5 separates
instantiation (`@EntityCreator`, Topic 4) from creation command
handling (a **static** `@CommandHandler`).

- Convert each AF4 `@CommandHandler` constructor into a **static**
  `@CommandHandler` method on the class that takes the command +
  `EventAppender appender` and calls `appender.append(...)`.
- Remove any `@CreationPolicy` / `AggregateCreationPolicy` annotations
  — they have no AF5 equivalent. Behavior risk: `ALWAYS` /
  `CREATE_IF_MISSING` semantics. Mention each removed `@CreationPolicy`
  in the step 7 diff summary so the human can confirm the new shape
  matches intent. For `CREATE_IF_MISSING`, the migration-path doc
  describes an `@InjectState @Nullable` pattern using a stateful command
  handler — surface this as an option but do not apply it automatically;
  it changes semantics.

### Topic 4 — `@EntityCreator` annotation (always applies)

Every event-sourced entity in AF5 needs exactly one constructor marked
with `@EntityCreator`
(`org.axonframework.eventsourcing.annotation.reflection.EntityCreator`).
Pick the pattern that best matches the AF4 code (see
`index.adoc#entitycreator-annotation`):

- **Pattern 1 — no-arg** (recommended default): keep the AF4 no-arg
  constructor, drop its `// Required by Axon` comment, annotate it
  `@EntityCreator`. The identifier and other state are set in the
  `@EventSourcingHandler` for the creation event (which usually
  already exists in AF4 code).
- **Pattern 2 — identifier-only**: when the AF4 constructor took just
  the identifier and you want to keep doing that, use
  `@EntityCreator public Entity(@InjectEntityId <IdType> id) { ... }`.
  `@InjectEntityId` is **mandatory** here.
- **Pattern 3 — creation event**: when the AF4 creation flow was "set
  most fields from the first event", convert directly to
  `@EntityCreator public Entity(<CreationEvent> event) { ... }`. If
  the AF4 `@EventSourcingHandler` for that event becomes redundant
  after this, drop it; otherwise keep it.

### Topic 5 — `EventAppender` instead of `AggregateLifecycle` (always applies when AF4 used `apply(...)`)

For every non-creation `@CommandHandler`:

- Add `EventAppender appender` (or `eventAppender`) as a parameter.
- Replace each `AggregateLifecycle.apply(event)` (and any static
  `apply(...)` import) with `appender.append(event)`.
- Remove the static import of `AggregateLifecycle.apply` and the
  `AggregateLifecycle` import.

`EventAppender` lives at
`org.axonframework.messaging.eventhandling.gateway.EventAppender`.

### Topic 6 — `@AggregateMember` → `@EntityMember` (applies when step 4 found child entities)

Per `multi-entity-migration.adoc`:

- Replace `@AggregateMember` with `@EntityMember`
  (`org.axonframework.modelling.entity.annotation.EntityMember` — confirm
  package against the loaded .adoc).
- Add `routingKey = "<field>"` when the AF4 form relied on a routing
  field on the child entity (e.g. `transactionId`). The .adoc example
  uses `@EntityMember(routingKey = "transactionId")`.
- Drop `@EntityId` from child-entity fields — child identification flows
  through `routingKey` and constructor / `@EventSourcingHandler`
  population, not a field-level annotation.
- **Hard constraint**: `@EntityMember` only supports `List<Value>`. If
  the AF4 code uses `Map<Key, Value>` for child entities, **stop** and
  ask the human via `AskUserQuestion` how to proceed (refactor to
  `List<Value>` first, or skip this candidate). Do not silently
  rewrite the data structure — that changes domain semantics.
- Child entities themselves do **not** need a class-level
  `@EventSourced` / `@EventSourcedEntity` annotation (the .adoc
  example leaves the `Transaction` class unannotated). The
  `@EventSourcingHandler` methods on the child class may still need
  the AF5 import swap from Topic 1.

### Topic 7 — Polymorphic aggregate hierarchies (applies when step 4 found subtypes)

Per `polymorphism-migration.adoc`:

- AF4 form: `AggregateConfigurer.defaultConfiguration(<Root>.class).withSubtypes(Set.of(<Sub1>.class, <Sub2>.class))`,
  or each subtype annotated `@Aggregate` (Spring).
- AF5 form (`--configuration-mode=axon-configuration`):
  `EventSourcedEntityModule.declarative(<IdType>.class, <Root>.class)
  .messagingModel((cfg, b) -> PolymorphicEntityMetamodel.forSuperType(<Root>.class)
      .addConcreteType(AnnotatedEntityMetamodel.forConcreteType(<Sub1>.class, ...))
      .addConcreteType(AnnotatedEntityMetamodel.forConcreteType(<Sub2>.class, ...))
      .build())`
  registered on the `EventSourcingConfigurer`. The `AnnotatedEntityMetamodel.forConcreteType`
  call needs the four resolvers/converters pulled from configuration
  (`ParameterResolverFactory`, `MessageTypeResolver`, `MessageConverter`,
  `EventConverter`) — copy this shape verbatim from the .adoc.
- AF5 form (`--configuration-mode=spring-boot`): annotate the root
  `@EventSourced(concreteTypes = { <Sub1>.class, <Sub2>.class })`. If
  the project uses plain Axon Configuration on the AF5 side, prefer the
  `.autodetected(String.class, <Root>.class)` form, which discovers
  subtypes from the `concreteTypes` attribute automatically.
- Drop the per-subtype `@Aggregate` annotations from the subtypes once
  the root carries the registration; subtypes do not need their own
  class-level entity annotation.
- Surface the removed `withSubtypes(...)` call (and any per-subtype
  Spring `@Aggregate`s) in the diff summary so the human can confirm.

### Topic 8 — Command and event message annotations (always applies)

Per `references/docs/messages.adoc`. The aggregate root is useless
without the messages it routes, so the skill migrates them in the
same run. Edit each command/event class **in place** — keep its
declaration form (Java POJO, Java record, Kotlin `data class`).

**Annotation renames** (consult `messages.adoc#message-specific-annotations`):

| AF4 annotation | AF5 replacement | Notes |
|----------------|-----------------|-------|
| `@TargetAggregateIdentifier` (`org.axonframework.modelling.command`) on a command field | `@TargetEntityId` (`org.axonframework.modelling.annotation`) on the same field | Required for any command the aggregate handles, otherwise routing breaks. |
| `@RoutingKey` on a command field | drop the field-level annotation; add class-level `@Command(routingKey = "<fieldName>")` (`org.axonframework.messaging.commandhandling.annotation`) | `routingKey` value is the property name, not the field annotation. |
| `@Revision("X")` on a command/event class | class-level `@Event(version = "X")` (or `@Command(version = "X")`) | The version travels into `MessageType`; do **not** add `name = ...`/`namespace = ...` attributes — keep AF4 defaults to preserve `payloadType`-style behavior (see the IMPORTANT box in `messages.adoc`). |
| (no AF4 annotation) on event classes | class-level `@Event` (`org.axonframework.messaging.eventhandling.annotation.Event`) | Marks the event as an AF5 message; safe default. |
| (no AF4 annotation) on command classes that lack `@Revision` / `@RoutingKey` | class-level `@Command` (`org.axonframework.messaging.commandhandling.annotation.Command`) | Same reasoning as `@Event`. |

**`@EventTag` on the aggregate identifier field of every event** (per
`messages.adoc#event-tagging-for-aggregate-identification`):

- Identify the **aggregate-identifier field**: it is the field with the
  same name as the AF4 `@AggregateIdentifier` on the root (e.g. `bikeId`
  on a `Bike` aggregate produces `bikeId` on every event).
- Annotate that single field on each event class with
  `@EventTag(key = "<RootSimpleName>")` (`org.axonframework.eventsourcing.annotation.EventTag`).
- **Exactly one** `@EventTag` per event, keyed by the root's simple
  class name (e.g. `"Bike"`, `"GiftCard"`). The key is **not** the AF4
  aggregate-type-FQN, it is the simple name — this matches how the
  AF5 aggregate-based event store reconstructs the `type` column.
- If an event has no obvious aggregate-identifier field (e.g. it
  carries a derived id), surface the gap via `AskUserQuestion` and ask
  the human which field to tag; do not guess.

Wiring matrix for Topic 8 is the same for all four AF4×AF5 combos —
message classes are configuration-flavor-agnostic. Spring Boot vs plain
Axon does not change anything in this topic.

Cross-aggregate caveat: if a command/event is referenced by **more than
one** aggregate (rare but possible), the migration is still safe — the
AF5 annotations apply per-class. The `@EventTag` key, however, must
match the **owning** aggregate's simple name. When you detect a shared
event, surface the ambiguity to the human via `AskUserQuestion` instead
of arbitrarily picking a key.

### Topic 9 — Snapshotting (applies when step 4 found a `snapshotTriggerDefinition` attribute)

Per `references/docs/snapshotting.adoc`. Earlier topics dropped the
`snapshotTriggerDefinition` attribute from `@Aggregate`; Topic 9 is
where the equivalent AF5 behavior is restored.

Translation rules (from the trigger bean recorded in step 4):

| AF4 trigger bean | AF5 `SnapshotPolicy` |
|------------------|----------------------|
| `EventCountSnapshotTriggerDefinition(snapshotter, N)` | `SnapshotPolicy.afterEvents(N)` |
| `AggregateLoadTimeSnapshotTriggerDefinition(snapshotter, Duration.ofMillis(N))` | `SnapshotPolicy.whenSourcingTimeExceeds(Duration.ofMillis(N))` |
| Custom subclass of `SnapshotTriggerDefinition` | Surface to the human — derive a best-effort `SnapshotPolicy.afterEvents(...)` only if the threshold is obvious from the constructor. |

The threshold (`N`, `Duration`, …) must be carried over from the AF4
bean; never invent a new value.

Wiring matrix:

| AF4 source → AF5 target | Snapshot wiring change |
|-------------------------|------------------------|
| Spring Boot → `spring-boot` | The `@EventSourced` Spring annotation **does not** expose `snapshotPolicy` (per `snapshotting.adoc#spring_boot_configuration`). To keep snapshotting, the entity must be registered through an explicit `EventSourcedEntityModule` bean carrying `.snapshotPolicy(c -> ...)`. Emit (a) the `@Bean EventSourcedEntityModule<...>` configuration class, (b) a `@Bean SnapshotStore` defaulting to `InMemorySnapshotStore` (or `AxonServerSnapshotStore` if the AF4 setup pointed at Axon Server) and (c) remove the `@EventSourced` annotation from the entity class — the explicit module takes over registration. Surface this trade-off in the diff summary so the human can confirm. |
| Spring Boot → `axon-configuration` | Already on `EventSourcedEntityModule.declarative(...)` from Topic 2. Add `.snapshotPolicy(c -> <SnapshotPolicy>)` to the builder, and register a `SnapshotStore` component on the `EventSourcingConfigurer` (default to `InMemorySnapshotStore`; switch to `AxonServerSnapshotStore` only if the AF4 setup used Axon Server). |
| plain Axon → `spring-boot` | Same as Spring Boot → `spring-boot` — emit an explicit `EventSourcedEntityModule` `@Bean` rather than relying on `@EventSourced`. |
| plain Axon → `axon-configuration` | Same as Spring Boot → `axon-configuration` — add `.snapshotPolicy(...)` on the existing module and a `SnapshotStore` component. |

**Delete the AF4 snapshot bean class.** Once the policy lives on the
module, the `EventCountSnapshotTriggerDefinition` subclass is dead
code; surface its file path in the diff summary so the human can
remove it (or remove it directly in the same edit). Do not leave a
dangling Spring `@Component` referenced by name from a now-removed
attribute.

If `--configuration-mode=spring-boot` was chosen **and** there was no
AF4 snapshot trigger, Topic 9 is a no-op.

## Variants

Variants are routed on **observable shape**, not project identity. Each
row points at the topic(s) that primarily apply.

| Variant | Trigger | Topics that apply | Example |
|---------|---------|-------------------|---------|
| Simple event-sourced root | `@Aggregate` / `@AggregateRoot`, has `@EventSourcingHandler` methods, no `@AggregateMember`, no subtypes | 1, 2, 3, 4, 5, 8 (always) + 9 (only if a `snapshotTriggerDefinition` is present) | `references/examples/01-event-sourced-spring-boot.md`, `references/examples/04-messages.md`, `references/examples/05-snapshotting.md` |
| Multi-entity aggregate | Same as above + at least one `@AggregateMember` field | 1, 2, 3, 4, 5, 6, 8 (+ 9 if applicable) | `references/examples/02-multi-entity.md` + `04-messages.md` (+ `05-snapshotting.md`) |
| Polymorphic hierarchy | Configuration registers subtypes via `withSubtypes(...)` or subclasses are annotated `@Aggregate` | 1, 2, 3, 4, 5, 7, 8 (+ 9 if applicable) | `references/examples/03-polymorphic.md` + `04-messages.md` (+ `05-snapshotting.md`) |
| State-stored aggregate | `@Aggregate` + JPA `@Entity` / `@Id`, no `@EventSourcingHandler` | none — stop per step 4 | n/a |

## References

Reference files are **conditionally loaded**. Load only rows whose
condition matches the current run.

| Topic | File | Load when |
|-------|------|-----------|
| Topics 1, 3, 4, 5 (class-body changes shared across all four AF4×AF5 combos) | `references/docs/aggregates/index.adoc` | always |
| Topic 2 wiring details (Spring `@EventSourced` semantics, dropped attributes; plain `EventSourcedEntityModule` registration) | `references/docs/aggregates/configuration-migration.adoc` | always — both flavors are documented in the same file |
| Topic 6 (`@AggregateMember` → `@EntityMember`, `routingKey`, no-Map constraint) | `references/docs/aggregates/multi-entity-migration.adoc` | step 4 found `@AggregateMember` fields |
| Topic 7 (polymorphic registration: declarative + autodetected) | `references/docs/aggregates/polymorphism-migration.adoc` | step 4 found subtypes or `withSubtypes(...)` registration |
| Topic 8 (`@TargetEntityId`, `@Event`/`@Command`, `@EventTag`, `@Revision`/`@RoutingKey` → annotation attributes) | `references/docs/messages.adoc` | always — every aggregate has commands and events that must be migrated |
| Topic 9 (`SnapshotPolicy` on `EventSourcedEntityModule`; `SnapshotStore` registration; Spring Boot module-bean trade-off) | `references/docs/snapshotting.adoc` | step 4 found a `snapshotTriggerDefinition = "..."` attribute on `@Aggregate` |
| Canonical Spring Boot → Spring Boot simple-root before/after | `references/examples/01-event-sourced-spring-boot.md` | source flavor is Spring Boot **and** target is `--configuration-mode=spring-boot` **and** no `@AggregateMember`, no subtypes |
| Multi-entity (Spring Boot → spring-boot) before/after | `references/examples/02-multi-entity.md` | Variant "Multi-entity aggregate" triggers |
| Polymorphic (plain Axon → axon-configuration) before/after | `references/examples/03-polymorphic.md` | Variant "Polymorphic hierarchy" triggers |
| Messages: commands + events before/after | `references/examples/04-messages.md` | always — Topic 8 always runs |
| Snapshotting: trigger bean → policy + store | `references/examples/05-snapshotting.md` | Topic 9 triggers (snapshot bean present) |

## MUST / MUST NOT

| MUST | MUST NOT |
|------|----------|
| Read the `.adoc` rows in the References table whose load condition matches this run, before any edit | Paraphrase migration knowledge from memory |
| Load reference files conditionally per the References table | Load every file under `references/` on every run |
| Check the candidate against the AF5 target shape first; report "already migrated" and stop with zero diff when the goal is reached | Re-apply edits to code already on the target form |
| Migrate exactly one root candidate per run, and bring along its commands, events, and snapshot trigger bean — these are inseparable from the root's behavior | Sweep all aggregate roots in a single run, or migrate a shared command/event class outside the context of its owning aggregate |
| For Topic 8: rename `@TargetAggregateIdentifier` → `@TargetEntityId` on every command the aggregate handles, and add exactly one `@EventTag(key = "<RootSimpleName>")` on the aggregate-identifier field of every event the aggregate emits or sources | Tag multiple fields per event, invent identifier fields that don't exist, or omit the migration "because the event class is shared" — surface the ambiguity instead |
| For Topic 9: migrate the snapshot trigger threshold into a `SnapshotPolicy.afterEvents(N)` / `whenSourcingTimeExceeds(...)` and add a `SnapshotStore` registration; when target = `spring-boot`, switch the entity from `@EventSourced` to an explicit `EventSourcedEntityModule` `@Bean` (snapshotting cannot live on the annotation) | Silently drop the snapshot threshold; leave a dangling Spring `@Component` referenced by a now-removed `snapshotTriggerDefinition` attribute |
| Honour `--configuration-mode` (default `spring-boot`) for the output flavor | Detect the target flavor from surrounding code |
| Recognize the AF4 source in either Spring Boot or plain Axon form | Refuse to migrate because source flavor differs from target |
| Detect state-stored aggregates in step 4 and stop with a clear "not supported" message | Attempt to migrate a state-stored aggregate by improvising an event-sourcing path |
| Stop with `AskUserQuestion` when an `@AggregateMember` is on a `Map<Key,Value>` field — that data shape is not supported by `@EntityMember` | Silently rewrite a `Map` into a `List` — that changes domain semantics |
| Preserve AF4 behavior | Introduce DCB or other AF5 patterns that change semantics |
| Surface dropped AF4 attributes (snapshots, cache, `@CreationPolicy`, `@EntityId`, `withSubtypes(...)`) in the diff summary | Silently discard configuration the human may need to re-introduce manually |
| End with diff + `AskUserQuestion` for human review | Touch version control, run the app, or claim success on build/compile |
| Route Variants on observable shape | Route on project name or file path |
| Append new project quirks to `references/examples/` | Edit existing examples to overwrite |
