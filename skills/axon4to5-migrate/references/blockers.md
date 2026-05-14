# Blockers — AF5 gaps with no portable target

Master index of every AF5 feature gap the orchestrator must surface as `AskUserQuestion`. Each blocker has a stable global key (`B1..B10`), a detection grep, the verbatim `AskUserQuestion` options, the `Output.decisions` key the recipe records, and the "Effect" on the recipe.

**Recipes link in here** via fragment IDs (e.g. `[blockers.md#B5](blockers.md#B5)`); recipes MUST NOT duplicate detection logic.

> 🚨 **DATA MIGRATION IS NOT IN SCOPE.** Every `move-to-*` option is a **code-rewrite choice, not a data- or schema-migration offer**. The user owns any out-of-band data move on a non-prod copy first. If the user has not planned the move, prefer `pause-migration` over `move-to-*`.

## How a recipe uses this file

1. In `## Decision points`, declare an entry referencing the relevant `B<n>` keys below.
2. On Preflight, run the **Detection** grep for each.
3. On a hit AND the key isn't yet in `inputs.decisions` → recipe emits **🔒 await decision**; orchestrator resolves (auto-policy or `AskUserQuestion`) and re-invokes.
4. Recipe applies **Effect** based on `inputs.decisions.<key>` (`proceed` / `output { result: blocked }` / `output { result: rejected }`).
5. The recipe never proceeds past `## Preflight` while any fired blocker is unresolved (await suspends the flow until the orchestrator returns the answer).

---

## B1 — `snapshotTriggerDefinition` / `Snapshotter` / `SnapshotTriggerDefinition`

**Used by:** `aggregate`.

**Why blocker.** `@EventSourcedEntity` does not yet expose a finalized snapshot API. AF4 trigger types have no AF5 rename target.

**Detection.**
```bash
grep -RnE 'snapshotTriggerDefinition|Snapshotter|SnapshotTriggerDefinition' \
     --include='*.java' --include='*.kt' <aggregate file> <aggregate package>
```

**Post-OpenRewrite caveat.** The bulk recipe silently strips `snapshotTriggerDefinition` from `@Aggregate` and leaves a `// TODO #LLM: reconfigure snapshot trigger …` marker. Run secondary probes:
```bash
grep -RnE 'TODO[^\n]*snapshot' --include='*.java' --include='*.kt' <aggregate file> <aggregate package>
git log -p -- <aggregate file> | grep -E 'snapshotTriggerDefinition'
```
Recommended: pin the decision in `progress.md` **before** OpenRewrite runs.

**AskUserQuestion.**
- `accept-drop` — drop the attribute; no snapshotting until AF5 ships the API.
- `pause-migration` — user removes/relocates snapshot config first.
- `remove-feature-first` — user deletes snapshot config now, re-introduces later.

**Output key.** `snapshotting: none | accept-drop | pause-migration | remove-feature-first`

**Effect.**
- `accept-drop` → proceed; do NOT carry the attribute to `@EventSourced`.
- others → `result: blocked`, exit.

---

## B2 — Map-typed `@AggregateMember`

**Used by:** `aggregate` (multi-entity variant).

**Why blocker.** `Map<K, V>`-typed `@AggregateMember` is a breaking change — `@EntityMember` does not support the same shape. Auto-rewrite silently re-keys the collection.

**Detection.**
```bash
grep -RnE '@AggregateMember[\s\S]{0,200}Map<' --include='*.java' --include='*.kt' <aggregate file>
```

**AskUserQuestion.**
- `surface-and-defer` *(Recommended)* — emit Output noting the Map-typed member; user redesigns to `List`/`Set` first.
- `pause-migration` — user redesigns now.

**Output key.** `map-typed-aggregate-member: none | surface-and-defer | pause-migration`

**Effect.** Either path → `result: blocked`, exit. No edits.

---

## B3 — `SagaTestFixture` on an aggregate's test class

**Used by:** `aggregate`.

**Why blocker.** No AF5 replacement for `SagaTestFixture`.

**Detection.**
```bash
grep -RnE 'SagaTestFixture' --include='*.java' --include='*.kt' <test class>
```

**AskUserQuestion.**
- `surface-and-skip-test` *(Recommended)* — leave saga test on AF4; skip the test-fixture migration step.
- `pause-migration` — stop.

**Output key.** `saga-test-fixture-flagged: none | surface-and-skip-test | pause-migration`

**Effect.**
- `surface-and-skip-test` → run aggregate steps; skip the test-fixture migration block.
- `pause-migration` → `result: blocked`, exit.

---

