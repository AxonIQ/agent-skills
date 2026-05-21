# 04 — Snapshot trigger (B1 — Blocker, no migration path)

**Why this case is interesting:** `@Aggregate(snapshotTriggerDefinition = "...")` does NOT carry over to AF5. The `@EventSourced` / `@EventSourcedEntity` annotations do not expose a portable snapshotting attribute.

**B1 always fires as a Blocker.** There is currently no verified auto-migration path for snapshot trigger configuration in either `configuration=spring` or `configuration=native`. The `EventSourcedEntityModule.declarative()` builder chain required to wire `SnapshotPolicy` is non-trivial: `declarative()` returns `MessagingModelPhase`, which only exposes `messagingModel()`. The `snapshotPolicy()` method is only reachable on `OptionalPhase` — after all mandatory phases (`messagingModel() → entityFactory() → criteriaResolver()`) have been traversed. The correct end-to-end pattern has not yet been validated for auto-migration. Do NOT attempt auto-migration — always halt with Blocker B1 and let the caller resolve manually.

**Apply-condition:** `$SOURCE` has `snapshotTriggerDefinition` attribute on `@Aggregate`.

## Detection

```
grep -nE 'snapshotTriggerDefinition|Snapshotter|SnapshotTriggerDefinition' <aggregate file> <aggregate package>
```

Also look for OpenRewrite leaving the marker `// TODO #LLM: reconfigure snapshot trigger ...` after stripping the attribute.

## Blocker B1

**Trigger:** `$SOURCE` has `snapshotTriggerDefinition` attribute on `@Aggregate` — regardless of what the companion bean is.

The recipe halts because there is no verified auto-migration path. The caller resolves manually — typically by:

1. **Picking `solve-manually`** — edit the source to remove `snapshotTriggerDefinition`, remove the matching snapshot trigger bean wiring elsewhere in the codebase, then re-invoke the skill. The recipe re-scans on re-invocation; the attribute is gone, B1 doesn't fire, the recipe proceeds.
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
> 1. **B1 (snapshotTriggerDefinition)** at `Dwelling.java:27` — `@Aggregate(snapshotTriggerDefinition = "dwellingSnapshotTrigger")`. AF5 `@EventSourced` / `@EventSourcedEntity` does not expose a portable replacement attribute (see [configuration-migration.adoc](../../../docs/paths/aggregates/configuration-migration.adoc) IMPORTANT note). There is currently no verified auto-migration path — the caller must resolve manually. The snapshot bean `dwellingSnapshotTrigger` is referenced ONLY from this aggregate; existing snapshot rows in event storage are not touched by this skill — data migration is out of scope.
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

// AF5 (configuration=spring)
@EventSourced(tagKey = "Dwelling", idType = DwellingId.class)
public class Dwelling { … }

// AF5 (configuration=native)
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

- **Existing snapshot rows in storage are NOT touched.** The recipe does not migrate stored data. When snapshotting is dropped (solve-manually), future loads replay the full event stream — a performance regression at large event counts.
- **Companion bean lifetime** — after the caller resolves manually, the original companion bean class (e.g. `BikeSnapshotDefinition`) is unreferenced dead code. The LEARNINGS block names it for the caller to delete.
- **Do NOT silently drop.** B1 MUST fire whenever `snapshotTriggerDefinition` is present. Do NOT attempt to auto-migrate, do NOT skip emitting the blocker.
- **`Snapshotter` / `SnapshotTriggerDefinition` direct field injections** (rare) also trigger B1. Detect via the same grep.
