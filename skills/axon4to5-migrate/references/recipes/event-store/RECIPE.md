---
id: event-store
title: Event Store
description: Swaps AF4 EmbeddedEventStore / JpaEventStorageEngine / AxonServerEventStore wiring to AF5 AggregateBased* engine — explicit bean (Spring) or registerEventStorageEngine (native).
order: 8
argument-hint: $SOURCE
---

# Event Store

> One-shot bean swap. AF4 used `EmbeddedEventStore` + `JpaEventStorageEngine` / `JdbcEventStorageEngine` / `AxonServerEventStore`. AF5 collapses to a single `EventStorageEngine` registration of an `AggregateBased*` type. **This recipe is MANDATORY** — "the starter auto-configures it" is never a valid skip: the AF5 starter registers DCB-flat `AxonServerEventStorageEngine` (not aggregate-keyed) by default; without an explicit `AggregateBased*` bean the project starts cleanly then fails at first command/replay against legacy data.
>
> 🚨 **SQL / DDL / data migration is OUT OF SCOPE.** AF5 JPA tables differ from AF4 (`domain_event_entry` → `aggregate_event_entry`). Recipe swaps Java code only and flags the schema-change requirement in Notes.

## Source

- `$SOURCE` (required) — FQN, file path, or simple class name of the `@Configuration` class (Spring) or Configurer setup class (native) that declares the AF4 `EventStorageEngine` / `EmbeddedEventStore` bean. Pass the main application class if no dedicated config class exists.

## Scope

- `$SOURCE` configuration class.
- Spring Boot main application class if `@EntityScan` must be added there (JPA backend only).

Scope grows during Research; never shrinks. Sibling aggregates, projectors, sagas are NOT in scope.

## Blocker

All detected at Preflight before any edit. If any fire and no `inputs.decisions` key resolves them → emit Blocker and stop.

**B1 — `MongoEventStorageEngine` detected**

No AF5 release of `axon-mongo`. Detection: `grep -RnE 'MongoEventStorageEngine|org\.axonframework\.extensions\.mongo|axon-mongo'`.

Options (in addition to three defaults):
- `move-to-axon-server` — code rewrite only; user runs Mongo→AS data migration out-of-band BEFORE deploy.
- `move-to-jpa` — code rewrite only; user owns AF5 JPA schema change AND Mongo→relational data move.
- `pause-migration` — stop; replace Mongo with a supported store (incl. data) before resuming.

**B2 — `JdbcEventStorageEngine` detected**

No AF5 drop-in. Detection: `grep -RnE 'JdbcEventStorageEngine' src`.

Options (in addition to three defaults):
- `move-to-jpa` — code rewrite only; user owns AF5 schema change out-of-band.
- `move-to-axon-server` — code rewrite only; user owns JDBC→AS data migration out-of-band.
- `defer-until-af5-jdbc` — stop and wait for AF5 JDBC equivalent.

**B3 — Custom `EventStorageEngine` subclass**

Project subclasses `JpaEventStorageEngine` / `AbstractEventStorageEngine` / `BatchingEventStorageEngine` / `AxonServerEventStore`. Detection: `grep -RnE 'extends\s+(JpaEventStorageEngine|JdbcEventStorageEngine|AbstractEventStorageEngine|BatchingEventStorageEngine|AxonServerEventStore)\b' src`.

Options (in addition to three defaults):
- `surface-and-defer` *(Recommended)* — open follow-up; recipe exits without swap.

**B4 — Custom `Serializer` (soft)**

Any `@Bean Serializer` / `XStreamSerializer` subclass / custom `RevisionResolver` / custom `ContentTypeConverter`. AF5 uses `Converter` / `EventConverter` SPI — Jackson/XStream defaults port automatically; subclassed serializers do not. **Does NOT block the bean swap.** Record FQNs in Result Notes; recipe continues.

**Unmet project prerequisites**

- Project does not compile pre-recipe → Blocker `prerequisite-not-compiling`.

## Out of Scope

- SQL / DDL / data migration — user owns out-of-band on a non-prod copy first.
- Sibling aggregates, projectors, sagas, command/query buses.
- Cross-engine data migration (Mongo→JPA, JDBC→AS).
- Custom `DomainEventEntry` subclasses — treated as B3.
- Logging, formatting, package renames.

## Applicable

Surface check on `$SOURCE` + project build file. Cheap reads only.

Decision rule (top-down; first match wins):