## B4 — `@DeadlineHandler` / `DeadlineManager`

**Used by:** `aggregate`, `saga`, `event-storage-engine` (when bean declared at bootstrap layer).

**Why blocker.** AF5 has no successor to `DeadlineManager`, `@DeadlineHandler`, `DeadlineMessage`, or the four AF4 impls (`Simple`/`JobRunr`/`Quartz`/`DbScheduler`). Naive rewrite drops scheduling silently — missed deadlines turn into runtime business-logic failures.

**Detection.**
```bash
grep -RnE '@DeadlineHandler|DeadlineManager|DeadlineMessage|deadlineManager\.schedule|cancelSchedule|cancelAllWithinScope' \
     --include='*.java' --include='*.kt' <target>
```

Also inspect injected fields / constructor params and any standalone `@Bean DeadlineManager` on a `@Configuration` class.

**AskUserQuestion.**
- `accept-stays-af4` — deadline code stays AF4; affected slice won't compile under AF5 until AF5 ships a replacement or user removes/redesigns.
- `pause-migration` *(Recommended)* — user removes/replaces the deadline flow first (own `ScheduledExecutorService` + JPA timestamp poll, or contact Axoniq for workflow roadmap).
- `remove-feature-first` — user redesigns now; recipe exits.

**Output key.** `deadline-handler: none | accept-stays-af4 | pause-migration | remove-feature-first`

**Effect.**
- `accept-stays-af4` → proceed with the rest of the recipe; do NOT touch `@DeadlineHandler` methods or `DeadlineManager` injection; surface in Output `notes`. Standalone `@Bean DeadlineManager` → comment out + `TODO[AF5 migration: B4]`, never silently delete.
- others → `result: blocked`, exit.

---

## B5 — `MongoTokenStore` (no AF5 release of `axon-mongo`)

**Used by:** `event-processor`.

**Why blocker.** No AF5 release of `axon-mongo` / `MongoTokenStore`. Token data is rebuildable by replay, but the switch MUST be a deliberate user decision.

**Detection.**
```bash
grep -RnE 'MongoTokenStore|registerTokenStore.*Mongo|org\.axonframework\.extensions\.mongo' \
     --include='*.java' --include='*.kt' --include='*.yml' --include='*.yaml' --include='*.properties' <project root>
```

**AskUserQuestion.**
- `move-to-jpa-token-store` — **code rewrite only.** Switch bean to AF5 `JpaTokenStore`. Token data rebuilt by **replay from event store**, run by the user. If the project can't tolerate a replay, pick `pause-migration` instead.
- `pause-migration` — user replaces token store (incl. data plan) before resuming.
- `accept-stays-af4` — token-store slice stays AF4 deps; recipe exits.

**Output key.** `mongo-token-store: none | move-to-jpa-token-store | pause-migration | accept-stays-af4`

**Effect.**
- `move-to-jpa-token-store` → proceed; surface for `event-storage-engine` to replace the bean. Learnings: *"User accepts replay-from-event-store as the token-data plan."*
- others → `result: blocked`, exit.

---

## B6 — Saga handler found inside an event-processor candidate

**Used by:** `event-processor`.

**Why blocker.** Sagas have no automatic AF5 rewrite. The candidate is a saga, not an event-processor — wrong recipe.

**Detection.**
```bash
grep -RlnE '@SagaEventHandler\b|@StartSaga\b|@EndSaga\b|@Saga\b' --include='*.java' --include='*.kt' <candidate>
```

**AskUserQuestion.**
- `wrong-recipe-skip` *(Recommended)* — orchestrator routes this candidate to the `saga` slot; recipe exits untouched.
- `pause-migration` — user removes saga first.

**Output key.** `saga-handler-detected: none | wrong-recipe-skip | pause-migration`

**Effect.**
- `wrong-recipe-skip` → `result: rejected`, `route_to: saga`, exit. No edits.
- `pause-migration` → `result: blocked`, exit.

---

## B7 — `axon-kafka` extension (no AF5 release)

**Used by:** `event-processor`.

**Why blocker.** No AF5 release of `axon-kafka`. `KafkaPublisher`, `StreamableKafkaMessageSource`, `KafkaMessageSourceConfigurer`, `KafkaProperties` reference AF4-only APIs. No automatic translation.

**Detection.**
```bash
grep -RnE 'org\.axonframework\.extensions\.kafka|axon-kafka|KafkaPublisher|StreamableKafkaMessageSource|KafkaMessageSourceConfigurer' \
     --include='*.java' --include='*.kt' --include='*.yml' --include='*.yaml' --include='*.properties' --include='pom.xml' --include='*.gradle*' <project>
```

