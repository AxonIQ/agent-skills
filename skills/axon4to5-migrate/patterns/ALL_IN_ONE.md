# Axon Framework 4 → 5 Migration Patterns

Automatically generated — do not edit manually. Regenerate with:
```
make generate          # or: python3 scripts/generate_all_in_one.py
```

- [dependencies](#dependencies)
  - [Dependency Migration — Maven / Gradle](#dependency-migration--maven--gradle)
    - [Console starter is incompatible with AF5 and is NOT removed by OR](#console-starter-is-incompatible-with-af5-and-is-not-removed-by-or)
    - [AF4](#af4)
    - [AF5](#af5)
  - [Serializer → Converter](#serializer--converter)
    - [Code references](#code-references)
    - [Config keys](#config-keys)
    - [Leftover class-name references after the package move](#leftover-class-name-references-after-the-package-move)
    - [application.yaml](#applicationyaml)
    - [application.yaml](#applicationyaml)
    - [Find leftover class-name references after the package move](#find-leftover-class-name-references-after-the-package-move)
- [aggregates](#aggregates)
  - [Aggregate Class Stereotype](#aggregate-class-stereotype)
  - [AggregateLifecycle.apply() → EventAppender.append()](#aggregatelifecycleapply--eventappenderappend)
  - [@AggregateMember → @EntityMember (Child Entities)](#aggregatemember--entitymember-child-entities)
  - [Command Class Annotation](#command-class-annotation)
    - [Command payloads referenced from @CommandHandler methods; @RoutingKey usages.](#command-payloads-referenced-from-commandhandler-methods-routingkey-usages)
  - [@CommandHandler — Import Move + EventAppender Parameter](#commandhandler--import-move--eventappender-parameter)
  - [@CreationPolicy Removal](#creationpolicy-removal)
    - [Stray references OR could not strip (rare) and entity files that still need](#stray-references-or-could-not-strip-rare-and-entity-files-that-still-need)
    - [a manual ALWAYS-handler flip to `static` — list all @CommandHandler-bearing](#a-manual-always-handler-flip-to-static--list-all-commandhandler-bearing)
    - [files inside @EventSourced classes for review.](#files-inside-eventsourced-classes-for-review)
  - [@EntityCreator — No-Arg Constructor Annotation](#entitycreator--no-arg-constructor-annotation)
    - [Find aggregate classes and check their no-arg constructors](#find-aggregate-classes-and-check-their-no-arg-constructors)
  - [Event Class Annotations](#event-class-annotations)
    - [Find event classes (usually records in the events/ package)](#find-event-classes-usually-records-in-the-events-package)
    - [Events without @Event annotation — after OpenRewrite; look for record/class in events packages](#events-without-event-annotation--after-openrewrite-look-for-recordclass-in-events-packages)
  - [Event Emission in Aggregates](#event-emission-in-aggregates)
  - [@EventSourcingHandler — Import Package Move](#eventsourcinghandler--import-package-move)
  - [GenericDomainEventMessage Removal](#genericdomaineventmessage-removal)
  - [@TargetAggregateIdentifier Removal](#targetaggregateidentifier-removal)
    - [OR renames to @TargetEntityId — AF5 routes by idType, so AI removes annotation + import](#or-renames-to-targetentityid--af5-routes-by-idtype-so-ai-removes-annotation--import)
- [event handlers](#event-handlers)
  - [In-Handler Command Dispatch — CommandGateway → CommandDispatcher](#in-handler-command-dispatch--commandgateway--commanddispatcher)
    - [Find event-handling classes that inject CommandGateway](#find-event-handling-classes-that-inject-commandgateway)
    - [Compound shapes (loops, conditionals, multiple sequential dispatches) the](#compound-shapes-loops-conditionals-multiple-sequential-dispatches-the)
    - [recipe could not rewrite — CommandGateway field still present in @EventHandler classes.](#recipe-could-not-rewrite--commandgateway-field-still-present-in-eventhandler-classes)
  - [CommandGateway — Top-Level Dispatchers (REST/MCP/CLI)](#commandgateway--top-level-dispatchers-restmcpcli)
    - [Top-level classes that inject CommandGateway but are NOT event handlers](#top-level-classes-that-inject-commandgateway-but-are-not-event-handlers)
    - [sendAndWait callers (must be rewritten — no AF5 equivalent)](#sendandwait-callers-must-be-rewritten--no-af5-equivalent)
    - [AF5 import landed, but chain still calls .thenApply / .get on .send() —](#af5-import-landed-but-chain-still-calls-thenapply--get-on-send)
    - [won't compile because .send() now returns CommandResult, not CompletableFuture.](#wont-compile-because-send-now-returns-commandresult-not-completablefuture)
  - [EventBus → EventSink](#eventbus--eventsink)
  - [@EventHandler, @DisallowReplay, @ResetHandler — Import Package Moves](#eventhandler-disallowreplay-resethandler--import-package-moves)
  - [Message Accessor Renames](#message-accessor-renames)
  - [Metadata Type Change](#metadata-type-change)
  - [@MetaDataValue → @MetadataValue](#metadatavalue--metadatavalue)
  - [@ProcessingGroup → @Namespace (Event Processor Routing)](#processinggroup--namespace-event-processor-routing)
  - [Sequencing Policy Migration](#sequencing-policy-migration)
    - [OR injects `# TODO AF5 migration` above the obsolete YAML key — find those](#or-injects--todo-af5-migration-above-the-obsolete-yaml-key--find-those)
    - [Stray @Bean SequencingPolicy declarations the recipe could not remove](#stray-bean-sequencingpolicy-declarations-the-recipe-could-not-remove)
    - [application.yaml](#applicationyaml)
    - [application.yaml — remove sequencing-policy key; mode stays](#applicationyaml--remove-sequencing-policy-key-mode-stays)
- [query handlers](#query-handlers)
  - [@QueryHandler — Import Package Move](#queryhandler--import-package-move)
  - [Named Query — @QueryHandler(queryName) → @Query Payload Record](#named-query--queryhandlerqueryname--query-payload-record)
  - [QueryGateway — Drop ResponseTypes Wrappers](#querygateway--drop-responsetypes-wrappers)
    - [Sites the recipe could not finish — 3-argument named queries](#sites-the-recipe-could-not-finish--3-argument-named-queries)
    - [multipleInstancesOf sites — convert to queryMany](#multipleinstancesof-sites--convert-to-querymany)
    - [Sites the recipe could not finish — 3-argument named queries](#sites-the-recipe-could-not-finish--3-argument-named-queries)
    - [multipleInstancesOf sites — convert to queryMany](#multipleinstancesof-sites--convert-to-querymany)
  - [QueryUpdateEmitter — Constructor Field → Method Parameter](#queryupdateemitter--constructor-field--method-parameter)
    - [Import moved by ChangePackage, but field/constructor injection still present](#import-moved-by-changepackage-but-fieldconstructor-injection-still-present)
    - [AI moves it to a method parameter and adds Class<Q> arg to emit(...).](#ai-moves-it-to-a-method-parameter-and-adds-classq-arg-to-emit)
- [interceptors](#interceptors)
  - [MessageDispatchInterceptor — handle(List) → interceptOnDispatch](#messagedispatchinterceptor--handlelist--interceptondispatch)
    - [Signature rewritten by MigrateMessageInterceptorSignatures, body left alone.](#signature-rewritten-by-migratemessageinterceptorsignatures-body-left-alone)
    - [OR injects a `// TODO #LLM` class-level comment pointing at the migration doc.](#or-injects-a--todo-llm-class-level-comment-pointing-at-the-migration-doc)
  - [MessageHandlerInterceptor — Handle Method Signature Migration](#messagehandlerinterceptor--handle-method-signature-migration)
    - [Signature rewritten by MigrateMessageInterceptorSignatures, body left alone.](#signature-rewritten-by-migratemessageinterceptorsignatures-body-left-alone)
    - [OR injects a `// TODO #LLM` class-level comment pointing at the migration doc.](#or-injects-a--todo-llm-class-level-comment-pointing-at-the-migration-doc)
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

**Pre-migration (AF4 original):**

```bash
grep -rn 'org.axonframework' --include='pom.xml' --include='build.gradle' --include='build.gradle.kts' .
grep -rn 'axon.serializer' --include='*.yaml' --include='*.properties' .
```

**Post-OpenRewrite (partial AF5 shape):**

```bash
#### Console starter is incompatible with AF5 and is NOT removed by OR
grep -rn 'console-framework-client-spring-boot-starter' \
  --include='pom.xml' --include='build.gradle' --include='build.gradle.kts' .
```

Use the AF4 grep during Step 2 Assessment to scope the work. Use the post-OR grep during Step 4 Validate when the compile loop points at this pattern.

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
- **OpenRewrite status:** Partial — OR renames BOM (`Axon4ToAxon5Bom`), bumps versions, swaps starter to commercial (`axon4-to-axoniq5-spring.yml`), and renames the `axon.serializer` Spring property prefix; AI removes `console-framework-client-spring-boot-starter`.

---

### Serializer → Converter

AF5 renames the serialization SPI from `Serializer` to `Converter` and moves the package from
`org.axonframework.serialization` to `org.axonframework.conversion`. The Spring Boot property prefix moves
accordingly: `axon.serializer.*` → `axon.converter.*`. The OpenRewrite recipe does the package rename only —
concrete class names (`JacksonSerializer`, `XStreamSerializer`) are NOT auto-renamed and must be rewritten by AI.

##### Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.serialization.Serializer` | `org.axonframework.conversion.Converter` |
| `org.axonframework.serialization.json.JacksonSerializer` | `org.axonframework.conversion.json.JacksonConverter` |
| `org.axonframework.serialization.xml.XStreamSerializer` | *(no AF5 equivalent — replace with Jackson)* |
| YAML key `axon.serializer.*` | `axon.converter.*` |

##### Detection

**Pre-migration (AF4 original):**

```bash
#### Code references
grep -rn '\bSerializer\b\|JacksonSerializer\|XStreamSerializer' \
  --include='*.java' --include='*.kt' --include='*.scala' .

#### Config keys
grep -rn 'axon\.serializer' --include='*.yaml' --include='*.yml' --include='*.properties' .
```

**Post-OpenRewrite (partial AF5 shape):**

```bash
#### Leftover class-name references after the package move
grep -rn 'JacksonSerializer\|XStreamSerializer\|\bSerializer\b' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

Use the AF4 grep during Step 2 Assessment to scope the work. Use the post-OR grep during Step 4 Validate when the compile loop points at this pattern.

##### Axon Framework 4 Code

```java
import org.axonframework.serialization.Serializer;
import org.axonframework.serialization.json.JacksonSerializer;

@Bean
public Serializer serializer(ObjectMapper objectMapper) {
    return JacksonSerializer.builder()
            .objectMapper(objectMapper)
            .build();
}
```

```yaml
#### application.yaml
axon:
  serializer:
    general: jackson
    events: jackson
```

##### Axon Framework 5 Code

```java
import org.axonframework.conversion.Converter;
import org.axonframework.conversion.json.JacksonConverter;

@Bean
public Converter converter(ObjectMapper objectMapper) {
    return JacksonConverter.builder()
            .objectMapper(objectMapper)
            .build();
}
```

```yaml
#### application.yaml
axon:
  converter:
    general: jackson
    events: jackson
```

##### Notes

- **`XStreamSerializer` has no AF5 replacement** — AF5 standardises on Jackson. Migrate XStream-encoded events
  ahead of the upgrade, or keep an AF4 reader process alongside until the legacy stream is drained.
- **`SerializerType.XSTREAM` / `JAVA` enum values** in `application.yaml` are intentionally left untouched by the
  recipe — they have no `ConverterType` equivalent and would silently break event reading. Fix manually to
  `jackson` (or remove if the default suffices).
- **Bean name change is conventional, not mandatory.** Renaming the `@Bean` method `serializer` → `converter`
  matches the new SPI but the framework binds by type, not name.

##### Partial migration state (post-OpenRewrite)

OpenRewrite's `axon4-to-axon5-conversion.yml` runs a single `ChangePackage` rule that rewrites
`org.axonframework.serialization` → `org.axonframework.conversion` recursively. After the recipe:

- Imports such as `org.axonframework.conversion.json.JacksonSerializer` are correct in terms of package but the
  AF5 class is named `JacksonConverter` — the import will not resolve. AI renames the class references.
- The `Serializer` interface name itself is also still present in code (the recipe moves only the package, not
  the class name). Rewrite to `Converter`.
- `application.yaml` keys are renamed by `ChangeSpringPropertyKey` in `axon4-to-axon5-extension-spring.yml`
  (`axon.serializer` → `axon.converter`); nested child keys (`general`, `events`, `messages`) carry over
  unchanged.

```bash
#### Find leftover class-name references after the package move
grep -rn 'JacksonSerializer\|XStreamSerializer\|\bSerializer\b' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

##### Notes (continued)

- **OpenRewrite status:** Partial — `ChangePackage` in `axon4-to-axon5-conversion.yml` rewrites the package
  prefix, and `ChangeSpringPropertyKey` in `axon4-to-axon5-extension-spring.yml` rewrites the YAML key prefix; AI
  rewrites the concrete class names (`JacksonSerializer` → `JacksonConverter`, drop `XStreamSerializer`) and the
  `SerializerType` enum values inside YAML.

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

**Pre-migration (AF4 original):**

```bash
grep -rn '@Aggregate\|@AggregateRoot\|@AggregateIdentifier' --include='*.java' --include='*.kt' --include='*.scala' .
```

**Post-OpenRewrite (partial AF5 shape):**

```bash
grep -rn 'idType = Object\.class\|@EventSourced[^(]' --include='*.java' --include='*.kt' --include='*.scala' .
```

Use the AF4 grep during Step 2 Assessment to scope the work. Use the post-OR grep during Step 4 Validate when the compile loop points at this pattern.

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
- **OpenRewrite status:** Partial — `ChangeType` rewrites `@Aggregate` → `@EventSourced` and `ConfigureEventSourcedAnnotation` adds `tagKey = "<SimpleName>"` + `idType = Object.class` placeholder; AI replaces the `Object.class` placeholder with the real id class.
- **Reference source:** `examples/java/af5/src/main/java/com/dddheroes/heroesofddd/armies/write/Army.java` (AF4 form: `examples/java/af4/.../Army.java`).

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

OR's `ReplaceAggregateLifecycleApply` rewrites the common case in full (call site + parameter injection + static import removal). The remaining AI follow-up cases are narrow:

- **`AggregateLifecycle.markDeleted()`** is not rewritten — no AF5 equivalent. Remove the call and audit downstream code that relied on the deletion semantics.
- **`AggregateLifecycle.apply(...)` calls from non-aggregate utilities** (helper classes, base types) where OR's `onlyIfUsing` predicate didn't match. Rewrite manually per the Rules above.

```bash
grep -rn 'AggregateLifecycle\.\(apply\|markDeleted\)\|import .*AggregateLifecycle' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

##### Notes

- **`.messaging.` infix is mandatory** — `org.axonframework.messaging.eventhandling.gateway.EventAppender`. The path without `.messaging.` does not exist.
- **Do not call `AggregateLifecycle.markDeleted()`** — there is no AF5 equivalent; remove the call entirely.
- **OpenRewrite status:** Full — `ReplaceAggregateLifecycleApply` (in `axon4-to-axon5-eventsourcing.yml`) rewrites `AggregateLifecycle.apply(...)` → `eventAppender.append(...)` and injects the `EventAppender eventAppender` parameter into the enclosing method.
- **Reference source:** `examples/java/af5/src/main/java/com/dddheroes/heroesofddd/armies/write/Army.java`.

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
- **OpenRewrite status:** Full — `ChangeType` (in `axon4-to-axon5-modelling.yml`) rewrites `AggregateMember` → `EntityMember` with `routingKey` preserved.

---

### Command Class Annotation

AF5 requires every command payload type (record or class) that targets a `@CommandHandler` to carry the `@Command`
annotation. AF4 had no class-level annotation on command payloads — the framework discovered them implicitly via
handler signatures. AF5 makes the contract explicit and folds the AF4 `@RoutingKey` field into a `routingKey`
attribute on `@Command`.

##### Import Mappings

| AF4 | AF5 |
|-----|-----|
| *(no class annotation)* | `org.axonframework.messaging.commandhandling.annotation.Command` |
| `org.axonframework.commandhandling.RoutingKey` (field annotation) | `@Command(routingKey = "fieldName")` (attribute on `@Command`) |

##### Detection

```bash
#### Command payloads referenced from @CommandHandler methods; @RoutingKey usages.
grep -rn '@RoutingKey\|@CommandHandler' --include='*.java' --include='*.kt' --include='*.scala' .
```

##### Axon Framework 4 Code

```java
// No class-level annotation. Optional @RoutingKey on a non-target field
// when the routing identifier differs from @TargetAggregateIdentifier.
public record ShipOrderCommand(
    @TargetAggregateIdentifier String orderId,
    @RoutingKey String warehouseId,
    String address
) { }
```

##### Axon Framework 5 Code

```java
import org.axonframework.messaging.commandhandling.annotation.Command;

@Command(routingKey = "warehouseId")
public record ShipOrderCommand(
    String orderId,
    String warehouseId,
    String address
) { }
```

When the command had no `@RoutingKey`, just add `@Command`:

```java
@Command
public record ShipOrderCommand(String orderId, String address) { }
```

##### Notes

- **`@Command` is mandatory** — without it, AF5 cannot dispatch the payload through `CommandDispatcher` /
  `CommandGateway`. The compiler will not catch this; the failure surfaces at runtime as "no handler for command".
- **`routingKey` references the field by name (string)**. Multi-handler scenarios use this to map a single command
  to several entities — the value of that field selects the receiving instance.
- **`@TargetAggregateIdentifier` is removed entirely** (see `target-aggregate-identifier.md`) — the target id is
  resolved by matching the command class to a `@Command`-annotated payload whose `idType` aligns with the entity's
  `@EventSourced(idType = …)`. Do not re-add it as a `routingKey`.
- Plain commands (no special routing) require only `@Command` with no attributes.
- **OpenRewrite status:** Full — `AddCommandAnnotation` (in `axon4-to-axon5-eventsourcing.yml`) scans
  `@CommandHandler` methods, adds `@Command` to their payload types, and migrates `@RoutingKey` field annotations
  into the `routingKey` attribute on `@Command`.
- **Reference source:** `examples/java/af5/src/main/java/com/dddheroes/heroesofddd/armies/write/ArmyCommand.java`.

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

**Pre-migration (AF4 original):**

```bash
grep -rn 'import org\.axonframework\.commandhandling\.CommandHandler' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

**Post-OpenRewrite (partial AF5 shape):**

```bash
grep -rn '@CommandHandler' --include='*.java' --include='*.kt' --include='*.scala' . \
  | grep -v 'EventAppender'   # candidates — review each: legitimately param-less, or missed by OR?
```

Use the AF4 grep during Step 2 Assessment to scope the work. Use the post-OR grep during Step 4 Validate when the compile loop points at this pattern.

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

OR moves the import and (via `ReplaceAggregateLifecycleApply` in `axon4-to-axon5-eventsourcing.yml`) injects `EventAppender` into every handler that called `AggregateLifecycle.apply(...)`. Two AI follow-up cases remain:

- **Handlers that did not emit events in AF4** (validation-only, throw on bad state) are left without `EventAppender` — correct as-is unless you intend to start emitting events.
- **Aggregate handlers whose event emission was indirect** (via a helper method, base class, or `applyEvents(...)` loop OR's predicate didn't catch) — add `EventAppender eventAppender` as the **last** parameter and the `org.axonframework.messaging.eventhandling.gateway.EventAppender` import, then rewrite the body per [aggregate-lifecycle.md](aggregate-lifecycle.md). Do NOT touch the already-correct `@CommandHandler` import.

```bash
grep -rn '@CommandHandler' --include='*.java' --include='*.kt' --include='*.scala' . \
  | grep -v 'EventAppender'   # candidates — review each: legitimately param-less, or missed by OR?
```

##### Notes

- **`.messaging.` infix is mandatory** — `org.axonframework.messaging.commandhandling.annotation.CommandHandler`.
  The path `org.axonframework.commandhandling.annotation.CommandHandler` does not exist.
- **`EventAppender` is required on aggregate and child entity handlers** — see [aggregate-lifecycle.md](aggregate-lifecycle.md).
  On non-aggregate components (event handlers, services) `@CommandHandler` is typically not used — apply this
  pattern only when the handler is inside an `@EventSourced`/`@EventSourcedEntity` class.
- **OpenRewrite status:** Partial — `ChangeType` (in `axon4-to-axon5-messaging.yml`) moves the import; `EventAppender` is added only on handlers that called `AggregateLifecycle.apply(...)` — AI adds the parameter on remaining aggregate handlers.
- **Reference source:** `examples/java/af5/src/main/java/com/dddheroes/heroesofddd/armies/write/Army.java`.

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

**Pre-migration (AF4 original):**

```bash
grep -rn '@CreationPolicy\|AggregateCreationPolicy\|import.*CreationPolicy' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

**Post-OpenRewrite (partial AF5 shape):**

```bash
#### Stray references OR could not strip (rare) and entity files that still need
#### a manual ALWAYS-handler flip to `static` — list all @CommandHandler-bearing
#### files inside @EventSourced classes for review.
grep -rln '@CommandHandler' --include='*.java' --include='*.kt' --include='*.scala' . \
  | xargs grep -l '@EventSourced\|@EventSourcedEntity'
```

Use the AF4 grep during Step 2 Assessment to scope the work. Use the post-OR grep during Step 4 Validate when the compile loop points at this pattern.

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
- **OpenRewrite status:** Partial — `RemoveAnnotation` strips `@CreationPolicy` and `ConvertCommandHandlerConstructorToStaticMethod` converts AF4 command-handler constructors to AF5 static factory methods; AI still flips ALWAYS handlers that weren't constructors to `static` and reviews CREATE_IF_MISSING semantics manually.

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
- **OpenRewrite status:** Full — `AddEntityCreatorAnnotation` (in `axon4-to-axon5-eventsourcing.yml`) annotates the no-arg constructor of every `@EventSourced` / `@EventSourcedEntity` class.
- **Reference source:** `examples/java/af5/src/main/java/com/dddheroes/heroesofddd/armies/write/Army.java`.

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
- **OpenRewrite status:** Full — `AddEventAnnotation` (in `axon4-to-axon5-eventsourcing.yml`) adds `@Event` to event payload types and migrates `@Revision("N")` → `@Event(version = "N")`; `AddEventTagAnnotation` (in `axon4-to-axon5-modelling.yml`) adds `@EventTag(key = "<EntitySimpleName>")` to the routing field.
- **Reference source:** `examples/java/af5/src/main/java/com/dddheroes/heroesofddd/armies/events/ArmyEvent.java`.

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
- **OpenRewrite status:** Full — `ReplaceAggregateLifecycleApply` (in `axon4-to-axon5-eventsourcing.yml`) handles both the `apply(...)` → `eventAppender.append(...)` rewrite and the `EventAppender` parameter injection; the `@CommandHandler` import move is handled by `ChangeType` in `axon4-to-axon5-messaging.yml`.

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
- **OpenRewrite status:** Full — `ChangeType` (in `axon4-to-axon5-eventsourcing.yml`) rewrites the import to `eventsourcing.annotation.EventSourcingHandler`.
- **Reference source:** `examples/java/af5/src/main/java/com/dddheroes/heroesofddd/armies/write/Army.java`.

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
- **OpenRewrite status:** None — no OR rule rewrites `GenericDomainEventMessage` → `GenericEventMessage`; AI does the rewrite and drops the `aggregateType` / `sequenceNumber` constructor arguments.

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

**Pre-migration (AF4 original):**

```bash
grep -rn '@TargetAggregateIdentifier\|TargetAggregateIdentifier' --include='*.java' --include='*.kt' --include='*.scala' .
```

**Post-OpenRewrite (partial AF5 shape):**

```bash
#### OR renames to @TargetEntityId — AF5 routes by idType, so AI removes annotation + import
grep -rn '@TargetEntityId\|TargetEntityId' --include='*.java' --include='*.kt' --include='*.scala' .
```

Use the AF4 grep during Step 2 Assessment to scope the work. Use the post-OR grep during Step 4 Validate when the compile loop points at this pattern.

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
- **OpenRewrite status:** Partial — OR's `ChangeType` (in `axon4-to-axon5-modelling.yml`) renames the annotation to `@TargetEntityId` rather than removing it; AI removes both the annotation and its import since AF5 routes by `idType` instead.

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

**Pre-migration (AF4 original):**

```bash
#### Find event-handling classes that inject CommandGateway
grep -rln 'CommandGateway' --include='*.java' --include='*.kt' --include='*.scala' . \
  | xargs grep -l '@EventHandler'
```

**Post-OpenRewrite (partial AF5 shape):**

```bash
#### Compound shapes (loops, conditionals, multiple sequential dispatches) the
#### recipe could not rewrite — CommandGateway field still present in @EventHandler classes.
grep -rln 'CommandGateway' --include='*.java' --include='*.kt' --include='*.scala' . \
  | xargs grep -l '@EventHandler'
```

Use the AF4 grep during Step 2 Assessment to scope the work. Use the post-OR grep during Step 4 Validate when the compile loop points at this pattern.

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
  scheduled tasks. For top-level dispatchers (REST/MCP/CLI/scheduled), see
  [command-gateway-top-level.md](command-gateway-top-level.md).
- **Compensation logic**: AF4 try/catch around `sendAndWait` becomes `.exceptionallyCompose(…)` on the future.
  Forgetting this means compensation silently stops on failure.
- **Simple cases** where you do not need the result: `return commandDispatcher.send(cmd).getResultMessage().thenApply(_ -> null);`
- **OpenRewrite status:** Partial — `MigrateCommandGatewayInEventHandler` (in `axon4-to-axon5-messaging.yml`) rewrites single-dispatch and try/catch bodies; AI handles compound shapes (loops, multiple sequential dispatches, conditional branches).

---

### CommandGateway — Top-Level Dispatchers (REST/MCP/CLI)

Top-level entry points (REST controllers, MCP tools, CLI runners, scheduled jobs) keep using `CommandGateway` in
AF5 — they have no `ProcessingContext`, so they cannot switch to `CommandDispatcher` (which is the in-handler
pattern, see [command-dispatcher.md](command-dispatcher.md)). What changes is the **API shape**:
`.send(cmd)` now returns `CommandResult` (not `CompletableFuture` directly), so callers must chain
`.resultAs(<Type>.class)` to get a `CompletableFuture<Type>`. `.sendAndWait(cmd)` is removed — block by
chaining `.resultAs(...).orTimeout(...).join()` (or whatever the caller's blocking contract demands).

##### Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.commandhandling.gateway.CommandGateway` | `org.axonframework.messaging.commandhandling.gateway.CommandGateway` |
| `org.axonframework.commandhandling.GenericCommandMessage` | *(usually removed — send plain payloads)* |

##### Detection

**Pre-migration (AF4 original):**

```bash
#### Top-level classes that inject CommandGateway but are NOT event handlers
grep -rln '\bCommandGateway\b\|import.*commandhandling\.gateway\.CommandGateway' \
  --include='*.java' --include='*.kt' --include='*.scala' . \
  | xargs grep -L '@EventHandler'

#### sendAndWait callers (must be rewritten — no AF5 equivalent)
grep -rn '\.sendAndWait\s*(' --include='*.java' --include='*.kt' --include='*.scala' .
```

**Post-OpenRewrite (partial AF5 shape):**

```bash
#### AF5 import landed, but chain still calls .thenApply / .get on .send() —
#### won't compile because .send() now returns CommandResult, not CompletableFuture.
grep -rln 'org\.axonframework\.messaging\.commandhandling\.gateway\.CommandGateway' \
  --include='*.java' --include='*.kt' --include='*.scala' . \
  | xargs grep -nE '\.send\([^)]*\)\s*\.(thenApply|thenCompose|thenAccept|get|join)'
```

##### Axon Framework 4 Code

```java
import org.axonframework.commandhandling.gateway.CommandGateway;

@RestController
@RequestMapping("games/{gameId}")
class BuildDwellingRestApi {

    private final CommandGateway commandGateway;

    BuildDwellingRestApi(CommandGateway commandGateway) {
        this.commandGateway = commandGateway;
    }

    // Async: returns CompletableFuture directly
    @PutMapping("/dwellings/{dwellingId}")
    CompletableFuture<Void> putDwellings(@PathVariable String dwellingId, @RequestBody Body body) {
        var command = BuildDwelling.command(dwellingId, body.creatureId(), body.costPerTroop());
        return commandGateway.send(command);
    }

    // Sync: blocks and returns the result
    @PostMapping("/dwellings")
    String createDwelling(@RequestBody Body body) {
        return commandGateway.sendAndWait(BuildDwelling.command(body.id(), body.creatureId(), body.costPerTroop()));
    }
}
```

##### Axon Framework 5 Code

```java
import org.axonframework.messaging.commandhandling.gateway.CommandGateway;

import java.util.concurrent.TimeUnit;

@RestController
@RequestMapping("games/{gameId}")
class BuildDwellingRestApi {

    private final CommandGateway commandGateway;

    BuildDwellingRestApi(CommandGateway commandGateway) {
        this.commandGateway = commandGateway;
    }

    // Async: .send() returns CommandResult — call .resultAs(Type.class) to get CompletableFuture<Type>
    @PutMapping("/dwellings/{dwellingId}")
    CompletableFuture<Void> putDwellings(@PathVariable String dwellingId, @RequestBody Body body) {
        var command = BuildDwelling.command(dwellingId, body.creatureId(), body.costPerTroop());
        return commandGateway.send(command).resultAs(Void.class);
    }

    // Sync: chain .resultAs + .orTimeout(...).join() — sendAndWait is gone
    @PostMapping("/dwellings")
    String createDwelling(@RequestBody Body body) {
        return commandGateway
                .send(BuildDwelling.command(body.id(), body.creatureId(), body.costPerTroop()))
                .resultAs(String.class)
                .orTimeout(30, TimeUnit.SECONDS)
                .join();
    }
}
```

##### Rules

- **Top-level dispatchers (REST/MCP/CLI/scheduled) KEEP `CommandGateway`.** Do NOT switch to `CommandDispatcher` —
  that only works inside a `ProcessingContext`.
- **`.send(cmd)` returns `CommandResult`** — chain `.resultAs(<Type>.class)` to get a `CompletableFuture<Type>`.
  Use `Void.class` when the command has no return payload.
- **`.sendAndWait(cmd)` is gone** — replace with `.send(cmd).resultAs(<Type>.class).orTimeout(<n>, SECONDS).join()`.
  The timeout choice is **caller-specific**: REST controllers typically use a small per-request budget; CLI runners
  may use a longer or unbounded wait. Pick what matches the original `sendAndWait` semantics in your code.
- **Update the import** to `org.axonframework.messaging.commandhandling.gateway.CommandGateway` (the `.messaging.`
  infix). The OpenRewrite `ChangePackage` rule does this automatically — see the partial state below.
- **`GenericCommandMessage` wrapping is usually unnecessary** — send plain command payloads. Keep
  `GenericCommandMessage` only if you need to attach metadata via the message constructor; otherwise pass the
  payload directly.

##### Partial migration state (post-OpenRewrite)

OpenRewrite's `axon4-to-axon5-messaging.yml` runs a top-level `ChangePackage` from
`org.axonframework.commandhandling` → `org.axonframework.messaging.commandhandling`, so the **import** is
rewritten automatically. There is **no** OpenRewrite rule that rewrites the `.send(...)` / `.sendAndWait(...)`
chain — `MigrateCommandGatewayInEventHandler` only targets `@EventHandler` classes, not top-level dispatchers.

After OR runs, expect this half-state in REST/MCP/CLI classes:

- ✅ Import on the AF5 `…messaging.commandhandling.gateway.CommandGateway` path.
- ❌ Body still calls `.sendAndWait(cmd)` (does not compile — method removed).
- ❌ Body still chains `.send(cmd).thenApply(...)` / `.thenCompose(...)` / `.get()` (does not compile —
  `.send()` now returns `CommandResult`, not `CompletableFuture`).

AI completes the gap by inserting `.resultAs(<Type>.class)` between `.send(cmd)` and the downstream chain, and by
rewriting `.sendAndWait(cmd)` to `.send(cmd).resultAs(<Type>.class).orTimeout(...).join()`.

##### Notes

- **OpenRewrite status:** Partial — `ChangePackage` in `axon4-to-axon5-messaging.yml` moves the `CommandGateway`
  import to the `.messaging.` path; AI rewrites the `.send()`/`.sendAndWait()` call chains (insert `.resultAs(...)`,
  replace `.sendAndWait` with `.send().resultAs().orTimeout().join()`).
- For in-handler dispatch (a class with `@EventHandler` that dispatches commands), see
  [command-dispatcher.md](command-dispatcher.md) — that pattern switches to `CommandDispatcher`; this one keeps
  `CommandGateway`.
- **Reference source:** `examples/java/af5/src/main/java/com/dddheroes/heroesofddd/creaturerecruitment/write/builddwelling/BuildDwellingRestApi.java`.

---

### EventBus → EventSink

AF4 exposed `EventBus` as the SPI for publishing events outside an aggregate (REST controllers, scheduled tasks,
infrastructure bootstrappers). AF5 renames it to `EventSink` — the publish-only role is now in the type name. The
method shape is unchanged: `publish(EventMessage…)` still exists.

##### Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.eventhandling.EventBus` | `org.axonframework.messaging.eventhandling.EventSink` |

##### Detection

```bash
grep -rn '\bEventBus\b\|import.*eventhandling\.EventBus' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

##### Axon Framework 4 Code

```java
import org.axonframework.eventhandling.EventBus;
import org.axonframework.eventhandling.GenericEventMessage;

@RestController
public class OrderIngestController {

    private final EventBus eventBus;

    public OrderIngestController(EventBus eventBus) {
        this.eventBus = eventBus;
    }

    @PostMapping("/orders/ingest")
    public void ingest(@RequestBody OrderImported event) {
        eventBus.publish(new GenericEventMessage<>(event));
    }
}
```

##### Axon Framework 5 Code

```java
import org.axonframework.messaging.eventhandling.EventSink;
import org.axonframework.messaging.eventhandling.GenericEventMessage;

@RestController
public class OrderIngestController {

    private final EventSink eventSink;

    public OrderIngestController(EventSink eventSink) {
        this.eventSink = eventSink;
    }

    @PostMapping("/orders/ingest")
    public void ingest(@RequestBody OrderImported event) {
        eventSink.publish(new GenericEventMessage<>(event));
    }
}
```

##### Notes

- **Use `EventSink` from REST / CLI / scheduled tasks** — the top-level entry points that have no
  `ProcessingContext`. Inside `@CommandHandler` methods on an aggregate, use the injected `EventAppender`
  (see `aggregate-lifecycle.md`); never inject `EventSink` into an aggregate.
- **Rename only — no body changes required.** `publish(...)` keeps the same overloads. Field name, constructor
  parameter, and any local variables are conventionally renamed `eventBus` → `eventSink` for readability but the
  compiler does not require it.
- AF5 keeps `EventStore` (event-sourced storage) and `EventSink` (publish SPI) as distinct concerns. Code that
  read from the store via `EventBus` was already going through `EventStore` — that path is unaffected by this
  rename.
- **OpenRewrite status:** Full — `ChangeType` rule in `axon4-to-axon5-messaging.yml` rewrites
  `org.axonframework.messaging.eventhandling.EventBus` → `…EventSink` (after the upstream `ChangePackage` moves
  `eventhandling` under `messaging.eventhandling`). The field/variable name change is cosmetic and not performed
  by the recipe.

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
- **OpenRewrite status:** Full — `ChangeType` (in `axon4-to-axon5-messaging.yml`) handles all three annotation imports (`@EventHandler`, `@DisallowReplay`, `@ResetHandler`).
- **Reference source:** `examples/java/af5/src/main/java/com/dddheroes/heroesofddd/creaturerecruitment/read/DwellingReadModelProjector.java`.

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
- **OpenRewrite status:** Full — `ChangeMethodName` rules (in `axon4-to-axon5-messaging.yml`) rewrite `getPayload`/`getMetaData`/`getIdentifier`/`getTimestamp`/`getPayloadType` and the `withMetaData`/`andMetaData` siblings.

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
- **OpenRewrite status:** Full — `ChangeType` (in `axon4-to-axon5-messaging.yml`) rewrites `org.axonframework.messaging.MetaData` → `org.axonframework.messaging.core.Metadata`.

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
- **OpenRewrite status:** Full — `ChangeType` (in `axon4-to-axon5-messaging.yml`) rewrites the annotation type and import.

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
- **OpenRewrite status:** Full — `ChangeType` (in `axon4-to-axon5-common.yml`) rewrites `@ProcessingGroup` → `@Namespace`; the string value is preserved.
- **Reference source:** `examples/java/af5/src/main/java/com/dddheroes/heroesofddd/creaturerecruitment/read/DwellingReadModelProjector.java`.

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

**Pre-migration (AF4 original):**

```bash
grep -rn 'SequencingPolicy\|sequencing-policy' \
  --include='*.java' --include='*.kt' --include='*.scala' --include='*.yaml' --include='*.properties' .
```

**Post-OpenRewrite (partial AF5 shape):**

```bash
#### OR injects `# TODO AF5 migration` above the obsolete YAML key — find those
grep -rn '# TODO AF5 migration' --include='*.yaml' --include='*.yml' --include='*.properties' .
#### Stray @Bean SequencingPolicy declarations the recipe could not remove
grep -rn '@Bean\s\+SequencingPolicy\|SequencingPolicy<EventMessage' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

Use the AF4 grep during Step 2 Assessment to scope the work. Use the post-OR grep during Step 4 Validate when the compile loop points at this pattern.

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
- **OpenRewrite status:** Partial — `ChangePackage` moves the interface, `MigrateSequencingPolicyLambda` rewrites lambdas, and `AnnotateObsoleteSequencingPolicyProperty` injects a `# TODO` comment above the YAML key; AI replaces the YAML wiring with a class-level `@SequencingPolicy(type = …, parameters = …)` annotation.

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
- **OpenRewrite status:** Full — `ChangeType` (in `axon4-to-axon5-messaging.yml`) rewrites the `@QueryHandler` import to `messaging.queryhandling.annotation.QueryHandler`.

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
- **OpenRewrite status:** None — no OR rule rewrites `@QueryHandler(queryName = "…")` into a `@Query` payload record; AI introduces the record and updates the handler signature.

---

### QueryGateway — Drop ResponseTypes Wrappers

AF4 typed the expected response of `queryGateway.query(...)` through the `ResponseTypes` SPI
(`ResponseTypes.instanceOf(Foo.class)`, `ResponseTypes.multipleInstancesOf(Foo.class)`,
`ResponseTypes.optionalInstanceOf(Foo.class)`). AF5 drops the `org.axonframework.messaging.responsetypes`
package entirely. The gateway accepts `Class<R>` directly for single-instance responses, and exposes
`queryMany(...)` for multi-instance responses.

##### Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.messaging.responsetypes.ResponseTypes` | *(remove import — package is gone)* |
| `org.axonframework.messaging.responsetypes.ResponseType` | *(remove)* |
| `ResponseTypes.instanceOf(Foo.class)` | `Foo.class` |
| `ResponseTypes.optionalInstanceOf(Foo.class)` | `Foo.class` (gateway still returns a `CompletableFuture`) |
| `ResponseTypes.multipleInstancesOf(Foo.class)` | use `queryGateway.queryMany(query, Foo.class)` |

##### Detection

**Pre-migration (AF4 original):**

```bash
grep -rn 'ResponseTypes\.\|responsetypes\|multipleInstancesOf\|instanceOf' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

**Post-OpenRewrite (partial AF5 shape):**

```bash
#### Sites the recipe could not finish — 3-argument named queries
grep -rn 'queryGateway\.query("' --include='*.java' --include='*.kt' --include='*.scala' .
#### multipleInstancesOf sites — convert to queryMany
grep -rn 'multipleInstancesOf' --include='*.java' --include='*.kt' --include='*.scala' .
```

Use the AF4 grep during Step 2 Assessment to scope the work. Use the post-OR grep during Step 4 Validate when the compile loop points at this pattern.

##### Axon Framework 4 Code

```java
// Single-instance, named query, 3-argument form
Future<Dwelling> result = queryGateway.query(
        "findDwellingById",
        new FindDwellingByIdQuery(id),
        ResponseTypes.instanceOf(Dwelling.class));

// Multi-instance — list of results
Future<List<Dwelling>> all = queryGateway.query(
        new FindAvailableDwellingsQuery(),
        ResponseTypes.multipleInstancesOf(Dwelling.class));
```

##### Axon Framework 5 Code

```java
// Single-instance — 2-argument form, no name string
CompletableFuture<Dwelling> result = queryGateway.query(
        new FindDwellingByIdQuery(id),
        Dwelling.class);

// Multi-instance — explicit queryMany method
CompletableFuture<List<Dwelling>> all = queryGateway.queryMany(
        new FindAvailableDwellingsQuery(),
        Dwelling.class);
```

##### Notes

- **The query-name string is gone.** AF5 routes purely by the payload type. If the AF4 site passed a name that
  differs from the payload's simple class name, annotate the payload record with `@Query(name = "…")` (see
  `query-named.md`).
- **`queryMany` is the only way to get a collection.** Calling `query(..., Class<R>)` with a list-shaped query
  binds to a single-instance handler at runtime and fails.
- **`CompletableFuture`, not `Future`.** AF4's return type widens to `CompletableFuture` so `.join()` /
  `.thenApply(...)` chains work without casting.
- **`ResponseType` field declarations** (e.g. cached `ResponseType<List<X>>` constants used across multiple
  query sites) become `Class<X>` references — drop the wrapper entirely.

##### Partial migration state (post-OpenRewrite)

`Axon4ToAxon5QueryResponseTypes` in `axon4-to-axon5-messaging.yml` rewrites the **2-argument** typed-payload
form `query(payload, ResponseTypes.instanceOf(Foo.class))` → `query(payload, Foo.class)` and prunes the
`responsetypes` import when no references remain. The recipe deliberately leaves the **3-argument**
`query(name, payload, ResponseTypes…)` shape alone — that case needs the payload to gain `@Query(name = "…")`
(or to be renamed) before the wrapper can be removed safely. `RemoveUnusedImports` (composed in the same
recipe) cleans up any orphaned `responsetypes.*` imports after manual rewrites.

```bash
#### Sites the recipe could not finish — 3-argument named queries
grep -rn 'queryGateway\.query("' --include='*.java' --include='*.kt' --include='*.scala' .
#### multipleInstancesOf sites — convert to queryMany
grep -rn 'multipleInstancesOf' --include='*.java' --include='*.kt' --include='*.scala' .
```

##### Notes (continued)

- **OpenRewrite status:** Partial — `Axon4ToAxon5QueryResponseTypes` (in `axon4-to-axon5-messaging.yml`)
  rewrites the 2-argument `query(payload, ResponseTypes.instanceOf(...))` form; AI rewrites the 3-argument named
  query form, converts `multipleInstancesOf` call sites to `queryMany`, and finishes any
  `ResponseType<R>`-typed local/field declarations.

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

**Pre-migration (AF4 original):**

```bash
grep -rn 'QueryUpdateEmitter' --include='*.java' --include='*.kt' --include='*.scala' .
```

**Post-OpenRewrite (partial AF5 shape):**

```bash
#### Import moved by ChangePackage, but field/constructor injection still present
#### AI moves it to a method parameter and adds Class<Q> arg to emit(...).
grep -rn 'private.*QueryUpdateEmitter\|QueryUpdateEmitter\s\+[a-z][A-Za-z0-9_]*\s*[;,)]\|\.emit\s*(' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

Use the AF4 grep during Step 2 Assessment to scope the work. Use the post-OR grep during Step 4 Validate when the compile loop points at this pattern.

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
- **OpenRewrite status:** Partial — `ChangePackage` (in `axon4-to-axon5-messaging.yml`) moves `QueryUpdateEmitter` to `messaging.queryhandling`; AI converts the constructor field to a method parameter and adds the `Class<Q>` first argument to `emit(...)`.

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

**Pre-migration (AF4 original):**

```bash
grep -rn 'implements MessageDispatchInterceptor\|BiFunction.*handle.*List' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

**Post-OpenRewrite (partial AF5 shape):**

```bash
#### Signature rewritten by MigrateMessageInterceptorSignatures, body left alone.
#### OR injects a `// TODO #LLM` class-level comment pointing at the migration doc.
grep -rn 'interceptOnDispatch\|// TODO #LLM' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

Use the AF4 grep during Step 2 Assessment to scope the work. Use the post-OR grep during Step 4 Validate when the compile loop points at this pattern.

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
- **OpenRewrite status:** Partial — `ChangeType` moves the interface to `messaging.core.MessageDispatchInterceptor` and `MigrateMessageInterceptorSignatures` rewrites the method signature; AI rewrites the body (single-message processing, `chain.proceed(modified, context)`).

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

**Pre-migration (AF4 original):**

```bash
grep -rn 'implements MessageHandlerInterceptor\|UnitOfWork.*InterceptorChain\|InterceptorChain.*UnitOfWork' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

**Post-OpenRewrite (partial AF5 shape):**

```bash
#### Signature rewritten by MigrateMessageInterceptorSignatures, body left alone.
#### OR injects a `// TODO #LLM` class-level comment pointing at the migration doc.
grep -rn 'interceptOnHandle\|// TODO #LLM' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

Use the AF4 grep during Step 2 Assessment to scope the work. Use the post-OR grep during Step 4 Validate when the compile loop points at this pattern.

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
- **OpenRewrite status:** Partial — `ChangeType` moves the interface to `messaging.core.MessageHandlerInterceptor` and `MigrateMessageInterceptorSignatures` rewrites the method signature; AI rewrites the body (UoW hooks → `ProcessingContext`, `chain.proceed()` → `chain.proceed(message, context)`, `uow.getMessage()` → `message`).

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
- **OpenRewrite status:** None — no OR rule rewrites `@Saga` → `@Component + @Entity` or migrates `@SagaEventHandler` / `SagaLifecycle`; AI does the full JPA-saga rewrite.

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
- **OpenRewrite status:** None — no OR rule creates the `EventStoreConfiguration` bean or the `@EntityScan` / `axon.axonserver.enabled: false` settings; AI writes them from scratch.

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

**Pre-migration (AF4 original):**

```bash
grep -rn 'AggregateTestFixture' --include='*.java' --include='*.kt' --include='*.scala' .
```

**Post-OpenRewrite (partial AF5 shape):**

```bash
grep -rn 'new AxonTestFixture\|AxonTestFixture<' --include='*.java' --include='*.kt' --include='*.scala' .
```

Use the AF4 grep during Step 2 Assessment to scope the work. Use the post-OR grep during Step 4 Validate when the compile loop points at this pattern.

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
- **OpenRewrite status:** Partial — OR (in `axon4-to-axon5-test.yml`) renames the type via `ChangeType`, rewrites the fluent DSL (`MigrateAxonTestFixtureFluentApi`), regenerates setup (`MigrateAggregateTestFixtureSetup`), and adds a Java `@AfterEach tearDown()` (`AddAxonTestFixtureTearDown`); AI completes Kotlin tear-down, fills setup the recipe could not infer (`new AxonTestFixture(...)` left over), and replaces `AggregateNotFoundException` with the domain exception.
- **Reference source:** `examples/java/af5/src/test/java/com/dddheroes/heroesofddd/armies/write/ArmyTest.java`.

---
