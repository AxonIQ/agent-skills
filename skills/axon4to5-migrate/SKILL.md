---
name: axon4to5-migrate
description: >-
  Migrate a Spring Boot or plain-Configurer Axon Framework 4 project to
  Axon Framework 5 — preserves behavior (no DCB, legacy event storage).
  Three modes: phased (default, resumable phase-by-phase), debug (triage
  from compile errors), single (one file / FQ class).
argument-hint: "[<file path or FQ class> | debug | phased]"
disable-model-invocation: true
---

# AF4 → AF5 migration — orchestrator + plugin recipes

ONE skill. Orchestrator owns: mode dispatch, the routing table, progress
mechanics, commit emission. Recipes are phase-unaware plugins with a fixed
five-section interface plus an optional subagent block. Source of truth is
**`progress.md`** under `<target>/.axon4to5-migration/` — read on
every invocation, rewritten before every commit, committed alongside the
code change it documents.

## Mode dispatch — `$ARGUMENTS`

```yaml
phased:                         # default — runs when $ARGUMENTS empty or "phased"
  trigger: "(no args) | 'phased'"
  flow: PHASE_LOOP from current state in progress.md
  resume: read progress.md ▶︎ RESUME HERE block on every entry

debug:
  trigger: "'debug'"
  flow: DEBUG_LOOP — driven by mvn output, route clusters to recipes
  use-when: full project compile failing, or alternative to phased order

single:
  trigger: "<file path or FQ class name>"
  flow: RUN_ONE — auto-route to recipe via routing table, run once, commit, stop
  recipe: NOT specified by user — orchestrator picks via the routing table
```

Ambiguous → AskUserQuestion. Never auto-pick "phased" when the user clearly
named a file but the path is wrong; surface the error.

## Goal

> Fully compiling, green-test codebase on AF5, **same architecture as AF4**.
> No DCB. No new patterns. Legacy event storage preserved.
> Standard build (`./mvnw clean verify` or `./gradlew clean build`) green
> at the end of stabilization, **with no `isolated-*` scope still active**
> — and with **no `isolated-*` profiles/source-sets left in any build
> file**. The FINALIZE step delegates cleanup of every per-target scope to
> the external `axon4to5-isolatedtest` skill as the last act of the
> orchestrator; a finished migration leaves no trace of itself in the
> project structure.
>
> The migration preserves the project's existing wiring style: a Spring Boot
> project stays on Spring auto-config (recipes use `@Component` / `@Bean`
> idioms); a plain framework-configuration project stays on the direct
> `Configurer` API (recipes use `EventSourcingConfigurer` /
> `MessagingConfigurer` / `CommandHandlingModule` / `EventSourcedEntityModule`).
> Wiring style is decided once at INIT and pinned — no recipe re-asks.

### 🚨 Data migration & SQL are out of scope — code only

This skill rewrites **code**: bean wiring, imports, annotations, handler
shapes, test fixtures, processor config. Nothing else.

It does **NOT**:

- emit, run, or curate any SQL / DDL / schema-migration script
  (no `domain_event_entry` → `aggregate_event_entry` rename DDL, no
  token-store schema, no DLQ schema);
- copy or transform event-store rows between stores (Mongo → AS,
  Mongo → relational, JDBC → JPA, …);
- copy or rebuild token-store rows;
- delete, rewrite, or re-read existing snapshot rows;
- export, import, or replay any persisted state.

Every `move-to-*` option in any recipe's `not-supported.md` is a
**code-rewrite choice**, not a data-migration offer. The user owns and
runs every schema change and data move out-of-band, on a non-prod copy
first, with row counts verified. If the user has not planned a data
move, recipes must prefer `pause-migration` / `accept-stays-af4` over
a `move-to-*` path.

