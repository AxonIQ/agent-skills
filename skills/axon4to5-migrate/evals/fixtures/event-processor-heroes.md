# Eval fixture — `event-processor` on `WhenCreatureRecruitedThenAddToArmyProcessor`

**AF4:** `axon4/heroes/.../creaturerecruitment/automation/WhenCreatureRecruitedThenAddToArmyProcessor.java`
**AF5:** `axon5/heroes/.../creaturerecruitment/automation/WhenCreatureRecruitedThenAddToArmyProcessor.java`

Class is a `@Component` projector that listens to `CreatureRecruited` and dispatches `AddCreatureToArmy` (with `IncreaseAvailableCreatures` as compensation on failure).

## Trigger

```
/axon4to5-migrate src/main/java/com/dddheroes/heroesofddd/creaturerecruitment/automation/WhenCreatureRecruitedThenAddToArmyProcessor.java
```

## Must-haves

### Step 3 — `@ProcessingGroup` → `@Namespace`

- ✅ `@ProcessingGroup("Automation_WhenCreatureRecruitedThenAddToArmy_Processor")` replaced by `@Namespace("Automation_WhenCreatureRecruitedThenAddToArmy_Processor")` (same string).
- ✅ Import `org.axonframework.config.ProcessingGroup` removed.
- ✅ Import `org.axonframework.messaging.core.annotation.Namespace` added.

### Step 4 — sibling annotations

- ✅ `@EventHandler` import → `org.axonframework.messaging.eventhandling.annotation.EventHandler`.
- ✅ `@DisallowReplay` import → `org.axonframework.messaging.eventhandling.replay.annotation.DisallowReplay`.
- ✅ `@MetaDataValue` → `@MetadataValue` (capital D dropped); import → `org.axonframework.messaging.core.annotation.MetadataValue`.

### Step 5 — class-level `CommandGateway` → method-parameter `CommandDispatcher`

- ✅ `private final CommandGateway commandGateway;` field **removed**.
- ✅ Constructor (was sole-arg `CommandGateway`) **removed** — Spring uses default no-arg.
- ✅ Handler method signature has `CommandDispatcher commandDispatcher` added as a parameter.
- ✅ Import `org.axonframework.messaging.commandhandling.gateway.CommandDispatcher` added.
- ✅ Import `org.axonframework.commandhandling.gateway.CommandGateway` (AF4) removed.

### Step 6 — async dispatch

- ✅ `commandGateway.sendAndWait(command, …)` rewritten to use `commandDispatcher.send(command, …)`.
- ✅ Handler return type changed from `void` to `CompletableFuture<?>` (or `CompletableFuture<Message>` — both are acceptable; AF5 reference uses `CompletableFuture<?>` returned from `exceptionallyCompose`).
- ✅ Import `java.util.concurrent.CompletableFuture` added.
- ✅ NO blocking `.get()` / `.join()` introduced. The AF5 reference uses `.getResultMessage().thenApply(...)` + `.exceptionallyCompose(...)` to translate the AF4 `try/catch` compensation into a future chain.

### Step 7 — `@SequencingPolicy` (optional but in this AF5 reference)

The AF5 reference adds `@SequencingPolicy(type = MetadataSequencingPolicy.class, parameters = GameMetaData.GAME_ID_KEY)`. This corresponds to the AF4 `@Bean SequencingPolicy<EventMessage<?>>` reading the same metadata key in `GameConfiguration.java`.

- ✅ When the user pinned this processor's sequencing-policy migration: `@SequencingPolicy` annotation on the class with `type = MetadataSequencingPolicy.class` and `parameters = GameMetaData.GAME_ID_KEY`.
- ✅ Import `org.axonframework.messaging.core.annotation.SequencingPolicy` AND `org.axonframework.messaging.core.sequencing.MetadataSequencingPolicy` added.
- ✅ AF4 `@Bean SequencingPolicy<...>` source deleted inline from the matching `GameConfiguration` class (Step 7 sub-step 2). NOT left to drift.

## Anti-patterns

- ❌ `CommandGateway` kept as a class-level field (it MUST go for an in-handler dispatcher).
- ❌ `sendAndWait(...)` left in place (handler must return a future).
- ❌ Naked `.join()` / `.get()` introduced anywhere (must use `.getResultMessage()` chain).
- ❌ `@ProcessingGroup` and `@Namespace` mismatched strings (would silently drop the processor).
- ❌ Old `@MetaDataValue` import left alongside new `@MetadataValue` (rename, don't duplicate).
- ❌ Sequencing policy moved to class annotation but the AF4 `@Bean SequencingPolicy<...>` left in `GameConfiguration` (drift).

## Output contract

```yaml
result: success
target: com.dddheroes.heroesofddd.creaturerecruitment.automation.WhenCreatureRecruitedThenAddToArmyProcessor
decisions:
  path: A (Spring Boot)
  processing-group: Automation_WhenCreatureRecruitedThenAddToArmy_Processor
  event-handler-mode: tracking
  processor-definition-migrated: false   # this run doesn't touch Path 10 @Bean rewriting
  error-handler-folded: none
  dlq-sites-flagged: none
  mongo-token-store: none
  saga-handler-detected: none
  axon-kafka: none
caller-expects: { commit: true, next: proceed }
```
