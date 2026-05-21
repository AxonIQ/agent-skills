---
name: axon4to5-migrate
description: >-
  Migrate Axon Framework 4 project to Axon(iq) Framework 5. Handles Spring Boot and native configurations.
  Covers aggregates, event handlers, sagas, query handlers, interceptors, event store, and tests.
argument-hint: "[project-path] [configuration=spring|native] [skip-openrewrite=true|false]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# axon4to5-migrate

## Goal

Fully (or as far as possible) compiling, green-test codebase on AF5, **same architecture as AF4**.
No DCB. No new patterns. Legacy event storage preserved.

---

## Step 1: Gather inputs

Ask the user the following questions using `AskUserQuestion`:

**Q1 — Project root path**
What is the path to the project root? (Default: current working directory)

**Q2 — Configuration style**
How does the application wire Axon?
- **spring** — Spring Boot auto-configuration (`@Aggregate`, `@Component`, `@Bean` idioms)
- **native** — Direct `Configurer` / `EventSourcingConfigurer` API

**Q3 — Migration approach**
Choose an approach:
- **A — OpenRewrite + AI (recommended)**: Run the OpenRewrite bulk recipe first (handles ~60% of mechanical renames automatically), then the AI handles remaining semantic changes.
- **B — AI only**: Skip OpenRewrite; the AI applies all patterns directly. Use when Maven/Gradle is not available or OpenRewrite has already run.
- **C — Assessment only**: Scan and report what needs migration, estimate effort, make no changes.

**Q4 — Skip specific components** (optional)
Are there component types to skip? (aggregates / event-handlers / query-handlers / interceptors / sagas / event-store / tests / none)

---

## Step 2: Assessment

**BEFORE reading any code**, load the pattern catalog:

```
Read: patterns/ALL_IN_ONE.md
```

Then scan the project to classify what needs migrating. For each category below, grep the source tree and
report findings in a table:

```bash
# Aggregates
grep -rln '@Aggregate\|@AggregateRoot' --include='*.java' --include='*.kt' --include='*.scala' <root>/src/

# Event handlers / processors
grep -rln '@ProcessingGroup\|@EventHandler' --include='*.java' --include='*.kt' --include='*.scala' <root>/src/

# Query handlers
grep -rln '@QueryHandler' --include='*.java' --include='*.kt' --include='*.scala' <root>/src/

# Interceptors
grep -rln 'implements MessageHandlerInterceptor' --include='*.java' --include='*.kt' --include='*.scala' <root>/src/

# Sagas
grep -rln '@Saga\|@SagaEventHandler' --include='*.java' --include='*.kt' --include='*.scala' <root>/src/

# Tests
grep -rln 'AggregateTestFixture' --include='*.java' --include='*.kt' --include='*.scala' <root>/src/

# Dependencies
grep -rn 'org.axonframework' --include='pom.xml' --include='build.gradle' --include='build.gradle.kts' <root>/

# YAML config
grep -rn 'axon.serializer\|sequencing-policy' --include='*.yaml' --include='*.properties' <root>/
```

Output a classification table:

```
| Category        | Files found | Complexity | Notes                    |
|-----------------|-------------|------------|--------------------------|
| Aggregates      | N           | Low/Med    | e.g. N with CommandHandler|
| Event handlers  | N           | Med        |                          |
| Query handlers  | N           | Low        |                          |
| Interceptors    | N           | High       | e.g. uses UnitOfWork     |
| Sagas           | N           | High       | e.g. uses SagaLifecycle  |
| Event store     | ✓/✗         | Low        | explicit config needed?  |
| Tests           | N           | Med        |                          |
| Dependencies    | pom.xml     | Low        |                          |
```

Ask: **"Proceed with migration (Approach A/B/C)?"** — or stop here if approach=C.

---

## Step 3: Execute migration

**Approach A — OpenRewrite + AI**

1. Invoke `axon4to5-openrewrite` skill to run the bulk recipe.
2. After OpenRewrite completes, proceed to the AI migration phases below.

**Approach B — AI only**

Skip to the AI migration phases below.

---

### AI Migration Phases

Execute the phases in this order. For each phase:
1. Find applicable files using grep (already identified in assessment).
2. Read each file.
3. Apply the relevant patterns from `patterns/ALL_IN_ONE.md`.
4. Verify the change compiles (or note why it cannot be verified yet).

---

#### Phase 1: Dependencies (pom.xml / build.gradle)

Patterns: **10. Dependencies → Maven/Gradle Migration**

For each `pom.xml` or `build.gradle`:
1. Update group ID and artifact IDs per the import mappings.
2. Rename `axon.serializer.*` → `axon.converter.*` in `application.yaml` / `application.properties`.
3. Remove `console-framework-client-spring-boot-starter` if present.

---

#### Phase 2: Event Classes

