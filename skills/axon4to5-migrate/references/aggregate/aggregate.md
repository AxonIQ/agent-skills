# Recipe: Aggregate → `@EventSourced` / `@EventSourcedEntity`

Atomic migration of ONE aggregate class and its surrounding commands, events, child entities, and primary test class.

## Canonical reference

Read these BEFORE running the Procedure. They hold the conceptual model, the full before/after examples, and the rationale that this recipe does NOT repeat.

- [../../docs/paths/aggregates/index.adoc](../../docs/paths/aggregates/index.adoc) — `@EventSourcedEntity` / `@EventSourced`, `@EntityCreator` patterns, `EventAppender`, `@EventTag` semantics, removal of `@CreationPolicy`, simple GiftCard before/after.
- [../../docs/paths/messages.adoc](../../docs/paths/messages.adoc) — `@TargetEntityId`, `@Event(version=…)`, `@Command(routingKey=…)`.
- [../../docs/paths/aggregates/multi-entity-migration.adoc](../../docs/paths/aggregates/multi-entity-migration.adoc) — `@EntityMember`.
- [../../docs/paths/aggregates/polymorphism-migration.adoc](../../docs/paths/aggregates/polymorphism-migration.adoc) — `concreteTypes`.
- [../../docs/paths/aggregates/configuration-migration.adoc](../../docs/paths/aggregates/configuration-migration.adoc) — `EventSourcedEntityModule.autodetected(...)` registration.
- [../../docs/paths/test-fixtures.adoc](../../docs/paths/test-fixtures.adoc) — `AxonTestFixture`, fluent given/when/then mapping.
- [../../docs/paths/snapshotting.adoc](../../docs/paths/snapshotting.adoc) — AF5.1 snapshot model (only relevant to [not-supported.md](not-supported.md) B1 decision).
- [../../docs/paths/index.adoc](../../docs/paths/index.adoc) §"Import and package changes" — exhaustive FQN moves.

This recipe holds only the **mechanical** edits, the **scoped verify**, and AskUserQuestion blockers from [not-supported.md](not-supported.md).

## Goal

The aggregate (and its commands, events, and primary test class) compile and behave on AF5 APIs:
- `@Aggregate` (Spring) → `@EventSourced`; `@AggregateRoot` (core) → `@EventSourcedEntity`.
- Identity expressed via `@EventTag` on events + entity `tagKey` (no more `@AggregateIdentifier`).
- `AggregateLifecycle.apply(...)` → `EventAppender` parameter on `@CommandHandler`.
- `@CreationPolicy` → AF5 handler shape (static for ALWAYS, instance for CREATE_IF_MISSING / NEVER).
- `@AggregateMember` → `@EntityMember` (multi-entity addendum).
- `AggregateTestFixture` → `AxonTestFixture` with full fluent API mapping.

## Inputs

- target: FQ aggregate class name (required)
- target_test: FQ test class name (optional — auto-discovered as `<target>Test` if absent)
- wiring: "spring-boot" | "framework-config" (required, supplied by migration runner from progress.md Pinned-decisions)

## End condition (verify BEFORE declaring done)

1. **Aggregate test class passes** if it exists in AF4 using `AggregateTestFixture` — now using `AxonTestFixture`. Scoped run is delegated to the external `axon4to5-isolatedtest` skill (see [../verification.md](../verification.md)):
   ```
   Skill: axon4to5-isolatedtest
   Inputs:
     target-name: <AggregateSimpleName>
     build-file: <target>/pom.xml | <target>/build.gradle(.kts)
     main-sources: [<aggregate + command + event + child-entity files>]
     test-sources: [<FQTestClass>]
     extra-deps: [axon-modelling, axon-eventsourcing, axon-test]
     cleanup: false
   ```
2. **Zero compile errors** in: the aggregate class, all command classes handled here, all event classes handled here, all child entities reachable via `@EntityMember`, the primary test class.

If aggregate has NO test class, end condition is just (2). Skip T.1–T.5 below.

## Output

