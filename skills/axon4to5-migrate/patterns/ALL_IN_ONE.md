# Axon Framework 4 → 5 Migration Patterns

Automatically generated — do not edit manually. Regenerate with:
```
make generate          # or: python3 scripts/generate_all_in_one.py
```

- [dependencies](#dependencies)
  - [Dependency Migration — Maven / Gradle](#dependency-migration--maven--gradle)
    - [AF4](#af4)
    - [AF5](#af5)
- [aggregates](#aggregates)
  - [Aggregate Class Stereotype](#aggregate-class-stereotype)
  - [AggregateLifecycle.apply() → EventAppender.append()](#aggregatelifecycleapply--eventappenderappend)
  - [@AggregateMember → @EntityMember (Child Entities)](#aggregatemember--entitymember-child-entities)
  - [@CommandHandler — Import Move + EventAppender Parameter](#commandhandler--import-move--eventappender-parameter)
  - [@CreationPolicy Removal](#creationpolicy-removal)
  - [@EntityCreator — No-Arg Constructor Annotation](#entitycreator--no-arg-constructor-annotation)
    - [Find aggregate classes and check their no-arg constructors](#find-aggregate-classes-and-check-their-no-arg-constructors)
  - [Event Class Annotations](#event-class-annotations)
    - [Find event classes (usually records in the events/ package)](#find-event-classes-usually-records-in-the-events-package)
    - [Events without @Event annotation — after OpenRewrite; look for record/class in events packages](#events-without-event-annotation--after-openrewrite-look-for-recordclass-in-events-packages)
  - [Event Emission in Aggregates](#event-emission-in-aggregates)
  - [@EventSourcingHandler — Import Package Move](#eventsourcinghandler--import-package-move)
  - [GenericDomainEventMessage Removal](#genericdomaineventmessage-removal)
  - [@TargetAggregateIdentifier Removal](#targetaggregateidentifier-removal)
- [event handlers](#event-handlers)
  - [In-Handler Command Dispatch — CommandGateway → CommandDispatcher](#in-handler-command-dispatch--commandgateway--commanddispatcher)
    - [Find event-handling classes that inject CommandGateway](#find-event-handling-classes-that-inject-commandgateway)
  - [@EventHandler, @DisallowReplay, @ResetHandler — Import Package Moves](#eventhandler-disallowreplay-resethandler--import-package-moves)
  - [Message Accessor Renames](#message-accessor-renames)
  - [Metadata Type Change](#metadata-type-change)
  - [@MetaDataValue → @MetadataValue](#metadatavalue--metadatavalue)
  - [@ProcessingGroup → @Namespace (Event Processor Routing)](#processinggroup--namespace-event-processor-routing)
  - [Sequencing Policy Migration](#sequencing-policy-migration)
    - [application.yaml](#applicationyaml)
    - [application.yaml — remove sequencing-policy key; mode stays](#applicationyaml--remove-sequencing-policy-key-mode-stays)
- [query handlers](#query-handlers)
  - [@QueryHandler — Import Package Move](#queryhandler--import-package-move)
  - [Named Query — @QueryHandler(queryName) → @Query Payload Record](#named-query--queryhandlerqueryname--query-payload-record)
  - [QueryUpdateEmitter — Constructor Field → Method Parameter](#queryupdateemitter--constructor-field--method-parameter)
- [interceptors](#interceptors)
  - [MessageDispatchInterceptor — handle(List) → interceptOnDispatch](#messagedispatchinterceptor--handlelist--interceptondispatch)
  - [MessageHandlerInterceptor — Handle Method Signature Migration](#messagehandlerinterceptor--handle-method-signature-migration)
- [sagas](#sagas)
  - [Saga Migration — @Saga → @Component @DisallowReplay](#saga-migration--saga--component-disallowreplay)
- [event store](#event-store)
  - [Event Store Configuration — JPA](#event-store-configuration--jpa)
- [tests](#tests)
  - [AggregateTestFixture → AxonTestFixture](#aggregatetestfixture--axontestfixture)

## dependencies

### Dependency Migration — Maven / Gradle

Update project dependencies from Axon Framework 4 to Axon Framework 5. The Maven group ID and artifact IDs
changed; the YAML configuration namespace changed from `axon.serializer` to `axon.converter`.

##### Import Mappings

| AF4 artifact | AF5 artifact |
|---|---|
| `org.axonframework:axon-spring-boot-starter` | `io.axoniq.framework:axoniq-spring-boot-starter` |
| `org.axonframework:axon-test` (scope=test) | `org.axonframework.extensions.spring:axon-spring-boot-starter-test` |
| `io.axoniq.console:console-framework-client-spring-boot-starter` | Remove — incompatible with AF5 |

##### Detection

```bash
grep -rn 'org.axonframework' --include='pom.xml' --include='build.gradle' --include='build.gradle.kts' .
grep -rn 'axon.serializer' --include='*.yaml' --include='*.properties' .
```

##### Axon Framework 4 — pom.xml

```xml
<properties>
    <axon.version>4.13.1</axon.version>
</properties>

<dependencies>
    <dependency>
        <groupId>org.axonframework</groupId>
        <artifactId>axon-spring-boot-starter</artifactId>
        <version>${axon.version}</version>
    </dependency>
    <dependency>
        <groupId>org.axonframework</groupId>
        <artifactId>axon-test</artifactId>
        <version>${axon.version}</version>
        <scope>test</scope>
    </dependency>
</dependencies>
```

##### Axon Framework 5 — pom.xml

```xml
<properties>
    <axon.version>5.0.0</axon.version>
</properties>

<dependencies>
    <dependency>
        <groupId>io.axoniq.framework</groupId>
        <artifactId>axoniq-spring-boot-starter</artifactId>
        <version>${axon.version}</version>
    </dependency>
    <dependency>
        <groupId>org.axonframework.extensions.spring</groupId>
        <artifactId>axon-spring-boot-starter-test</artifactId>
        <version>${axon.version}</version>
        <scope>test</scope>
    </dependency>
</dependencies>
```

##### YAML configuration namespace

```yaml
#### AF4
axon:
  serializer:
    general: jackson
    events: jackson

#### AF5
axon:
  converter:
    general: jackson
    events: jackson
```

- `axon.serializer.*` → `axon.converter.*` — rename the top-level key.
- All child keys (`general`, `events`, `messages`) remain the same — only the parent changes.

##### Notes

- Remove `io.axoniq.console:console-framework-client-spring-boot-starter` — no AF5-compatible version exists yet.
- For Maven multi-module projects, update the BOM/parent version in the root `pom.xml` only; child modules inherit.
- For Gradle, replace `implementation("org.axonframework:axon-spring-boot-starter:…")` with
  `implementation("io.axoniq.framework:axoniq-spring-boot-starter:…")`.
- The `axon-test` artifact is replaced by `axon-spring-boot-starter-test` from the Spring extensions group.

---

## aggregates

### Aggregate Class Stereotype

AF4 marked event-sourced aggregates with `@Aggregate` (Spring) or `@AggregateRoot` (native configurer) and a
`@AggregateIdentifier` field. AF5 replaces these with `@EventSourced`/`@EventSourcedEntity` on the class — the
identity type is declared as an attribute, not via a field annotation.

##### Import Mappings

| AF4 | AF5 (Spring) | AF5 (native) |
|-----|-------------|--------------|
| `org.axonframework.spring.stereotype.Aggregate` | `org.axonframework.extension.spring.stereotype.EventSourced` | — |
| `org.axonframework.modelling.command.AggregateRoot` | — | `org.axonframework.eventsourcing.annotation.EventSourcedEntity` |
| `org.axonframework.modelling.command.AggregateIdentifier` | *(remove — no replacement)* | *(remove)* |

##### Detection

```bash
grep -rn '@Aggregate\|@AggregateRoot\|@AggregateIdentifier' --include='*.java' --include='*.kt' --include='*.scala' .
```

##### Axon Framework 4 Code

```java
import org.axonframework.spring.stereotype.Aggregate;
import org.axonframework.modelling.command.AggregateIdentifier;

@Aggregate
public class Order {

    @AggregateIdentifier
    private OrderId orderId;

    protected Order() { }  // no annotation
}
```

##### Axon Framework 5 Code — Spring Boot (`configuration=spring`)

```java
import org.axonframework.extension.spring.stereotype.EventSourced;
import org.axonframework.eventsourcing.annotation.reflection.EntityCreator;

@EventSourced(tagKey = "Order", idType = OrderId.class)
public class Order {

    // No @AggregateIdentifier field annotation

    @EntityCreator
    protected Order() { }
}
```

##### Axon Framework 5 Code — Native Configurer (`configuration=native`)

```java
import org.axonframework.eventsourcing.annotation.EventSourcedEntity;
import org.axonframework.eventsourcing.annotation.reflection.EntityCreator;

@EventSourcedEntity(tagKey = "Order", idType = OrderId.class)
public class Order {

    @EntityCreator
    protected Order() { }
}
```

##### Required attributes (never omit)

| Attribute | Value | Why |
|-----------|-------|-----|
| `tagKey` | Simple class name string, e.g. `"Order"` | Event routing key — defaults to class name but silently breaks on rename |
| `idType` | Class of the AF4 `@AggregateIdentifier` field, e.g. `OrderId.class` | Default is `String.class`; wrong type → silent identity resolution failure |

##### Partial migration state (post-OpenRewrite)

OR rewrites `@Aggregate` → `@EventSourced` and inserts a placeholder `idType = Object.class`. `tagKey` defaults to the simple class name but may still be missing on hand-written / unusual cases. Common half-state:

```java
@EventSourced(tagKey = "Order", idType = Object.class)   // idType is a placeholder
public class Order {
    private OrderId orderId;  // @AggregateIdentifier already stripped
    protected Order() { }     // @EntityCreator NOT added — see entity-creator.md
}
```

Minimal fix: replace `idType = Object.class` with the real id class (`OrderId.class`), confirm `tagKey` matches the simple class name used by event `@EventTag(key = …)`, and add `@EntityCreator` to the no-arg constructor. Do NOT re-add `@AggregateIdentifier` or revert `@EventSourced` to `@Aggregate`. Audit:

```bash
grep -rn 'idType = Object\.class\|@EventSourced[^(]' --include='*.java' --include='*.kt' --include='*.scala' .
```

##### Notes

- **`.extension.spring.` infix is mandatory** in Path A — `org.axonframework.extension.spring.stereotype.EventSourced`.
  The path `org.axonframework.spring.stereotype.EventSourced` does not exist; it causes a compile error.
- **Remove `@AggregateIdentifier`** from the field — the identity is now declared on the class annotation.
- **`@EntityCreator` on the no-arg constructor is required** — see [entity-creator.md](entity-creator.md).
- **Snapshot trigger**: if `@Aggregate` carried `snapshotTriggerDefinition`, there is no AF5 equivalent — this is
  a blocker that requires manual resolution.
- **OpenRewrite Phase 1** sometimes rewrites `@Aggregate` → `@EventSourced` without adding `tagKey`/`idType`.
  Always grep for `@EventSourced` without attributes after Phase 1 and add them.

---

### AggregateLifecycle.apply() → EventAppender.append()

AF4 used a `ThreadLocal`-backed static method `AggregateLifecycle.apply(event)` to publish events from inside
`@CommandHandler` methods. AF5 removes `ThreadLocal` entirely — an `EventAppender` is injected as a method
parameter into every `@CommandHandler`.

##### Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.modelling.command.AggregateLifecycle` | *(remove)* |
| `static org.axonframework.modelling.command.AggregateLifecycle.apply` | *(remove)* |
| — | `org.axonframework.messaging.eventhandling.gateway.EventAppender` |

##### Detection

```bash
grep -rn 'AggregateLifecycle\.apply\|import.*AggregateLifecycle' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

##### Axon Framework 4 Code

```java
import static org.axonframework.modelling.command.AggregateLifecycle.apply;

@CommandHandler
public void handle(ShipOrderCommand cmd) {
    apply(new OrderShippedEvent(orderId, cmd.getAddress()));
}
```

##### Axon Framework 5 Code

```java
import org.axonframework.messaging.eventhandling.gateway.EventAppender;

@CommandHandler
public void handle(ShipOrderCommand cmd, EventAppender eventAppender) {
    eventAppender.append(new OrderShippedEvent(orderId, cmd.getAddress()));
}
```

##### Rules

1. Every `@CommandHandler` on the aggregate (and child entities) gets `EventAppender eventAppender` as its **last** parameter.
2. Every `AggregateLifecycle.apply(event)` becomes `eventAppender.append(event)`.
3. Remove both the static import and the regular import for `AggregateLifecycle`.
4. Static `@CommandHandler` factory methods also receive `EventAppender` as a parameter — static methods can receive injected parameters.

##### Partial migration state (post-OpenRewrite)

OR does not rewrite `AggregateLifecycle.apply(...)` call sites — they remain after the bulk pass, sometimes mixed with hand-edited handlers that already use `eventAppender.append(...)`. Common half-state in one class:

```java
@CommandHandler
public void handleA(CmdA cmd, EventAppender eventAppender) {
    eventAppender.append(new EventA());          // already migrated
}

@CommandHandler
public void handleB(CmdB cmd) {                  // EventAppender param missing
    AggregateLifecycle.apply(new EventB());      // still AF4
}
```

Minimal fix: for each handler still calling `AggregateLifecycle.apply(...)`, add the `EventAppender eventAppender` parameter (per [command-handler.md](command-handler.md)) and rewrite only the `apply(...)` lines that are still there. Do NOT re-rewrite handlers already using `eventAppender.append(...)`. Once every site is converted, drop the `AggregateLifecycle` import.

```bash
grep -rn 'AggregateLifecycle\.apply\|import .*AggregateLifecycle' --include='*.java' --include='*.kt' --include='*.scala' .
```

##### Notes

- **`.messaging.` infix is mandatory** — `org.axonframework.messaging.eventhandling.gateway.EventAppender`. The path without `.messaging.` does not exist.
- **Do not call `AggregateLifecycle.markDeleted()`** — there is no AF5 equivalent; remove the call entirely.

---

### @AggregateMember → @EntityMember (Child Entities)

AF4 used `@AggregateMember` to declare child entity collections within an aggregate. AF5 renames this to
`@EntityMember`. Child entities do NOT carry a class-level `@EventSourced`/`@EventSourcedEntity` — they are
discovered through the parent.

##### Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.modelling.command.AggregateMember` | `org.axonframework.modelling.entity.annotation.EntityMember` |

##### Detection

```bash
grep -rn '@AggregateMember' --include='*.java' --include='*.kt' --include='*.scala' .
```

##### Axon Framework 4 Code

```java
import org.axonframework.modelling.command.AggregateMember;

@Aggregate
public class Order {

    @AggregateMember
    private List<OrderLine> lines;

    @AggregateMember(routingKey = "lineId")
    private List<OrderLine> detailedLines;
}
```

##### Axon Framework 5 Code

```java
import org.axonframework.modelling.entity.annotation.EntityMember;

@EventSourced(tagKey = "Order", idType = OrderId.class)
public class Order {

    @EntityMember
    private List<OrderLine> lines;

    @EntityMember(routingKey = "lineId")
    private List<OrderLine> detailedLines;
}
```

##### Child entity requirements

Each child entity class must:
1. **NOT** carry `@EventSourced`/`@EventSourcedEntity` — discovered through the parent.
2. Have `@EntityCreator` on one constructor.
3. Use `EventAppender eventAppender` in its own `@CommandHandler` methods.

```java
// AF5 child entity
public class OrderLine {

    @EntityCreator
    public OrderLine() {}

    @CommandHandler
    public void handle(UpdateLineCommand cmd, EventAppender eventAppender) {
        eventAppender.append(new LineUpdatedEvent(cmd.lineId(), cmd.quantity()));
    }
}
```

##### Notes

- **`Map<K, V>` is a blocker** — `@EntityMember` supports `List<V>` only. Rewrite as `List<V>` with
  internal id management before applying this pattern.
- **`routingKey`** attribute carries over unchanged from `@AggregateMember`.

---

### @CommandHandler — Import Move + EventAppender Parameter

The `@CommandHandler` annotation moved to the `messaging.commandhandling.annotation` package. Every `@CommandHandler`
on an aggregate or child entity must also receive an `EventAppender` as its last parameter (see
[aggregate-lifecycle.md](aggregate-lifecycle.md)).

##### Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.commandhandling.CommandHandler` | `org.axonframework.messaging.commandhandling.annotation.CommandHandler` |

##### Detection

```bash
grep -rn 'import org\.axonframework\.commandhandling\.CommandHandler' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

##### Axon Framework 4 Code

```java
import org.axonframework.commandhandling.CommandHandler;

@CommandHandler
public void handle(ShipOrderCommand cmd) {
    AggregateLifecycle.apply(new OrderShippedEvent(orderId));
}
```

##### Axon Framework 5 Code

```java
import org.axonframework.messaging.commandhandling.annotation.CommandHandler;
import org.axonframework.messaging.eventhandling.gateway.EventAppender;

@CommandHandler
public void handle(ShipOrderCommand cmd, EventAppender eventAppender) {
    eventAppender.append(new OrderShippedEvent(orderId));
}
```

##### Partial migration state (post-OpenRewrite)

OR moves the import to the `messaging.commandhandling.annotation` package but does NOT add the `EventAppender` parameter to handler signatures — the handler body still calls `AggregateLifecycle.apply(...)` (or has been partially rewritten elsewhere). Common half-state:

```java
import org.axonframework.messaging.commandhandling.annotation.CommandHandler;  // import already AF5
// EventAppender NOT imported

@CommandHandler
public void handle(ShipOrderCommand cmd) {                 // signature still AF4 — no EventAppender
    AggregateLifecycle.apply(new OrderShippedEvent(orderId));
}
```

Minimal fix: append `EventAppender eventAppender` as the **last** parameter, add the `org.axonframework.messaging.eventhandling.gateway.EventAppender` import, and rewrite the body per [aggregate-lifecycle.md](aggregate-lifecycle.md). Do NOT touch the already-correct `@CommandHandler` import. Audit:

```bash
grep -rn '@CommandHandler' --include='*.java' --include='*.kt' --include='*.scala' . \
  | grep -v 'EventAppender'
```

##### Notes

- **`.messaging.` infix is mandatory** — `org.axonframework.messaging.commandhandling.annotation.CommandHandler`.
  The path `org.axonframework.commandhandling.annotation.CommandHandler` does not exist.
- **`EventAppender` is required on aggregate and child entity handlers** — see [aggregate-lifecycle.md](aggregate-lifecycle.md).
  On non-aggregate components (event handlers, services) `@CommandHandler` is typically not used — apply this
  pattern only when the handler is inside an `@EventSourced`/`@EventSourcedEntity` class.

---

### @CreationPolicy Removal

AF4's `@CreationPolicy(AggregateCreationPolicy.*)` annotation is removed in AF5. The creation semantics are
replaced by the `@EntityCreator` constructor and the presence/absence of static vs instance `@CommandHandler`.

##### Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.modelling.command.CreationPolicy` | *(remove)* |
| `org.axonframework.modelling.command.AggregateCreationPolicy` | *(remove)* |

##### Detection

```bash
grep -rn '@CreationPolicy\|AggregateCreationPolicy\|import.*CreationPolicy' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

##### Migration by policy value

###### ALWAYS — creation handler

```java
// AF4
@CommandHandler
@CreationPolicy(AggregateCreationPolicy.ALWAYS)
public static MyAggregate create(CreateCommand cmd) { ... }

// AF5 — make the handler static (ALWAYS = factory pattern)
@CommandHandler
public static MyAggregate create(CreateCommand cmd, EventAppender eventAppender) {
    eventAppender.append(new CreatedEvent(cmd.id()));
    return new MyAggregate();
}
```

###### CREATE_IF_MISSING — upsert handler

```java
// AF4
@CommandHandler
@CreationPolicy(AggregateCreationPolicy.CREATE_IF_MISSING)
public void handle(UpsertCommand cmd) { ... }

// AF5 — instance handler; @EntityCreator on no-arg constructor handles the "create" case
// No @CreationPolicy annotation needed
@CommandHandler
public void handle(UpsertCommand cmd, EventAppender eventAppender) {
    eventAppender.append(new UpsertedEvent(cmd.id()));
}
```

###### NEVER (default) — normal instance handler

```java
// AF4 (explicit or absent)
@CommandHandler
@CreationPolicy(AggregateCreationPolicy.NEVER)
public void handle(UpdateCommand cmd) { ... }

// AF5 — just remove the annotation; instance @CommandHandler is the default
@CommandHandler
public void handle(UpdateCommand cmd, EventAppender eventAppender) {
    eventAppender.append(new UpdatedEvent(cmd.id()));
}
```

##### Notes

- **Remove the annotation and both imports** — no replacement annotation is needed.
- **ALWAYS → static factory** is the most common case where OpenRewrite does NOT flip to `static` — always
  verify the handler is static after removing `@CreationPolicy(ALWAYS)`.
- **`@EntityCreator` on the no-arg constructor** is required in all cases — see [entity-creator.md](entity-creator.md).

---

### @EntityCreator — No-Arg Constructor Annotation

AF5 requires the no-arg constructor of an aggregate (and of child entities) to be annotated with `@EntityCreator`.
This tells the framework which constructor to use when materializing an empty entity before replaying events.
In AF4 the no-arg constructor was required but had no annotation.

##### Import Mappings

| AF4 | AF5 |
|-----|-----|
| *(no annotation on no-arg constructor)* | `org.axonframework.eventsourcing.annotation.reflection.EntityCreator` |

##### Detection

```bash
#### Find aggregate classes and check their no-arg constructors
grep -rn '@EventSourced\|@EventSourcedEntity' --include='*.java' --include='*.kt' --include='*.scala' -l .
```

##### Axon Framework 4 Code

```java
@Aggregate
public class Order {

    @AggregateIdentifier
    private OrderId orderId;

    // Required by Axon, no annotation
    protected Order() { }

    // other constructors / handlers...
}
```

##### Axon Framework 5 Code

```java
import org.axonframework.eventsourcing.annotation.reflection.EntityCreator;

@EventSourced(tagKey = "Order", idType = OrderId.class)
public class Order {

    @EntityCreator
    protected Order() { }

    // other constructors / handlers...
}
```

##### Notes

- **Required on child entities too** — every class annotated `@EntityMember`'s no-arg constructor needs
  `@EntityCreator`.
- **`.reflection.` infix is mandatory** — `org.axonframework.eventsourcing.annotation.reflection.EntityCreator`.
  The path without `.reflection.` does not exist.
- **Visibility** — the no-arg constructor may be `protected` or package-private; it does NOT need to be `public`.
- **Omitting `@EntityCreator`** causes a runtime failure when the framework attempts to instantiate the entity —
  the failure message mentions missing creator constructor.

---

### Event Class Annotations

AF5 requires event classes (records or regular classes) to carry the `@Event` annotation. The `@EventTag`
annotation on the routing field replaces the implicit `AggregateIdentifier` link. `@Revision` collapses
into `@Event(version = N)`.

##### Import Mappings

| AF4 | AF5 |
|-----|-----|
| *(no class annotation)* | `org.axonframework.messaging.eventhandling.annotation.Event` |
| *(no field annotation for routing on events)* | `org.axonframework.eventsourcing.annotation.EventTag` |
| `@Revision("N")` | `@Event(version = N)` (attribute on `@Event`) |

##### Detection

```bash
#### Find event classes (usually records in the events/ package)
grep -rn '@Revision\|import.*eventhandling\.Event' --include='*.java' --include='*.kt' --include='*.scala' .
#### Events without @Event annotation — after OpenRewrite; look for record/class in events packages
```

##### Axon Framework 4 Code

```java
// No class-level annotation; revision via @Revision
@Revision("1")
public record OrderShippedEvent(
    String orderId,
    String address
) { }

// Plain event, no revision
public record OrderCreatedEvent(
    String orderId
) { }
```

##### Axon Framework 5 Code

```java
import org.axonframework.messaging.eventhandling.annotation.Event;
import org.axonframework.eventsourcing.annotation.EventTag;

// With version
@Event(version = 1)
public record OrderShippedEvent(
    @EventTag(key = "Order")
    String orderId,
    String address
) { }

// Without version (default)
@Event
public record OrderCreatedEvent(
    @EventTag(key = "Order")
    String orderId
) { }
```

##### Notes

- **`@Event` is required** — events without it are not recognized by AF5 handlers.
- **`@EventTag`** marks the field whose value is used as the aggregate routing key. Its `key` attribute must match
  the `tagKey` on the aggregate's `@EventSourced` annotation.
- **Every event type** routed to a specific aggregate must have `@EventTag` on the routing field, or the framework
  cannot match events to aggregate instances.
- **`@Revision("N")` → `@Event(version = N)`** — the version is now an `int` attribute, not a string annotation.
- **Pure value events** (not tied to any aggregate) still need `@Event`; they do not need `@EventTag`.

---

### Event Emission in Aggregates

AF4 used a `ThreadLocal`-backed static method `AggregateLifecycle.apply(event)` to publish events from inside
command handlers. AF5 removes `ThreadLocal` entirely; event publishing uses an `EventAppender` parameter injected
into every `@CommandHandler` method.

##### Import Mappings

| AF4 | AF5 |
|-----|-----|
| `import static org.axonframework.modelling.command.AggregateLifecycle.apply` | *(remove)* |
| `org.axonframework.modelling.command.AggregateLifecycle` | *(remove)* |
| `org.axonframework.commandhandling.CommandHandler` | `org.axonframework.messaging.commandhandling.annotation.CommandHandler` |
| — | `org.axonframework.messaging.eventhandling.gateway.EventAppender` |

##### Detection

```bash
grep -rn 'AggregateLifecycle\.apply\|import.*AggregateLifecycle\|import.*commandhandling\.CommandHandler' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

##### Axon Framework 4 Code

```java
import static org.axonframework.modelling.command.AggregateLifecycle.apply;
import org.axonframework.commandhandling.CommandHandler;

@CommandHandler
public void handle(ShipOrderCommand cmd) {
    // validate...
    apply(new OrderShippedEvent(this.orderId, cmd.getAddress()));
}

@CommandHandler
@CreationPolicy(AggregateCreationPolicy.CREATE_IF_MISSING)
public void handle(CreateOrderCommand cmd) {
    apply(new OrderCreatedEvent(cmd.getOrderId()));
}
```

##### Axon Framework 5 Code

```java
import org.axonframework.messaging.commandhandling.annotation.CommandHandler;
import org.axonframework.messaging.eventhandling.gateway.EventAppender;

@CommandHandler
public void handle(ShipOrderCommand cmd, EventAppender eventAppender) {
    // validate...
    eventAppender.append(new OrderShippedEvent(this.orderId, cmd.getAddress()));
}

@CommandHandler
@CreationPolicy(AggregateCreationPolicy.CREATE_IF_MISSING)
public void handle(CreateOrderCommand cmd, EventAppender eventAppender) {
    eventAppender.append(new OrderCreatedEvent(cmd.getOrderId()));
}
```

##### Rules

1. **Every `@CommandHandler`** on the aggregate and on every child entity gets `EventAppender eventAppender` as
   its **last** parameter — including static factory handlers and constructor handlers.
2. Every `AggregateLifecycle.apply(event)` call becomes `eventAppender.append(event)`.
3. Remove the static import and the regular `AggregateLifecycle` import.

##### Notes

- **`.messaging.` infix is mandatory** for both `@CommandHandler` and `EventAppender` — the paths without it
  do not exist.
- **Child entities**: every `@CommandHandler` on a child entity (`@EntityMember`) also needs `EventAppender`.
  The parent aggregate's `EventAppender` is NOT shared.
- **Static factory `@CommandHandler`**: still needs `EventAppender` as last parameter even though the method is static.
- **`EventAppender.append(…)` is one-event-at-a-time** — for multiple events use separate calls:
  `eventAppender.append(e1); eventAppender.append(e2);`
- **grep after migration**: `grep -rn 'AggregateLifecycle' …` — any surviving call is a compile error.

---

### @EventSourcingHandler — Import Package Move

`@EventSourcingHandler` moved to a new package in AF5. The annotation's behavior is unchanged — it marks
methods that apply events to rebuild aggregate state from the event stream.

##### Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.eventsourcing.EventSourcingHandler` | `org.axonframework.eventsourcing.annotation.EventSourcingHandler` |

##### Detection

```bash
grep -rn 'import org.axonframework.eventsourcing.EventSourcingHandler' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

##### Axon Framework 4 Code

```java
import org.axonframework.eventsourcing.EventSourcingHandler;

@EventSourcingHandler
public void on(OrderCreatedEvent event) {
    this.orderId = new OrderId(event.orderId());
}
```

##### Axon Framework 5 Code

```java
import org.axonframework.eventsourcing.annotation.EventSourcingHandler;

@EventSourcingHandler
public void on(OrderCreatedEvent event) {
    this.orderId = new OrderId(event.orderId());
}
```

##### Notes

- **Only the import changes** — the annotation itself, its semantics, and method signatures are identical.
- **`.annotation.` infix added** — `org.axonframework.eventsourcing.**annotation**.EventSourcingHandler`.
- Methods inside `@EventSourcingHandler` that call `event.getPayload()` / `event.getMetaData()` should be updated
  to `event.payload()` / `event.metaData()` — see [message-accessors pattern](../30-event-handlers/message-accessors.md).

---

### GenericDomainEventMessage Removal

AF4 exposed `GenericDomainEventMessage` for constructing event messages with aggregate metadata (type,
sequence). AF5 removes this class — aggregate events are appended through `EventAppender` which sets the
aggregate context automatically. Where direct `GenericDomainEventMessage` construction was used (typically
in test setup or infrastructure code), use `GenericEventMessage` instead.

##### Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.messaging.eventhandling.GenericDomainEventMessage` | `org.axonframework.messaging.eventhandling.GenericEventMessage` |
| `org.axonframework.domain.GenericDomainEventMessage` | `org.axonframework.messaging.eventhandling.GenericEventMessage` |

##### Detection

```bash
grep -rn 'GenericDomainEventMessage' --include='*.java' --include='*.kt' --include='*.scala' .
```

##### Axon Framework 4 Code

```java
import org.axonframework.messaging.eventhandling.GenericDomainEventMessage;

// In test setup — constructing a past event
GenericDomainEventMessage<OrderCreatedEvent> message =
    new GenericDomainEventMessage<>("Order", orderId.toString(), 0,
        new OrderCreatedEvent(orderId));
```

##### Axon Framework 5 Code

```java
import org.axonframework.messaging.eventhandling.GenericEventMessage;

// GenericEventMessage — aggregate context is not required in AF5 event construction
GenericEventMessage<OrderCreatedEvent> message =
    new GenericEventMessage<>(new OrderCreatedEvent(orderId));
```

##### Notes

- In **aggregate code**, you never construct event messages directly — use `EventAppender.append(event)` instead.
- In **test fixtures** (`AxonTestFixture`), pass the plain event object to `given().events(...)` — no wrapper needed.
- In **infrastructure / replay** code that reads raw events, use `GenericEventMessage` if a wrapper is still required.
- `GenericDomainEventMessage` carried `aggregateType` and `sequenceNumber`; `GenericEventMessage` does not.
  If your code reads those fields, revisit whether you still need them in AF5.

---

### @TargetAggregateIdentifier Removal

AF4 required a `@TargetAggregateIdentifier` annotation on the command field that routes the command to the
correct aggregate instance. AF5 removes this annotation — routing is now driven by the `idType` declared on
`@EventSourced` and the command's field type.

##### Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.modelling.command.TargetAggregateIdentifier` | *(remove — no replacement)* |

##### Detection

```bash
grep -rn '@TargetAggregateIdentifier\|TargetAggregateIdentifier' --include='*.java' --include='*.kt' --include='*.scala' .
```

##### Axon Framework 4 Code

```java
import org.axonframework.modelling.command.TargetAggregateIdentifier;

public record CreateOrderCommand(
    @TargetAggregateIdentifier OrderId orderId,
    String customerId
) {}
```

##### Axon Framework 5 Code

```java
public record CreateOrderCommand(
    OrderId orderId,
    String customerId
) {}
```

##### Notes

- **Remove the annotation and its import.** No replacement needed.
- **Remove `@TargetAggregateVersion` too** if present — also gone in AF5.
- AF5 routes commands by matching the command's field type against the aggregate's `idType = OrderId.class`
  declared on `@EventSourced`. The field name is irrelevant; the type match is the routing key.
- If two fields share the same type as `idType`, routing is ambiguous — rename one or use a wrapper type.

---

## event handlers

### In-Handler Command Dispatch — CommandGateway → CommandDispatcher

AF4 injected `CommandGateway` as a class-level field in event processors that dispatched commands from inside
`@EventHandler` methods. AF5 replaces this with `CommandDispatcher` injected as a **method parameter** — the
framework automatically binds it to the active `ProcessingContext`. The dispatch API is **async** in AF5.

##### Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.commandhandling.gateway.CommandGateway` | *(remove field/constructor injection)* |
| — | `org.axonframework.messaging.commandhandling.gateway.CommandDispatcher` |
| — | `java.util.concurrent.CompletableFuture` |

##### Detection

```bash
#### Find event-handling classes that inject CommandGateway
grep -rln 'CommandGateway' --include='*.java' --include='*.kt' --include='*.scala' . \
  | xargs grep -l '@EventHandler'
```

##### Axon Framework 4 Code

```java
@ProcessingGroup("orders")
@Component
public class OrderAutomation {

    private final CommandGateway commandGateway;

    public OrderAutomation(CommandGateway commandGateway) {
        this.commandGateway = commandGateway;
    }

    @EventHandler
    public void on(PaymentReceivedEvent event,
                   @MetaDataValue("gameId") String gameId) {
        commandGateway.sendAndWait(
            new ShipOrderCommand(event.orderId()),
            MetaData.with("gameId", gameId)
        );
    }
}
```

##### Axon Framework 5 Code

```java
@Namespace("orders")
@Component
public class OrderAutomation {

    // No CommandGateway field or constructor parameter

    @EventHandler
    public CompletableFuture<?> on(PaymentReceivedEvent event,
                                   @MetadataValue("gameId") String gameId,
                                   CommandDispatcher commandDispatcher) {
        return commandDispatcher
            .send(new ShipOrderCommand(event.orderId()), MetaData.with("gameId", gameId))
            .getResultMessage();
    }
}
```

##### Key API differences

| AF4 | AF5 |
|-----|-----|
| `commandGateway.sendAndWait(cmd)` | `commandDispatcher.send(cmd).getResultMessage()` → `CompletableFuture` |
| `commandGateway.send(cmd)` | `commandDispatcher.send(cmd)` |
| `commandGateway.sendAndWait(cmd, MetaData.with(…))` | `commandDispatcher.send(cmd, MetaData.with(…)).getResultMessage()` |
| try/catch synchronous | `.exceptionallyCompose(err -> …)` on the future |
| `void` return from handler | `CompletableFuture<?>` return from handler |

##### Use `.resultAs(Type.class)` to avoid wildcards

```java
commandDispatcher.send(cmd).resultAs(Void.class)   // returns CompletableFuture<Void>
```

##### Notes

- **Remove the `CommandGateway` field AND constructor parameter entirely** — do not keep both.
- **Event handler must return `CompletableFuture<?>`** when it dispatches commands — the framework propagates the
  future correctly. Do not call `.join()` inside the handler (blocks the thread).
- **`CommandDispatcher` only works inside a `ProcessingContext`** — it cannot be used in REST controllers or
  scheduled tasks. For those, keep `CommandGateway` (see command-gateway recipe).
- **Compensation logic**: AF4 try/catch around `sendAndWait` becomes `.exceptionallyCompose(…)` on the future.
  Forgetting this means compensation silently stops on failure.
- **Simple cases** where you do not need the result: `return commandDispatcher.send(cmd).getResultMessage().thenApply(_ -> null);`

---

### @EventHandler, @DisallowReplay, @ResetHandler — Import Package Moves

These three event-handling annotations moved to new packages in AF5. Their semantics are unchanged.

##### Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.eventhandling.EventHandler` | `org.axonframework.messaging.eventhandling.annotation.EventHandler` |
| `org.axonframework.eventhandling.DisallowReplay` | `org.axonframework.messaging.eventhandling.replay.annotation.DisallowReplay` |
| `org.axonframework.eventhandling.ResetHandler` | `org.axonframework.messaging.eventhandling.replay.annotation.ResetHandler` |

##### Detection

```bash
grep -rn 'import org\.axonframework\.eventhandling\.\(EventHandler\|DisallowReplay\|ResetHandler\)' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

##### Axon Framework 4 Code

```java
import org.axonframework.eventhandling.EventHandler;
import org.axonframework.eventhandling.DisallowReplay;
import org.axonframework.eventhandling.ResetHandler;

@Component
@ProcessingGroup("orders")
@DisallowReplay
public class OrderProjector {

    @EventHandler
    public void on(OrderCreatedEvent event) {
        // handle
    }

    @ResetHandler
    public void onReset() {
        // clear read model
    }
}
```

##### Axon Framework 5 Code

```java
import org.axonframework.messaging.eventhandling.annotation.EventHandler;
import org.axonframework.messaging.eventhandling.replay.annotation.DisallowReplay;
import org.axonframework.messaging.eventhandling.replay.annotation.ResetHandler;

@Component
@Namespace("orders")
@DisallowReplay
public class OrderProjector {

    @EventHandler
    public void on(OrderCreatedEvent event) {
        // handle
    }

    @ResetHandler
    public void onReset() {
        // clear read model
    }
}
```

##### Notes

- **Only import paths change** — annotation names, attributes, and usage patterns are identical.
- **`@DisallowReplay` moves to `replay.annotation`** — the `replay.` infix is new; do not omit it.
- **Event handler return type**: handlers that dispatch commands via `CommandDispatcher` must return
  `CompletableFuture<?>` — see [command-dispatcher.md](command-dispatcher.md).

---

### Message Accessor Renames

AF4 used JavaBean-style getter methods on `Message` objects (`getPayload()`, `getMetaData()`, etc.). AF5 renames
these to plain property-style accessors without the `get` prefix.

##### Import Mappings

| AF4 method | AF5 method |
|-----------|-----------|
| `message.getPayload()` | `message.payload()` |
| `message.getMetaData()` | `message.metaData()` |
| `message.getIdentifier()` | `message.identifier()` |
| `message.getTimestamp()` | `message.timestamp()` |
| `event.getPayloadType()` | `event.payloadType()` |
| `message.getMetaData().get("key")` | `message.metaData().get("key")` |

##### Detection

```bash
grep -rn '\.getPayload()\|\.getMetaData()\|\.getIdentifier()\|\.getTimestamp()\|\.getPayloadType()' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

##### Axon Framework 4 Code

```java
@MessageHandlerInterceptor
public Object intercept(UnitOfWork<? extends CommandMessage<?>> uow, InterceptorChain chain) {
    Object payload = uow.getMessage().getPayload();
    Map<String, Object> meta = uow.getMessage().getMetaData();
    String id = uow.getMessage().getIdentifier();
    return chain.proceed();
}
```

##### Axon Framework 5 Code

```java
@Override
public MessageStream<?> interceptOnHandle(
        CommandMessage message,
        ProcessingContext context,
        MessageHandlerInterceptorChain<CommandMessage> chain) {
    Object payload = message.payload();
    MetaData meta = message.metaData();
    String id = message.identifier();
    return chain.proceed(message, context);
}
```

##### Notes

- **`MetaData` type in AF5** — `message.metaData()` returns `org.axonframework.messaging.MetaData` which is a
  `Map<String, Object>`. Non-String values stored as metadata must be stringified (`toString()`) when accessed
  via `@MetadataValue` since the annotation injects `String`.
- **Applies to all `Message` subtypes**: `CommandMessage`, `EventMessage`, `QueryMessage`.
- **Inside `@EventSourcingHandler`**: payload is the event itself (method parameter) — no accessor needed.
- **Inside test lambdas**: `events.get(0).getPayload()` → `(YourEventType) events.get(0).payload()`.

---

### Metadata Type Change

AF4 `Metadata` implemented `Map<String, Object>` — values were arbitrary objects. AF5 `Metadata` implements
`Map<String, String>` — values are strings only. Code that stored or read non-string metadata values must
be updated to serialize/deserialize to/from `String`.

##### Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.messaging.MetaData` | `org.axonframework.messaging.core.Metadata` |

Note the capitalisation change: `MetaData` (AF4) → `Metadata` (AF5).

##### Detection

```bash
grep -rn 'org\.axonframework\.messaging\.MetaData\|MetaData\.with\|MetaData\.emptyInstance\|Map<String, Object>' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

##### Axon Framework 4 Code

```java
import org.axonframework.messaging.MetaData;

// AF4 — values are Object
MetaData meta = MetaData.with("userId", userId).and("role", role);
Object val = meta.get("userId");        // returns Object
String userId = (String) meta.get("userId");

// As a parameter type
public void dispatch(CreateOrderCommand cmd, MetaData meta) { ... }
```

##### Axon Framework 5 Code

```java
import org.axonframework.messaging.core.Metadata;

// AF5 — values are String
Metadata meta = Metadata.from(Map.of("userId", userId.toString(), "role", role.toString()));
String userId = meta.get("userId");     // already String, no cast

// As a parameter type
public void dispatch(CreateOrderCommand cmd, Metadata meta) { ... }
```

##### Notes

- **Rename the import and the type** — `MetaData` → `Metadata`.
- **Cast non-string values to `String`** when storing (or use `toString()`).
- **Remove casts when reading** — values are already `String`.
- If you stored serialized objects (JSON, etc.) in metadata, the serialisation contract is unchanged;
  just ensure the stored value is a `String`.
- `MetaData.emptyInstance()` → `Metadata.emptyInstance()` (same method name, new type).
- `MetaData.with(key, value)` → `Metadata.from(Map.of(key, value.toString()))`.

---

### @MetaDataValue → @MetadataValue

AF4 used `@MetaDataValue` (capital D) from `org.axonframework.messaging.annotation.MetaDataValue`. AF5 renames
it to `@MetadataValue` (lowercase d) and moves it to a new package.

##### Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.messaging.annotation.MetaDataValue` | `org.axonframework.messaging.core.annotation.MetadataValue` |

##### Detection

```bash
grep -rn '@MetaDataValue\|import.*MetaDataValue' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

##### Axon Framework 4 Code

```java
import org.axonframework.messaging.annotation.MetaDataValue;

@EventHandler
public void on(OrderCreatedEvent event,
               @MetaDataValue("gameId") String gameId,
               @MetaDataValue("playerId") String playerId) {
    // handle
}
```

##### Axon Framework 5 Code

```java
import org.axonframework.messaging.core.annotation.MetadataValue;

@EventHandler
public void on(OrderCreatedEvent event,
               @MetadataValue("gameId") String gameId,
               @MetadataValue("playerId") String playerId) {
    // handle
}
```

##### Notes

- **Both the annotation name and the import change**: `MetaDataValue` → `MetadataValue` (capital D → lowercase d).
- **Package changes**: `messaging.annotation` → `messaging.core.annotation`.
- **String key is unchanged** — the metadata key string stays the same.
- This annotation is used in `@EventHandler`, `@CommandHandler`, `@QueryHandler` methods, and interceptors —
  update it everywhere.

---

### @ProcessingGroup → @Namespace (Event Processor Routing)

AF4 grouped event handlers with `@ProcessingGroup("name")`. AF5 renames this to `@Namespace("name")`. The
string value is a binding contract and must match all external references (YAML config, processor definitions).

##### Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.config.ProcessingGroup` | `org.axonframework.messaging.core.annotation.Namespace` |

##### Detection

```bash
grep -rn 'import org\.axonframework\.config\.ProcessingGroup\|@ProcessingGroup' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

##### Axon Framework 4 Code

```java
import org.axonframework.config.ProcessingGroup;

@ProcessingGroup("orders")
@Component
public class OrderProjector {
    // @EventHandler methods...
}
```

##### Axon Framework 5 Code

```java
import org.axonframework.messaging.core.annotation.Namespace;

@Namespace("orders")
@Component
public class OrderProjector {
    // @EventHandler methods...
}
```

##### Verify external references

After renaming, grep the repository for the **old group string** to find all places that must also be updated:

```bash
grep -rn '"orders"' \
  --include='*.java' --include='*.kt' --include='*.scala' --include='*.yaml' --include='*.properties' .
```

Places to update:
- `application.yaml`: rename the `axon.eventhandling.processors.<name>.*` segment if needed.
- `EventProcessorDefinition.pooledStreaming("orders")` in Spring `@Bean` config.
- `MessagingConfigurer.eventProcessing(…).processor("orders", …)` in native config.

##### Partial migration state (post-OpenRewrite)

OR rewrites the `@ProcessingGroup` symbol to `@Namespace`, but an unrelated `import org.axonframework.config.ProcessingGroup;` line (from a class no longer using it, or a stale wildcard) may linger and fail to resolve. Common half-state:

```java
import org.axonframework.config.ProcessingGroup;             // stale — class is gone in AF5
import org.axonframework.messaging.core.annotation.Namespace; // already AF5

@Namespace("orders")
public class OrderProjector { /* ... */ }
```

Minimal fix: delete the lingering AF4 `ProcessingGroup` import line. Do NOT revert the `@Namespace` annotation. Audit:

```bash
grep -rn 'import org\.axonframework\.config\.ProcessingGroup\|import org\.axonframework\.common\.configuration\.ProcessingGroup' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

##### Notes

- **OpenRewrite Phase 1** usually swaps the annotation but may leave the AF4 import. Always grep for the old import.
- **String case-sensitivity** — `"Orders"` ≠ `"orders"`. YAML key, annotation value, and any processor-definition
  argument must all be identical.
- A **namespace mismatch silently drops all events** at runtime — there is no compile-time signal.

---

### Sequencing Policy Migration

AF4 wired sequencing policies externally — via YAML `axon.eventhandling.processors.<group>.sequencing-policy`,
a `@Bean SequencingPolicy<EventMessage<?>>`, or programmatic `EventProcessingConfigurer.assignSequencingPolicy(…)`.
AF5 moves policy declaration to a class-level `@SequencingPolicy` annotation on the event-handling class.

##### Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.eventhandling.async.SequencingPolicy` (interface) | `org.axonframework.messaging.core.sequencing.SequencingPolicy` |
| YAML: `sequencing-policy: beanName` | `@SequencingPolicy` annotation on handler class |
| — | `org.axonframework.messaging.core.annotation.SequencingPolicy` (annotation) |
| — | `org.axonframework.messaging.core.sequencing.MetadataSequencingPolicy` |

##### Detection

```bash
grep -rn 'SequencingPolicy\|sequencing-policy' \
  --include='*.java' --include='*.kt' --include='*.scala' --include='*.yaml' --include='*.properties' .
```

##### Part 1 — Remove YAML wiring, add @SequencingPolicy annotation

###### Axon Framework 4

```yaml
#### application.yaml
axon:
  eventhandling:
    processors:
      orders:
        mode: pooled
        sequencing-policy: gameIdSequencingPolicy   # <-- references @Bean name
```

```java
// Configuration class
@Bean
public SequencingPolicy<EventMessage<?>> gameIdSequencingPolicy() {
    return e -> e.getMetaData().get("gameId");
}
```

###### Axon Framework 5

```yaml
#### application.yaml — remove sequencing-policy key; mode stays
axon:
  eventhandling:
    processors:
      orders:
        mode: pooled
```

```java
import org.axonframework.messaging.core.annotation.Namespace;
import org.axonframework.messaging.core.annotation.SequencingPolicy;
import org.axonframework.messaging.core.sequencing.MetadataSequencingPolicy;

@Namespace("orders")
@SequencingPolicy(type = MetadataSequencingPolicy.class, parameters = "gameId")
public class OrderProjector { … }
```

##### Part 2 — Custom SequencingPolicy interface rewrite

###### Axon Framework 4

```java
import org.axonframework.eventhandling.async.SequencingPolicy;

public class MyPolicy implements SequencingPolicy<EventMessage<?>> {
    @Override
    public Object getSequenceIdentifierFor(EventMessage<?> event) {
        return event.getPayload().getClass().getSimpleName();
    }
}
```

###### Axon Framework 5

```java
import org.axonframework.messaging.core.sequencing.SequencingPolicy;
import org.axonframework.messaging.eventhandling.EventMessage;
import org.axonframework.messaging.core.ProcessingContext;
import java.util.Optional;

public class MyPolicy implements SequencingPolicy {
    @Override
    public Optional<Object> sequenceIdentifierFor(EventMessage<?> message, ProcessingContext context) {
        return Optional.ofNullable(message.payload().getClass().getSimpleName());
    }
}
```

##### Method signature changes

| | AF4 | AF5 |
|---|---|---|
| Method name | `getSequenceIdentifierFor` | `sequenceIdentifierFor` |
| Parameters | `EventMessage<?> event` | `EventMessage<?> message, ProcessingContext context` |
| Return | `Object` (null = no sequence) | `Optional<Object>` (empty = no sequence) |
| Interface generic | `SequencingPolicy<EventMessage<?>>` | `SequencingPolicy` (no generic) |

##### Built-in policy classes

| Policy | Usage |
|--------|-------|
| `MetadataSequencingPolicy` | `@SequencingPolicy(type = MetadataSequencingPolicy.class, parameters = "metadataKey")` |
| `SequentialPerAggregatePolicy` | `@SequencingPolicy(type = SequentialPerAggregatePolicy.class)` |
| `SequentialPolicy` | `@SequencingPolicy(type = SequentialPolicy.class)` |
| `FullConcurrencyPolicy` | `@SequencingPolicy(type = FullConcurrencyPolicy.class)` |

##### Notes

- **`@SequencingPolicy` annotation package is `core.annotation`** — `org.axonframework.messaging.core.annotation.SequencingPolicy`.
  Not `core.sequencing.annotation.SequencingPolicy` (doesn't exist).
- **`parameters` is a `String`** representing the metadata key for `MetadataSequencingPolicy`.
- **`@Bean SequencingPolicy` definition** — leave the bean in the configuration class (other processors may use it);
  only remove the YAML reference.

---

## query handlers

### @QueryHandler — Import Package Move

The `@QueryHandler` annotation moved to a new package in AF5. The annotation's behavior and method signatures
are unchanged.

##### Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.queryhandling.QueryHandler` | `org.axonframework.messaging.queryhandling.annotation.QueryHandler` |
| `org.axonframework.queryhandling.QueryUpdateEmitter` | `org.axonframework.messaging.queryhandling.QueryUpdateEmitter` |

##### Detection

```bash
grep -rn 'import org\.axonframework\.queryhandling\.QueryHandler' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

##### Axon Framework 4 Code

```java
import org.axonframework.queryhandling.QueryHandler;

@Component
public class OrderQueryHandler {

    @QueryHandler
    public OrderView handle(GetOrderByIdQuery query) {
        return repository.findById(query.orderId()).orElse(null);
    }

    @QueryHandler
    public List<OrderView> handle(GetAllOrdersQuery query) {
        return repository.findAll();
    }
}
```

##### Axon Framework 5 Code

```java
import org.axonframework.messaging.queryhandling.annotation.QueryHandler;

@Component
public class OrderQueryHandler {

    @QueryHandler
    public OrderView handle(GetOrderByIdQuery query) {
        return repository.findById(query.orderId()).orElse(null);
    }

    @QueryHandler
    public List<OrderView> handle(GetAllOrdersQuery query) {
        return repository.findAll();
    }
}
```

##### Notes

- **Only the import changes** — annotation name, attributes, and method signatures are identical.
- **`@QueryHandler(queryName = "…")` pattern**: if any handler used `queryName` to decouple the handler from a
  specific query class, this must be migrated to a `@Query`-annotated payload record — see the `query-payload-record`
  atom in `references/atoms/`.
- **`QueryUpdateEmitter`** import also changes — see the `query-update-emitter` atom in `references/atoms/`.

---

### Named Query — @QueryHandler(queryName) → @Query Payload Record

AF4 allowed routing queries by a `queryName` string. AF5 routes entirely by the first method parameter type —
the `queryName` attribute is removed. When AF4 used a named query, introduce a top-level payload record.

##### Import Mappings

| AF4 | AF5 |
|-----|-----|
| `@QueryHandler(queryName = "…")` attribute | *(remove attribute)* |
| — | `org.axonframework.messaging.queryhandling.annotation.Query` (only when class name ≠ queryName) |

##### Detection

```bash
grep -rn '@QueryHandler.*queryName' --include='*.java' --include='*.kt' --include='*.scala' .
```

##### Axon Framework 4 Code

```java
@QueryHandler(queryName = "findAvailable")
public Iterable<BikeStatus> findAvailable(String bikeType) {
    return repository.findAllByStatus(BikeStatus.available(bikeType));
}
```

##### Axon Framework 5 Code

Introduce a payload record in the query API package:

```java
// queries/FindAvailableQuery.java
import org.axonframework.messaging.queryhandling.annotation.Query;

// Add @Query ONLY when simple class name ≠ queryName string (case-sensitive)
// "FindAvailableQuery" ≠ "findAvailable" → annotation required
@Query(name = "findAvailable")
public record FindAvailableQuery(String bikeType) {}
```

Update the handler:

```java
@QueryHandler
public Iterable<BikeStatus> findAvailable(FindAvailableQuery query) {
    return repository.findAllByStatus(BikeStatus.available(query.bikeType()));
}
```

##### Notes

- **Do NOT nest the record inside the handler class** — query records are shared API; place them in the
  project's query API package.
- **`@Query` is only needed when the record's simple class name does not equal the `queryName` string
  (case-sensitive).** If they match, the annotation is optional.
- No-param queries: `public record FindAvailableQuery() {}` — the record still needs to exist even with
  no fields.

---

### QueryUpdateEmitter — Constructor Field → Method Parameter

AF4 injected `QueryUpdateEmitter` as a constructor field. AF5 enforces method-level injection — the emitter
becomes a parameter on each `@EventHandler` that calls it. The `emit()` signature gains a `Class<Q>` first
argument.

##### Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.queryhandling.QueryUpdateEmitter` | `org.axonframework.messaging.queryhandling.QueryUpdateEmitter` |

##### Detection

```bash
grep -rn 'QueryUpdateEmitter' --include='*.java' --include='*.kt' --include='*.scala' .
```

##### Axon Framework 4 Code

```java
import org.axonframework.queryhandling.QueryUpdateEmitter;

@ProcessingGroup("queries")
@Component
public class OrderProjection {

    private final QueryUpdateEmitter updateEmitter;

    public OrderProjection(QueryUpdateEmitter updateEmitter) {
        this.updateEmitter = updateEmitter;
    }

    @EventHandler
    public void on(OrderPlacedEvent event) {
        updateEmitter.emit(q -> true, new OrderDto(event));
    }
}
```

##### Axon Framework 5 Code

```java
import org.axonframework.messaging.queryhandling.QueryUpdateEmitter;

@Namespace("queries")
@Component
public class OrderProjection {

    // No QueryUpdateEmitter field or constructor parameter

    @EventHandler
    public void on(OrderPlacedEvent event, QueryUpdateEmitter updateEmitter) {
        updateEmitter.emit(GetOrderQuery.class, q -> true, new OrderDto(event));
    }
}
```

##### emit() signature change

| AF4 | AF5 |
|-----|-----|
| `emit(predicate, update)` | `emit(QueryClass.class, predicate, update)` |

The query class is the first argument — it matches the `@QueryHandler` first parameter type.

##### Notes

- **Remove the constructor field and injection entirely** — do not keep both.
- **Add `QueryUpdateEmitter` as a parameter** to every `@EventHandler` that calls `emit(…)`.
- **The query class argument is required** — `emit(q -> true, dto)` does not compile in AF5.

---

## interceptors

### MessageDispatchInterceptor — handle(List) → interceptOnDispatch

AF4 dispatch interceptors processed messages in a batch: `handle(List<? extends M>)` returned a
`BiFunction<Integer, M, M>` applied per message. AF5 changes to single-message: `interceptOnDispatch`
receives one message, modifies it inline, and delegates to the chain.

##### Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.messaging.MessageDispatchInterceptor` | `org.axonframework.messaging.core.MessageDispatchInterceptor` |
| `java.util.List` | *(remove)* |
| `java.util.function.BiFunction` | *(remove)* |
| — | `org.axonframework.messaging.core.MessageDispatchInterceptorChain` |
| — | `org.axonframework.messaging.core.MessageStream` |
| — | `org.axonframework.messaging.core.unitofwork.ProcessingContext` |

##### Detection

```bash
grep -rn 'implements MessageDispatchInterceptor\|BiFunction.*handle.*List' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

##### Axon Framework 4 Code

```java
import java.util.List;
import java.util.function.BiFunction;
import org.axonframework.messaging.MessageDispatchInterceptor;

public class MyDispatchInterceptor implements MessageDispatchInterceptor<CommandMessage<?>> {

    @Override
    public BiFunction<Integer, CommandMessage<?>, CommandMessage<?>> handle(
            List<? extends CommandMessage<?>> messages) {
        return (index, message) -> {
            // modify message
            return GenericCommandMessage.asCommandMessage(message.getPayload())
                .withMetaData(message.getMetaData().and("extra", "value"));
        };
    }
}
```

##### Axon Framework 5 Code

```java
import org.axonframework.messaging.core.MessageDispatchInterceptor;
import org.axonframework.messaging.core.MessageDispatchInterceptorChain;
import org.axonframework.messaging.core.MessageStream;
import org.axonframework.messaging.core.unitofwork.ProcessingContext;
import org.jspecify.annotations.Nullable;

public class MyDispatchInterceptor implements MessageDispatchInterceptor<CommandMessage> {

    @Override
    public MessageStream<?> interceptOnDispatch(
            CommandMessage message,
            @Nullable ProcessingContext context,
            MessageDispatchInterceptorChain<CommandMessage> chain) {
        CommandMessage modified = message.withMetadata(
            message.metadata().andWith("extra", "value")
        );
        return chain.proceed(modified, context);
    }
}
```

##### Notes

- **Generic type loses wildcard** — `CommandMessage<?>` → `CommandMessage` (no wildcard).
- **Method name change** — `handle` → `interceptOnDispatch`.
- **Return type change** — `BiFunction<Integer, M, M>` → `MessageStream<?>`.
- **Always call `chain.proceed(modified, context)`** at the end — returning without calling it drops the message.

---

### MessageHandlerInterceptor — Handle Method Signature Migration

AF4 handler interceptors implemented `MessageHandlerInterceptor<M>` with a `handle(UnitOfWork, InterceptorChain)`
method. AF5 replaces this with `interceptOnHandle(M, ProcessingContext, MessageHandlerInterceptorChain<M>)`.
The chain call changes from no-arg `chain.proceed()` to `chain.proceed(message, context)`.

##### Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.messaging.unitofwork.UnitOfWork` | *(remove)* |
| `org.axonframework.messaging.InterceptorChain` | *(remove)* |
| `org.axonframework.messaging.MessageHandlerInterceptor` | `org.axonframework.messaging.core.MessageHandlerInterceptor` |
| — | `org.axonframework.messaging.core.MessageHandlerInterceptorChain` |
| — | `org.axonframework.messaging.core.MessageStream` |
| — | `org.axonframework.messaging.core.unitofwork.ProcessingContext` |

##### Detection

```bash
grep -rn 'implements MessageHandlerInterceptor\|UnitOfWork.*InterceptorChain\|InterceptorChain.*UnitOfWork' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

##### Axon Framework 4 Code

```java
import org.axonframework.messaging.MessageHandlerInterceptor;
import org.axonframework.messaging.unitofwork.UnitOfWork;
import org.axonframework.messaging.InterceptorChain;

public class AuthInterceptor implements MessageHandlerInterceptor<CommandMessage<?>> {

    @Override
    public Object handle(
            @Nonnull UnitOfWork<? extends CommandMessage<?>> unitOfWork,
            @Nonnull InterceptorChain interceptorChain) throws Exception {
        CommandMessage<?> cmd = unitOfWork.getMessage();
        String playerId = (String) cmd.getMetaData().get("playerId");
        validate(playerId);
        return interceptorChain.proceed();
    }
}
```

##### Axon Framework 5 Code

```java
import org.axonframework.messaging.core.MessageHandlerInterceptor;
import org.axonframework.messaging.core.MessageHandlerInterceptorChain;
import org.axonframework.messaging.core.MessageStream;
import org.axonframework.messaging.core.unitofwork.ProcessingContext;

public class AuthInterceptor implements MessageHandlerInterceptor<CommandMessage> {

    @Override
    public @NonNull MessageStream<?> interceptOnHandle(
            @NonNull CommandMessage message,
            @NonNull ProcessingContext context,
            @NonNull MessageHandlerInterceptorChain<CommandMessage> chain) {
        String playerId = (String) message.metaData().get("playerId");
        validate(playerId);
        return chain.proceed(message, context);
    }
}
```

##### Dispatching commands from within an interceptor (AF5)

Instead of loading aggregates via `Repository`, use `CommandDispatcher.forContext(context)`:

```java
// AF4 — loading aggregate directly
Repository<ResourcesPool> repo = ...;
repo.loadOrCreate(id, () -> new ResourcesPool(id))
    .execute(rp -> rp.handle(cmd));

// AF5 — dispatch via CommandDispatcher bound to the current ProcessingContext
CommandDispatcher.forContext(context)
    .send(withdrawCommand)
    .resultAs(Void.class)
    .join();
```

##### Key changes

| Element | AF4 | AF5 |
|---------|-----|-----|
| Method name | `handle` | `interceptOnHandle` |
| Parameters | `UnitOfWork<? extends M>, InterceptorChain` | `M, ProcessingContext, MessageHandlerInterceptorChain<M>` |
| Return type | `Object` | `MessageStream<?>` |
| Chain call | `interceptorChain.proceed()` | `chain.proceed(message, context)` |
| Generic bound | `CommandMessage<?>` | `CommandMessage` (no wildcard) |
| Checked exceptions | `throws Exception` | removed |
| Access message | `unitOfWork.getMessage()` | use `message` parameter directly |

##### UnitOfWork lifecycle hook replacements

| AF4 | AF5 |
|-----|-----|
| `unitOfWork.onCommit(uow -> {…})` | `context.runOnAfterCommit(ctx -> {…})` |
| `unitOfWork.onPrepareCommit(uow -> {…})` | `context.runOnPreInvocation(ctx -> {…})` |
| `unitOfWork.onRollback(uow -> {…})` | `context.onError((ctx, err) -> {…})` |
| `unitOfWork.onCleanup(uow -> {…})` | `context.doFinally(ctx -> {…})` |

##### Notes

- **`chain.proceed()` → `chain.proceed(message, context)`** — must pass both arguments. Zero-arg form does not exist.
- **Generic de-wildcard is mandatory** — `CommandMessage<?>` → `CommandMessage`. Wildcard causes a compile error.
- **`throws Exception` removed** — the AF5 signature does not declare checked exceptions.
- **`ProcessingContext` is not `@Nullable`** here — always present during handling.

---

## sagas

### Saga Migration — @Saga → @Component @DisallowReplay

AF4 used the `@Saga` annotation (both `org.axonframework.spring.stereotype.Saga` for Spring and
`org.axonframework.modelling.saga.Saga` for SPI). AF5 replaces this with a regular Spring `@Component`
annotated `@DisallowReplay`, backed by JPA persistence. The `@SagaEventHandler` annotation is replaced
by `@EventHandler`.

##### Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.spring.stereotype.Saga` | *(remove)* |
| `org.axonframework.modelling.saga.Saga` | *(remove)* |
| `org.axonframework.modelling.saga.SagaEventHandler` | `org.axonframework.messaging.eventhandling.annotation.EventHandler` |
| `org.axonframework.modelling.saga.StartSaga` | *(remove — use `@EventHandler` for start)* |
| `org.axonframework.modelling.saga.EndSaga` | *(remove — close via lifecycle method)* |
| `org.axonframework.modelling.saga.SagaLifecycle` | *(remove)* |
| — | `@Component`, `@DisallowReplay` |

##### Detection

```bash
grep -rn '@Saga\|import.*stereotype.Saga\|import.*modelling.saga' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

##### Axon Framework 4 Code

```java
import org.axonframework.spring.stereotype.Saga;
import org.axonframework.modelling.saga.SagaEventHandler;
import org.axonframework.modelling.saga.StartSaga;
import org.axonframework.modelling.saga.EndSaga;
import org.axonframework.modelling.saga.SagaLifecycle;

@Saga
public class OrderFulfillmentSaga {

    @SagaEventHandler(associationProperty = "orderId")
    @StartSaga
    public void on(OrderPlacedEvent event) {
        SagaLifecycle.associateWith("orderId", event.orderId());
        // dispatch command...
    }

    @SagaEventHandler(associationProperty = "orderId")
    @EndSaga
    public void on(OrderDeliveredEvent event) {
        SagaLifecycle.end();
    }
}
```

##### Axon Framework 5 Code

```java
import org.springframework.stereotype.Component;
import org.axonframework.messaging.eventhandling.annotation.EventHandler;
import org.axonframework.messaging.eventhandling.replay.annotation.DisallowReplay;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "order_fulfillment_saga")
@Component
@DisallowReplay
public class OrderFulfillmentSaga {

    @Id
    private String orderId;

    // JPA-persisted state fields
    private String status;

    protected OrderFulfillmentSaga() { } // JPA required

    @EventHandler
    public CompletableFuture<?> on(OrderPlacedEvent event, CommandDispatcher commandDispatcher) {
        this.orderId = event.orderId();
        this.status = "STARTED";
        // save via repository, then dispatch...
        return commandDispatcher.send(new ProcessPaymentCommand(event.orderId()))
            .getResultMessage();
    }

    @EventHandler
    public void on(OrderDeliveredEvent event) {
        this.status = "COMPLETED";
        // save final state
    }
}
```

##### Architecture change: JPA persistence

AF5 sagas are **JPA entities** — the framework no longer manages saga state via its own store. You must:
1. Annotate the saga class with `@Entity` and `@Table`.
2. Add an `@Id` field for the correlation key.
3. Add a `protected` no-arg constructor for JPA.
4. Persist state changes manually using a Spring Data repository.
5. Load saga state in `@EventHandler` methods using the repository.

##### Notes

- **`@SagaEventHandler(associationProperty = …)` → plain `@EventHandler`** — AF5 routes events to processors
  by namespace; load the saga state from JPA using the event's correlation field.
- **`SagaLifecycle.associateWith(…)` removed** — no equivalent; correlation is handled by the JPA lookup.
- **`SagaLifecycle.end()` removed** — mark the saga "done" via a field and stop persisting it, or delete the
  JPA entity.
- **`@StartSaga` / `@EndSaga` removed** — lifecycle is now expressed through JPA entity existence.
- **Deadline Manager (`@DeadlineHandler`)** — no AF5 equivalent yet; this is a blocker if used.
- **`SagaTestFixture` removed** — no AF5 test fixture replacement; tests using it cannot be automatically migrated.

---

## event store

### Event Store Configuration — JPA

AF5 requires an explicit `EventStorageEngine` bean when using JPA (the in-process store). It is NOT
auto-configured by `axoniq-spring-boot-starter` when Axon Server is disabled.

##### Import Mappings

| AF4 | AF5 |
|-----|-----|
| *(auto-configured; no explicit bean)* | `org.axonframework.eventsourcing.eventstore.jpa.AggregateBasedJpaEventStorageEngine` |
| — | `org.axonframework.messaging.core.unitofwork.transaction.jpa.JpaTransactionalExecutorProvider` |
| — | `org.axonframework.messaging.eventhandling.conversion.EventConverter` |

##### Detection

```bash
grep -rn 'EventStorageEngine\|EmbeddedEventStore\|JpaEventStorageEngine' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

##### Axon Framework 4 Code (implicit auto-config)

```java
// No explicit configuration needed in AF4 with Spring Boot
// axon-spring-boot-starter auto-configured the JPA event store
```

##### Axon Framework 5 Code

```java
import org.axonframework.eventsourcing.eventstore.jpa.AggregateBasedJpaEventStorageEngine;
import org.axonframework.messaging.core.unitofwork.transaction.jpa.JpaTransactionalExecutorProvider;
import org.axonframework.messaging.eventhandling.conversion.EventConverter;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.autoconfigure.domain.EntityScan;

@Configuration
@EntityScan(basePackages = {
    "com.example",             // your project's package
    "org.axonframework",
    "io.axoniq.framework"
})
@ConditionalOnProperty(name = "axon.axonserver.enabled", havingValue = "false")
public class EventStoreConfiguration {

    @Bean
    public EventStorageEngine eventStorageEngine(
            EntityManagerFactory emf,
            EventConverter eventConverter) {
        return new AggregateBasedJpaEventStorageEngine(
            new JpaTransactionalExecutorProvider(emf),
            eventConverter,
            UnaryOperator.identity()
        );
    }
}
```

##### application.yaml — disable Axon Server

```yaml
axon:
  axonserver:
    enabled: false
```

##### @EntityScan requirement

AF5's JPA event store uses its own JPA entities. Add both `org.axonframework` and `io.axoniq.framework` to
the `@EntityScan` packages alongside your application's own packages, or the event store tables will not be created.

##### Notes

- This configuration is needed **only** when using the embedded JPA store (no Axon Server).
- When Axon Server is enabled (`axon.axonserver.enabled: true`), no explicit `EventStorageEngine` bean is needed.
- `AggregateBasedJpaEventStorageEngine` is the AF5 equivalent of AF4's `JpaEventStorageEngine`.
- `UnaryOperator.identity()` is the no-op event transformer (events stored as-is).

---

## tests

### AggregateTestFixture → AxonTestFixture

AF4 used `AggregateTestFixture<T>` for BDD-style aggregate testing. AF5 replaces it with `AxonTestFixture`
which wraps an `EventSourcingConfigurer` rather than a bare class reference.

##### Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.test.aggregate.AggregateTestFixture` | `org.axonframework.test.fixture.AxonTestFixture` |
| — | `org.axonframework.eventsourcing.configuration.EventSourcingConfigurer` |
| — | `org.axonframework.eventsourcing.configuration.EventSourcedEntityModule` |

##### Detection

```bash
grep -rn 'AggregateTestFixture' --include='*.java' --include='*.kt' --include='*.scala' .
```

##### Axon Framework 4 Code

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

##### Axon Framework 5 Code

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

##### Fluent DSL changes

| AF4 | AF5 |
|-----|-----|
| `fixture.given(events…)` | `fixture.given().events(events…)` |
| `fixture.givenNoPriorActivity()` | `fixture.given().noPriorActivity()` |
| `.when(cmd)` | `.when().command(cmd)` |
| `.expectEvents(events…)` | `.then().events(events…)` |
| `.expectException(Cls.class)` | `.then().exception(Cls.class)` |
| `.expectNoEvents()` | `.then().noEvents()` |

##### Exception behavior change

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

##### Partial migration state (post-OpenRewrite)

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

##### Notes

- **`fixture.stop()` in `@AfterEach` is required** — omitting it causes resource leaks across test runs.
- **`AxonTestFixture` is not generic** — no type parameter, unlike `AggregateTestFixture<T>`.
- **Child entities**: if the aggregate uses `@EntityMember` child entities, register each type in the configurer's
  `registerEntity(…)` calls.
- **`SagaTestFixture` removed** — no AF5 replacement; tests using it cannot be automatically migrated (blocker).

---
