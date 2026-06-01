# Use case 01 — Spring Boot + JPA backend

**Why interesting:** Most common migration shape — covers two AF4 patterns: (a) explicit `EmbeddedEventStore` + `JpaEventStorageEngine` bean in a `@Configuration` class, and (b) no explicit engine bean + `axon.axonserver.enabled=false` (or `axon.axonserver.event-store.enabled=false`) in `application.yml` WITH JPA on the classpath (`spring-boot-starter-data-jpa` / `EntityManagerFactory`). In AF4, `JpaEventStoreAutoConfiguration` had `@ConditionalOnBean(EntityManagerFactory.class)` — it only fired when JPA was actually on the classpath; the YAML flag was just the trigger that stopped Axon Server from winning the race.

The AF5 shape has **three cases** — the `@Bean` override keys on whether the connector *enhancer is active*; `@EntityScan` keys on whether the connector is *present at all*:

- **Connector present, `axon.axonserver.enabled` ≠ `false`** (the usual post-Phase-1 case — `axoniq-spring-boot-starter` pulls the connector transitively): the connector enhancer wins and registers DCB-flat `AxonServerEventStorageEngine`. You MUST add an explicit `@Bean AggregateBasedJpaEventStorageEngine` AND `@EntityScan` — without both, the app either starts cleanly then fails at first command/replay, or fails on startup with `Could not resolve root entity 'AggregateEventEntry'`. This is the "After (AF5)" shown below.
- **Connector present, `axon.axonserver.enabled=false`** (AS disabled, want JPA): `disableAxonServerConfigurationEnhancer` takes the connector enhancer out of the race, so `JpaEventStoreAutoConfiguration` auto-registers `AggregateBasedJpaEventStorageEngine` — **no `@Bean` needed**. But the connector is still on the classpath, so `@EntityScan` IS needed. See the **Variant — connector present but disabled** below.
- **Connector absent** (JPA-only deployment — connector `<exclusion>`'d or never depended on): `JpaEventStoreAutoConfiguration` registers `AggregateBasedJpaEventStorageEngine` + its framework entities itself. Just delete the AF4 beans; **add NOTHING**. See the **Variant — connector absent** below.

## Before (AF4)

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

## After (AF5)

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

## What changed

- `EmbeddedEventStore` bean **deleted** — AF5 wires the event store from the engine alone; no `EmbeddedEventStore` wrapper.
- `JpaEventStorageEngine.builder()…build()` → `new AggregateBasedJpaEventStorageEngine(JpaTransactionalExecutorProvider, EventConverter, configurer)`.
- `Serializer` arg **removed** — AF5 engines take `EventConverter` (resolved from configuration registry), not a `Serializer` constructor arg.
- `EntityManagerProvider` + `TransactionManager` → `EntityManagerFactory` + `JpaTransactionalExecutorProvider`.
- `@EntityScan` added to main class covering three package roots — required because the explicit `@Bean EventStorageEngine` trips `@ConditionalOnMissingBean` on `JpaEventStoreAutoConfiguration` before its `@Import(DefaultEntityRegistrar.class)` fires.

## Caveats

- **`UnaryOperator.identity()`** keeps `AggregateBasedJpaEventStorageEngineConfiguration` defaults. Only use a custom configurer lambda if AF4 explicitly tuned `batchSize` / `gapTimeout` / `persistenceExceptionResolver`.
- **Schema change is out-of-band.** `domain_event_entry` → `aggregate_event_entry` table rename + column renames. Record in Result Notes; do NOT write SQL.
- **`io.axoniq.framework` in `@EntityScan`** — drop this entry on the free AF5 line (no commercial `DeadLetterEntry`). Include on the AxonIQ commercial line.

## Variant — connector absent (JPA-only deployment)

When the project does NOT have `axon-server-connector` on the classpath — e.g. it excludes it from `axoniq-spring-boot-starter`:

```xml
<dependency>
    <groupId>io.axoniq</groupId>
    <artifactId>axoniq-spring-boot-starter</artifactId>
    <exclusions>
        <exclusion>
            <groupId>io.axoniq.framework</groupId>
            <artifactId>axon-server-connector</artifactId>
        </exclusion>
    </exclusions>
</dependency>
```

— or depends only on `axon-eventsourcing` / `axon-messaging` / `axoniq-framework-spring` without the connector.

Then `JpaEventStoreAutoConfiguration` (gated `@ConditionalOnBean({EntityManagerFactory, PlatformTransactionManager})` + `@ConditionalOnMissingBean({EventStore, EventStorageEngine})`) auto-registers `AggregateBasedJpaEventStorageEngine` via a `ConfigurationEnhancer`, and registers the framework JPA entities via `@RegisterDefaultEntities(packages = {"org.axonframework.eventsourcing.eventstore.jpa"})`.

### After (AF5) — connector absent

```java
// EventStoreConfiguration: the whole class is DELETED if it held only the
// EmbeddedEventStore + JpaEventStorageEngine beans. No replacement bean.
```

```java
@SpringBootApplication           // NO @EntityScan
public class MyApplication {
    public static void main(String[] args) {
        SpringApplication.run(MyApplication.class, args);
    }
}
```

**Do NOT add a `@Bean EventStorageEngine` and do NOT add `@EntityScan`.** Adding the bean trips `@ConditionalOnMissingBean` and suppresses the auto-config (including its `@RegisterDefaultEntities`); adding `@EntityScan` displaces `AutoConfigurationPackages` and breaks `TokenEntry` / `DeadLetterEntry` registration. The schema-change flag (`domain_event_entry` → `aggregate_event_entry`) still applies — record it in Result Notes.

## Variant — connector present but disabled (`axon.axonserver.enabled=false`)

The connector stays on the classpath (full `axoniq-spring-boot-starter`, no exclusion), but Axon Server is switched off and the app uses the JPA event store:

```properties
axon.axonserver.enabled=false
```

`AxonServerAutoConfiguration`'s `disableAxonServerConfigurationEnhancer` bean disables the connector enhancer, so `JpaEventStoreAutoConfiguration` auto-registers `AggregateBasedJpaEventStorageEngine` — **no `@Bean` override needed.** But because `axon-server-connector` is still on the classpath, the framework JPA entities are not scanned cleanly — **`@EntityScan` IS required.**

### After (AF5) — connector present but disabled

```java
// EventStoreConfiguration: deleted if it held only the AF4 EmbeddedEventStore +
// JpaEventStorageEngine beans. No replacement @Bean — JPA auto-config registers it.
```

```java
import org.springframework.boot.autoconfigure.domain.EntityScan;

@SpringBootApplication
@EntityScan(basePackages = {       // REQUIRED — connector on classpath
    "com.example",
    "org.axonframework",
    "io.axoniq.framework"          // drop on the free AF5 line
})
public class MyApplication {
    public static void main(String[] args) {
        SpringApplication.run(MyApplication.class, args);
    }
}
```

So: **no `@Bean`, but YES `@EntityScan`.** Schema-change flag still applies.
