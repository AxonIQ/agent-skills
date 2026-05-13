# Recipe: Aggregate-centric `EventStorageEngine` wiring

Atomic migration of the **event store backend wiring (code only)**: pick the right AF5 `EventStorageEngine` implementation and wire it up.

AF4 used `EmbeddedEventStore` + `JpaEventStorageEngine` / `JdbcEventStorageEngine` / Axon Server backed engine. AF5 collapses to a single bean of type `org.axonframework.eventsourcing.eventstore.EventStorageEngine`.

This is a one-shot recipe (Migration Phase #7) — no item iteration; one bean swap.

> 🚨 **SQL / DDL / data migration is OUT OF SCOPE.** This recipe does NOT
> emit, run, or curate any schema-migration script. The AF5 JPA table
> shape differs from AF4 (`domain_event_entry` → `aggregate_event_entry`);
> the user owns that schema change and the underlying data move
> out-of-band, on a non-prod copy first, with row counts verified.
> Recipe only swaps the **Java/Kotlin code** wiring.

> **Bootstrap-layer reads & generic write-side migration.** During the same Phase #7 sweep, route any class that reads `Configuration#eventStore()` / `eventBus()` OR declares generic write-side configuration (`@Bean ConfigurerModule` for non-Axon components, `DefaultConfigurer.defaultConfiguration()`, free-standing lifecycle hooks, `implements Lifecycle`, generic `configurer.registerComponent(...)`) through [configuration.md](configuration.md). Each such class is migrated as its own atomic item, separate from the storage-engine bean swap below.

## Canonical reference

- [../../docs/paths/event-store.adoc](../../docs/paths/event-store.adoc) — which `EventStorageEngine` to pick (DCB vs aggregate-based), `LegacyJpaEventStorageEngine`. Schema-change content in that doc is informational only — this recipe does not act on it.
- [../../docs/paths/snapshotting.adoc](../../docs/paths/snapshotting.adoc) — AF5.1 snapshot model (needed for the `accept-drop` vs `pause-migration` decision in [not-supported.md](not-supported.md)).
- [../../docs/paths/serializers.adoc](../../docs/paths/serializers.adoc) — `Serializer` → `Converter`, removal of `XStreamSerializer`.
- [../../docs/paths/index.adoc](../../docs/paths/index.adoc) §"Import and package changes".

Recipe holds bean-swap mechanics and the Path A / Path B wiring; concepts live in the docs above.

## Mandatory

This recipe is **MANDATORY for every AF4 → AF5 migration**. "Spring Boot starter auto-configures it" is NEVER a valid skip reason: the AF5 starter applies AF5 defaults (DCB-flat engine on Axon Server, `JpaEventStorageEngine` on relational backends), NOT a migration of the existing AF4 event store. Without the explicit `AggregateBased…EventStorageEngine` bean swap, the AF5 default cannot read AF4-stored events — the project will appear to start cleanly and then fail at first command/replay against legacy data. Run the recipe even when the project compiles without it.

## Goal

ONE registration of an `EventStorageEngine`, picked along TWO axes:

- **Wiring path** (from `inputs.wiring` — pinned at INIT, never re-asked):
  - **Path A — Spring Boot** (`wiring=spring-boot`): registered as a Spring `@Bean` (or auto-configured by the starter when no bean is present).
  - **Path B — framework Configurer** (`wiring=framework-config`): registered programmatically via `EventSourcingConfigurer.componentRegistry(...)`.
- **Backend sub-path** (chosen from inspection / `AskUserQuestion`):
  - **JPA** — `AggregateBasedJpaEventStorageEngine`. Schema change required out-of-band; user-owned, not done here.
  - **Axon Server** — `AggregateBasedAxonServerEventStorageEngine`. Explicit registration overrides the autoconfigured DCB-flat engine (preserves aggregate-keyed event log).

Recipe ships the code change only. Schema / data moves are explicitly out of scope (see banner above).

## Inputs

- target: FQ name of the configuration class that today declares the `EventStorageEngine` bean / Configurer registration (required)
- wiring: "spring-boot" | "framework-config" (required, supplied by orchestrator from progress.md Pinned-decisions)
- backend: `jpa` | `axon-server` (optional — derived from inspection; user picks via AskUserQuestion when ambiguous)

## Subagent guidelines

- subagent_type: general-purpose
- isolation: worktree
  # Bean swap can ripple through autoconfigure imports — worktree gives easy rollback if
  # the path picked turns out wrong (e.g. user wanted Path B but Path A was picked first).
- prompt-framing: |
  This is a one-shot bean swap. NO test runs as part of the recipe — runtime verification
  happens during stabilization, after the user has applied any required schema changes
  out-of-band on their database. The recipe's job is: pick the right AF5 engine, replace
  the bean / Configurer registration, surface custom-Serializer ports to the orchestrator.
  SQL / DDL / data migration is out of scope and must NOT be produced by this recipe.
- parallelism: single

## Preflight

1. **Read [not-supported.md](not-supported.md) first** — run every Detection grep listed there. If any blocker fires, follow that file's `AskUserQuestion` flow and apply its "Effect on Procedure" before doing anything else. Recipe must NOT proceed past Preflight while a blocker is unresolved.
2. Project already declares a single `EventStorageEngine` bean of an `AggregateBased*` type?
3. No leftover `JpaEventStorageEngine` / `JdbcEventStorageEngine` / `EmbeddedEventStore` references?
4. Compile clean?
5. If 2–4 all yes AND no blocker fired → return Output with `result: skipped`.

## Decision tree — which AF5 engine?

Inspect AF4 wiring before changing anything.

| AF4 wiring observed | AF5 target | Notes |
|---|---|---|
| `JpaEventStorageEngine.builder()…build()` (often inside `EmbeddedEventStore`) | `AggregateBasedJpaEventStorageEngine` | Backend = JPA. Schema change required out-of-band — user-owned, not done by this recipe. |
| `AxonServerEventStore` / `AxonServer*EventStore` autoconfigured by `axon-spring-boot-starter` | `AggregateBasedAxonServerEventStorageEngine` | Axoniq connector's `AxonServerConfigurationEnhancer` auto-registers `AxonServerEventStorageEngine` (DCB-flat), **NOT** the aggregate-based variant. To preserve aggregate-keyed event-log semantics, register `AggregateBasedAxonServerEventStorageEngine` explicitly. Backend = Axon Server. |
| `JdbcEventStorageEngine.builder()…build()` | *No drop-in equivalent in AF5 yet* | **Blocker — see [not-supported.md](not-supported.md) B2.** User picks JPA / Axon Server / defer. |
| `MongoEventStorageEngine` (from `axon-mongo` extension) | *No AF5 release of `axon-mongo`* | **Blocker — see [not-supported.md](not-supported.md) B1.** User picks Axon Server / JPA / pause / accept-stays-af4. |
| Custom `EventStorageEngine` subclass | Reimplement on top of `AggregateBased*EventStorageEngine` | **Blocker — see [not-supported.md](not-supported.md) B3.** Out of scope for one atomic invocation. |

### Detection (run from target root)

```bash
grep -RnE 'JpaEventStorageEngine|JdbcEventStorageEngine|MongoEventStorageEngine|EmbeddedEventStore|AxonServerEventStore' \
     --include='*.java' --include='*.kt' src 2>/dev/null

# Mongo extension signals:
grep -RnE 'org\.axonframework\.extensions\.mongo|axon-mongo' \
     --include='*.java' --include='*.kt' --include='pom.xml' --include='*.gradle*' . 2>/dev/null

# Spring Boot starter signals:
grep -RnE 'axon-server-connector|axoniq-spring-boot-starter|axon-spring-boot-starter' pom.xml */pom.xml 2>/dev/null
```

If project depends on `axoniq-spring-boot-starter` (or pre-migration `axon-spring-boot-starter` plus `axon-server-connector`), the **Axon Server backend** is almost always the right answer even if `JpaEventStorageEngine` bean co-exists.

After inspection, ask user with `AskUserQuestion` to confirm the **backend** (JPA vs Axon Server). Default to inspection's recommendation; mark it `(Recommended)`. The wiring path (A vs B) is NOT asked — it's already pinned in `inputs.wiring`.

### Blockers

Full detection greps + `AskUserQuestion` flows + Output decision keys live in [not-supported.md](not-supported.md). Run that file's checks during Preflight; this section just summarizes which rows of the decision tree route there.

| Decision-tree row | Blocker | File |
|---|---|---|
| `JdbcEventStorageEngine.builder()…build()` | B2 | [not-supported.md](not-supported.md) |
| `MongoEventStorageEngine` | B1 | [not-supported.md](not-supported.md) |
| Custom `EventStorageEngine` subclass | B3 | [not-supported.md](not-supported.md) |
| Custom `Serializer` (soft) | B4 | [not-supported.md](not-supported.md) |

## FQN cheat sheet

### AF4 — remove

| Element | FQN |
|---|---|
| `EmbeddedEventStore` | `org.axonframework.eventsourcing.eventstore.EmbeddedEventStore` |
| `JpaEventStorageEngine` | `org.axonframework.eventsourcing.eventstore.jpa.JpaEventStorageEngine` |
| `JdbcEventStorageEngine` | `org.axonframework.eventsourcing.eventstore.jdbc.JdbcEventStorageEngine` |
| `AxonServerEventStore` | `org.axonframework.axonserver.connector.event.axon.AxonServerEventStore` |
| `MongoEventStorageEngine` | `org.axonframework.extensions.mongo.eventsourcing.eventstore.MongoEventStorageEngine` |

### AF5 — add

| Element | FQN |
|---|---|
| `EventStorageEngine` (interface) | `org.axonframework.eventsourcing.eventstore.EventStorageEngine` |
| `AggregateBasedJpaEventStorageEngine` | `org.axonframework.eventsourcing.eventstore.jpa.AggregateBasedJpaEventStorageEngine` |
| `AggregateBasedAxonServerEventStorageEngine` | `io.axoniq.framework.axonserver.connector.event.AggregateBasedAxonServerEventStorageEngine` (ships in `io.axoniq.framework:axon-server-connector`, free) |
| `AggregateBasedJpaEventStorageEngineConfiguration` | `org.axonframework.eventsourcing.eventstore.jpa.AggregateBasedJpaEventStorageEngineConfiguration` |
| `AggregateEventEntry` (JPA entity) | `org.axonframework.eventsourcing.eventstore.jpa.AggregateEventEntry` |
| `JpaTransactionalExecutorProvider` | `org.axonframework.messaging.core.unitofwork.transaction.jpa.JpaTransactionalExecutorProvider` |
| `EventConverter` | `org.axonframework.messaging.eventhandling.conversion.EventConverter` |
| `Converter` | `org.axonframework.conversion.Converter` |
| `EventSourcingConfigurer` | `org.axonframework.eventsourcing.configuration.EventSourcingConfigurer` |
| `ComponentDefinition` | `org.axonframework.common.configuration.ComponentDefinition` |
| `ConfigurationEnhancer` | `org.axonframework.common.configuration.ConfigurationEnhancer` |

> AF5 replaced `Serializer` with `Converter` / `EventConverter`. New storage engines take an `EventConverter`, not a `Serializer`. If AF4 wired a `Serializer` bean as a constructor arg to the engine, that wiring is gone — `EventConverter` is resolved from the configuration registry.

### Path A — Spring Boot

#### Condition

- `inputs.wiring == "spring-boot"`. Project depends on `axon-spring-boot-starter` (AF4) or `axoniq-spring-boot-starter` (post-OpenRewrite AF5).

The two backends share Spring's auto-configuration vs explicit-bean dynamic; sub-paths split on backend.

#### Sub-path A.JPA — Spring Boot + JPA backend

##### Condition

- AF4 wiring observed via `JpaEventStorageEngine.builder()…build()` (typically inside an `EmbeddedEventStore`).
- ALSO the fallback target when AF4 used `JdbcEventStorageEngine` and the user picks "move to JPA + Hibernate over same DB."

##### A.JPA.0. What "auto-config" actually does (read this BEFORE step 1)

> ⚠️ Verified on `axoniq-spring-boot-starter:5.1.x` (bytecode inspection in `~/.m2`):
> **`JpaEventStoreAutoConfiguration` does NOT reliably win.**

Two enhancers race to register `EventStorageEngine`, both via `registerIfNotPresent(..., SearchScope.ALL)`:

| Enhancer | Source | `order()` | Engine registered |
|---|---|---|---|
| `AxonServerConfigurationEnhancer` | ServiceLoader-discovered from `axon-server-connector` (transitive of `axoniq-spring-boot-starter`) | `Integer.MIN_VALUE + 10` (= -2147483638) | `AxonServerEventStorageEngine` (DCB-flat) |
| `AggregateBasedJpaEventStorageEngineConfigurationEnhancer` | Spring `@Bean` from `JpaEventStoreAutoConfiguration` | `Integer.MAX_VALUE - 600` (≈ 2147483047) | `AggregateBasedJpaEventStorageEngine` |

Connector wins the race by ~4 billion in ordering. The JPA enhancer's later `registerIfNotPresent` finds the slot occupied → skips.

Critical: **`axon.axonserver.enabled: false` does NOT disable the connector's ServiceLoader enhancer.** The property only gates `@Bean` methods inside `AxonServerAutoConfiguration` (connection manager, `AxonServerConfiguration`). The ServiceLoader-discovered `AxonServerConfigurationEnhancer` is independent of Spring conditions and runs whenever the connector JAR is on the classpath — which it always is once Phase 1 OpenRewrite swaps `axon-spring-boot-starter` → `axoniq-spring-boot-starter`.

Net effect of "let auto-config win": DCB-flat `AxonServerEventStorageEngine` ends up registered against an Axon Server connection that doesn't exist (because `enabled=false` keeps the connection beans dormant). Application fails to publish events.

**Therefore: always declare an explicit `@Bean EventStorageEngine` on Path A.JPA.** The "no bean — let auto-config handle it" pattern from AF4 does NOT carry over.

The mechanism that makes the explicit `@Bean` win: `SpringComponentRegistry.hasComponent(Class, name, SearchScope.ALL)` checks **both** the local `Components` map AND the Spring `BeanFactory` (via `beanFactory.getBeanNamesForType(type).length > 0`). With `SearchScope.ALL` (which BOTH enhancers use), a Spring `@Bean` of type `EventStorageEngine` is visible BEFORE either enhancer runs — both `registerIfNotPresent` calls see the slot occupied and skip. Aggregate-based JPA wins regardless of enhancer ordering.

> **How to verify enhancer ordering on a future project** (if recipe claims drift):
> ```bash
> # 1. Find the connector enhancer in your local Maven cache
> find ~/.m2/repository/io/axoniq/framework/axon-server-connector -name '*.jar' -not -name '*-sources*'
> # 2. List ServiceLoader-discovered enhancers
> unzip -p <jar> META-INF/services/org.axonframework.common.configuration.ConfigurationEnhancer
> # 3. Inspect each enhancer's order() with javap
> unzip -p <jar> <enhancer-class-path> > /tmp/e.class && javap -p -c /tmp/e.class | grep -B1 -A8 'public int order'
> ```

##### A.JPA.1. Replace AF4 wiring with explicit `@Bean EventStorageEngine`

**Always declare an explicit Spring `@Bean EventStorageEngine`** — the AF4 "no bean, let auto-config handle it" pattern does NOT carry over (see A.JPA.0 for why).

If project declared its own AF4 `EventStore` / `EventStorageEngine` / `EmbeddedEventStore` `@Bean`, **delete those bean methods** (two beans of `EventStorageEngine` = startup failure), then add:

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

Imports:

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

`UnaryOperator.identity()` keeps `AggregateBasedJpaEventStorageEngineConfiguration` defaults. If AF4 explicitly tuned `batchSize` / `gapTimeout` / `persistenceExceptionResolver` etc., use the enhancer pattern in A.JPA.2 instead.

Also delete the `EmbeddedEventStore` bean — AF5 wires the event store from the engine alone.

##### A.JPA.2. Override defaults — register a `ConfigurationEnhancer`

Only when AF4 wiring tuned `batchSize`, `gapTimeout`, `lowestGlobalSequence`, `maxGapOffset`, `gapCleaningThreshold`, or the `PersistenceExceptionResolver`. Mirror the framework's `AggregateBasedJpaEventStorageEngineConfigurationEnhancer`:

```java
@Bean
public ConfigurationEnhancer aggregateBasedJpaEventStorageEngineCustomization(
        EntityManagerFactory entityManagerFactory,
        PersistenceExceptionResolver persistenceExceptionResolver) {

    return registry -> {
        UnaryOperator<AggregateBasedJpaEventStorageEngineConfiguration> configurer = config ->
                config.batchSize(200)
                      .gapTimeout(60_000)
                      .persistenceExceptionResolver(persistenceExceptionResolver);

        ComponentDefinition<EventStorageEngine> definition =
                ComponentDefinition.ofType(EventStorageEngine.class)
                                   .withBuilder(configuration ->
                                           new AggregateBasedJpaEventStorageEngine(
                                                   new JpaTransactionalExecutorProvider(entityManagerFactory),
                                                   configuration.getComponent(EventConverter.class),
                                                   configurer))
                                   .onShutdown(Phase.INBOUND_EVENT_CONNECTORS, ese -> {
                                       if (ese instanceof AggregateBasedJpaEventStorageEngine engine) {
                                           engine.close();
                                       }
                                   });

        registry.registerIfNotPresent(definition, SearchScope.ALL);
    };
}
```

Default knobs are usually fine — only introduce the enhancer if AF4 explicitly tuned them.

##### A.JPA.3. Custom `Serializer` → `Converter`

Different SPI; flag for user. The recipe does NOT auto-port a custom `Serializer`. AF5 ships matching default converters for Jackson/XStream — most projects work without changes. Subclassed serializers / custom `RevisionResolver` / `ContentTypeConverter` need redesign.

##### A.JPA.4. Schema change is out of band — flag, do not emit

AF5's JPA event store uses `aggregate_event_entry` (renamed columns, stricter constraints) instead of AF4's `domain_event_entry`. The framework cannot read AF4 events out of the old table.

> 🚨 **This recipe does NOT emit, run, or stage any SQL / DDL.** Schema change and any associated data move are the user's responsibility, executed out-of-band on a non-prod copy first. The recipe's job is only to flag that the schema change is needed.

Record one entry in the recipe's Output `notes` so the orchestrator surfaces it to the user (e.g. *"JPA backend selected — user must apply AF5 schema change for `aggregate_event_entry` table before runtime verification. See AF5 reference docs."*). Do not write `.sql` files into the target.

For the AF5 schema shape and a worked example of a possible rename script, point the user at the AF5 reference guide ([../../docs/paths/event-store.adoc](../../docs/paths/event-store.adoc) — informational only).

##### A.JPA.5. Entity scan — MANDATORY when an explicit `@Bean EventStorageEngine` is declared

> 🚨 **An explicit `@Bean EventStorageEngine` silently disables `@RegisterDefaultEntities`.**
> Path A.JPA.1 forces an explicit `@Bean EventStorageEngine` (see A.JPA.0 — auto-config does NOT reliably win when `axon-server-connector` is on the classpath). That bean trips the `@ConditionalOnMissingBean(EventStorageEngine.class)` guard on `JpaEventStoreAutoConfiguration`, which Spring evaluates BEFORE processing `@Import` — so the `DefaultEntityRegistrar` that would have appended `org.axonframework.eventsourcing.eventstore.jpa` to `AutoConfigurationPackages` never runs. Symptom at startup: `Could not resolve root entity 'AggregateEventEntry'`.

Without an `@EntityScan`, the project loses entity registration for **three** framework JPA entities, all in different packages, all gated by `@ConditionalOnMissingBean` on different autoconfig classes:

| Entity | Framework package | Autoconfig class |
|---|---|---|
| `AggregateEventEntry` | `org.axonframework.eventsourcing.eventstore.jpa` | `JpaEventStoreAutoConfiguration` |
| `TokenEntry` | `org.axonframework.eventhandling.tokenstore.jpa` | `JpaAutoConfiguration` |
| `DeadLetterEntry` | `io.axoniq.framework.messaging.eventhandling.deadletter.jpa` | `JpaDeadLetterQueueAutoConfiguration` (commercial line) |

Adding `@EntityScan` *displaces* `AutoConfigurationPackages` for JPA entity discovery, so a partial scan (just the event-store package) silently breaks the other framework entities. **Always scan the full set in one annotation.**

Add `@EntityScan` on the Spring Boot main application class (or any `@Configuration` class — `@EntityScan` is independent of `@SpringBootApplication`):

```java
import org.springframework.boot.autoconfigure.domain.EntityScan;

@SpringBootApplication
@EntityScan(basePackages = {
    "com.<app>",                  // project's own @Entity classes
    "org.axonframework",           // AggregateEventEntry + TokenEntry
    "io.axoniq.framework"          // DeadLetterEntry (commercial AF5 only — drop on free-af5 line)
})
public class <App>Application { ... }
```

If the project uses an explicit `LocalContainerEntityManagerFactoryBean` with fixed `packagesToScan` instead of Spring Boot's default scan, add the same three roots to that list — same rule, same reason.

Don't copy `AggregateEventEntry` / `TokenEntry` / `DeadLetterEntry` into the project; custom `DomainEventEntry` subclasses are out of scope (treated as a B3 custom-storage-engine blocker).

#### Sub-path A.AS — Spring Boot + Axon Server backend

##### Condition

- AF4 wiring uses `AxonServerEventStore` autoconfigured by the starter — even if `JpaEventStorageEngine` is also declared, the Axon Server backend is almost always correct here.

##### A.AS.0. What the connector autoconfig actually does

Verified on `axon-server-connector:5.x` (`AxonServerConfigurationEnhancer`, ServiceLoader-discovered):

- Registers `EventStorageEngine` via `AxonServerEventStorageEngineFactory.constructForContext(...)` → constructs **`AxonServerEventStorageEngine`** (DCB-flat).
- `AggregateBasedAxonServerEventStorageEngine` ships in the same JAR but has **no factory** and is **not auto-registered** — opt-in.
- Connector calls `registerIfNotPresent`, so any earlier-registered or Spring-bean-registered `EventStorageEngine` wins.

Choose based on the migration goal, not just on Axon Server presence:

| Goal | Engine | Path |
|---|---|---|
| Preserve AF4 aggregate-keyed event log on AF5 (orchestrator default — "legacy storage preserved") | `AggregateBasedAxonServerEventStorageEngine` | **B-aggregate** — explicit `@Bean`. |
| Migrate to AF5 DCB semantics (flat event log, no aggregate routing) | `AxonServerEventStorageEngine` | **B-DCB** — let autoconfig win. |

If unsure, ask user. Aggregate preservation is the safe default; DCB migration is a separate, larger initiative.

##### A.AS.1-aggregate. Declare explicit `@Bean EventStorageEngine`

Same mechanism as A.JPA.1: the Spring `@Bean` is visible to `SpringComponentRegistry.hasComponent(EventStorageEngine.class, ALL)` (which inspects both the local `Components` map AND `BeanFactory.getBeanNamesForType()`), so the connector's `registerIfNotPresent(...)` finds the slot occupied and skips. The aggregate-based engine wins:

```java
@Bean
public EventStorageEngine storageEngine(AxonServerConnectionManager connectionManager,
                                        EventConverter eventConverter) {
    // getConnection() = default context. Use getConnection(String) for non-default.
    return new AggregateBasedAxonServerEventStorageEngine(
            connectionManager.getConnection(),
            eventConverter
    );
}
```

Imports:

```java
import io.axoniq.framework.axonserver.connector.api.AxonServerConnectionManager;
import io.axoniq.framework.axonserver.connector.event.AggregateBasedAxonServerEventStorageEngine;
import org.axonframework.eventsourcing.eventstore.EventStorageEngine;
import org.axonframework.messaging.eventhandling.conversion.EventConverter;
```

If project also declared an AF4 `@Bean EventStore` / `@Bean EventStorageEngine`, **delete those** — two beans of `EventStorageEngine` = startup failure.

##### A.AS.1-DCB. Remove AF4 storage-engine wiring

Delete any AF4 `@Bean EventStore` / `@Bean EventStorageEngine`. With no Spring bean of that type, the connector's `AxonServerConfigurationEnhancer` auto-registers `AxonServerEventStorageEngine` (DCB-flat). Adding your own bean prevents autoconfig.

##### A.AS.2. Confirm connector dependency

```xml
<dependency>
    <groupId>io.axoniq.framework</groupId>
    <artifactId>axoniq-spring-boot-starter</artifactId>
</dependency>
```

(The OpenRewrite recipe should already have done this swap. Verify.)

##### A.AS.3. No schema work

Axon Server stores its own events; nothing to flag.

##### A.AS.4. Caveat — converter wiring

If AF4 explicitly wired a `Serializer` bean (e.g. Jackson) to the storage engine, port to a `Converter`/`EventConverter` bean. Without one, AF5 falls back to default converter, which may not round-trip events serialized by a customized AF4 Jackson serializer. Surface to user.

### Path B — framework Configurer

#### Condition

- `inputs.wiring == "framework-config"`. Project does NOT depend on Spring Boot starter (`axoniq-spring-boot-starter` / `axon-spring-boot-starter`). Wiring lives in code via `EventSourcingConfigurer.create()` / `componentRegistry(...)`.

#### Sub-path B.JPA — framework Configurer + JPA backend

```java
EventSourcingConfigurer configurer = EventSourcingConfigurer.create();

configurer.componentRegistry(registry ->
    registry.registerComponent(
        EventStorageEngine.class,
        configuration -> new AggregateBasedJpaEventStorageEngine(
            new JpaTransactionalExecutorProvider(entityManagerFactory),
            configuration.getComponent(EventConverter.class),
            cfg -> cfg.batchSize(100)
        )
    )
);
```

Same schema-change flagging as Path A's JPA sub-path applies (A.JPA.4). User owns the DDL / data move out-of-band; recipe records the requirement in Output `notes` only.

#### Sub-path B.AS — framework Configurer + Axon Server backend

```java
configurer.componentRegistry(registry ->
    registry.registerComponent(
        EventStorageEngine.class,
        configuration -> new AggregateBasedAxonServerEventStorageEngine(
            configuration.getComponent(AxonServerConnection.class),
            configuration.getComponent(EventConverter.class)
        )
    )
);
```

For Axon Server in framework-config setups, the connector's enhancer auto-registers the DCB-flat engine when on the classpath — explicit `componentRegistry.registerComponent(...)` is the override path for aggregate preservation.

No SQL migration on the Axon Server backend — Axon Server stores its own events.

## Procedure

1. Locate target.
   - if Inputs.target set → use it
   - else → first match of the AF4 storage-engine greps above
2. Inspect AF4 wiring (greps above + dependency check). Classify into one of the rows of the decision tree (which **backend**: JPA / Axon Server / blocker).
3. Pick path:
   - **Wiring path** is taken from `inputs.wiring` — A (Spring Boot) or B (framework Configurer). NEVER ask.
   - **Backend** comes from inspection / blocker resolution: `jpa` or `axon-server`.
   - any blocker resolved with `pause-migration` / `accept-stays-af4` / `defer-until-af5-jdbc` / `surface-and-defer` → Output with `result: blocked`, `caller-expects.next: record-and-skip`, exit (no bean swap).
4. Run path Steps (see ### Path A / ### Path B above; pick the right sub-path inside).
5. Surface custom-`Serializer` ports in Output `notes` (orchestrator records to `learnings.md`).
6. On the JPA backend, surface "schema change required, user-owned, out-of-band" in Output `notes` (no SQL artifact produced).
7. Verify against ## End condition.
8. Emit ## Output. Orchestrator commits the code change only.

## End condition

1. Configuration class compiles cleanly under an `isolated-<BeanSimpleName>` scope created by the external `axon4to5-isolatedtest` skill (compile-only invocation).
2. JPA backend only (sub-path A.JPA or B.JPA): user-owned schema change flagged in Output `notes` (no SQL produced or staged by the recipe).
3. Custom `Serializer` → `Converter` ports surfaced to the orchestrator in Output `notes` (orchestrator records to `learnings.md`).

> Runtime verification of the storage engine belongs to stabilization (after the user has applied any required schema change on the build's database out-of-band).

## Output

Emit exactly one fenced ```yaml block per the six-variant Output contract
([../output-contract.md](../output-contract.md)). Schema below shows the
`success` shape with all event-storage-engine `decisions` keys; for the
other five variants copy the matching example from `output-contract.md`.

```yaml
result: success | skipped | rejected | needs-decision | blocked | failed
target: <FQ config class>
reason: <one short line — required for every variant except success>
decisions:
  path: <A (Spring Boot) | B (framework Configurer)>     # taken from inputs.wiring
  backend: <jpa | axon-server>                            # picked from inspection / blocker resolution
  bean-replaced: <bean / component name>
  schema-change-flagged: <true | false>                   # true on JPA backend (user owns DDL out-of-band)
  serializer-ports-flagged: <list | "none">      # B4 (soft blocker)
  mongo-event-store: <none | move-to-axon-server | move-to-jpa | pause-migration | accept-stays-af4>   # B1
  jdbc-event-store: <none | move-to-jpa | move-to-axon-server | defer-until-af5-jdbc>                  # B2
  custom-storage-engine-subclass: <none | surface-and-defer | pause-migration>                          # B3
caller-expects:
  commit: <true | false>
  next: <proceed | ask-user | record-and-skip | halt | route-to:<recipe>>
notes: <optional free text — e.g. "JdbcEventStorageEngine present, no AF5 path; user picked defer-until-af5-jdbc; original @Bean preserved as commented block with TODO[AF5 migration: B2]">
```

Blocker keys (`B1` / `B2` / `B3` / `B4`) map to `result: blocked` or
`result: needs-decision` per [not-supported.md](not-supported.md).

## Caveats

- **SQL / DDL / data migration is OUT OF SCOPE.** This skill rewrites code only. The user runs any schema change and data move out-of-band, on a non-prod copy first, before deploying the AF5 build. Recipe only flags the requirement.
- **Never rely on JPA auto-config alone when `axon-server-connector` is on the classpath.** The connector's ServiceLoader-discovered `AxonServerConfigurationEnhancer` (`order = MIN_VALUE + 10`) outraces `JpaEventStoreAutoConfiguration`'s enhancer (`order ≈ MAX_VALUE - 600`) on `registerIfNotPresent` and registers DCB-flat `AxonServerEventStorageEngine` first — even with `axon.axonserver.enabled=false`. See A.JPA.0 for the bytecode-level explanation. Always declare an explicit Spring `@Bean EventStorageEngine` on Path A.JPA. The `axoniq-spring-boot-starter` swap (Phase 1 OpenRewrite) silently puts the connector on the classpath; "the project doesn't use Axon Server" is no defence.
- **Two `EventStorageEngine` beans = startup failure.** AF5 autoconfig backs off only when no other bean is present. Remove leftover AF4 `@Bean EventStore` / `@Bean EventStorageEngine`.
- **JDBC has no AF5 drop-in yet.** If AF4 used `JdbcEventStorageEngine`, stop and ask user to pick JPA or Axon Server. Don't write a custom AF5 JDBC engine inside a migration run.
- **Mongo has no AF5 release at all.** `MongoEventStorageEngine` and `axon-mongo-spring-boot-autoconfigure` pull AF4 transitives. Run the Mongo blocker prompt before any bean swap; never silently swap to a JPA/Axon Server engine over Mongo data — the event log itself needs out-of-band migration by the user.
- **Custom `Serializer` ≠ `Converter`.** Jackson/XStream defaults port automatically. Subclassed serializers / custom `RevisionResolver` / `ContentTypeConverter` are not one-line ports — surface to stabilization.
- **`AggregateEventEntry` table comes from the framework JAR.** Don't copy it. Custom `DomainEventEntry` subclasses = custom storage-engine subclass — out of scope.
- **Explicit `@Bean EventStorageEngine` silently kills `@RegisterDefaultEntities`.** Spring evaluates `@ConditionalOnMissingBean(EventStorageEngine.class)` on `JpaEventStoreAutoConfiguration` BEFORE processing its `@Import(DefaultEntityRegistrar.class)`, so framework JPA entities (`AggregateEventEntry`, `TokenEntry`, `DeadLetterEntry`) never reach `AutoConfigurationPackages`. Always pair the explicit bean with a project-wide `@EntityScan` covering `com.<app>`, `org.axonframework`, `io.axoniq.framework` (commercial line) — see A.JPA.5. Partial `@EntityScan` is worse than none: it displaces `AutoConfigurationPackages` entirely, breaking entities from other autoconfigs that were still firing.

## Verify (against End condition)

Invoke the external `axon4to5-isolatedtest` skill compile-only (see [../verification.md](../verification.md)):

```
Skill: axon4to5-isolatedtest
Inputs:
  target-name: <BeanSimpleName>                  # e.g. AxonConfig
  build-file: <target>/pom.xml | <target>/build.gradle(.kts)
  main-sources:
    - src/main/java/<…>/<ConfigClass>.java
  test-sources: []                               # compile-only run
  extra-deps:
    - org.axonframework:axon-eventsourcing:${axon5.version}
    # plus axon-eventsourcing-jpa OR axon-server-connector per chosen sub-path.
  cleanup: false
```

This recipe usually adds zero new tests. Runtime verification belongs to stabilization, after the user has applied any required schema change to the build's database out-of-band.
