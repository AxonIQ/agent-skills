# Recipe `event-storage-engine` — blockers

Run every Detection grep BEFORE `## Procedure`. For each hit: run the `AskUserQuestion`, record under `decisions.<key>`, apply "Effect". Never auto-rewrite a bean swap when a blocker is unresolved.

> 🚨 **DATA MIGRATION & SQL/DDL ARE NOT IN SCOPE.** Every `move-to-*` option is a **code-rewrite choice, not a data- or schema-migration offer**. If the user has not planned the schema/data move on a non-prod copy, do NOT pick a `move-to-*` option — `pause-migration` instead.

## B1 — `MongoEventStorageEngine` (no AF5 release of `axon-mongo`)

**Why.** No AF5 release. No AF5 equivalent. Mongo conflicts directly with AF5 paths — no Mongo Path D.

**Detection:**
```bash
grep -RnE 'MongoEventStorageEngine|org\.axonframework\.extensions\.mongo|axon-mongo' \
     --include='*.java' --include='*.kt' --include='pom.xml' --include='*.gradle*' .
```

**AskUserQuestion:**
- `move-to-axon-server` — **code rewrite only.** User MUST run Mongo→AS data migration out-of-band BEFORE deploying AF5 build.
- `move-to-jpa` — **code rewrite only.** User owns AF5 JPA schema change AND Mongo→relational data move, out-of-band. Recipe emits NO SQL.
- `pause-migration` — user replaces Mongo with supported store (incl. data) before resuming.
- `accept-stays-af4` — event-store slice stays AF4; recipe exits.

**Output key:** `mongo-event-store: none | move-to-axon-server | move-to-jpa | pause-migration | accept-stays-af4`.

**Effect:**
- `move-to-axon-server` → backend = `axon-server` (A.AS / B.AS). Learnings line: *"User accepts Mongo→Axon Server data migration is out-of-band."*
- `move-to-jpa` → backend = `jpa` (A.JPA / B.JPA). Learnings line: *"User accepts Mongo→relational data move AND AF5 JPA schema change are out-of-band."*
- others → `result: blocked`, `next: record-and-skip`, exit.

## B2 — `JdbcEventStorageEngine` (no AF5 drop-in)

**Why.** No AF5 `JdbcEventStorageEngine` yet. Don't write a custom AF5 JDBC engine inside a migration run.

**Detection:**
```bash
grep -RnE 'JdbcEventStorageEngine' --include='*.java' --include='*.kt' src
```

**AskUserQuestion:**
- `move-to-jpa` — code rewrite only; user owns AF5 schema change out-of-band.
- `move-to-axon-server` — code rewrite only; user runs JDBC→AS data migration out-of-band.
- `defer-until-af5-jdbc` — stop; wait for AF5 to ship a JDBC equivalent.

**Output key:** `jdbc-event-store: none | move-to-jpa | move-to-axon-server | defer-until-af5-jdbc`.

**Effect:**
- `move-to-jpa` / `move-to-axon-server` → backend per pick, sub-path per `inputs.wiring`.
- `defer-until-af5-jdbc` → `result: blocked`, `next: record-and-skip`, exit.

## B3 — Custom `EventStorageEngine` subclass

**Why.** Subclasses for custom storage / encryption / multitenancy. Reimplementation on `AggregateBased*` is out of scope.

**Detection:**
```bash
grep -RnE 'extends\s+(JpaEventStorageEngine|JdbcEventStorageEngine|MongoEventStorageEngine|AbstractEventStorageEngine|BatchingEventStorageEngine|AxonServerEventStore)\b' \
     --include='*.java' --include='*.kt' src
```

**AskUserQuestion:**
- `surface-and-defer` *(Recommended)* — follow-up issue; recipe exits.
- `pause-migration` — user removes subclass first.

**Output key:** `custom-storage-engine-subclass: none | surface-and-defer | pause-migration`.

**Effect:** Either path → `result: blocked`, `next: record-and-skip`, exit. No bean swap.

## B4 — Custom `Serializer` (soft blocker)

**Why.** AF5 replaces `Serializer` with `Converter` / `EventConverter`. Jackson/XStream defaults port automatically. Subclassed serializers / custom `RevisionResolver` / custom `ContentTypeConverter` do NOT.

**Detection:** during backend inspection — any `@Bean Serializer`, component-registry-bound `Serializer`, `XStreamSerializer` / `JacksonSerializer` subclass, custom `RevisionResolver`.

**Action:** Don't auto-port. Add to `decisions.serializer-ports-flagged: [<FQNs>]` for `learnings.md`.

**Output key:** `serializer-ports-flagged: [<class FQNs>] | none`.