1. **AF4 event store wiring detected** — any of `EmbeddedEventStore`, `JpaEventStorageEngine`, `JdbcEventStorageEngine`, `AxonServerEventStore`, `MongoEventStorageEngine` referenced in `$SOURCE` OR in `axon-spring-boot-starter` dependency without an explicit `EventStorageEngine` bean. → **continue**.
2. **Already migrated** — `$SOURCE` already declares an `AggregateBasedJpaEventStorageEngine` or `AggregateBasedAxonServerEventStorageEngine` bean / `registerEventStorageEngine` call with no AF4 remnants. → **continue** (idempotent Success-Criteria check decides).
3. **No event-store wiring found** — no AF4 engine references and no recognized AF5 engine in `$SOURCE`. → **Rejected**.

## Success Criteria

Extends DEFAULT.md baseline. Success criteria split by `configuration` input.

### Common — both configurations

1. **No AF4 engine references** as live (uncommented) code: none of `EmbeddedEventStore`, `JpaEventStorageEngine`, `JdbcEventStorageEngine`, `AxonServerEventStore` (type names or imports).
2. **Single `EventStorageEngine` registration** — exactly one bean / `registerEventStorageEngine` call; duplicate registrations cause startup failure.

### configuration=spring (Path A)

3. Explicit `@Bean EventStorageEngine` (or `@Bean EventStorageEngine`-typed method) present in `$SOURCE`, returning an `AggregateBasedJpaEventStorageEngine` OR `AggregateBasedAxonServerEventStorageEngine` instance.
4. **JPA backend only:** `@EntityScan(basePackages = {..., "org.axonframework", "io.axoniq.framework"})` present on the Spring Boot main class (or any `@Configuration`). Partial `@EntityScan` covering only the app package is a mismatch — it silently drops `AggregateEventEntry` / `TokenEntry` / `DeadLetterEntry`.

### configuration=native (Path B)

3. `configurer.registerEventStorageEngine(config -> new AggregateBased*EventStorageEngine(...))` OR `configurer.componentRegistry(reg -> reg.registerComponent(EventStorageEngine.class, ...))` present in `$SOURCE` with an `AggregateBased*` factory.

Aggregation rule: **all match (AND)** — DEFAULT.md baseline AND all applicable items above.

### Verification

`axon4to5-isolatedtest` with `test-sources: []` (compile-only). No isolated test exists for configuration classes; "no test coverage" → Learning. Runtime verification belongs to stabilization after the user applies any schema change.

## References

- [event-store.adoc](../../docs/paths/event-store.adoc) — *apply-condition:* always. Engine selection table (`AggregateBasedJpaEventStorageEngine` vs `AggregateBasedAxonServerEventStorageEngine`), schema changes (`domain_event_entry` → `aggregate_event_entry`).
- [serializers.adoc](../../docs/paths/serializers.adoc) — *apply-condition:* custom `Serializer` / `XStreamSerializer` detected (B4 soft blocker). `Serializer` → `Converter` / `EventConverter` SPI.
- [configuration.adoc](../../docs/paths/configuration.adoc) — *apply-condition:* `configuration=native`. `DefaultConfigurer` → `EventSourcingConfigurer`, `ConfigurerModule` → `ConfigurationEnhancer`, bootstrap-layer reads.

## Toolbox

### Step 1 — Preflight detection (always)

*Apply-condition:* always.

Run greps from `$SOURCE` project root before touching any file:

```bash
# AF4 engine references
grep -RnE 'JpaEventStorageEngine|JdbcEventStorageEngine|MongoEventStorageEngine|EmbeddedEventStore|AxonServerEventStore' --include='*.java' --include='*.kt' src

# Mongo extension
grep -RnE 'org\.axonframework\.extensions\.mongo|axon-mongo' --include='*.java' --include='*.kt' --include='pom.xml' --include='*.gradle*' .

# Connector / starter presence (implies Axon Server backend preference)
grep -RnE 'axon-server-connector|axoniq-spring-boot-starter|axon-spring-boot-starter' pom.xml */pom.xml
```

If `axoniq-spring-boot-starter` OR `axon-server-connector` present → **Axon Server backend is almost always correct** even when `JpaEventStorageEngine` bean co-exists.

### Step 2 — Backend decision

*Apply-condition:* always.

