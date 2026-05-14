---
name: axon4to5-migrate
description: >-
  Migrate Axon Framework 4 project to Axon(iq) Framework 5.
argument-hint: "framework=<axon|axoniq> configuration=<native|spring> mode=<single|project> [execution=<inline|subagent>] [source=<class|file|fqn>]"
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/list-recipes.sh)
disable-model-invocation: true
---

# axon4to5-migrate

## Goal

> Fully (or as most as possible) compiling, green-test codebase on AF5, **same architecture as AF4**.
> No DCB. No new patterns. Legacy event storage preserved.
> The migration preserves the project's existing configuration style: a Spring Boot
> project stays on Spring auto-config (recipes use `@Component` / `@Bean`
> idioms); a plain framework-configuration project stays on the direct
> `Configurer` API (recipes use `EventSourcingConfigurer` /
> `MessagingConfigurer` / `CommandHandlingModule` / `EventSourcedEntityModule`).

## Available recipes (auto-listed)

!`${CLAUDE_SKILL_DIR}/scripts/list-recipes.sh`

## Inputs

- `framework` (**required**): which Axon flavor to migrate. Currently supported values: `axon`, `axoniq`. Any other
  value → STOP.
- `configuration` (**required**): how the application wires Axon. Currently supported values: `native`, `spring`. Any
  other value → STOP.
- `mode` (required): what gets migrated in one invocation.
    - `single` — one element (a class, e.g. an Aggregate). Requires `source`.
    - `project` — the whole application (default: current working directory). `source` ignored.
- `execution` (optional, default `inline`): how the orchestrator runs its steps. Only meaningful for `mode=project` —
  for `mode=single` it has no observable effect.
    - `inline` — main session does discovery + recipe runs sequentially. No `Agent` tool use.
    - `subagent` — orchestrator MAY dispatch via the `Agent` tool: discovery → `Explore` subagent, recipe sub-flow per
      item → `general-purpose` subagent (parallel batches). Useful for `project` mode on large codebases.
- `source` (required for `mode=single`): hint identifying the thing to migrate (class name, file path, FQN).
- `skip-openrewrite` (optional, default `false`): when `true`, the orchestrator SKIPS Pre-step 2 (the OpenRewrite bulk pass) and goes straight to the mode-specific producer. Use this when (a) OpenRewrite Phase 1 has already been run separately on the tree, (b) the caller is exercising a recipe in isolation (e.g. evals — subagents cannot recursively invoke another Skill), or (c) the project is not built with Maven/Gradle so the OpenRewrite plugin is unreachable. Values: `true` / `false`. Any other value → STOP. The downstream recipe must still tolerate both AF4-shaped and partially-migrated sources (see each recipe's `# Applicable` predicates).

## Durability

**ALWAYS `Read` [`references/DURABILITY.md`](references/DURABILITY.md) FIRST — before pre-steps.** Mandatory. It defines the state files under `.axon4to5-migration/`, the hooks observed across pre-steps + queue + recipe results + caller decisions, and the commit protocol. Reads `progress.md` on entry to decide resume vs fresh.

## Pre-steps (common to every mode)

These run **before** any mode-specific logic — independent of whether `mode=single`, `project`, or anything added later.

1. **Parse** — read `framework`, `configuration`, `mode`, `execution`, `skip-openrewrite` from `$ARGUMENTS`.
    - If `framework` is missing or ∉ {`axon`, `axoniq`} → STOP and report unsupported framework.
    - If `configuration` is missing or ∉ {`native`, `spring`} → STOP and report unsupported configuration.
    - If `mode` is missing or ∉ {`single`, `project`} → STOP and report unsupported mode.
    - `execution` defaults to `inline` if missing. If present and ∉ {`inline`, `subagent`} → STOP and report unsupported
      execution.
    - `skip-openrewrite` defaults to `false` if missing. If present and ∉ {`true`, `false`} → STOP and report unsupported value.
2. **OpenRewrite** — **skipped entirely when `skip-openrewrite=true`.** Otherwise, internally invoke
   `axon4to5-openrewrite` via the `Skill` tool, passing `framework=$framework`. This is a step of this orchestrator, not
   a separate command. Idempotent — safe even on a partially-migrated tree. If it fails → STOP and report the failure
   (no gap-filling on a broken bulk pass). When skipped, surface that fact in the eventual report (Notes or Learnings)
   so the caller knows the queue ran against unprocessed AF4 (or already-partially-migrated) sources and the recipes did
   all the work themselves.

Only after pre-steps complete does the mode-specific producer below run.

## Modes

### `single`

Migrate ONE element (one aggregate, one event processor, etc.) using exactly one recipe from the list above.

Steps (after the common pre-steps):

1. **Match** — map user's request + `source` to ONE recipe in the auto-listed set. Primary signal: the catalog's
   `applicable` block (surface predicates against `$SOURCE` — annotations / type markers). Fallback signal: `id` +
   `title` + `description`. If ambiguous → ask user via `AskUserQuestion` to pick (show `title` to the user; dispatch by
   `id`). If no `applicable` block matches and description is also unclear → STOP and report.
2. **Execute** — `Read` the chosen recipe file under [`references/recipes/`](references/recipes/) (`<name>/RECIPE.md`)
   and execute it per the **Recipe sub-flow** ([`FLOW.md`](references/recipes/FLOW.md), already loaded). Recipe-local
   auxiliary files (examples, fixtures, supporting docs) live alongside it in the same `<name>/` directory.
3. **Verify** — behavior is preserved (no DCB, keep `AggregateBasedEventStorageEngine`, etc.).
4. **Report** — render the report (see Queue flow § Render report).

MUST NOT:

- Run without all required parameters resolved to a supported value.
- Run multiple recipes in one invocation.
- Migrate more than the single source named by the user.
- Migrate anything outside the supported `(framework, configuration)` matrix — the rest of the codebase stays untouched.
- Introduce DCB or swap event storage engine.

### `project`

Migrate **everything in the working directory** that any recipe in the catalog declares applicable. `source` is ignored.

Steps (after the common pre-steps):

1. **Discover** — for each recipe in the auto-listed catalog, evaluate its `applicable` predicates across the codebase
   to produce candidate sources.
    - `execution=inline` → orchestrator scans inline using `Grep` / `Glob` / `Read`.
    - `execution=subagent` → dispatch one `Explore` subagent **per recipe** (parallel batch via a single `Agent` tool
      message with multiple calls). Each agent receives the recipe's `applicable` block + `id` and returns a list of
      FQNs / file paths. Read-only — no edits.
2. **Enqueue** — every `(recipe, source)` candidate. Deduplication is recipe's concern (handled inside its Recipe
   sub-flow); orchestrator does not collapse items across recipes.
