**Result:** ✅ Success
**Source:** `com.dddheroes.heroesofddd.creaturerecruitment.read.DwellingReadModelProjector`
**Recipe:** axon4to5-event-processor

**Notes:** Pure-projector Spring variant (use-case 01). All Success Criteria match. `@ProcessingGroup("ReadModel_Dwelling")` swapped to `@Namespace("ReadModel_Dwelling")` (string preserved exactly). AF4 imports for `@EventHandler`, `@ResetHandler`, and `@MetaDataValue` replaced with their AF5 counterparts (`org.axonframework.messaging.eventhandling.annotation.EventHandler`, `org.axonframework.messaging.eventhandling.replay.annotation.ResetHandler`, `org.axonframework.messaging.core.annotation.MetadataValue`). `@MetaDataValue` parameter annotation flipped to `@MetadataValue` (capital `M`, lowercase `d`). Class-level `@SequencingPolicy(type = MetadataSequencingPolicy.class, parameters = GameMetaData.GAME_ID_KEY)` added to preserve the AF4 `@Bean SequencingPolicy gameIdSequencingPolicy` behaviour. `@Component` (Spring stereotype) preserved. No `CommandDispatcher` introduced — pure read-side projector with no in-handler dispatch.

**Learnings:**
- AF4 `@Bean SequencingPolicy gameIdSequencingPolicy` keyed on `GameMetaData.GAME_ID_KEY` becomes orphan once all dependent processor groups have been migrated to class-level `@SequencingPolicy` — do not delete here; write-configuration cleanup owns bean removal.