Patterns: **20. Aggregates → Event Class Annotations**

For each event record/class:
1. Add `@Event` annotation.
2. Add `@EventTag(key = "<AggregateTagKey>")` to the routing field — the key must match the aggregate's `tagKey`.
3. Replace `@Revision("N")` with `@Event(version = N)`.

---

#### Phase 3: Aggregates

Patterns: **20. Aggregates → all patterns**

For each aggregate class:
1. Replace `@Aggregate`/`@AggregateRoot` → `@EventSourced(tagKey = "…", idType = …)`.
2. Remove `@AggregateIdentifier` from the field.
3. Add `@EntityCreator` to the no-arg constructor.
4. Add `EventAppender eventAppender` as last parameter to every `@CommandHandler`.
5. Replace `AggregateLifecycle.apply(…)` → `eventAppender.append(…)`.
6. Update `@CommandHandler` import: `commandhandling.CommandHandler` → `messaging.commandhandling.annotation.CommandHandler`.
7. Update `@EventSourcingHandler` import: `eventsourcing.EventSourcingHandler` → `eventsourcing.annotation.EventSourcingHandler`.

**Verification checklist per aggregate:**
- `grep '@EventSourced' file` — has `tagKey` and `idType` attributes
- `grep 'AggregateLifecycle' file` — no matches
- `grep 'EventAppender' file` — one occurrence per `@CommandHandler`
- `grep '@EntityCreator' file` — present on no-arg constructor

---

#### Phase 4: Event Handlers / Processors

Patterns: **30. Event Handlers → all patterns**

For each event-handling class (projectors, automation processors):
1. Replace `@ProcessingGroup("name")` → `@Namespace("name")`.
2. Update `@EventHandler` import.
3. Update `@DisallowReplay` import.
4. Replace `@MetaDataValue` → `@MetadataValue` (both annotation name and import).
5. If class has `CommandGateway` field:
   - Remove the field and constructor injection.
   - Add `CommandDispatcher commandDispatcher` as method parameter to each `@EventHandler` that dispatches.
   - Change handler return type to `CompletableFuture<?>`.
   - Replace `commandGateway.sendAndWait(cmd, meta)` → `commandDispatcher.send(cmd, meta).getResultMessage()`.
6. If class has `sequencing-policy` in YAML or `@Bean SequencingPolicy`:
   - Add `@SequencingPolicy(type = MetadataSequencingPolicy.class, parameters = "metadataKey")` to the class.
   - Remove the YAML `sequencing-policy` key for this processor.

**Verify external namespace references:**
```bash
grep -rn '"<namespace-name>"' --include='*.yaml' --include='*.java' --include='*.kt' .
```

---

#### Phase 5: Query Handlers

Patterns: **40. Query Handlers**

For each query-handler class:
1. Update `@QueryHandler` import: `queryhandling.QueryHandler` → `messaging.queryhandling.annotation.QueryHandler`.
2. If class has `@ProcessingGroup`, apply namespace-routing pattern.
3. If class has `@MetaDataValue`, apply metadata-value pattern.

---

#### Phase 6: Interceptors

Patterns: **50. Interceptors**

For each `MessageHandlerInterceptor` implementation:
1. Update the interface generic: `CommandMessage<?>` → `CommandMessage`.
2. Rename method `handle(…)` → `interceptOnHandle(…)`.
3. Change parameters: `UnitOfWork<…> uow, InterceptorChain chain` → `CommandMessage message, ProcessingContext context, MessageHandlerInterceptorChain<CommandMessage> chain`.
4. Change return type: `Object` → `MessageStream<?>`.
5. Change chain call: `chain.proceed()` → `chain.proceed(message, context)`.
6. Change message access: `uow.getMessage()` → `message` (direct).
7. Update `getMetaData()` → `metaData()`, `getPayload()` → `payload()`.
8. Remove `throws Exception`.
9. Update imports — add `MessageHandlerInterceptorChain`, `MessageStream`, `ProcessingContext`; remove `UnitOfWork`, `InterceptorChain`.
10. If body uses `Repository.loadOrCreate(…).execute(…)`:
    - Replace with `CommandDispatcher.forContext(context).send(cmd).resultAs(Void.class).join()`.

---

#### Phase 7: Sagas

Patterns: **60. Sagas**

For each saga class:
1. Remove `@Saga` annotation (both Spring and SPI variants).
2. Add `@Component`, `@DisallowReplay`, `@Entity`, `@Table` annotations.
3. Add `@Id` field for the correlation key.
4. Add `protected` no-arg constructor for JPA.
5. Replace `@SagaEventHandler(associationProperty = …)` → `@EventHandler`.
6. Remove `@StartSaga`, `@EndSaga` annotations.
7. Remove all `SagaLifecycle.*` calls.
8. If saga dispatches commands via `CommandGateway` field → apply command-dispatcher pattern.
9. Add persistence logic: load/save via a Spring Data repository.

