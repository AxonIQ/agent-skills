---
name: axon4to5-migrate
description: >-
  Migrate Axon Framework 4 project to Axon(iq) Framework 5. Spring Boot and native configs.
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

**Detection greps** (always include `--include='*.java' --include='*.kt' --include='*.scala'`):

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

Output a classification table (Category | Files found | Complexity | Notes) covering: Aggregates, Event handlers, Query handlers, Interceptors, Sagas, Event store, Tests, Dependencies.

**Blockers to flag before starting** (no AF5 equivalent — must be commented out + reported):
- `@DeadlineHandler`
- `SagaTestFixture`
- `snapshotTriggerDefinition` on `@Aggregate`

Use `AskUserQuestion` to confirm before proceeding (or stop here if approach C).

---

## Step 2.5: Initialise / resume progress tracking

`<project-root>/.axon4to5-migration/progress.md` is the durable single source of truth for this migration. It survives across Claude Code sessions; without it a new session has no memory of pinned decisions or which files were already migrated.

**On entry:** read `<project-root>/.axon4to5-migration/progress.md` FIRST. If it exists, honour the **Pinned Decisions** table and resume from the **RESUME HERE** block — do NOT re-ask Step 1 questions already answered there.

**If it does not exist:** create it now using the schema below, filling Pinned Decisions from the Step 1 answers.

**Update protocol:** after every file migrated, update the relevant Phase status row + the matching Per-phase items row with the commit SHA, then commit the code change **and** `progress.md` in the same commit.

Schema:

```markdown
---
last-updated: <ISO date>
session-count: <N>
---

# Axon Framework 4 → 5 Migration — Progress

## ▶︎ RESUME HERE

- **Current phase:** <Step 3 phase 1..9 | Validate | Done>
- **Next action:** <one sentence>
- **Awaiting user input?** <yes/no — what for>
- **Last commit:** <short SHA — message>

## Pinned Decisions

| Question | Answer | Source |
|----------|--------|--------|
| Configuration style | spring \| native | Step 1 Q2 |
| Migration approach | A \| B \| C | Step 1 Q3 |
| Commit cadence | one per file \| one per phase | <answered or default> |

## Phase status

| # | Phase | Status | Notes |
|---|-------|--------|-------|
| 1 | Dependencies | pending \| in-progress \| done \| skipped \| blocked | |
| 2 | Event classes | … | |
| 3 | Aggregates | … | |
| 4 | Event handlers | … | |
| 5 | Query handlers | … | |
| 6 | Interceptors | … | |
| 7 | Sagas | … | |
| 8 | Event store | … | |
| 9 | Tests | … | |
| V | Validate | … | |

## Per-phase items

Per phase, list the FQ class names migrated, status, and commit SHA.

### Phase 3 — Aggregates

| Class | Status | Commit | Notes |
|-------|--------|--------|-------|
| com.example.OrderAggregate | done | abc1234 | |
| com.example.PaymentAggregate | in-progress | — | EventAppender param being added |

## Blockers

(list any `🚧` items with the class name + reason — DeadlineHandler, SagaTestFixture, snapshotTriggerDefinition, etc.)
```

When a session is interrupted, the next session re-enters Step 2.5, then jumps directly to the **Next action** recorded in **RESUME HERE** — it does not re-run Step 1 questions.

---

## Step 3: Execute migration

### Approach A — OpenRewrite + AI

1. Run the `axon4to5-openrewrite` skill to execute the bulk recipe.
2. After OpenRewrite completes, proceed to the AI phases below.

#### What OpenRewrite covers (and what it leaves for AI)

Each pattern's `Notes` section ends with an `OpenRewrite status:` line — **Full** (no AI work), **Partial** (OR does part, AI fills the gap), or **None** (no OR rule, AI does it from scratch). Read that line on the specific pattern you're about to apply.

Cross-pattern overview (when you need to plan the AI follow-up workload before starting): see [`references/openrewrite-coverage.md`](references/openrewrite-coverage.md).

### Approach B — AI only

**Before touching any code**, load the pattern catalog:

```
Read: patterns/ALL_IN_ONE.md
```

Then execute the phases in order. Each phase below names the pattern files to apply — those files hold the verbatim AF4 → AF5 imports, annotation names, before/after code, and per-pattern rules. SKILL.md does not duplicate them.