**AskUserQuestion.**
- `accept-stays-af4` — Kafka slice stays AF4; affected modules won't compile against AF5; scope pinned.
- `pause-migration` — user replaces Kafka integration (native Kafka client + custom `EventBus` adapter, or move publication to Axon Server).
- `remove-feature-first` — user deletes Kafka wiring now; re-introduces non-Axon Kafka later.

**Output key.** `axon-kafka: none | accept-stays-af4 | pause-migration | remove-feature-first`

**Effect.** Any non-`none` → `result: blocked`, exit. No edits. Learnings: *"User accepts axon-kafka has no AF5 path; Kafka slice is the user's responsibility, out-of-band."*

---

## B8 — `MongoEventStorageEngine` (no AF5 release of `axon-mongo`)

**Used by:** `event-storage-engine`.

**Why blocker.** No AF5 release. No AF5 equivalent. Mongo conflicts directly with AF5 storage paths.

**Detection.**
```bash
grep -RnE 'MongoEventStorageEngine|org\.axonframework\.extensions\.mongo|axon-mongo' \
     --include='*.java' --include='*.kt' --include='pom.xml' --include='*.gradle*' .
```

**AskUserQuestion.**
- `move-to-axon-server` — **code rewrite only.** User MUST run Mongo→AS data migration out-of-band BEFORE deploying AF5 build.
- `move-to-jpa` — **code rewrite only.** User owns AF5 JPA schema change AND Mongo→relational data move, out-of-band. Recipe emits NO SQL.
- `pause-migration` — user replaces Mongo with supported store (incl. data) before resuming.
- `accept-stays-af4` — event-store slice stays AF4; recipe exits.

**Output key.** `mongo-event-store: none | move-to-axon-server | move-to-jpa | pause-migration | accept-stays-af4`

**Effect.**
- `move-to-axon-server` → backend = `axon-server`. Learnings: *"User accepts Mongo→Axon Server data migration is out-of-band."*
- `move-to-jpa` → backend = `jpa`. Learnings: *"User accepts Mongo→relational data move AND AF5 JPA schema change are out-of-band."*
- others → `result: blocked`, exit.

---

## B9 — `JdbcEventStorageEngine` (no AF5 drop-in)

**Used by:** `event-storage-engine`.

**Why blocker.** No AF5 `JdbcEventStorageEngine` yet. Don't write a custom AF5 JDBC engine inside a migration run.

**Detection.**
```bash
grep -RnE 'JdbcEventStorageEngine' --include='*.java' --include='*.kt' src
```

**AskUserQuestion.**
- `move-to-jpa` — code rewrite only; user owns AF5 schema change out-of-band.
- `move-to-axon-server` — code rewrite only; user runs JDBC→AS data migration out-of-band.
- `defer-until-af5-jdbc` — stop; wait for AF5 JDBC equivalent.

**Output key.** `jdbc-event-store: none | move-to-jpa | move-to-axon-server | defer-until-af5-jdbc`

**Effect.**
- `move-to-jpa` / `move-to-axon-server` → backend per pick.
- `defer-until-af5-jdbc` → `result: blocked`, exit.

---

## B10 — Custom `EventStorageEngine` subclass + custom `Serializer`

**Used by:** `event-storage-engine`.

**Why blocker.** Project subclasses `EventStorageEngine` for custom storage / encryption / multitenancy. Reimplementation on `AggregateBased*` is out of scope. Custom `Serializer` (subclassed, custom `RevisionResolver`, custom `ContentTypeConverter`) is a soft blocker — Jackson/XStream defaults port automatically, custom ones don't.

**Detection.**
```bash
grep -RnE 'extends\s+(JpaEventStorageEngine|JdbcEventStorageEngine|MongoEventStorageEngine|AbstractEventStorageEngine|BatchingEventStorageEngine|AxonServerEventStore)\b' \
     --include='*.java' --include='*.kt' src
```

Plus inspection for custom `@Bean Serializer` / `XStreamSerializer` subclass / `JacksonSerializer` subclass / `RevisionResolver` / `ContentTypeConverter`.

**AskUserQuestion (subclass).**
- `surface-and-defer` *(Recommended)* — follow-up issue; recipe exits.
- `pause-migration` — user removes subclass first.

**Output key.**
- Subclass: `custom-storage-engine-subclass: none | surface-and-defer | pause-migration`
- Soft serializer: `serializer-ports-flagged: [<FQN list>] | none`

**Effect.** Subclass blocker → `result: blocked`, exit. Soft serializer → continue but record in `notes` for `learnings.md`.
