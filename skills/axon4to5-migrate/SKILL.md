---
name: axon4to5-migrate
description: >-
  Migrate a Spring Boot or plain-Configurer Axon Framework 4 project to
  Axon Framework 5 — preserves behavior (no DCB, legacy event storage).
  Three modes: phased (default), debug (triage from compile errors),
  single (one file / FQ class).
argument-hint: "[<file path or FQ class> | debug | phased]"
disable-model-invocation: true
---

# AF4 → AF5 migration

**One skill, one job.** Drive a project through Axon 4 → 5 by routing
each candidate file to its **recipe** (under `references/<recipe>/`),
running it, then committing the result. Single source of truth for
project state is `<target>/.axon4to5-migration/progress.md`.

## What this skill does NOT do

- **No data migration.** Recipes rewrite code only — no SQL/DDL, no
  event-store row copies, no token-store rebuild, no snapshot rewrites.
  Every `move-to-*` option in a recipe's `not-supported.md` is a
  **code-rewrite choice**; the user owns any matching data move out-of-band.
- **No DCB / no new patterns.** Preserve the AF4 architecture as-is.
- **No build-tool gymnastics.** Per-target scoped verify is delegated
  to the external `axon4to5-isolatedtest` skill; bulk migration to
  `axon4to5-openrewrite`. This skill never hand-crafts `./mvnw -P …`
  or `./gradlew :test…` invocations.

## Modes (`$ARGUMENTS`)

| `$ARGUMENTS` | Mode | What it does |
|---|---|---|
| empty / `phased` | **PHASED** (default) | Walk routing table top-to-bottom, resumable from `progress.md`. |
| `debug` | **DEBUG** | Drive from build output: cluster compile errors → route highest-leverage cluster to a recipe. |
| `<file path or FQ class>` | **SINGLE** | Auto-route via routing table, run one recipe, commit, stop. |

Ambiguous → `AskUserQuestion`. A bad file path is NOT default-to-phased — surface the error.

## Goal — done when

- Standard build is green (`./mvnw clean verify` or `./gradlew clean build`),
  no `isolated-*` profiles/source-sets left in any build file.
- Same architecture as AF4 (no DCB, legacy event storage preserved).
- Project's existing wiring style is preserved:
  - **Spring Boot project** → stays on Spring auto-config (Path A in recipes).
  - **Plain Configurer project** → stays on direct `Configurer` API (Path B).

Wiring is pinned once at INIT — recipes never re-detect.

## Routing table

Single source of truth for: phase order, discovery, single-file auto-routing.

| Recipe | Mode | Phase | Discovery (grep) | Condition / Notes |
|---|---|---|---|---|
| `openrewrite` | one-shot | 1 | n/a | Project depends on `org.axonframework.*` and not yet on AF5 BOM. Delegates to external `axon4to5-openrewrite` skill (`--framework axon|axoniq` from pinned license). |
| `aggregate` | iterative | 2 | `@Aggregate\b\|@AggregateRoot\b` (`*.java`, `*.kt`) | Class with `@Aggregate`/`@AggregateRoot` AND `@EventSourcingHandler`. Variants detected in recipe: simple / multi-entity / polymorphic. |
| `event-processor` | iterative | 3 | `@ProcessingGroup\|org\.axonframework\.eventhandling\.EventHandler` | Class with `@EventHandler` methods. |
| `command-gateway` | iterative | 4 | `org\.axonframework\.commandhandling\.gateway\.CommandGateway` | Top-of-chain caller injecting `CommandGateway`, **not** a message handler. exclude-when: `@EventHandler\|@CommandHandler\|@QueryHandler\|@MessageHandlerInterceptor`. |
| `query-gateway` | iterative | 5 | `org\.axonframework\.queryhandling\.QueryGateway` | Top-of-chain caller injecting `QueryGateway`, **not** a handler. exclude-when: `@EventHandler\|@CommandHandler\|@QueryHandler`. |
| `query-handler` | iterative | 6 | `org\.axonframework\.queryhandling\.QueryHandler` | Class with `@QueryHandler` methods. |
| `interceptors` | iterative | 7 | `implements\s+MessageDispatchInterceptor\b\|implements\s+MessageHandlerInterceptor\b` | Implements AF4 interceptor SPI, **not** itself a handler. exclude-when: `@CommandHandler\|@EventHandler\|@QueryHandler` on same class. |
| `event-storage-engine` | one-shot | 8 | n/a | Project declares `EventStorageEngine` / `EmbeddedEventStore` / `AxonServerEventStore` bean (A) **or** registers one via `componentRegistry.registerComponent(EventStorageEngine.class, ...)` (B). Also dispatches into [event-storage-engine/configuration.md](references/event-storage-engine/configuration.md) for `eventStore()` / `eventBus()` reads and generic write-side shape changes. |
| `saga` | not-supported | n/a | `@Saga\b\|@SagaEventHandler\|@StartSaga\|@EndSaga\|SagaConfigurer` | Detected at INIT. Four-way decision per saga in the recipe. Sagas with `@DeadlineHandler` blocked from migrate path. |
| `debug` | triage | n/a | n/a (build errors) | Top-level mode, NOT a phase. Routes clusters to other recipes — sibling links allowed here only. |

