# Recipe: openrewrite (Migration Phase #1)

Thin wrapper around the installed external skill **`axon4to5-openrewrite`**. This recipe decides which `--framework` value to pass, invokes the skill via the Skill tool, then classifies the bulk diff so per-construct recipes don't have to re-derive it.

The external skill owns everything build-tool-specific: Maven vs Gradle detection, recipe artifact pinning, wrapper bumps on JDK mismatches, init-script wiring, retries on transient failures. Recipes never invent `mvn rewrite-maven-plugin:run` or `gradle rewriteRun` invocations.

## Canonical reference

- [docs/paths/index.adoc](../docs/paths/index.adoc) — full list of package + module moves, BOM, what the bulk recipes target.
- [docs/prerequisites.adoc](../docs/prerequisites.adoc) — JDK / Spring Boot / Axon Server baseline.

> **The post-run state is expected to be non-compiling.** The external skill runs the *first* mechanical step only. The remaining AF4 → AF5 surface (handler shapes, async dispatch, configuration model, aggregate model) is judgment-driven and lives in the per-construct recipes. Compile errors after this recipe are the work the per-construct recipes exist to do, scoped iteratively via [verification.md](verification.md) (which delegates to `axon4to5-isolatedtest`).

## Goal

Bulk mechanical rewrites applied by the external skill:

- Java compiler target bumped (Spring Boot 4 / AF5 minimum).
- Spring Boot upgraded to 3.5.x (no-op if already ≥ 3.5 / 4.x).
- AF4 package renames inside `org.axonframework.*` (and `io.axoniq.framework.*` for commercial).
- Maven coordinates / BOM swapped to AF5.

Compilation is NOT a success criterion. The external skill returns success when its recipe applied cleanly; non-compiling source is the expected baseline for the per-construct phases.

## Inputs

- target: project root path (required — the Skill tool's CWD is the external skill's working directory).
- license: `free-af5` | `axoniq-commercial` (required — pinned in `progress.md` Pinned-decisions at INIT). Maps to:
  - `free-af5` → `--framework axon`
  - `axoniq-commercial` → `--framework axoniq`
- commit: always `--commit false` for this recipe. The orchestrator owns the commit per [commit-cadence.md](commit-cadence.md) — the external skill leaves the working tree modified.

## Preflight

1. Project already at AF5? Check `pom.xml` BOM / dep versions (or `build.gradle*` for Gradle).
2. Recent OpenRewrite run already committed? `git log --oneline | grep af5-migration | head -5`.
3. If both clean → return Output with `recipe-status: skipped-already-applied`, `skip=true`. AskUserQuestion only when the user explicitly wants to re-run.

## Subagent guidelines

- subagent_type: general-purpose
- isolation: worktree
  # Bulk transform touches many files; worktree gives easy rollback if a license
  # choice turns out wrong (e.g. user wanted free but ran commercial).
- prompt-framing: |
  Invoke the installed external skill `axon4to5-openrewrite` via the Skill tool
  with the chosen `--framework` value and `--commit false`. Do NOT hand-craft
  Maven/Gradle invocations. Do NOT attempt to fix compile errors after the run.
- parallelism: single

## Procedure

1. Validate target.
   - Path exists, has `pom.xml` OR `build.gradle*`, is a git repo.
   - Refuse if path is the AxonFramework repo itself (`git remote get-url origin` matches).
2. Pre-flight clean tree check.
   - Dirty → `AskUserQuestion`: stash / commit-first / abort.
3. Read pinned license from `progress.md` Pinned-decisions.
   - Absent or ambiguous → run Step 4a to classify, then pin the decision before continuing.
   - `free-af5` → `--framework axon`.
   - `axoniq-commercial` → `--framework axoniq`.
4. Invoke the external skill via the Skill tool:

   ```
   Skill: axon4to5-openrewrite
   Arguments: --framework <axon | axoniq> --commit false
   ```

   The Skill tool's CWD must be the target project root. The external skill:
   - detects build tool (Maven vs Gradle),
   - resolves the recipe artifact and pins it,
   - bumps the build wrapper on `Unsupported class file major version` errors,
   - surfaces specific failure routes (`Could not find artifact …`, recipe parse errors, …) with a one-line summary the orchestrator forwards verbatim.

5. Read the external skill's report (see "Reading the report" below).
6. Emit `## Output` for the orchestrator. Orchestrator owns the commit.

### Step 4a — Inspect free-vs-commercial signals

Only used when the license decision is unset or weak.

```bash
# AF4 dependency footprint — narrow to dependency declarations.
grep -RE 'org\.axonframework' --include='pom.xml' --include='build.gradle*' <target>

# Source-level signals for commercial-only features.
grep -RE 'AxonServer|DistributedCommandBus|SequencedDeadLetterQueue|DeadLetter' \
     --include='*.java' --include='*.kt' <target>/src 2>/dev/null
```

Classify:

