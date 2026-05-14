# Use case 02 — Spring Boot + Axon Server backend

**Why interesting:** `axoniq-spring-boot-starter` includes `axon-server-connector`, whose `AxonServerConfigurationEnhancer` (ServiceLoader, `order=MIN_VALUE+10`) auto-registers `AxonServerEventStorageEngine` (DCB-flat) — NOT the aggregate-based variant. To preserve AF4's aggregate-keyed event log semantics, an explicit `@Bean AggregateBasedAxonServerEventStorageEngine` must be declared. The Spring `@Bean` is visible to `SpringComponentRegistry.hasComponent(ALL)` — both enhancers find the slot occupied and skip.

## Before (AF4)

```java
// AF4: no explicit @Bean needed — axon-spring-boot-starter auto-wires AxonServerEventStore
// This is the "no config" case or minimal config:
@SpringBootApplication
public class MyApplication {
    public static void main(String[] args) {
        SpringApplication.run(MyApplication.class, args);
    }
}
```

Or explicitly:

```java
@Configuration
public class AxonConfig {

    @Bean
    public AxonServerEventStore eventStore(AxonServerConfiguration serverConfig,
                                           AxonServerConnectionManager connectionManager) {
        return AxonServerEventStore.builder()
                .configuration(serverConfig)
                .axonServerConnectionManager(connectionManager)
                .build();
    }
}
```

## After (AF5)

```java
import io.axoniq.framework.axonserver.connector.api.AxonServerConnectionManager;
import io.axoniq.framework.axonserver.connector.event.AggregateBasedAxonServerEventStorageEngine;
import org.axonframework.eventsourcing.eventstore.EventStorageEngine;
import org.axonframework.messaging.eventhandling.conversion.EventConverter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class AxonConfig {

    @Bean
    public EventStorageEngine storageEngine(AxonServerConnectionManager connectionManager,
                                            EventConverter eventConverter) {
        return new AggregateBasedAxonServerEventStorageEngine(
                connectionManager.getConnection(),
                eventConverter
        );
    }
}
```

For a non-default Axon Server context:
```java
return new AggregateBasedAxonServerEventStorageEngine(
        connectionManager.getConnection("my-context"),
        eventConverter
);
```

## What changed

- Any AF4 `@Bean AxonServerEventStore` **deleted** (two beans of `EventStorageEngine` = startup failure).
- Explicit `@Bean EventStorageEngine` returning `AggregateBasedAxonServerEventStorageEngine` **added** — overrides connector's auto-registration of DCB-flat `AxonServerEventStorageEngine`.
- `AxonServerConfiguration` arg removed — AF5 engine takes `AxonServerConnectionManager.getConnection()` directly.
- No `@EntityScan` needed — Axon Server stores its own events; no JPA entities involved.
- No schema change — Axon Server event storage is server-side.

## Caveats

- **`AggregateBasedAxonServerEventStorageEngine` is opt-in.** The connector JAR ships it but does not auto-register it. Explicit `@Bean` or `registerEventStorageEngine` is the only registration path.
- **DCB migration is out of scope.** If the project wants to migrate to the DCB-native `AxonServerEventStorageEngine` (requires Axon Server 2025.2.0+), that is a separate, larger initiative — not handled by this recipe.
- **Custom `Serializer` / `EventConverter`** — if AF4 explicitly wired a custom `Serializer` to the event store, AF5 uses `EventConverter` (different SPI). Flag in Result Notes; the recipe does not auto-port custom serializers.
