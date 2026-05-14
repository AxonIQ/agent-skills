# Recipe: event-storage-engine

One-shot bean swap: pick the right AF5 `EventStorageEngine` and wire it.

AF4 used `EmbeddedEventStore` + `JpaEventStorageEngine` / `JdbcEventStorageEngine` / Axon Server-backed engine. AF5 collapses to a single bean of `org.axonframework.eventsourcing.eventstore.EventStorageEngine`.

> 🚨 **SQL / DDL / data migration is OUT OF SCOPE.** AF5 JPA tables differ from AF4 (`domain_event_entry` → `aggregate_event_entry`). The user owns schema + data move out-of-band on a non-prod copy first. Recipe only swaps the Java/Kotlin code wiring and flags the requirement in `notes`.

**This recipe is MANDATORY.** "The Spring Boot starter auto-configures it" is NEVER a valid skip — the AF5 starter applies AF5 defaults (DCB-flat on Axon Server, `JpaEventStorageEngine` on relational), NOT a migration of the existing AF4 event store. Without the explicit `AggregateBased…EventStorageEngine` bean, the project starts cleanly then fails at first command/replay against legacy data.

> **Bootstrap-layer reads & generic write-side migration** during the same event-storage-engine pass: any class reading `Configuration#eventStore()` / `eventBus()` OR declaring `@Bean ConfigurerModule` for non-Axon components, `DefaultConfigurer.defaultConfiguration()`, free-standing lifecycle hooks, `implements Lifecycle`, generic `configurer.registerComponent(...)` — migrate as separate items via Step W.

## Inputs

```yaml
target: <FQ config class declaring EventStorageEngine bean / Configurer registration>      # required
wiring: spring-boot | framework-config                                                       # pinned project decision
decisions: { ... }                                                                            # populated across re-resolutions
```

## Preflight

1. For each entry in `## Decision points` with `trigger: detected-at-preflight`, run its Detection. If it fires AND the key isn't in `inputs.decisions` → **🔒 await decision** for that key.
2. Inspect AF4 wiring (greps below) → populates `decisions.backend` deduction context.
3. Idempotency: project already declares a single `EventStorageEngine` bean of an `AggregateBased*` type, no leftover `JpaEventStorageEngine` / `JdbcEventStorageEngine` / `EmbeddedEventStore`, compile clean → `output { result: skipped }`.

### Inspection greps

```bash
grep -RnE 'JpaEventStorageEngine|JdbcEventStorageEngine|MongoEventStorageEngine|EmbeddedEventStore|AxonServerEventStore' --include='*.java' --include='*.kt' src
grep -RnE 'org\.axonframework\.extensions\.mongo|axon-mongo' --include='*.java' --include='*.kt' --include='pom.xml' --include='*.gradle*' .
grep -RnE 'axon-server-connector|axoniq-spring-boot-starter|axon-spring-boot-starter' pom.xml */pom.xml
```

If `axoniq-spring-boot-starter` / `axon-server-connector` is present, **Axon Server backend** is almost always the right answer even if `JpaEventStorageEngine` bean co-exists.

## Decision points

### backend

- **Trigger**: detected-at-preflight (always — every event-storage-engine run needs a backend choice)
- **Detection**: inspection greps above categorize the AF4 wiring into one of: `jpa-only`, `axon-server-only`, `both`, `mongo`, `jdbc`, `custom-subclass`.
- **Question**: > "Inspection suggests `<inferred>` backend. Confirm AF5 target?"
- **Options**:
    - `jpa` — `AggregateBasedJpaEventStorageEngine` (relational; schema migration out-of-band by user)
    - `axon-server` — `AggregateBasedAxonServerEventStorageEngine` (preserves aggregate-keyed log; Axon Server stores events)
- **Auto-policy**:
    - `pinned.license == "axoniq-commercial": axon-server`         # commercial deployments typically default to AS
    - `pinned.license == "free-af5": jpa`                          # free AF5 doesn't ship Axon Server connector
    - `fallback: ask-user`
- **Effect**:
    - `jpa` → run Path A.JPA (Spring Boot) or B.JPA (framework Configurer).
    - `axon-server` → run Path A.AS or B.AS.
