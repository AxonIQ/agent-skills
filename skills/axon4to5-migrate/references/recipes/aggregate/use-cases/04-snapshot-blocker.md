# 04 — Snapshot trigger (B1 auto-migration and Blocker)

**Why this case is interesting:** `@Aggregate(snapshotTriggerDefinition = "...")` does NOT carry over to AF5. The `@EventSourced` / `@EventSourcedEntity` annotations do not expose a portable snapshotting attribute. Two paths exist: (A) the companion bean is a known translatable type → recipe **auto-migrates** to `EventSourcedEntityModule.declarative(...)` — no Blocker; (B) companion is a custom subclass or not in scope → recipe **halts** with Blocker B1.

**Apply-condition:** `$SOURCE` has `snapshotTriggerDefinition` attribute on `@Aggregate`.

## Detection

```
grep -nE 'snapshotTriggerDefinition|Snapshotter|SnapshotTriggerDefinition' <aggregate file> <aggregate package>
```

Also look for OpenRewrite leaving the marker `// TODO #LLM: reconfigure snapshot trigger ...` after stripping the attribute.

## Path A — Auto-migration (companion bean is translatable)

**Trigger:** companion bean class (located by `@Component("<beanName>")` in scope) extends `EventCountSnapshotTriggerDefinition` or `AggregateLoadTimeSnapshotTriggerDefinition` with an explicit threshold.

Translation table:

| AF4 trigger | AF5 `SnapshotPolicy` |
|---|---|
| `EventCountSnapshotTriggerDefinition(snapshotter, N)` | `SnapshotPolicy.afterEvents(N)` |
| `AggregateLoadTimeSnapshotTriggerDefinition(snapshotter, Duration)` | `SnapshotPolicy.whenSourcingTimeExceeds(Duration)` |

### Before (AF4)

```java
// Bike.java
@Aggregate(snapshotTriggerDefinition = "bikeSnapshotDefinition")
public class Bike { ... }

// BikeSnapshotDefinition.java
@Component("bikeSnapshotDefinition")
public class BikeSnapshotDefinition extends EventCountSnapshotTriggerDefinition {
    public BikeSnapshotDefinition(Snapshotter snapshotter) {
        super(snapshotter, 10);
    }
}
```

### After — `configuration=native`

```java
// Bike.java — @EventSourcedEntity retained; snapshotTriggerDefinition dropped
@EventSourcedEntity(tagKey = "Bike", idType = String.class)
public class Bike { ... }   // class-body migration (Topics 1–5) also applied

// AxonConfig.java (or BikeConfiguration.java) — new module registration with snapshotPolicy
configurer
    .componentRegistry(cr -> cr.registerComponent(
            SnapshotStore.class,
            c -> new InMemorySnapshotStore()))
    .modelling()
    .registerEventSourcedEntity(
        EventSourcedEntityModule.declarative(String.class, Bike.class)
            .snapshotPolicy(c -> SnapshotPolicy.afterEvents(10))
    );

// BikeSnapshotDefinition.java → dead code; LEARNINGS entry: "delete BikeSnapshotDefinition"
```

### After — `configuration=spring`

```java
// Bike.java — @EventSourced DROPPED; module bean below registers it
public class Bike { ... }   // class-body migration (Topics 1–5) still applied; NO @EventSourced

// BikeConfiguration.java — replaces BikeSnapshotDefinition.java
@Configuration
class BikeConfiguration {
    @Bean
    EventSourcedEntityModule<String, Bike> bikeModule() {
        return EventSourcedEntityModule.declarative(String.class, Bike.class)
                .snapshotPolicy(c -> SnapshotPolicy.afterEvents(10))
                .build();
    }
    @Bean
    SnapshotStore snapshotStore() {
        return new InMemorySnapshotStore();
        // switch to new AxonServerSnapshotStore(...) if the AF4 app used Axon Server
    }
}

// BikeSnapshotDefinition.java → dead code; LEARNINGS entry: "delete BikeSnapshotDefinition"
```

Result emitted after auto-migration:

```
return SUCCESS

> **Result:** ✅ Success
> **Source:** `com.example.bike.Bike`
> **Recipe:** axon4to5-aggregate
>
> **Notes:** All Success Criteria match. Snapshot trigger auto-migrated:
> `bikeSnapshotDefinition` (EventCountSnapshotTriggerDefinition, N=10) →
> `EventSourcedEntityModule.declarative(String.class, Bike.class).snapshotPolicy(c -> SnapshotPolicy.afterEvents(10)).build()`.
>
> **Learnings:**
> - `BikeSnapshotDefinition` is now dead code — delete it.
```

## Path B — Blocker (custom subclass or companion not found)

