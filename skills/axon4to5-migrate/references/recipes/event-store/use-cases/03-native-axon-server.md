# Use case 03 — Framework Configurer + Axon Server backend (native)

**Why interesting:** Native (non-Spring) projects wire the event store via `EventSourcingConfigurer.registerEventStorageEngine(...)`. The connector's `AxonServerConfigurationEnhancer` is still ServiceLoader-discovered and still registers DCB-flat `AxonServerEventStorageEngine` when present — but an explicit `registerEventStorageEngine(...)` call overrides it because it runs before the enhancer processes the registry.

## Before (AF4)

```java
public class AxonConfig {

    public Configuration buildConfiguration() {
        Configurer configurer = DefaultConfigurer.defaultConfiguration();
        // AF4: AxonServerEventStore auto-configured by axon-server-connector starter
        // or explicitly:
        // configurer.configureEventStore(c -> AxonServerEventStore.builder()
        //         .configuration(c.getComponent(AxonServerConfiguration.class))
        //         .axonServerConnectionManager(c.getComponent(AxonServerConnectionManager.class))
        //         .build());
        return configurer.buildConfiguration();
    }
}
```

## After (AF5)

```java
import io.axoniq.framework.axonserver.connector.api.AxonServerConnectionManager;
import io.axoniq.framework.axonserver.connector.event.AggregateBasedAxonServerEventStorageEngine;
import org.axonframework.eventsourcing.configuration.EventSourcingConfigurer;
import org.axonframework.messaging.eventhandling.conversion.EventConverter;

public class AxonConfig {

    public AxonConfiguration buildConfiguration() {
        EventSourcingConfigurer configurer = EventSourcingConfigurer.create();

        configurer.registerEventStorageEngine(config -> {
            AxonServerConnectionManager manager =
                    config.getComponent(AxonServerConnectionManager.class);
            return new AggregateBasedAxonServerEventStorageEngine(
                    manager.getConnection(),
                    config.getComponent(EventConverter.class)
            );
        });

        return configurer.build();
    }
}
```

## What changed

- `DefaultConfigurer.defaultConfiguration()` → `EventSourcingConfigurer.create()`.
- `buildConfiguration()` → `build()`. Return type `AxonConfiguration`.
- AF4 `configureEventStore(...)` → AF5 `registerEventStorageEngine(...)`.
- Factory lambda receives AF5 read-only `Configuration` — use `config.getComponent(...)` to resolve deps.
- No `@EntityScan` — no JPA; Axon Server stores its own events.

## Caveats

- `config.getComponent(AxonServerConnectionManager.class)` works only if the connector enhancer has registered the connection manager. If the project manually registers `AxonServerConnectionManager`, pass it as a constructor arg to the setup method instead.
- For non-default Axon Server context: `manager.getConnection("my-context")`.
