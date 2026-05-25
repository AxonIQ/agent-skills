# Java reference sources

Static reference copies of representative classes from the Heroes example app, in their AF4 and AF5 shapes side by side. **Not compiled, not maintained against upstream** — read these alongside the markdown patterns to see the full shape of migrated code.

Source: `.knowledge/repositories/axon-examples/{axon4,axon5}/heroes/`.

## What each file demonstrates

- `armies/write/Army.java` — Aggregate root: state-stored `@Aggregate` (AF4) vs `EventSourcedEntity` + `@EntityCreator` / `@EventSourcingHandler` + decider-style command handlers (AF5).
- `armies/write/ArmyCommand.java` — Sealed command interface with nested records.
- `armies/events/ArmyEvent.java` — Sealed event interface with nested records (AF4 `@Revision` vs AF5 `@EventTag` / converter wiring).
- `creaturerecruitment/read/DwellingReadModelProjector.java` — Projector / read model: AF4 `@ProcessingGroup` + `@EventHandler` vs AF5 event-handling component.
- `creaturerecruitment/write/builddwelling/BuildDwellingRestApi.java` — REST controller: AF4 `CommandGateway.sendAndWait` vs AF5 `CommandGateway.sendAndWait(..., context)` / message-name wiring.
- `armies/write/ArmyTest.java` — Aggregate test: AF4 `AggregateTestFixture` vs AF5 `AxonTestFixture` / decider-style assertions.

## AF4 ↔ AF5 pairs

| AF4 path | AF5 path |
|---|---|
| `af4/src/main/java/com/dddheroes/heroesofddd/armies/write/Army.java` | `af5/src/main/java/com/dddheroes/heroesofddd/armies/write/Army.java` |
| `af4/src/main/java/com/dddheroes/heroesofddd/armies/write/ArmyCommand.java` | `af5/src/main/java/com/dddheroes/heroesofddd/armies/write/ArmyCommand.java` |
| `af4/src/main/java/com/dddheroes/heroesofddd/armies/events/ArmyEvent.java` | `af5/src/main/java/com/dddheroes/heroesofddd/armies/events/ArmyEvent.java` |
| `af4/src/main/java/com/dddheroes/heroesofddd/creaturerecruitment/read/DwellingReadModelProjector.java` | `af5/src/main/java/com/dddheroes/heroesofddd/creaturerecruitment/read/DwellingReadModelProjector.java` |
| `af4/src/main/java/com/dddheroes/heroesofddd/creaturerecruitment/write/builddwelling/BuildDwellingRestApi.java` | `af5/src/main/java/com/dddheroes/heroesofddd/creaturerecruitment/write/builddwelling/BuildDwellingRestApi.java` |
| `af4/src/test/java/com/dddheroes/heroesofddd/armies/write/ArmyTest.java` | `af5/src/test/java/com/dddheroes/heroesofddd/armies/write/ArmyTest.java` |