**Adding a phase** = append a row with the next `Phase` number + a folder under `references/`.

### Single-file routing

User passes a file path or FQ class. Inspect the file, then for each
`iterative` / `one-shot` row in ascending `Phase` order:
- if `Discovery` matches AND `exclude-when` does not → that row wins.
- multi-match → lowest `Phase` wins. Ask via `AskUserQuestion` only if user wants to override.

User says **what**; the skill picks **how**.

## Recipe contract

Every `references/<recipe>/<recipe>.md` has these sections (parsed by heading, order flexible):

- **Canonical reference** — links into `docs/paths/*` (concepts live there; recipes only do mechanical edits).
- **Inputs** — typed list. `wiring` always supplied by the orchestrator from pinned decisions.
- **Preflight** — quick "already migrated?" check. If `not-supported.md` exists, run its Detection greps first.
- **Procedure** — numbered pseudo-code; branches into `### Path A — Spring Boot` / `### Path B — framework Configurer`.
- **End condition** — objective, machine-checkable.
- **Output** — one fenced ```yaml block with `result:` (see below).

Optional: `## Subagent guidelines` (declares how to fan out; default = serial, inline).
Optional: `not-supported.md` sibling file (blocker detections + `AskUserQuestion` flows + Output `decisions` keys).

### Output — one shape, six results

Every recipe Output is a YAML block with a single discriminator `result:`:

```yaml
result: success | skipped | rejected | needs-decision | blocked | failed
target: <FQ class | file path | "n/a">
reason: <one short line>            # required for everything except success
decisions: { <recipe-specific keys> }
caller-expects:
  commit: true | false
  next:   proceed | ask-user | record-and-skip | halt | route-to:<recipe>
notes: <optional free text>
```

| `result:` | When | Orchestrator does |
|---|---|---|
| `success` | End condition passed. | commit code + `progress.md`; next item. |
| `skipped` | Preflight saw target already on AF5. | no commit; next item. |
| `rejected` | Routing was wrong; this recipe doesn't apply. | no commit; if `next == route-to:<recipe>` re-route, else next. |
| `needs-decision` | A blocker requires `AskUserQuestion`. | run `AskUserQuestion` with `notes` options; on fix → re-run recipe; on defer → commit `progress.md` only; on stop → HALT. |
| `blocked` | AF5 gap with no recovery; AF4 surface commented-out + `TODO[AF5 migration: <key>]`. | if `commit: true` commit code + `progress.md`; else commit `progress.md` only; record blocker key. |
| `failed` | Verify red / external tool exit non-zero. | no commit; surface `reason`+`notes`; `AskUserQuestion`: hand off to `debug` / pause / stop. |

