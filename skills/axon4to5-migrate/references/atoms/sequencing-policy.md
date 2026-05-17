---
atom-id: sequencing-policy
title: "SequencingPolicy — YAML/@Bean wiring → @SequencingPolicy annotation + interface rewrite"
af4-symbols: ["org.axonframework.eventhandling.async.SequencingPolicy", "registerSequencingPolicy", "assignSequencingPolicy"]
af5-symbols: ["@SequencingPolicy", "org.axonframework.messaging.core.annotation.SequencingPolicy", "org.axonframework.messaging.core.sequencing.SequencingPolicy", "sequenceIdentifierFor"]
detect: grep -rn 'SequencingPolicy\|sequencing-policy' --include='*.java' --include='*.kt' --include='*.scala' --include='*.yaml' --include='*.properties' .
used-by: [event-processor]
---

# SequencingPolicy Migration

AF4 wired sequencing policies externally — via YAML `axon.eventhandling.processors.<group>.sequencing-policy`,
`@Bean SequencingPolicy`, or programmatic `EventProcessingConfigurer.assignSequencingPolicy(…)`. AF5 moves policy
declaration to a class-level `@SequencingPolicy` annotation on the event-handling class.

The AF4 `SequencingPolicy<EventMessage<?>>` interface is also renamed and its method signature changed.

## Part 1 — @SequencingPolicy class annotation

### Detect

```bash
grep -rn 'sequencing-policy\|assignSequencingPolicy\|registerSequencingPolicy' \
  --include='*.java' --include='*.kt' --include='*.scala' --include='*.yaml' --include='*.properties' .
```

### Add annotation to the event-handling class

```java
// AF5
import org.axonframework.messaging.core.annotation.SequencingPolicy;
import org.axonframework.messaging.core.sequencing.MetadataSequencingPolicy;

@Namespace("orders")
@SequencingPolicy(type = MetadataSequencingPolicy.class, parameters = "gameId")
public class OrderProjector { … }
```

Import: `org.axonframework.messaging.core.annotation.SequencingPolicy`

⚠️ Package is `core.annotation`, NOT `core.sequencing.annotation`. Wrong path causes a compile error.

### Built-in policy classes (no body migration needed)

| AF4 | AF5 | Notes |
|---|---|---|
| `MetadataSequencingPolicy` | `MetadataSequencingPolicy.class` + `parameters = "<metadataKey>"` | Sequences by a metadata key |
| `SequentialPerAggregatePolicy` | `SequentialPerAggregatePolicy.class` | AF4 default |
| `SequentialPolicy` | `SequentialPolicy.class` | Fully sequential |
| `FullConcurrencyPolicy` | `FullConcurrencyPolicy.class` | No sequencing |

### Remove YAML key

After adding the annotation, delete the corresponding YAML key from `application.yaml`:

```yaml
# Remove this:
axon:
  eventhandling:
    processors:
      orders:
        sequencing-policy: com.example.OrderSequencingPolicy
```

### `@Bean SequencingPolicy` — leave the bean in place

The `@Bean SequencingPolicy` definition itself is **not deleted** by this recipe — other processors may share it.
Leave it; flag in Result NOTES if it becomes an orphan after all consumers are migrated.

## Part 2 — Custom SequencingPolicy interface rewrite

### Detect

```bash
grep -rln 'implements.*SequencingPolicy' --include='*.java' --include='*.kt' --include='*.scala' .
```

### Interface and method changes

**Remove:**
```java
import org.axonframework.eventhandling.async.SequencingPolicy;

public class MyPolicy implements SequencingPolicy<EventMessage<?>> {

    @Override
    public Object getSequenceIdentifierFor(EventMessage<?> event) {
        return event.getPayload().getClass().getSimpleName();
    }
}
```

**Replace with:**
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

### Change summary

| | AF4 | AF5 |
|---|---|---|
| Interface | `SequencingPolicy<EventMessage<?>>` | `SequencingPolicy` (no generic) |
| Import | `org.axonframework.eventhandling.async.SequencingPolicy` | `org.axonframework.messaging.core.sequencing.SequencingPolicy` |
| Method name | `getSequenceIdentifierFor` | `sequenceIdentifierFor` |
| Method signature | `Object getSequenceIdentifierFor(EventMessage<?> event)` | `Optional<Object> sequenceIdentifierFor(EventMessage<?> message, ProcessingContext context)` |
| Return value | `return value;` / `return null;` | `return Optional.ofNullable(value);` / `return Optional.empty();` |
| Payload access | `event.getPayload()` | `message.payload()` (see [[message-accessors]]) |
| Metadata access | `event.getMetaData()` | `message.metaData()` |

## Gotchas

- **`@SequencingPolicy` package is `core.annotation`** — `org.axonframework.messaging.core.annotation.SequencingPolicy`.
  Not `core.sequencing.annotation.SequencingPolicy` (that path doesn't exist).
- **`parameters` is a `String`** — if the built-in `MetadataSequencingPolicy` is used, `parameters = "<metadataKey>"`.
- **`@Bean` may be shared** — do not delete the bean just because one processor migrated; others may still reference it.

## Used By

- **[[event-processor]]** — Step 6 (when YAML or `@Bean` declares a sequencing policy for `$SOURCE`'s group)
  and Step 7 (when `$SOURCE`'s project ships a custom `SequencingPolicy` implementation)