Emit exactly one fenced ```yaml block per the six-variant Output contract
([../output-contract.md](../output-contract.md)). Schema below shows the
`success` shape with all aggregate-specific `decisions` keys; for
`skipped` / `rejected` / `needs-decision` / `blocked` / `failed` shapes
copy the matching example from `output-contract.md` and keep the
aggregate-specific decision keys that apply.

```yaml
result: success | skipped | rejected | needs-decision | blocked | failed
target: <FQ aggregate class>
reason: <one short line — required for every variant except success>
decisions:
  path: <A (Spring Boot) | B (framework Configurer)>     # taken from inputs.wiring
  variant: <simple | multi-entity | polymorphic>
  creation-policy: <NEVER | ALWAYS-handled | ALWAYS-static-factory>
  test-fixture: <migrated | none>
  snapshotting: <none | accept-drop | pause-migration | remove-feature-first>             # B1
  configurer-registration: <auto-spring | added-explicit | surfaced-for-user>              # Path B only
  map-typed-aggregate-member: <none | surface-and-defer | pause-migration>                 # B3
  saga-test-fixture-flagged: <none | surface-and-skip-test | pause-migration>              # B4
  deadline-handler: <none | accept-stays-af4 | pause-migration | remove-feature-first>     # B5
caller-expects:
  commit: <true | false>
  next: <proceed | ask-user | record-and-skip | halt | route-to:<recipe>>
notes: <optional free text — verbatim AskUserQuestion options for needs-decision>
```

Blocker keys (`B1` / `B3` / `B4` / `B5`) map to `result: blocked` or
`result: needs-decision` per [not-supported.md](not-supported.md).

## Preflight (ALWAYS run first)

Maybe the job is already done — don't waste context.

1. **Read [not-supported.md](not-supported.md) first** — run every Detection grep listed there against the candidate aggregate, its events, child entities, and the configuration referencing it. If any blocker fires, follow that file's `AskUserQuestion` flow and apply its "Effect on Procedure" before doing anything else. Recipe must NOT proceed past Preflight while a blocker is unresolved.
2. Check compilation problems on the aggregate file + its primary test file. Use `mcp__ide__getDiagnostics` if available, else invoke the external `axon4to5-isolatedtest` skill with `target-name: <AggregateSimpleName>`, the migrated main files, and `test-sources: []` for a compile-only signal.
3. If zero compile problems AND test class exists, run scoped tests (see End condition).
4. If green AND no blocker fired → STOP. `AskUserQuestion`:
   - **Skip** *(Recommended)* — treat as already migrated.
   - **Deep verify** — diff current source against AF4 baseline (`git log` / `git show`) to confirm nothing was silently lost (dropped `snapshotTriggerDefinition`, missing `@EventTag`, lost `@CreationPolicy` semantics, missed multi-entity field).
5. Only proceed to procedure if user picks **Deep verify** OR step 2/3 reported failures.

## In scope

- ONE aggregate class annotated `@Aggregate` (Spring) or `@AggregateRoot` / `@Aggregate` (core).
- ALL command classes whose `@CommandHandler` lives on this aggregate.
- ALL event classes whose `@EventSourcingHandler` lives on this aggregate.
- Child entities reachable via `@AggregateMember` on this aggregate.
- The aggregate's primary test class (typically `<Aggregate>Test`) plus its direct subclasses.

## Out of scope

- DCB-style decomposition or any architectural restructuring.
- Snapshotting configuration — see [not-supported.md](not-supported.md) B1.
- Map-typed `@AggregateMember` — see [not-supported.md](not-supported.md) B3.
- `SagaTestFixture` migration — see [not-supported.md](not-supported.md) B4.
- `@DeadlineHandler` / `DeadlineManager` use inside the aggregate — see [not-supported.md](not-supported.md) B5.

## Subagent guidelines

Aggregates are mutually independent — different files, different tests, different
profile entries in `pom.xml`. The migration runner may fan out one subagent per
aggregate to parallelise the analysis half of the recipe. Apply / verify / commit
stay serial in the migration runner (`pom.xml` is a single shared file; merging
parallel `<profiles>` inserts is fragile).

```yaml
- subagent_type: general-purpose
- isolation: none           # subagents return a structured plan; migration runner writes
- parallelism: per-item     # one subagent per discovered aggregate target
- prompt-framing: |
    READ-ONLY analysis of ONE aggregate target. Do NOT edit files,
    commit, or run mvn. Read the aggregate, its commands, its events,
    its child entities, and its primary test class + subclasses.

    Identify and return as structured Output:
      1. Variant: simple | multi-entity | polymorphic.
      2. Blockers from not-supported.md (snapshotting, Map-typed
         @AggregateMember, SagaTestFixture, @DeadlineHandler) — with
         exact file:line references.
      3. CreationPolicy → handler-shape per command handler (consult
         creation-policy-decision.md). Note any handler that risks NPE
         on null state when AF5 materialises an empty entity.
      4. The existing project-specific domain exception (or rule /
         specification / helper) that would fire on the empty-state
         precondition for each such handler — exception type + message
         the test should expect in place of AggregateNotFoundException.
         Match the project's existing style; do NOT invent a new
         exception type.
      5. Test base file (`<Aggregate>Test`) — does it already have
         @AfterEach tearDown() { fixture.stop(); }? If not, flag.
      6. List of test methods asserting AggregateNotFoundException, with
         the proposed replacement assertion (rule class + message).
      7. The full `main-sources` / `test-sources` file lists to pass to
         the external `axon4to5-isolatedtest` skill for the
         `isolated-<Target>` scope (per [../verification.md](../verification.md)).

    DO NOT WRITE FILES. The migration runner owns: applying edits, splicing
    the profile into pom.xml, running scoped verify, committing.