**AF4 auto-configuration truth** (from `JpaEventStoreAutoConfiguration` + `AxonServerBusAutoConfiguration` source):
- `AxonServerBusAutoConfiguration` is gated by `@ConditionalOnProperty("axon.axonserver.enabled", matchIfMissing=true)`. The `eventStore` bean inside also requires `@ConditionalOnProperty("axon.axonserver.event-store.enabled", matchIfMissing=true)`.
- `JpaEventStoreAutoConfiguration` is gated by `@ConditionalOnBean(EntityManagerFactory.class)` + `@ConditionalOnMissingBean({EventStore, EventBus, EventStorageEngine})`. It runs **after** `AxonServerBusAutoConfiguration`.

Run these greps in addition to Step 1:

```bash
# YAML flags that disabled Axon Server event store in AF4
grep -rn 'axon\.axonserver\.enabled\|axon\.axonserver\.event-store\.enabled' \
    src/main/resources/ application*.yml application*.yaml 2>/dev/null

# JPA on classpath check
grep -rn 'spring-boot-starter-data-jpa\|hibernate-core\|axon-eventsourcing-jpa' \
    pom.xml */pom.xml build.gradle* 2>/dev/null
```

Decision table (top-down; first match wins):

| Observation | Inferred backend |
|---|---|
| `axon.axonserver.enabled=false` OR `axon.axonserver.event-store.enabled=false` **AND** `EntityManagerFactory` on classpath (`spring-boot-starter-data-jpa` / `hibernate-core`) | **JPA** — AS disabled in AF4; JPA was the auto-configured fallback |
| `axon.axonserver.enabled=false` OR `axon.axonserver.event-store.enabled=false` **AND** NO JPA on classpath | Unclear — AS disabled but no JPA fallback; ask user |
| `JpaEventStorageEngine` explicit bean AND no `axon-server-connector` dependency | **JPA** |
| `axon-server-connector` / `axoniq-spring-boot-starter` in pom AND none of the above flags set to `false` | **Axon Server** |
| `JpaEventStorageEngine` AND `axon-server-connector` AND no YAML flag | Ask user — recommend Axon Server |
| `JdbcEventStorageEngine` | → B2 blocker |
| `MongoEventStorageEngine` | → B1 blocker |
| Custom subclass | → B3 blocker |

**Key**: `axon.axonserver.enabled=false` alone does not mean JPA — it means Axon Server was disabled. JPA was the fallback **only if** `EntityManagerFactory` was on the classpath. Always verify both the YAML flag AND the JPA dependency presence together.

Ask user to confirm backend if ambiguous (`AskUserQuestion`, default = inferred). Record choice.

### Step 3a — Path A: Spring Boot explicit `@Bean` (configuration=spring)

*Apply-condition:* `configuration=spring`.

> ⚠️ **Never rely on auto-config alone.** When `axon-server-connector` is on the classpath (always after Phase 1 OpenRewrite), `AxonServerConfigurationEnhancer` (ServiceLoader, `order=MIN_VALUE+10`) outraces `JpaEventStoreAutoConfiguration` (order≈`MAX_VALUE-600`) and registers DCB-flat `AxonServerEventStorageEngine`. `axon.axonserver.enabled=false` does NOT stop the ServiceLoader enhancer. An explicit Spring `@Bean EventStorageEngine` wins because `SpringComponentRegistry.hasComponent(ALL)` checks the Spring `BeanFactory` — both enhancers find the slot occupied and skip.

**Delete** any AF4 `@Bean EventStore` / `@Bean EventStorageEngine` / `@Bean EmbeddedEventStore` (two beans of `EventStorageEngine` = startup failure).

**JPA backend — add:**

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

Use `UnaryOperator.identity()` unless AF4 explicitly tuned `batchSize` / `gapTimeout` / `persistenceExceptionResolver`.

**Axon Server backend — add:**

