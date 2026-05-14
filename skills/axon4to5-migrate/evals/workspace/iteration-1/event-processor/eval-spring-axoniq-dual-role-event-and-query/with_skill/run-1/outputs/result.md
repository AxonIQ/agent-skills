**Result:** ✅ Success
**Source:** `com.dddheroes.heroesofddd.creaturerecruitment.read.getalldwellings.GetAllDwellingsQueryHandler`
**Recipe:** axon4to5-event-processor

**Notes:** Dual-role class (use-case 07) — both `@EventHandler` and `@QueryHandler` migrated to keep file internally consistent. Applied: `@ProcessingGroup("Read_GetAllDwellings_QueryCache")` → `@Namespace("Read_GetAllDwellings_QueryCache")` (string preserved); added class-level `@SequencingPolicy(type = MetadataSequencingPolicy.class, parameters = GameMetaData.GAME_ID_KEY)`; AF4 → AF5 import swaps for `EventHandler`, `QueryHandler`, `MetaDataValue` → `MetadataValue`; `@MetaDataValue` parameter annotation rewritten on the `@EventHandler` method. `@Component`, method bodies, return types, and repository injection preserved verbatim.

**Learnings:**
- The `@QueryHandler` method on this class has no `@MetaDataValue` parameter — only the `@EventHandler` method required the parameter-annotation rewrite. The `@QueryHandler` import was still swapped to its AF5 location to keep the file internally consistent.
- `ResponseType` is not used in this file; no query-handler response-type rewrites required.
- Namespace string preserved as `"Read_GetAllDwellings_QueryCache"` (from the source `@ProcessingGroup`). Caller must ensure every external reference (YAML, `EventProcessorDefinition.pooledStreaming(...)`) uses the same string.
