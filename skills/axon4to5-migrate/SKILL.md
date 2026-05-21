---
name: axon4to5-migrate
description: >-
  Migrate Axon Framework 4 project to Axon(iq) Framework 5. Handles Spring Boot and native configurations.
  Covers aggregates, event handlers, sagas, query handlers, interceptors, event store, and tests.
argument-hint: "[project-path] [configuration=spring|native] [skip-openrewrite=true|false]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# Axon Framework 4 → 5 Migration

## Step 1: Gather inputs

Use `AskUserQuestion` for each question below.

**Q1 — Project root path**
What is the path to the project root? (Default: current working directory)

**Q2 — Configuration style**
How does the application wire Axon?
- **spring** — Spring Boot auto-configuration (`@Aggregate`, `@Component`, `@Bean` idioms)
- **native** — Direct `Configurer` / `EventSourcingConfigurer` API

**Q3 — Migration approach**
- **A — OpenRewrite + AI (recommended)**: Run the OpenRewrite bulk recipe first (~60% of mechanical renames), then AI handles remaining semantic changes.
- **B — AI only**: Skip OpenRewrite; AI applies all patterns directly.
- **C — Assessment only**: Scan and report what needs migration, estimate effort, make no changes.

---

## Step 2: Assessment

Scan the codebase and classify what needs migrating.

**Detection hints:**
- `@Aggregate` / `@AggregateRoot` → aggregate class
- `@ProcessingGroup` / `@EventHandler` → event handler / projector
- `@QueryHandler` → query handler
- `implements MessageHandlerInterceptor` → interceptor
- `@Saga` / `@SagaEventHandler` → saga
- `AggregateTestFixture` → test code
- `org.axonframework` in `pom.xml` / `build.gradle` → dependency block
- `axon.serializer` in YAML → config key to rename

```bash
grep -rln '@Aggregate\|@AggregateRoot' --include='*.java' --include='*.kt' --include='*.scala' <root>/src/
grep -rln '@ProcessingGroup\|@EventHandler' --include='*.java' --include='*.kt' --include='*.scala' <root>/src/
grep -rln '@QueryHandler' --include='*.java' --include='*.kt' --include='*.scala' <root>/src/
grep -rln 'implements MessageHandlerInterceptor' --include='*.java' --include='*.kt' --include='*.scala' <root>/src/
grep -rln '@Saga\|@SagaEventHandler' --include='*.java' --include='*.kt' --include='*.scala' <root>/src/
grep -rln 'AggregateTestFixture' --include='*.java' --include='*.kt' --include='*.scala' <root>/src/
grep -rn 'org.axonframework' --include='pom.xml' --include='build.gradle' --include='build.gradle.kts' <root>/
grep -rn 'axon.serializer\|@DeadlineHandler\|SagaTestFixture' --include='*.yaml' --include='*.properties' --include='*.java' --include='*.kt' <root>/src/
```

Output a classification table:

```
| Category        | Files found | Complexity | Notes                    |
|-----------------|-------------|------------|--------------------------|
| Aggregates      | N           | Low/Med    |                          |
| Event handlers  | N           | Med        |                          |
| Query handlers  | N           | Low        |                          |
| Interceptors    | N           | High       |                          |
| Sagas           | N           | High       |                          |
| Event store     | ✓/✗         | Low        |                          |
| Tests           | N           | Med        |                          |
| Dependencies    | pom.xml     | Low        |                          |
```

**Blockers to flag before starting:**
- `@DeadlineHandler` found → no AF5 equivalent; those handlers must be commented out
- `SagaTestFixture` found → no AF5 replacement; those tests cannot be automatically migrated
- `snapshotTriggerDefinition` on `@Aggregate` → no AF5 equivalent; requires manual redesign

Use `AskUserQuestion` to confirm before proceeding (or stop here if approach C).

---

## Step 3: Execute migration

### Approach A — OpenRewrite + AI

1. Run the `axon4to5-openrewrite` skill to execute the bulk recipe.
2. After OpenRewrite completes, proceed to the AI phases below.

### Approach B — AI only

**Before touching any code**, load the pattern catalog:

```
Read: patterns/ALL_IN_ONE.md
```

Then execute the phases in order.

---

### Phase 1: Dependencies

Pattern: **10. Dependencies → Maven/Gradle Migration**

