# Recipe: event-storage-engine (Migration Phase #8)

One-shot bean swap: pick the right AF5 `EventStorageEngine` and wire it.

AF4 used `EmbeddedEventStore` + `JpaEventStorageEngine` / `JdbcEventStorageEngine` / Axon Server-backed engine. AF5 collapses to a single bean of `org.axonframework.eventsourcing.eventstore.EventStorageEngine`.

> 🚨 **SQL / DDL / data migration is OUT OF SCOPE.** AF5 JPA tables differ from AF4 (`domain_event_entry` → `aggregate_event_entry`). The user owns schema + data move out-of-band on a non-prod copy first. Recipe only swaps the Java/Kotlin code wiring and flags the requirement in `notes`.

**This recipe is MANDATORY.** "The Spring Boot starter auto-configures it" is NEVER a valid skip — the AF5 starter applies AF5 defaults (DCB-flat on Axon Server, `JpaEventStorageEngine` on relational), NOT a migration of the existing AF4 event store. Without the explicit `AggregateBased…EventStorageEngine` bean, the project starts cleanly then fails at first command/replay against legacy data.

> **Bootstrap-layer reads & generic write-side migration** during the same Phase #8 sweep: any class reading `Configuration#eventStore()` / `eventBus()` OR declaring `@Bean ConfigurerModule` for non-Axon components, `DefaultConfigurer.defaultConfiguration()`, free-standing lifecycle hooks, `implements Lifecycle`, generic `configurer.registerComponent(...)` — migrate as separate items via the Step W block below.

## Inputs

- `target` — FQ class declaring the `EventStorageEngine` bean / Configurer registration (required)
- `wiring` — `spring-boot` | `framework-config` (pinned)
- `backend` — `jpa` | `axon-server` (optional; derived from inspection, ask user when ambiguous)

## Preflight

1. Read [not-supported.md](not-supported.md), resolve every Detection grep.
2. Project already declares a single `EventStorageEngine` bean of an `AggregateBased*` type? No leftover `JpaEventStorageEngine` / `JdbcEventStorageEngine` / `EmbeddedEventStore`? Compile clean?
3. All yes AND no blocker fired → `result: skipped`.

## Decision tree — which AF5 engine

| AF4 wiring observed | AF5 target | Notes |
|---|---|---|
| `JpaEventStorageEngine.builder()…build()` (often inside `EmbeddedEventStore`) | `AggregateBasedJpaEventStorageEngine` | Backend = JPA. Schema change required out-of-band — user-owned. |
| `AxonServerEventStore` autoconfigured by Spring Boot starter | `AggregateBasedAxonServerEventStorageEngine` | Connector enhancer auto-registers DCB-flat `AxonServerEventStorageEngine` — to preserve aggregate-keyed log, register the aggregate-based variant explicitly. |
| `JdbcEventStorageEngine.builder()…build()` | *No drop-in in AF5* | **Blocker B2** — pick JPA / Axon Server / defer. |
| `MongoEventStorageEngine` (`axon-mongo` extension) | *No AF5 release* | **Blocker B1** — pick Axon Server / JPA / pause / accept-stays-af4. |
| Custom `EventStorageEngine` subclass | reimplement on `AggregateBased*` | **Blocker B3** — out of scope for one atomic invocation. |

Detection greps:
```bash
grep -RnE 'JpaEventStorageEngine|JdbcEventStorageEngine|MongoEventStorageEngine|EmbeddedEventStore|AxonServerEventStore' --include='*.java' --include='*.kt' src
grep -RnE 'org\.axonframework\.extensions\.mongo|axon-mongo' --include='*.java' --include='*.kt' --include='pom.xml' --include='*.gradle*' .
grep -RnE 'axon-server-connector|axoniq-spring-boot-starter|axon-spring-boot-starter' pom.xml */pom.xml
```

If `axoniq-spring-boot-starter` / `axon-server-connector` is present, **Axon Server backend** is almost always the right answer even if `JpaEventStorageEngine` bean co-exists.

After inspection, `AskUserQuestion` to confirm backend (default = inspection result, marked `(Recommended)`). The wiring path is NOT asked — it's pinned in `inputs.wiring`.

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