3. **Drain** — for each item run the Recipe sub-flow:
    - `execution=inline` → run in main session, sequentially.
    - `execution=subagent` → dispatch each item to a `general-purpose` subagent. Batch independent items in a single
      `Agent` tool message so they run in parallel. Subagent receives `(recipe path, source, framework, configuration)`
      and the full Recipe sub-flow spec; returns one result block (`RESULT:` line + NOTES). Orchestrator parses and
      records.
4. **Report** — render the report (see Queue flow § Render report).

MUST NOT:

- Spawn a subagent under `execution=inline`.
- Pass anything beyond `(recipe path, source, framework, configuration)` to a recipe subagent — context bloat defeats
  the parallelism win.
- Cross repository boundaries during discovery.
- Halt the queue on a single Failure — record and drain the rest.
- Introduce DCB or swap event storage engine.

## Queue flow

`$SOURCE` is referenced throughout the recipe sub-flow as the argument passed to the skill from `source`.
Every mode produces a **queue** of `(recipe, source)` items. A single processing loop drains it. What happens on empty
queue depends on the mode.

```mermaid
flowchart TD
    A[Skill invoked] --> PARSE["<b>Parse</b><br/>framework, configuration,<br/>mode, execution"]
    PARSE --> ORW[["<b>OpenRewrite</b><br/>(internal: Skill axon4to5-openrewrite,<br/>framework=$framework, idempotent)"]]
    ORW -- fail --> XORW[STOP: bulk-rewrite failed]
    ORW -- ok --> B["! list-recipes.sh<br/>(recipes catalog)"]
    B --> C{mode}
%% mode-specific producers — all feed the same queue
    C -- single --> P1["<b>Match</b><br/>request+source<br/>→ enqueue 1 item"]
    C -- project --> P2["<b>Discover</b><br/>execution=inline: Grep/Glob inline<br/>execution=subagent: 1 Explore agent<br/>per recipe (parallel batch)<br/>scan project per applicable<br/>→ <b>Enqueue</b> N items"]
    C -- other --> X[STOP: unsupported mode]
    P1 --> Q[(Migration queue)]
    P2 --> Q
%% shared processing loop — items stay in the queue, state transitions write back to it
    Q --> L{<b>Drain</b><br/>any pending<br/>items in queue?}
    L -- yes --> INP["pick next pending →<br/>mark in-progress in queue"]
    INP --> W[["<b>Execute</b> recipe sub-flow on item<br/>execution=inline: main session<br/>execution=subagent: general-purpose<br/>agent per item (parallel batch)"]]
    W --> R{<b>RESULT?</b>}
    R -- "Blocker (first attempt)" --> BR[["<b>Resolve blocker</b><br/>per BLOCKER_RESOLUTION.md<br/>(orchestrator-side fixup<br/>using the recipe's NOTES)"]]
    BR --> BRQ{<b>Resolved?</b><br/>budget = 1<br/>attempt per item}
    BRQ -- yes --> W
    BRQ -- "no / budget exhausted" --> BLK["mark item → blocked<br/>attach RESULT=Blocker + NOTES<br/>(🚧 caller must resolve)"]
    R -- "Blocker (already retried)" --> BLK
    R -- "Success / Rejected / Failure" --> VER["<b>Verify</b><br/>behavior preserved<br/>(no DCB, keep AggregateBased<br/>EventStorageEngine)"]
    VER --> DONE["mark item → done in queue<br/>attach RESULT + NOTES + files_changed<br/>(✅ Success | ⏭ Rejected | ❌ Failure)"]
    DONE --> Q
    BLK --> Q
    L -- no --> RPT["<b>Report</b> &amp; END<br/>list of done items from queue:<br/>(recipe, source, RESULT, NOTES,<br/>files_changed)"]
```

