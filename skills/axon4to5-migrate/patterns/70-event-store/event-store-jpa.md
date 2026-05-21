# Event Store Configuration — JPA

AF5 requires an explicit `EventStorageEngine` bean when using JPA (the in-process store). It is NOT
auto-configured by `axoniq-spring-boot-starter` when Axon Server is disabled.

## Import Mappings

| AF4 | AF5 |
|-----|-----|
| *(auto-configured; no explicit bean)* | `org.axonframework.eventsourcing.eventstore.jpa.AggregateBasedJpaEventStorageEngine` |
| — | `org.axonframework.messaging.core.unitofwork.transaction.jpa.JpaTransactionalExecutorProvider` |
| — | `org.axonframework.messaging.eventhandling.conversion.EventConverter` |

## Detection

```bash
grep -rn 'EventStorageEngine\|EmbeddedEventStore\|JpaEventStorageEngine' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

## Axon Framework 4 Code (implicit auto-config)

```java
// No explicit configuration needed in AF4 with Spring Boot
// axon-spring-boot-starter auto-configured the JPA event store
```

## Axon Framework 5 Code

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

## application.yaml — disable Axon Server

```yaml
axon:
  axonserver:
    enabled: false
```

## @EntityScan requirement

AF5's JPA event store uses its own JPA entities. Add both `org.axonframework` and `io.axoniq.framework` to
the `@EntityScan` packages alongside your application's own packages, or the event store tables will not be created.

## Notes

- This configuration is needed **only** when using the embedded JPA store (no Axon Server).
- When Axon Server is enabled (`axon.axonserver.enabled: true`), no explicit `EventStorageEngine` bean is needed.
- `AggregateBasedJpaEventStorageEngine` is the AF5 equivalent of AF4's `JpaEventStorageEngine`.
- `UnaryOperator.identity()` is the no-op event transformer (events stored as-is).