- **Strong commercial signal** — `axon-server-connector`, `axon-distributed-commandbus-*`, references to `AxonServerConfiguration` / `DistributedCommandBus` / `SequencedDeadLetterQueue` / `DeadLetter`. → `--framework axoniq`.
- **Weak commercial signal** — Spring auto-config wires Axon Server profile but no source references; commented-out DLQ snippets; test-only references. → ask user (default: `axoniq`).
- **No commercial signal** — only core `axon-messaging` / `axon-modelling` / `axon-eventsourcing` / Spring Boot starter, no source references to dropped features. → `--framework axon`.

### Reading the report

Two acceptable terminal states (see "End condition" below):

- **Success** — external skill exited 0, recipe applied. Run the Behavior-change classification below.
- **Failure** — external skill exited non-zero. Copy its one-line bail reason verbatim into `Output.notes`, set `recipe-status: failed`, surface to the orchestrator.

If the report shows "no changes" but the project is plainly AF4, treat as failure with reason `recipe-no-op` and surface for diagnosis.

### Step 7 — STOP

DO NOT run `mvn compile` / `mvn verify` / `./gradlew build`. The orchestrator owns the commit and the next-step checkpoint with the user.

## Behavior-change classification (anti-alarmism)

The external skill performs **paired** rewrites: it removes an AF4 annotation AND inserts the AF5 equivalent in the same diff (sometimes via two separate sub-recipes). Reporting only the removal makes the run sound destructive when behavior is preserved. Use the inventory and table below before flagging anything to the user.

### Post-run inventory — what should already be done

The published recipes (`Axon4ToAxon5*` Group A and `Axon4ToAxoniq5*` Group B) at `axon-migration:5.1.x`/`5.2.x` actually do:

**Build files / coordinates:**
- BOM swap: `axon-bom` → `axon-framework-bom` (free) or `axoniq-framework-bom` (commercial).
- Java source/target bumped to the configured LTS (≥ 21).
- Dependencies with no AF5 port removed (e.g. `axon-spring-aot`).
- Spring Boot starter swap: `axon-spring-boot-starter` → `axoniq-spring-boot-starter` (commercial path only).

**Package / class renames:**
- Handler annotations moved into `.annotation.*` subpackages.
- `EventBus` → `EventSink`, `ConfigurerModule` → `ConfigurationEnhancer`.
- Extension repackaging (e.g. `org.axonframework.micrometer` → `org.axonframework.extension.metrics.micrometer`).
- Commercial path also re-namespaces `org.axonframework.*` → `io.axoniq.framework.*` for Axon Server connector, DLQ, distributed-messaging, and Testcontainers classes.

