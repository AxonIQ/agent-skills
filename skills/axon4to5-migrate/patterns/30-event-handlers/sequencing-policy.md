# Sequencing Policy Migration

AF4 wired sequencing policies externally — via YAML `axon.eventhandling.processors.<group>.sequencing-policy`,
a `@Bean SequencingPolicy<EventMessage<?>>`, or programmatic `EventProcessingConfigurer.assignSequencingPolicy(…)`.
AF5 moves policy declaration to a class-level `@SequencingPolicy` annotation on the event-handling class.

## Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.eventhandling.async.SequencingPolicy` (interface) | `org.axonframework.messaging.core.sequencing.SequencingPolicy` |
| YAML: `sequencing-policy: beanName` | `@SequencingPolicy` annotation on handler class |
| — | `org.axonframework.messaging.core.annotation.SequencingPolicy` (annotation) |
| — | `org.axonframework.messaging.core.sequencing.MetadataSequencingPolicy` |

## Detection

```bash
grep -rn 'SequencingPolicy\|sequencing-policy' \
  --include='*.java' --include='*.kt' --include='*.scala' --include='*.yaml' --include='*.properties' .
```

## Part 1 — Remove YAML wiring, add @SequencingPolicy annotation

### Axon Framework 4

```yaml
# application.yaml
axon:
  eventhandling:
    processors:
      orders:
        mode: pooled
        sequencing-policy: gameIdSequencingPolicy   # <-- references @Bean name
```

```java
// Configuration class
@Bean
public SequencingPolicy<EventMessage<?>> gameIdSequencingPolicy() {
    return e -> e.getMetaData().get("gameId");
}
```

### Axon Framework 5

```yaml
# application.yaml — remove sequencing-policy key; mode stays
axon:
  eventhandling:
    processors:
      orders:
        mode: pooled
```

```java
import org.axonframework.messaging.core.annotation.Namespace;
import org.axonframework.messaging.core.annotation.SequencingPolicy;
import org.axonframework.messaging.core.sequencing.MetadataSequencingPolicy;

@Namespace("orders")
@SequencingPolicy(type = MetadataSequencingPolicy.class, parameters = "gameId")
public class OrderProjector { … }
```

## Part 2 — Custom SequencingPolicy interface rewrite

### Axon Framework 4

```java
import org.axonframework.eventhandling.async.SequencingPolicy;

public class MyPolicy implements SequencingPolicy<EventMessage<?>> {
    @Override
    public Object getSequenceIdentifierFor(EventMessage<?> event) {
        return event.getPayload().getClass().getSimpleName();
    }
}
```

### Axon Framework 5

```java
import org.axonframework.messaging.core.sequencing.SequencingPolicy;
import org.axonframework.messaging.eventhandling.EventMessage;
import org.axonframework.messaging.core.ProcessingContext;
import java.util.Optional;

public class MyPolicy implements SequencingPolicy {
    @Override
    public Optional<Object> sequenceIdentifierFor(EventMessage<?> message, ProcessingContext context) {
        return Optional.ofNullable(message.payload().getClass().getSimpleName());
    }
}
```

## Method signature changes

| | AF4 | AF5 |
|---|---|---|
| Method name | `getSequenceIdentifierFor` | `sequenceIdentifierFor` |
| Parameters | `EventMessage<?> event` | `EventMessage<?> message, ProcessingContext context` |
| Return | `Object` (null = no sequence) | `Optional<Object>` (empty = no sequence) |
| Interface generic | `SequencingPolicy<EventMessage<?>>` | `SequencingPolicy` (no generic) |

## Built-in policy classes

| Policy | Usage |
|--------|-------|
| `MetadataSequencingPolicy` | `@SequencingPolicy(type = MetadataSequencingPolicy.class, parameters = "metadataKey")` |
| `SequentialPerAggregatePolicy` | `@SequencingPolicy(type = SequentialPerAggregatePolicy.class)` |
| `SequentialPolicy` | `@SequencingPolicy(type = SequentialPolicy.class)` |
| `FullConcurrencyPolicy` | `@SequencingPolicy(type = FullConcurrencyPolicy.class)` |

## Notes

- **`@SequencingPolicy` annotation package is `core.annotation`** — `org.axonframework.messaging.core.annotation.SequencingPolicy`.
  Not `core.sequencing.annotation.SequencingPolicy` (doesn't exist).
- **`parameters` is a `String`** representing the metadata key for `MetadataSequencingPolicy`.
- **`@Bean SequencingPolicy` definition** — leave the bean in the configuration class (other processors may use it);
  only remove the YAML reference.
