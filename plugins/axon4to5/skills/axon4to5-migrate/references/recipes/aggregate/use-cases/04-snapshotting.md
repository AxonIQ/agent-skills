# 04 — Snapshot trigger migration (`SnapshotTriggerDefinition` → `@Snapshotting` / `SnapshotPolicy`)

**Why this case is interesting:** AF4 configured snapshotting with a `SnapshotTriggerDefinition` (usually a `@Bean` referenced by `@Aggregate(snapshotTriggerDefinition = "...")`). AF5.1 drives snapshotting from a `SnapshotPolicy` configured on the entity — `@Snapshotting` for `configuration=spring`, a `SnapshotPolicy` on the `EventSourcedEntityModule` for `configuration=native` — plus an explicit `SnapshotStore`. The recipe performs this migration (Toolbox Step S); it is **not** a blocker.

**Apply-condition:** `$SOURCE` had `snapshotTriggerDefinition` on `@Aggregate` (or a post-OpenRewrite `// TODO #LLM: reconfigure snapshot trigger` marker).

All shapes below are verified against `axon-5.1.x` (5.1.2-SNAPSHOT).

## Detection

```
grep -nE 'snapshotTriggerDefinition|Snapshotter|SnapshotTriggerDefinition' <aggregate file> <aggregate package>
```

Identify the companion `@Bean SnapshotTriggerDefinition` to learn the threshold — e.g. `new EventCountSnapshotTriggerDefinition(100)`.

## Trigger → policy mapping

| AF4 trigger | AF5 policy |
|---|---|
| `EventCountSnapshotTriggerDefinition(N)` | `SnapshotPolicy.afterEvents(N)` |
| `AggregateLoadTimeSnapshotTriggerDefinition(ms)` | `SnapshotPolicy.whenSourcingTimeExceeds(Duration.ofMillis(ms))` |
| `NoSnapshotTriggerDefinition` | none — drop snapshotting |
| custom subclass | compose built-ins with `.or(...)`, or implement `SnapshotPolicy.shouldSnapshot(EvolutionResult)` directly and register the instance via the configuration API |

`SnapshotPolicy` / `EvolutionResult` are in `org.axonframework.eventsourcing.snapshot.api`.

## Before (AF4)

```java
@Aggregate(snapshotTriggerDefinition = "dwellingSnapshotTrigger")
public class Dwelling { … }

// companion bean, elsewhere in config
@Bean
public SnapshotTriggerDefinition dwellingSnapshotTrigger(Snapshotter snapshotter) {
    return new EventCountSnapshotTriggerDefinition(snapshotter, 100);
}
```

## After (AF5) — `configuration=spring` (Path A)

```java
import org.axonframework.extension.spring.stereotype.EventSourced;
import org.axonframework.eventsourcing.annotation.Snapshotting;

@EventSourced(tagKey = "Dwelling", idType = DwellingId.class)
@Snapshotting(afterEvents = 100)
public class Dwelling { … }
```

```java
// the SnapshotStore the policy needs (OSS line: in-memory only)
import org.axonframework.eventsourcing.snapshot.store.SnapshotStore;
import org.axonframework.eventsourcing.snapshot.inmemory.InMemorySnapshotStore;

@Configuration
public class SnapshotConfig {
    @Bean
    public SnapshotStore snapshotStore() {
        return new InMemorySnapshotStore();
    }
}
```

The AF4 `dwellingSnapshotTrigger` bean is **deleted**. For a per-event policy (`whenEventMatches`), drop `@Snapshotting` and declare an explicit `@Bean EventSourcedEntityModule<DwellingId, Dwelling>` with `.snapshotPolicy(...)` instead — Spring picks up `Module` beans automatically.

## After (AF5) — `configuration=native` (Path B)

`autodetected(...)` has no snapshot hook, so switch this entity to `declarative(...)` and traverse the mandatory phases before `snapshotPolicy(...)` (which lives on `OptionalPhase`):

```java
import org.axonframework.eventsourcing.snapshot.api.SnapshotPolicy;
import org.axonframework.eventsourcing.snapshot.store.SnapshotStore;
import org.axonframework.eventsourcing.snapshot.inmemory.InMemorySnapshotStore;

EventSourcingConfigurer.create()
    .componentRegistry(cr -> cr.registerComponent(SnapshotStore.class, c -> new InMemorySnapshotStore()))
    .registerEntity(
        EventSourcedEntityModule.declarative(DwellingId.class, Dwelling.class)
            .messagingModel(/* … */)
            .entityFactory(/* … */)
            .criteriaResolver(/* … */)
            .snapshotPolicy(c -> SnapshotPolicy.afterEvents(100))
            .build()
    )
    .start();
```

## Result emitted (Path A, OSS line)

```
return SUCCESS

> **Result:** ✅ Success
> **Source:** `com.dddheroes.heroesofddd.creaturerecruitment.write.dwelling.Dwelling`
> **Recipe:** axon4to5-aggregate
>
> **Notes:** All Success Criteria match. Snapshotting migrated: `EventCountSnapshotTriggerDefinition(100)` → `@Snapshotting(afterEvents = 100)`; registered `InMemorySnapshotStore`; deleted the `dwellingSnapshotTrigger` bean.
>
> **Learnings:**
> ## 2026-06-01 — OSS axon-5.1.x ships only InMemorySnapshotStore
> **Trigger:** project-shape
> **Where:** `creaturerecruitment.write.dwelling.Dwelling`
> **Surprise:** No persistent open-source `SnapshotStore` exists on `axon-5.1.x`; `InMemorySnapshotStore` loses snapshots on restart.
> **Resolution:** Wired `InMemorySnapshotStore` to preserve in-run behaviour; flagged that persistent storage needs `framework=axoniq`'s `AxonServerSnapshotStore`.
```

## Caveats

- **A policy with no `SnapshotStore` silently never persists.** Always register a store. On `framework=axon` the only option is `InMemorySnapshotStore` (lost on restart — record a Learning); `framework=axoniq` has the persistent `AxonServerSnapshotStore` (`io.axoniq.framework.axonserver.connector.snapshot`, constructor `(AxonServerConnection, Converter)`).
- **`@Snapshotting` is `configuration=spring` only**, `@Target(TYPE)`, attributes `afterEvents` (int) and `afterSourcingTime` (ISO-8601 String, e.g. `"PT5S"`); both set → either fires.
- **Existing snapshot rows in storage are NOT touched** — data migration is out of scope. The new store starts empty; entities reconstruct from the event stream until fresh snapshots are written.
- **Delete the AF4 companion bean** — the `@Bean SnapshotTriggerDefinition` (and any `Snapshotter` wiring) is dead after migration. If it is outside `# Scope`, name it in a Learning for the caller to remove.
- **`Dwelling`'s `public DwellingId dwellingId;`** field made public solely for AF4 snapshotting can be tightened to `private` in a follow-up stabilisation pass (not by this recipe).