1. Locate target (Inputs.target or first AF4 storage-engine grep hit).
2. Inspect AF4 wiring; classify backend (JPA / Axon Server / blocker row).
3. Pick path:
   - **Wiring path** = `inputs.wiring` (NEVER ask).
   - **Backend** = inspection / blocker resolution.
   - Any blocker resolved with `pause` / `accept-stays-af4` / `defer-until-af5-jdbc` / `surface-and-defer` → `result: blocked`, `next: record-and-skip`, exit.
4. Run path sub-steps (below).
5. Surface custom-`Serializer` ports in `notes` (B4 soft blocker).
6. On JPA backend, flag "schema change required, user-owned, out-of-band" in `notes`. **No SQL artifact produced.**
7. Emit `## Output`.

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

**A.JPA.3 — Custom `Serializer` → `Converter`** — different SPI; flag for user; do NOT auto-port.

**A.JPA.4 — Schema change is out of band** — record one entry in Output `notes` (e.g. *"JPA backend selected — user must apply AF5 schema change for `aggregate_event_entry` before runtime verification."*). Do NOT write `.sql` files.

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

**A.AS.4** — custom `Serializer` → `Converter` flag for user.

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

During the same Phase #8 pass, migrate each class that:
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
2. JPA backend: schema-change requirement flagged in `notes` (no SQL produced).
3. Custom `Serializer` ports surfaced in `notes`.

Runtime verification belongs to stabilization (after user applies any schema change).

## Output

```yaml
result: success | skipped | rejected | needs-decision | blocked | failed
target: <FQ config class>
reason: <one short line>
decisions:
  path: A (Spring Boot) | B (framework Configurer)
  backend: jpa | axon-server
  bean-replaced: <bean / component name>
  schema-change-flagged: <true on JPA>
  serializer-ports-flagged: [<…>] | none                                              # B4
  mongo-event-store: none | move-to-axon-server | move-to-jpa | pause-migration | accept-stays-af4   # B1
  jdbc-event-store: none | move-to-jpa | move-to-axon-server | defer-until-af5-jdbc                  # B2
  custom-storage-engine-subclass: none | surface-and-defer | pause-migration                          # B3
caller-expects: { commit: <bool>, next: <…> }
notes: <e.g. "JdbcEventStorageEngine present, no AF5 path; user picked defer-until-af5-jdbc; original @Bean preserved as commented block with TODO[AF5 migration: B2]">
```

## Subagent guidelines

```yaml
subagent_type: general-purpose
isolation: worktree                    # bean swap can ripple through autoconfigure imports
parallelism: single
prompt-framing: |
  One-shot bean swap. NO test runs as part of the recipe — runtime verification happens
  during stabilization, after the user has applied any required schema changes out-of-band.
  Pick the right AF5 engine, replace the bean / Configurer registration, surface custom-Serializer
  ports in Output notes. SQL / DDL / data migration MUST NOT be produced.
```

## Verify

`axon4to5-isolatedtest` compile-only:
```
target-name: <BeanSimpleName>
main-sources: [<ConfigClass>.java]
test-sources: []
extra-deps: [axon-eventsourcing, axon-eventsourcing-jpa OR axon-server-connector per sub-path]
```

## Caveats

- **Never rely on JPA auto-config alone when `axon-server-connector` is on the classpath** — see A.JPA preamble.
- **Two `EventStorageEngine` beans = startup failure.** Delete leftover AF4 beans.
- **JDBC has no AF5 drop-in.** Ask user to pick JPA or Axon Server. Don't write a custom AF5 JDBC engine inside a migration run.
- **Mongo has no AF5 release.** Run the Mongo blocker prompt before any bean swap; never silently swap to JPA/Axon Server over Mongo data — the event log needs out-of-band migration.
- **Custom `Serializer` ≠ `Converter`.** Subclassed serializers / custom `RevisionResolver` / `ContentTypeConverter` are not one-line ports — surface to stabilization.
- **`AggregateEventEntry` comes from the framework JAR.** Don't copy it. Custom `DomainEventEntry` subclasses = custom storage-engine = B3 blocker.
- **Explicit `@Bean EventStorageEngine` kills `@RegisterDefaultEntities`** — see A.JPA.5. Always pair with project-wide `@EntityScan`.
