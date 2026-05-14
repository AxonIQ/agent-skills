**Result:** ⏭️ Rejected
**Source:** `com.dddheroes.heroesofddd.creaturerecruitment.read.DwellingReadModelProjector`
**Recipe:** axon4to5-aggregate

**Notes:** Applicable predicate 2 failed at `DwellingReadModelProjector.java:13` — class is annotated `@ProcessingGroup("ReadModel_Dwelling")` with zero `@CommandHandler` methods (only `@EventHandler` and `@ResetHandler`). This is a read-model projector / event-handling component, not an aggregate. Route to the `event-processor` recipe — the aggregate recipe does not touch projector sources. Source file left byte-identical (no `@EventSourced` / `@EventSourcedEntity` / `@EntityCreator` annotations added).