Worked examples per variant: [references/output-contract.md](references/output-contract.md).

### Forbidden in recipes (lint)

- Cross-recipe links (no `../command-gateway/…` from inside `aggregate/`). Exception: the `debug` recipe — its job IS routing.
- Duplication of canonical-doc content (full FQN tables, side-by-side code samples, "why this changed" prose). Link to `docs/paths/*` instead.
- References to `progress.md` / `learnings.md` / orchestrator semantics — the orchestrator owns state.
- Migration-phase numbering in free-form ("phase 1") — only `Migration Phase #N` is allowed (the `org.axonframework.common.lifecycle.Phase` framework class is exempt).
- Any `result:` value outside the six above.

## Docs routing table

Recipes hold **mechanical edits**. Canonical explanation of each AF4 → AF5 shift lives once in `docs/paths/`. Recipes link in; they do NOT duplicate.

| Topic | Doc | Used by |
|---|---|---|
| Import / package changes, "what's not in AF5 yet" | [docs/paths/index.adoc](docs/paths/index.adoc) | every recipe |
| Message annotations (`@TargetEntityId`, `@Event`, `@Command`, …) | [docs/paths/messages.adoc](docs/paths/messages.adoc) | `aggregate`, `*-gateway`, `query-handler` |
| Aggregates → `EventSourcedEntity` | [docs/paths/aggregates/index.adoc](docs/paths/aggregates/index.adoc) | `aggregate` |
| Multi-entity (`@EntityMember`) | [docs/paths/aggregates/multi-entity-migration.adoc](docs/paths/aggregates/multi-entity-migration.adoc) | `aggregate` |
| Polymorphic entities (`concreteTypes`) | [docs/paths/aggregates/polymorphism-migration.adoc](docs/paths/aggregates/polymorphism-migration.adoc) | `aggregate` |
| Entity Configurer registration | [docs/paths/aggregates/configuration-migration.adoc](docs/paths/aggregates/configuration-migration.adoc) | `aggregate` Path B |
| Event store choice | [docs/paths/event-store.adoc](docs/paths/event-store.adoc) | `event-storage-engine` |
| Snapshotting | [docs/paths/snapshotting.adoc](docs/paths/snapshotting.adoc) | `aggregate`, `event-storage-engine` |
| Serializer → Converter | [docs/paths/serializers.adoc](docs/paths/serializers.adoc) | `event-storage-engine` |
| Event processors | [docs/paths/projectors-event-processors.adoc](docs/paths/projectors-event-processors.adoc) | `event-processor` |
| Sequencing policies | [docs/paths/sequencing-policies.adoc](docs/paths/sequencing-policies.adoc) | `event-processor` |
| DLQ | [docs/paths/dlq.adoc](docs/paths/dlq.adoc) | `event-processor` |
| Test fixtures (`AxonTestFixture`) | [docs/paths/test-fixtures.adoc](docs/paths/test-fixtures.adoc) | `aggregate` |
| Interceptors | [docs/paths/interceptors.adoc](docs/paths/interceptors.adoc) | `interceptors` (+ pointer from each handler recipe) |
| Configuration migration | [docs/paths/configuration.adoc](docs/paths/configuration.adoc) | `event-storage-engine` + per-topic `*/configuration-reads.md` |
| Architecture / why | [docs/understanding-architecture-principles.adoc](docs/understanding-architecture-principles.adoc), [docs/solved-architecture-choices.adoc](docs/solved-architecture-choices.adoc), [docs/why-upgrade.adoc](docs/why-upgrade.adoc), [docs/prerequisites.adoc](docs/prerequisites.adoc) | INIT, when user asks "why X" |

## State — `<target>/.axon4to5-migration/`

```
.axon4to5-migration/
├── index.md       # short README pointing at progress.md and learnings.md
├── progress.md    # SINGLE SOURCE OF TRUTH; rewritten before every commit
└── learnings.md   # append-only narrative — surprises, manual fixes, decisions
```

