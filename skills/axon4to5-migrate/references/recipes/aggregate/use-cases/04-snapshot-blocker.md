# 04 — Snapshot trigger Blocker (B1)

**Why this case is interesting:** `@Aggregate(snapshotTriggerDefinition = "...")` does NOT carry over to AF5. The `@EventSourced` / `@EventSourcedEntity` annotations do not expose a portable snapshotting attribute (see [configuration-migration.adoc](../../../docs/paths/aggregates/configuration-migration.adoc) IMPORTANT note: "attributes you may have used in AF4 (like caching, snapshotting, …) are no longer supported"). The recipe halts because dropping the trigger has runtime consequences the caller must accept, and the snapshot-trigger bean wiring lives outside this recipe's scope.

**Apply-condition:** `$SOURCE` has `snapshotTriggerDefinition` attribute on `@Aggregate`.

## Detection

```
grep -nE 'snapshotTriggerDefinition|Snapshotter|SnapshotTriggerDefinition' <aggregate file> <aggregate package>
```

Also look for OpenRewrite leaving the marker `// TODO #LLM: reconfigure snapshot trigger ...` after stripping the attribute.

## Recipe behaviour

The recipe never silently drops the attribute. On detection it adds B1 to the unified Blocker emission (see § Blocker, "Emission model — all blockers at once" in [RECIPE.md](../RECIPE.md)) and halts. The caller resolves manually — typically by:

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

- **Existing snapshot rows in storage are NOT touched.** The recipe does not migrate stored data. Dropping the trigger means future loads of `Dwelling` replay the full event stream instead of resuming from a snapshot — a performance regression that may be material at large event counts. The caller owns that tradeoff.
- **`dwellingSnapshotTrigger` bean lifetime** — the bean is referenced ONLY by `@Aggregate(snapshotTriggerDefinition = "...")`. After the attribute is dropped, the bean is unreferenced. The recipe does NOT delete the bean (out of scope: Spring config beans); the caller cleans it up as part of the manual resolution.
- **Do NOT silently drop the attribute.** The recipe MUST emit Blocker B1 on every detection. Snapshotting is a behavioural concern; the caller must accept the change explicitly by editing the source. There is no "auto-drop" mode.
- **`Snapshotter` / `SnapshotTriggerDefinition` direct field injections** (rare — usually the trigger is bean-name-referenced) also trigger B1. Detect via the same grep.