1. Update group ID: `org.axonframework` → `io.axoniq.framework`.
2. Update artifact IDs per the import mappings in the pattern.
3. Rename YAML keys: `axon.serializer.*` → `axon.converter.*`.
4. Remove `console-framework-client-spring-boot-starter` if present.

---

### Phase 2: Event Classes

Pattern: **20. Aggregates → Event Class Annotations**

For each event record/class used as an AF5 event:
1. Add `@Event` annotation (`org.axonframework.messaging.eventhandling.annotation.Event`).
2. Add `@EventTag(key = "<tagKey>")` to the routing field — key must match the aggregate's `tagKey`.
3. Replace `@Revision("N")` with `@Event(version = N)`.

---

### Phase 3: Aggregates

Patterns: **20. Aggregates → all**

For each aggregate class:
1. Replace `@Aggregate`/`@AggregateRoot` → `@EventSourced(tagKey = "…", idType = …)` (Spring) or `@EventSourcedEntity(…)` (native).
2. Remove `@AggregateIdentifier` from the identity field.
3. Add `@EntityCreator` to the no-arg constructor.
4. Remove `@TargetAggregateIdentifier` from all command classes that target this aggregate.
5. Add `EventAppender eventAppender` as the **last** parameter to every `@CommandHandler` method.
6. Replace every `AggregateLifecycle.apply(event)` → `eventAppender.append(event)`.
7. Update `@CommandHandler` import: `commandhandling.CommandHandler` → `messaging.commandhandling.annotation.CommandHandler`.
8. Update `@EventSourcingHandler` import: `eventsourcing.EventSourcingHandler` → `eventsourcing.annotation.EventSourcingHandler`.

**Blocker:** if `@Aggregate` carried `snapshotTriggerDefinition`, there is no AF5 equivalent — comment it out and note it for the user.

---

### Phase 4: Event Handlers / Processors

Patterns: **30. Event Handlers → all**

For each event-handling class:
1. Replace `@ProcessingGroup("name")` → `@Namespace("name")`.
2. Update `@EventHandler`, `@DisallowReplay`, `@ResetHandler` imports.
3. Replace `@MetaDataValue` → `@MetadataValue` (annotation name + import).
4. Replace `MetaData` type references → `Metadata` (`org.axonframework.messaging.core.Metadata`).
5. If class injects `CommandGateway` as a field:
   - Remove the field and its constructor injection.
   - Add `CommandDispatcher commandDispatcher` as a parameter to each `@EventHandler` that dispatches.
   - Change handler return type to `CompletableFuture<?>`.
   - Replace `commandGateway.sendAndWait(cmd)` → `commandDispatcher.send(cmd).getResultMessage()`.
6. If `sequencing-policy` exists in YAML or as a `@Bean`:
   - Add `@SequencingPolicy(type = MetadataSequencingPolicy.class, parameters = "metadataKey")` to the class.
   - Remove the YAML `sequencing-policy` key for this processor.

---

### Phase 5: Query Handlers

Pattern: **40. Query Handlers**

For each query-handler class:
1. Update `@QueryHandler` import: `queryhandling.QueryHandler` → `messaging.queryhandling.annotation.QueryHandler`.
2. If class has `@ProcessingGroup`, replace with `@Namespace` (same as Phase 4 step 1).
3. If class has `@MetaDataValue`, apply Phase 4 step 3.

---

### Phase 6: Interceptors

Pattern: **50. Interceptors**

For each `MessageHandlerInterceptor` implementation:
1. Update the interface generic: `CommandMessage<?>` → `CommandMessage`.
2. Rename method `handle(…)` → `interceptOnHandle(…)`.
3. New parameters: `CommandMessage message, ProcessingContext context, MessageHandlerInterceptorChain<CommandMessage> chain`.
4. Change return type: `Object` → `MessageStream<?>`.
5. Change chain call: `chain.proceed()` → `chain.proceed(message, context)`.
6. Replace `uow.getMessage()` → `message` (direct access).
7. Replace `getMetaData()` → `metaData()`, `getPayload()` → `payload()`.
8. Remove `throws Exception`.
9. Update imports: add `MessageHandlerInterceptorChain`, `MessageStream`, `ProcessingContext`; remove `UnitOfWork`, `InterceptorChain`.

---

### Phase 7: Sagas

Pattern: **60. Sagas**