```java
@Bean
public EventStorageEngine storageEngine(AxonServerConnectionManager connectionManager,
                                        EventConverter eventConverter) {
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

### Step 3b — Path B: framework Configurer (configuration=native)

*Apply-condition:* `configuration=native`.

**JPA backend:**

```java
EventSourcingConfigurer configurer = EventSourcingConfigurer.create();
configurer.registerEventStorageEngine(config ->
    new AggregateBasedJpaEventStorageEngine(
        new JpaTransactionalExecutorProvider(entityManagerFactory),
        config.getComponent(EventConverter.class),
        UnaryOperator.identity()
    )
);
```

Imports: `org.axonframework.eventsourcing.configuration.EventSourcingConfigurer`, `org.axonframework.eventsourcing.eventstore.jpa.AggregateBasedJpaEventStorageEngine`, `org.axonframework.messaging.core.unitofwork.transaction.jpa.JpaTransactionalExecutorProvider`, `org.axonframework.messaging.eventhandling.conversion.EventConverter`.

**Axon Server backend:**

```java
configurer.registerEventStorageEngine(config -> {
    AxonServerConnectionManager manager = config.getComponent(AxonServerConnectionManager.class);
    return new AggregateBasedAxonServerEventStorageEngine(
            manager.getConnection(),
            config.getComponent(EventConverter.class)
    );
});
```

Imports: `io.axoniq.framework.axonserver.connector.api.AxonServerConnectionManager`, `io.axoniq.framework.axonserver.connector.event.AggregateBasedAxonServerEventStorageEngine`, `org.axonframework.eventsourcing.configuration.EventSourcingConfigurer`, `org.axonframework.messaging.eventhandling.conversion.EventConverter`.

### Step 4 — `@EntityScan` (JPA backend + configuration=spring only)

*Apply-condition:* `configuration=spring` AND JPA backend.

> 🚨 Explicit `@Bean EventStorageEngine` trips `@ConditionalOnMissingBean(EventStorageEngine.class)` on `JpaEventStoreAutoConfiguration` BEFORE Spring processes `@Import(DefaultEntityRegistrar.class)`. Framework JPA entities never reach `AutoConfigurationPackages`. Symptom: `Could not resolve root entity 'AggregateEventEntry'`.

Add to the Spring Boot main class (or any `@Configuration`):

```java
@SpringBootApplication
@EntityScan(basePackages = {
    "com.<app>",               // project's own @Entity classes
    "org.axonframework",       // AggregateEventEntry + TokenEntry
    "io.axoniq.framework"      // DeadLetterEntry (commercial AF5 — drop on free-af5 line)
})
public class <App>Application { ... }
```

Import: `org.springframework.boot.autoconfigure.domain.EntityScan`.

**Partial `@EntityScan` covering only the app package is WORSE than none** — it displaces `AutoConfigurationPackages` entirely, breaking `TokenEntry` and `DeadLetterEntry` registrations from other autoconfigs.

If project uses explicit `LocalContainerEntityManagerFactoryBean` with `packagesToScan`, add the same three roots there instead.

### Step 5 — Schema change flag (JPA backend)

*Apply-condition:* JPA backend (any `configuration`).

Record in Result Notes: *"JPA backend selected — user must apply AF5 schema change (`domain_event_entry` → `aggregate_event_entry`) out-of-band before runtime verification. See `event-store.adoc`."* Do NOT write SQL files.

## Use cases

- [01-spring-boot-jpa.md](use-cases/01-spring-boot-jpa.md) — *apply-condition:* `configuration=spring` AND JPA backend. Shows explicit `@Bean` + `@EntityScan` + deleted `EmbeddedEventStore`.
- [02-spring-boot-axon-server.md](use-cases/02-spring-boot-axon-server.md) — *apply-condition:* `configuration=spring` AND Axon Server backend. Shows explicit `@Bean AggregateBasedAxonServerEventStorageEngine`.
- [03-native-axon-server.md](use-cases/03-native-axon-server.md) — *apply-condition:* `configuration=native` AND Axon Server backend. Shows `registerEventStorageEngine` on `EventSourcingConfigurer`.
- [04-native-jpa.md](use-cases/04-native-jpa.md) — *apply-condition:* `configuration=native` AND JPA backend. Shows `registerEventStorageEngine` + schema flag.

## Gotchas

- **`axon.axonserver.enabled=false` alone ≠ JPA backend.** In AF4, this flag gated `AxonServerBusAutoConfiguration` — but `JpaEventStoreAutoConfiguration` only kicked in when `EntityManagerFactory` was **also** on the classpath (`@ConditionalOnBean(EntityManagerFactory.class)`). Without JPA on the classpath, disabling AS left no EventStorageEngine auto-configured. Always check BOTH the YAML flag AND the presence of `spring-boot-starter-data-jpa` / `hibernate-core` to infer JPA backend. In AF5, `axon.axonserver.enabled=false` only gates `@Bean` methods in `AxonServerAutoConfiguration` — the ServiceLoader-discovered `AxonServerConfigurationEnhancer` is NOT gated by it. An explicit `@Bean EventStorageEngine` is the only reliable way to enforce JPA on the AF5 path.
- **Auto-config never reliably wins on Spring when `axon-server-connector` is on the classpath.** Phase 1 OpenRewrite swaps `axon-spring-boot-starter` → `axoniq-spring-boot-starter`, which brings the connector. The connector's `AxonServerConfigurationEnhancer` (`order=MIN_VALUE+10`) runs `registerIfNotPresent` before `JpaEventStoreAutoConfiguration`'s enhancer (`order≈MAX_VALUE-600`) — DCB-flat `AxonServerEventStorageEngine` wins. `axon.axonserver.enabled=false` only gates `@Bean` methods in `AxonServerAutoConfiguration`, NOT the ServiceLoader enhancer. Always declare explicit `@Bean EventStorageEngine` on Path A.JPA.
- **Two `EventStorageEngine` beans = startup failure.** Delete ALL AF4 `@Bean EventStore` / `@Bean EventStorageEngine` / `@Bean EmbeddedEventStore` before adding the AF5 bean.
- **`AggregateEventEntry` comes from the framework JAR — never copy it.** Custom `DomainEventEntry` subclasses = B3 custom subclass blocker.
- **Partial `@EntityScan` is worse than none.** Adding `@EntityScan` for only the app package displaces `AutoConfigurationPackages` entirely — all framework JPA entities stop being registered. Always include `org.axonframework` and `io.axoniq.framework` in the same annotation.
- **`AggregateBasedAxonServerEventStorageEngine` is NOT auto-registered.** Even with `axoniq-spring-boot-starter`, the connector only auto-registers the DCB-flat `AxonServerEventStorageEngine`. The aggregate-based variant requires an explicit `@Bean` (Spring) or `registerEventStorageEngine` call (native).
- **`AxonServerEventStorageEngine` (DCB) vs `AggregateBasedAxonServerEventStorageEngine`**: DCB migration (flat event log, no aggregate routing) is a separate larger initiative. This recipe always targets the aggregate-based engine to preserve legacy semantics.
- **Custom `Serializer` ≠ `Converter`**: subclassed serializers / custom `RevisionResolver` / custom `ContentTypeConverter` are not one-line ports. Surface as B4 (soft) and flag in Notes.
- **JPA schema change is out-of-band and blocking for runtime.** The AF5 app will start cleanly with the new bean but fail at first command/replay until the schema change is applied. Always flag in Notes.

## Result

Inherits DEFAULT.md baseline.

### Success

Say **"return SUCCESS"**, then emit result block. `Recipe:` field is `axon4to5-event-store`. NOTES must include: (a) which path was taken (A.JPA / A.AS / B.JPA / B.AS); (b) if JPA: schema-change note for `aggregate_event_entry` (user-owned, out-of-band); (c) if custom Serializer flagged: list the FQNs; (d) no test coverage (Learning).

### Blocker

Say **"return BLOCKER"**, then emit result block. `Recipe:` field is `axon4to5-event-store`. NOTES name each detected blocker + location. Options block: three DEFAULT.md baselines + all recipe-specific options listed in the `## Blocker` section that apply.