Templates: [assets/progress-template.md](assets/progress-template.md),
[assets/learnings-template.md](assets/learnings-template.md),
[assets/index-template.md](assets/index-template.md).

**Persistence invariant:** every state change ends with `progress.md`
rewritten + committed in the **same** commit as the code change it
documents. Never split work and bookkeeping.

`progress.md` must include a `▶︎ RESUME HERE` block pointing at the
*next* unit (not the one just finished) — exact recipe, exact verify
command. A fresh session reading `progress.md` resumes with no
clarifying questions about state.

## Orchestrator flow

```
ORCHESTRATE($ARGUMENTS):
  target = resolve_and_validate()             # exists, has pom.xml/build.gradle,
                                              # git repo, NOT axonframework itself
  mode   = parse($ARGUMENTS)

  if SINGLE:
    ensure_pinned()                           # license → wiring → build-tool
    row = route_single_file(arg)              # via routing table
    run_recipe(row, arg); suggest /clear; STOP

  if DEBUG:
    loop:
      compile target                          # ./mvnw test-compile / ./gradlew testClasses
      if green → STOP (migration done in this branch)
      (row, item) = cluster_and_route()       # see references/debug/debug.md
      run_recipe(row, item)
      if compile output unchanged → AskUserQuestion: surface / skip-defer / stop

  if PHASED (default):
    if no progress.md → INIT
    else: read progress.md; handle dirty tree; confirm resume
    for each routing-table row in {iterative, one-shot} not yet done:
      items = discover(row) − deferred − unsupported
      for item in items: run_recipe(row, item)
      AskUserQuestion: continue / pause / stop
    FINALIZE


run_recipe(row, item):
  inputs = build_inputs(item, row)            # always includes pinned wiring + build-tool
  output = execute(row.recipe, inputs)        # runs ## Preflight → ## Procedure → ## End condition
  act(output)                                 # branches on output.result — see contract above


INIT (first PHASED run only):
  mkdir <target>/.axon4to5-migration/
  seed from assets/*-template.md
  ensure_pinned()                             # MANDATORY — never skipped
  scan routing-table not-supported rows:
    for each hit: AskUserQuestion accept-stays-af4 / pause / remove-feature-first
  commit "chore(af5-migration): initialize migration"


ensure_pinned():
  if license not pinned:
    rec = recommend_license()                 # commercial deps / sagas / upcasters → axoniq-commercial
    AskUserQuestion with rec listed first as "(Recommended) — {reason}"
    pin license                               # free-af5 | axoniq-commercial
  if wiring not pinned:
    detect: axon-spring-boot-starter dep → spring-boot
           @SpringBootApplication             → spring-boot
           DefaultConfigurer.defaultConfiguration / direct Configurer → framework-config
           else                               → AskUserQuestion
    pin wiring
  if build-tool not pinned:
    pom.xml only → maven; build.gradle* only → gradle; both → AskUserQuestion; neither → HALT
    pin build-tool


FINALIZE (after every routing-table row done):
  for each target with isolated-<X> scope (from progress.md):
    invoke axon4to5-isolatedtest with cleanup: true
  promote AF5 deps from cleaned scopes into main deps; remove activation refs in scripts/CI/docs
  full build (no scope):
    maven  → ./mvnw -f <target>/pom.xml clean verify
    gradle → ./gradlew -p <target> clean build
  if red, classify:
    recipe traceable → reopen that phase; re-enter PHASED; FINALIZE re-runs once green
    missed dep promotion → diff scope dep blocks; fix main deps; retry
    env / infra → AskUserQuestion: investigate / pause / stop
  update progress.md (all done); commit "chore(af5-migration): remove isolated-* scaffolding"
```

**Pinned decisions are NEVER re-asked.** They live in `progress.md`
Pinned-decisions block in order: license → wiring → build-tool →
not-supported decisions. Every recipe reads them; recipes never re-detect.

