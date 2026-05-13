# Recipe `event-processor` — blockers

Run every Detection grep BEFORE `## Procedure`. For each hit: run the `AskUserQuestion`, record under `decisions.<key>`, apply "Effect". Never silently rewrite around an unresolved blocker.

> 🚨 **DATA MIGRATION IS NOT IN SCOPE.** Token-store rows, DLQ entries, and any other persisted state are NOT migrated by this skill. Token data is rebuildable by replay; `move-to-jpa-token-store` is a **code rewrite + user-run replay**, NOT a Mongo→relational data export.

## B1 — `MongoTokenStore` (no AF5 release of `axon-mongo`)

**Why.** No AF5 release of `axon-mongo` / `MongoTokenStore`. Token data is rebuildable by replay, but the switch MUST be a deliberate user decision.

**Detection:**
```bash
grep -RnE 'MongoTokenStore|registerTokenStore.*Mongo|org\.axonframework\.extensions\.mongo' \
     --include='*.java' --include='*.kt' --include='*.yml' --include='*.yaml' --include='*.properties' <project root>
```

**AskUserQuestion:**
- `move-to-jpa-token-store` — **code rewrite only.** Switch bean to AF5 `JpaTokenStore`. Token data rebuilt by **replay from event store**, run by the user. If project can't tolerate a replay (large event log, side-effecting projections, idempotency concerns), pick `pause-migration`.
- `pause-migration` — user replaces token store (incl. data plan) before resuming.
- `accept-stays-af4` — keep token-store slice on AF4 deps; recipe exits.

**Output key:** `mongo-token-store: none | move-to-jpa-token-store | pause-migration | accept-stays-af4`.

**Effect:**
- `move-to-jpa-token-store` → proceed; surface for event-storage-engine to replace the bean. Learnings line: *"User accepts replay-from-event-store as the token-data plan."*
- others → `result: blocked`, `next: record-and-skip`, exit.

## B2 — Saga handler in candidate

**Why.** Sagas have no automatic AF5 rewrite. Wrong recipe.

**Detection:**
```bash
grep -RlnE '@SagaEventHandler\b|@StartSaga\b|@EndSaga\b|@Saga\b' --include='*.java' --include='*.kt' <candidate file>
```

**AskUserQuestion:**
- `wrong-recipe-skip` *(Recommended)* — orchestrator routes to saga slot; this recipe exits untouched.
- `pause-migration` — user removes saga first.

**Output key:** `saga-handler-detected: none | wrong-recipe-skip | pause-migration`.

**Effect:**
- `wrong-recipe-skip` → `result: rejected`, `next: route-to:saga`, exit. No edits.
- `pause-migration` → `result: blocked`, `next: record-and-skip`, exit.

## B3 — `axon-kafka` extension (no AF5 release)

**Why.** No AF5 release of `axon-kafka`. `KafkaPublisher`, `StreamableKafkaMessageSource`, `KafkaMessageSourceConfigurer`, `KafkaProperties` reference AF4-only APIs. No automatic translation.

**Detection:**
```bash
grep -RnE 'org\.axonframework\.extensions\.kafka|axon-kafka|KafkaPublisher|StreamableKafkaMessageSource|KafkaMessageSourceConfigurer' \
     --include='*.java' --include='*.kt' --include='*.yml' --include='*.yaml' --include='*.properties' --include='pom.xml' --include='*.gradle*' <project root>
```

**AskUserQuestion:**
- `accept-stays-af4` — Kafka slice stays AF4; affected modules won't compile against AF5; scope pinned.
- `pause-migration` — user replaces Kafka integration (native Kafka client + custom `EventBus` adapter, or move publication to Axon Server).
- `remove-feature-first` — user deletes Kafka wiring now, re-introduces a non-Axon Kafka integration later.

**Output key:** `axon-kafka: none | accept-stays-af4 | pause-migration | remove-feature-first`.

**Effect:** Any non-`none` → `result: blocked`, `next: record-and-skip`, exit. No edits. Learnings line: *"User accepts axon-kafka has no AF5 path; Kafka slice is the user's responsibility, out-of-band."*

> 🚨 **No data migration.** Switching off `axon-kafka` does not migrate, replay, or re-publish any messages already on Kafka topics.