> The `[[Execute recipe sub-flow]]` node is the **nested** sub-flow defined in
> [`references/recipes/FLOW.md`](references/recipes/FLOW.md) (loaded at skill start). The queue only reacts to the
> recipe's emitted result.
>
> The `[[Resolve blocker]]` node executes the orchestrator-side blocker-fixup playbook in
> [`references/recipes/BLOCKER_RESOLUTION.md`](references/recipes/BLOCKER_RESOLUTION.md). Budget is **one** resolution
> attempt per item: if it succeeds, the same item re-enters the recipe sub-flow once; if it fails or a second Blocker
> comes back from the re-attempt, the item is marked blocked and the queue moves on (the queue never halts on a single
> blocker — caller resolves and re-invokes the skill).

## Recipe sub-flow

**ALWAYS load [`references/recipes/FLOW.md`](references/recipes/FLOW.md) via the `Read` tool at skill start — before any
mode-specific logic.** It defines the orchestrator-owned control flow every recipe executes against. Non-optional.
Recipes fill in named sections referenced from that flow; they never re-implement it.

### Recipe defaults ([`DEFAULT.md`](references/recipes/DEFAULT.md))

**ALWAYS `Read` [`references/recipes/DEFAULT.md`](references/recipes/DEFAULT.md) BEFORE any per-recipe `RECIPE.md` under
[`references/recipes/`](references/recipes/).** It holds shared defaults for every named recipe section (`# Applicable`,
`# Scope`, `# References`, `# Success Criteria`, `# Blocker`, `# Toolbox`, `# Out of Scope`, `# Gotchas`).

Merge rule when executing a recipe:

- For each section the FLOW consults, start from [`DEFAULT.md`](references/recipes/DEFAULT.md)'s content for that
  section.
- If `RECIPE.md` defines the same section → **`RECIPE.md` overrides** (full section replacement, not append).
    - Exception: if `RECIPE.md`'s section body references [`DEFAULT.md`](references/recipes/DEFAULT.md) (e.g. literal
      token `@DEFAULT.md` or prose like "inherits from DEFAULT.md" / "extends DEFAULT.md") → **append** the recipe's
      content to the default's content for that section instead of replacing.
- If `RECIPE.md` omits the section → the [`DEFAULT.md`](references/recipes/DEFAULT.md) content stands.
- Recipe authors only write sections that differ from the default. No need to re-state defaults.

## References/Docs: Migration paths catalog

Shared cross-recipe knowledge base at [`references/docs/paths/`](references/docs/paths/). Recipes pick relevant entries
in their `### Migration Paths` subsection, each with an **apply-condition** (a fact about current scope that triggers
loading the file). The orchestrator never reads these directly — only recipes do, gated by their declared
apply-condition.

Catalog (one file per topic; `.adoc`):

| Path                                                                                                       | Topic                                               |
|------------------------------------------------------------------------------------------------------------|-----------------------------------------------------|
| [`aggregates/index.adoc`](references/docs/paths/aggregates/index.adoc)                                     | Aggregate migration entry point                     |
| [`aggregates/configuration-migration.adoc`](references/docs/paths/aggregates/configuration-migration.adoc) | Aggregate Spring/Configurer wiring                  |
| [`aggregates/multi-entity-migration.adoc`](references/docs/paths/aggregates/multi-entity-migration.adoc)   | Aggregates with child entities (`@AggregateMember`) |
| [`aggregates/polymorphism-migration.adoc`](references/docs/paths/aggregates/polymorphism-migration.adoc)   | Polymorphic aggregates                              |
| [`configuration.adoc`](references/docs/paths/configuration.adoc)                                           | Global Axon configuration / Configurer              |
| [`messages.adoc`](references/docs/paths/messages.adoc)                                                     | Command / Event / Query message changes             |
| [`event-store.adoc`](references/docs/paths/event-store.adoc)                                               | Event Store engine + APIs                           |
| [`snapshotting.adoc`](references/docs/paths/snapshotting.adoc)                                             | Snapshot trigger + storage                          |
| [`serializers.adoc`](references/docs/paths/serializers.adoc)                                               | Serializer registration + payload formats           |
| [`interceptors.adoc`](references/docs/paths/interceptors.adoc)                                             | Command / Event / Query handler interceptors        |
| [`projectors-event-processors.adoc`](references/docs/paths/projectors-event-processors.adoc)               | Projection / Event Processor wiring                 |
| [`sequencing-policies.adoc`](references/docs/paths/sequencing-policies.adoc)                               | Event sequencing policies                           |
| [`dlq.adoc`](references/docs/paths/dlq.adoc)                                                               | Dead-Letter Queue                                   |
| [`test-fixtures.adoc`](references/docs/paths/test-fixtures.adoc)                                           | Test fixtures migration                             |