- **Reference**: `## Decision tree` table below.

### mongo-event-store

- **Trigger**: detected-at-preflight
- **Detection**:
    ```
    grep -RnE 'MongoEventStorageEngine|org\.axonframework\.extensions\.mongo|axon-mongo' --include='*.java' --include='*.kt' --include='pom.xml' --include='*.gradle*' .
    ```
- **Question**: > "Project uses Mongo for event storage. No AF5 release of `axon-mongo`. How to handle?"
- **Options**:
    - `move-to-axon-server` — code rewrite only; user runs Mongo→AS data migration out-of-band BEFORE deploy
    - `move-to-jpa` — code rewrite only; user owns AF5 JPA schema change AND Mongo→relational data move
    - `pause-migration` — user replaces Mongo with supported store (incl. data) before resuming
    - `accept-stays-af4` — event-store slice stays AF4; recipe exits
- **Auto-policy**:
    - `fallback: ask-user`
- **Effect**:
    - `move-to-axon-server` → `decisions.backend = "axon-server"` (overrides default); proceed via Path A.AS / B.AS. Learnings: "user accepts Mongo→Axon Server data migration is out-of-band".
    - `move-to-jpa` → `decisions.backend = "jpa"`; proceed via Path A.JPA / B.JPA. Learnings: "user accepts Mongo→relational data move AND AF5 JPA schema change are out-of-band".
    - others → `output { result: blocked, reason: "mongo event store deferred — see blockers.md#B8" }`, exit.