```

**Why not full work-in-parallel via worktrees?** Each aggregate's
`axon4to5-isolatedtest` invocation appends a per-target scope to the same
shared build file (`pom.xml` or `build.gradle(.kts)`). Concurrent worktree
commits to the same scope-block region produce merge conflicts that need
deterministic resolution. The "research-in-parallel, write-in-serial" shape
above gets the analysis-time wall-clock savings without the merge problem.
A fully isolated worktree variant is feasible if the migration runner pre-allocates
all scope slots first in a single commit, then subagents fill their slot —
out of scope for this version of the recipe.

## Slim FQN cheatsheet

Full move tables: [../../docs/paths/index.adoc](../../docs/paths/index.adoc) §"Import and package changes" (all framework + extension packages) and [../../docs/paths/aggregates/index.adoc](../../docs/paths/aggregates/index.adoc) §"Import and package changes" (aggregate-specific). Per-recipe addendum lives in [annotation-cheatsheet.md](annotation-cheatsheet.md).

The four moves you almost always touch during this recipe:

| Removed (AF4) | Replaced by (AF5) |
|---|---|
| `AggregateLifecycle.apply(...)` (static) | `EventAppender#append(...)` (method parameter) |
| `@AggregateIdentifier` (field-level) | *(removed — use `@EventTag` on event field + entity `tagKey`)* |
| `@CreationPolicy` | *(removed — encoded by handler shape, see [creation-policy-decision.md](creation-policy-decision.md))* |
| `@AggregateMember` | `@EntityMember` (see multi-entity addendum) |

> ⚠️ `@InjectState` does NOT exist — always use `@InjectEntity`.

## Procedure

### Step 1 — Identify

1.1. Work on class given as target. If none, find first `@Aggregate`/`@AggregateRoot` class with `@EventSourcingHandler` methods.
1.2. Identify all **command classes** — first param of every `@CommandHandler` on aggregate (and constructor).
1.3. Identify all **event classes** — first param of every `@EventSourcingHandler`.
1.4. Identify primary **test class** (`<Aggregate>Test`) and direct subclasses (`grep -rln "extends <Aggregate>Test"`). Migrate base first.

### Step 2 — Detect variant

- **Simple** — no `@AggregateMember`, no concrete `@Aggregate`-annotated subclasses. Continue with steps 3–14, then Path A/B, then test fixture.
- **Multi-entity** — has any `@AggregateMember` field. Run steps 3–14 on root, then apply [multi-entity-migration.md](multi-entity-migration.md). **Map-typed members are a breaking change** — surface via `AskUserQuestion` before rewriting.
- **Polymorphic** — abstract/concrete superclass with subclasses also annotated `@Aggregate` and inheriting handlers. Run steps 3–14 on base + each subtype, then apply [polymorphism-migration.md](polymorphism-migration.md). Concrete subtypes do NOT carry `@EventSourcedEntity` themselves — discovered through base.