Example (B1 — Mongo):

```
return BLOCKER

> **Result:** 🚧 Blocker
> **Source:** `com.example.AxonConfig`
> **Recipe:** axon4to5-event-store
>
> **Notes:** 1 blocker detected. B1 (MongoEventStorageEngine) at `AxonConfig.java:14` — `MongoEventStorageEngine.builder()…build()`. No AF5 release of `axon-mongo`. Code rewrite only — data migration from Mongo to target store is the caller's responsibility out-of-band.
>
> **Options:**
>
> _For B1 (MongoEventStorageEngine):_
> - [ ] **move-to-axon-server** — rewrite to Axon Server backend; caller runs Mongo→AS data migration out-of-band before deploy.
> - [ ] **move-to-jpa** — rewrite to JPA backend; caller owns AF5 JPA schema change AND Mongo→relational data move.
> - [ ] **pause-migration** — stop; replace Mongo with a supported store (incl. data) before resuming.
> - [ ] **skip** — keep `AxonConfig` as-is; queue moves on.
> - [ ] **revert** — undo all edits; restore pre-recipe state.
> - [ ] **solve-manually** — pause; caller handles migration, then re-invokes.
```

### Rejected

Say **"return REJECTED"**, then emit result block. `Recipe:` field is `axon4to5-event-store`. NOTES name the failed `# Applicable` predicate (3 — no event store wiring found).

### Failure

Say **"return FAILURE"**, then emit result block. NOTES: failing Success Criteria + last error verbatim. LEARNINGS nearly always present.
