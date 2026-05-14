**Result:** 🚧 Blocker
**Source:** `com.dddheroes.heroesofddd.creaturerecruitment.write.Dwelling`
**Recipe:** axon4to5-aggregate

**Notes:** 1 blocker detected. Caller must resolve before re-invoking.

1. **B1 (snapshotTriggerDefinition)** at `Dwelling.java:27` — `@Aggregate(snapshotTriggerDefinition = "dwellingSnapshotTrigger")`. AF5 `@EventSourced` / `@EventSourcedEntity` does not expose a portable replacement snapshot attribute (see configuration-migration.adoc IMPORTANT note: "attributes you may have used in AF4 (like caching, snapshotting, …) are no longer supported"). The snapshot bean `dwellingSnapshotTrigger` is referenced only from this aggregate; existing snapshot rows in event storage are not touched by this skill — data migration is out of scope.

**Learnings:**
- `Dwelling`'s `public DwellingId dwellingId;` field (`Dwelling.java:33`) was made public solely for snapshotting; once snapshotting is dropped, it can be tightened to `private` during a follow-up stabilisation pass (not by this recipe).

**Options:**

_For B1 (snapshot):_
- [ ] **skip** — leave `Dwelling` in its current partial state (AF4 shape preserved on disk); queue moves on.
- [ ] **revert** — undo this recipe's edits; restore the pre-recipe `@Aggregate(snapshotTriggerDefinition = "dwellingSnapshotTrigger")` shape.
- [ ] **solve-manually** — pause; caller removes the `dwellingSnapshotTrigger` bean (and any snapshot-trigger configuration referencing it), strips the `snapshotTriggerDefinition` attribute from `@Aggregate`, then re-invokes the skill.
