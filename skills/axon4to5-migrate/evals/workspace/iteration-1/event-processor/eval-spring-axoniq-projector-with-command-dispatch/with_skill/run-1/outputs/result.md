**Result:** ✅ Success
**Source:** `com.dddheroes.heroesofddd.creaturerecruitment.automation.WhenCreatureRecruitedThenAddToArmyProcessor`
**Recipe:** axon4to5-event-processor

**Notes:** Single-file migration per use-case 02 (projector with in-handler command dispatch). All Success Criteria match on first Apply: AF4 imports removed; `@ProcessingGroup` → `@Namespace` (string preserved); `@DisallowReplay`, `@EventHandler` swapped to AF5 packages; both `@MetaDataValue` parameters flipped to `@MetadataValue` (capital-D loss + package change); class-level `@SequencingPolicy(type = MetadataSequencingPolicy.class, parameters = GameMetaData.GAME_ID_KEY)` added; `CommandGateway` field + constructor removed; `CommandDispatcher` added as last method parameter; handler return type now `CompletableFuture<? extends Message>` (AF5 `Message` is non-generic); `sendAndWait` rewritten to `send(...).getResultMessage()` with `.thenApply(m -> (Message) m).exceptionallyCompose(failure -> ...)` for the compensation path.

**Learnings:**
- `GameMetaData.with(gameId, playerId)` helper still produces `org.axonframework.messaging.core.MetaData` (AF5 package) — if the helper itself remains on AF4 `org.axonframework.messaging.MetaData`, command dispatch will fail at runtime even though it compiles. Flagged for the project-wide pass; helper migration is outside the strict event-processor recipe scope.
