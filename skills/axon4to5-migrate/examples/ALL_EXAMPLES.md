# Axon Framework 4 → 5 Migration Examples

Automatically generated — do not edit manually. Regenerate with:
```
python3 scripts/generate_all_in_one.py
```

Concrete before/after examples showing full file migrations. Consult when a pattern alone is insufficient.

- [aggregates](#aggregates)
  - [01 — Spring Boot, straight migration (Path A)](#01--spring-boot-straight-migration-path-a)
  - [02 — Native Configurer, straight migration (Path B)](#02--native-configurer-straight-migration-path-b)
  - [03 — Constructor-style `@CommandHandler` (creation via annotated constructor)](#03--constructor-style-commandhandler-creation-via-annotated-constructor)
  - [04 — Snapshot trigger (B1 — Blocker, no migration path)](#04--snapshot-trigger-b1--blocker-no-migration-path)
  - [05 — Multi-entity (`@AggregateMember` → `@EntityMember`)](#05--multi-entity-aggregatemember--entitymember)
  - [06 — Polymorphic aggregate hierarchy (`concreteTypes`)](#06--polymorphic-aggregate-hierarchy-concretetypes)
  - [07 — Test fixture migration (`AggregateTestFixture` → `AxonTestFixture`)](#07--test-fixture-migration-aggregatetestfixture--axontestfixture)
  - [08 — Rejected: projector source routed to the aggregate recipe](#08--rejected-projector-source-routed-to-the-aggregate-recipe)
- [command gateway](#command-gateway)
  - [01 — Spring REST controller: `send(cmd, metadata)` → `.resultAs(Void.class)`](#01--spring-rest-controller-sendcmd-metadata--resultasvoidclass)
  - [02 — Spring REST controller: `sendAndWait` → preferred async `send(cmd, R.class)`](#02--spring-rest-controller-sendandwait--preferred-async-sendcmd-rclass)
  - [03 — Scheduler / runner: `sendAndWait` → import-only](#03--scheduler--runner-sendandwait--import-only)
  - [04 — Inline `CommandCallback` lambda → `.onSuccess(...).onError(...)`](#04--inline-commandcallback-lambda--onsuccessonerror)
  - [05 — Rejected: handler class with `CommandGateway` field](#05--rejected-handler-class-with-commandgateway-field)
- [event handlers](#event-handlers)
  - [01 — Pure projector (Spring)](#01--pure-projector-spring)
  - [02 — Projector with in-handler command dispatch (CommandGateway → CommandDispatcher)](#02--projector-with-in-handler-command-dispatch-commandgateway--commanddispatcher)
  - [03 — YAML + `@Bean SequencingPolicy` → class-level `@SequencingPolicy`](#03--yaml--bean-sequencingpolicy--class-level-sequencingpolicy)
  - [04 — Spring processor wiring: `EventProcessorDefinition` (Path A)](#04--spring-processor-wiring-eventprocessordefinition-path-a)
    - [application.yaml — drives the same processor's defaults](#applicationyaml--drives-the-same-processors-defaults)
  - [05 — Native processor wiring: `MessagingConfigurer.eventProcessing(...)` (Path B)](#05--native-processor-wiring-messagingconfigurereventprocessing-path-b)
  - [06 — Custom `SequencingPolicy` rewrite](#06--custom-sequencingpolicy-rewrite)
  - [07 — Dual-role class: `@EventHandler` + `@QueryHandler` on the same class](#07--dual-role-class-eventhandler--queryhandler-on-the-same-class)
  - [08 — Rejected: aggregate source routed to the event-processor recipe](#08--rejected-aggregate-source-routed-to-the-event-processor-recipe)
- [event store](#event-store)
  - [Use case 01 — Spring Boot + JPA backend](#use-case-01--spring-boot--jpa-backend)
  - [Use case 02 — Spring Boot + Axon Server backend](#use-case-02--spring-boot--axon-server-backend)
  - [Use case 03 — Framework Configurer + Axon Server backend (native)](#use-case-03--framework-configurer--axon-server-backend-native)
  - [Use case 04 — Framework Configurer + JPA backend (native)](#use-case-04--framework-configurer--jpa-backend-native)
- [interceptors](#interceptors)
  - [Use case 01 — Dispatch Interceptor, Spring Boot](#use-case-01--dispatch-interceptor-spring-boot)
  - [Use case 02 — Handler Interceptor, Spring Boot (with lifecycle hooks)](#use-case-02--handler-interceptor-spring-boot-with-lifecycle-hooks)
  - [Use case 03 — Handler Interceptor, Native Config (registration site rewrite)](#use-case-03--handler-interceptor-native-config-registration-site-rewrite)
  - [Use case 04 — Annotation-based interceptor (B1 Blocker)](#use-case-04--annotation-based-interceptor-b1-blocker)
- [query handlers](#query-handlers)
  - [01 — Spring REST controller: import-only change](#01--spring-rest-controller-import-only-change)
  - [01 — Simple @QueryHandler class: import-only swap](#01--simple-queryhandler-class-import-only-swap)
  - [02 — Blocking `.get()` call: prefer async upgrade; fallback to `.orTimeout().join()` when constrained](#02--blocking-get-call-prefer-async-upgrade-fallback-to-ortimeoutjoin-when-constrained)
  - [02 — Named query removal: queryName attribute → payload record](#02--named-query-removal-queryname-attribute--payload-record)
  - [03 — QueryUpdateEmitter: constructor injection → method parameter](#03--queryupdateemitter-constructor-injection--method-parameter)
  - [03 — ResponseType wrapper removal + `queryMany`](#03--responsetype-wrapper-removal--querymany)
  - [04 — Named query: string dispatch → `@Query`-annotated payload class](#04--named-query-string-dispatch--query-annotated-payload-class)
  - [04 — @ProcessingGroup → @Namespace and @MetaDataValue → @MetadataValue](#04--processinggroup--namespace-and-metadatavalue--metadatavalue)
  - [05 — Rejected: handler class with `QueryGateway` field](#05--rejected-handler-class-with-querygateway-field)
  - [05 — Rejected: class with no @QueryHandler](#05--rejected-class-with-no-queryhandler)
- [sagas](#sagas)
  - [Use case 01 — JPA state shape (Spring, no deadlines)](#use-case-01--jpa-state-shape-spring-no-deadlines)
  - [Use case 02 — DeadlineManager → Blocker with partial migration (comment out)](#use-case-02--deadlinemanager--blocker-with-partial-migration-comment-out)
  - [Use case 03 — Rejected: source is not a saga](#use-case-03--rejected-source-is-not-a-saga)

## aggregates

### 01 — Spring Boot, straight migration (Path A)

**Why this case is interesting:** Baseline Path A. `@Aggregate` → `@EventSourced`, `apply(...)` → `eventAppender.append(...)`, no-arg `@EntityCreator`, every event gets `@EventTag`. The shape every other use case extends from.

**Apply-condition:** `configuration=spring` AND no `@AggregateMember` AND no polymorphism AND no `snapshotTriggerDefinition`.

##### Before (AF4)

```java
package com.dddheroes.heroesofddd.calendar.write;

import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.eventsourcing.EventSourcingHandler;
import org.axonframework.modelling.command.AggregateCreationPolicy;
import org.axonframework.modelling.command.AggregateIdentifier;
import org.axonframework.modelling.command.CreationPolicy;
import org.axonframework.spring.stereotype.Aggregate;

import static org.axonframework.modelling.command.AggregateLifecycle.apply;

@Aggregate
class Calendar {

    @AggregateIdentifier
    private CalendarId calendarId;
    private Month currentMonth;
    private Week currentWeek;
    private Day currentDay;

    @CommandHandler
    @CreationPolicy(AggregateCreationPolicy.CREATE_IF_MISSING)
    void decide(StartDay command) {
        new CannotSkipDays(command, currentMonth, currentWeek, currentDay).verify();
        apply(DayStarted.event(command.calendarId(), command.month(), command.week(), command.day()));
    }

    @EventSourcingHandler
    void evolve(DayStarted event) {
        calendarId = new CalendarId(event.calendarId());
        currentMonth = new Month(event.month());
        currentWeek = new Week(event.week());
        currentDay = new Day(event.day());
    }

    @CommandHandler
    void decide(FinishDay command) {
        new CanOnlyFinishCurrentDay(command, currentMonth, currentWeek, currentDay).verify();
        apply(DayFinished.event(command.calendarId(), command.month(), command.week(), command.day()));
    }

    Calendar() { /* required by Axon */ }
}
```

##### After (AF5)

```java
package com.dddheroes.heroesofddd.calendar.write;

import org.axonframework.eventsourcing.annotation.EventSourcingHandler;
import org.axonframework.eventsourcing.annotation.reflection.EntityCreator;
import org.axonframework.extension.spring.stereotype.EventSourced;
import org.axonframework.messaging.commandhandling.annotation.CommandHandler;
import org.axonframework.messaging.eventhandling.gateway.EventAppender;

@EventSourced(tagKey = "Calendar", idType = CalendarId.class)
class Calendar {

    private CalendarId calendarId;
    private Month currentMonth;
    private Week currentWeek;
    private Day currentDay;

    @CommandHandler
    void decide(StartDay command, EventAppender eventAppender) {
        new CannotSkipDays(command, currentMonth, currentWeek, currentDay).verify();
        eventAppender.append(DayStarted.event(command.calendarId(), command.month(), command.week(), command.day()));
    }

    @EventSourcingHandler
    void evolve(DayStarted event) {
        calendarId = new CalendarId(event.calendarId());
        currentMonth = new Month(event.month());
        currentWeek = new Week(event.week());
        currentDay = new Day(event.day());
    }

    @CommandHandler
    void decide(FinishDay command, EventAppender eventAppender) {
        new CanOnlyFinishCurrentDay(command, currentMonth, currentWeek, currentDay).verify();
        eventAppender.append(DayFinished.event(command.calendarId(), command.month(), command.week(), command.day()));
    }

    @EntityCreator
    Calendar() { /* required by Axon */ }
}
```

Plus on every event class:

```java
import org.axonframework.eventsourcing.annotation.EventTag;
import org.axonframework.messaging.eventhandling.annotation.Event;

@Event
public record DayStarted(@EventTag(key = "Calendar") String calendarId, int month, int week, int day) { }
```

Plus on every command class:

```java
import org.axonframework.modelling.annotation.TargetEntityId;
import org.axonframework.messaging.commandhandling.annotation.Command;

@Command
public record FinishDay(@TargetEntityId String calendarId, int month, int week, int day) { }
```

##### What changed

- `@Aggregate` (`org.axonframework.spring.stereotype.Aggregate`) → `@EventSourced(tagKey = "Calendar", idType = CalendarId.class)` (`org.axonframework.extension.spring.stereotype.EventSourced` — the `.extension.spring.` infix is mandatory).
- `tagKey` AND `idType` always emitted explicitly. Defaults exist but invisible defaults break on rename.
- `@AggregateIdentifier` annotation + import removed. Field stays plain.
- `@CreationPolicy(CREATE_IF_MISSING)` removed — instance `@CommandHandler` + no-arg `@EntityCreator` is the default semantics in AF5. (See [aggregates/index.adoc](../../../docs/paths/aggregates/index.adoc) § Removal of `@CreationPolicy`.)
- `@CommandHandler` import → `org.axonframework.messaging.commandhandling.annotation.CommandHandler` (`.messaging.` infix mandatory).
- `@EventSourcingHandler` import → `org.axonframework.eventsourcing.annotation.EventSourcingHandler` (`.annotation.` infix).
- `@EntityCreator` annotation on the no-arg constructor (`org.axonframework.eventsourcing.annotation.reflection.EntityCreator` — `.reflection.` infix mandatory).
- `AggregateLifecycle.apply(event)` → `eventAppender.append(event)` for each handler; `EventAppender eventAppender` parameter added on every `@CommandHandler` (`org.axonframework.messaging.eventhandling.gateway.EventAppender` — `.messaging.` infix).
- Every event gets `@EventTag(key = "Calendar")` on the id field; class-level `@Event`. One tag per event (no DCB).
- Every command gets `@Command`; `@TargetAggregateIdentifier` → `@TargetEntityId`.

##### Caveats

- `tagKey` must be the **same string** on the entity and on every event. Pick the entity simple class name as the project default (`"Calendar"`), not the field name (`"calendarId"`).
- `idType` is non-default here (`CalendarId`, not `String`). Omitting it would fail silently at runtime, not at compile time.
- If the AF4 source had `@Aggregate(snapshotTriggerDefinition = "...")`, this use case's apply-condition doesn't match — the recipe emits Blocker B1 instead. See [04-snapshot-blocker.md](04-snapshot-blocker.md).
- Drop the AF4 framework-only no-arg constructor if `@EntityCreator` is on a new one; do not leave both.

---

### 02 — Native Configurer, straight migration (Path B)

**Why this case is interesting:** Path B replaces `@EventSourced` (Spring stereotype) with `@EventSourcedEntity` (framework annotation) AND requires explicit registration through the `EventSourcingConfigurer`. The annotation choice is non-cosmetic: choosing wrong leaves the entity un-registered at startup.

**Apply-condition:** `configuration=native` AND no `@AggregateMember` AND no polymorphism AND no `snapshotTriggerDefinition`.

##### Before (AF4)

```java
package io.axoniq.demo.gamerental.command;

import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.eventsourcing.EventSourcingHandler;
import org.axonframework.modelling.command.AggregateIdentifier;
import org.axonframework.spring.stereotype.Aggregate;

import static org.axonframework.modelling.command.AggregateLifecycle.apply;

@Aggregate
class Game {

    @AggregateIdentifier
    private String gameIdentifier;
    private int stock;
    private Set<String> renters;

    @CommandHandler
    public Game(RegisterGameCommand command) {
        apply(new GameRegisteredEvent(command.getGameIdentifier(),
                                      command.getTitle(), command.getReleaseDate(),
                                      command.getDescription(),
                                      command.isSingleplayer(), command.isMultiplayer()));
    }

    @CommandHandler
    public void handle(RentGameCommand command) {
        if (stock <= 0) throw new IllegalStateException("insufficient stock");
        apply(new GameRentedEvent(gameIdentifier, command.getRenter()));
    }

    @EventSourcingHandler
    public void on(GameRegisteredEvent event) {
        this.gameIdentifier = event.getGameIdentifier();
        this.stock = 1;
        this.renters = new HashSet<>();
    }

    @EventSourcingHandler
    public void on(GameRentedEvent event) {
        this.stock--;
        this.renters.add(event.getRenter());
    }

    public Game() { /* Required by Axon */ }
}
```

Plus, somewhere in the bootstrap:

```java
// AF4 — usually via Spring auto-discovery; for the native form:
AggregateConfigurer.defaultConfiguration(Game.class);
```

##### After (AF5)

```java
package io.axoniq.demo.gamerental.command;

import org.axonframework.eventsourcing.annotation.EventSourcedEntity;
import org.axonframework.eventsourcing.annotation.EventSourcingHandler;
import org.axonframework.eventsourcing.annotation.reflection.EntityCreator;
import org.axonframework.messaging.commandhandling.annotation.CommandHandler;
import org.axonframework.messaging.eventhandling.gateway.EventAppender;

@EventSourcedEntity(tagKey = "Game", idType = String.class)
public class Game {

    private String gameIdentifier;
    private int stock;
    private Set<String> renters;

    @EntityCreator
    public Game(GameRegisteredEvent event) {            // Pattern 3 — creation-from-origin-event
        this.gameIdentifier = event.gameIdentifier();
        this.stock = 1;
        this.renters = new HashSet<>();
    }

    @CommandHandler
    public static void handle(RegisterGameCommand cmd, EventAppender appender) {
        appender.append(new GameRegisteredEvent(cmd.gameIdentifier(), cmd.title(),
                                                 cmd.releaseDate(), cmd.description(),
                                                 cmd.singleplayer(), cmd.multiplayer()));
    }

    @CommandHandler
    public void handle(RentGameCommand cmd, EventAppender appender) {
        if (stock <= 0) throw new IllegalStateException("insufficient stock");
        appender.append(new GameRentedEvent(gameIdentifier, cmd.renter()));
    }

    @EventSourcingHandler
    public Game on(GameRentedEvent event) {
        this.stock--;
        this.renters.add(event.renter());
        return this;
    }
}
```

Configurer wiring (typically in `*Configuration.java`, `*Application.java`, or `*Bootstrap.java`):

```java
EventSourcingConfigurer.create()
    .registerEntity(EventSourcedEntityModule.autodetected(String.class, Game.class))
    .registerCommandHandlingModule(...)
    .start();
```

##### What changed

- `@Aggregate` (Spring stereotype) → `@EventSourcedEntity(tagKey = "Game", idType = String.class)` (framework annotation, `org.axonframework.eventsourcing.annotation.EventSourcedEntity`). NO `.extension.spring.` package here — that's Path A only.
- The annotated constructor `public Game(RegisterGameCommand)` is split:
  - Creation command becomes a **static** `@CommandHandler` factory taking `EventAppender`.
  - A new `@EntityCreator` constructor takes the origin event (`GameRegisteredEvent`) and seeds the state directly. This is Pattern 3 from [aggregates/index.adoc](../../../docs/paths/aggregates/index.adoc) § `@EntityCreator` patterns — the smallest behavioural diff for AF4 constructor-style creation handlers.
- `@AggregateIdentifier` removed; `gameIdentifier` stays plain.
- All `@CommandHandler` / `@EventSourcingHandler` imports move to AF5 packages (`.messaging.` / `.annotation.` infixes).
- `AggregateLifecycle.apply(...)` → `appender.append(...)`; `EventAppender appender` parameter on every `@CommandHandler`.
- AF4 `AggregateConfigurer.defaultConfiguration(Game.class)` → `EventSourcedEntityModule.autodetected(String.class, Game.class)` registered through `configurer.registerEntity(...)`. The first generic parameter (`String.class`) MUST match `idType` on `@EventSourcedEntity`.
- `@ExceptionHandler` on aggregate methods stays as-is — it is an Axon interceptor, not a Spring annotation, and AF5 keeps the import.

##### Caveats

- Mixing the two annotations is a classic mistake: do NOT emit `@EventSourced` under `configuration=native`. `@EventSourced` is the Spring stereotype; the framework Configurer only picks up `@EventSourcedEntity`.
- The `idType` first parameter of `EventSourcedEntityModule.autodetected(...)` must match the `idType` on `@EventSourcedEntity`. Mismatch → "no entity registered for id type X" at runtime, not at compile time.
- If the AF4 bootstrap also called `withSubtypes(...)`, you're in polymorphic territory — use case 06.
- If the AF4 bootstrap cannot be located (no `*Configuration.java` / `*Application.java` / `*Bootstrap.java`), emit Blocker `configurer-file-not-found` rather than guessing.

---

### 03 — Constructor-style `@CommandHandler` (creation via annotated constructor)

**Why this case is interesting:** The AF4 idiom of `public Entity(CreationCommand)` doesn't map 1:1 to AF5. There are three valid AF5 shapes (Patterns 1/2/3 in [aggregates/index.adoc](../../../docs/paths/aggregates/index.adoc) § `@EntityCreator` patterns). Pattern 3 — `@EntityCreator(<OriginEvent>)` — is the smallest behavioural diff for AF4 constructor-style handlers and is the recipe's default when no `@CreationPolicy` was declared. Wrong-pattern compiles cleanly and fails at runtime.

**Apply-condition:** `$SOURCE` has at least one `@CommandHandler` constructor (creation via annotated constructor, not `@CreationPolicy`).

##### Before (AF4)

```java
import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.eventsourcing.EventSourcingHandler;
import org.axonframework.modelling.command.AggregateIdentifier;
import org.axonframework.spring.stereotype.Aggregate;
import static org.axonframework.modelling.command.AggregateLifecycle.apply;

@Aggregate
public class Game {

    @AggregateIdentifier
    private String gameIdentifier;
    private int stock;

    @CommandHandler
    public Game(RegisterGameCommand command) {                  // ← creation via annotated constructor
        apply(new GameRegisteredEvent(command.getGameIdentifier(), command.getTitle()));
    }

    @CommandHandler
    public void handle(RentGameCommand command) {
        if (stock <= 0) throw new IllegalStateException("insufficient stock");
        apply(new GameRentedEvent(gameIdentifier, command.getRenter()));
    }

    @EventSourcingHandler
    public void on(GameRegisteredEvent event) {
        this.gameIdentifier = event.getGameIdentifier();
        this.stock = 1;
    }

    public Game() { /* required by Axon */ }
}
```

##### After (AF5) — Pattern 3 (creation-from-origin-event)

```java
import org.axonframework.eventsourcing.annotation.EventSourcedEntity;
import org.axonframework.eventsourcing.annotation.EventSourcingHandler;
import org.axonframework.eventsourcing.annotation.reflection.EntityCreator;
import org.axonframework.messaging.commandhandling.annotation.CommandHandler;
import org.axonframework.messaging.eventhandling.gateway.EventAppender;

@EventSourcedEntity(tagKey = "Game", idType = String.class)
public class Game {

    private String gameIdentifier;
    private int stock;

    @EntityCreator
    public Game(GameRegisteredEvent event) {                    // ← AF4 ctor → @EntityCreator on the origin event
        this.gameIdentifier = event.gameIdentifier();
        this.stock = 1;
    }

    @CommandHandler
    public static void handle(RegisterGameCommand cmd, EventAppender appender) {   // ← static creation handler
        appender.append(new GameRegisteredEvent(cmd.gameIdentifier(), cmd.title()));
    }

    @CommandHandler
    public void handle(RentGameCommand cmd, EventAppender appender) {
        if (stock <= 0) throw new IllegalStateException("insufficient stock");
        appender.append(new GameRentedEvent(gameIdentifier, cmd.renter()));
    }
}
```

##### Alternative AF5 shapes

- **Pattern 1 — no-arg `@EntityCreator`** + instance `@CommandHandler` for the creation command:
  ```java
  @EntityCreator
  public Game() { }                                              // empty entity materialised by framework

  @CommandHandler
  public void handle(RegisterGameCommand cmd, EventAppender appender) {
      if (gameIdentifier != null) throw new IllegalStateException("already registered");
      appender.append(new GameRegisteredEvent(cmd.gameIdentifier(), cmd.title()));
  }
  ```
  Use when the AF4 source had `@CreationPolicy(CREATE_IF_MISSING)` — the framework materialises an empty entity, the instance handler runs, the AF5 `@EventSourcingHandler` then seeds the state.

- **Pattern 2 — identifier-only `@EntityCreator`** + static creation handler:
  ```java
  @EntityCreator
  public Game(@InjectEntityId String gameIdentifier) {
      this.gameIdentifier = gameIdentifier;
  }
  ```
  Less common for AF4 constructor-style migrations; reserved for cases where the identifier is the only seed and the rest of state comes from a single canonical creation event.

##### Decision table

| AF4 shape | AF5 shape | Reasoning |
|---|---|---|
| `public Entity(CreationCommand)` (no `@CreationPolicy`) | **Pattern 3** — `@EntityCreator(OriginEvent)` + static `@CommandHandler` factory | Smallest behavioural diff: the creation event still drives state. |
| `@CreationPolicy(ALWAYS) void handle(CreationCommand)` | **Pattern 1** or **Pattern 3** + static `@CommandHandler` | AF5 framework throws `EntityAlreadyExistsForCreationalCommandHandlerException` on collision. |
| `@CreationPolicy(CREATE_IF_MISSING) void handle(...)` | **Pattern 1** — no-arg `@EntityCreator` + instance `@CommandHandler` | The handler runs against a freshly-materialised empty entity. See [aggregates/index.adoc](../../../docs/paths/aggregates/index.adoc) § Removal of `@CreationPolicy`. |
| `@CreationPolicy(NEVER) void handle(...)` (or absent) | Pattern N/A — instance `@CommandHandler` only (no `@EntityCreator` change) | Entity must already exist; default flow. |

##### What changed

- AF4 annotated constructor → AF5 **static** `@CommandHandler` factory taking `EventAppender`. The constructor's role (instantiating the entity) is taken over by a separate `@EntityCreator`.
- `@EntityCreator(OriginEvent)` (Pattern 3) replaces the AF4 framework-only no-arg constructor AND the AF4 `@EventSourcingHandler(OriginEvent)` body — both jobs collapse into the AF5 creator constructor. (The original `@EventSourcingHandler(OriginEvent)` can be deleted; its work moves into the `@EntityCreator` body.)
- `AggregateLifecycle.apply(...)` → `appender.append(...)` per usual.

##### Caveats

- **No compile-time signal for wrong pattern.** Pattern 1 with a NPE on null state, Pattern 3 with a missing `@EventSourcingHandler(OriginEvent)` body, both compile. Verify by running the entity's tests via `axon4to5-isolatedtest`.
- **Static AF5 creation handler can throw `EntityAlreadyExistsForCreationalCommandHandlerException`** when the entity already exists. If the AF4 source allowed re-registration (rare — usually it threw inside the constructor body), prefer Pattern 1.
- **Pattern 3 + leftover `@EventSourcingHandler(OriginEvent)`** double-seeds the entity. After moving the seeding logic into `@EntityCreator(OriginEvent)`, **delete** the matching `@EventSourcingHandler` to avoid double-mutation when sourcing past events.
- Spring metadata (`@Profile`, `@ExceptionHandler`) on aggregate methods is NOT touched — preserve verbatim. They are Axon / Spring annotations whose imports survive into AF5 unchanged.

---

### 04 — Snapshot trigger (B1 — Blocker, no migration path)

**Why this case is interesting:** `@Aggregate(snapshotTriggerDefinition = "...")` does NOT carry over to AF5. The `@EventSourced` / `@EventSourcedEntity` annotations do not expose a portable snapshotting attribute.

**B1 always fires as a Blocker.** There is currently no verified auto-migration path for snapshot trigger configuration in either `configuration=spring` or `configuration=native`. The `EventSourcedEntityModule.declarative()` builder chain required to wire `SnapshotPolicy` is non-trivial: `declarative()` returns `MessagingModelPhase`, which only exposes `messagingModel()`. The `snapshotPolicy()` method is only reachable on `OptionalPhase` — after all mandatory phases (`messagingModel() → entityFactory() → criteriaResolver()`) have been traversed. The correct end-to-end pattern has not yet been validated for auto-migration. Do NOT attempt auto-migration — always halt with Blocker B1 and let the caller resolve manually.

**Apply-condition:** `$SOURCE` has `snapshotTriggerDefinition` attribute on `@Aggregate`.

##### Detection

```
grep -nE 'snapshotTriggerDefinition|Snapshotter|SnapshotTriggerDefinition' <aggregate file> <aggregate package>
```

Also look for OpenRewrite leaving the marker `// TODO #LLM: reconfigure snapshot trigger ...` after stripping the attribute.

##### Blocker B1

**Trigger:** `$SOURCE` has `snapshotTriggerDefinition` attribute on `@Aggregate` — regardless of what the companion bean is.

The recipe halts because there is no verified auto-migration path. The caller resolves manually — typically by:

1. **Picking `solve-manually`** — edit the source to remove `snapshotTriggerDefinition`, remove the matching snapshot trigger bean wiring elsewhere in the codebase, then re-invoke the skill. The recipe re-scans on re-invocation; the attribute is gone, B1 doesn't fire, the recipe proceeds.
2. **Picking `revert`** — undo any partial edits the recipe applied; restore the pre-recipe `@Aggregate(snapshotTriggerDefinition = "...")` form.
3. **Picking `skip`** — leave the source in whatever partial state OpenRewrite left it; the queue moves on. The blocker shows up in the final report.

##### What the Blocker looks like

Source: heroes `Dwelling.java`, annotated `@Aggregate(snapshotTriggerDefinition = "dwellingSnapshotTrigger")`.

```
return BLOCKER

> **Result:** 🚧 Blocker
> **Source:** `com.dddheroes.heroesofddd.creaturerecruitment.write.dwelling.Dwelling`
> **Recipe:** axon4to5-aggregate
>
> **Notes:** 1 blocker detected. Caller must resolve before re-invoking.
>
> 1. **B1 (snapshotTriggerDefinition)** at `Dwelling.java:27` — `@Aggregate(snapshotTriggerDefinition = "dwellingSnapshotTrigger")`. AF5 `@EventSourced` / `@EventSourcedEntity` does not expose a portable replacement attribute (see [configuration-migration.adoc](../../../docs/paths/aggregates/configuration-migration.adoc) IMPORTANT note). There is currently no verified auto-migration path — the caller must resolve manually. The snapshot bean `dwellingSnapshotTrigger` is referenced ONLY from this aggregate; existing snapshot rows in event storage are not touched by this skill — data migration is out of scope.
>
> **Learnings:**
> - `Dwelling`'s `public DwellingId dwellingId;` field was made public solely for snapshotting; once snapshotting is dropped, it can be tightened to `private` during a follow-up stabilisation pass (not by this recipe).
>
> **Options:**
>
> _For B1 (snapshot):_
> - [ ] **skip** — leave `Dwelling` in its current partial state (any OpenRewrite edits already applied remain); queue moves on.
> - [ ] **revert** — undo this recipe's edits; restore the pre-recipe `@Aggregate(snapshotTriggerDefinition = "dwellingSnapshotTrigger")` shape.
> - [ ] **solve-manually** — pause; caller removes the `dwellingSnapshotTrigger` bean (and any snapshot-trigger configuration referencing it), strips the attribute from `@Aggregate`, then re-invokes the skill.
```

##### After the caller resolves manually and re-invokes

Source no longer has the attribute (the caller dropped it). The recipe re-scans, B1 no longer fires, the recipe proceeds normally and emits Success:

```java
// AF4 (after caller manually dropped the attribute)
@Aggregate
public class Dwelling { … }

// AF5 (configuration=spring)
@EventSourced(tagKey = "Dwelling", idType = DwellingId.class)
public class Dwelling { … }

// AF5 (configuration=native)
@EventSourcedEntity(tagKey = "Dwelling", idType = DwellingId.class)
public class Dwelling { … }
```

Result emitted on the re-invocation:

```
return SUCCESS

> **Result:** ✅ Success
> **Source:** `com.dddheroes.heroesofddd.creaturerecruitment.write.dwelling.Dwelling`
> **Recipe:** axon4to5-aggregate
>
> **Notes:** All Success Criteria match. The caller had previously resolved Blocker B1 by removing the `snapshotTriggerDefinition` attribute and the matching bean; re-scan found no blockers and the recipe proceeded.
```

##### Caveats

- **Existing snapshot rows in storage are NOT touched.** The recipe does not migrate stored data. When snapshotting is dropped (solve-manually), future loads replay the full event stream — a performance regression at large event counts.
- **Companion bean lifetime** — after the caller resolves manually, the original companion bean class (e.g. `BikeSnapshotDefinition`) is unreferenced dead code. The LEARNINGS block names it for the caller to delete.
- **Do NOT silently drop.** B1 MUST fire whenever `snapshotTriggerDefinition` is present. Do NOT attempt to auto-migrate, do NOT skip emitting the blocker.
- **`Snapshotter` / `SnapshotTriggerDefinition` direct field injections** (rare) also trigger B1. Detect via the same grep.

---

### 05 — Multi-entity (`@AggregateMember` → `@EntityMember`)

**Why this case is interesting:** `@EntityMember` replaces `@AggregateMember` AND its semantics tighten in two important ways: (1) **`Map<K, V>` is NOT supported** — AF5 accepts `List<Value>` only; (2) the child entity drops `@EntityId` and is reached strictly through the parent (no class-level `@EventSourced` / `@EventSourcedEntity` on the child). Every event still carries exactly **one** `@EventTag` — keyed to the ROOT, never the child.

**Apply-condition:** scope contains at least one `@AggregateMember` field (any collection shape).

##### Before (AF4) — `List<Transaction>` form (supported)

```java
import org.axonframework.modelling.command.AggregateMember;
import org.axonframework.modelling.command.EntityId;

@Aggregate
public class GiftCard {

    @AggregateIdentifier
    private String cardId;

    @AggregateMember
    private List<Transaction> transactions = new ArrayList<>();

    @CommandHandler
    public void handle(StartRedemptionCommand cmd) {
        apply(new RedemptionStartedEvent(cardId, cmd.transactionId(), cmd.amount()));
    }

    @EventSourcingHandler
    public void on(RedemptionStartedEvent evt) {
        this.transactions.add(new Transaction(evt.transactionId(), evt.amount()));
    }
}

public class Transaction {

    @EntityId
    private String transactionId;
    private int amount;
    private boolean completed;

    public Transaction(String transactionId, int amount) {
        this.transactionId = transactionId;
        this.amount = amount;
    }

    @CommandHandler
    public void handle(CompleteRedemptionCommand cmd) {
        if (completed) throw new IllegalStateException("already completed");
        apply(new RedemptionCompletedEvent(cmd.cardId(), cmd.transactionId()));
    }

    @EventSourcingHandler
    public void on(RedemptionCompletedEvent evt) {
        this.completed = true;
    }

    protected Transaction() { }
}
```

##### After (AF5) — `List<Transaction>` form

```java
import org.axonframework.modelling.entity.annotation.EntityMember;

@EventSourced(tagKey = "GiftCard")
public class GiftCard {

    private String cardId;

    @EntityMember(routingKey = "transactionId")             // ← key = child's id-property name
    private List<Transaction> transactions = new ArrayList<>();

    @EntityCreator
    public GiftCard() { }

    @CommandHandler
    public void handle(StartRedemptionCommand cmd, EventAppender appender) {
        appender.append(new RedemptionStartedEvent(cardId, cmd.transactionId(), cmd.amount()));
    }

    @EventSourcingHandler
    public void on(RedemptionStartedEvent evt) {
        this.transactions.add(new Transaction(evt.transactionId(), evt.amount()));
    }
}

public class Transaction {                                  // ← plain POJO, NO class-level annotation

    private String transactionId;                            // ← @EntityId removed, plain field
    private int amount;
    private boolean completed;

    public Transaction(String transactionId, int amount) {
        this.transactionId = transactionId;
        this.amount = amount;
    }

    @EntityCreator                                           // ← child also has @EntityCreator
    Transaction() { }

    @CommandHandler
    public void handle(CompleteRedemptionCommand cmd, EventAppender appender) {
        if (completed) throw new IllegalStateException("already completed");
        appender.append(new RedemptionCompletedEvent(cmd.cardId(), cmd.transactionId()));
    }

    @EventSourcingHandler
    public void on(RedemptionCompletedEvent evt) {
        this.completed = true;
    }
}

// Events — exactly ONE @EventTag per event, keyed to the ROOT (GiftCard).
public record RedemptionStartedEvent(@EventTag(key = "GiftCard") String cardId, String transactionId, int amount) { }
public record RedemptionCompletedEvent(@EventTag(key = "GiftCard") String cardId, String transactionId) { }
```

##### What changed

- Field annotation: `@AggregateMember` → `@EntityMember(routingKey = "transactionId")`. The `routingKey` value MUST equal the child's id-field name — typos compile, route nothing, fail in tests.
- Import: `org.axonframework.modelling.command.AggregateMember` → `org.axonframework.modelling.entity.annotation.EntityMember`.
- Child class: `@EntityId` annotation + import removed; the id field stays plain.
- Child class is a plain POJO — **NO** `@EventSourced` / `@EventSourcedEntity` at class level. The framework wires it through the parent's `@EntityMember`.
- Child class carries `@EntityCreator` on a no-arg constructor (or another supported pattern — see use case 03). The parent's AF4 framework-only `protected Transaction()` no-arg gets `@EntityCreator`.
- Every `@CommandHandler` on the child takes `EventAppender` parameter; bodies use `appender.append(...)`.
- Events keep exactly **one** `@EventTag` — keyed to the ROOT (`"GiftCard"`), never to the child. Children don't have their own event stream without DCB.

##### Blocker B2 — `Map<K, V>` form

If the AF4 source has `@AggregateMember Map<Key, Child>`:

```java
@AggregateMember
private Map<String, Transaction> transactionsById = new HashMap<>();
```

The recipe emits Blocker B2. The migration path documented in [multi-entity-migration.adoc](../../../docs/paths/aggregates/multi-entity-migration.adoc) ("Maps are not supported"): rewrite the field as `List<Value>` and manage id lookups internally OR via a custom resolver.

The rewrite is **not mechanical inside the recipe scope** because it touches:

- The parent's `@EventSourcingHandler` bodies that did `map.put(key, child)` / `map.remove(key)` — these become `list.add(...)` plus an explicit `list.removeIf(t -> t.txId().equals(key))` (or equivalent).
- Command handlers that did `map.get(key)` — these become a list scan with id-equality lookup, or a derived index field on the parent.
- Events' shape may need to change if the key was a synthetic id not previously emitted.
- **All readers / projections / tests outside the aggregate that observed the map shape** — `Map<K, V>` projections become `List<V>` ones, with all the breakage that implies.

Recipe-specific Option offered by the recipe alongside skip / revert / solve-manually:

- `redesign-map-to-list` — pause this item. Caller rewrites the `Map<K, V>` member as `List<V>` plus id-management logic, updates every reader/projection that observed the map, then re-invokes the skill. The recipe will then proceed via Step M with the standard `@EntityMember(routingKey = "<idProperty>") List<V>` mapping.

Example Blocker block:

```
return BLOCKER

> **Result:** 🚧 Blocker
> **Source:** `com.example.inventory.Inventory`
> **Recipe:** axon4to5-aggregate
>
> **Notes:** Blocker B2 (Map-typed @AggregateMember) fired at `Inventory.java:24` — `@AggregateMember private Map<String, StockItem> items`. AF5 `@EntityMember` supports `List<Value>` only (see [multi-entity-migration.adoc](../../../docs/paths/aggregates/multi-entity-migration.adoc) § "Maps are not supported"). Migration path: rewrite as `List<StockItem>` + internal id lookup (or custom resolver). The rewrite touches the parent's `@EventSourcingHandler` bodies (map put/remove → list ops), command-handler reads (`map.get(key)` → list scan), and every reader/projection that observed the map shape — all outside this recipe's scope.
>
> **Options:**
> - [ ] **skip** — leave `Inventory` in its current partial state; queue moves on.
> - [ ] **revert** — undo this recipe's edits; restore the pre-recipe `@AggregateMember Map<…>` shape.
> - [ ] **solve-manually** — pause; caller fixes by hand.
> - [ ] **redesign-map-to-list** — pause; caller rewrites the Map member as `List<V>` plus id-management logic, updates external readers/projections, then re-invokes with the new shape.
```

##### Caveats

- **`routingKey` must exactly match the child's id-field name.** Typos route nothing; runtime-only failure. Test every child command after migration.
- **Never put `@EventTag` on a child class or a child-shape event.** Tags belong to the ROOT entity — one per event.
- **Never annotate the child with `@EventSourced` / `@EventSourcedEntity`.** AF5 wires children through `@EntityMember`; double-annotation throws "entity already registered" at startup.
- **Drop the AF4 framework-only no-arg ctor on the child** once `@EntityCreator` is on a usable constructor; leaving both is dead code that risks confusion.
- For the Map → List rewrite, do NOT preserve the original key as a `String key` field on the child if it duplicates an existing id field. Single source of truth: the child's id field is its identity.

---

### 06 — Polymorphic aggregate hierarchy (`concreteTypes`)

**Why this case is interesting:** AF4 wires a polymorphic hierarchy through subclass `@Aggregate` stereotypes (Spring auto-detect) OR `AggregateConfigurer.withSubtypes(...)` (native). AF5 inverts this: **the base** carries `@EventSourcedEntity(concreteTypes = {Sub1.class, ...})` and subtypes drop their class-level stereotype entirely. Double-annotation throws "entity already registered" at startup.

**Apply-condition:** `$SOURCE` is abstract `@AggregateRoot` (or `@Aggregate`) with concrete `@Aggregate` subclasses in the same module.

##### Before (AF4)

```java
import org.axonframework.modelling.command.AggregateIdentifier;
import org.axonframework.modelling.command.AggregateRoot;
import org.axonframework.spring.stereotype.Aggregate;
import static org.axonframework.modelling.command.AggregateLifecycle.apply;

@AggregateRoot                                                  // ← abstract base also annotated
public abstract class Card {

    @AggregateIdentifier
    protected String cardId;
    protected int balance;

    @CommandHandler
    public void handle(DebitCardCommand cmd) {
        if (cmd.amount() > balance) throw new IllegalStateException("insufficient");
        apply(new CardDebitedEvent(cardId, cmd.amount()));
    }

    @EventSourcingHandler
    public void on(CardDebitedEvent e) {
        this.balance -= e.amount();
    }

    Card() { }
}

@Aggregate                                                       // ← subtype carries its own stereotype
public class OpenLoopGiftCard extends Card {

    @CommandHandler
    public OpenLoopGiftCard(IssueOpenLoopCommand cmd) {
        apply(new OpenLoopCardIssuedEvent(cmd.cardId(), cmd.amount()));
    }

    @EventSourcingHandler
    void on(OpenLoopCardIssuedEvent e) {
        this.cardId = e.cardId();
        this.balance = e.amount();
    }

    OpenLoopGiftCard() { }
}

@Aggregate
public class RechargeableGiftCard extends Card {

    @CommandHandler
    public RechargeableGiftCard(IssueRechargeableCommand cmd) {
        apply(new RechargeableCardIssuedEvent(cmd.cardId(), cmd.amount()));
    }

    @CommandHandler
    public void handle(RechargeCommand cmd) {
        apply(new CardRechargedEvent(cardId, cmd.amount()));
    }

    @EventSourcingHandler void on(RechargeableCardIssuedEvent e) { this.cardId = e.cardId(); this.balance = e.amount(); }
    @EventSourcingHandler void on(CardRechargedEvent e)            { this.balance += e.amount(); }

    RechargeableGiftCard() { }
}
```

Plus, for native projects, somewhere in the bootstrap:

```java
AggregateConfigurer.defaultConfiguration(Card.class)
    .withSubtypes(OpenLoopGiftCard.class, RechargeableGiftCard.class);
```

##### After (AF5) — native path (Path B)

```java
@EventSourcedEntity(
        tagKey = "Card",
        idType = String.class,
        concreteTypes = { OpenLoopGiftCard.class, RechargeableGiftCard.class }   // ← lives on the BASE only
)
public abstract class Card {

    protected String cardId;
    protected int balance;

    @EntityCreator
    protected Card() { }

    @CommandHandler
    public void handle(DebitCardCommand cmd, EventAppender appender) {
        if (cmd.amount() > balance) throw new IllegalStateException("insufficient");
        appender.append(new CardDebitedEvent(cardId, cmd.amount()));
    }

    @EventSourcingHandler
    public void on(CardDebitedEvent e) {
        this.balance -= e.amount();
    }
}

// NO class-level @EventSourcedEntity on subtypes — discovered via base's concreteTypes.
public class OpenLoopGiftCard extends Card {

    @EntityCreator
    public OpenLoopGiftCard() { }

    @CommandHandler
    public static void handle(IssueOpenLoopCommand cmd, EventAppender appender) {
        appender.append(new OpenLoopCardIssuedEvent(cmd.cardId(), cmd.amount()));
    }

    @EventSourcingHandler
    void on(OpenLoopCardIssuedEvent e) {
        this.cardId = e.cardId();
        this.balance = e.amount();
    }
}

public class RechargeableGiftCard extends Card {

    @EntityCreator
    public RechargeableGiftCard() { }

    @CommandHandler
    public static void handle(IssueRechargeableCommand cmd, EventAppender appender) {
        appender.append(new RechargeableCardIssuedEvent(cmd.cardId(), cmd.amount()));
    }

    @CommandHandler
    public void handle(RechargeCommand cmd, EventAppender appender) {
        appender.append(new CardRechargedEvent(cardId, cmd.amount()));
    }

    @EventSourcingHandler void on(RechargeableCardIssuedEvent e) { this.cardId = e.cardId(); this.balance = e.amount(); }
    @EventSourcingHandler void on(CardRechargedEvent e)            { this.balance += e.amount(); }
}
```

Bootstrap (native — Path B):

```java
configurer.registerEntity(
        EventSourcedEntityModule.autodetected(String.class, Card.class)         // ← registered ONCE on the base
);
// Delete the AF4 AggregateConfigurer.defaultConfiguration(Card.class).withSubtypes(...) call.
```

For Spring (Path A), substitute `@EventSourced(...)` for `@EventSourcedEntity(...)` on the base; bootstrap registration is auto-discovered.

##### What changed

- **Base class**: `@AggregateRoot` (or `@Aggregate`) → `@EventSourcedEntity(tagKey = "...", idType = ..., concreteTypes = { Sub1.class, Sub2.class })` (Path B) OR `@EventSourced(...)` (Path A).
- **Subtypes**: class-level `@Aggregate` annotation removed entirely. Subtypes carry NO stereotype — discovered via `concreteTypes`.
- `tagKey` lives on the **base** only. Subtypes inherit it. Every event from any subtype still carries `@EventTag(key = "<base tagKey>")` — one tag per event.
- `@AggregateIdentifier` removed from the base; protected id field stays plain.
- Every `@CommandHandler` / `@EventSourcingHandler` import moves to AF5 packages — on **both** the base AND every subtype.
- Subtype creation handlers (constructor-style) → **static** `@CommandHandler` factories. The base has a `protected @EntityCreator` no-arg constructor for the framework; each subtype has a `public @EntityCreator` constructor too.
- Native bootstrap: `AggregateConfigurer.defaultConfiguration(Base.class).withSubtypes(...)` → `EventSourcedEntityModule.autodetected(IdType.class, Base.class)`. Single registration on the base.

##### Caveats

- **Subtypes MUST NOT carry `@EventSourced` / `@EventSourcedEntity`.** Double-annotation throws "entity already registered" at startup.
- **`concreteTypes` MUST list every concrete subtype.** Missing entries surface as commands routed to the base instead of the intended subtype — runtime failure, no compile signal.
- **Subtypes MUST extend the migrated base.** A subtype still extending an AF4-shaped base (or one that lost its annotation by mistake) simply isn't discovered.
- **DO NOT migrate to `EventSourcedEntityModule.declarative(...)`** unless the project explicitly needs metamodel overrides. AutoDetected is the architecture-neutral path.
- **DO NOT force a concrete base abstract.** If the AF4 base was non-abstract, checkpoint with the user — making it abstract is a behavioural change.
- **`@EntityCreator` lives on both** the base (protected, framework-only no-arg) AND each subtype (public, supports the subtype's creation command). Forgetting either causes startup failure or routing failure.

---

### 07 — Test fixture migration (`AggregateTestFixture` → `AxonTestFixture`)

**Why this case is interesting:** The fixture API surface changes shape: `new AggregateTestFixture<>(Type.class)` → `AxonTestFixture.with(<configurer>)`, the given/when/then DSL becomes fluent (`.given().events(...)`, `.when().command(...)`, `.then().events(...)`), and AF5 record-style accessors (`payload()` / `metaData()`) replace AF4 getters. Most importantly: assertion expectations flip in two specific cases — `AggregateNotFoundException` (instance handlers) and `EntityAlreadyExistsForCreationalCommandHandlerException` (static handlers) — and silently flipping these masks real behavioural regressions.

**Apply-condition:** `<target>Test` exists in `# Scope` AND uses `AggregateTestFixture`. (Skipped entirely when Blocker B3 fires — i.e. the test class uses `SagaTestFixture`; the recipe halts before reaching the test-fixture migration step.)

##### Before (AF4)

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

##### After (AF5)

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

##### What changed

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

##### AF5 exception flips — silent migration risk

**Always re-check these two cases** when migrating a test class:

| AF4 expectation | AF5 reality | Fix |
|---|---|---|
| `expectException(AggregateNotFoundException.class)` on an **instance** `@CommandHandler` | AF5 + no-arg `@EntityCreator` materialises an empty entity, instance handler runs against null state, any project domain rule fires instead. | Replace with the project's existing domain exception (e.g. `CanOnlyFinishCurrentDay.Violation`). DO NOT invent a new exception type. |
| Test that should succeed but now throws `EntityAlreadyExistsForCreationalCommandHandlerException` | A previously-`@CreationPolicy(ALWAYS)` handler was migrated to **static** `@CommandHandler` — AF5 framework rejects re-creation. | Re-check the static-vs-instance choice (see use case 03 decision table). For `CREATE_IF_MISSING` semantics, use instance + no-arg `@EntityCreator`, not static. |

##### Caveats

- **Do NOT silently weaken assertions.** A flipped expectation that matches AF5 reality counts as Success only when the underlying behaviour is preserved. Replacing `expectException(AggregateNotFoundException)` with `expectSuccessfulHandlerExecution()` is a regression mask.
- **The fixture's identifier type matters.** `EventSourcedEntityModule.autodetected(<IdType>.class, ...)` MUST match the `idType` declared on the entity's `@EventSourced` / `@EventSourcedEntity`. Mismatched types fail at fixture-construction time — usually quickly surfaced.
- **`@AfterEach fixture.stop()` is non-optional.** Forgetting it leaks the embedded event store between tests; subtle ordering-dependent failures appear later.
- **`SagaTestFixture` is unrelated.** If the test class also uses `SagaTestFixture`, the recipe emits Blocker B3 (no AF5 saga fixture replacement) — only happens if a saga test was incorrectly placed alongside an aggregate test.

---

### 08 — Rejected: projector source routed to the aggregate recipe

**Why this case is interesting:** The aggregate recipe must reject sources that are not aggregates, but the rejection must be informative — pointing the caller to the correct sister recipe. The source file MUST remain unchanged. This use case anchors what Rejected outputs look like.

**Apply-condition:** `$SOURCE` annotated `@ProcessingGroup` AND zero `@CommandHandler` methods.

##### Detection

The `# Applicable` decision rule, predicate 2:

> Projector / event processor — class annotated `@ProcessingGroup` AND zero `@CommandHandler` methods.

Detected by reading the class header + scanning methods for `@CommandHandler`.

##### Source (left untouched)

```java
package com.dddheroes.heroesofddd.creaturerecruitment.read;

import org.axonframework.config.ProcessingGroup;
import org.axonframework.eventhandling.EventHandler;
import org.springframework.stereotype.Component;

@Component
@ProcessingGroup("ReadModel_Dwelling")
public class DwellingReadModelProjector {

    private final DwellingReadModelRepository repository;

    @EventHandler
    public void on(DwellingBuilt event) {
        repository.save(new DwellingReadModel(event.dwellingId(), event.creatureId()));
    }

    @EventHandler
    public void on(AvailableCreaturesChanged event) {
        repository.findById(event.dwellingId()).ifPresent(rm -> rm.setAvailable(event.changedTo()));
    }
}
```

##### Result block

```
return REJECTED

> **Result:** ⏭️ Rejected
> **Source:** `com.dddheroes.heroesofddd.creaturerecruitment.read.DwellingReadModelProjector`
> **Recipe:** axon4to5-aggregate
>
> **Notes:** Applicable predicate 2 failed at `DwellingReadModelProjector.java:9` — class is annotated `@ProcessingGroup("ReadModel_Dwelling")` with zero `@CommandHandler` methods (`@EventHandler` only). This is a projection / event-handling component, not an aggregate. Route to the `event-processor` recipe — the aggregate recipe does not touch projector sources.
```

##### What did NOT happen

- No edits to the source file. The aggregate recipe ran the `# Applicable` check, predicate 2 returned a definitive "no", and the recipe exited before Research.
- No `# Scope` enumeration, no `# References` reading, no `# Success Criteria` evaluation. Rejected halts the sub-flow at the first diamond in FLOW.md.
- No retry budget consumed (Rejected is not a Failure).

##### Other Rejected predicates

The `# Applicable` decision rule lists six predicates that result in Rejected (or continuation):

1. **Saga** — `@Saga` OR `@SagaEventHandler` / `@StartSaga` / `@EndSaga`. Route to saga recipe.
2. **Projector / event processor** — `@ProcessingGroup` AND zero `@CommandHandler`. Route to event-processor recipe. *(This use case.)*
3. **State-stored aggregate** — `@Aggregate` AND JPA `@Entity` AND zero `@EventSourcingHandler` AND direct field mutation in command handlers. State-stored support is out of scope of this skill.
4. **Event-sourced aggregate, AF4 shape** — `@Aggregate` / `@AggregateRoot` AND ≥1 `@EventSourcingHandler`. **Continue** to Research.
5. **Event-sourced aggregate, partially-migrated** — already on `@EventSourced` / `@EventSourcedEntity` AND ≥1 `@EventSourcingHandler`. **Continue** — the pre-Apply Success Criteria check decides idempotent-Success vs. continue.
6. **None of the above** — Rejected with NOTES naming the failed predicate.

##### Caveats

- **NOTES must name the predicate** that failed, not just "not an aggregate". Without specificity, the caller cannot route to the right next recipe. (Predicate 1 → saga recipe; predicate 2 → event-processor recipe; predicate 3 → no successor — surface as project-level concern.)
- **Source on disk MUST be byte-identical** to the input. The grader uses this as a sanity check that Rejected really did not touch the file (e.g. by asserting `@ProcessingGroup` is still present and `@EventSourced` / `@EventSourcedEntity` / `@EntityCreator` were NOT added).
- **Do not "pre-emptively" migrate any imports** even if a Rejected source happens to have AF4 imports that look migratable. Rejected means "wrong recipe" — the right recipe will own those edits.
- Dual-role classes (BOTH `@QueryHandler` AND `@EventHandler` on the same class — see eval 14 in the legacy set) also fail predicate 2 from this recipe's perspective and are Rejected. The event-processor / query-handler recipes own them.

---

## command gateway

### 01 — Spring REST controller: `send(cmd, metadata)` → `.resultAs(Void.class)`

**Why this case is interesting:** The most common and most surprising migration for REST controllers. AF4's `commandGateway.send(cmd, metadata)` returned `CompletableFuture<Void>` — so returning it from a `CompletableFuture<Void>` controller method compiled fine. In AF5 the same call returns `CommandResult`, which is NOT assignable to `CompletableFuture`. Without the `.resultAs(Void.class)` fix, the migration looks complete (import changed, method signature unchanged) but does not compile.

**Apply-condition:** `$SOURCE` is a Spring `@RestController` AND uses `commandGateway.send(cmd, metadata)` whose result flows into `CompletableFuture<Void>` or `CompletableFuture<R>`.

##### Before (AF4)

```java
package com.example.orders.api;

import com.example.orders.commands.CreateOrderCommand;
import com.example.orders.shared.RequestContext;
import org.axonframework.commandhandling.gateway.CommandGateway;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.concurrent.CompletableFuture;

@RestController
@RequestMapping("/orders")
class OrderRestController {

    private final CommandGateway commandGateway;

    OrderRestController(CommandGateway commandGateway) {
        this.commandGateway = commandGateway;
    }

    @PostMapping
    CompletableFuture<Void> createOrder(
            @RequestHeader("X-User-Id") String userId,
            @RequestBody OrderRequest body
    ) {
        var command = new CreateOrderCommand(body.orderId(), body.product());
        return commandGateway.send(command, RequestContext.with(userId));
    }
}
```

##### After (AF5)

```java
package com.example.orders.api;

import com.example.orders.commands.CreateOrderCommand;
import com.example.orders.shared.RequestContext;
import org.axonframework.messaging.commandhandling.gateway.CommandGateway;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.concurrent.CompletableFuture;

@RestController
@RequestMapping("/orders")
class OrderRestController {

    private final CommandGateway commandGateway;

    OrderRestController(CommandGateway commandGateway) {
        this.commandGateway = commandGateway;
    }

    @PostMapping
    CompletableFuture<Void> createOrder(
            @RequestHeader("X-User-Id") String userId,
            @RequestBody OrderRequest body
    ) {
        var command = new CreateOrderCommand(body.orderId(), body.product());
        return commandGateway.send(command, RequestContext.with(userId))
                             .resultAs(Void.class);
    }
}
```

##### What changed

- `CommandGateway` import: `org.axonframework.commandhandling.gateway.CommandGateway` → `org.axonframework.messaging.commandhandling.gateway.CommandGateway`.
- `return commandGateway.send(command, context)` → appended `.resultAs(Void.class)`.
- Field type, constructor, and parameter name unchanged.

##### Caveats

- **`CommandResult` is NOT `CompletableFuture`** — the AF4 `send(cmd, metadata)` returned `CompletableFuture<Void>` and could be `return`ed directly from a `CompletableFuture<Void>` method. AF5 returns `CommandResult`, so `.resultAs(Void.class)` is required. Forgetting this is the most common silent compile failure.
- **Metadata helper migration is a separate step** — if `RequestContext.with(userId)` (or equivalent) returns AF4 `org.axonframework.messaging.MetaData`, the file will still fail to compile after this recipe's edits. Flag the helper in NOTES as a follow-up; do NOT attempt to migrate it from inside this recipe.
- **`CompletableFuture` import already present** — since the method return type was `CompletableFuture<Void>` in AF4, the import is already there. No new import needed.

---

### 02 — Spring REST controller: `sendAndWait` → preferred async `send(cmd, R.class)`

**Why this case is interesting:** `sendAndWait` still exists in AF5 and can be kept (import-only change). But inside a Spring `@RestController`, blocking the request thread is unnecessary — Spring dispatches `CompletableFuture<R>` method results asynchronously with no behavioural change to the caller. Preferred migration: upgrade the method return type from `R` to `CompletableFuture<R>` and swap to `send(cmd, R.class)`. If the surrounding code cannot accept a future, the fallback is import-only.

**Apply-condition:** `$SOURCE` is a Spring `@RestController` AND uses `commandGateway.sendAndWait(cmd, R.class)` (or `sendAndWait(cmd)`) where the surrounding method can return a `CompletableFuture`.

##### Before (AF4)

```java
package com.example.capacity.api;

import com.example.capacity.commands.ReserveCapacityCommand;
import com.example.capacity.dto.ReservationResult;
import org.axonframework.commandhandling.gateway.CommandGateway;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/capacity")
class CapacityRestController {

    private final CommandGateway commandGateway;

    CapacityRestController(CommandGateway commandGateway) {
        this.commandGateway = commandGateway;
    }

    @PutMapping("/{courseId}")
    ReservationResult reserveCapacity(
            @PathVariable String courseId,
            @RequestParam int seats
    ) {
        return commandGateway.sendAndWait(
                new ReserveCapacityCommand(courseId, seats),
                ReservationResult.class
        );
    }
}
```

##### After (AF5) — preferred: async

```java
package com.example.capacity.api;

import com.example.capacity.commands.ReserveCapacityCommand;
import com.example.capacity.dto.ReservationResult;
import org.axonframework.messaging.commandhandling.gateway.CommandGateway;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.concurrent.CompletableFuture;

@RestController
@RequestMapping("/capacity")
class CapacityRestController {

    private final CommandGateway commandGateway;

    CapacityRestController(CommandGateway commandGateway) {
        this.commandGateway = commandGateway;
    }

    @PutMapping("/{courseId}")
    CompletableFuture<ReservationResult> reserveCapacity(
            @PathVariable String courseId,
            @RequestParam int seats
    ) {
        return commandGateway.send(
                new ReserveCapacityCommand(courseId, seats),
                ReservationResult.class
        );
    }
}
```

##### What changed

- `CommandGateway` import: AF4 package → AF5 package.
- Method return type: `ReservationResult` → `CompletableFuture<ReservationResult>`.
- `sendAndWait(cmd, ReservationResult.class)` → `send(cmd, ReservationResult.class)`.
- `import java.util.concurrent.CompletableFuture;` added.

##### Caveats

- **Fallback (keep blocking):** if the caller requires a synchronous result (e.g. integration test asserting on the return value, or the controller is part of a chain that expects a direct type), keep `sendAndWait(...)` and change only the import. `sendAndWait` still exists in AF5.
- **`send(cmd, R.class)` shorthand** — convenience for `send(cmd).resultAs(R.class)`. Prefer when no metadata is involved.
- **Spring serves `CompletableFuture<R>` async** — same HTTP response, no thread blocking. The HTTP client observes no difference; the server thread is freed immediately.
- **`sendAndWait(cmd, timeout, unit)` overload is GONE in AF5** — if the source uses this three-argument form, rewrite to `send(cmd, R.class).orTimeout(timeout, unit)` (future, preferred) or append `.join()` to preserve blocking (always with a timeout — never bare `.join()` without one).

---

### 03 — Scheduler / runner: `sendAndWait` → import-only

**Why this case is interesting:** `@Scheduled` methods, `CommandLineRunner`, and `ApplicationRunner` callers cannot accept a `CompletableFuture` — they run to completion and return `void`. In AF5 `sendAndWait` still exists and the call site is functionally unchanged. The only required edit is the `CommandGateway` import package swap. This is the simplest migration shape: one import line changes, nothing else.

**Apply-condition:** `$SOURCE` is a `@Scheduled` method or `CommandLineRunner` / `ApplicationRunner` using `commandGateway.sendAndWait(...)` (caller cannot accept a future).

##### Before (AF4)

```java
package com.example.jobs;

import com.example.jobs.commands.ProcessPendingOrdersCommand;
import org.axonframework.commandhandling.gateway.CommandGateway;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
class ScheduledOrderProcessor {

    private final CommandGateway commandGateway;

    ScheduledOrderProcessor(CommandGateway commandGateway) {
        this.commandGateway = commandGateway;
    }

    @Scheduled(fixedDelay = 60_000)
    void processOrders() {
        commandGateway.sendAndWait(new ProcessPendingOrdersCommand());
    }
}
```

##### After (AF5)

```java
package com.example.jobs;

import com.example.jobs.commands.ProcessPendingOrdersCommand;
import org.axonframework.messaging.commandhandling.gateway.CommandGateway;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
class ScheduledOrderProcessor {

    private final CommandGateway commandGateway;

    ScheduledOrderProcessor(CommandGateway commandGateway) {
        this.commandGateway = commandGateway;
    }

    @Scheduled(fixedDelay = 60_000)
    void processOrders() {
        commandGateway.sendAndWait(new ProcessPendingOrdersCommand());
    }
}
```

##### What changed

- `CommandGateway` import: `org.axonframework.commandhandling.gateway.CommandGateway` → `org.axonframework.messaging.commandhandling.gateway.CommandGateway`.
- Everything else unchanged — `sendAndWait`, field, constructor, method body.

##### Caveats

- **Do NOT introduce `CompletableFuture` here** — `@Scheduled void` methods must not return a future. If you force `send(cmd, Void.class)` and block via `.join()`, you introduce a blocking call on the scheduler thread that may exceed the fixed-delay period. Keep `sendAndWait`.
- **Same applies to `CommandLineRunner.run(...)` and `ApplicationRunner.run(...)`** — callers that run to completion and return `void`; prefer `sendAndWait`.
- **`sendAndWait(cmd, timeout, unit)` is gone in AF5** — if the source uses the three-argument form, rewrite to `send(cmd, Void.class).orTimeout(timeout, unit).join()` to preserve the blocking + timeout semantic (always with a timeout — never bare `.join()`).

---

### 04 — Inline `CommandCallback` lambda → `.onSuccess(...).onError(...)`

**Why this case is interesting:** AF4's `CommandGateway.send(cmd, CommandCallback)` accepted a callback for async success/failure handling. The `CommandCallback` SPI is removed in AF5. Inline lambdas passed at call sites can be mechanically rewritten to the `CommandResult` fluent chain (`.onSuccess(...).onError(...)`). Classes that fully implement `CommandCallback` as a separate type are Blocker B1 and cannot be handled here.

**Apply-condition:** `$SOURCE` passes an inline lambda or anonymous class as `CommandCallback` argument to `commandGateway.send(cmd, callback)` at one or more call sites.

##### Before (AF4)

```java
package com.example.notifications.api;

import com.example.notifications.commands.SendNotificationCommand;
import org.axonframework.commandhandling.CommandCallback;
import org.axonframework.commandhandling.CommandMessage;
import org.axonframework.commandhandling.CommandResultMessage;
import org.axonframework.commandhandling.gateway.CommandGateway;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/notifications")
class NotificationController {

    private final CommandGateway commandGateway;

    NotificationController(CommandGateway commandGateway) {
        this.commandGateway = commandGateway;
    }

    @PostMapping("/{recipientId}")
    void notify(@PathVariable String recipientId) {
        commandGateway.send(
                new SendNotificationCommand(recipientId),
                (CommandCallback<SendNotificationCommand, Void>) (msg, result) -> {
                    if (result.isExceptional()) {
                        System.err.println("Failed: " + result.exceptionResult().getMessage());
                    } else {
                        System.out.println("Sent to " + recipientId);
                    }
                }
        );
    }
}
```

##### After (AF5)

```java
package com.example.notifications.api;

import com.example.notifications.commands.SendNotificationCommand;
import org.axonframework.messaging.commandhandling.gateway.CommandGateway;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/notifications")
class NotificationController {

    private final CommandGateway commandGateway;

    NotificationController(CommandGateway commandGateway) {
        this.commandGateway = commandGateway;
    }

    @PostMapping("/{recipientId}")
    void notify(@PathVariable String recipientId) {
        commandGateway.send(new SendNotificationCommand(recipientId))
                      .onSuccess(result -> System.out.println("Sent to " + recipientId))
                      .onError(error -> System.err.println("Failed: " + error.getMessage()));
    }
}
```

##### What changed

- `CommandGateway` import: AF4 package → AF5 package.
- `CommandCallback`, `CommandMessage`, `CommandResultMessage` imports removed (SPI gone).
- `send(cmd, callback)` → `send(cmd).onSuccess(...).onError(...)`.
- The inline lambda's two-arg form `(msg, result) -> { if (result.isExceptional()) ... }` split into two single-arg lambdas.

##### Caveats

- **Preserve error semantics.** The AF4 callback's `isExceptional()` path maps to `onError(Throwable error -> ...)`. Do NOT silently drop the error branch — that is a behavioural regression.
- **`onSuccess` and `onError` are terminal** — `CommandResult` fluent chain. `onSuccess(...)` receives the typed result (or `null` for `Void`); `onError(...)` receives the `Throwable`. Both return `CommandResult` so they can be chained.
- **Blocker B1 boundary** — if the class itself `implements CommandCallback` rather than passing a lambda, stop and emit Blocker B1. The error semantics and design intent of the full implementation are outside what the recipe can safely infer.
- **`void` method stays `void`** — since the call result is consumed via the fluent chain, the surrounding method return type does not need to change unless the caller wants to compose on the result.

---

### 05 — Rejected: handler class with `CommandGateway` field

**Why this case is interesting:** A class that injects `CommandGateway` as a field AND has handler annotations (`@EventHandler`, `@CommandHandler`, etc.) looks like a target for this recipe at first glance — it imports `CommandGateway`. But the presence of handler annotations makes it an event-handling component, NOT a top-of-chain caller. The command-gateway recipe must reject it and route to the event-processor recipe (which owns Step 4: `CommandGateway` → `CommandDispatcher` inside a handler).

**Apply-condition:** `$SOURCE` has any method annotated `@EventHandler` / `@CommandHandler` / `@QueryHandler` / `@SagaEventHandler` / `@MessageHandlerInterceptor` (predicate 2 fires).

##### Example (AF4 source — NOT touched by this recipe)

```java
package com.example.automation;

import com.example.events.OrderPlacedEvent;
import com.example.commands.ReserveInventoryCommand;
import org.axonframework.commandhandling.gateway.CommandGateway;
import org.axonframework.config.ProcessingGroup;
import org.axonframework.eventhandling.EventHandler;
import org.springframework.stereotype.Component;

@Component
@ProcessingGroup("Automation_OrderInventory")
class WhenOrderPlacedReserveInventoryProcessor {

    private final CommandGateway commandGateway;  // <-- has CommandGateway

    WhenOrderPlacedReserveInventoryProcessor(CommandGateway commandGateway) {
        this.commandGateway = commandGateway;
    }

    @EventHandler   // <-- this triggers Applicable predicate 2
    public void on(OrderPlacedEvent event) {
        commandGateway.sendAndWait(new ReserveInventoryCommand(event.orderId()));
    }
}
```

##### Expected result

The command-gateway recipe returns Rejected immediately. The source is untouched.

```
return REJECTED

> **Result:** ⏭️ Rejected
> **Source:** `com.example.automation.WhenOrderPlacedReserveInventoryProcessor`
> **Recipe:** axon4to5-command-gateway
>
> **Notes:** Applicable predicate 2 failed — class has `@EventHandler` methods. This is an event-handling component, not a top-of-chain caller. Route to the event-processor recipe; it owns in-handler command dispatch via `CommandDispatcher` (Step 4).
```

##### What changed

Nothing — the recipe did not touch the file.

##### Caveats

- **The event-processor recipe (Step 4) owns this migration**, not the command-gateway recipe. The correct migration for in-handler dispatch is: remove the `CommandGateway` field + add `CommandDispatcher commandDispatcher` as a method parameter.
- **Do NOT apply command-gateway toolbox steps to the `CommandGateway` import in this class.** If you swap the import to AF5 `CommandGateway` and leave the field, the event-processor recipe will find an inconsistent state and emit a Learning. Leave the class fully untouched.
- **Mixed class (some methods are handlers, some are genuinely top-of-chain)**: in practice, this shape is rare. If encountered, run the handler recipe first; the command-gateway recipe can touch the non-handler methods on follow-up.

---

## event handlers

### 01 — Pure projector (Spring)

**Why this case is interesting:** Baseline of the event-processor recipe. `@EventHandler`-only class with no `CommandGateway` injection — common read-model projection. Tests the four "always" steps (Namespace swap, annotation import moves, metadata accessor rename) and proves the recipe skips command-dispatch steps when not needed. Class-level `@Component` (Spring stereotype) is preserved.

**Apply-condition:** `configuration=spring` AND `$SOURCE` has only `@EventHandler` / `@ResetHandler` methods (no `CommandGateway` field, no in-handler dispatch).

##### Before (AF4)

```java
package com.dddheroes.heroesofddd.creaturerecruitment.read;

import com.dddheroes.heroesofddd.creaturerecruitment.events.AvailableCreaturesChanged;
import com.dddheroes.heroesofddd.creaturerecruitment.events.DwellingBuilt;
import com.dddheroes.heroesofddd.shared.metadata.GameMetaData;
import org.axonframework.config.ProcessingGroup;
import org.axonframework.eventhandling.EventHandler;
import org.axonframework.eventhandling.ResetHandler;
import org.axonframework.messaging.annotation.MetaDataValue;
import org.springframework.stereotype.Component;

@Component
@ProcessingGroup("ReadModel_Dwelling")
public class DwellingReadModelProjector {

    private final DwellingReadModelRepository repository;

    public DwellingReadModelProjector(DwellingReadModelRepository repository) {
        this.repository = repository;
    }

    @EventHandler
    public void on(DwellingBuilt event, @MetaDataValue(GameMetaData.GAME_ID_KEY) String gameId) {
        repository.save(new DwellingReadModel(gameId, event.dwellingId(), event.creatureId()));
    }

    @EventHandler
    public void on(AvailableCreaturesChanged event,
                   @MetaDataValue(GameMetaData.GAME_ID_KEY) String gameId) {
        repository.findById(new DwellingReadModelId(gameId, event.dwellingId()))
                  .ifPresent(rm -> rm.setAvailable(event.changedTo()));
    }

    @ResetHandler
    public void onReset() {
        repository.deleteAll();
    }
}
```

##### After (AF5)

```java
package com.dddheroes.heroesofddd.creaturerecruitment.read;

import com.dddheroes.heroesofddd.creaturerecruitment.events.AvailableCreaturesChanged;
import com.dddheroes.heroesofddd.creaturerecruitment.events.DwellingBuilt;
import com.dddheroes.heroesofddd.shared.metadata.GameMetaData;
import org.axonframework.messaging.core.annotation.MetadataValue;
import org.axonframework.messaging.core.annotation.Namespace;
import org.axonframework.messaging.core.annotation.SequencingPolicy;
import org.axonframework.messaging.core.sequencing.MetadataSequencingPolicy;
import org.axonframework.messaging.eventhandling.annotation.EventHandler;
import org.axonframework.messaging.eventhandling.replay.annotation.ResetHandler;
import org.springframework.stereotype.Component;

@Component
@Namespace("ReadModel_Dwelling")
@SequencingPolicy(type = MetadataSequencingPolicy.class, parameters = GameMetaData.GAME_ID_KEY)
public class DwellingReadModelProjector {

    private final DwellingReadModelRepository repository;

    public DwellingReadModelProjector(DwellingReadModelRepository repository) {
        this.repository = repository;
    }

    @EventHandler
    public void on(DwellingBuilt event, @MetadataValue(GameMetaData.GAME_ID_KEY) String gameId) {
        repository.save(new DwellingReadModel(gameId, event.dwellingId(), event.creatureId()));
    }

    @EventHandler
    public void on(AvailableCreaturesChanged event,
                   @MetadataValue(GameMetaData.GAME_ID_KEY) String gameId) {
        repository.findById(new DwellingReadModelId(gameId, event.dwellingId()))
                  .ifPresent(rm -> rm.setAvailable(event.changedTo()));
    }

    @ResetHandler
    public void onReset() {
        repository.deleteAll();
    }
}
```

##### What changed

- `@ProcessingGroup("ReadModel_Dwelling")` → `@Namespace("ReadModel_Dwelling")` (string preserved exactly).
- Import swap: `org.axonframework.config.ProcessingGroup` → `org.axonframework.messaging.core.annotation.Namespace`.
- `@EventHandler` import: `org.axonframework.eventhandling.EventHandler` → `org.axonframework.messaging.eventhandling.annotation.EventHandler`.
- `@ResetHandler` import: `org.axonframework.eventhandling.ResetHandler` → `org.axonframework.messaging.eventhandling.replay.annotation.ResetHandler`.
- `@MetaDataValue` (capital `D`) → `@MetadataValue` (capital `M`, lowercase `d`) at `org.axonframework.messaging.core.annotation.MetadataValue`. Case-sensitive — the annotation symbol AND the import package change.
- `@SequencingPolicy(type = MetadataSequencingPolicy.class, parameters = GameMetaData.GAME_ID_KEY)` added at class level because the AF4 project had a `@Bean SequencingPolicy gameIdSequencingPolicy` keyed on the same metadata key. See use-case 03 for the YAML / @Bean → annotation move.
- `@Component` preserved (Spring stereotype, not Axon).
- Constructor + field injection of `DwellingReadModelRepository` preserved — no in-handler command dispatch, so no `CommandDispatcher` parameter is introduced.

##### Caveats

- **`@Namespace` string IS the binding contract.** Match the AF4 `@ProcessingGroup` value exactly. Mismatch silently drops events at runtime; there is no compile signal.
- **`@MetaDataValue` (AF4) vs `@MetadataValue` (AF5)** — typos compile cleanly and the parameter silently receives `null`. Grep for the AF4 form after the rewrite to confirm zero remain.
- **`@SequencingPolicy` annotation is recipe-derived**, not present in the AF4 source. The recipe adds it only when the AF4 wiring referenced a custom policy for this processing group (Step 6). For projectors without a sequencing policy, omit it.
- **Do NOT introduce `CommandDispatcher` here.** Pure projectors do not dispatch commands; threading the dispatcher parameter is wasted ceremony AND surfaces a stale code-smell for reviewers.

---

### 02 — Projector with in-handler command dispatch (CommandGateway → CommandDispatcher)

**Why this case is interesting:** "Automation" / process-manager-style projectors that observe events and dispatch commands. AF4 injected `CommandGateway` as a field and called `sendAndWait(...)` in the handler body. AF5 moves the gateway to a method parameter (`CommandDispatcher`), and `sendAndWait` is gone — the future from `send(...).getResultMessage()` surfaces failure off-thread. Try/catch compensation paths become `.exceptionallyCompose(...)`. The handler return type changes from `void` to `CompletableFuture<?>`.

**Apply-condition:** `$SOURCE` injects a `CommandGateway` field AND dispatches commands in `@EventHandler` bodies.

##### Before (AF4)

```java
package com.dddheroes.heroesofddd.automation;

import com.dddheroes.heroesofddd.creaturerecruitment.events.CreatureRecruited;
import com.dddheroes.heroesofddd.armies.write.addcreature.AddCreatureToArmy;
import com.dddheroes.heroesofddd.creaturerecruitment.write.changeavailablecreatures.IncreaseAvailableCreatures;
import com.dddheroes.heroesofddd.shared.metadata.GameMetaData;
import org.axonframework.commandhandling.gateway.CommandGateway;
import org.axonframework.config.ProcessingGroup;
import org.axonframework.eventhandling.DisallowReplay;
import org.axonframework.eventhandling.EventHandler;
import org.axonframework.messaging.MetaData;
import org.axonframework.messaging.annotation.MetaDataValue;
import org.springframework.stereotype.Component;

@Component
@ProcessingGroup("Automation_WhenCreatureRecruitedThenAddToArmy_Processor")
@DisallowReplay
public class WhenCreatureRecruitedThenAddToArmyProcessor {

    private final CommandGateway commandGateway;

    public WhenCreatureRecruitedThenAddToArmyProcessor(CommandGateway commandGateway) {
        this.commandGateway = commandGateway;
    }

    @EventHandler
    public void on(CreatureRecruited event,
                   @MetaDataValue(GameMetaData.GAME_ID_KEY) String gameId) {
        MetaData metadata = GameMetaData.with(gameId);
        try {
            commandGateway.sendAndWait(
                AddCreatureToArmy.command(
                    event.toArmy(), event.creatureId(), event.quantity()
                ),
                metadata
            );
        } catch (Exception failure) {
            // compensation — increase availability back
            commandGateway.sendAndWait(
                IncreaseAvailableCreatures.command(
                    event.dwellingId(), event.creatureId(), event.quantity()
                ),
                metadata
            );
        }
    }
}
```

##### After (AF5)

```java
package com.dddheroes.heroesofddd.automation;

import com.dddheroes.heroesofddd.creaturerecruitment.events.CreatureRecruited;
import com.dddheroes.heroesofddd.armies.write.addcreature.AddCreatureToArmy;
import com.dddheroes.heroesofddd.creaturerecruitment.write.changeavailablecreatures.IncreaseAvailableCreatures;
import com.dddheroes.heroesofddd.shared.metadata.GameMetaData;
import org.axonframework.messaging.commandhandling.gateway.CommandDispatcher;
import org.axonframework.messaging.core.Message;
import org.axonframework.messaging.core.MetaData;
import org.axonframework.messaging.core.annotation.MetadataValue;
import org.axonframework.messaging.core.annotation.Namespace;
import org.axonframework.messaging.core.sequencing.MetadataSequencingPolicy;
import org.axonframework.messaging.core.annotation.SequencingPolicy;
import org.axonframework.messaging.eventhandling.annotation.EventHandler;
import org.axonframework.messaging.eventhandling.replay.annotation.DisallowReplay;
import org.springframework.stereotype.Component;

import java.util.concurrent.CompletableFuture;

@Component
@Namespace("Automation_WhenCreatureRecruitedThenAddToArmy_Processor")
@DisallowReplay
@SequencingPolicy(type = MetadataSequencingPolicy.class, parameters = GameMetaData.GAME_ID_KEY)
public class WhenCreatureRecruitedThenAddToArmyProcessor {

    @EventHandler
    public CompletableFuture<? extends Message> on(CreatureRecruited event,
                                                   @MetadataValue(GameMetaData.GAME_ID_KEY) String gameId,
                                                   CommandDispatcher commandDispatcher) {
        MetaData metadata = GameMetaData.with(gameId);
        return commandDispatcher.send(
                AddCreatureToArmy.command(
                    event.toArmy(), event.creatureId(), event.quantity()
                ),
                metadata
            )
            .getResultMessage()
            .thenApply(m -> (Message) m)
            .exceptionallyCompose(failure ->
                commandDispatcher.send(
                        IncreaseAvailableCreatures.command(
                            event.dwellingId(), event.creatureId(), event.quantity()
                        ),
                        metadata
                    )
                    .getResultMessage()
                    .thenApply(m -> m)
            );
    }
}
```

##### What changed

- `@ProcessingGroup` → `@Namespace` (string preserved).
- `@SequencingPolicy(type = MetadataSequencingPolicy.class, parameters = GameMetaData.GAME_ID_KEY)` added at class level (AF4 had a `@Bean SequencingPolicy gameIdSequencingPolicy` referenced via `EventProcessingConfigurer.assignSequencingPolicy(...)` for this group — see use-case 03).
- `@DisallowReplay` import: `org.axonframework.eventhandling.DisallowReplay` → `org.axonframework.messaging.eventhandling.replay.annotation.DisallowReplay`.
- `@EventHandler` import to AF5 location.
- `@MetaDataValue` → `@MetadataValue` (capital-D loss + package change).
- **Class-level `CommandGateway` field removed.** Constructor injection removed too — the class has no remaining dependencies in this example, so the explicit constructor is also gone.
- Handler method signature gains `CommandDispatcher commandDispatcher` as the **last** parameter. AF5 binds it to the active `ProcessingContext` automatically.
- Handler return type: `void` → `CompletableFuture<? extends Message>`. AF5 `Message` is NON-generic — `CompletableFuture<? extends Message<?>>` (with the `<?>`) does NOT compile.
- `sendAndWait(...)` → `send(...).getResultMessage()` — returns `CompletableFuture<? extends Message>`. The AF4 blocking semantics are replaced with the async chain.
- Try/catch compensation → `.exceptionallyCompose(failure -> commandDispatcher.send(<compensation>).getResultMessage())`. The `.thenApply(m -> m)` bridge widens the wildcard capture so the future type lines up with what `exceptionallyCompose` expects.

##### Caveats

- **`sendAndWait` is not just an API rename.** The AF4 form blocked + threw on failure. The AF5 form returns a `CompletableFuture` and the failure surfaces on the future, NOT in the try-block. AF4 try/catch around `sendAndWait` silently stops compensating under AF5 if you "just remove the await" — that is a real behavioural regression. Always rewrite compensation to `.exceptionallyCompose(...)`.
- **AF5 `Message` is non-generic.** Declared as `public interface Message` (no type parameter). Anything that writes `Message<?>` in the wildcard position fails to compile against AF5. The correct shape is `CompletableFuture<? extends Message>`.
- **`.thenApply(m -> m)` bridge** is often needed before `.exceptionallyCompose(...)` to widen `CompletableFuture<? extends Message>` to `CompletableFuture<Message>` (wildcard capture refuses `exceptionallyCompose`'s type bound otherwise).
- **`CommandDispatcher` is bound to `ProcessingContext`**, NOT to a bean lifecycle. Do not keep a class-level field side-by-side with the parameter — that mixes two dispatch paths and confuses readers.
- **Helper methods that build metadata (e.g. `GameMetaData.with(gameId)`) often return AF4 `org.axonframework.messaging.MetaData`.** If they don't get migrated to AF5 `org.axonframework.messaging.core.MetaData`, command dispatch fails at runtime (type-check passes due to similarity). Flag in Result NOTES; the helper migration is outside the strict event-processor recipe scope.
- **`@DisallowReplay` semantics unchanged** — it still means "skip this handler during a reset/replay". Only the import location moves.

---

### 03 — YAML + `@Bean SequencingPolicy` → class-level `@SequencingPolicy`

**Why this case is interesting:** AF4 projects expressed per-processor sequencing two ways: either as a YAML key under `axon.eventhandling.processors.<group>.sequencing-policy` OR as a `@Bean SequencingPolicy <group>SequencingPolicy` referenced by `EventProcessingConfigurer.assignSequencingPolicy(...)`. AF5 collapses both forms into a class-level `@SequencingPolicy` annotation on the projector itself. The recipe must:

- Add `@SequencingPolicy` at the class level (Step 6).
- Delete the YAML key for `$SOURCE`'s group (Step 8).
- Leave the `@Bean SequencingPolicy` definition in place if other processors share it (do NOT delete; flag as potential orphan in Result NOTES).

**Apply-condition:** `application.yaml` declares `axon.eventhandling.processors.<group>.sequencing-policy` for `$SOURCE`'s group OR a `@Bean SequencingPolicy` is registered via `EventProcessingConfigurer.assignSequencingPolicy(...)`.

##### Before (AF4)

`application.yaml`:

```yaml
axon:
  serializer:
    events: jackson
  eventhandling:
    processors:
      ReadModel_Dwelling:
        mode: tracking
        sequencing-policy: gameIdSequencingPolicy
      Automation_WhenCreatureRecruitedThenAddToArmy_Processor:
        mode: pooled
        sequencing-policy: gameIdSequencingPolicy
        thread-count: 8
```

`GameConfiguration.java`:

```java
import org.axonframework.eventhandling.async.SequencingPolicy;
import org.axonframework.eventhandling.EventMessage;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class GameConfiguration {

    @Bean
    public SequencingPolicy<EventMessage<?>> gameIdSequencingPolicy() {
        return event -> event.getMetaData().get(GameMetaData.GAME_ID_KEY);
    }
}
```

`DwellingReadModelProjector.java` (relevant header — full body in use-case 01):

```java
@Component
@ProcessingGroup("ReadModel_Dwelling")
public class DwellingReadModelProjector { … }
```

##### After (AF5)

`application.yaml`:

```yaml
axon:
  converter:
    events: jackson
  eventhandling:
    processors:
      ReadModel_Dwelling:
        mode: pooled
      Automation_WhenCreatureRecruitedThenAddToArmy_Processor:
        mode: pooled
        thread-count: 8
```

`GameConfiguration.java` — kept as-is for now (the bean is shared across two processors). After all dependent processors are migrated, the bean becomes orphan; the recipe surfaces that in Result NOTES but does NOT delete the bean (out of scope).

`DwellingReadModelProjector.java`:

```java
@Component
@Namespace("ReadModel_Dwelling")
@SequencingPolicy(type = MetadataSequencingPolicy.class, parameters = GameMetaData.GAME_ID_KEY)
public class DwellingReadModelProjector { … }
```

##### What changed

- **YAML**:
  - `axon.eventhandling.processors.ReadModel_Dwelling.sequencing-policy: gameIdSequencingPolicy` — DELETED. The information now lives on the class.
  - `axon.eventhandling.processors.ReadModel_Dwelling.mode: tracking` → `mode: pooled`. AF5 has no `TrackingEventProcessor`; `PooledStreamingEventProcessor` is the direct replacement.
  - `axon.serializer.*` → `axon.converter.*` (only the slice in scope — full conversion is the serializer recipe's job; surface as a Learning).
- **Class annotation**: `@SequencingPolicy(type = MetadataSequencingPolicy.class, parameters = GameMetaData.GAME_ID_KEY)` added at class level. `MetadataSequencingPolicy` is a built-in AF5 policy that reads a single metadata key — semantically equivalent to the AF4 `event -> event.getMetaData().get(GameMetaData.GAME_ID_KEY)` lambda.
- **`@Bean` definition**: left in place. `gameIdSequencingPolicy` is referenced by TWO processors in this example; the recipe migrates ONLY `$SOURCE`'s reference. The bean becomes orphan only when BOTH processors have been migrated to class-level annotations — that detection (and the bean deletion) is the orchestrator's concern, not this recipe's.

##### Built-in `SequencingPolicy` types

| AF5 policy class | Behaviour | AF4 equivalent |
|---|---|---|
| `MetadataSequencingPolicy` | Sequence by a single metadata key (`parameters = "<key>"`). | `event -> event.getMetaData().get("<key>")` lambda. |
| `SequentialPerAggregatePolicy` | One sequence per aggregate id. **AF4 default**. | `SequentialPerAggregatePolicy.INSTANCE`. |
| `SequentialPolicy` | All events strictly sequential. **AF5/DCB default**. | `SequentialPolicy.INSTANCE`. |
| `FullConcurrencyPolicy` | No sequencing — handlers can run in parallel for any event. | `FullConcurrencyPolicy.INSTANCE`. |

For these four, the recipe just emits `@SequencingPolicy(type = <PolicyClass>.class[, parameters = "<key>"])`. No body migration needed.

For **custom policies** (a project-specific class implementing `SequencingPolicy<EventMessage<?>>`), see use-case 06.

##### Caveats

- **`mode: tracking` → `mode: pooled` is mandatory** for any YAML processor entry; `TrackingEventProcessor` is gone in AF5. Subscribing processors stay `mode: subscribing`.
- **Do NOT delete the `@Bean SequencingPolicy` definition unless EVERY referencing processor has been migrated.** Premature deletion breaks the other processors at startup. Flag in Result NOTES that it MAY become orphan once the migration is complete.
- **`MetadataSequencingPolicy` parameter is a String key**, not a `Function<EventMessage, Object>`. If the AF4 lambda did anything more complex than a single metadata read (e.g. `event.getMetaData().get("game-id") + ":" + event.getPayload().tenantId()`), the policy is **custom** and use-case 06 applies — `MetadataSequencingPolicy` will not preserve the behaviour.
- **`axon.serializer.*` rename has wider blast radius.** This recipe rewrites only the slice in scope. The full project-wide rename (`axon.serializer.events: jackson` plus every Java/Spring reference to `Serializer` beans) belongs to the serializer recipe; surface as a Learning if the YAML has more `axon.serializer.*` keys than this recipe touches.
- **Processor renames create silent failures.** Do not rename the processing-group string while doing the sequencing-policy move — the `@Namespace` value, the YAML key, the `EventProcessorDefinition.pooledStreaming(...)` argument, and any `EventProcessingConfigurer.assignHandlerTypesMatching(...)` must all remain the same string.

---

### 04 — Spring processor wiring: `EventProcessorDefinition` (Path A)

**Why this case is interesting:** AF5 Spring projects replace the AF4 `@Bean ConfigurerModule` that called `EventProcessingConfigurer.registerPooledStreamingEventProcessor(...)` with a single `@Bean EventProcessorDefinition`. The new bean owns the processor type (`pooledStreaming` or `subscribing`), handler matching, and customisation in one fluent builder. The AF4 `EventProcessingConfigurer` API is gone — keeping it side-by-side causes startup failures.

**Apply-condition:** `configuration=spring` AND the project's `@Configuration` class registers `$SOURCE`'s processor via the AF4 `EventProcessingConfigurer` API (`registerPooledStreamingEventProcessor(...)` / `registerSubscribingEventProcessor(...)` / `assignHandlerTypesMatching(...)`).

##### Before (AF4)

```java
import org.axonframework.config.ConfigurerModule;
import org.axonframework.config.EventProcessingConfigurer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class AxonConfig {

    @Bean
    public ConfigurerModule configureProjectors() {
        return configurer -> {
            EventProcessingConfigurer processing = configurer.eventProcessing();
            processing.registerPooledStreamingEventProcessor(
                          "ReadModel_Dwelling",
                          org.axonframework.config.Configuration::eventStore,
                          (config, builder) -> builder.initialSegmentCount(8)
                                                      .batchSize(100)
                      )
                      .assignHandlerTypesMatching(
                          "ReadModel_Dwelling",
                          type -> type.getPackageName()
                                      .startsWith("com.dddheroes.heroesofddd.creaturerecruitment.read")
                      );
        };
    }
}
```

##### After (AF5)

```java
import org.axonframework.extension.spring.config.EventProcessorDefinition;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class AxonConfig {

    @Bean
    public EventProcessorDefinition readModelDwellingProcessor() {
        return EventProcessorDefinition
                .pooledStreaming("ReadModel_Dwelling")
                .assigningHandlers(descriptor -> descriptor.beanType().getPackageName()
                                                .startsWith("com.dddheroes.heroesofddd.creaturerecruitment.read"))
                .customized(config -> config.initialSegmentCount(8).batchSize(100));
    }
}
```

For subscribing processors, swap `.pooledStreaming(...)` for `.subscribing(...)`:

```java
@Bean
public EventProcessorDefinition someSubscribingProcessor() {
    return EventProcessorDefinition.subscribing("SomeGroup")
                                   .assigningHandlers(descriptor -> /* … */);
}
```

##### What changed

- AF4 `@Bean ConfigurerModule` returning a `Configurer` lambda → AF5 `@Bean EventProcessorDefinition` returning a fluent builder.
- Import: `org.axonframework.config.ConfigurerModule` and `org.axonframework.config.EventProcessingConfigurer` removed; `org.axonframework.extension.spring.config.EventProcessorDefinition` added. The `.extension.spring.config.` package is mandatory — the bean is Spring-Boot-specific.
- `registerPooledStreamingEventProcessor(name, eventStoreSupplier, customizer)` → `.pooledStreaming(name).customized(customizer)`. The event-store wiring is inferred from the configurer; no manual `eventStore` reference needed.
- `assignHandlerTypesMatching(name, predicate)` → `.assigningHandlers(descriptor -> predicate)`. The predicate's argument is now a `HandlerDescriptor` exposing `beanType()`, not a raw `Class<?>` — call `descriptor.beanType().getPackageName()` etc.
- The customisation closure signature changes too: AF4 `(config, builder) -> builder.initialSegmentCount(8)` → AF5 `config -> config.initialSegmentCount(8)`. The new closure is a single-arg setter chain on the `EventProcessorSettings` builder.

##### Coexistence with YAML

`EventProcessorDefinition` `@Bean` and YAML properties are both valid AF5 inputs. The `@Bean` takes precedence when both define the same processor, but YAML can still set knobs the bean doesn't override:

```yaml
#### application.yaml — drives the same processor's defaults
axon:
  eventhandling:
    processors:
      ReadModel_Dwelling:
        mode: pooled
        thread-count: 8
```

The `@Bean` here adds handler-matching + `initialSegmentCount` / `batchSize`, the YAML sets `thread-count`. Result is the union, with `@Bean` winning on overlap. Choose ONE source of truth per processor in real projects — mixing is OK during migration but should be cleaned up.

##### Caveats

- **Mixed AF4 + AF5 wiring fails at startup.** Spring picks up the AF5 `@Bean EventProcessorDefinition` first; a stale `@Bean ConfigurerModule` that still references `EventProcessingConfigurer.registerPooledStreamingEventProcessor(...)` either fails (no such method on the AF5 `Configurer`) or is silently shadowed. Delete the AF4 wiring in the same commit.
- **`subscribing` processors are NOT the default.** AF4's default was `Tracking`; AF5's default is `pooledStreaming`. Use `subscribing` only when the AF4 source explicitly registered a subscribing processor.
- **Handler-matching closure differs.** The AF4 form took a `Class<?>` predicate; the AF5 form takes a `HandlerDescriptor`. Existing predicates that called `type.getPackageName()` work by going through `descriptor.beanType().getPackageName()`. Predicates that called more advanced reflection (e.g. `type.getDeclaredMethods()`) need re-thinking.
- **`EventProcessorDefinition.subscribing(...)`** exists for completeness but is rarely used in greenfield AF5 — most projects move to `pooledStreaming` for the throughput / resume semantics.
- **DO NOT use `MessagingConfigurer.eventProcessing(...)` in a Spring app.** That fluent block is the native (Path B) equivalent — see use-case 05. Spring projects always use `@Bean EventProcessorDefinition`.

---

### 05 — Native processor wiring: `MessagingConfigurer.eventProcessing(...)` (Path B)

**Why this case is interesting:** Non-Spring projects used the AF4 `EventProcessingConfigurer` / `EventProcessingModule` API. AF5 routes everything through `MessagingConfigurer.eventProcessing(...)` — a fluent block that takes processor type, name, and a module-level configuration in one shot. The old `EventProcessingConfigurer` interface is gone.

**Apply-condition:** `configuration=native` AND the project's Configurer block calls `configurer.eventProcessing().registerPooledStreamingEventProcessor(...)` (or `registerSubscribingEventProcessor(...)`).

##### Before (AF4)

```java
import org.axonframework.config.Configurer;
import org.axonframework.config.DefaultConfigurer;
import org.axonframework.config.EventProcessingConfigurer;

public class Bootstrap {

    public static void main(String[] args) {
        Configurer configurer = DefaultConfigurer.defaultConfiguration();

        configurer.eventProcessing()
                  .registerPooledStreamingEventProcessor(
                          "ReadModel_Dwelling",
                          org.axonframework.config.Configuration::eventStore,
                          (config, builder) -> builder.initialSegmentCount(8).batchSize(100)
                  )
                  .assignHandlerTypesMatching(
                          "ReadModel_Dwelling",
                          type -> type.getPackageName().startsWith("com.dddheroes.heroesofddd.creaturerecruitment.read")
                  )
                  .registerEventHandler(c -> new DwellingReadModelProjector(c.getComponent(DwellingReadModelRepository.class)));

        configurer.buildConfiguration().start();
    }
}
```

##### After (AF5)

```java
import org.axonframework.eventsourcing.configuration.EventSourcingConfigurer;
import org.axonframework.messaging.configuration.MessagingConfigurer;

public class Bootstrap {

    public static void main(String[] args) {
        EventSourcingConfigurer eventSourcing = EventSourcingConfigurer.create();

        eventSourcing.messaging(messaging ->
            messaging.eventProcessing(eventProcessing ->
                eventProcessing.pooledStreaming(pooledStreaming ->
                    pooledStreaming.processor("ReadModel_Dwelling", module ->
                        module.eventHandlingComponents(components ->
                                  components.autodetected(cfg ->
                                      new DwellingReadModelProjector(
                                          cfg.getComponent(DwellingReadModelRepository.class)
                                      )
                                  )
                              )
                              .customized((cfg, conf) -> conf.batchSize(100).initialSegmentCount(8))
                    )
                )
            )
        );

        eventSourcing.start();
    }
}
```

For subscribing processors, swap `.pooledStreaming(...)` for `.subscribing(...)`:

```java
eventProcessing.subscribing(subscribing ->
    subscribing.processor("SomeGroup", module ->
        module.eventHandlingComponents(...)
              .notCustomized()
    )
)
```

##### What changed

- **Top-level configurer**: AF4 `DefaultConfigurer.defaultConfiguration()` returning a `Configurer` → AF5 `EventSourcingConfigurer.create()` (event-sourcing-aware) or `MessagingConfigurer.create()` (messaging-only). The build/start lifecycle moves from `configurer.buildConfiguration().start()` to `configurer.start()` directly.
- **Event-processing entry point**: AF4 `configurer.eventProcessing()` returning an `EventProcessingConfigurer` → AF5 `.messaging(m -> m.eventProcessing(ep -> ...))` taking a fluent consumer.
- **Processor registration**: AF4 `.registerPooledStreamingEventProcessor(name, eventStoreSupplier, customizer)` → AF5 `.pooledStreaming(ps -> ps.processor(name, module -> ...))`. The event-store wiring is implicit; no manual `eventStore` supplier needed.
- **Handler registration**: AF4 `.registerEventHandler(cfg -> new MyProjector(cfg.getComponent(Repo.class)))` plus a separate `.assignHandlerTypesMatching(...)` → AF5 `module.eventHandlingComponents(components -> components.autodetected(cfg -> new MyProjector(...)))`. The matcher is implicit — `autodetected(...)` includes the component for the surrounding processor.
- **Customisation**: AF4 `(config, builder) -> builder.batchSize(100)` (2 args) → AF5 `(cfg, conf) -> conf.batchSize(100)` (still 2 args but on a different builder type). Use `.notCustomized()` when there were no AF4 customisations.
- **Module FQNs**: `org.axonframework.messaging.configuration.MessagingConfigurer`, `org.axonframework.eventsourcing.configuration.EventSourcingConfigurer`. The `EventProcessorModule` / `PooledStreamingEventProcessorModule` types are accessed through the fluent block; you rarely import them directly.

##### Caveats

- **DO NOT use `EventProcessorDefinition` here.** That bean type is Spring-Boot-specific (`org.axonframework.extension.spring.config.EventProcessorDefinition`). Native projects always use the fluent `MessagingConfigurer.eventProcessing(...)` block.
- **Side-by-side AF4 + AF5 doesn't compile.** The AF4 `EventProcessingConfigurer` interface is gone in AF5; the old method calls won't resolve. Delete the entire AF4 chain in the same commit as introducing the AF5 fluent block.
- **`autodetected(...)` vs explicit handler matching.** The AF5 fluent block does the matching through `autodetected(...)` (the framework adopts the component for the surrounding processor). If the AF4 project used a custom `type -> …` predicate, the AF5 form is either `autodetected` plus class-level `@Namespace` on each component (recommended) or a custom `components.matching(...)` call (rare).
- **`notCustomized()` is mandatory when omitting customisation.** Forgetting it leaves the builder in an "uninitialised" state and start fails. Always close with either `.customized(...)` or `.notCustomized()`.
- **Subscribing vs pooled defaults**: AF4 default was `Tracking`; AF5 has no `Tracking`. The default is `pooledStreaming`. Only register `subscribing` when the AF4 source explicitly did so.
- **Per-slice projects** (vertical-slice layouts where each bounded context has its own `static MessagingConfigurer configure(MessagingConfigurer)` method) put the fluent block inside that per-slice method. The recipe migrates the slice that owns `$SOURCE`'s processor; other slices are out of scope.

---

### 06 — Custom `SequencingPolicy` rewrite

**Why this case is interesting:** Built-in policies (`MetadataSequencingPolicy`, `SequentialPerAggregatePolicy`, etc.) cover most projects, but some need a class-level custom policy that derives the sequence id from event payload + metadata. The interface, method signature, return wrapping, and accessor names all change. Wrong-shaped migration compiles cleanly under generics but returns wrong sequence ids — events get out-of-order or wrongly serialised at the processor level.

**Apply-condition:** scope contains a class implementing the AF4 `SequencingPolicy<EventMessage<?>>` interface that `$SOURCE` depends on.

##### Before (AF4)

```java
package com.dddheroes.heroesofddd.shared.sequencing;

import com.dddheroes.heroesofddd.shared.metadata.GameMetaData;
import org.axonframework.eventhandling.EventMessage;
import org.axonframework.eventhandling.async.SequencingPolicy;

public class TenantAndGameSequencingPolicy implements SequencingPolicy<EventMessage<?>> {

    @Override
    public Object getSequenceIdentifierFor(EventMessage<?> event) {
        String tenant = (String) event.getMetaData().get(GameMetaData.TENANT_KEY);
        String gameId = (String) event.getMetaData().get(GameMetaData.GAME_ID_KEY);
        if (tenant == null || gameId == null) {
            return null;   // full-concurrency fallback
        }
        return tenant + ":" + gameId;
    }
}
```

The policy is registered via `EventProcessingConfigurer.assignSequencingPolicy("MyProcessor", c -> c.getComponent(TenantAndGameSequencingPolicy.class))` or as a `@Bean` referenced from YAML.

##### After (AF5)

```java
package com.dddheroes.heroesofddd.shared.sequencing;

import com.dddheroes.heroesofddd.shared.metadata.GameMetaData;
import org.axonframework.messaging.core.ProcessingContext;
import org.axonframework.messaging.core.sequencing.SequencingPolicy;
import org.axonframework.messaging.eventhandling.EventMessage;

import java.util.Optional;

public class TenantAndGameSequencingPolicy implements SequencingPolicy {

    @Override
    public Optional<Object> sequenceIdentifierFor(EventMessage message, ProcessingContext context) {
        String tenant = (String) message.metaData().get(GameMetaData.TENANT_KEY);
        String gameId = (String) message.metaData().get(GameMetaData.GAME_ID_KEY);
        if (tenant == null || gameId == null) {
            return Optional.empty();   // full-concurrency fallback
        }
        return Optional.of(tenant + ":" + gameId);
    }
}
```

Class registration via the projector:

```java
@Component
@Namespace("MyProcessor")
@SequencingPolicy(type = TenantAndGameSequencingPolicy.class)
public class MyProjector { … }
```

##### What changed

- **Interface swap**: `org.axonframework.eventhandling.async.SequencingPolicy` → `org.axonframework.messaging.core.sequencing.SequencingPolicy`. The generic parameter (`<EventMessage<?>>`) is GONE — AF5 binds the message type via reflection at registration time.
- **Method rename + signature change**:
  - Name: `getSequenceIdentifierFor` → `sequenceIdentifierFor`.
  - Argument list: AF4 took one `EventMessage<?>` parameter; AF5 takes `EventMessage message, ProcessingContext context`. The context is bound by the framework — usually ignored inside the policy body.
  - Return type: `Object` → `Optional<Object>`.
- **Accessor renames** inside the body:
  - `event.getPayload()` → `message.payload()`.
  - `event.getMetaData()` → `message.metaData()`.
- **Return wrapping**: `return value;` → `return Optional.of(value);`; `return null;` → `return Optional.empty();`. Returning bare `null` from `Optional<Object>` compiles but throws NPE downstream at processor scheduling.
- **`EventMessage` import**: `org.axonframework.eventhandling.EventMessage` → `org.axonframework.messaging.eventhandling.EventMessage`. (Same simple name; only the package changed.)
- **Registration**: from `assignSequencingPolicy(...)` / YAML to class-level `@SequencingPolicy(type = TenantAndGameSequencingPolicy.class)` on the projector. The custom policy class itself is referenced by `type = ...`; there is no `parameters = "..."` for custom policies (only built-in policies like `MetadataSequencingPolicy` use `parameters`).

##### Caveats

- **`Object` → `Optional<Object>` is the silent regression.** A naive "rename + recompile" that keeps `return null` compiles cleanly because `null` is assignable to `Optional<Object>`. The processor scheduler then NPEs at runtime. Always grep the rewritten policy for `return null` and replace with `Optional.empty()`.
- **The `ProcessingContext context` parameter is rarely used.** Most custom policies ignore it. AF5 exposes it for advanced cases (e.g. "sequence by current request id from the context"), but if the AF4 body didn't need it, the AF5 body doesn't either.
- **`message.payload()` is now a record-style accessor** returning the event payload type directly, not wrapped in `EventMessage.getPayload()`. Existing casts like `(MyEvent) event.getPayload()` become `(MyEvent) message.payload()`.
- **The generic parameter on the interface is gone**, but the parameter on the policy method is preserved as `EventMessage` (also without `<?>` in AF5 — `Message` and its subtypes are non-generic). If a project has `SequencingPolicy<DomainEvent>` (custom narrowing), the AF5 form drops the narrowing and the policy body must cast `message.payload()` explicitly.
- **Class-level annotation registration** (`@SequencingPolicy(type = TenantAndGameSequencingPolicy.class)`) is the AF5 preferred form. The AF4 `assignSequencingPolicy(...)` API is gone; do NOT carry it over.

---

### 07 — Dual-role class: `@EventHandler` + `@QueryHandler` on the same class

**Why this case is interesting:** "Cache-by-event" projectors expose both `@QueryHandler` methods (for serving queries from a cache) and `@EventHandler` methods (for keeping the cache fresh). Both recipes apply in tandem — the event-processor recipe owns `@Namespace`, `@SequencingPolicy`, and the AF5 `@EventHandler` import; the query-handler recipe (run separately) owns the `@QueryHandler` import. Splitting these into two recipe invocations would double-touch the file and risk drift. The event-processor recipe migrates the event-handler half AND surfaces the still-AF4 query-handler half as a Learning so the caller can route the file through the query-handler recipe next.

**Apply-condition:** `$SOURCE` has BOTH `@EventHandler` AND `@QueryHandler` methods (dual-role).

##### Before (AF4)

```java
package com.dddheroes.heroesofddd.creaturerecruitment.read;

import com.dddheroes.heroesofddd.creaturerecruitment.events.AvailableCreaturesChanged;
import com.dddheroes.heroesofddd.creaturerecruitment.events.DwellingBuilt;
import com.dddheroes.heroesofddd.shared.metadata.GameMetaData;
import org.axonframework.config.ProcessingGroup;
import org.axonframework.eventhandling.EventHandler;
import org.axonframework.messaging.annotation.MetaDataValue;
import org.axonframework.queryhandling.QueryHandler;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
@ProcessingGroup("ReadModel_Dwelling")
public class GetAllDwellingsQueryHandler {

    private final DwellingReadModelRepository repository;

    public GetAllDwellingsQueryHandler(DwellingReadModelRepository repository) {
        this.repository = repository;
    }

    @QueryHandler
    public List<DwellingReadModel> handle(GetAllDwellingsQuery query,
                                          @MetaDataValue(GameMetaData.GAME_ID_KEY) String gameId) {
        return repository.findAllByGameId(gameId);
    }

    @EventHandler
    public void on(DwellingBuilt event,
                   @MetaDataValue(GameMetaData.GAME_ID_KEY) String gameId) {
        repository.save(new DwellingReadModel(gameId, event.dwellingId(), event.creatureId()));
    }

    @EventHandler
    public void on(AvailableCreaturesChanged event,
                   @MetaDataValue(GameMetaData.GAME_ID_KEY) String gameId) {
        repository.findById(new DwellingReadModelId(gameId, event.dwellingId()))
                  .ifPresent(rm -> rm.setAvailable(event.changedTo()));
    }
}
```

##### After (AF5)

```java
package com.dddheroes.heroesofddd.creaturerecruitment.read;

import com.dddheroes.heroesofddd.creaturerecruitment.events.AvailableCreaturesChanged;
import com.dddheroes.heroesofddd.creaturerecruitment.events.DwellingBuilt;
import com.dddheroes.heroesofddd.shared.metadata.GameMetaData;
import org.axonframework.messaging.core.annotation.MetadataValue;
import org.axonframework.messaging.core.annotation.Namespace;
import org.axonframework.messaging.core.sequencing.MetadataSequencingPolicy;
import org.axonframework.messaging.core.annotation.SequencingPolicy;
import org.axonframework.messaging.eventhandling.annotation.EventHandler;
import org.axonframework.messaging.queryhandling.annotation.QueryHandler;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
@Namespace("ReadModel_Dwelling")
@SequencingPolicy(type = MetadataSequencingPolicy.class, parameters = GameMetaData.GAME_ID_KEY)
public class GetAllDwellingsQueryHandler {

    private final DwellingReadModelRepository repository;

    public GetAllDwellingsQueryHandler(DwellingReadModelRepository repository) {
        this.repository = repository;
    }

    @QueryHandler
    public List<DwellingReadModel> handle(GetAllDwellingsQuery query,
                                          @MetadataValue(GameMetaData.GAME_ID_KEY) String gameId) {
        return repository.findAllByGameId(gameId);
    }

    @EventHandler
    public void on(DwellingBuilt event,
                   @MetadataValue(GameMetaData.GAME_ID_KEY) String gameId) {
        repository.save(new DwellingReadModel(gameId, event.dwellingId(), event.creatureId()));
    }

    @EventHandler
    public void on(AvailableCreaturesChanged event,
                   @MetadataValue(GameMetaData.GAME_ID_KEY) String gameId) {
        repository.findById(new DwellingReadModelId(gameId, event.dwellingId()))
                  .ifPresent(rm -> rm.setAvailable(event.changedTo()));
    }
}
```

##### What changed (event-processor recipe — this recipe's scope)

- `@ProcessingGroup` → `@Namespace` (string preserved).
- `@SequencingPolicy(type = MetadataSequencingPolicy.class, parameters = GameMetaData.GAME_ID_KEY)` added (project's `@Bean SequencingPolicy gameIdSequencingPolicy` referenced this group — see use-case 03).
- `@EventHandler` import: AF4 → `org.axonframework.messaging.eventhandling.annotation.EventHandler`.
- `@MetaDataValue` (capital `D`) → `@MetadataValue` (capital `M`) at `org.axonframework.messaging.core.annotation.MetadataValue`. This applies to BOTH the `@QueryHandler` AND the `@EventHandler` method parameters — the recipe rewrites the parameter annotation on every method in scope.

##### What also changes here (technically the query-handler recipe's scope)

- `@QueryHandler` import: `org.axonframework.queryhandling.QueryHandler` → `org.axonframework.messaging.queryhandling.annotation.QueryHandler`.

The event-processor recipe **also** swaps the `@QueryHandler` import in this dual-role case to keep the file internally consistent. The query-handler recipe will then re-visit the file (e.g. during a project-mode run) and confirm idempotency.

##### What the recipe DOES NOT change

- Method bodies — repository calls, return types, parameter ordering all preserved verbatim.
- The Spring `@Component` stereotype.
- The constructor + field injection of `DwellingReadModelRepository` (this is not in-handler dispatch — it is a class-level dependency for both query AND event paths).

##### Caveats

- **`@MetadataValue` capitalisation applies to both handler types.** The annotation rename catches every parameter site — `@QueryHandler` and `@EventHandler` alike. A grep for `@MetaDataValue(` after the rewrite must return zero.
- **The query-handler recipe owns response-type rewrites** (e.g. `ResponseType<List<X>>` to `List<X>` directly). The event-processor recipe must NOT touch return types or `ResponseType` constructs even when sitting in a dual-role file. If you see `ResponseType` usage, flag in Result NOTES; the query-handler recipe handles it.
- **`@SequencingPolicy` covers the EventHandler side only.** Queries are dispatched synchronously and do not respect sequencing policies. The annotation is still correct at class level — the framework applies it only when scheduling event handlers.
- **Do NOT split dual-role classes into two classes.** A class with both `@EventHandler` and `@QueryHandler` is a deliberate design choice (cache + query from same data). Splitting them is a refactor, not a migration; out of scope.
- **The class-level `@Component`** anchors Spring auto-discovery. Both `@EventHandler` and `@QueryHandler` rely on it (in Spring projects); preserve verbatim.

---

### 08 — Rejected: aggregate source routed to the event-processor recipe

**Why this case is interesting:** The event-processor recipe must reject sources that are not event-handling components. Aggregates carry `@EventSourcingHandler` (NOT `@EventHandler`), and the recipe must not be tricked by the partial similarity into editing the aggregate. The rejection NOTES point the caller to the aggregate recipe so the queue can route correctly.

**Apply-condition:** `$SOURCE` is annotated `@Aggregate` / `@AggregateRoot` with `@EventSourcingHandler` methods.

##### Detection

The `# Applicable` decision rule, predicate 2:

> Aggregate — class annotated `@Aggregate` / `@AggregateRoot` AND has at least one `@EventSourcingHandler` (not `@EventHandler`). → **Rejected** with NOTES naming `aggregate`.

Detection reads the class header annotation + scans methods for `@EventSourcingHandler` (the AF4 import is `org.axonframework.eventsourcing.EventSourcingHandler`; AF5 is `org.axonframework.eventsourcing.annotation.EventSourcingHandler`). Either form triggers predicate 2.

##### Source (left untouched)

```java
package com.dddheroes.heroesofddd.calendar.write;

import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.eventsourcing.EventSourcingHandler;
import org.axonframework.modelling.command.AggregateIdentifier;
import org.axonframework.spring.stereotype.Aggregate;

import static org.axonframework.modelling.command.AggregateLifecycle.apply;

@Aggregate
class Calendar {

    @AggregateIdentifier
    private CalendarId calendarId;

    @CommandHandler
    void decide(StartDay command) {
        apply(new DayStarted(command.calendarId(), command.day()));
    }

    @EventSourcingHandler
    void evolve(DayStarted event) {
        this.calendarId = new CalendarId(event.calendarId());
    }

    Calendar() { }
}
```

##### Result block

```
return REJECTED

> **Result:** ⏭️ Rejected
> **Source:** `com.dddheroes.heroesofddd.calendar.write.Calendar`
> **Recipe:** axon4to5-event-processor
>
> **Notes:** Applicable predicate 2 failed at `Calendar.java:11` — class is annotated `@Aggregate` and has `@EventSourcingHandler` methods (event-sourced aggregate). This is the aggregate recipe's job. Route to `axon4to5-aggregate`.
```

##### What did NOT happen

- No edits to `Calendar.java`. The event-processor recipe ran the `# Applicable` check, predicate 2 returned a definitive "no", and the recipe exited before Research.
- No `# Scope` enumeration, no `# References` reading, no `# Success Criteria` evaluation. Rejected halts the sub-flow at the first diamond in FLOW.md.
- No `@Namespace` added, no `@EventHandler` import introduced. (Critical guardrail — adding `@Namespace` to an aggregate would compile but mis-route command handling at runtime.)
- No retry budget consumed (Rejected is not a Failure).

##### Other Rejected predicates (recap)

The `# Applicable` decision rule lists six predicates:

1. **Saga** — `@Saga` OR `@SagaEventHandler`. Route to saga recipe.
2. **Aggregate** — `@Aggregate` / `@AggregateRoot` + `@EventSourcingHandler`. Route to aggregate recipe. *(This use case.)*
3. **Event-handling component, AF4 shape** — `@EventHandler` AND `@ProcessingGroup`. **Continue** to Research.
4. **Event-handling component, partially-migrated** — `@EventHandler` AND `@Namespace`. **Continue** (Success Criteria pre-Apply check decides).
5. **Event-handling component, no group/namespace** — `@EventHandler` but no group marker. **Continue** with NOTES surfacing the missing namespace.
6. **None of the above** — no `@EventHandler` anywhere. Rejected with NOTES naming the failed predicate.

##### Caveats

- **`@EventSourcingHandler` vs `@EventHandler` is the load-bearing distinction.** Both are method-level annotations on what looks like event-handling code; the difference is which framework subsystem schedules them. Aggregates use `@EventSourcingHandler` (re-applying past events to reconstruct state); event processors use `@EventHandler` (downstream event reactions). Mis-routing breaks command handling silently.
- **NOTES must say `aggregate` or name the aggregate recipe explicitly.** Without specificity, the orchestrator's queue cannot route to the right next recipe in project mode.
- **Source on disk MUST be byte-identical to the input.** The grader can sanity-check this by asserting `@Aggregate` is still present and `@EventSourced` / `@Namespace` / `@EventHandler` (AF5 import) were NOT added.
- **State-stored aggregates also fall here.** An `@Aggregate` + JPA `@Entity` source with zero `@EventSourcingHandler` methods technically misses predicate 2 (no `@EventSourcingHandler`); the aggregate recipe rejects it as state-stored. The event-processor recipe doesn't see it at all — predicate 6 catches it as "none of the above".

---

## event store

### Use case 01 — Spring Boot + JPA backend

**Why interesting:** Most common migration shape — covers two AF4 patterns: (a) explicit `EmbeddedEventStore` + `JpaEventStorageEngine` bean in a `@Configuration` class, and (b) no explicit engine bean + `axon.axonserver.enabled=false` (or `axon.axonserver.event-store.enabled=false`) in `application.yml` WITH JPA on the classpath (`spring-boot-starter-data-jpa` / `EntityManagerFactory`). In AF4, `JpaEventStoreAutoConfiguration` had `@ConditionalOnBean(EntityManagerFactory.class)` — it only fired when JPA was actually on the classpath; the YAML flag was just the trigger that stopped Axon Server from winning the race. AF5 requires an explicit `@Bean AggregateBasedJpaEventStorageEngine` AND `@EntityScan` covering framework packages — without both, the app either starts cleanly then fails at first command/replay, or fails on startup with `Could not resolve root entity 'AggregateEventEntry'`.

##### Before (AF4)

```java
@Configuration
public class EventStoreConfiguration {

    @Bean
    public EmbeddedEventStore eventStore(EventStorageEngine storageEngine,
                                         AxonConfiguration config) {
        return EmbeddedEventStore.builder()
                .storageEngine(storageEngine)
                .messageMonitor(config.messageMonitor(EmbeddedEventStore.class, "eventStore"))
                .build();
    }

    @Bean
    public EventStorageEngine storageEngine(EntityManagerProvider entityManagerProvider,
                                            TransactionManager transactionManager,
                                            Serializer snapshotSerializer) {
        return JpaEventStorageEngine.builder()
                .entityManagerProvider(entityManagerProvider)
                .transactionManager(transactionManager)
                .snapshotSerializer(snapshotSerializer)
                .build();
    }
}
```

```java
@SpringBootApplication
public class MyApplication {
    public static void main(String[] args) {
        SpringApplication.run(MyApplication.class, args);
    }
}
```

##### After (AF5)

```java
@Configuration
public class EventStoreConfiguration {

    @Bean
    public EventStorageEngine eventStorageEngine(EntityManagerFactory entityManagerFactory,
                                                 EventConverter eventConverter) {
        return new AggregateBasedJpaEventStorageEngine(
                new JpaTransactionalExecutorProvider(entityManagerFactory),
                eventConverter,
                UnaryOperator.identity()
        );
    }
}
```

```java
import org.springframework.boot.autoconfigure.domain.EntityScan;

@SpringBootApplication
@EntityScan(basePackages = {
    "com.example",             // project's own @Entity classes
    "org.axonframework",       // AggregateEventEntry + TokenEntry
    "io.axoniq.framework"      // DeadLetterEntry (commercial AF5; drop on free-af5 line)
})
public class MyApplication {
    public static void main(String[] args) {
        SpringApplication.run(MyApplication.class, args);
    }
}
```

Imports for `EventStoreConfiguration`:
```java
import jakarta.persistence.EntityManagerFactory;
import org.axonframework.eventsourcing.eventstore.EventStorageEngine;
import org.axonframework.eventsourcing.eventstore.jpa.AggregateBasedJpaEventStorageEngine;
import org.axonframework.messaging.core.unitofwork.transaction.jpa.JpaTransactionalExecutorProvider;
import org.axonframework.messaging.eventhandling.conversion.EventConverter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import java.util.function.UnaryOperator;
```

##### What changed

- `EmbeddedEventStore` bean **deleted** — AF5 wires the event store from the engine alone; no `EmbeddedEventStore` wrapper.
- `JpaEventStorageEngine.builder()…build()` → `new AggregateBasedJpaEventStorageEngine(JpaTransactionalExecutorProvider, EventConverter, configurer)`.
- `Serializer` arg **removed** — AF5 engines take `EventConverter` (resolved from configuration registry), not a `Serializer` constructor arg.
- `EntityManagerProvider` + `TransactionManager` → `EntityManagerFactory` + `JpaTransactionalExecutorProvider`.
- `@EntityScan` added to main class covering three package roots — required because the explicit `@Bean EventStorageEngine` trips `@ConditionalOnMissingBean` on `JpaEventStoreAutoConfiguration` before its `@Import(DefaultEntityRegistrar.class)` fires.

##### Caveats

- **`UnaryOperator.identity()`** keeps `AggregateBasedJpaEventStorageEngineConfiguration` defaults. Only use a custom configurer lambda if AF4 explicitly tuned `batchSize` / `gapTimeout` / `persistenceExceptionResolver`.
- **Schema change is out-of-band.** `domain_event_entry` → `aggregate_event_entry` table rename + column renames. Record in Result Notes; do NOT write SQL.
- **`io.axoniq.framework` in `@EntityScan`** — drop this entry on the free AF5 line (no commercial `DeadLetterEntry`). Include on the AxonIQ commercial line.

---

### Use case 02 — Spring Boot + Axon Server backend

**Why interesting:** `axoniq-spring-boot-starter` includes `axon-server-connector`, whose `AxonServerConfigurationEnhancer` (ServiceLoader, `order=MIN_VALUE+10`) auto-registers `AxonServerEventStorageEngine` (DCB-flat) — NOT the aggregate-based variant. To preserve AF4's aggregate-keyed event log semantics, an explicit `@Bean AggregateBasedAxonServerEventStorageEngine` must be declared. The Spring `@Bean` is visible to `SpringComponentRegistry.hasComponent(ALL)` — both enhancers find the slot occupied and skip.

##### Before (AF4)

```java
// AF4: no explicit @Bean needed — axon-spring-boot-starter auto-wires AxonServerEventStore
// This is the "no config" case or minimal config:
@SpringBootApplication
public class MyApplication {
    public static void main(String[] args) {
        SpringApplication.run(MyApplication.class, args);
    }
}
```

Or explicitly:

```java
@Configuration
public class AxonConfig {

    @Bean
    public AxonServerEventStore eventStore(AxonServerConfiguration serverConfig,
                                           AxonServerConnectionManager connectionManager) {
        return AxonServerEventStore.builder()
                .configuration(serverConfig)
                .axonServerConnectionManager(connectionManager)
                .build();
    }
}
```

##### After (AF5)

```java
import io.axoniq.framework.axonserver.connector.api.AxonServerConnectionManager;
import io.axoniq.framework.axonserver.connector.event.AggregateBasedAxonServerEventStorageEngine;
import org.axonframework.eventsourcing.eventstore.EventStorageEngine;
import org.axonframework.messaging.eventhandling.conversion.EventConverter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class AxonConfig {

    @Bean
    public EventStorageEngine storageEngine(AxonServerConnectionManager connectionManager,
                                            EventConverter eventConverter) {
        return new AggregateBasedAxonServerEventStorageEngine(
                connectionManager.getConnection(),
                eventConverter
        );
    }
}
```

For a non-default Axon Server context:
```java
return new AggregateBasedAxonServerEventStorageEngine(
        connectionManager.getConnection("my-context"),
        eventConverter
);
```

##### What changed

- Any AF4 `@Bean AxonServerEventStore` **deleted** (two beans of `EventStorageEngine` = startup failure).
- Explicit `@Bean EventStorageEngine` returning `AggregateBasedAxonServerEventStorageEngine` **added** — overrides connector's auto-registration of DCB-flat `AxonServerEventStorageEngine`.
- `AxonServerConfiguration` arg removed — AF5 engine takes `AxonServerConnectionManager.getConnection()` directly.
- No `@EntityScan` needed — Axon Server stores its own events; no JPA entities involved.
- No schema change — Axon Server event storage is server-side.

##### Caveats

- **`AggregateBasedAxonServerEventStorageEngine` is opt-in.** The connector JAR ships it but does not auto-register it. Explicit `@Bean` or `registerEventStorageEngine` is the only registration path.
- **DCB migration is out of scope.** If the project wants to migrate to the DCB-native `AxonServerEventStorageEngine` (requires Axon Server 2025.2.0+), that is a separate, larger initiative — not handled by this recipe.
- **Custom `Serializer` / `EventConverter`** — if AF4 explicitly wired a custom `Serializer` to the event store, AF5 uses `EventConverter` (different SPI). Flag in Result Notes; the recipe does not auto-port custom serializers.

---

### Use case 03 — Framework Configurer + Axon Server backend (native)

**Why interesting:** Native (non-Spring) projects wire the event store via `EventSourcingConfigurer.registerEventStorageEngine(...)`. The connector's `AxonServerConfigurationEnhancer` is still ServiceLoader-discovered and still registers DCB-flat `AxonServerEventStorageEngine` when present — but an explicit `registerEventStorageEngine(...)` call overrides it because it runs before the enhancer processes the registry.

##### Before (AF4)

```java
public class AxonConfig {

    public Configuration buildConfiguration() {
        Configurer configurer = DefaultConfigurer.defaultConfiguration();
        // AF4: AxonServerEventStore auto-configured by axon-server-connector starter
        // or explicitly:
        // configurer.configureEventStore(c -> AxonServerEventStore.builder()
        //         .configuration(c.getComponent(AxonServerConfiguration.class))
        //         .axonServerConnectionManager(c.getComponent(AxonServerConnectionManager.class))
        //         .build());
        return configurer.buildConfiguration();
    }
}
```

##### After (AF5)

```java
import io.axoniq.framework.axonserver.connector.api.AxonServerConnectionManager;
import io.axoniq.framework.axonserver.connector.event.AggregateBasedAxonServerEventStorageEngine;
import org.axonframework.eventsourcing.configuration.EventSourcingConfigurer;
import org.axonframework.messaging.eventhandling.conversion.EventConverter;

public class AxonConfig {

    public AxonConfiguration buildConfiguration() {
        EventSourcingConfigurer configurer = EventSourcingConfigurer.create();

        configurer.registerEventStorageEngine(config -> {
            AxonServerConnectionManager manager =
                    config.getComponent(AxonServerConnectionManager.class);
            return new AggregateBasedAxonServerEventStorageEngine(
                    manager.getConnection(),
                    config.getComponent(EventConverter.class)
            );
        });

        return configurer.build();
    }
}
```

##### What changed

- `DefaultConfigurer.defaultConfiguration()` → `EventSourcingConfigurer.create()`.
- `buildConfiguration()` → `build()`. Return type `AxonConfiguration`.
- AF4 `configureEventStore(...)` → AF5 `registerEventStorageEngine(...)`.
- Factory lambda receives AF5 read-only `Configuration` — use `config.getComponent(...)` to resolve deps.
- No `@EntityScan` — no JPA; Axon Server stores its own events.

##### Caveats

- `config.getComponent(AxonServerConnectionManager.class)` works only if the connector enhancer has registered the connection manager. If the project manually registers `AxonServerConnectionManager`, pass it as a constructor arg to the setup method instead.
- For non-default Axon Server context: `manager.getConnection("my-context")`.

---

### Use case 04 — Framework Configurer + JPA backend (native)

**Why interesting:** Native projects with JPA event store use `EventSourcingConfigurer.registerEventStorageEngine(...)`. No `@EntityScan` needed (no Spring Boot auto-config involved), but the schema change is still out-of-band and must be flagged. Also no `axon-server-connector` race condition since the class is not loaded by Spring Boot.

##### Before (AF4)

```java
public class AxonConfig {

    private final EntityManager entityManager;
    private final TransactionManager transactionManager;

    public AxonConfig(EntityManager entityManager, TransactionManager transactionManager) {
        this.entityManager = entityManager;
        this.transactionManager = transactionManager;
    }

    public Configuration buildConfiguration() {
        Configurer configurer = DefaultConfigurer.defaultConfiguration();

        configurer.configureEventStore(c ->
            EmbeddedEventStore.builder()
                .storageEngine(JpaEventStorageEngine.builder()
                    .entityManagerProvider(() -> entityManager)
                    .transactionManager(transactionManager)
                    .build())
                .build()
        );

        return configurer.buildConfiguration();
    }
}
```

##### After (AF5)

```java
import org.axonframework.eventsourcing.configuration.EventSourcingConfigurer;
import org.axonframework.eventsourcing.eventstore.jpa.AggregateBasedJpaEventStorageEngine;
import org.axonframework.messaging.core.unitofwork.transaction.jpa.JpaTransactionalExecutorProvider;
import org.axonframework.messaging.eventhandling.conversion.EventConverter;

public class AxonConfig {

    private final EntityManagerFactory entityManagerFactory;

    public AxonConfig(EntityManagerFactory entityManagerFactory) {
        this.entityManagerFactory = entityManagerFactory;
    }

    public AxonConfiguration buildConfiguration() {
        EventSourcingConfigurer configurer = EventSourcingConfigurer.create();

        configurer.registerEventStorageEngine(config ->
            new AggregateBasedJpaEventStorageEngine(
                new JpaTransactionalExecutorProvider(entityManagerFactory),
                config.getComponent(EventConverter.class),
                UnaryOperator.identity()
            )
        );

        return configurer.build();
    }
}
```

Import: add `import java.util.function.UnaryOperator;`.

##### What changed

- `DefaultConfigurer.defaultConfiguration()` → `EventSourcingConfigurer.create()`.
- `EmbeddedEventStore.builder()…build()` **deleted** — not needed in AF5.
- `JpaEventStorageEngine.builder()…build()` → `new AggregateBasedJpaEventStorageEngine(JpaTransactionalExecutorProvider, EventConverter, configurer)`.
- `EntityManagerProvider` + `TransactionManager` → `EntityManagerFactory` + `JpaTransactionalExecutorProvider`.
- `Serializer` arg removed — `EventConverter` resolved from configuration registry.
- `buildConfiguration()` → `build()`. Return type `AxonConfiguration`.

##### Caveats

- **Schema change is out-of-band** — `domain_event_entry` → `aggregate_event_entry` table rename + column renames. Flag in Result Notes; do NOT write SQL files.
- **`UnaryOperator.identity()`** keeps defaults. Use a custom lambda only if AF4 tuned `batchSize` / `gapTimeout` / `persistenceExceptionResolver`.
- No `@EntityScan` — not Spring Boot; JPA entity registration is configured by the JPA provider setup outside Axon.

---

## interceptors

### Use case 01 — Dispatch Interceptor, Spring Boot

Dispatch interceptor enriches a command with metadata before it reaches the bus. `@Component` stays; `InterceptorAutoConfiguration` discovers by generic type.

##### Before (AF4)

```java
package io.axoniq.demo.bikerental.common;

import org.axonframework.commandhandling.CommandMessage;
import org.axonframework.messaging.MessageDispatchInterceptor;
import org.springframework.stereotype.Component;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.function.BiFunction;

@Component
public class DispatchTimeCommandDispatchInterceptor implements MessageDispatchInterceptor<CommandMessage<?>> {

    @Override
    public BiFunction<Integer, CommandMessage<?>, CommandMessage<?>> handle(
            List<? extends CommandMessage<?>> messages) {
        return (index, command) -> {
            return command.withMetaData(Map.of("dispatchTime", Instant.now().toString()));
        };
    }
}
```

##### After (AF5)

```java
package io.axoniq.demo.bikerental.common;

import org.axonframework.messaging.commandhandling.CommandMessage;
import org.axonframework.messaging.core.MessageDispatchInterceptor;
import org.axonframework.messaging.core.MessageDispatchInterceptorChain;
import org.axonframework.messaging.core.MessageStream;
import org.axonframework.messaging.core.unitofwork.ProcessingContext;
import org.jspecify.annotations.Nullable;
import org.springframework.stereotype.Component;

import java.time.Instant;
import java.util.Collections;

@Component
public class DispatchTimeCommandDispatchInterceptor implements MessageDispatchInterceptor<CommandMessage> {

    @Override
    public MessageStream<?> interceptOnDispatch(CommandMessage message,
                                                @Nullable ProcessingContext context,
                                                MessageDispatchInterceptorChain<CommandMessage> chain) {
        CommandMessage enrichedMessage = message.andMetadata(
                Collections.singletonMap("dispatchTime", Instant.now().toString())
        );
        return chain.proceed(enrichedMessage, context);
    }
}
```

##### What changed

- Method: `handle(List<...>)` → `interceptOnDispatch(M, @Nullable ProcessingContext, Chain)`
- Return: `BiFunction<Integer, M, M>` → `MessageStream<?>`
- Body: batch-lambda collapsed — receive one `message`, modify inline, call `chain.proceed(modified, context)`
- Generic: `CommandMessage<?>` → `CommandMessage` (no wildcard)
- `withMetaData(Map.of(...))` → `andMetadata(Collections.singletonMap(...))` — AF5 message accessor
- Removed imports: `java.util.List`, `java.util.function.BiFunction`, `java.util.Map`, `org.axonframework.commandhandling.CommandMessage` (AF4), `org.axonframework.messaging.MessageDispatchInterceptor` (AF4)
- Added imports: `org.axonframework.messaging.commandhandling.CommandMessage` (AF5), `org.axonframework.messaging.core.MessageDispatchInterceptor`, `org.axonframework.messaging.core.MessageDispatchInterceptorChain`, `org.axonframework.messaging.core.MessageStream`, `org.axonframework.messaging.core.unitofwork.ProcessingContext`, `org.jspecify.annotations.Nullable`, `java.util.Collections`
- `@Component` unchanged — Path A auto-discovery

##### Caveats

- `context` is `@Nullable` — may be `null` when dispatching from outside a handler (HTTP endpoint). Pass it as-is to `chain.proceed(enrichedMessage, context)` — never null-guard it.
- `Map.of(...)` → `Collections.singletonMap(...)` is a style choice; either compiles. The key change is `withMetaData` → `andMetadata`.

---

### Use case 02 — Handler Interceptor, Spring Boot (with lifecycle hooks)

Handler interceptor that logs commands and wires pre/post lifecycle callbacks. `@Component` stays; shows full `UnitOfWork` → `ProcessingContext` replacement including `onCommit` and `onRollback`.

##### Before (AF4)

```java
package io.example.interceptors;

import org.axonframework.commandhandling.CommandMessage;
import org.axonframework.messaging.InterceptorChain;
import org.axonframework.messaging.MessageHandlerInterceptor;
import org.axonframework.messaging.unitofwork.UnitOfWork;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

@Component
public class LoggingCommandHandlerInterceptor implements MessageHandlerInterceptor<CommandMessage<?>> {

    private static final Logger logger = LoggerFactory.getLogger(LoggingCommandHandlerInterceptor.class);

    @Override
    public Object handle(UnitOfWork<? extends CommandMessage<?>> unitOfWork,
                         InterceptorChain interceptorChain) throws Exception {
        CommandMessage<?> command = unitOfWork.getMessage();
        logger.info("Handling command: {}", command.getCommandName());

        unitOfWork.onCommit(uow -> {
            logger.info("Command committed: {}", command.getCommandName());
        });

        unitOfWork.onRollback(uow -> {
            logger.error("Command rolled back: {}", command.getCommandName());
        });

        return interceptorChain.proceed();
    }
}
```

##### After (AF5)

```java
package io.example.interceptors;

import org.axonframework.messaging.commandhandling.CommandMessage;
import org.axonframework.messaging.core.MessageHandlerInterceptor;
import org.axonframework.messaging.core.MessageHandlerInterceptorChain;
import org.axonframework.messaging.core.MessageStream;
import org.axonframework.messaging.core.unitofwork.ProcessingContext;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

@Component
public class LoggingCommandHandlerInterceptor implements MessageHandlerInterceptor<CommandMessage> {

    private static final Logger logger = LoggerFactory.getLogger(LoggingCommandHandlerInterceptor.class);

    @Override
    public MessageStream<?> interceptOnHandle(CommandMessage message,
                                              ProcessingContext context,
                                              MessageHandlerInterceptorChain<CommandMessage> chain) {
        logger.info("Handling command: {}", message.getCommandName());

        context.runOnAfterCommit(ctx -> {
            logger.info("Command committed: {}", message.getCommandName());
        });

        context.onError((ctx, error) -> {
            logger.error("Command rolled back: {}", message.getCommandName());
        });

        return chain.proceed(message, context);
    }
}
```

##### What changed

- Method: `handle(UnitOfWork<...>, InterceptorChain) throws Exception` → `interceptOnHandle(M, ProcessingContext, Chain)`
- Return: `Object` → `MessageStream<?>`
- `unitOfWork.getMessage()` removed — use `message` parameter directly
- `unitOfWork.onCommit(uow -> ...)` → `context.runOnAfterCommit(ctx -> ...)`
- `unitOfWork.onRollback(uow -> ...)` → `context.onError((ctx, error) -> ...)` — note two-arg lambda
- `return interceptorChain.proceed()` → `return chain.proceed(message, context)`
- `throws Exception` removed from method signature
- Generic: `CommandMessage<?>` → `CommandMessage`
- Removed imports: `org.axonframework.commandhandling.CommandMessage` (AF4), `org.axonframework.messaging.InterceptorChain`, `org.axonframework.messaging.MessageHandlerInterceptor` (AF4), `org.axonframework.messaging.unitofwork.UnitOfWork`
- Added imports: `org.axonframework.messaging.commandhandling.CommandMessage` (AF5), `org.axonframework.messaging.core.MessageHandlerInterceptor`, `org.axonframework.messaging.core.MessageHandlerInterceptorChain`, `org.axonframework.messaging.core.MessageStream`, `org.axonframework.messaging.core.unitofwork.ProcessingContext`

##### Caveats

- `onError` callback signature is `(ProcessingContext ctx, Throwable error)` — two args, not one.
- `onPrepareCommit` (AF4) → `runOnPreInvocation` (AF5), not `runOnAfterCommit`. Map carefully: pre-commit is `runOnPreInvocation`, post-commit is `runOnAfterCommit`.
- `context` for handler interceptors is **never null** — no `@Nullable` annotation needed.

---

### Use case 03 — Handler Interceptor, Native Config (registration site rewrite)

Standalone handler interceptor without Spring. Path B — explicit registration in Configurer. Shows both the interceptor class rewrite AND the registration call rewrite from `Configurer` to `MessagingConfigurer`.

##### Before (AF4)

**Interceptor class:**

```java
package io.example.interceptors;

import org.axonframework.commandhandling.CommandMessage;
import org.axonframework.messaging.InterceptorChain;
import org.axonframework.messaging.MessageHandlerInterceptor;
import org.axonframework.messaging.unitofwork.UnitOfWork;

public class AuditCommandHandlerInterceptor implements MessageHandlerInterceptor<CommandMessage<?>> {

    @Override
    public Object handle(UnitOfWork<? extends CommandMessage<?>> unitOfWork,
                         InterceptorChain interceptorChain) throws Exception {
        // pre-handle audit
        Object result = interceptorChain.proceed();
        // post-handle audit
        return result;
    }
}
```

**Registration site (Configurer file):**

```java
import org.axonframework.config.Configurer;
import org.axonframework.config.DefaultConfigurer;

Configurer configurer = DefaultConfigurer.defaultConfiguration();
configurer.registerCommandHandlerInterceptor(config -> new AuditCommandHandlerInterceptor());
```

##### After (AF5)

**Interceptor class:**

```java
package io.example.interceptors;

import org.axonframework.messaging.commandhandling.CommandMessage;
import org.axonframework.messaging.core.MessageHandlerInterceptor;
import org.axonframework.messaging.core.MessageHandlerInterceptorChain;
import org.axonframework.messaging.core.MessageStream;
import org.axonframework.messaging.core.unitofwork.ProcessingContext;

public class AuditCommandHandlerInterceptor implements MessageHandlerInterceptor<CommandMessage> {

    @Override
    public MessageStream<?> interceptOnHandle(CommandMessage message,
                                              ProcessingContext context,
                                              MessageHandlerInterceptorChain<CommandMessage> chain) {
        // pre-handle audit
        return chain.proceed(message, context);
        // post-handle audit belongs in runOnAfterCommit if needed
    }
}
```

**Registration site (Configurer file):**

```java
import org.axonframework.messaging.core.config.MessagingConfigurer;

MessagingConfigurer configurer = MessagingConfigurer.create();
configurer.registerCommandHandlerInterceptor(config -> new AuditCommandHandlerInterceptor());
```

##### What changed

**Interceptor class:**
- Method: `handle(UnitOfWork, InterceptorChain) throws Exception` → `interceptOnHandle(M, ProcessingContext, Chain)`
- Return: `Object` → `MessageStream<?>`; intermediate result variable eliminated
- Chain: `interceptorChain.proceed()` → `chain.proceed(message, context)` as direct return
- Generic: `CommandMessage<?>` → `CommandMessage`
- Removed imports: `org.axonframework.commandhandling.CommandMessage` (AF4), `org.axonframework.messaging.InterceptorChain`, `org.axonframework.messaging.MessageHandlerInterceptor` (AF4), `org.axonframework.messaging.unitofwork.UnitOfWork`
- Added imports: AF5 equivalents

**Registration site:**
- Receiver type: `Configurer` (AF4) → `MessagingConfigurer` (AF5)
- Factory: `DefaultConfigurer.defaultConfiguration()` → `MessagingConfigurer.create()`
- Method name **unchanged**: `registerCommandHandlerInterceptor(...)` stays the same
- Import: `org.axonframework.config.Configurer` + `org.axonframework.config.DefaultConfigurer` removed; `org.axonframework.messaging.core.config.MessagingConfigurer` added

##### Caveats

- Method names on `MessagingConfigurer` are identical to AF4 `Configurer` for typed interceptors (`registerCommandHandlerInterceptor`, `registerEventHandlerInterceptor`, `registerQueryHandlerInterceptor`). **Exception**: AF4 generic `registerDispatchInterceptor(...)` → AF5 typed `registerCommandDispatchInterceptor(...)` / `registerEventDispatchInterceptor(...)` / `registerQueryDispatchInterceptor(...)` — pick the correct typed form based on the interceptor's generic `M` type.
- AF4 post-handle logic stored in a local variable (`Object result = interceptorChain.proceed()`) cannot have a direct equivalent when the chain is async. Move post-handle logic into `context.runOnAfterCommit(...)` instead.

---

### Use case 04 — Annotation-based interceptor (B1 Blocker)

`@MessageHandlerInterceptor` used as a **method annotation** inside a handler class. This is NOT the same as implementing the `MessageHandlerInterceptor<M>` interface. Not functional in AF5 < 5.2.0. Recipe halts with Blocker B1.

##### Source (triggers B1)

```java
package io.example.handlers;

import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.commandhandling.CommandMessage;
import org.axonframework.messaging.InterceptorChain;
import org.axonframework.messaging.interceptors.MessageHandlerInterceptor;
import org.springframework.stereotype.Component;

@Component
public class OrderCommandHandler {

    @CommandHandler
    public String handle(CreateOrderCommand cmd) {
        return "created";
    }

    @MessageHandlerInterceptor(messageType = CommandMessage.class)
    public Object intercept(CommandMessage<?> message, InterceptorChain chain) throws Exception {
        // pre-handling interceptor logic
        return chain.proceed();
    }
}
```

##### Expected result

```
return BLOCKER

> **Result:** 🚧 Blocker
> **Source:** `io.example.handlers.OrderCommandHandler`
> **Recipe:** axon4to5-interceptors
>
> **Notes:** B1 — `@MessageHandlerInterceptor` annotation on method `intercept(...)` at `OrderCommandHandler.java:17`. Using this annotation to declare inline interceptor methods is not supported in AF5 < 5.2.0. The `MessageHandlerInterceptor<M>` *interface* is fully migratable; this *annotation* form requires AF5 5.2.0+.
>
> **Options:**
> - [ ] **skip** — keep `OrderCommandHandler` as-is; queue moves on. The inline interceptor will be silently ignored at runtime until 5.2.0.
> - [ ] **revert** — undo any edits; restore pre-recipe state.
> - [ ] **solve-manually** — extract the interceptor method into a standalone class implementing `MessageHandlerInterceptor<CommandMessage>` (fully migratable today), or wait for AF5 5.2.0+.
```

##### What distinguishes annotation from interface

| Form | Class declaration | Detectable by |
|------|-------------------|---------------|
| Interface (migratable) | `implements MessageHandlerInterceptor<CommandMessage>` | `grep 'implements MessageHandlerInterceptor'` |
| Annotation (B1) | `@MessageHandlerInterceptor` on a method | `grep '@MessageHandlerInterceptor'` |

The annotation may appear on a class that also has `@CommandHandler` / `@EventHandler` methods — that's the expected pattern for the inline style. The interface implementation appears on a dedicated interceptor class without handler annotations.

---

## query handlers

### 01 — Spring REST controller: import-only change

**Why this case is interesting:** The simplest AF4→AF5 path. The controller already uses the `Class<R>` overload of `query(...)` — AF5 kept this overload. Only the `QueryGateway` import package changes.

**Apply-condition:** `$SOURCE` is a Spring `@RestController` AND all `query(...)` calls use `Class<R>` (no `ResponseType` wrapper, no named-query string).

##### Before (AF4)

```java
package com.example.dwellings.api;

import com.example.dwellings.read.DwellingReadModel;
import org.axonframework.queryhandling.QueryGateway;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.concurrent.CompletableFuture;

@RestController
@RequestMapping("/dwellings")
class DwellingRestController {

    private final QueryGateway queryGateway;

    DwellingRestController(QueryGateway queryGateway) {
        this.queryGateway = queryGateway;
    }

    @GetMapping("/{dwellingId}")
    CompletableFuture<DwellingReadModel> getDwelling(@PathVariable String dwellingId) {
        return queryGateway.query(new GetDwellingById(dwellingId), DwellingReadModel.class);
    }
}
```

##### After (AF5)

```java
package com.example.dwellings.api;

import com.example.dwellings.read.DwellingReadModel;
import org.axonframework.messaging.queryhandling.gateway.QueryGateway;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.concurrent.CompletableFuture;

@RestController
@RequestMapping("/dwellings")
class DwellingRestController {

    private final QueryGateway queryGateway;

    DwellingRestController(QueryGateway queryGateway) {
        this.queryGateway = queryGateway;
    }

    @GetMapping("/{dwellingId}")
    CompletableFuture<DwellingReadModel> getDwelling(@PathVariable String dwellingId) {
        return queryGateway.query(new GetDwellingById(dwellingId), DwellingReadModel.class);
    }
}
```

##### What changed

- `org.axonframework.queryhandling.QueryGateway` → `org.axonframework.messaging.queryhandling.gateway.QueryGateway`
- Body, field, constructor, and method signature **unchanged**

##### Caveats

- If the AF4 call had used `ResponseTypes.instanceOf(DwellingReadModel.class)` instead of `DwellingReadModel.class`, the wrapper must be stripped — see use-case 03.
- The controller returns `CompletableFuture<DwellingReadModel>` — Spring MVC serves async futures natively. No blocking concern here.

---

### 01 — Simple @QueryHandler class: import-only swap

**Why this case is interesting:** Projection classes that already use typed query payload classes (no string `queryName`, no `QueryUpdateEmitter`) need only the `@QueryHandler` import package to change. Everything else — annotations, parameters, method bodies — stays byte-identical.

**Apply-condition:** `$SOURCE` has `@QueryHandler` with proper payload-class parameters, no `queryName` attribute, no `QueryUpdateEmitter` dependency.

---

##### Before (AF4)

```java
package io.axoniq.demo.bikerental.rental.query;

import org.axonframework.queryhandling.QueryHandler;
import org.springframework.stereotype.Component;

@Component
public class BikeStatusHandler {

    private final BikeStatusRepository bikeStatusRepository;

    public BikeStatusHandler(BikeStatusRepository bikeStatusRepository) {
        this.bikeStatusRepository = bikeStatusRepository;
    }

    @QueryHandler
    public Iterable<BikeStatus> findAll(FindAllBikes query) {
        return bikeStatusRepository.findAll();
    }

    @QueryHandler
    public BikeStatus findOne(FindBikeById query) {
        return bikeStatusRepository.findById(query.bikeId()).orElse(null);
    }
}
```

##### After (AF5)

```java
package io.axoniq.demo.bikerental.rental.query;

import org.axonframework.messaging.queryhandling.annotation.QueryHandler;
import org.springframework.stereotype.Component;

@Component
public class BikeStatusHandler {

    private final BikeStatusRepository bikeStatusRepository;

    public BikeStatusHandler(BikeStatusRepository bikeStatusRepository) {
        this.bikeStatusRepository = bikeStatusRepository;
    }

    @QueryHandler
    public Iterable<BikeStatus> findAll(FindAllBikes query) {
        return bikeStatusRepository.findAll();
    }

    @QueryHandler
    public BikeStatus findOne(FindBikeById query) {
        return bikeStatusRepository.findById(query.bikeId()).orElse(null);
    }
}
```

##### What changed

- `org.axonframework.queryhandling.QueryHandler` → `org.axonframework.messaging.queryhandling.annotation.QueryHandler`
- Everything else: unchanged.

---

### 02 — Blocking `.get()` call: prefer async upgrade; fallback to `.orTimeout().join()` when constrained

**Why this case is interesting:** AF4 code often calls `.get()` on the `CompletableFuture` returned by `queryGateway.query(...)`. AF5 still returns `CompletableFuture<R>`, so the preferred fix is to stop blocking entirely — change the method return type to `CompletableFuture<R>` and return the future directly. The `.orTimeout().join()` pattern is a fallback only when the method signature is truly constrained by a sync framework contract.

**Apply-condition:** `$SOURCE` has bare `.get()` or `.join()` without `.orTimeout(...)` on a `queryGateway.query(...)` result.

---

##### Path A — Method can return `CompletableFuture<R>` (preferred)

Use when the method is a plain service method, Spring MVC endpoint, or any caller whose signature is not locked to a sync return by an external framework contract.

###### Before (AF4)

```java
package com.example.dwellings;

import org.axonframework.queryhandling.QueryGateway;
import org.springframework.stereotype.Component;

@Component
class DwellingsQueryService {

    private final QueryGateway queryGateway;

    DwellingsQueryService(QueryGateway queryGateway) {
        this.queryGateway = queryGateway;
    }

    DwellingReadModel getDwelling(String dwellingId) {
        try {
            return queryGateway.query(new GetDwellingById(dwellingId), DwellingReadModel.class).get();
        } catch (Exception e) {
            throw new RuntimeException("Query failed", e);
        }
    }
}
```

###### After (AF5 — preferred)

```java
package com.example.dwellings;

import org.axonframework.messaging.queryhandling.gateway.QueryGateway;
import org.springframework.stereotype.Component;

import java.util.concurrent.CompletableFuture;

@Component
class DwellingsQueryService {

    private final QueryGateway queryGateway;

    DwellingsQueryService(QueryGateway queryGateway) {
        this.queryGateway = queryGateway;
    }

    CompletableFuture<DwellingReadModel> getDwelling(String dwellingId) {
        return queryGateway.query(new GetDwellingById(dwellingId), DwellingReadModel.class);
    }
}
```

###### What changed

- AF4 import → AF5 import.
- Method return type `DwellingReadModel` → `CompletableFuture<DwellingReadModel>`.
- `import java.util.concurrent.CompletableFuture;` added.
- Body simplified: return the future directly — no `.get()`, no try-catch.

---

##### Path B — Method signature constrained to sync return (fallback)

Use only when the method implements a sync contract that cannot be changed: a sync interface method, `@KafkaListener`, `@JmsListener`, MCP `SyncResourceSpecification` lambda, Camel route step, `CommandLineRunner.run(...)`, `@Scheduled void`, `main(String[])`.

###### Before (AF4)

```java
// implements SomeSyncInterface { SomeResult fetchResult(String id); }
@Override
public SomeResult fetchResult(String id) {
    try {
        return queryGateway.query(new GetSomething(id), SomeResult.class).get();
    } catch (Exception e) {
        throw new RuntimeException(e);
    }
}
```

###### After (AF5 — sync-constrained fallback)

```java
import java.util.concurrent.TimeUnit;

@Override
public SomeResult fetchResult(String id) {
    try {
        return queryGateway.query(new GetSomething(id), SomeResult.class)
                .orTimeout(30, TimeUnit.SECONDS)
                .join();
    } catch (Exception e) {
        throw new RuntimeException(e);
    }
}
```

###### What changed

- AF4 import → AF5 import.
- `.get()` → `.orTimeout(30, TimeUnit.SECONDS).join()`.
- `import java.util.concurrent.TimeUnit;` added.
- The existing `catch (Exception e)` still catches `CompletionException` (unchecked, extends `RuntimeException`).

---

##### Caveats

- **Never use `.orTimeout().join()` when the method can go async.** It is a fallback for genuinely constrained callers, not a universal fix.
- **30-second timeout is a default.** Shorten when the surrounding framework has a tighter SLA.
- **Callers of the migrated method** (Path A) will need to handle `CompletableFuture<R>` — check that callers compile after the return type change.

---

### 02 — Named query removal: queryName attribute → payload record

**Why this case is interesting:** AF4 used string-based `queryName` routing (`@QueryHandler(queryName = "findAll")`). AF5 routes exclusively by the first method parameter type — the payload class IS the routing key. Every handler with `queryName` must receive a dedicated payload record, and every bare-param or no-param handler signature must be updated.

**Apply-condition:** `$SOURCE` has any `@QueryHandler(queryName = "…")`.

---

##### Before (AF4) — from bike-rental-extended

```java
package io.axoniq.demo.bikerental.rental.query;

import org.axonframework.queryhandling.QueryHandler;
import org.springframework.stereotype.Component;

@Component
public class RentalBikeQueryProjection {

    private final BikeStatusRepository bikeStatusRepository;

    public RentalBikeQueryProjection(BikeStatusRepository bikeStatusRepository) {
        this.bikeStatusRepository = bikeStatusRepository;
    }

    @QueryHandler(queryName = "findAll")
    public Iterable<BikeStatus> findAll() {
        return bikeStatusRepository.findAll();
    }

    @QueryHandler(queryName = "findAvailable")
    public Iterable<BikeStatus> findAvailable(String bikeType) {
        return bikeStatusRepository.findAllByBikeTypeAndStatus(bikeType, RentalStatus.AVAILABLE);
    }

    @QueryHandler(queryName = "findOne")
    public BikeStatus findOne(String bikeId) {
        return bikeStatusRepository.findById(bikeId).orElse(null);
    }
}
```

##### After (AF5)

```java
package io.axoniq.demo.bikerental.rental.query;

import org.axonframework.messaging.queryhandling.annotation.Query;
import org.axonframework.messaging.queryhandling.annotation.QueryHandler;
import org.springframework.stereotype.Component;

@Component
public class RentalBikeQueryProjection {

    private final BikeStatusRepository bikeStatusRepository;

    public RentalBikeQueryProjection(BikeStatusRepository bikeStatusRepository) {
        this.bikeStatusRepository = bikeStatusRepository;
    }

    @QueryHandler
    public Iterable<BikeStatus> findAll(FindAllQuery ignored) {
        return bikeStatusRepository.findAll();
    }

    @QueryHandler
    public Iterable<BikeStatus> findAvailable(FindAvailableQuery query) {
        return bikeStatusRepository.findAllByBikeTypeAndStatus(query.bikeType(), RentalStatus.AVAILABLE);
    }

    @QueryHandler
    public BikeStatus findOne(FindOneQuery query) {
        return bikeStatusRepository.findById(query.bikeId()).orElse(null);
    }

}
```

**Separate query class files** (in the project's query API package, e.g. `rental/api/`):

```java
@Query(name = "findAll")
public record FindAllQuery() {}

@Query(name = "findAvailable")
public record FindAvailableQuery(String bikeType) {}

@Query(name = "findOne")
public record FindOneQuery(String bikeId) {}
```

> These records are **not** inner classes of `RentalBikeQueryProjection`. They live in a shared API package so both the handler and the dispatch site (query-gateway recipe) can reference them.

##### What changed

- `@QueryHandler(queryName = "…")` → `@QueryHandler` (attribute removed on all three methods).
- `org.axonframework.queryhandling.QueryHandler` → `org.axonframework.messaging.queryhandling.annotation.QueryHandler`.
- `org.axonframework.messaging.queryhandling.annotation.Query` import added.
- Three payload records introduced as inner records: `FindAllQuery`, `FindAvailableQuery`, `FindOneQuery`.
- Each record carries `@Query(name = "…")` matching the original AF4 `queryName` string (case-sensitive matching required; "FindAllQuery" ≠ "findAll" so annotation is mandatory).
- `findAll()` no-param → `findAll(FindAllQuery ignored)` — marker record as required first parameter.
- `findAvailable(String bikeType)` → `findAvailable(FindAvailableQuery query)` — bare scalar wrapped; body updated `bikeType` → `query.bikeType()`.
- `findOne(String bikeId)` → `findOne(FindOneQuery query)` — same pattern; `bikeId` → `query.bikeId()`.

##### Caveats

- **Dispatch side coupling**: The `queryGateway.query("findAll", ...)` calls elsewhere MUST also be updated (query-gateway recipe, use-case 04). Handler and dispatch sides must agree on payload class.
- **@Query annotation omittable if names match**: If the record simple name happens to equal the AF4 queryName string exactly (case-sensitive), `@Query` is not required. In practice this rarely happens because Java class names are typically PascalCase while AF4 query names were camelCase.
- **Records must be top-level**: Always create query records as separate top-level classes in the project's query API package — never as inner classes of the handler. They are shared API used by both handler and dispatch sides.

---

### 03 — QueryUpdateEmitter: constructor injection → method parameter

**Why this case is interesting:** AF4 `QueryUpdateEmitter` was a Spring-managed bean injected via constructor. AF5 injects it as a method-level parameter directly into each `@EventHandler` method that emits updates. Additionally, the `emit()` signature changed from a 2-arg form (predicate on `QueryMessage`) to a 3-arg form (query payload class + predicate on payload + update).

**Apply-condition:** `$SOURCE` has `QueryUpdateEmitter` as a constructor dependency.

---

##### Before (AF4) — from bike-rental-extended

```java
package io.axoniq.demo.bikerental.rental.query;

import org.axonframework.eventhandling.EventHandler;
import org.axonframework.queryhandling.QueryHandler;
import org.axonframework.queryhandling.QueryUpdateEmitter;
import org.springframework.stereotype.Component;

@Component
public class BikeStatusSubscriptionProjection {

    private final BikeStatusRepository bikeStatusRepository;
    private final QueryUpdateEmitter updateEmitter;

    public BikeStatusSubscriptionProjection(BikeStatusRepository bikeStatusRepository,
                                            QueryUpdateEmitter updateEmitter) {
        this.bikeStatusRepository = bikeStatusRepository;
        this.updateEmitter = updateEmitter;
    }

    @EventHandler
    public void on(BikeRegisteredEvent event) {
        var bikeStatus = new BikeStatus(event.getBikeId(), event.getBikeType(), event.getLocation());
        bikeStatusRepository.save(bikeStatus);
        updateEmitter.emit(q -> "findAll".equals(q.getQueryName()), bikeStatus);
    }

    @QueryHandler
    public Iterable<BikeStatus> findAll(FindAllBikes query) {
        return bikeStatusRepository.findAll();
    }
}
```

##### After (AF5)

```java
package io.axoniq.demo.bikerental.rental.query;

import org.axonframework.messaging.eventhandling.annotation.EventHandler;
import org.axonframework.messaging.queryhandling.QueryUpdateEmitter;
import org.axonframework.messaging.queryhandling.annotation.QueryHandler;
import org.springframework.stereotype.Component;

@Component
public class BikeStatusSubscriptionProjection {

    private final BikeStatusRepository bikeStatusRepository;

    public BikeStatusSubscriptionProjection(BikeStatusRepository bikeStatusRepository) {
        this.bikeStatusRepository = bikeStatusRepository;
    }

    @EventHandler
    public void on(BikeRegisteredEvent event, QueryUpdateEmitter updateEmitter) {
        var bikeStatus = new BikeStatus(event.bikeId(), event.bikeType(), event.location());
        bikeStatusRepository.save(bikeStatus);
        updateEmitter.emit(FindAllBikes.class, q -> true, bikeStatus);
    }

    @QueryHandler
    public Iterable<BikeStatus> findAll(FindAllBikes query) {
        return bikeStatusRepository.findAll();
    }
}
```

##### What changed

- `private final QueryUpdateEmitter updateEmitter` field removed.
- Constructor: `QueryUpdateEmitter updateEmitter` param removed; body assignment removed.
- `@EventHandler on(BikeRegisteredEvent event)` → `on(BikeRegisteredEvent event, QueryUpdateEmitter updateEmitter)` — QUE injected as method param.
- `updateEmitter.emit(q -> "findAll".equals(q.getQueryName()), bikeStatus)` (2-arg) → `updateEmitter.emit(FindAllBikes.class, q -> true, bikeStatus)` (3-arg).
  - First arg: query payload class (`FindAllBikes.class`) identifies which subscription query to update.
  - Second arg: predicate now receives the payload `FindAllBikes q` directly (not the `QueryMessage` envelope). Use `q -> true` when all subscribers of that query type should receive the update; use a narrowing predicate (e.g. `q -> q.bikeId().equals(event.bikeId())`) for targeted updates.
- Imports updated:
  - `org.axonframework.queryhandling.QueryUpdateEmitter` → `org.axonframework.messaging.queryhandling.QueryUpdateEmitter`
  - `org.axonframework.eventhandling.EventHandler` → `org.axonframework.messaging.eventhandling.annotation.EventHandler` (fixed on touched method)
  - `org.axonframework.queryhandling.QueryHandler` → `org.axonframework.messaging.queryhandling.annotation.QueryHandler`

##### Caveats

- **Predicate parameter type change**: AF4 predicate `Predicate<QueryMessage<Q,?>>` receives the full message envelope. AF5 predicate `Predicate<Q>` receives the payload directly. Rewrite any predicate that accessed message-level fields like `q.getQueryName()`, `q.getMetaData()`.
- **Multiple @EventHandler methods**: If multiple event handlers emit updates, each gets a `QueryUpdateEmitter updateEmitter` parameter independently.
- **@EventHandler import side effect**: This recipe fixes `@EventHandler` import only on methods physically modified for QUE injection. Untouched @EventHandler methods retain their AF4 imports — event-processor recipe handles those.

---

### 03 — ResponseType wrapper removal + `queryMany`

**Why this case is interesting:** AF4 required wrapping response types in `ResponseTypes.instanceOf(R.class)` / `multipleInstancesOf(R.class)`. AF5 removed this SPI entirely. The `multipleInstancesOf` case is a double change: remove wrapper AND rename method to `queryMany`.

**Apply-condition:** `$SOURCE` uses `ResponseTypes.instanceOf(...)` / `multipleInstancesOf(...)` / `optionalInstanceOf(...)`.

##### Before (AF4)

```java
package com.example.bikes.api;

import com.example.bikes.query.BikeStatus;
import org.axonframework.messaging.responsetypes.ResponseTypes;
import org.axonframework.queryhandling.QueryGateway;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.concurrent.CompletableFuture;

@RestController
@RequestMapping("/bikes")
class BikeStatusController {

    private final QueryGateway queryGateway;

    BikeStatusController(QueryGateway queryGateway) {
        this.queryGateway = queryGateway;
    }

    @GetMapping("/{bikeId}")
    CompletableFuture<BikeStatus> findOne(@PathVariable String bikeId) {
        return queryGateway.query(
                new FindBikeById(bikeId),
                ResponseTypes.instanceOf(BikeStatus.class)
        );
    }

    @GetMapping
    CompletableFuture<List<BikeStatus>> findAll() {
        return queryGateway.query(
                new FindAllBikes(),
                ResponseTypes.multipleInstancesOf(BikeStatus.class)
        );
    }
}
```

##### After (AF5)

```java
package com.example.bikes.api;

import com.example.bikes.query.BikeStatus;
import org.axonframework.messaging.queryhandling.gateway.QueryGateway;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.concurrent.CompletableFuture;

@RestController
@RequestMapping("/bikes")
class BikeStatusController {

    private final QueryGateway queryGateway;

    BikeStatusController(QueryGateway queryGateway) {
        this.queryGateway = queryGateway;
    }

    @GetMapping("/{bikeId}")
    CompletableFuture<BikeStatus> findOne(@PathVariable String bikeId) {
        return queryGateway.query(new FindBikeById(bikeId), BikeStatus.class);
    }

    @GetMapping
    CompletableFuture<List<BikeStatus>> findAll() {
        return queryGateway.queryMany(new FindAllBikes(), BikeStatus.class);
    }
}
```

##### What changed

- AF4 import → AF5 import.
- `import org.axonframework.messaging.responsetypes.ResponseTypes;` removed.
- `ResponseTypes.instanceOf(BikeStatus.class)` → `BikeStatus.class`.
- `query(..., ResponseTypes.multipleInstancesOf(BikeStatus.class))` → `queryMany(..., BikeStatus.class)`.
- Method return types unchanged (`CompletableFuture<BikeStatus>`, `CompletableFuture<List<BikeStatus>>`).

##### Caveats

- `query(...)` is **always single-response** in AF5. Any AF4 site using `multipleInstancesOf` MUST use `queryMany(...)` — using `query(...)` with a `Class<R>` would compile but return only the first result.
- `optionalInstanceOf(R.class)` → `query(payload, R.class)`. The future resolves to `null` if no result — callers must handle null.
- Custom `ResponseType` subclass in the project → Blocker B2; do not attempt to strip mechanically.

---

### 04 — Named query: string dispatch → `@Query`-annotated payload class

**Why this case is interesting:** AF4's named-query overload `query("name", payload, ResponseType)` is removed in AF5. The correct migration is NOT to construct `GenericQueryMessage` — it is to move the name onto the payload class via `@Query(name = "…")`. When payload was a bare scalar, a new record must be introduced, which also requires a coupled handler-side parameter-type change.

**Apply-condition:** `$SOURCE` has `queryGateway.query("name", payload, …)` or `queryGateway.queryMany("name", payload, …)` calls.

##### Two sub-cases

###### A — Payload class already exists (annotation-only)

Payload classes (`FindOneBike`, `FindAllBikes`) already exist as dedicated records. Only `@Query` annotation added; handler signatures unchanged.

**Before (AF4 dispatch):**
```java
import org.axonframework.messaging.responsetypes.ResponseTypes;
import org.axonframework.queryhandling.QueryGateway;

@GetMapping("/bikes")
public CompletableFuture<List<BikeStatus>> findAll() {
    return queryGateway.query("findAll", new FindAllBikes(), ResponseTypes.multipleInstancesOf(BikeStatus.class));
}

@GetMapping("/bikes/{bikeId}")
public CompletableFuture<BikeStatus> findOne(@PathVariable String bikeId) {
    return queryGateway.query("findOne", new FindOneBike(bikeId), BikeStatus.class);
}
```

**Before (payload classes):**
```java
public record FindAllBikes() {}
public record FindOneBike(String bikeId) {}
```

**After (AF5 dispatch):**
```java
import org.axonframework.messaging.queryhandling.gateway.QueryGateway;

@GetMapping("/bikes")
public CompletableFuture<List<BikeStatus>> findAll() {
    return queryGateway.queryMany(new FindAllBikes(), BikeStatus.class);
}

@GetMapping("/bikes/{bikeId}")
public CompletableFuture<BikeStatus> findOne(@PathVariable String bikeId) {
    return queryGateway.query(new FindOneBike(bikeId), BikeStatus.class);
}
```

**After (payload classes):**
```java
import org.axonframework.messaging.queryhandling.annotation.Query;

@Query(name = "findAll")
public record FindAllBikes() {}

@Query(name = "findOne")
public record FindOneBike(String bikeId) {}
```

Handler-side `@QueryHandler(queryName = "findAll")` stays unchanged — routing matches via `@Query(name = "findAll")`.

###### B — Bare scalar payload (introduce record + handler edit)

**Before (AF4):**
```java
// dispatch
queryGateway.query("getStatus", paymentId, PaymentStatus.class)

// handler
@QueryHandler(queryName = "getStatus")
public PaymentStatus getStatus(String paymentId) { ... }
```

**After (AF5):**
```java
// new payload record
import org.axonframework.messaging.queryhandling.annotation.Query;

@Query(name = "getStatus")
public record GetPaymentStatusQuery(String paymentId) {}

// dispatch
queryGateway.query(new GetPaymentStatusQuery(paymentId), PaymentStatus.class)

// handler (coupled edit — in scope)
@QueryHandler(queryName = "getStatus")
public PaymentStatus getStatus(GetPaymentStatusQuery query) {
    return ... query.paymentId() ...;
}
```

##### Caveats

- **`@Query.name()` must match AF4 string exactly.** The default is the simple class name; AF4 names almost never match. Always set `name` explicitly.
- **`queryMany` for `multipleInstancesOf`.** The named-form `query("findAll", ...)` with `multipleInstancesOf` becomes `queryMany(new FindAllBikes(), R.class)`.
- **Never construct `GenericQueryMessage` at dispatch sites** to "preserve" the name. This scatters routing keys across dispatch sites instead of centralising them on the payload class.
- **Handler-side edit is in scope only when payload class changes** (scalar → record). When payload was already a dedicated class, only the `@Query` annotation is added — handlers unchanged.

---

### 04 — @ProcessingGroup → @Namespace and @MetaDataValue → @MetadataValue

**Why this case is interesting:** Heroes-of-DDD and similar projects annotate query handler classes with `@ProcessingGroup` for grouping, and use `@MetaDataValue` for injecting metadata into handler method parameters. Both annotation names and packages changed in AF5.

**Apply-condition:** `$SOURCE` has `@ProcessingGroup` or `@MetaDataValue` (or both).

---

##### Before (AF4) — from heroes-of-ddd

```java
package com.dddheroes.heroesofddd.creaturerecruitment.read.getalldwellings;

import org.axonframework.config.ProcessingGroup;
import org.axonframework.eventhandling.EventHandler;
import org.axonframework.messaging.annotation.MetaDataValue;
import org.axonframework.queryhandling.QueryHandler;
import org.springframework.stereotype.Component;

@ProcessingGroup("Read_GetAllDwellings_QueryCache")
@Component
class GetAllDwellingsQueryHandler {

    private final DwellingReadModelRepository dwellingReadModelRepository;

    GetAllDwellingsQueryHandler(DwellingReadModelRepository dwellingReadModelRepository) {
        this.dwellingReadModelRepository = dwellingReadModelRepository;
    }

    @QueryHandler
    GetAllDwellings.Result handle(GetAllDwellings query) {
        var dwellings = dwellingReadModelRepository.findAllByGameId(query.gameId());
        return new GetAllDwellings.Result(dwellings);
    }

    @EventHandler
    void evolve(DwellingBuilt event, @MetaDataValue("gameId") String gameId) {
        var item = new DwellingReadModel(gameId, event.dwellingId(), event.creatureId(), event.costPerTroop(), 0);
        dwellingReadModelRepository.save(item);
    }
}
```

##### After (AF5)

```java
package com.dddheroes.heroesofddd.creaturerecruitment.read.getalldwellings;

import org.axonframework.messaging.core.annotation.Namespace;
import org.axonframework.messaging.core.annotation.MetadataValue;
import org.axonframework.messaging.eventhandling.annotation.EventHandler;
import org.axonframework.messaging.queryhandling.annotation.QueryHandler;
import org.springframework.stereotype.Component;

@Namespace("Read_GetAllDwellings_QueryCache")
@Component
class GetAllDwellingsQueryHandler {

    private final DwellingReadModelRepository dwellingReadModelRepository;

    GetAllDwellingsQueryHandler(DwellingReadModelRepository dwellingReadModelRepository) {
        this.dwellingReadModelRepository = dwellingReadModelRepository;
    }

    @QueryHandler
    GetAllDwellings.Result handle(GetAllDwellings query) {
        var dwellings = dwellingReadModelRepository.findAllByGameId(query.gameId());
        return new GetAllDwellings.Result(dwellings);
    }

    @EventHandler
    void evolve(DwellingBuilt event, @MetadataValue("gameId") String gameId) {
        var item = new DwellingReadModel(gameId, event.dwellingId(), event.creatureId(), event.costPerTroop(), 0);
        dwellingReadModelRepository.save(item);
    }
}
```

##### What changed

- `@ProcessingGroup("Read_GetAllDwellings_QueryCache")` → `@Namespace("Read_GetAllDwellings_QueryCache")`.
  - Remove `org.axonframework.config.ProcessingGroup`.
  - Add `org.axonframework.messaging.core.annotation.Namespace`.
- `@MetaDataValue("gameId")` → `@MetadataValue("gameId")` (capital D removed; same key string).
  - Remove `org.axonframework.messaging.annotation.MetaDataValue`.
  - Add `org.axonframework.messaging.core.annotation.MetadataValue`.
- `@QueryHandler` import: `org.axonframework.queryhandling.QueryHandler` → `org.axonframework.messaging.queryhandling.annotation.QueryHandler`.
- `@EventHandler` import also updated here since the method is being touched: `org.axonframework.eventhandling.EventHandler` → `org.axonframework.messaging.eventhandling.annotation.EventHandler`.
- Method bodies and logic: unchanged.

##### Caveats

- **`MetaData` type rename**: If `MetaData` appears as a parameter type (not just the annotation), it also renames to `Metadata` with new import `org.axonframework.messaging.core.Metadata`.
- **Namespace value preserved verbatim**: Copy the string from `@ProcessingGroup` exactly — it controls event processor thread pool assignment in AF5.

---

### 05 — Rejected: handler class with `QueryGateway` field

**Why this case is interesting:** A class injects `QueryGateway` as a field AND has handler annotations (`@EventHandler`, `@QueryHandler`, etc.). It looks like a candidate at first glance — it imports `QueryGateway`. But the handler annotations make it a message-handling component, NOT a top-of-chain caller. The query-gateway recipe must reject it and route to the appropriate handler recipe.

**Apply-condition:** `$SOURCE` has any method annotated `@EventHandler` / `@CommandHandler` / `@QueryHandler` / `@SagaEventHandler` / `@MessageHandlerInterceptor` (predicate 2 fires).

##### Example (AF4 source — NOT touched by this recipe)

```java
package com.example.automation;

import com.example.queries.GetInventoryStatus;
import com.example.commands.ReserveInventoryCommand;
import org.axonframework.commandhandling.gateway.CommandGateway;
import org.axonframework.queryhandling.QueryGateway;
import org.axonframework.config.ProcessingGroup;
import org.axonframework.eventhandling.EventHandler;
import org.springframework.stereotype.Component;

@Component
@ProcessingGroup("Automation_Inventory")
class WhenOrderPlacedCheckInventoryProcessor {

    private final QueryGateway queryGateway;  // <-- has QueryGateway
    private final CommandGateway commandGateway;

    WhenOrderPlacedCheckInventoryProcessor(QueryGateway queryGateway, CommandGateway commandGateway) {
        this.queryGateway = queryGateway;
        this.commandGateway = commandGateway;
    }

    @EventHandler   // <-- this triggers Applicable predicate 2
    public void on(OrderPlacedEvent event) {
        // in-handler query dispatch
        var status = queryGateway.query(new GetInventoryStatus(event.itemId()), InventoryStatus.class).join();
        if (status.hasStock()) {
            commandGateway.sendAndWait(new ReserveInventoryCommand(event.orderId(), event.itemId()));
        }
    }
}
```

##### Expected result

The query-gateway recipe returns Rejected immediately. The source is untouched.

```
return REJECTED

> **Result:** ⏭️ Rejected
> **Source:** `com.example.automation.WhenOrderPlacedCheckInventoryProcessor`
> **Recipe:** axon4to5-query-gateway
>
> **Notes:** Applicable predicate 2 failed — class has `@EventHandler` methods. This is an event-handling component, not a top-of-chain caller. Route to the event-processor recipe; it owns in-handler query and command dispatch.
```

##### What changed

Nothing — the recipe did not touch the file.

##### Caveats

- **The event-processor recipe owns in-handler dispatch** — both `QueryGateway` and `CommandGateway` inside a handler are migrated by the event-processor recipe (Step 4).
- **Do NOT swap the `QueryGateway` import to AF5** in this class from inside this recipe. If you partially migrate the import and leave the class, the event-processor recipe will find inconsistent state. Leave the class fully untouched.
- **Mixed class (some methods are handlers, some are top-of-chain callers)**: run the handler recipe first; the query-gateway recipe can touch non-handler call sites on follow-up only after handler migration is complete.

---

### 05 — Rejected: class with no @QueryHandler

**Why this case is interesting:** A class that dispatches queries via `QueryGateway` but has no `@QueryHandler` method looks superficially related to query handling but falls outside the scope of this recipe. The correct recipe is query-gateway.

**Apply-condition:** `$SOURCE` has `QueryGateway` dependency but no `@QueryHandler` annotation.

---

##### Example — pure query dispatcher (AF4)

```java
package com.example.payment.service;

import org.axonframework.queryhandling.QueryGateway;
import org.springframework.stereotype.Service;
import java.util.concurrent.CompletableFuture;

@Service
public class PaymentDispatchService {

    private final QueryGateway queryGateway;

    public PaymentDispatchService(QueryGateway queryGateway) {
        this.queryGateway = queryGateway;
    }

    public CompletableFuture<PaymentStatus> getStatus(String paymentId) {
        return queryGateway.query(new GetPaymentStatus(paymentId), PaymentStatus.class);
    }
}
```

##### Expected result

The query-handler recipe evaluates Applicable predicate 4 (no `@QueryHandler`) → **Rejected**.

```
**Result:** ⏭️ Rejected
**Recipe:** axon4to5-query-handler
**Reason:** no-query-handler — $SOURCE dispatches queries but declares no @QueryHandler methods.
Consider the query-gateway recipe for this class.
```

Source file is NOT modified.

##### Routing

| Observation | Recipe |
|---|---|
| `@QueryHandler` on methods | query-handler (this recipe) |
| `QueryGateway` field, no `@QueryHandler` | query-gateway |
| `@SagaEventHandler` | saga recipe |

---

## sagas

### Use case 01 — JPA state shape (Spring, no deadlines)

**Why interesting:** demonstrates full structural rewrite of an AF4 `@Saga` to `@Component @DisallowReplay` with JPA-backed state. Shows that three things change together: the saga class itself, a new state entity, and a new repository. No deadline handling in this case.

##### Before (AF4)

```java
@Saga
public class PaymentSaga {

    @Autowired private transient CommandGateway commandGateway;

    private String bikeId;
    private String renter;

    @StartSaga
    @SagaEventHandler(associationProperty = "bikeId")
    public void on(BikeRequestedEvent event) {
        this.bikeId = event.bikeId();
        this.renter = event.renter();
        SagaLifecycle.associateWith("paymentReference", event.rentalReference());
        commandGateway.send(new PreparePaymentCommand(10, event.rentalReference()));
    }

    @EndSaga
    @SagaEventHandler(associationProperty = "paymentReference")
    public void on(PaymentConfirmedEvent event) {
        commandGateway.send(new ApproveRequestCommand(bikeId, renter));
    }

    @EndSaga
    @SagaEventHandler(associationProperty = "paymentReference")
    public void on(PaymentRejectedEvent event) {
        commandGateway.send(new RejectRequestCommand(bikeId, renter));
    }
}
```

##### After (AF5)

###### PaymentSaga.java (rewritten)

```java
import org.axonframework.messaging.commandhandling.gateway.CommandDispatcher;
import org.axonframework.messaging.commandhandling.gateway.CommandGateway;
import org.axonframework.messaging.eventhandling.annotation.EventHandler;
import org.axonframework.messaging.eventhandling.replay.annotation.DisallowReplay;
import org.springframework.stereotype.Component;

@Component
@DisallowReplay
public class PaymentSaga {

    private final PaymentStateRepository repository;

    public PaymentSaga(PaymentStateRepository repository) {
        this.repository = repository;
    }

    @EventHandler
    public void on(BikeRequestedEvent event, CommandDispatcher commandDispatcher) {
        repository.save(new PaymentState(event.rentalReference(), event.bikeId(), event.renter()));
        commandDispatcher.send(new PreparePaymentCommand(10, event.rentalReference()));
    }

    @EventHandler
    public void on(PaymentConfirmedEvent event, CommandDispatcher commandDispatcher) {
        repository.findById(event.paymentReference()).ifPresent(state -> {
            state.setStatus(PaymentState.Status.CONFIRMED);
            commandDispatcher.send(new ApproveRequestCommand(state.bikeId(), state.renter()));
        });
    }

    @EventHandler
    public void on(PaymentRejectedEvent event, CommandDispatcher commandDispatcher) {
        repository.findById(event.paymentReference()).ifPresent(state -> {
            state.setStatus(PaymentState.Status.REJECTED);
            commandDispatcher.send(new RejectRequestCommand(state.bikeId(), state.renter()));
        });
    }
}
```

###### PaymentState.java (new file — same package)

```java
import jakarta.persistence.Entity;
import jakarta.persistence.Id;

@Entity
public class PaymentState {

    @Id
    private String paymentReference;
    private String bikeId;
    private String renter;
    private Status status;
    private long timestamp;

    public PaymentState() {}

    public PaymentState(String paymentReference, String bikeId, String renter) {
        this.paymentReference = paymentReference;
        this.bikeId = bikeId;
        this.renter = renter;
        this.status = Status.PENDING;
        this.timestamp = System.currentTimeMillis();
    }

    public String paymentReference() { return paymentReference; }
    public String bikeId() { return bikeId; }
    public String renter() { return renter; }
    public Status status() { return status; }
    public void setStatus(Status status) { this.status = status; }

    public enum Status { PENDING, CONFIRMED, REJECTED }
}
```

###### PaymentStateRepository.java (new file — same package)

```java
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface PaymentStateRepository extends JpaRepository<PaymentState, String> {
    List<PaymentState> findAllByTimestampLessThanAndStatusIn(long timestamp, PaymentState.Status... status);
}
```

##### What changed

- `@Saga` → `@Component @DisallowReplay`
- Saga fields (`bikeId`, `renter`) → fields in `PaymentState` entity
- `@StartSaga @SagaEventHandler(associationProperty = "bikeId")` → `@EventHandler` saves a new `PaymentState` row (the `paymentReference` / correlation key becomes the JPA `@Id`)
- `SagaLifecycle.associateWith("paymentReference", value)` → implicit: the state entity is looked up by the correlation key (`event.paymentReference()`)
- `@EndSaga @SagaEventHandler(...)` → `@EventHandler` updates state status (or deletes row)
- `CommandGateway` field removed; `CommandDispatcher commandDispatcher` added as method parameter on each `@EventHandler`
- Two new files created: `PaymentState.java` (`@Entity`) and `PaymentStateRepository.java` (`JpaRepository`)

##### Caveats

- Processor wiring: the migrated `@Component` must be registered as an event processor. For Spring, add a `@Bean EventProcessorDefinition` in the `@Configuration` class (see `projectors-event-processors.adoc`). Without it, the handlers are auto-assigned to the default processor which may conflict with other components.
- `@DisallowReplay` prevents double-processing of state-creating handlers during event replay. Required.
- The JPA entity needs a no-arg constructor for Hibernate (add `public PaymentState() {}`).
- `CommandDispatcher` is injected per-handler by the framework via `ProcessingContext`. Not available in `@Scheduled` methods — use `CommandGateway` field there.

---

### Use case 02 — DeadlineManager → Blocker with partial migration (comment out)

**Why interesting:** AF5 has no `DeadlineManager`. The recipe migrates the full saga structure (class, event handlers, state entity, repository) but cannot design the deadline replacement — that is a project-specific decision. Deadline code is commented out with TODO markers, and Blocker B1 is emitted so the caller can choose the replacement strategy.

##### Before (AF4) — deadline-bearing saga

```java
@Saga
public class PaymentSagaWithDeadline {

    @Autowired private transient CommandGateway commandGateway;
    @Autowired private transient DeadlineManager deadlineManager;

    private String bikeId;
    private String renter;

    @StartSaga
    @SagaEventHandler(associationProperty = "bikeId")
    public void on(BikeRequestedEvent event) {
        this.bikeId = event.bikeId();
        this.renter = event.renter();
        SagaLifecycle.associateWith("paymentReference", event.rentalReference());
        commandGateway.send(new PreparePaymentCommand(10, event.rentalReference()));
    }

    @SagaEventHandler(associationProperty = "paymentReference")
    public void on(PaymentPreparedEvent event) {
        deadlineManager.schedule(Duration.ofSeconds(30), "cancelPayment", event.paymentId());
    }

    @EndSaga
    @SagaEventHandler(associationProperty = "paymentReference")
    public void on(PaymentConfirmedEvent event) {
        commandGateway.send(new ApproveRequestCommand(bikeId, renter));
    }

    @DeadlineHandler(deadlineName = "cancelPayment")
    public void cancelPayment(String paymentId) {
        commandGateway.send(new RejectPaymentCommand(paymentId));
    }
}
```

##### After (AF5) — partial migration, deadline code commented out

```java
import org.axonframework.messaging.commandhandling.gateway.CommandDispatcher;
import org.axonframework.messaging.commandhandling.gateway.CommandGateway;
import org.axonframework.messaging.eventhandling.annotation.EventHandler;
import org.axonframework.messaging.eventhandling.replay.annotation.DisallowReplay;
import org.springframework.stereotype.Component;
// import org.axonframework.deadline.DeadlineManager;            // TODO AF5: removed — no equivalent
// import org.axonframework.deadline.annotation.DeadlineHandler; // TODO AF5: removed — no equivalent

@Component
@DisallowReplay
public class PaymentSagaWithDeadline {

    private final CommandGateway commandGateway;
    private final PaymentSagaWithDeadlineStateRepository repository;

    // TODO AF5: DeadlineManager removed — design replacement (e.g. @Scheduled poller on state entity)
    // private transient DeadlineManager deadlineManager;

    public PaymentSagaWithDeadline(CommandGateway commandGateway,
                                   PaymentSagaWithDeadlineStateRepository repository) {
        this.commandGateway = commandGateway;
        this.repository = repository;
    }

    @EventHandler
    public void on(BikeRequestedEvent event, CommandDispatcher commandDispatcher) {
        repository.save(new PaymentSagaWithDeadlineState(event.rentalReference(), event.bikeId(), event.renter()));
        commandDispatcher.send(new PreparePaymentCommand(10, event.rentalReference()));
    }

    @EventHandler
    public void on(PaymentPreparedEvent event) {
        repository.findById(event.paymentReference())
                  .ifPresent(state -> {
                      state.setStatus(PaymentSagaWithDeadlineState.Status.PREPARED);
                      // TODO AF5: schedule 30s deadline — deadlineManager.schedule(...) removed
                      // deadlineManager.schedule(Duration.ofSeconds(30), "cancelPayment", event.paymentId());
                  });
    }

    @EventHandler
    public void on(PaymentConfirmedEvent event, CommandDispatcher commandDispatcher) {
        repository.findById(event.paymentReference())
                  .ifPresent(state -> {
                      state.setStatus(PaymentSagaWithDeadlineState.Status.CONFIRMED);
                      commandDispatcher.send(new ApproveRequestCommand(state.bikeId(), state.renter()));
                  });
    }

    // TODO AF5: @DeadlineHandler has no AF5 equivalent — implement as @Scheduled poller or manual scheduler
    // @DeadlineHandler(deadlineName = "cancelPayment")
    // public void cancelPayment(String paymentId) {
    //     commandGateway.send(new RejectPaymentCommand(paymentId));
    // }
}
```

##### What changed

- `@Saga` → `@Component @DisallowReplay` (saga structure fully migrated)
- `@SagaEventHandler` → `@EventHandler` with JPA repository lookup
- `SagaLifecycle.associateWith(...)` → implicit via `repository.save(new ...State(...))`
- `@EndSaga` → `@EventHandler` + `state.setStatus(CONFIRMED)`
- **`DeadlineManager` field commented out** with TODO
- **`deadlineManager.schedule(...)` call commented out** with TODO
- **`@DeadlineHandler` method commented out** with TODO block
- `CommandGateway` field kept (constructor-injected) — needed if caller adds `@Scheduled` poller later
- Two new files created: `PaymentSagaWithDeadlineState.java`, `PaymentSagaWithDeadlineStateRepository.java`
- Recipe emits **Blocker B1** — source is partially migrated; caller decides on deadline replacement

##### What the caller should do next (solve-manually option)

1. Decide on a deadline replacement strategy. Common options:
   - **`@Scheduled` poller** (Spring): add `@Scheduled(fixedDelay = 1000)` method querying `findAllByTimestampLessThanAndStatusIn(cutoff, Status.PREPARED, Status.PENDING)`. Add `@EnableScheduling` to the Spring Boot app.
   - **`ScheduledExecutorService`** (native or Spring): wire manually; same polling logic applies.
2. Uncomment and adapt the TODO-marked blocks.
3. Re-invoke the saga recipe — it will re-check and proceed to Success.

##### Caveats

- `CommandGateway` field is kept because the future `@Scheduled` poller cannot receive `CommandDispatcher` as a method parameter (pollers are not event handlers). This is intentional.
- The state entity already has a `timestamp` field and `findAllByTimestampLessThanAndStatusIn` repository method — ready to be used by the caller's `@Scheduled` poller.
- `DeadlineManager.cancelAllWithinScope(...)` in `@EndSaga` handlers is also commented out. The caller's poller will naturally skip terminal-status rows via `statusIn(PENDING, PREPARED)` predicate.

---

### Use case 03 — Rejected: source is not a saga

**Why interesting:** shows the rejection path when the saga recipe is invoked on a class that is not a saga — typically an aggregate or projector accidentally routed here. Recipe must leave source untouched.

##### Example

`$SOURCE` is `CreatureRecruitmentAggregate.java`, annotated `@Aggregate` with `@EventSourcingHandler` methods. The caller invoked the saga recipe by mistake.

##### Expected outcome

```
return REJECTED

> **Result:** ⏭️ Rejected
> **Source:** `com.example.CreatureRecruitmentAggregate`
> **Recipe:** axon4to5-saga
>
> **Notes:** Applicable predicate failed — class is annotated @Aggregate with @EventSourcingHandler methods. This is an event-sourced aggregate, not a saga. Route to the aggregate recipe instead. No edits made.
```

##### What did NOT happen

- No `@Component` added to the aggregate.
- No `@EventHandler` (AF5) import added.
- No state entity or repository created.
- Source file byte-identical to input.

##### Routing guidance in NOTES

Always name the correct recipe when rejecting:
- `@Aggregate` + `@EventSourcingHandler` → route to **aggregate** recipe
- `@ProcessingGroup` + `@EventHandler` (projector) → route to **event-processor** recipe
- No recognizable Axon 4 marker at all → ask user to clarify

---