**Trigger:** companion bean is a custom subclass of `EventCountSnapshotTriggerDefinition` (overrides `shouldSnapshot(...)` or similar), or the companion bean cannot be located in scope.

The recipe halts because it cannot safely derive the threshold. The caller resolves manually — typically by:

1. **Picking `solve-manually`** — edit the source to remove `snapshotTriggerDefinition`, remove the matching `dwellingSnapshotTrigger` bean wiring elsewhere in the codebase, then re-invoke the skill. The recipe re-scans on re-invocation; the attribute is gone, B1 doesn't fire, the recipe proceeds.
2. **Picking `revert`** — undo any partial edits the recipe applied; restore the pre-recipe `@Aggregate(snapshotTriggerDefinition = "...")` form.
3. **Picking `skip`** — leave the source in whatever partial state OpenRewrite left it; the queue moves on. The blocker shows up in the final report.

## What the Blocker looks like

Source: heroes `Dwelling.java`, annotated `@Aggregate(snapshotTriggerDefinition = "dwellingSnapshotTrigger")`.

```
return BLOCKER

> **Result:** 🚧 Blocker
> **Source:** `com.dddheroes.heroesofddd.creaturerecruitment.write.dwelling.Dwelling`
> **Recipe:** axon4to5-aggregate
>
> **Notes:** 1 blocker detected. Caller must resolve before re-invoking.
>
> 1. **B1 (snapshotTriggerDefinition)** at `Dwelling.java:27` — `@Aggregate(snapshotTriggerDefinition = "dwellingSnapshotTrigger")`. AF5 `@EventSourced` / `@EventSourcedEntity` does not expose a portable replacement attribute (see [configuration-migration.adoc](../../../docs/paths/aggregates/configuration-migration.adoc) IMPORTANT note). The snapshot bean `dwellingSnapshotTrigger` is referenced ONLY from this aggregate; existing snapshot rows in event storage are not touched by this skill — data migration is out of scope.
>
> **Learnings:**
> - `Dwelling`'s `public DwellingId dwellingId;` field was made public solely for snapshotting; once snapshotting is dropped, it can be tightened to `private` during a follow-up stabilisation pass (not by this recipe).
>
> **Options:**
>
> _For B1 (snapshot):_
> - [ ] **skip** — leave `Dwelling` in its current partial state (any OpenRewrite edits already applied remain); queue moves on.
> - [ ] **revert** — undo this recipe's edits; restore the pre-recipe `@Aggregate(snapshotTriggerDefinition = "dwellingSnapshotTrigger")` shape.
> - [ ] **solve-manually** — pause; caller removes the `dwellingSnapshotTrigger` bean (and any snapshot-trigger configuration referencing it), strips the attribute from `@Aggregate`, then re-invokes the skill.
```

## After the caller resolves manually and re-invokes

Source no longer has the attribute (the caller dropped it). The recipe re-scans, B1 no longer fires, the recipe proceeds normally and emits Success:

```java
// AF4 (after caller manually dropped the attribute)
@Aggregate
public class Dwelling { … }

// AF5 (Path A — configuration=spring)
@EventSourced(tagKey = "Dwelling", idType = DwellingId.class)
public class Dwelling { … }

// AF5 (Path B — configuration=native)
@EventSourcedEntity(tagKey = "Dwelling", idType = DwellingId.class)
public class Dwelling { … }
```

Result emitted on the re-invocation:

```
return SUCCESS

> **Result:** ✅ Success
> **Source:** `com.dddheroes.heroesofddd.creaturerecruitment.write.dwelling.Dwelling`
> **Recipe:** axon4to5-aggregate
>
> **Notes:** All Success Criteria match. The caller had previously resolved Blocker B1 by removing the `snapshotTriggerDefinition` attribute and the matching bean; re-scan found no blockers and the recipe proceeded.
```

## Caveats

- **Existing snapshot rows in storage are NOT touched.** The recipe does not migrate stored data. When snapshotting is dropped (solve-manually), future loads replay the full event stream — a performance regression at large event counts. When auto-migrated, snapshotting continues with the same threshold.
- **Companion bean lifetime** — after auto-migration, the original companion bean class (e.g. `BikeSnapshotDefinition`) is unreferenced dead code. The recipe does NOT delete it (out of scope); the LEARNINGS block names it for the caller to delete.
- **Do NOT silently drop.** If the companion bean cannot be found or is a custom subclass, Blocker B1 MUST fire. Auto-migration only applies when the threshold is directly readable from `super(snapshotter, N)`.
- **`Snapshotter` / `SnapshotTriggerDefinition` direct field injections** (rare) also trigger B1. Detect via the same grep.