**Subagents.** A recipe is run in a subagent only if it declares
`## Subagent guidelines` AND its Procedure does not use
`AskUserQuestion` (prompts must reach the main conversation). The
subagent returns a structured Output; the orchestrator owns commits.

**Dirty working tree on resume.** If `git status --porcelain` shows
files the orchestrator did not touch, pause and `AskUserQuestion`:
stage-only-migration-files / let-user-clean-up / skip-this-commit.

**Encourage `/clear` between units.** After every commit on a
non-trivial unit, say so — phase boundaries especially.

## Commit rules

- **One commit per item.** Stage explicit paths only — never `git add -A`.
- **Same commit** must include the code change + matching `progress.md` rewrite (+ `learnings.md` if dirty).
- **Conventional message.** Subject line table + body shape: [references/commit-cadence.md](references/commit-cadence.md). Template: [assets/commit-message-template.md](assets/commit-message-template.md).
- **Never** `git push`, `git commit --amend`, `--no-verify`, or commit on `main` / `master`.
- **Never** silently delete an AF4 bean / registration / fixture call when its AF5 successor is missing. Comment it out, drop `// TODO[AF5 migration: <blocker-key>]`, record in `progress.md` Pinned-decisions + `learnings.md`.

## Anti-patterns

- Running `./mvnw verify` after Migration Phase #1 (it WILL fail by design until stabilization).
- Re-running OpenRewrite to "fix" what a per-construct recipe couldn't handle.
- Treating `event-storage-engine` as "auto-configured by the Spring Boot starter, no action needed" — the AF5 starter applies AF5 defaults, not a migration of the existing AF4 event store. The explicit `AggregateBased…EventStorageEngine` bean swap is mandatory.
- Editing files outside the recipe's scope to "clean up" — keep diffs atomic.
- Hand-crafting `-P isolated-…` or `:testIsolated…` invocations — that's the `axon4to5-isolatedtest` skill's job.

## Reference index

Shared (loaded on demand):
- [references/verification.md](references/verification.md) — call shape for `axon4to5-isolatedtest` / `axon4to5-openrewrite`.
- [references/commit-cadence.md](references/commit-cadence.md) — commit rules per `result:`.
- [references/source-access.md](references/source-access.md) — where AF4/AF5 sources resolve locally.
- [references/output-contract.md](references/output-contract.md) — worked examples for each `result:` variant.

Recipes:
- [references/openrewrite.md](references/openrewrite.md)
- [references/aggregate/aggregate.md](references/aggregate/aggregate.md)
- [references/event-processor/event-processor.md](references/event-processor/event-processor.md)
- [references/command-gateway/command-gateway.md](references/command-gateway/command-gateway.md)
- [references/query-gateway/query-gateway.md](references/query-gateway/query-gateway.md)
- [references/query-handler/query-handler.md](references/query-handler/query-handler.md)
- [references/interceptors/interceptors.md](references/interceptors/interceptors.md)
- [references/event-storage-engine/event-storage-engine.md](references/event-storage-engine/event-storage-engine.md)
- [references/saga/saga.md](references/saga/saga.md)
- [references/debug/debug.md](references/debug/debug.md)

Topic-nested configuration sub-references:
- [references/event-processor/configuration-reads.md](references/event-processor/configuration-reads.md)
- [references/command-gateway/configuration-reads.md](references/command-gateway/configuration-reads.md)
- [references/query-gateway/configuration-reads.md](references/query-gateway/configuration-reads.md)
- [references/event-storage-engine/configuration.md](references/event-storage-engine/configuration.md)

External skills (invoked via Skill tool):
- `axon4to5-openrewrite` — bulk Migration Phase #1 recipe.
- `axon4to5-isolatedtest` — per-target `isolated-<TargetName>` scope; inputs: `target-name`, `build-file`, `main-sources`, `test-sources`, `extra-deps`, `cleanup`.

Evals: [evals/](evals/).