Variants are not mutually exclusive; apply both addenda when both detection rules fire.

### Steps 3–14 — Class-level transformation

3. In each command class:
   - Remove `import org.axonframework.modelling.command.TargetAggregateIdentifier`.
   - Add `import org.axonframework.modelling.annotation.TargetEntityId`.
   - Replace `@TargetAggregateIdentifier` → `@TargetEntityId`.
4. Annotate each command class with `@Command` (`org.axonframework.messaging.commandhandling.annotation.Command`). If AF4 had `@RoutingKey` on a property → `@Command(routingKey = "<propertyName>")` and remove `@RoutingKey` annotation + import.
5. In aggregate, identify the `@AggregateIdentifier`-annotated property and the `@EventSourcingHandler` that sets it from an event property. That event property is the one to annotate with `@EventTag`.
6. Annotate aggregate-id field in **every** event with `@EventTag(key = "<EntityName>")`. Use entity's simple class name (e.g. `"GiftCard"`) so it matches entity's `tagKey`. Without DCB, exactly ONE `@EventTag` per event.
    - When `@EventTag` is used WITHOUT `key`, framework derives it from the field name. Recommended: be explicit (`@EventTag(key = "Bike")`).
    - Pick a `tagKey` that conveys the **entity type** (`"Bike"`) rather than the field name (`"bikeId"`) — stays stable across renames.
