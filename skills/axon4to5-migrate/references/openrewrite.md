# Recipe: openrewrite (Migration Phase #1)

Thin wrapper around the external **`axon4to5-openrewrite`** skill. Decides `--framework` from pinned license, invokes the skill, classifies the resulting diff.

The external skill owns build-tool detection (Maven/Gradle), recipe pinning, wrapper bumps, retries. Never hand-craft `mvn rewrite-maven-plugin:run` / `gradle rewriteRun`.

> Post-run state is expected to be **non-compiling**. The bulk recipe applies the first mechanical step only — remaining surface (handler shapes, async dispatch, configuration, aggregate model) is per-construct work.

## Inputs

- `target` — project root path (Skill tool CWD).
- `license` — `free-af5` → `--framework axon`; `axoniq-commercial` → `--framework axoniq`. Pinned at INIT.
- `commit` — always `--commit false`; orchestrator owns the commit.

## Preflight

- Already on AF5? Check `pom.xml` BOM / dep versions OR `build.gradle*`. AND `git log --oneline | grep af5-migration | head -5`.
- Both clean → `result: skipped` (`already on AF5`). Re-run only if user explicitly asks.

## Procedure

1. **Validate target.** Path exists, has `pom.xml` OR `build.gradle*`, is a git repo. Refuse if path is the AxonFramework repo itself.
2. **Clean tree.** Dirty → `AskUserQuestion`: stash / commit-first / abort.
3. **Read pinned license.** If unset, run Step 3a then pin.
4. **Invoke the external skill:**
   ```
   Skill: axon4to5-openrewrite
   Arguments: --framework <axon | axoniq> --commit false
   ```
5. **Read its report** — see "Reading the report".
6. **Emit `## Output`.** Orchestrator owns the commit.

**STOP after step 5/6.** Do NOT run `mvn compile` / `mvn verify` / `./gradlew build`.

### Step 3a — Inspect free-vs-commercial signals (only when license unset)

```bash
grep -RE 'org\.axonframework' --include='pom.xml' --include='build.gradle*' <target>
grep -RE 'AxonServer|DistributedCommandBus|SequencedDeadLetterQueue|DeadLetter' \
     --include='*.java' --include='*.kt' <target>/src 2>/dev/null
```

| Signal | Decision |
|---|---|
| `axon-server-connector`, `axon-distributed-commandbus-*`, source refs to `AxonServerConfiguration` / `DistributedCommandBus` / DLQ | `--framework axoniq` |
| Spring auto-config wires Axon Server profile but no source refs; commented-out DLQ snippets | ask user (default `axoniq`) |
| Only core `axon-{messaging,modelling,eventsourcing}` / Spring Boot starter, no source refs | `--framework axon` |

## Reading the report

- **Success** (exit 0) — run "Behavior-change classification" below; emit `result: success`.
- **Failure** (exit ≠ 0) — working tree clean (skill rolls back). Copy bail reason verbatim into `notes`; emit `result: failed`, `next: halt`.
- **No changes but project plainly AF4** — treat as failure with reason `recipe-no-op`.

## Behavior-change classification (anti-alarmism)

The external skill performs **paired** rewrites — removes an AF4 annotation AND inserts AF5 equivalent. Reporting only the removal makes the run sound destructive when behavior is preserved.

### What the recipe already does (inventory — don't flag these)

**Build files:** BOM swap (`axon-bom` → `axon-framework-bom` / `axoniq-framework-bom`), Java source/target ≥ 21, dropped deps (`axon-spring-aot`), commercial starter swap.

**Renames:** handler annotations into `.annotation.*` subpackages, `EventBus` → `EventSink`, `ConfigurerModule` → `ConfigurationEnhancer`, extension repackaging, commercial path re-namespaces `org.axonframework.*` → `io.axoniq.framework.*` for Axon Server / DLQ / distributed-messaging / Testcontainers classes.

**On the entity:** `@Aggregate` → `@EventSourced`, `@AggregateRoot` → `@EventSourcedEntity`, `@AggregateIdentifier` stripped, no-arg `@EntityCreator` ctor added, `@CreationPolicy` stripped, `AggregateLifecycle.apply(...)` → `eventAppender.append(...)` with `EventAppender` parameter.

**On events:** `@EventTag` added on id-matching component, `@Revision("x")` → `@Event(version = "x")`, bare events get `@Event` + default `0.0.1`. Accessors `getPayload()` / `getMetaData()` / `getIdentifier()` → `payload()` / `metadata()` / `identifier()`.

