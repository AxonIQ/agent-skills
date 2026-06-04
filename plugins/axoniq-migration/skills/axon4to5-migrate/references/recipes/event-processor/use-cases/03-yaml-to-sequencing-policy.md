# 03 — YAML + `@Bean SequencingPolicy` → class-level `@SequencingPolicy`

**Why this case is interesting:** AF4 projects expressed per-processor sequencing two ways: either as a YAML key under `axon.eventhandling.processors.<group>.sequencing-policy` OR as a `@Bean SequencingPolicy <group>SequencingPolicy` referenced by `EventProcessingConfigurer.assignSequencingPolicy(...)`. AF5 collapses both forms into a class-level `@SequencingPolicy` annotation on the projector itself. The recipe must:

- Add `@SequencingPolicy` at the class level (Step 6).
- Delete the YAML key for `$SOURCE`'s group (Step 8).
- Leave the `@Bean SequencingPolicy` definition in place if other processors share it (do NOT delete; flag as potential orphan in Result NOTES).

**Apply-condition:** `application.yaml` declares `axon.eventhandling.processors.<group>.sequencing-policy` for `$SOURCE`'s group OR a `@Bean SequencingPolicy` is registered via `EventProcessingConfigurer.assignSequencingPolicy(...)`.

## Before (AF4)

`application.yaml`:

```yaml
axon:
  serializer:
    events: jackson
  eventhandling:
    processors:
      ReadModel_Dwelling:
        mode: tracking
        sequencing-policy: gameIdSequencingPolicy
      Automation_WhenCreatureRecruitedThenAddToArmy_Processor:
        mode: pooled
        sequencing-policy: gameIdSequencingPolicy
        thread-count: 8
```

`GameConfiguration.java`:

```java
import org.axonframework.eventhandling.async.SequencingPolicy;
import org.axonframework.eventhandling.EventMessage;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class GameConfiguration {

    @Bean
    public SequencingPolicy<EventMessage<?>> gameIdSequencingPolicy() {
        return event -> event.getMetaData().get(GameMetaData.GAME_ID_KEY);
    }
}
```

`DwellingReadModelProjector.java` (relevant header — full body in use-case 01):

```java
@Component
@ProcessingGroup("ReadModel_Dwelling")
public class DwellingReadModelProjector { … }
```

## After (AF5)

`application.yaml`:

```yaml
axon:
  converter:
    events: jackson
  eventhandling:
    processors:
      ReadModel_Dwelling:
        mode: pooled
      Automation_WhenCreatureRecruitedThenAddToArmy_Processor:
        mode: pooled
        thread-count: 8
```

`GameConfiguration.java` — kept as-is for now (the bean is shared across two processors). After all dependent processors are migrated, the bean becomes orphan; the recipe surfaces that in Result NOTES but does NOT delete the bean (out of scope).

`DwellingReadModelProjector.java`:

```java
@Component
@Namespace("ReadModel_Dwelling")
@SequencingPolicy(type = MetadataSequencingPolicy.class, parameters = GameMetaData.GAME_ID_KEY)
public class DwellingReadModelProjector { … }
```

## What changed

- **YAML**:
  - `axon.eventhandling.processors.ReadModel_Dwelling.sequencing-policy: gameIdSequencingPolicy` — DELETED. The information now lives on the class.
  - `axon.eventhandling.processors.ReadModel_Dwelling.mode: tracking` → `mode: pooled`. AF5 has no `TrackingEventProcessor`; `PooledStreamingEventProcessor` is the direct replacement.
  - `axon.serializer.*` → `axon.converter.*` (only the slice in scope — full conversion is the serializer recipe's job; surface as a Learning).
- **Class annotation**: `@SequencingPolicy(type = MetadataSequencingPolicy.class, parameters = GameMetaData.GAME_ID_KEY)` added at class level. `MetadataSequencingPolicy` is a built-in AF5 policy that reads a single metadata key — semantically equivalent to the AF4 `event -> event.getMetaData().get(GameMetaData.GAME_ID_KEY)` lambda.
- **`@Bean` definition**: left in place. `gameIdSequencingPolicy` is referenced by TWO processors in this example; the recipe migrates ONLY `$SOURCE`'s reference. The bean becomes orphan only when BOTH processors have been migrated to class-level annotations — that detection (and the bean deletion) is the orchestrator's concern, not this recipe's.

## Built-in `SequencingPolicy` types

| AF5 policy class | Behaviour | AF4 equivalent |
|---|---|---|
| `MetadataSequencingPolicy` | Sequence by a single metadata key (`parameters = "<key>"`). | `event -> event.getMetaData().get("<key>")` lambda. |
| `SequentialPerAggregatePolicy` | One sequence per aggregate id. **AF4 default**. | `SequentialPerAggregatePolicy.INSTANCE`. |
| `SequentialPolicy` | All events strictly sequential. **AF5/DCB default**. | `SequentialPolicy.INSTANCE`. |
| `FullConcurrencyPolicy` | No sequencing — handlers can run in parallel for any event. | `FullConcurrencyPolicy.INSTANCE`. |

For these four, the recipe just emits `@SequencingPolicy(type = <PolicyClass>.class[, parameters = "<key>"])`. No body migration needed.

For **custom policies** (a project-specific class implementing `SequencingPolicy<EventMessage<?>>`), see use-case 06.

## Caveats

- **`mode: tracking` → `mode: pooled` is mandatory** for any YAML processor entry; `TrackingEventProcessor` is gone in AF5. Subscribing processors stay `mode: subscribing`.
- **Do NOT delete the `@Bean SequencingPolicy` definition unless EVERY referencing processor has been migrated.** Premature deletion breaks the other processors at startup. Flag in Result NOTES that it MAY become orphan once the migration is complete.
- **`MetadataSequencingPolicy` parameter is a String key**, not a `Function<EventMessage, Object>`. If the AF4 lambda did anything more complex than a single metadata read (e.g. `event.getMetaData().get("game-id") + ":" + event.getPayload().tenantId()`), the policy is **custom** and use-case 06 applies — `MetadataSequencingPolicy` will not preserve the behaviour.
- **`axon.serializer.*` rename has wider blast radius.** This recipe rewrites only the slice in scope. The full project-wide rename (`axon.serializer.events: jackson` plus every Java/Spring reference to `Serializer` beans) belongs to the serializer recipe; surface as a Learning if the YAML has more `axon.serializer.*` keys than this recipe touches.
- **Processor renames create silent failures.** Do not rename the processing-group string while doing the sequencing-policy move — the `@Namespace` value, the YAML key, the `EventProcessorDefinition.pooledStreaming(...)` argument, and any `EventProcessingConfigurer.assignHandlerTypesMatching(...)` must all remain the same string.