7. Annotate each event class with `@Event` (`org.axonframework.messaging.eventhandling.annotation.Event`). If event had `@Revision("x")` → `@Event(version = "x")` and remove `@Revision` annotation + import. Otherwise add bare `@Event` (default name = simple class name, default version = `0.0.1`).
8. Remove `@AggregateIdentifier` annotation (and import) from aggregate. Id field stays as regular field.
9. Replace import `org.axonframework.eventsourcing.EventSourcingHandler` → `org.axonframework.eventsourcing.annotation.EventSourcingHandler`.
10. Replace import `org.axonframework.commandhandling.CommandHandler` → `org.axonframework.messaging.commandhandling.annotation.CommandHandler`.
11. Annotate aggregate's no-arg constructor with `@EntityCreator` (mandatory in AF5). If no no-arg ctor exists, add one. Framework instantiates entity via this ctor before applying events.

    > **Likely already done by OpenRewrite (Migration Phase #1).** The bulk recipe inserts a no-arg `@EntityCreator` constructor and removes the AF4 `@Aggregate`/`@AggregateRoot` annotation in the same pass. Verify presence via grep before adding — duplicate `@EntityCreator` constructors compile but indicate a partial rewrite.

    Three legal `@EntityCreator` shapes — no-arg / `@InjectEntityId`-only / origin-event payload. See [../../docs/paths/aggregates/index.adoc](../../docs/paths/aggregates/index.adoc) §"Patterns of @EntityCreator usage" for the worked code. For architecture-neutral migration prefer the no-arg pattern (matches the OpenRewrite default).
12. Replace `AggregateLifecycle.apply(event)` → `eventAppender.append(event)`. Add `EventAppender eventAppender` as method parameter to every `@CommandHandler`. Remove static import of `AggregateLifecycle.apply`.
13. Verify `@CreationPolicy` / `AggregateCreationPolicy` migration. **OpenRewrite (Migration Phase #1) already removed the annotation and imports.** Behavior is preserved when paired with the no-arg `@EntityCreator` from Step 11 — no restoration work needed for `CREATE_IF_MISSING`. **The wrong handler shape compiles cleanly and only fails at test time.** Full matrix in [creation-policy-decision.md](creation-policy-decision.md). Short version:
    - `ALWAYS` → **`static`** `@CommandHandler`. OpenRewrite usually does NOT flip to static — verify and reshape if needed.
    - `CREATE_IF_MISSING` → **instance** `@CommandHandler` + no-arg `@EntityCreator`. **Default post-OpenRewrite outcome.** Do NOT switch to `static + @InjectEntity` here unless AF4 already threw on existing entities — that flips semantics.
    - `NEVER` (or absent) → instance `@CommandHandler` (default).
    - Cosmetic cleanup: source comments next to former-`@CreationPolicy` handlers (e.g. `// performance downside in comparison to constructor`) may be stale after Step 11 added a real constructor. Drop them as part of this step — purely textual, no behavior impact.
14. Apply variant addenda from Step 2 if they fired.

### Path A — Spring Boot

Use when project depends on `axoniq-spring-boot-starter` (or AF4 `axon-spring-boot-starter`).

A.1. Replace `@Aggregate` (`org.axonframework.spring.stereotype.Aggregate`) → `@EventSourced` (`org.axonframework.extension.spring.stereotype.EventSourced`).

A.2. Configure `@EventSourced`:
- **`tagKey`** — same value as `@EventTag(key = ...)` on events. Default = entity's simple class name; if you use that as the tag key, you can omit `tagKey`. Recommended: be explicit (`@EventSourced(tagKey = "GiftCard")`).
- **`idType`** — set when AF4 `@AggregateIdentifier` field is **NOT** `String`. Default is `String.class`; mismatched types cause silent identifier-resolution failures. Example: `@EventSourced(tagKey = "Army", idType = ArmyId.class)`.
- **`concreteTypes`** — only when polymorphism addendum applies.

> ⚠️ **`snapshotTriggerDefinition` / caching attributes are NOT portable.** Preflight already ran [not-supported.md](not-supported.md) B1 — apply the recorded decision (`snapshotting`) here: if `accept-drop`, omit the attribute from `@EventSourced`; otherwise the recipe already exited.

### Path B — framework Configurer (no Spring)

Use when `inputs.wiring == "framework-config"` (project wires AF directly via `EventSourcingConfigurer.create()` / `MessagingConfigurer.create()` — no Spring auto-config).

B.1. Replace `@Aggregate` / `@AggregateRoot` (Spring or core, AF4) → `@EventSourcedEntity` (`org.axonframework.eventsourcing.annotation.EventSourcedEntity`). This is the **framework-level** annotation; in framework-config projects there is no Spring stereotype to swap to. Remove the AF4 `@Aggregate` / `@AggregateRoot` import.

B.2. Configure `@EventSourcedEntity` attributes — same semantics as `@EventSourced` in Path A:
- **`tagKey`** — must equal `@EventTag(key = ...)` on events. Default = entity's simple class name; if you use that as the tag key, you can omit `tagKey`. Recommended: be explicit (`@EventSourcedEntity(tagKey = "GiftCard")`).
- **`idType`** — set when AF4 `@AggregateIdentifier` field is **NOT** `String`. Default `String.class`.
- **`concreteTypes`** — only when polymorphism addendum applies.

Worked GiftCard class shape: [../../docs/paths/aggregates/index.adoc](../../docs/paths/aggregates/index.adoc) §"Simple `EventSourcedEntity` example".

> ⚠️ Same `snapshotTriggerDefinition` rule as Path A: Preflight already ran [not-supported.md](not-supported.md) B1. If `accept-drop`, omit the attribute from `@EventSourcedEntity`; otherwise the recipe already exited.

B.3. Register the entity in the project's `Configurer` setup. Find the file that builds the `EventSourcingConfigurer` (typical names: `*Configuration.java`, `*Application.java`, `*Bootstrap.java`, or a per-slice `<Slice>Configuration.java` whose static `configure(EventSourcingConfigurer)` returns the configurer with this slice's registrations applied). The canonical layout aggregates per-slice contributions into a single bootstrap chain:

```java
import org.axonframework.eventsourcing.configuration.EventSourcingConfigurer;
import org.axonframework.eventsourcing.configuration.EventSourcedEntityModule;

EventSourcingConfigurer.create()
    .registerEntity(
        EventSourcedEntityModule.autodetected(String.class, GiftCard.class))   // ← add this
    .registerCommandHandlingModule(...)
    .start();
```

`EventSourcedEntityModule.autodetected(IdType.class, EntityType.class)` reads the `@EventSourcedEntity` annotation on the entity to infer sourcing criteria, ID resolver, and entity factory. The `IdType` must match the routing-key Java type (the same value used for `idType` on `@EventSourcedEntity`).

If the project follows a per-slice configuration pattern (each slice exposes a `static EventSourcingConfigurer configure(EventSourcingConfigurer)` and a top-level module aggregator chains them), add `.registerEntity(EventSourcedEntityModule.autodetected(IdType.class, Entity.class))` inside the slice's `configure(...)` method:

```java
public class GiftCardConfiguration {
    public static EventSourcingConfigurer configure(EventSourcingConfigurer configurer) {
        return configurer
            .registerEntity(EventSourcedEntityModule.autodetected(String.class, GiftCard.class))
            .registerCommandHandlingModule(
                CommandHandlingModule.named("GiftCard")
                    .commandHandlers()
                    .autodetectedCommandHandlingComponent(c -> new GiftCardCommandHandler()));
    }
}
```

B.4. If the project's command handler also lives in a separate class (typical for framework-config layouts) and is not yet registered, add it via `CommandHandlingModule.autodetectedCommandHandlingComponent(...)`. This typically belongs in the `command-gateway` recipe or the bootstrap configuration class (see [../event-storage-engine/configuration.md](../event-storage-engine/configuration.md)) — but if the aggregate cannot reach a registered handler, it has no entry point. Surface this as Output `notes` rather than expanding scope here.

B.5. If you cannot locate the configurer setup file (multi-module project, generated wiring, etc.), do NOT silently skip. Emit Output with `result: needs-decision`, `caller-expects.next: ask-user`, and `reason: "Path B annotation rewrite done; please register the entity via EventSourcedEntityModule.autodetected(...) in your Configurer chain — recipe could not locate it."` Annotation rewrites from Steps 3–14 + B.1–B.2 are still committed (so `caller-expects.commit: true` for the partial work).

## Test fixture migration

Migrates AF4's `AggregateTestFixture` → AF5's `AxonTestFixture` built from `ApplicationConfigurer`. Full mapping table + gotchas in [test-fixture-mapping.md](test-fixture-mapping.md).

> If project has no test class for this aggregate, **skip T.1–T.5** and proceed to Verify.

T.1. Find test class (`<Aggregate>Test`) and subclasses (`grep -rln "extends <Aggregate>Test"`). Migrate base first.

T.2. Replace `AggregateTestFixture` with `AxonTestFixture`:
- Import: `org.axonframework.test.aggregate.AggregateTestFixture` → `org.axonframework.test.fixture.AxonTestFixture`.
- Field type: `AggregateTestFixture<?>` → `AxonTestFixture`.
- `@BeforeEach`: `new AggregateTestFixture<>(<Aggregate>.class)` → `AxonTestFixture.with(<configurer>)`.
- Minimal configurer (replace `IdType` / `Aggregate` with concrete types):
  ```java
  EventSourcingConfigurer.create()
                         .registerEntity(EventSourcedEntityModule.autodetected(IdType.class, Aggregate.class))
  ```
  Default `Customization(integrationEnabled=false)` already disables Axon Server / Postgres enhancers.
- Add `@AfterEach tearDown() { fixture.stop(); }`.

T.3. Convert each test method to fluent given/when/then. Mapping in [test-fixture-mapping.md](test-fixture-mapping.md). Common edits:
- `fixture.given(events…)` → `fixture.given().events(events…)`.
- `fixture.givenNoPriorActivity()` → `fixture.given().noPriorActivity()`.
- `.when(cmd)` → `.when().command(cmd)`.
- `.expectEvents(events…)` → `.then().events(events…)`.
- `.expectException(Cls.class)` → `.then().exception(Cls.class)`.

> **`EventMessage` accessors are record-style in AF5.** Inside `eventsSatisfy(events -> { ... })` lambdas (or any other place handling raw `EventMessage`), use `events.get(0).payload()` and `events.get(0).metaData()` — **NOT** AF4's `getPayload()` / `getMetaData()`.

T.4. Adjust behavioral assertions for AF5 semantics. Full list in [test-fixture-mapping.md](test-fixture-mapping.md). Most common:
- `AggregateNotFoundException` is **NOT** thrown for instance handlers in AF5. With no-arg `@EntityCreator`, framework always materializes empty entity, so handler runs and any domain rule against empty state surfaces instead.
- Static (creational) handlers throw `EntityAlreadyExistsForCreationalCommandHandlerException` when entity already exists. If you see this in a test that should succeed on existing entities, the handler shouldn't be `static` — re-check Step 13 against [creation-policy-decision.md](creation-policy-decision.md).

T.5. Run just the migrated tests. Confirm they pass before moving on. If they fail, do NOT declare success — re-check Step 13 (handler shape) and T.4 (exception expectations). Test run is also the smoke test for Step 13: a wrong static-vs-instance `CreationPolicy` choice has no compile-time signal.

## Verify (against End condition)

If surrounding code still uses AF4 APIs, scope verification to the aggregate by invoking the external `axon4to5-isolatedtest` skill (see [../verification.md](../verification.md)):

```
Skill: axon4to5-isolatedtest
Inputs:
  target-name: <AggregateSimpleName>          # e.g. Faculty
  build-file: <target>/pom.xml | <target>/build.gradle(.kts)
  main-sources:
    - src/main/java/<…>/<Aggregate>.java
    - src/main/java/<…>/<Command>.java …
    - src/main/java/<…>/<Event>.java …
    - src/main/java/<…>/<ChildEntity>.java …    # if @EntityMember present
  test-sources:
    - src/test/java/<…>/<Aggregate>Test.java
    - src/test/java/<…>/<Aggregate>SubTest.java # if subclasses migrated together
  extra-deps:
    - org.axonframework:axon-modelling:${axon5.version}
    - org.axonframework:axon-eventsourcing:${axon5.version}
    - org.axonframework:axon-test:${axon5.version}
    # Add org.axonframework.extensions.spring:axon-spring for Spring path A.
    # Add jackson-annotations:2.21 pin if Spring Boot 3.5.x — see test-fixture-mapping.md.
  cleanup: false                                # true on the recipe's last successful run
```

The external skill returns the exact copy-paste compile + test commands; recipes do NOT hand-craft Maven `-P` flags or Gradle `:testIsolated…` invocations.

Run a follow-up invocation with `cleanup: true` ONLY when the recipe's End condition is green AND the migration runner is ready to commit (the cleanup removes the scope from the build file).

> ⚠️ **Prefer per-file source paths over package wildcards.** A glob like `src/main/java/com/example/write/**/*.java` would pull in every file in that package — including `*Mcp.java`, `*RestApi.java`, and other non-migration files that may still use AF4 APIs or Java preview features. The external skill defaults to per-file includes; pass explicit paths.

> ⚠️ **Multi-module / multi-project**: the external skill writes the scope into the build file of the module that owns the target. The migration runner's pinned `build-tool` plus the target's owning module determine `build-file` — pass the absolute path to the right module's build file (not the parent reactor pom).

## Caveats

- **IDE LSP false positives after the AF5 import refactor.** Once the bulk OpenRewrite recipes have run and `org.axonframework.*` package names have shifted, some editors / Java LSPs report phantom `cannot resolve` errors for package-private types referenced from sub-package tests (e.g. `AstrologersId` from `astrologers.write.proclaimweeksymbol`). javac and the build tool are the source of truth — if `axon4to5-isolatedtest` returns a green scoped test result, the migration is fine. Do NOT chase phantom LSP errors with extra `public` modifiers or extra source entries.

## Reference index (this recipe's local references)

- [annotation-cheatsheet.md](annotation-cheatsheet.md) — full FQN tables.
- [creation-policy-decision.md](creation-policy-decision.md) — `ALWAYS`/`CREATE_IF_MISSING`/`NEVER` → AF5 handler shape.
- [multi-entity-migration.md](multi-entity-migration.md) — `@AggregateMember` hierarchies addendum. Map-not-supported breaking change here.
- [polymorphism-migration.md](polymorphism-migration.md) — inherited handlers, `concreteTypes` registration.
- [test-fixture-mapping.md](test-fixture-mapping.md) — `AggregateTestFixture` → `AxonTestFixture` full mapping + gotchas.
- [examples/](examples/) — curated before/after migrations.