**Idempotency — handle partially-migrated code.** Before applying a pattern, check whether the AF5 shape is already partially present from a prior pass (commonly: OpenRewrite). If so, complete the gaps (e.g. fix the placeholder `idType = Object.class`, add the missing `EventAppender` parameter, drop the lingering AF4 import) instead of re-applying the full pattern from the AF4 shape — re-application creates duplicates or reverses already-correct edits. See each pattern's **"Partial migration state (post-OpenRewrite)"** section for the concrete half-state and the minimal completion step.

---

### Phase order and pattern map

Apply phases strictly in this order — Phase 2 events are consumed by Phases 3, 4, 7; aggregate tagKey choice in Phase 3 must match `@EventTag` in Phase 2.

| # | Phase                       | Patterns (in `patterns/`)                                              |
|---|-----------------------------|------------------------------------------------------------------------|
| 1 | Dependencies                | `10-dependencies/*`                                                    |
| 2 | Event classes               | `20-aggregates/event-annotation.md`                                    |
| 3 | Aggregates                  | `20-aggregates/*` (all)                                                |
| 4 | Event handlers / processors | `30-event-handlers/*`                                                  |
| 5 | Query handlers              | `40-query-handlers/*`                                                  |
| 6 | Interceptors                | `50-interceptors/*`                                                    |
| 7 | Sagas                       | `60-sagas/saga-component.md` + Phase 4 patterns if saga dispatches cmds|
| 8 | Event store config (JPA)    | `70-event-store/event-store-jpa.md`                                    |
| 9 | Tests                       | `80-tests/test-fixture.md`                                             |

Cross-phase couplings the LLM must remember:

- **tagKey alignment** — the `tagKey` chosen in Phase 3 (`@EventSourced(tagKey=…)`) MUST equal the `@EventTag(key=…)` value applied in Phase 2 on the routing field of every event the aggregate emits.
- **EventAppender parameter** — Phase 3 changes every `@CommandHandler` method on an aggregate to take `EventAppender eventAppender` as the **last** parameter. Without it, `eventAppender.append(...)` in the body won't compile.
- **CommandGateway → CommandDispatcher** — if a saga (Phase 7) or query class (Phase 5) injects `CommandGateway`, apply the Phase 4 `command-dispatcher.md` pattern to those classes too.
- **Blockers — comment out, do NOT delete.** `snapshotTriggerDefinition` (Phase 3), `@DeadlineHandler` (Phase 7), `SagaTestFixture` (Phase 9) have no AF5 equivalent — add a `// TODO: no AF5 equivalent` note and surface in the summary.

For complex scenarios (multi-entity aggregates, polymorphic hierarchies, saga persistence, named queries, dispatch interceptors), also load `examples/ALL_EXAMPLES.md` for full before/after file walkthroughs.

---

## Step 4: Validate

**Definition of done: `mvn compile` (or `./gradlew compileJava`) exits 0.** Grep emptiness is NOT the gate — OpenRewrite renames symbols, so AF4 strings can be gone while the code still won't compile (e.g. `@EventSourced` present but missing `tagKey`/`idType`; `@CommandHandler` import updated but signature still lacks `EventAppender`).

**Intermediate non-compiling states are expected.** Phase 3 renames `@Aggregate` → `@EventSourced`, but the code only compiles again once the dependent edits (remove `@AggregateIdentifier`, add `@EntityCreator`, add `EventAppender` params, rewrite `AggregateLifecycle.apply` → `eventAppender.append`, update imports) are also applied. Do NOT roll back on a red intermediate compile — keep applying the dependent patterns until the loop converges.

### 4a. Compile loop (PRIMARY)

```bash
# Maven
mvn compile -q 2>&1 | tee /tmp/axon-compile.log

# Gradle
./gradlew compileJava 2>&1 | tee /tmp/axon-compile.log
```

For each `[ERROR]` line, map the symbol/method to a pattern and apply it. Re-compile. Repeat until clean.

**Compiler-error → pattern map** (representative; not exhaustive):