- **Reference**: [blockers.md#B8](blockers.md#B8).

### jdbc-event-store

- **Trigger**: detected-at-preflight
- **Detection**:
    ```
    grep -RnE 'JdbcEventStorageEngine' --include='*.java' --include='*.kt' src
    ```
- **Question**: > "Project uses `JdbcEventStorageEngine` — no AF5 drop-in equivalent. How to handle?"
- **Options**:
    - `move-to-jpa` — code rewrite only; user owns AF5 schema change out-of-band
    - `move-to-axon-server` — code rewrite only; user runs JDBC→AS data migration out-of-band
    - `defer-until-af5-jdbc` — stop; wait for AF5 JDBC equivalent
- **Auto-policy**:
    - `pinned.license == "axoniq-commercial": move-to-axon-server`
    - `pinned.license == "free-af5": move-to-jpa`
    - `fallback: ask-user`
- **Effect**:
    - `move-to-jpa` / `move-to-axon-server` → set `decisions.backend` accordingly; proceed.
    - `defer-until-af5-jdbc` → `output { result: blocked, reason: "no AF5 JDBC equivalent — see blockers.md#B9" }`, exit.
- **Reference**: [blockers.md#B9](blockers.md#B9).

### custom-storage-engine-subclass

- **Trigger**: detected-at-preflight
- **Detection**:
    ```
    grep -RnE 'extends\s+(JpaEventStorageEngine|JdbcEventStorageEngine|MongoEventStorageEngine|AbstractEventStorageEngine|BatchingEventStorageEngine|AxonServerEventStore)\b' --include='*.java' --include='*.kt' src
    ```
- **Question**: > "Project subclasses `EventStorageEngine` for custom storage / encryption / multitenancy. Reimplementation on `AggregateBased*` is out of scope. How to handle?"
- **Options**:
    - `surface-and-defer` *(Recommended)* — follow-up issue; recipe exits
    - `pause-migration` — user removes subclass first
- **Auto-policy**:
    - `fallback: ask-user`
- **Effect**:
    - Either choice → `output { result: blocked, reason: "custom storage-engine subclass — see blockers.md#B10" }`, exit. No bean swap.
- **Reference**: [blockers.md#B10](blockers.md#B10).

### serializer-ports

- **Trigger**: triggered-in-procedure (during backend inspection)
- **Detection**: any `@Bean Serializer` (Path A), component-registry-bound `Serializer` (Path B), `XStreamSerializer` / `JacksonSerializer` subclass, custom `RevisionResolver`, custom `ContentTypeConverter`.
- **Question**: > "Project has a custom `Serializer` impl. AF5 uses `Converter` / `EventConverter` (different SPI). Jackson/XStream defaults port automatically; subclassed serializers do not. How to handle?"
- **Options**:
    - `flag-and-continue` — bean swap proceeds; custom `Serializer` recorded in `output.decisions.serializer-ports-flagged` for follow-up at stabilization
    - `pause-migration` — user redesigns the serializer first
- **Auto-policy**:
    - `always: flag-and-continue`     # soft blocker — never auto-block; user must inspect later
    - `fallback: ask-user`
- **Effect**:
    - `flag-and-continue` → continue procedure; record FQN list in `output.decisions.serializer-ports-flagged`.
    - `pause-migration` → `output { result: blocked }`, exit.
- **Reference**: [blockers.md#B10](blockers.md#B10) (soft blocker).

## Decision tree — which AF5 engine

After Decision-point resolution, `decisions.backend` is one of `jpa` / `axon-server`. The wiring path is pinned (`inputs.wiring`). Pick the path sub-section:

| `inputs.wiring` | `decisions.backend` | Path |
|---|---|---|
| `spring-boot` | `jpa` | A.JPA |
| `spring-boot` | `axon-server` | A.AS |
| `framework-config` | `jpa` | B.JPA |
| `framework-config` | `axon-server` | B.AS |

## FQN cheat sheet

| AF4 (remove) | FQN |
|---|---|
| `EmbeddedEventStore` | `org.axonframework.eventsourcing.eventstore.EmbeddedEventStore` |
| `JpaEventStorageEngine` | `org.axonframework.eventsourcing.eventstore.jpa.JpaEventStorageEngine` |
| `JdbcEventStorageEngine` | `org.axonframework.eventsourcing.eventstore.jdbc.JdbcEventStorageEngine` |
| `AxonServerEventStore` | `org.axonframework.axonserver.connector.event.axon.AxonServerEventStore` |
| `MongoEventStorageEngine` | `org.axonframework.extensions.mongo.eventsourcing.eventstore.MongoEventStorageEngine` |

| AF5 (add) | FQN |
|---|---|
| `EventStorageEngine` | `org.axonframework.eventsourcing.eventstore.EventStorageEngine` |
| `AggregateBasedJpaEventStorageEngine` | `org.axonframework.eventsourcing.eventstore.jpa.AggregateBasedJpaEventStorageEngine` |
| `AggregateBasedAxonServerEventStorageEngine` | `io.axoniq.framework.axonserver.connector.event.AggregateBasedAxonServerEventStorageEngine` (in `io.axoniq.framework:axon-server-connector`) |
| `JpaTransactionalExecutorProvider` | `org.axonframework.messaging.core.unitofwork.transaction.jpa.JpaTransactionalExecutorProvider` |
| `EventConverter` | `org.axonframework.messaging.eventhandling.conversion.EventConverter` |
| `ConfigurationEnhancer` | `org.axonframework.common.configuration.ConfigurationEnhancer` |
| `ComponentDefinition` | `org.axonframework.common.configuration.ComponentDefinition` |
| `EventSourcingConfigurer` | `org.axonframework.eventsourcing.configuration.EventSourcingConfigurer` |

AF5 replaced `Serializer` with `Converter` / `EventConverter`. Engines take `EventConverter` from the configuration registry — not a `Serializer` constructor arg.

## Procedure

1. Run Preflight (Decision points resolved).
2. Branch on (`inputs.wiring`, `decisions.backend`) per Decision tree → run the appropriate Path sub-section.
3. Run Step W (bootstrap-layer sweep) for any in-scope sibling config classes.
4. Emit `output`.

### Path A.JPA — Spring Boot + JPA

> ⚠️ **`JpaEventStoreAutoConfiguration` does NOT reliably win** when `axon-server-connector` is on the classpath. The connector's ServiceLoader-discovered `AxonServerConfigurationEnhancer` (`order = MIN_VALUE + 10`) outraces the JPA enhancer (`order ≈ MAX_VALUE - 600`) on `registerIfNotPresent` — registers DCB-flat `AxonServerEventStorageEngine` first. **`axon.axonserver.enabled=false` does NOT disable the ServiceLoader enhancer.** The Phase 1 OpenRewrite swap to `axoniq-spring-boot-starter` silently puts the connector on the classpath.
>
> **Therefore: always declare an explicit `@Bean EventStorageEngine`.** A Spring `@Bean` of type `EventStorageEngine` is visible to `SpringComponentRegistry.hasComponent(... SearchScope.ALL)` (which checks `BeanFactory` too) — both enhancers see the slot occupied and skip.

**A.JPA.1 — Replace AF4 wiring with explicit `@Bean`:**

Delete any AF4 `@Bean EventStore` / `@Bean EventStorageEngine` / `EmbeddedEventStore` (two beans of `EventStorageEngine` = startup failure). Add:

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

Imports: `jakarta.persistence.EntityManagerFactory`, `org.axonframework.eventsourcing.eventstore.EventStorageEngine`, `…jpa.AggregateBasedJpaEventStorageEngine`, `…transaction.jpa.JpaTransactionalExecutorProvider`, `…conversion.EventConverter`, Spring `@Bean`/`@Configuration`, `java.util.function.UnaryOperator`.

`UnaryOperator.identity()` keeps defaults. If AF4 explicitly tuned `batchSize` / `gapTimeout` / `persistenceExceptionResolver`, use A.JPA.2 instead.

**A.JPA.2 — Tune defaults via `ConfigurationEnhancer`** (only when AF4 actually tuned them):

```java
@Bean
public ConfigurationEnhancer aggregateBasedJpaEventStorageEngineCustomization(
        EntityManagerFactory emf, PersistenceExceptionResolver per) {
    return registry -> {
        UnaryOperator<AggregateBasedJpaEventStorageEngineConfiguration> cfg = c ->
                c.batchSize(200).gapTimeout(60_000).persistenceExceptionResolver(per);
        ComponentDefinition<EventStorageEngine> def =
                ComponentDefinition.ofType(EventStorageEngine.class)
                    .withBuilder(configuration -> new AggregateBasedJpaEventStorageEngine(
                            new JpaTransactionalExecutorProvider(emf),
                            configuration.getComponent(EventConverter.class),
                            cfg))
                    .onShutdown(Phase.INBOUND_EVENT_CONNECTORS, ese -> {
                        if (ese instanceof AggregateBasedJpaEventStorageEngine engine) engine.close();
                    });
        registry.registerIfNotPresent(def, SearchScope.ALL);
    };
}
```

**A.JPA.3 — Custom `Serializer` → `Converter`** — already surfaced via [`serializer-ports`](#serializer-ports) decision point; do NOT auto-port.

**A.JPA.4 — Schema change is out of band** — record one entry in `output.notes` (e.g. *"JPA backend selected — user must apply AF5 schema change for `aggregate_event_entry` before runtime verification."*). Do NOT write `.sql` files.

**A.JPA.5 — `@EntityScan` is MANDATORY when declaring explicit `@Bean EventStorageEngine`:**

> 🚨 Explicit `@Bean EventStorageEngine` trips `@ConditionalOnMissingBean(EventStorageEngine.class)` on `JpaEventStoreAutoConfiguration`, which Spring evaluates BEFORE processing `@Import` — the `DefaultEntityRegistrar` that appends `org.axonframework.eventsourcing.eventstore.jpa` to `AutoConfigurationPackages` never runs. Symptom: `Could not resolve root entity 'AggregateEventEntry'`.

Three framework JPA entities to register:

| Entity | Package |
|---|---|
| `AggregateEventEntry` | `org.axonframework.eventsourcing.eventstore.jpa` |
| `TokenEntry` | `org.axonframework.eventhandling.tokenstore.jpa` |
| `DeadLetterEntry` (commercial) | `io.axoniq.framework.messaging.eventhandling.deadletter.jpa` |

```java
@SpringBootApplication
@EntityScan(basePackages = {
    "com.<app>",                  // project's own @Entity
    "org.axonframework",          // AggregateEventEntry + TokenEntry
    "io.axoniq.framework"         // DeadLetterEntry — drop on free-af5 line
})
public class <App>Application { ... }
```

Partial `@EntityScan` is **worse than none** — it displaces `AutoConfigurationPackages` entirely.

If the project uses explicit `LocalContainerEntityManagerFactoryBean` with `packagesToScan`, add the same three roots there.

### Path A.AS — Spring Boot + Axon Server

Connector enhancer auto-registers `AxonServerEventStorageEngine` (DCB-flat). `AggregateBasedAxonServerEventStorageEngine` ships in the same JAR but is **not auto-registered**.

| Goal | Engine | Strategy |
|---|---|---|
| Preserve AF4 aggregate-keyed event log (default — "legacy storage preserved") | `AggregateBasedAxonServerEventStorageEngine` | explicit `@Bean` (overrides autoconfig — same `SearchScope.ALL` mechanism as A.JPA) |
| Migrate to AF5 DCB semantics | `AxonServerEventStorageEngine` | let autoconfig win — delete any AF4 `@Bean EventStore` / `@Bean EventStorageEngine` |

**A.AS.1 (aggregate, recommended):**

```java
@Bean
public EventStorageEngine storageEngine(AxonServerConnectionManager connectionManager,
                                        EventConverter eventConverter) {
    return new AggregateBasedAxonServerEventStorageEngine(
            connectionManager.getConnection(),    // default context
            eventConverter);
}
```

Imports: `io.axoniq.framework.axonserver.connector.api.AxonServerConnectionManager`, `io.axoniq.framework.axonserver.connector.event.AggregateBasedAxonServerEventStorageEngine`, `org.axonframework.eventsourcing.eventstore.EventStorageEngine`, `org.axonframework.messaging.eventhandling.conversion.EventConverter`. Delete any AF4 `@Bean EventStore` / `@Bean EventStorageEngine`.

**A.AS.2** — confirm `io.axoniq.framework:axoniq-spring-boot-starter` (Phase 1 OpenRewrite should have done this).

**A.AS.3** — no schema work. Axon Server stores its own events.

**A.AS.4** — custom `Serializer` flagged via [`serializer-ports`](#serializer-ports).

### Path B.JPA — framework Configurer + JPA

```java
configurer.componentRegistry(registry ->
    registry.registerComponent(
        EventStorageEngine.class,
        configuration -> new AggregateBasedJpaEventStorageEngine(
            new JpaTransactionalExecutorProvider(entityManagerFactory),
            configuration.getComponent(EventConverter.class),
            cfg -> cfg.batchSize(100))));
```

Same schema-change flagging as A.JPA.4.

### Path B.AS — framework Configurer + Axon Server

```java
configurer.componentRegistry(registry ->
    registry.registerComponent(
        EventStorageEngine.class,
        configuration -> new AggregateBasedAxonServerEventStorageEngine(
            configuration.getComponent(AxonServerConnection.class),
            configuration.getComponent(EventConverter.class))));
```

No schema work.

### Step W — Bootstrap-layer configuration sweep

During the same event-storage-engine pass, migrate each class that:
- reads `Configuration#eventStore()` / `eventBus()`, OR
- declares `@Bean ConfigurerModule` for non-Axon components, OR
- calls `DefaultConfigurer.defaultConfiguration()`, OR
- has free-standing lifecycle hooks, OR
- `implements Lifecycle`, OR
- calls generic `configurer.registerComponent(...)`.

Each such class migrates as an **atomic item** separate from the storage-engine bean swap. Common rewrites:

| AF4 | AF5 |
|---|---|
| `org.axonframework.config.Configurer` | `org.axonframework.configuration.MessagingConfigurer` / `ModellingConfigurer` / `EventSourcingConfigurer` |
| `org.axonframework.config.ConfigurerModule` | `org.axonframework.configuration.ConfigurationEnhancer` (Spring `@Bean`) |
| `DefaultConfigurer.defaultConfiguration()` | `MessagingConfigurer.create()` / `EventSourcingConfigurer.create()` |
| `implements Lifecycle` | register lifecycle on `ComponentRegistry` |
| `configurer.registerComponent(...)` | `configurer.componentRegistry(reg -> reg.registerComponent(...))` |
| `eventStore()` lookup | `configuration.getComponent(EventStorageEngine.class)` |
| `eventBus()` lookup | inject `EventSink` (`org.axonframework.messaging.eventhandling.EventSink`) |

## End condition

1. Config class compiles cleanly under an `isolated-<ClassName>` scope (compile-only `axon4to5-isolatedtest`).
2. JPA backend: schema-change requirement flagged in `output.notes` (no SQL produced).
3. Custom `Serializer` ports surfaced in `output.decisions.serializer-ports-flagged`.

Runtime verification belongs to stabilization (after user applies any schema change).

## Output

```yaml
result: success | skipped | rejected | blocked | failed
target: <FQ config class>
reason: <one short line>
decisions:
  path: A (Spring Boot) | B (framework Configurer)
  backend: jpa | axon-server
  bean-replaced: <bean / component name>
  schema-change-flagged: true | false
  serializer-ports-flagged: [<FQN>, …] | none
  mongo-event-store: none | move-to-axon-server | move-to-jpa | pause-migration | accept-stays-af4
  jdbc-event-store: none | move-to-jpa | move-to-axon-server | defer-until-af5-jdbc
  custom-storage-engine-subclass: none | surface-and-defer | pause-migration
files_touched:
  - <repo-relative path>
notes: <e.g. "JdbcEventStorageEngine present, no AF5 path; user picked defer-until-af5-jdbc; original @Bean preserved as commented block with TODO[AF5 migration: B9]">
```

## Subagent guidelines

```yaml
subagent_type: general-purpose
isolation: worktree                    # bean swap can ripple through autoconfigure imports
parallelism: single
on_unexpected_condition: keep-edits-and-fail
prompt-framing: |
  One-shot bean swap. NO test runs as part of the recipe — runtime verification happens
  during stabilization, after the user has applied any required schema changes out-of-band.
  Pick the right AF5 engine, replace the bean / Configurer registration, surface custom-Serializer
  ports in Output decisions. SQL / DDL / data migration MUST NOT be produced.
```

**Eligibility**: subagent-eligible only AFTER `backend`, `mongo-event-store`, `jdbc-event-store`, `custom-storage-engine-subclass`, `serializer-ports` are resolved (each has `fallback: ask-user` so main session must resolve interactively unless pinned).

## Caveats

- **Never rely on JPA auto-config alone when `axon-server-connector` is on the classpath** — see A.JPA preamble.
- **Two `EventStorageEngine` beans = startup failure.** Delete leftover AF4 beans.
- **JDBC has no AF5 drop-in.** Decision point [`jdbc-event-store`](#jdbc-event-store) forces the choice; never silently rewrite.
- **Mongo has no AF5 release.** Decision point [`mongo-event-store`](#mongo-event-store) forces the choice; never silently swap to JPA/Axon Server over Mongo data — the event log needs out-of-band migration.
- **Custom `Serializer` ≠ `Converter`.** Subclassed serializers / custom `RevisionResolver` / `ContentTypeConverter` are not one-line ports — surfaced via [`serializer-ports`](#serializer-ports).
- **`AggregateEventEntry` comes from the framework JAR.** Don't copy it. Custom `DomainEventEntry` subclasses = custom storage-engine = [`custom-storage-engine-subclass`](#custom-storage-engine-subclass) blocker.
- **Explicit `@Bean EventStorageEngine` kills `@RegisterDefaultEntities`** — see A.JPA.5. Always pair with project-wide `@EntityScan`.

## Reference pairs (AF4 → AF5)

Bundled in [evals/fixtures/](../evals/fixtures/):

- **Spring Boot + JPA + `axon.axonserver.enabled: false`** (the classic A.JPA case with the classpath connector — explicit `@Bean` required): the trio `axon4/heroes/{GameConfiguration.java, HeroesOfDDDApplication.java, application.yaml}` ↔ `axon5/heroes/...`. Shows the YAML `serializer` → `converter` rename, `sequencing-policy` keys removed (moved to class-level `@SequencingPolicy` annotation in the event-processor recipe), and the mandatory `@EntityScan(basePackages = { "com.<app>", "org.axonframework", "io.axoniq.framework" })`.
- **Spring Boot + Axon Server backend (A.AS, autoconfig adequate):** `axon4/gamerental/Game.java` ↔ `axon5/gamerental/Game.java`. Bundled for the aggregate side of the same project.
