# Use case 01 — Spring Boot + JPA backend

**Why interesting:** Most common migration shape — covers two AF4 patterns: (a) explicit `EmbeddedEventStore` + `JpaEventStorageEngine` bean in a `@Configuration` class, and (b) no explicit engine bean + `axon.axonserver.enabled=false` (or `axon.axonserver.event-store.enabled=false`) in `application.yml` WITH JPA on the classpath (`spring-boot-starter-data-jpa` / `EntityManagerFactory`). In AF4, `JpaEventStoreAutoConfiguration` had `@ConditionalOnBean(EntityManagerFactory.class)` — it only fired when JPA was actually on the classpath; the YAML flag was just the trigger that stopped Axon Server from winning the race. AF5 requires an explicit `@Bean AggregateBasedJpaEventStorageEngine` AND `@EntityScan` covering framework packages — without both, the app either starts cleanly then fails at first command/replay, or fails on startup with `Could not resolve root entity 'AggregateEventEntry'`.

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