| Compiler error fragment                                                | Apply pattern                                          |
|------------------------------------------------------------------------|--------------------------------------------------------|
| `cannot find symbol: class Aggregate` / `AggregateRoot` / `AggregateIdentifier` | `patterns/20-aggregates/aggregate-class.md` (add `@EventSourced(tagKey=…, idType=…)`, remove `@AggregateIdentifier`) |
| `@EventSourced` / `@EventSourcedEntity` reports missing attribute, or runtime tag mismatch | `patterns/20-aggregates/aggregate-class.md` "Required attributes" — `tagKey` + `idType` are mandatory |
| `cannot find symbol: method apply(…)` inside an aggregate              | `patterns/20-aggregates/aggregate-lifecycle.md` + add `EventAppender` param (`patterns/20-aggregates/command-handler.md`) |
| `package org.axonframework.commandhandling does not exist` for `CommandHandler` | `patterns/20-aggregates/command-handler.md` — import is `org.axonframework.messaging.commandhandling.annotation.CommandHandler` |
| `cannot find symbol: class ProcessingGroup` / `MetaData` / `MetaDataValue` | `patterns/30-event-handlers/namespace-routing.md`, `metadata-type.md`, `metadata-value.md` |
| `cannot find symbol: class AggregateTestFixture` / `SagaTestFixture`   | `patterns/80-tests/*` — `AggregateTestFixture` → `AxonTestFixture`; `SagaTestFixture` is a blocker (no AF5 equivalent) |

If a compile error does not match any catalog pattern, stop and ask the user — do NOT guess.

### 4b. Post-compile AF4-leftover audit (SECONDARY)

Compiles green, but the compiler won't flag AF4 names inside comments, log strings, or YAML keys. Run a discovery scan to catch those:

```bash
grep -rn \
  'org\.axonframework\.spring\.stereotype\.Aggregate\|AggregateLifecycle\|@ProcessingGroup\|@TargetAggregateIdentifier\|AggregateTestFixture\|SagaEventHandler\|@Saga\b\|axon\.serializer\|\bMetaData\b\|GenericDomainEventMessage' \
  --include='*.java' --include='*.kt' --include='*.scala' --include='*.yaml' --include='*.properties' <root>/src/
```

This is an audit, not a gate. Hits in comments/docs may be intentional history; hits in active code mean the compile loop missed something — re-enter 4a.

### 4c. Tests

```bash
mvn test          # or ./gradlew test
```

### 4d. Summary

```
| Phase              | Status       | Notes                        |
|--------------------|--------------|------------------------------|
| Dependencies       | ✅ / ❌      |                              |
| Event classes      | ✅ / ❌      |                              |
| Aggregates         | ✅ (N files) |                              |
| Event handlers     | ✅ (N files) |                              |
| Query handlers     | ✅ (N files) |                              |
| Interceptors       | ✅ (N files) |                              |
| Sagas              | ✅ / ⏭ / 🚧 |                              |
| Event store        | ✅ / ⏭      |                              |
| Tests              | ✅ (N files) |                              |

Compilation: ✅ green / ⚠️ N error(s) remain
Tests:       ✅ green / ⚠️ N failure(s)
AF4 leftovers (4b): none / list
Blockers:    none / list here
```

---

## Behavior rules

- **Always load `patterns/ALL_IN_ONE.md` before touching any code** — it contains all import mappings and before/after examples.
- **Work through phases in order** — aggregates define events consumed by downstream handlers.
- **Apply patterns one file at a time** and verify imports after each edit.
- **Compilation green is the definition of done; grep emptiness is not.** Drive completion from `mvn compile` / `./gradlew compileJava` exit code and the `[ERROR]` list — see Step 4a. Intermediate red compiles between dependent patterns are expected; keep applying patterns, do not revert.
- **Flag blockers — never silently skip.** If a pattern has no AF5 equivalent (DeadlineHandler, SagaTestFixture, snapshotTriggerDefinition), comment out the code, add a `// TODO` note, and report it in the summary.
- **Preserve architecture** — no DCB, no event storage engine swap, no new patterns.
- **Do not auto-fix ambiguous cases.** When a compile error doesn't match a catalog pattern directly, ask the user before guessing.
- **Never edit `patterns/ALL_IN_ONE.md`, `examples/ALL_EXAMPLES.md`, or the catalog block inside `patterns/README.md` by hand** — regenerate them with `make generate` (or `python3 scripts/generate_all_in_one.py`).
- **Persist progress.** After every migrated file, update `<project-root>/.axon4to5-migration/progress.md` and commit it alongside the code change. A new session must be able to read `progress.md` alone and resume.