**If `@DeadlineHandler` is used** — this is a blocker; no AF5 equivalent exists. Comment out and note.

---

#### Phase 8: Event Store Configuration

Patterns: **70. Event Store**

If the project uses JPA (no Axon Server):
1. Create `EventStoreConfiguration.java` with `AggregateBasedJpaEventStorageEngine` bean.
2. Add `@EntityScan` with `org.axonframework` and `io.axoniq.framework` packages.
3. Add `@ConditionalOnProperty(name = "axon.axonserver.enabled", havingValue = "false")`.
4. Set `axon.axonserver.enabled: false` in `application.yaml`.

---

#### Phase 9: Tests

Patterns: **80. Tests**

For each test class using `AggregateTestFixture`:
1. Replace `AggregateTestFixture<T> fixture` → `AxonTestFixture fixture` (no type param).
2. Replace `new AggregateTestFixture<>(Aggregate.class)` →
   ```java
   AxonTestFixture.with(
       EventSourcingConfigurer.create()
           .registerEntity(EventSourcedEntityModule.autodetected(AggId.class, Aggregate.class))
   )
   ```
3. Add `@AfterEach void tearDown() { fixture.stop(); }`.
4. Update DSL: `given(events)` → `given().events(events)`, `when(cmd)` → `when().command(cmd)`, `expectEvents(…)` → `then().events(…)`.
5. Update exception assertions: `AggregateNotFoundException.class` → the domain exception.

---

## Step 4: Validate

After all phases complete, run validation:

**1. Compile check**

```bash
# Maven
mvn compile -q 2>&1 | head -100

# Gradle
./gradlew classes 2>&1 | head -100
```

If errors remain:
- Search errors for AF4 class names — apply remaining patterns from `ALL_IN_ONE.md`.
- Common missed patterns:
  - `getPayload()` / `getMetaData()` → `payload()` / `metaData()` (message-accessors)
  - Remaining `org.axonframework.config.ProcessingGroup` imports
  - `org.axonframework.commandhandling.CommandHandler` (non-aggregate classes)

**2. Scan for remaining AF4 symbols**

```bash
grep -rn 'org.axonframework.spring.stereotype.Aggregate\|AggregateLifecycle\|@ProcessingGroup\|CommandGateway\|AggregateTestFixture\|SagaEventHandler\|@Saga\b\|axon.serializer' \
  --include='*.java' --include='*.kt' --include='*.scala' --include='*.yaml' <root>/src/
```

Any match is an incomplete migration — apply the relevant pattern.

**3. Test check** (optional, after compile is green)

```bash
mvn test -pl <module>   # or ./gradlew test
```

**4. Report results**

```
✅ Migration complete

| Phase              | Status      | Notes                        |
|--------------------|-------------|------------------------------|
| Dependencies       | ✅          |                              |
| Event classes      | ✅          |                              |
| Aggregates         | ✅ (N files)|                              |
| Event handlers     | ✅ (N files)|                              |
| Query handlers     | ✅ (N files)|                              |
| Interceptors       | ✅ (N files)|                              |
| Sagas              | ⏭ skipped  | No sagas found               |
| Event store        | ✅          |                              |
| Tests              | ✅ (N files)|                              |

Compilation: ✅ green / ⚠️ N error(s) remain — see notes
```

---

## Behavior rules

- **Always load `patterns/ALL_IN_ONE.md` before touching any code** — it contains all import mappings and
  before/after examples for every migration pattern.
- Work through phases **in order** — aggregates define the events and commands consumed by downstream handlers.
- Apply patterns **one file at a time** and verify imports are correct after each edit.
- **Preserve architecture** — no DCB, no event storage engine swap, no new patterns.
- When uncertain about a package path, grep the local AF5 jars or consult `references/atoms/` for the definitive
  import path.
- For deep per-component details (use-cases, blockers, edge cases), consult the relevant
  `references/recipes/<component>/RECIPE.md` and `references/atoms/` files.

---

## Advanced usage — single component

To migrate a single component instead of the whole project:

```
axon4to5-migrate configuration=spring mode=single source=com.example.Army
```

The skill matches the source class to a recipe in `references/recipes/`, then executes the recipe sub-flow
per `references/recipes/FLOW.md`. Load `FLOW.md` and the recipe's `RECIPE.md` for detailed orchestration.

---

## Expanding the skill

To add a new migration pattern:
1. Create `patterns/<NN-category>/<pattern-name>.md` following the format in existing files.
2. Add an entry to `patterns/ALL_IN_ONE.md` under the relevant section.
3. Add a corresponding atom to `references/atoms/` if it is a single API change used by multiple recipes.
4. Reference the atom in the relevant `references/recipes/<component>/RECIPE.md` under `# Atoms`.
