# Eval fixture — `aggregate` on `Dwelling`

**AF4:** `.knowledge/repositories/axon-examples/axon4/heroes/src/main/java/com/dddheroes/heroesofddd/creaturerecruitment/write/Dwelling.java`
**AF5:** `.knowledge/repositories/axon-examples/axon5/heroes/src/main/java/com/dddheroes/heroesofddd/creaturerecruitment/write/Dwelling.java`

Aggregate test (also migrated): `.../write/DwellingTest.java`.

Events touched: `DwellingBuilt`, `AvailableCreaturesChanged`, `CreatureRecruited`. Commands touched: `BuildDwelling`, `IncreaseAvailableCreatures`, `RecruitCreature`.

## Trigger

```
/axon4to5-migrate src/main/java/com/dddheroes/heroesofddd/creaturerecruitment/write/Dwelling.java
```

Pinned decisions: `license = axoniq-commercial`, `wiring = spring-boot`, `build-tool = maven`.

## Must-haves (grep the AF5 output)

### Class-level rewrite

- ✅ Class is annotated `@EventSourced(tagKey = "Dwelling", idType = DwellingId.class)` (NOT `@EventSourcedEntity` — Path A).
- ✅ Import `org.axonframework.extension.spring.stereotype.EventSourced` is present.
- ✅ `@AggregateIdentifier` annotation **removed** from the id field (`dwellingId` stays as plain field).
- ✅ Imports removed: `org.axonframework.modelling.command.AggregateIdentifier`, `org.axonframework.modelling.command.AggregateCreationPolicy`, `org.axonframework.modelling.command.CreationPolicy`, `org.axonframework.spring.stereotype.Aggregate`.
- ✅ Static import `import static org.axonframework.modelling.command.AggregateLifecycle.*;` removed.
- ✅ No-arg constructor exists and is annotated `@EntityCreator` (or OpenRewrite has inserted one).

### Handler shape

- ✅ Every `@CommandHandler` method has an `EventAppender eventAppender` parameter added.
- ✅ `@CommandHandler` import is AF5: `org.axonframework.messaging.commandhandling.annotation.CommandHandler`.
- ✅ Every `AggregateLifecycle.apply(...)` rewritten to `eventAppender.append(...)`.
- ✅ Import `org.axonframework.messaging.eventhandling.gateway.EventAppender` present.
- ✅ `@CreationPolicy(CREATE_IF_MISSING)` annotation removed from instance `@CommandHandler` (semantics preserved by no-arg `@EntityCreator`).
- ✅ `@EventSourcingHandler` import moved to `org.axonframework.eventsourcing.annotation.EventSourcingHandler`.

### Events (in `creaturerecruitment/events/`)

- ✅ Each event carries `@Event` (`org.axonframework.messaging.eventhandling.annotation.Event`).
- ✅ The aggregate-id field on every event has `@EventTag(key = "Dwelling")` (or no `key` defaulting to the simple class name — explicit form is preferred).
- ✅ Import `org.axonframework.eventsourcing.annotation.EventTag` present.

### Commands (in `creaturerecruitment/write/<slice>/`)

- ✅ Each command class carries `@Command` (`org.axonframework.messaging.commandhandling.annotation.Command`).
- ✅ Field annotated `@TargetEntityId` (`org.axonframework.modelling.annotation.TargetEntityId`) — replaces AF4 `@TargetAggregateIdentifier`.
- ✅ AF4 `@TargetAggregateIdentifier` annotation + import are removed.

### Snapshotting blocker (B1)

- ✅ `Output.decisions.snapshotting` is one of `accept-drop | pause-migration | remove-feature-first`.
- ✅ If `accept-drop`: `snapshotTriggerDefinition` attribute is NOT present on `@EventSourced`. A `// TODO #LLM: reconfigure snapshot trigger …` marker is acceptable (OpenRewrite's parking comment) — the AF5 reference file has one.
- ✅ If user picks `pause-migration` / `remove-feature-first`: `result: blocked`, no rewrite, no `@EventSourced` annotation introduced.

## Anti-patterns

- ❌ `@EventSourcedEntity` used instead of `@EventSourced` on Path A.
- ❌ `@AggregateIdentifier` left in the file.
- ❌ Any `AggregateLifecycle.apply(...)` line remaining.
- ❌ `@CreationPolicy` / `AggregateCreationPolicy` imports remaining.
- ❌ Snapshotting silently dropped without recording in `Output.decisions.snapshotting` and `progress.md` Pinned-decisions.
- ❌ `tagKey` mismatched between `@EventSourced(tagKey = ...)` and `@EventTag(key = ...)` — the strings must agree (here both must be `"Dwelling"`).
- ❌ Multiple `@EntityCreator` constructors (OpenRewrite + recipe both inserted one).

## Output contract

```yaml
result: success                     # or blocked when snapshotting halts
target: com.dddheroes.heroesofddd.creaturerecruitment.write.Dwelling
decisions:
  path: A (Spring Boot)
  variant: simple
  creation-policy: NEVER            # AF4 had CREATE_IF_MISSING but instance-handler shape preserves it
  test-fixture: migrated            # if DwellingTest exists and is in scope
  snapshotting: accept-drop         # B1
  deadline-handler: none            # B5
caller-expects: { commit: true, next: proceed }
```