**On the entity:**
- `@Aggregate` → `@EventSourced(tagKey = ..., idType = ...)` (Spring stereotype).
- `@AggregateRoot` → `@EventSourcedEntity(...)` (core stereotype).
- `@AggregateIdentifier` annotation + import removed (id field stays as a regular field).
- No-arg `@EntityCreator` constructor added (created if it didn't exist).
- `@CreationPolicy` and `AggregateCreationPolicy` annotations + imports stripped unconditionally.
- `AggregateLifecycle.apply(...)` calls → `eventAppender.append(...)` with `EventAppender` injected as a handler parameter.

**On events:**
- `@EventTag` added on record components / fields whose name matches the entity's id field.
- `@Revision("x")` → `@Event(version = "x")`; bare events get `@Event` with default name + `0.0.1` version.
- Accessor renames: `getPayload()` → `payload()`, `getMetaData()` → `metadata()`, `getIdentifier()` → `identifier()`.

**On commands:**
- `@TargetAggregateIdentifier` → `@TargetEntityId` on the id field.
- `@RoutingKey` lifted off record components onto a class-level `@Command(routingKey = "...")`.
- Constructor `@CommandHandler`s converted to `public static void handle(...)` methods.
- In-handler `CommandGateway` fields swapped for injected `CommandDispatcher` parameters.

**On query handlers / dispatch:**
- `ResponseTypes.instanceOf(X.class)` unwrapped to a direct `X.class` argument.
- `query(...)` paired with `multipleInstancesOf` renamed to `queryMany(...)`.

**On Spring config:**
- `axon.serializer.*` properties renamed to `axon.converter.*` in `application.properties`/YAML.
- Advisory `// TODO`s inserted above obsolete `sequencing-policy` settings and lost aggregate config (e.g. `snapshotTriggerDefinition`).

**On test classes:**
- `AggregateTestFixture` and `SagaTestFixture` → `AxonTestFixture`.
- Fluent given/when/then chain rewritten to AF5's phase-aware API.
- `@EntityCreator` added on test-class no-arg constructors when the test class itself models an entity.

> ⚠️ Test **subclasses** (`extends <Aggregate>Test`) are rewritten by the same pass — verify with `grep -rln "extends .*Test" <target>/src/test`. The agent does NOT need to re-walk the hierarchy.

### Behavior-change table

| AF4 element removed by recipe | Paired AF5 insertion (same run; possibly different sub-recipe) | Behavior status | What to tell the user |
|---|---|---|---|
| `@CreationPolicy(CREATE_IF_MISSING)` on instance `@CommandHandler` | No-arg `@EntityCreator` constructor on the entity | **Preserved.** AF5 materializes empty entity via the no-arg `@EntityCreator`, then runs the instance handler. | Nothing to flag. Optionally note: `AggregateNotFoundException` no longer thrown for instance handlers. |
| `@CreationPolicy(ALWAYS)` on instance `@CommandHandler` | **Not** auto-translated — handler stays as instance method | **Manual reshape required.** The annotation is stripped but the handler is NOT made `static`. An `ALWAYS` handler then runs as if it were `CREATE_IF_MISSING`. | Flag explicitly. Per-aggregate recipe Step 13 must convert to `static`. |
| `@CreationPolicy(NEVER)` on instance `@CommandHandler` | Annotation stripped; handler stays instance | **Preserved** — instance is the AF5 default. | Nothing to flag. |
| `@AggregateIdentifier` on entity field | `tagKey` attribute on `@EventSourced` / `@EventSourcedEntity` + `@EventTag` on event field | **Preserved.** | Nothing to flag. |
| `AggregateLifecycle.apply(...)` static call | `EventAppender` parameter on handler + `eventAppender.append(...)` | **Preserved.** | Nothing to flag. |
| `@TargetAggregateIdentifier` on command field | `@TargetEntityId` on the same field | **Preserved.** | Nothing to flag. |
| `@Revision("x")` on event | `@Event(version = "x")` on the same event | **Preserved.** | Nothing to flag. |
| `@RoutingKey` on record component | `@Command(routingKey = "<name>")` on the command class | **Preserved.** | Nothing to flag. |
| Constructor `@CommandHandler` | `public static void handle(...)` method | **Preserved.** | Nothing to flag. |
| `getPayload()` / `getMetaData()` / `getIdentifier()` on `EventMessage` | `payload()` / `metadata()` / `identifier()` | **Preserved.** | Nothing to flag. |

**Genuinely behavior-changing — DO flag these:**

- `@CreationPolicy(ALWAYS)` handler not converted to `static` (see table row 2).
- `snapshotTriggerDefinition` / cache attribute on `@Aggregate` **dropped** with no AF5 equivalent; recipe leaves a `// TODO`. Snapshotting is not portable in this recipe — surface for follow-up.
- `EventStorageEngine` bean signature changed but no replacement bean wired (sometimes a TODO is left).
- Any handler-method parameter list shrank (e.g. `MetaData` parameter removed) without an obvious AF5 substitute inserted.
- Imports for AF4 types remaining alongside their AF5 replacements (the recipe should rename, not duplicate).
- Advisory `// TODO` comments inserted by the recipe — deliberate hand-off markers.

**Cosmetic-only — mention as tidy-up, NOT as behavior loss:**

- Source comments next to mutated code that no longer match (e.g. `// performance downside in comparison to constructor` left attached to a `@CommandHandler` after a no-arg `@EntityCreator` constructor was added). Behavior is unaffected.
- Unused imports left after annotation moves.

When in doubt, grep the diff for the AF5 counterpart before claiming an AF4 element was "removed without a replacement."

## End condition

Two acceptable terminal states — both are normal exits, neither halts the caller:

1. **Success.** External skill exited 0 with at least one rewrite (or "already migrated" — see Preflight). `git diff --stat` shows the expected set of mechanical rewrites for the chosen framework. Output `decisions` captures `framework`, `recipe-status: success`, and behavior-change notes.
2. **Graceful bail.** External skill exited non-zero. Working tree is clean (the external skill rolls back on failure). Output `recipe-status: failed` with the bail reason verbatim. Per-construct recipes proceed without this step — make that explicit to the caller.

## Output

- target: <target project root>
- decisions:
    - license: <free-af5 | axoniq-commercial>
    - framework: <axon | axoniq>
    - recipe-status: <success | failed | skipped-already-applied>
    - bail-reason: <one-line from external skill | "n/a">
    - behavior-changes-flagged: <yes | no | "n/a">
- needs-user-decision: false typically — true only when the external skill reported a recoverable failure the user can fix mid-session.
- notes: behavior-change warnings on success; or the external skill's bail message on failure.

> Subject line for the orchestrator's commit (chosen by orchestrator based on Output):
> `chore(af5-migration): apply OpenRewrite recipe (--framework <FRAMEWORK>) (Migration Phase #1)`

## Caveats

- **Don't run inside the AxonFramework repo.** Recipes are for consumer projects — running against the framework rewrites framework source. Step 1 enforces this.
- **Free vs commercial is a license choice, not a version bump.** Both flavours target the same release line.
- **Spring Boot upgrade is safe on already-modern projects.** The bulk recipes never downgrade.
- **Compile failures after recipe are expected, not a problem to chase.** Remaining shape changes live in per-construct recipes scoped via `axon4to5-isolatedtest`.
- **OpenRewrite is a productivity accelerator, not a prerequisite.** If the external skill bails, per-construct recipes still run on AF4 source. The migration takes longer because mechanical work is amortised across phases instead of batched once, but it is not blocked.

## Reference docs

- External skill: `axon4to5-openrewrite` — owns Maven/Gradle detection, retries, wrapper bumps, init-script wiring.
- [docs/paths/index.adoc](../docs/paths/index.adoc) — human-language migration paths the recipes implement.
