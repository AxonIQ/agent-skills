# Use case 04 — Framework Configurer + JPA backend (native)

**Why interesting:** Native projects with JPA event store use `EventSourcingConfigurer.registerEventStorageEngine(...)`. No `@EntityScan` needed (no Spring Boot auto-config involved), but the schema change is still out-of-band and must be flagged. Also no `axon-server-connector` race condition since the class is not loaded by Spring Boot.

## Before (AF4)

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

## After (AF5)

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

## What changed

- `DefaultConfigurer.defaultConfiguration()` → `EventSourcingConfigurer.create()`.
- `EmbeddedEventStore.builder()…build()` **deleted** — not needed in AF5.
- `JpaEventStorageEngine.builder()…build()` → `new AggregateBasedJpaEventStorageEngine(JpaTransactionalExecutorProvider, EventConverter, configurer)`.
- `EntityManagerProvider` + `TransactionManager` → `EntityManagerFactory` + `JpaTransactionalExecutorProvider`.
- `Serializer` arg removed — `EventConverter` resolved from configuration registry.
- `buildConfiguration()` → `build()`. Return type `AxonConfiguration`.

## Caveats

- **Schema change is out-of-band** — `domain_event_entry` → `aggregate_event_entry` table rename + column renames. Flag in Result Notes; do NOT write SQL files.
- **`UnaryOperator.identity()`** keeps defaults. Use a custom lambda only if AF4 tuned `batchSize` / `gapTimeout` / `persistenceExceptionResolver`.
- No `@EntityScan` — not Spring Boot; JPA entity registration is configured by the JPA provider setup outside Axon.
