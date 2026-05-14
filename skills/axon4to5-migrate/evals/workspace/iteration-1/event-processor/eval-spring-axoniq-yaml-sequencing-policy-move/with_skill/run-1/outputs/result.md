**Result:** ✅ Success
**Source:** `application.yaml`
**Recipe:** axon4to5-event-processor

**Notes:**
- Renamed top-level `axon.serializer.*` → `axon.converter.*` (nested keys `general`, `events`, `messages` preserved verbatim).
- Deleted `sequencing-policy: gameIdSequencingPolicy` from all 5 processors under `axon.eventhandling.processors.*` (moves to class-level `@SequencingPolicy` annotation on each projector — out of scope for this eval).
- No `mode: tracking` keys found; existing `mode: pooled` and `mode: subscribing` left unchanged.
- All other keys preserved byte-for-byte (`batch-size`, `initial-segment-count`, `dlq.enabled`, etc.).

**Learnings:**
- 5 projectors require follow-up class-level `@SequencingPolicy(type = MetadataSequencingPolicy.class, parameters = "<gameId metadata key>")` to preserve `gameIdSequencingPolicy` behaviour: `Automation_WhenCreatureRecruitedThenAddToArmy_Processor`, `Automation_WhenWeekStartedThenProclaimWeekSymbol_Processor`, `Automation_WhenWeekSymbolProclaimedThenIncreaseDwellingAvailableCreatures_Processor`, `ReadModel_Dwelling`, `Read_GetAllDwellings_QueryCache`.
- DLQ wired on 3 processors (`dlq.enabled: true`) — informational, route to commercial `axoniq-dead-letter` flow per `dlq.adoc`.
- `axon.serializer` rename was scoped to this YAML slice; broader project-wide `Serializer` → `Converter` migration belongs to the serializer recipe.