For each saga class:
1. Remove `@Saga` annotation (both Spring and SPI variants).
2. Add `@Component`, `@DisallowReplay`, `@Entity`, `@Table` annotations.
3. Add `@Id` field for the correlation key.
4. Add `protected` no-arg constructor for JPA.
5. Replace `@SagaEventHandler(associationProperty = …)` → `@EventHandler`.
6. Remove `@StartSaga`, `@EndSaga`, all `SagaLifecycle.*` calls.
7. If the saga dispatches commands via `CommandGateway` field → apply Phase 4 step 5.
8. Add persistence: load/save via a Spring Data repository in each `@EventHandler`.

**Blocker:** if `@DeadlineHandler` is used — no AF5 equivalent exists. Comment out those methods and add a `// TODO: no AF5 DeadlineHandler — redesign required` note.

---

### Phase 8: Event Store Configuration

Pattern: **70. Event Store**

If the project uses JPA (no Axon Server):
1. Create `EventStoreConfiguration.java` with `AggregateBasedJpaEventStorageEngine` bean.
2. Add `@EntityScan` with `org.axonframework` and `io.axoniq.framework` packages.
3. Set `axon.axonserver.enabled: false` in `application.yaml`.

---

### Phase 9: Tests

Pattern: **80. Tests**

For each test using `AggregateTestFixture`:
1. Replace `AggregateTestFixture<T> fixture` → `AxonTestFixture fixture`.
2. Replace constructor: `new AggregateTestFixture<>(Aggregate.class)` →
   ```java
   AxonTestFixture.with(
       EventSourcingConfigurer.create()
           .registerEntity(EventSourcedEntityModule.autodetected(AggId.class, Aggregate.class))
   )
   ```
3. Add `@AfterEach void tearDown() { fixture.stop(); }`.
4. Update DSL: `given(events)` → `given().events(events)`, `when(cmd)` → `when().command(cmd)`, `expectEvents(…)` → `then().events(…)`.
5. Replace `AggregateNotFoundException.class` with the domain exception thrown from validation on empty state.

**Blocker:** `SagaTestFixture` — no AF5 replacement exists. Comment out those tests and note them for the user.

---

## Step 4: Validate

**1. Compile check**

```bash
# Maven
mvn compile -q 2>&1 | head -100

# Gradle
./gradlew classes 2>&1 | head -100
```

**2. Scan for remaining AF4 symbols**

```bash
grep -rn \
  'org.axonframework.spring.stereotype.Aggregate\|AggregateLifecycle\|@ProcessingGroup\|@TargetAggregateIdentifier\|CommandGateway\|AggregateTestFixture\|SagaEventHandler\|@Saga\b\|axon.serializer\|MetaData\b\|GenericDomainEventMessage' \
  --include='*.java' --include='*.kt' --include='*.scala' --include='*.yaml' <root>/src/
```

Any match is an incomplete migration — apply the relevant pattern from `ALL_IN_ONE.md`.

**3. Test check**

```bash
mvn test -pl <module>   # or ./gradlew test
```

**4. Summary**

```
| Phase              | Status      | Notes                        |
|--------------------|-------------|------------------------------|
| Dependencies       | ✅ / ❌     |                              |
| Event classes      | ✅ / ❌     |                              |
| Aggregates         | ✅ (N files)|                              |
| Event handlers     | ✅ (N files)|                              |
| Query handlers     | ✅ (N files)|                              |
| Interceptors       | ✅ (N files)|                              |
| Sagas              | ✅ / ⏭ / 🚧|                              |
| Event store        | ✅ / ⏭     |                              |
| Tests              | ✅ (N files)|                              |

Compilation: ✅ green / ⚠️ N error(s) remain
Blockers:    none / ⚠️ list here
```

---

## Behavior rules

- **Always load `patterns/ALL_IN_ONE.md` before touching any code** — it contains all import mappings and before/after examples.
- **For complex scenarios** (multi-entity aggregates, polymorphic hierarchies, saga persistence, named queries, dispatch interceptors), load `examples/ALL_EXAMPLES.md` for complete before/after file walkthroughs.
- **Work through phases in order** — aggregates define events consumed by downstream handlers.
- **Apply patterns one file at a time** and verify imports after each edit.
- **Flag blockers — never silently skip.** If a pattern has no AF5 equivalent (DeadlineHandler, SagaTestFixture, snapshotTriggerDefinition), comment out the code, add a `// TODO` note, and report it in the summary.
- **Preserve architecture** — no DCB, no event storage engine swap, no new patterns.
- **Do not auto-fix ambiguous cases.** When a compile error doesn't match a catalog pattern directly, ask the user before guessing.