**On commands:** `@TargetAggregateIdentifier` → `@TargetEntityId`, `@RoutingKey` lifted to class-level `@Command(routingKey = "…")`, constructor `@CommandHandler` → `public static void handle(...)` methods, in-handler `CommandGateway` → injected `CommandDispatcher` parameters.

**On query dispatch:** `ResponseTypes.instanceOf(X.class)` unwrapped to direct `X.class`; `query(...) + multipleInstancesOf` → `queryMany(...)`.

**On Spring config:** `axon.serializer.*` → `axon.converter.*`. Advisory `// TODO` inserted above obsolete `sequencing-policy` settings and lost aggregate config (e.g. `snapshotTriggerDefinition`).

**On test classes:** `AggregateTestFixture` / `SagaTestFixture` → `AxonTestFixture`, fluent chain rewritten, `@EntityCreator` added on test-class no-arg constructors when the test models an entity. Subclasses (`extends <Aggregate>Test`) are rewritten in the same pass.

### Preserved behavior — nothing to flag

| AF4 removed | AF5 inserted (same run) |
|---|---|
| `@CreationPolicy(CREATE_IF_MISSING)` on instance `@CommandHandler` | no-arg `@EntityCreator` ctor (framework materializes empty entity, runs instance handler) |
| `@CreationPolicy(NEVER)` on instance `@CommandHandler` | annotation stripped; instance is the AF5 default |
| `@AggregateIdentifier` on entity field | `tagKey` on `@EventSourced` / `@EventSourcedEntity` + `@EventTag` on event field |
| `AggregateLifecycle.apply(...)` | `EventAppender` parameter + `eventAppender.append(...)` |
| `@TargetAggregateIdentifier` / `@Revision("x")` / `@RoutingKey` | `@TargetEntityId` / `@Event(version="x")` / `@Command(routingKey="…")` |
| Constructor `@CommandHandler` | `public static void handle(...)` |
| `getPayload()` / `getMetaData()` / `getIdentifier()` | `payload()` / `metadata()` / `identifier()` |

### DO flag these (genuine behavior change)

- `@CreationPolicy(ALWAYS)` instance handler **not converted to `static`** by the recipe — runs as if `CREATE_IF_MISSING`. The aggregate recipe Step 13 must convert.
- `snapshotTriggerDefinition` / cache attribute on `@Aggregate` **dropped** with no AF5 equivalent (recipe leaves `// TODO`). Snapshotting not portable here.
- `EventStorageEngine` bean signature changed but no replacement wired.
- Handler-method parameter list shrank (e.g. `MetaData` removed) without an obvious AF5 substitute.
- AF4 imports remaining alongside AF5 replacements (the recipe should rename, not duplicate).
- Advisory `// TODO`s inserted by the recipe — deliberate hand-off markers.

### Cosmetic — mention but not flag as behavior loss

- Source comments next to mutated code that no longer match (e.g. stale `// performance downside …` next to a `@CommandHandler` after a no-arg `@EntityCreator` was added).
- Unused imports left after annotation moves.

When in doubt, grep the diff for the AF5 counterpart before claiming "removed without replacement".

## End condition

| State | When |
|---|---|
| `result: success` | exit 0, ≥ 1 rewrite, `git diff --stat` shows expected set |
| `result: skipped` | Preflight matched "already on AF5" |
| `result: failed` | exit ≠ 0; working tree clean (skill rolled back) |

## Output

```yaml
result: success | skipped | failed | needs-decision
target: <target project root>
reason: <one short line>
decisions:
  license: free-af5 | axoniq-commercial
  framework: axon | axoniq
  bail-reason: <one-line from external skill | "n/a">
  behavior-changes-flagged: yes | no | "n/a"
caller-expects: { commit: <true on success / false otherwise>, next: <proceed | ask-user | halt> }
notes: <behavior-change warnings on success; external skill's bail message verbatim on failed>
```

Orchestrator commit subject: `chore(af5-migration): apply OpenRewrite recipe (--framework <FRAMEWORK>) (Migration Phase #1)`.

## Subagent guidelines

```yaml
subagent_type: general-purpose
isolation: worktree                   # broad transform; easy rollback on license-choice mismatch
parallelism: single
prompt-framing: |
  Invoke axon4to5-openrewrite via the Skill tool with the chosen --framework and --commit false.
  Do NOT hand-craft Maven/Gradle invocations. Do NOT attempt to fix compile errors after the run.
```

## Caveats

- Don't run inside the AxonFramework repo itself.
- Compile failures after this recipe are expected; per-construct recipes scoped via `axon4to5-isolatedtest` handle the rest.
- If the external skill bails, per-construct recipes still run on AF4 source — slower but not blocked.