Intermediate phases may leave the project non-compiling — by design.
Per-target `isolated-<TargetName>` scopes (Maven profiles or Gradle
source sets, depending on the project's build tool) keep verification
scoped to one migrated item — atomic, parallelizable, individually
removable. Scope creation, augmentation, and cleanup are delegated to
the installed external skill **`axon4to5-isolatedtest`** — every recipe
invokes it (Skill tool) with `target-name`, the `main-sources` /
`test-sources` lists, optional `extra-deps`, and `cleanup` (false while
iterating; true on the recipe's last successful verify). See
[references/verification.md](references/verification.md) for the call
pattern. This skill does NOT carry its own per-target build-scoping
mechanics anymore.

## Routing table

Single source of truth for: phase order, per-recipe discovery, single-file
auto-routing, INIT detection of unsupported features.

### Column key

| Column | Purpose |
|---|---|
| **Recipe** | Folder name under `references/`. Also the recipe id used in commit bodies. |
| **Mode** | `iterative` (one item at a time) · `one-shot` (no item iteration) · `not-supported` (stop and message) · `triage` (top-level mode, not a phase) · `utility` (invoked transitively) |
| **Phase** | Migration phase number `1–9`, or `n/a` for non-phase rows |
| **Discovery** | Grep pattern used to find candidates. `n/a` for one-shot or non-phase rows. |
| **Condition** | Plain-language predicate — "when does this recipe apply?" |
| **Notes** | Per-recipe extras: `exclude-when` greps, sub-paths, license-decision, the `not-supported-message`, keyword aliases, file-include globs. Free-form. |

### Table

| Recipe | Mode | Phase | Discovery (grep) | Condition | Notes |
|---|---|---|---|---|---|
| `openrewrite` | one-shot | 1 | n/a | Target depends on `org.axonframework.*` and not yet on AF5 BOM | Delegates to installed external skill `axon4to5-openrewrite`. License decision (free-af5 / axoniq) → `--framework axon|axoniq`. Aliases: openrewrite, recipes, bulk. |
| `aggregate` | iterative | 2 | `@Aggregate\b\|@AggregateRoot\b` (`*.java`, `*.kt`) | Class with `@Aggregate`/`@AggregateRoot` AND `@EventSourcingHandler` methods | Variant detection in Procedure: simple / multi-entity / polymorphic. Aliases: aggregate, event-sourced-aggregate, entity. |
| `event-processor` | iterative | 3 | `@ProcessingGroup\|org\.axonframework\.eventhandling\.EventHandler` | Class with `@EventHandler` methods (typically `@ProcessingGroup`) | Aliases: event-processor, eventhandler, projector, projection. |
| `command-gateway` | iterative | 4 | `org\.axonframework\.commandhandling\.gateway\.CommandGateway` | Top-of-chain caller injecting `CommandGateway`, NOT a message handler | exclude-when: `@EventHandler\|@CommandHandler\|@QueryHandler\|@MessageHandlerInterceptor`. Three return-shape paths (MVC / scheduler / reactive). Aliases: command-gateway, commanddispatch, controller-command. |
| `query-gateway` | iterative | 5 | `org\.axonframework\.queryhandling\.QueryGateway` | Top-of-chain caller injecting `QueryGateway`, NOT a message handler | exclude-when: `@EventHandler\|@CommandHandler\|@QueryHandler`. Aliases: query-gateway, controller-query. |
| `query-handler` | iterative | 6 | `org\.axonframework\.queryhandling\.QueryHandler` | Class with `@QueryHandler` methods | Aliases: query-handler, queryhandler. |
| `interceptors` | iterative | 7 | `implements\s+MessageDispatchInterceptor\b\|implements\s+MessageHandlerInterceptor\b` (`*.java`, `*.kt`) | Class that implements one of the AF4 interceptor SPIs and is NOT itself a message handler | Two variants in Procedure: dispatch / handler / both. Path B also touches `register*Interceptor` registration sites on `MessagingConfigurer`. exclude-when: `@CommandHandler\|@EventHandler\|@QueryHandler` on the same class (those classes belong to their handler recipe). Aliases: interceptors, interceptor, message-interceptor, handler-interceptor, dispatch-interceptor. |
| `event-storage-engine` | one-shot | 8 | n/a (one-shot bean swap) | Project declares `EventStorageEngine` / `EmbeddedEventStore` / `AxonServerEventStore` bean (Path A) or registers one via `componentRegistry.registerComponent(EventStorageEngine.class, ...)` (Path B). The same one-shot run also dispatches into [configuration.md](references/event-storage-engine/configuration.md) for `eventStore()` / `eventBus()` reads AND generic write-side shape changes (`@Bean ConfigurerModule` for non-Axon components, `DefaultConfigurer.defaultConfiguration()`, free-standing lifecycle hooks, `Lifecycle` interface, generic `registerComponent`). | Wiring path comes from inputs.wiring (A=Spring Boot / B=framework Configurer); backend (JPA / Axon Server) chosen from inspection. Aliases: event-storage-engine, storage-engine, eventstore, configuration, configuration-class, readconfig, writeconfig, configurer, configurer-module. |
| `saga` | not-supported | n/a | `@Saga\b\|@SagaEventHandler\|@StartSaga\|@EndSaga\|SagaConfigurer` | Project uses AF4 sagas | Detected at INIT, decided per saga. Recipe surfaces a four-way decision: `migrate-to-event-handler-with-state` (worked example inside the recipe — only when no `@DeadlineHandler` and association mechanics are simple), `accept-stays-af4`, `pause-migration`, `remove-feature-first`. Sagas with deadlines are blocked from the migrate path — own scheduler / wait for Axoniq Workflows / contact Axoniq. |
| `debug` | triage | n/a | n/a (driven by build errors) | Build failing without any `isolated-*` scope active, or alternative to phased order | Top-level mode, NOT a phase. Routes clusters to other recipes — sibling-link exemption applies. Aliases: debug, triage, compile-errors. |

> **Per-target build scoping is delegated to the installed external skill `axon4to5-isolatedtest`.** Every iterative recipe invokes it transitively to seed/extend an `isolated-<TargetName>` Maven profile or Gradle source-set. This skill no longer has a `verify-in-isolation` recipe row — see [references/verification.md](references/verification.md) for the call pattern.

Adding a phase = appending one row with the next `Phase` integer + a recipe
folder. Adding an unsupported-feature stop = appending a `not-supported` row.

### Single-file routing (auto-assign recipe)

User passes a file path or FQ class. Orchestrator does NOT ask "which
recipe?" — it inspects the file and matches the routing table:

```
1. content = read(file)
2. for each row where Mode in {iterative, one-shot}, sorted by Phase ascending:
     - if row.Discovery matches content
       AND row.Notes.exclude-when does NOT match → row wins
3. if multiple match (e.g. event-storage-engine class also reads `eventProcessor`):
     - pick the row with the lowest Phase
     - ask user via AskUserQuestion only if user wants to override
```

User says **what** to migrate (the file). The skill picks **how** via the table.

## Docs routing table — canonical migration guide per recipe

Recipes hold the **mechanical procedure** (find/replace, scoped verify, AskUserQuestion flows). The **canonical explanation** of each AF4 → AF5 shift — concepts, full FQN tables, before/after code samples, design rationale — lives once under `docs/paths/`. When a recipe needs to remind itself of "why" or show a worked code shape, it MUST read from this table and link to the doc rather than re-explain.

Every recipe SHOULD start with a `## Canonical reference` block listing the rows from this table that apply to it. The orchestrator does NOT pre-load these docs; each recipe pulls in only what it needs at run time.

Source of truth for the prose / examples. Recipes MUST NOT duplicate.

| Topic | Canonical doc | Used by recipes |
|---|---|---|
| **Base import / package changes (all renames, all modules, BOM)** | [docs/paths/index.adoc](docs/paths/index.adoc) | `openrewrite` (drives renames); every other recipe touches imports |
| **What is NOT in AF5 yet (sagas, upcasters, replay, kafka, …)** | [docs/paths/index.adoc](docs/paths/index.adoc) §"What is not yet there" | INIT detection; `saga`; per-recipe `not-supported.md` |
| **Architecture principles ("why" of AF5)** | [docs/understanding-architecture-principles.adoc](docs/understanding-architecture-principles.adoc) | When user asks "why X changed"; cross-linked from `aggregate`, `event-processor` |
| **Application design problems solved** | [docs/solved-architecture-choices.adoc](docs/solved-architecture-choices.adoc) | "Why ThreadLocal removed", "Why DCB", checkpoints when user pushes back |
| **Why upgrade at all** | [docs/why-upgrade.adoc](docs/why-upgrade.adoc) | INIT preamble when user is undecided |
| **Prerequisites (JDK, Spring Boot, Axon Server versions)** | [docs/prerequisites.adoc](docs/prerequisites.adoc) | INIT preflight (read once before `ensure_pinned()` so the recommended-license reason can cite version constraints) |
| **Message annotation moves (`@TargetEntityId`, `@Event`, `@Command`, `@Revision` → `version`, `@RoutingKey` → `routingKey`)** | [docs/paths/messages.adoc](docs/paths/messages.adoc) | `aggregate` (Steps 3–7), `command-gateway`, `query-gateway`, `query-handler`, `openrewrite` |
| **Aggregate → `EventSourcedEntity` core concepts** (`@EventSourcedEntity`, `@EventSourced`, `@EntityCreator`, `EventAppender`, `@EventTag`, removal of `@CreationPolicy`, simple GiftCard example) | [docs/paths/aggregates/index.adoc](docs/paths/aggregates/index.adoc) | `aggregate` (Goal, Steps 5–13) |
| **Multi-entity (`@AggregateMember` → `@EntityMember`)** | [docs/paths/aggregates/multi-entity-migration.adoc](docs/paths/aggregates/multi-entity-migration.adoc) | `aggregate` (multi-entity variant) |
| **Polymorphic entities (`concreteTypes`, inherited handlers)** | [docs/paths/aggregates/polymorphism-migration.adoc](docs/paths/aggregates/polymorphism-migration.adoc) | `aggregate` (polymorphic variant) |
| **Entity / aggregate Configurer registration (`EventSourcedEntityModule.autodetected(...)`)** | [docs/paths/aggregates/configuration-migration.adoc](docs/paths/aggregates/configuration-migration.adoc) | `aggregate` Path B |
| **Event store choice** (which `EventStorageEngine`, DCB vs aggregate-based, `LegacyJpaEventStorageEngine`) | [docs/paths/event-store.adoc](docs/paths/event-store.adoc) | `event-storage-engine` |
| **Snapshot model (5.1: `SnapshotPolicy` on `EventSourcedEntityModule`, removal of `SnapshotTriggerDefinition`)** | [docs/paths/snapshotting.adoc](docs/paths/snapshotting.adoc) | `aggregate` (`not-supported.md` B1 decision), `event-storage-engine` |
| **Serializer → Converter (`JacksonConverter`, removal of `XStreamSerializer`)** | [docs/paths/serializers.adoc](docs/paths/serializers.adoc) | `event-storage-engine` |
| **Event processor model** (`@ProcessingGroup` → `@Namespace`, `PooledStreamingEventProcessor`, removal of `TrackingEventProcessor`, `QueryUpdateEmitter` as parameter, `EventProcessorDefinition` Spring bean, `EventProcessorSettings`) | [docs/paths/projectors-event-processors.adoc](docs/paths/projectors-event-processors.adoc) | `event-processor` |
| **Sequencing policies (`@SequencingPolicy` on class, AF4 → AF5 policy classes)** | [docs/paths/sequencing-policies.adoc](docs/paths/sequencing-policies.adoc) | `event-processor` Step 7 |
| **Dead-Letter Queue (schema change, per-component scoping, no MongoDB)** | [docs/paths/dlq.adoc](docs/paths/dlq.adoc) | `event-processor` Step 2 sweep (flag-only); commercial recipe owns the bean swap |
| **Test fixtures (`AggregateTestFixture` / `SagaTestFixture` → `AxonTestFixture`, fluent API)** | [docs/paths/test-fixtures.adoc](docs/paths/test-fixtures.adoc) | `aggregate` (Test fixture migration T.1–T.5) |
| **Interceptors (interface rewrite, registration, Spring auto-discovery)** | [docs/paths/interceptors.adoc](docs/paths/interceptors.adoc) | `interceptors` (primary owner — interface rewrite + Path B registration sites); `event-processor`, `command-gateway`, `query-handler` keep one-liner pointers for the edge case where an interceptor lives on the same class as a handler |
| **Configuration migration (`Configurer` → `MessagingConfigurer` / `ModellingConfigurer` / `EventSourcingConfigurer`, `ConfigurerModule` → `ConfigurationEnhancer`, lifecycle, component registration)** | [docs/paths/configuration.adoc](docs/paths/configuration.adoc) | `event-storage-engine` ([configuration.md](references/event-storage-engine/configuration.md) — bootstrap-layer reads + generic writes); per-topic reads in [event-processor/configuration-reads.md](references/event-processor/configuration-reads.md), [command-gateway/configuration-reads.md](references/command-gateway/configuration-reads.md), [query-gateway/configuration-reads.md](references/query-gateway/configuration-reads.md) |

**Routing rule for recipes**: when a recipe step would otherwise explain a concept, drop a one-line pointer to the doc instead. Recipes keep only:

- mechanical edit steps (concrete find/replace, import swaps, scoped grep);
- the AskUserQuestion flow (and its `not-supported.md` blockers);
- scoped verify invocations (delegated to external `axon4to5-isolatedtest`);
- Path A vs Path B selection logic that is recipe-specific;
- short "binding rule" notes that exist only because of how the recipe is invoked (e.g. the `@Namespace("<n>")` string must equal the `pooledStreamingMatching("<n>")` call — only meaningful at execution time).

Forbidden in recipes (lint-enforced — see "Forbidden in any recipe" below):
- full FQN tables that already live in [docs/paths/index.adoc](docs/paths/index.adoc) (Slim cheatsheets pointing at the doc are fine);
- side-by-side AF4-vs-AF5 code samples that exist verbatim in a doc;
- conceptual "why this changed" paragraphs;
- repeated "What is not yet there" lists.

When a doc is missing the example a recipe needs, prefer **adding it to the doc** and pointing the recipe at it, rather than duplicating it in the recipe.

## Recipe interface contract

Every `references/<recipe>/<recipe>.md` MUST declare these five sections,
parsed by heading. Order is flexible — orchestrator parses by heading
match, not position. The template below shows one common arrangement
(End condition / Output near the top works as a contract header before
the steps; near the bottom works as a closer after the steps):

```
# Recipe: <name>

## Canonical reference
- [docs/paths/<topic>.adoc](docs/paths/<topic>.adoc) — concepts, full FQN tables, before/after examples
- (additional doc(s) if the recipe spans multiple topics — see SKILL.md docs routing table)

## Inputs
- target: <FQ class | file path | none>  (required | optional)
- wiring: "spring-boot" | "framework-config"  (required, supplied by orchestrator from progress.md Pinned-decisions)
- <other recipe-specific args, each typed and required/optional flagged>

## Preflight
- quick "already migrated?" check → return Output with `result: skipped`

## Procedure
- main flow as numbered pseudo-code; conditions explicit, parameters typed
- references each ### Path subsection by condition

### Path A — Spring Boot
#### Condition
- inputs.wiring == "spring-boot"
#### Steps
- pseudo-code: numbered, conditions explicit, parameters typed
- uses Spring idioms: @Component / @Bean / @Configuration, application.yml,
  Spring auto-configuration backing off when user beans are declared.

### Path B — framework Configurer
#### Condition
- inputs.wiring == "framework-config"
#### Steps
- pseudo-code: numbered, conditions explicit, parameters typed
- uses the AF5 builder API directly: EventSourcingConfigurer.create() /
  MessagingConfigurer.create(), CommandHandlingModule,
  QueryHandlingModule, EventSourcedEntityModule, eventProcessing(...).

## End condition
- objective, machine-checkable

## Output
- (YAML block — see "Output contract — six variants" below for the canonical schema)
```

Recipe MUST emit **exactly one** `result:` value. See **Output contract — six variants** below for the canonical schema, per-variant invariants, and worked examples.

Optional sections recipes may keep: `## Goal`, `## In scope` / `## Out of
scope`, `## FQN cheat sheet`, `## Caveats`, `## Examples`, `## Reference
index` (links INTO the recipe's own folder only).

### Output contract — six variants

Every recipe Output is a union with discriminator `result:`. The orchestrator branches on `result:` alone — never on `needs-user-decision` or `recipe-status` (legacy fields, removed). Variants are mutually exclusive.

| `result:` | Meaning | `caller-expects.commit` | `caller-expects.next` |
|---|---|---|---|
| `success` | All `## End condition` checks passed. Code rewritten, scoped verify green. | `true` | `proceed` |
| `skipped` | Preflight found the target is already on AF5 (idempotent re-run). No edits. | `false` | `proceed` |
| `rejected` | Routing was wrong: target doesn't match the recipe's domain. No edits. | `false` | `proceed` or `route-to:<recipe>` |
| `needs-decision` | A choice must be made by a human (`AskUserQuestion` flow from `not-supported.md`, ambiguous wiring, …). MUST bubble up — never resolved inside a subagent. | `false` | `ask-user` |
| `blocked` | A hard AF5 gap with no recipe-internal recovery (`@DeadlineHandler` without Workflows, Mongo event store with no `move-to-*` chosen). Partial edits MAY be committed; the blocking surface is commented-out with a `TODO[AF5 migration: <key>]` marker per Anti-patterns. | `true` (when blocker key + TODO marker exist) / `false` (when nothing was edited) | `record-and-skip` |
| `failed` | Recipe started but ended in a state it can't classify (external tool non-zero exit with rollback, scoped verify red, edit conflict). | `false` | `halt` |

**Required fields per variant**

| Field | success | skipped | rejected | needs-decision | blocked | failed |
|---|---|---|---|---|---|---|
| `result` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `target` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `reason` | optional | required | required | required | required | required |
| `decisions` | required (recipe-specific keys) | `{}` | `{}` | partial — record what is known | required (must include the `not-supported.md` blocker key) | optional |
| `caller-expects.commit` | `true` | `false` | `false` | `false` | `true` or `false` | `false` |
| `caller-expects.next` | `proceed` | `proceed` | `proceed` \| `route-to:<recipe>` | `ask-user` | `record-and-skip` | `halt` |
| `notes` | optional | optional | optional | optional — list the verbatim AskUserQuestion options | optional | recommend `debug` mode or surface verbatim tool output |

**Why six and not four**

- `skipped` ≠ `rejected`: same caller action today, but distinguishing them lets `debug` mode catch routing-table bugs (`rejected` means the routing table sent the wrong recipe; `skipped` means it sent the right one but nothing's left to do).
- `blocked` ≠ `failed`: a blocker is an *expected* AF5 gap with a known commented-out shape and a `not-supported.md` key. A failure is *unexpected* — the recipe doesn't know what's wrong. Caller actions differ: `record-and-skip` (proceed with other items) vs `halt` (stop the run).
- `needs-decision` ≠ `blocked`: `needs-decision` pauses to ask a question the recipe doesn't yet know the answer to; `blocked` is the post-answer state where the resolution was "no AF5 path".

**Orchestrator classify()**

```
classify(output) = output.result          # one field, six outcomes
```

No multi-field walk. Recipe contract requires `result:` to be one of the six values; orchestrator HALTs on any other value (defensive — schema violation, not a user-facing error).

### Optional `not-supported.md` sibling file

Recipes that have AF5-blocking inputs (no portable target, missing AF5
release, removed SPI) put detection + `AskUserQuestion` flows in a
sibling `references/<recipe>/not-supported.md`. Each blocker entry gives:

- **Why blocker** — one paragraph.
- **Detection** — exact grep / inspection.
- **AskUserQuestion** — verbatim option labels.
- **Output decision key** — added to the recipe's Output `decisions`.
- **Effect on Procedure** — proceed / redirect path / exit with `result: needs-decision` or `result: blocked` (per the variant table in "Output contract — six variants").

When a `not-supported.md` exists, the recipe's `## Preflight` MUST list
"Read [not-supported.md] first — run every Detection grep" as its first
step. Recipe must NOT proceed past Preflight while a blocker is
unresolved. The orchestrator records each `decisions.<key>` from the
recipe's Output exactly as the recipe emits it.

This pattern replaces former top-level `not-supported`-mode rows in the
routing table for blockers that are scoped to a specific recipe (e.g.
Mongo on `event-storage-engine` / `event-processor`, snapshotting on
`aggregate`). Top-level `not-supported` rows stay only for project-wide
features detected at INIT (e.g. `saga`).

### Optional `## Subagent guidelines`

Declares how the orchestrator should spawn a subagent for this recipe. If
absent, the orchestrator uses the default (`general-purpose`, no isolation,
no framing). Shape:

```
## Subagent guidelines

- subagent_type: <general-purpose | Explore | Plan | claude-code-guide>
  # which subagent the orchestrator passes to the Agent tool

- isolation: <none | worktree>
  # use "worktree" for broad sweeping edits with easy rollback

- prompt-framing: |
  # paragraph(s) the orchestrator prepends to the recipe-execution prompt

- parallelism: <single | per-item>
  # "per-item" lets the orchestrator fan out one subagent per discovered candidate
```

The orchestrator NEVER invents subagent types not listed in the available
agents — `general-purpose` is the safe default.

### Forbidden in any recipe (lint enforced)

- migration-phase numbering in any free-form ("phase 1", "Phase 2",
  "(phase 9)") — except the explicit form **"Migration Phase #N"**
- references to sibling recipes (no `../command-gateway/…`)
- references to `progress.md` / `learnings.md` / `index.md` / orchestrator
  semantics
- duplication of canonical-doc content: full FQN tables already in
  [docs/paths/index.adoc](docs/paths/index.adoc), AF4-vs-AF5 side-by-side
  code samples already in the matching `docs/paths/*.adoc`, conceptual
  "why this changed" paragraphs. Use a one-line `[docs/paths/…](…)` pointer
  instead. See the **Docs routing table** above for the canonical doc per
  recipe.
- `## Output` MUST emit a fenced ```yaml block with a single `result:`
  field, where `result:` is exactly one of
  `success | skipped | rejected | needs-decision | blocked | failed`.
  Legacy fields (`needs-user-decision`, `needs-user-decision-reason`,
  `recipe-status`, `skip`) are forbidden — fold their semantics into
  `result:` + `decisions:` + `reason:` per the Output contract.

The framework class `org.axonframework.common.lifecycle.Phase` is
exempt — recipes refer to it as `Phase.<NAME>` or via FQN, never as a
migration phase number.

The `debug` recipe is **exempt from the no-sibling-links rule** — its
routing IS its job. The external `axon4to5-isolatedtest` skill is the
canonical owner of per-target build scoping; recipes invoke it via the
Skill tool (or host equivalent) rather than linking sideways.

## Procedure form (pseudo-code with explicit conditions)

Every recipe's `## Procedure` is the **main flow**. Branches go to `### Path
A / B / …` subsections, each gated by a `#### Condition`. The procedure is
concise pseudo-code:

```
## Procedure

1. Locate target.
   - if Inputs.target set → use it
   - else → first match of <discovery grep>
2. Detect variant.
   - has @AggregateMember field? → variant=multi-entity
   - has subclass annotated @Aggregate? → variant=polymorphic
   - else → variant=simple
3. Run class-level transformation (steps 3a–3n below).
4. Pick path from pinned `wiring` decision (recipes do NOT re-detect):
   - inputs.wiring == "spring-boot"      → Path A (Spring Boot)
   - inputs.wiring == "framework-config" → Path B (framework Configurer)
5. Run path Steps (see ### Path A / ### Path B).
6. Run test fixture migration if test class exists.
7. Verify against ## End condition.
8. Emit ## Output.
```

## Source of truth = progress.md

State lives in `<target>/.axon4to5-migration/progress.md`. The
orchestrator reads it on every invocation, rewrites the relevant sections
before every commit, and stages it together with the code change. A fresh
session must be able to resume from this file alone.

Conventional commit messages — no structured body block. See
[references/commit-cadence.md](references/commit-cadence.md) for the full
subject-line table and [assets/commit-message-template.md](assets/commit-message-template.md)
for the template.

### Persistence invariant

Every state change ends with: **`progress.md` rewritten + commit including
it**. Never mutate the working tree without a corresponding `progress.md`
update in the same commit.

### Persistence checklist (run before every commit)

- [ ] **▶︎ RESUME HERE** points at the *next* unit (not the one just done).
      Has Next action, exact recipe, exact verify command.
- [ ] **Phase status table** row updated: `Items done / total`, `Last commit`.
- [ ] **Per-phase plan table** row for just-finished item: status `done`
      (or `blocked` / `deferred-to-stabilization`), commit SHA.
- [ ] If non-obvious lesson: `learnings.md` has new dated entry.
- [ ] If any AF4 bean / registration / fixture call was **commented out**
      (rather than migrated) in this commit, the relevant `not-supported.md`
      blocker key (e.g. `B5`) is cited in the commit message body AND in
      a fresh `learnings.md` entry. Silent deletion of unsupported surfaces
      is forbidden — see Anti-patterns.

A fresh session reading `progress.md` after this commit must pick up the next
action with NO clarifying questions about state.

### Resume protocol

When `progress.md` exists:

1. Read it top-to-bottom. **▶︎ RESUME HERE** block tells the exact next move.
2. Sanity-check working tree:
   ```bash
   git -C <target> rev-parse --short HEAD
   git -C <target> status --porcelain
   ```
   - HEAD matches recorded last commit + tree clean → proceed.
   - HEAD ahead (user committed manually) → surface, trust user.
   - Tree dirty → previous session crashed. AskUserQuestion: inspect diff /
     reset to last commit (destructive — only with explicit user OK) /
     continue from dirty (treat in-progress edits as yours to finish).
3. Read **Pinned user decisions** block — license target, commit cadence,
   storage path, unsupported-feature acceptance — already answered. Do **NOT**
   re-prompt.
4. Read `learnings.md` only on demand (full file may not fit in context for
   long-running migrations — pull entries when relevant).
5. Confirm in 1–2 sentences with user via AskUserQuestion ("Resuming at
   phase X. Next: Y. Continue?").
6. Trust `progress.md`. If user says it's wrong, fix together, commit fix,
   then continue.

### Mid-phase dirty tree (user WIP detected)

If `git status --porcelain` shows files the orchestrator did NOT touch
(user-side WIP that crept in), pause and AskUserQuestion:

- `Stage and commit only the migration files I touched` *(Recommended)* —
  `git add` with explicit paths.
- `Let me handle the working tree first` — pause, let user clean up, resume.
- `Skip this commit` — record skip in `progress.md`, continue without committing.

Don't silently sweep user WIP into a migration commit.

### Encourage `/clear` between units

After every commit on a non-trivial unit (the whole of Migration Phase #1,
every 2–3 migrated items, or anything large):

> "Committed `<sha>`. Working tree clean, `progress.md` up to date. Safe
> point to `/clear` if you'd like — when you come back, just invoke this
> skill again and I'll resume."

Phase boundaries especially. Don't insist; user decides.

## State directory — `<target>/.axon4to5-migration/`

```
<target>/.axon4to5-migration/
├── index.md       # short README — points at progress.md and learnings.md.
├── progress.md    # SINGLE SOURCE OF TRUTH for migration state.
│                  #   Rewritten before every commit, committed with the code.
│                  #   Sections: Goal / ▶︎ RESUME HERE / Pinned decisions /
│                  #             Phase status / Per-phase plan.
└── learnings.md   # Append-only narrative. Surprises, manual fixes, decisions.
```

Templates: [assets/index-template.md](assets/index-template.md),
[assets/progress-template.md](assets/progress-template.md),
[assets/learnings-template.md](assets/learnings-template.md).

`.axon4to5-migration/` is committed alongside the migration changes —
every migration commit includes a `progress.md` rewrite.

## Orchestrator pseudocode

Three modes (`phased` / `single` / `debug`) all funnel into ONE inner loop:
**pick items → run recipe → classify output → commit**. Mode-specific code
just decides *where the items come from*. Output schema is unchanged — the
unification is an orchestrator-internal `classify()` helper.

### Entry

```
ORCHESTRATE:
  mode   = parse($ARGUMENTS)               # phased | single | debug
  target = resolve_and_validate(...)       # exists; has pom.xml/build.gradle;
                                           # git repo; not AxonFramework itself
  dispatch:  single → SINGLE   debug → DEBUG   phased → PHASED   (default)
```

Ambiguous `$ARGUMENTS` → AskUserQuestion then re-dispatch. Never auto-pick
"phased" when the user clearly named a file but the path is wrong — surface
the error.

### Three modes — each is a thin wrapper around the inner loop

```
PHASED:
  if no progress.md           → INIT
  read progress.md; handle dirty tree (Resume protocol); confirm with user
  for each routing-table row in {iterative, one-shot} not yet done:
    items = (row.Mode == one-shot) ? [None] : discover(row.Discovery)
    items -= State.deferred_or_unsupported
    PROCESS_ITEMS(row, items)
    AskUserQuestion: continue / pause / stop
  FINALIZE

SINGLE:
  row = route(arg) via routing table        # auto — no user prompt
  ensure_pinned()                           # license, wiring, build-tool —
                                            # full INIT first run, else
                                            # ensure_pinned() block only
                                            # (NEVER skip the license prompt)
  PROCESS_ITEMS(row, [arg])
  suggest /clear, STOP

DEBUG:
  repeat until green or stopped:
    compile (no scope active)
    (row, item) = route(highest-leverage cluster)   # see references/debug
    PROCESS_ITEMS(row, [item])
    if compile output unchanged → AskUserQuestion: surface/skip-defer/stop
```

### Inner loop — PROCESS_ITEMS, handle, classify

```
PROCESS_ITEMS(row, items):
  par = subagent_guidelines(row.Recipe).parallelism      # default: single

  if par == per-item AND |items| >= 2 AND mode != single:
    plans = fan_out_readonly(items)                      # parallel subagents;
                                                         # MUST NOT edit/commit
    for plan in plans (in items order):
      apply plan to working tree; run scoped verify
      handle(plan.output)
  else:
    for item in items:
      output = EXECUTE_RECIPE(row.Recipe, build_inputs(item, row))
      handle(output)

handle(output):
  switch classify(output):                                  # discriminator: output.result
    success         → commit code + progress.md (per-item conventional);
                      suggest /clear; next
    skipped         → no commit; next                       # already migrated
    rejected        → no commit; if next == route-to:<recipe>
                      re-route via routing table; else next
    needs-decision  → AskUserQuestion using output.notes options:
                        fix   → re-run EXECUTE_RECIPE (same inputs + pinned answer)
                        defer → record decision; commit progress.md only; next
                        stop  → HALT
    blocked         → if output.caller-expects.commit == true
                        commit code + progress.md (comment-out + TODO marker)
                      else
                        commit progress.md only
                      record blocker key in Pinned-decisions; next
    failed          → surface output.reason + output.notes verbatim;
                      AskUserQuestion: hand-off-to-debug-mode / pause / stop
                      no commit of partial work.

classify(output):                            # one place, six outcomes
  return output.result                       # must be one of:
                                             #   success | skipped | rejected
                                             #   needs-decision | blocked | failed
                                             # any other value → orchestrator HALT
                                             # (schema violation)
```

`commit` here means: stage explicit paths only (touched code + progress.md +
learnings.md if dirty), conventional message. **Never** `git add -A`, push,
amend, `--no-verify`, or commit on `main`/`master`.

### EXECUTE_RECIPE (subroutine)

```
EXECUTE_RECIPE(recipe, inputs):
  validate inputs against recipe ## Inputs        # wiring + build-tool
                                                  # always pinned, never re-detected
  run recipe ## Preflight                         # already-migrated → result: skipped
  run recipe ## Procedure                         # subagent if recipe declares
                                                  # ## Subagent guidelines AND its
                                                  # Procedure does NOT use
                                                  # AskUserQuestion; else inline.
                                                  # Inline fallback recorded only
                                                  # in Output.notes.
  verify recipe ## End condition                  # green → result: success
                                                  # red   → result: failed
                                                  #         (or blocked if mapped to
                                                  #          a not-supported.md key)
  return Output
```

Subagent prompt template: prepend recipe's `prompt-framing`, then:
*"Read references/&lt;recipe&gt;/&lt;recipe&gt;.md, execute its ## Procedure.
Inputs: &lt;serialized&gt;. Return a filled ## Output block. Do NOT commit —
the orchestrator owns commits."* Subagent_type defaults to `general-purpose`.

### INIT (one-time, at first PHASED run)

```
INIT:
  mkdir -p <target>/.axon4to5-migration/
  seed index.md, progress.md, learnings.md from assets/*-template.md

  ensure_pinned()              # ALWAYS — license first, then wiring, then build-tool.
                               # No exit path skips any of these three.

  for each row.Mode == not-supported with discovery hits:
    AskUserQuestion: accept-stays-af4 / pause / remove-feature-first
    record decision in Pinned-decisions; narrative line to learnings.md

  commit "chore(af5-migration): initialize migration"

ensure_pinned():               # called from INIT AND from SINGLE mini-INIT
  if not pinned("license"):    # MANDATORY — orchestrator MUST NOT proceed
                               # past this step without an answer; openrewrite
                               # and several not-supported branches read it.
    rec = recommend_license()
    AskUserQuestion ONCE with recommended option first:
      - "{rec} (Recommended) — {rec_reason}"
      - the other option
    pin("license", answer)     # free-af5 | axoniq-commercial

  if not pinned("wiring"):
    detect_wiring():           # spring-boot | framework-config
      grep build files for axon[-iq]-spring-boot-starter           → spring-boot
      else @SpringBootApplication OR (@Configuration + @Bean of    → spring-boot
           org.axonframework.* type)
      else DefaultConfigurer.defaultConfiguration( OR              → framework-config
           direct org.axonframework.config.Configurer use
      else ambiguous → AskUserQuestion ONCE
    pin("wiring", value)

  if not pinned("build-tool"):
    detect_build_tool():       # maven | gradle
      pom.xml only            → maven
      build.gradle* only      → gradle
      both                    → AskUserQuestion ONCE
      neither                 → HALT
    pin("build-tool", value)

recommend_license():           # signals → suggested option + one-line reason
  if any of:
    - dependency on axon-{mongo,kafka,amqp,tracing-opentelemetry}
    - dependency on any org.axoniq.* artifact (Axon Server EE, AxonIQ Console,
      Axoniq Workflows)
    - project uses @Saga / upcasters / replay / DLQ on Mongo
      (features not yet in free AF5 — see docs/paths/index.adoc
       §"What is not yet there")
  → return ("axoniq-commercial",
            "your project depends on features not in free AF5 yet")
  else
  → return ("free-af5",
            "no commercial-only deps detected; free AF5 covers your stack")
```

Pinned decisions live in `progress.md` Pinned-decisions block in a fixed
order: **license → wiring → build-tool → not-supported decisions**. Recipes
read them; they NEVER re-detect, NEVER re-prompt. `ensure_pinned()` is the
single entry point for INIT *and* SINGLE mini-INIT — there is no path that
runs a recipe without `license` being answered first.

### FINALIZE (one-time, after every routing-table row is done)

```
FINALIZE:
  for each target with an isolated-<X> scope:                # recorded in
    invoke axon4to5-isolatedtest with cleanup: true          # progress.md
                                                             # per-phase plan
  promote AF5 deps from cleaned scopes into main deps:
    - dedupe extra-deps lists across targets
    - splice into main pom(s) / build.gradle(.kts) (each touched module)
    - promote any surviving ${axon5.version} to a top-level property
    - delete activation refs in scripts/CI/docs
      ('-P isolated-' for Maven, ':testIsolated' for Gradle)

  full build (NO scope active):
    maven  → ./mvnw clean verify
    gradle → ./gradlew clean build

  if red, classify failure:                                  # ONE 3-way
    traceable to a recipe      → reopen that phase; re-enter PHASE loop;
                                 FINALIZE re-runs once green
    missed dep promotion       → diff scope dep blocks; fix main deps; retry
    env / infra (untraceable)  → AskUserQuestion: investigate/pause/stop

  update progress.md: every row done; RESUME HERE = "Migration complete"
  single commit "chore(af5-migration): remove isolated-* scaffolding"
  tell user; recommend /clear
```

One commit per item / phase / finalize — explicit paths only, conventional
message. The `axon4to5-isolatedtest` skill owns scope creation and removal;
this orchestrator never hand-crafts `-P isolated-` or `:testIsolated`
invocations.

## Commit & verification

- Commit cadence rules: [references/commit-cadence.md](references/commit-cadence.md).
- Commit message template: [assets/commit-message-template.md](assets/commit-message-template.md).
- Verification rules (mvn flags, multi-module reactor, scoped vs full):
  [references/verification.md](references/verification.md).

One commit per item. Stage explicit paths only. Never push, amend, or
`--no-verify`. Commit on the user's current branch — never on `main` /
`master`.

## Anti-patterns — don't

- Skipping the human checkpoint between phases.
- Running `mvn verify` after Migration Phase #1 (it WILL fail — expected
  until stabilization).
- Letting `progress.md` drift behind reality. Always rewrite the relevant
  section, then commit code + `progress.md` together — never split work and
  bookkeeping across commits.
- Re-running OpenRewrite to "fix" what a per-construct recipe couldn't
  handle.
- **Silently deleting an AF4 bean / Configurer call / registration / fixture
  call whose AF5 successor is missing, deferred, or pinned by a
  `not-supported.md` blocker.** Comment it out instead, leave a
  `// TODO[AF5 migration]` marker that cites the blocker key (e.g. `B5`),
  and record the decision in `progress.md` Pinned-decisions + a
  `learnings.md` entry. Deletion loses the AF4 wiring shape (so the day
  the AF5 successor lands nobody knows what to restore) and erases the
  audit trail. The most common offenders: `@Bean DeadlineManager`,
  `EventProcessingConfigurer.registerPooledStreamingEventProcessor(...)`
  (the rewrite to `@Bean EventProcessorDefinition` is mandatory, not
  optional), and AF4 `Matchers.*` calls in test fixtures.
- **Treating `event-storage-engine` as "auto-configured by the Spring Boot
  starter, no action needed".** The AF5 starter applies AF5 defaults
  (DCB-flat / `JpaEventStorageEngine`), NOT a migration of the existing
  AF4 event store. The explicit `AggregateBased…EventStorageEngine` bean
  swap is mandatory — without it the project starts and then fails at
  first read of legacy data.
- Spawning a subagent to invoke a code-mutating recipe **when the recipe
  itself uses AskUserQuestion** — those prompts must reach the main
  conversation. The orchestrator wraps EXECUTE_RECIPE in a subagent only
  when the recipe declares `## Subagent guidelines` and its Procedure does
  not gate on user input.
- Treating Gradle and Maven as identical — they are not. The external
  `axon4to5-openrewrite` skill handles both build tools (Maven plugin
  vs. `init.gradle` script + JDK 21 Launcher requirement). The external
  `axon4to5-isolatedtest` skill handles Maven profile (`isolated-<X>`)
  vs. Gradle source-set (`isolated<X>`) per the pinned `build-tool`
  decision. Recipes invoke these skills with `target-name`, `main-sources`,
  `test-sources` — never hand-craft `./mvnw -P …` or `./gradlew :test…`
  invocations inside this skill.
- Editing files outside the recipe's scope to "clean up" — keep diffs
  atomic.
- `git add -A` / `git push` / `git commit --amend` / `--no-verify`.

## Reference index

Shared (loaded on demand):
- [references/verification.md](references/verification.md) — mvn flags, reactor rules.
- [references/commit-cadence.md](references/commit-cadence.md) — commit rules per recipe kind.
- [references/source-access.md](references/source-access.md) — where AF4/AF5 sources resolve locally.
- [references/output-contract.md](references/output-contract.md) — worked examples for the six-variant Output union (`result:` discriminator).

Recipes (one per concept):
- [references/openrewrite.md](references/openrewrite.md)
- [references/aggregate/aggregate.md](references/aggregate/aggregate.md)
- [references/event-processor/event-processor.md](references/event-processor/event-processor.md)
- [references/command-gateway/command-gateway.md](references/command-gateway/command-gateway.md)
- [references/query-gateway/query-gateway.md](references/query-gateway/query-gateway.md)
- [references/query-handler/query-handler.md](references/query-handler/query-handler.md)
- [references/interceptors/interceptors.md](references/interceptors/interceptors.md) — `MessageDispatchInterceptor` / `MessageHandlerInterceptor` interface rewrite + framework-config registration sites.
- [references/event-storage-engine/event-storage-engine.md](references/event-storage-engine/event-storage-engine.md) — storage-engine bean swap + bootstrap-layer reads + generic write-side shape changes ([configuration.md](references/event-storage-engine/configuration.md))

Topic-nested configuration sub-references (linked from each topic recipe):
- [references/event-processor/configuration-reads.md](references/event-processor/configuration-reads.md) — `eventProcessor` / `tokenStore` / `sequencedDeadLetterProcessor` lookups, async lifecycle, `TrackingEventProcessor` → `StreamingEventProcessor`.
- [references/command-gateway/configuration-reads.md](references/command-gateway/configuration-reads.md) — `commandBus()` root lookup.
- [references/query-gateway/configuration-reads.md](references/query-gateway/configuration-reads.md) — `queryBus()` / `queryUpdateEmitter()` root lookups.
- [references/debug/debug.md](references/debug/debug.md)

External skills (installed separately — invoked via Skill tool):
- `axon4to5-openrewrite` — bulk OpenRewrite recipe for the Migration Phase #1 (`openrewrite` recipe row).
- `axon4to5-isolatedtest` — per-target `isolated-<TargetName>` scope (Maven profile / Gradle source-set) for every iterative recipe's verify step. Inputs: `target-name`, `build-file`, `main-sources`, `test-sources`, optional `extra-deps`, `cleanup`.

Per-recipe addenda are linked from inside each recipe's own folder. Topic
files do NOT link sideways to other topics — shared content lives at
the top of `references/` or in `assets/`.
