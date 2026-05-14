---
name: axon4to5-migrate
description: >-
  Migrate a Spring Boot or plain-Configurer Axon Framework 4 project to
  Axon Framework 5 — preserves behavior (no DCB, legacy event storage).
  Three modes: phased (default), debug (triage), single (one file).
argument-hint: "[<file path or FQ class> | debug | phased]"
disable-model-invocation: true
---

# AF4 → AF5 migration

Classify each candidate file → run its recipe → commit per item. State lives in `<target>/.axon4to5-migration/progress.md`. Self-contained: every example referenced is bundled under `evals/fixtures/`.

**Out of scope.** SQL, DDL, data migration, event-store row copies, snapshot rewrites. **Code only.** Every `move-to-*` blocker option is a code-rewrite choice; the user owns any data move out-of-band.

## Modes

| `$ARGUMENTS` | Mode | Flow |
|---|---|---|
| empty / `phased` | **PHASED** | Walk routing table top-down; resumable from `progress.md`. |
| `debug` | **DEBUG** | Run compile, cluster errors by root cause, route highest-leverage cluster, repeat. |
| `<file path or FQ class>` | **SINGLE** | Classify, run one recipe, commit, stop. |

Bad path → surface error, do NOT fall back to phased. Ambiguous → `AskUserQuestion`.

## Routing — recipes

Recipes are independent. Ordering matters only for two endpoints:
- **`openrewrite` runs first** (bulk transform; other recipes depend on its rewrites).
- **`event-storage-engine` runs last** (depends on every iterative recipe having already migrated handlers and gateways).

Everything else can run in any order — the table lists the default sequence used by PHASED mode.

| Order | Recipe | Discovery (grep) | Exclude-when (grep) | Notes |
|---|---|---|---|---|
| 1st | [openrewrite](references/openrewrite.md) | n/a — project on `org.axonframework.*`, not yet AF5 BOM | — | one-shot |
| 2 | [aggregate](references/aggregate.md) | `@Aggregate\b\|@AggregateRoot\b` | — | iterative |
| 3 | [event-processor](references/event-processor.md) | `@ProcessingGroup\|org\.axonframework\.eventhandling\.EventHandler` | — | iterative |
| 4 | [command-gateway](references/command-gateway.md) | `org\.axonframework\.commandhandling\.gateway\.CommandGateway` | `@EventHandler\|@CommandHandler\|@QueryHandler\|@MessageHandlerInterceptor` | iterative |
| 5 | [query-gateway](references/query-gateway.md) | `org\.axonframework\.queryhandling\.QueryGateway` | `@EventHandler\|@CommandHandler\|@QueryHandler` | iterative |
| 6 | [query-handler](references/query-handler.md) | `org\.axonframework\.queryhandling\.QueryHandler` | — | iterative |
| 7 | [interceptors](references/interceptors.md) | `implements\s+MessageDispatchInterceptor\b\|implements\s+MessageHandlerInterceptor\b` | `@CommandHandler\|@EventHandler\|@QueryHandler` | iterative |
| 8 | [config-reads](references/config-reads.md) | field type `org\.axonframework\.config\.(Configuration\|EventProcessingConfiguration)` AND a `commandBus()` / `queryBus()` / `eventProcessor` lookup in the body | — | iterative — handles read-side variants of `command-gateway` / `query-gateway` / `event-processor` |
| last | [event-storage-engine](references/event-storage-engine.md) | n/a — declares `EventStorageEngine` / `EmbeddedEventStore` / `AxonServerEventStore` bean | — | one-shot; bundles bootstrap-layer config sweep |

**Non-recipe rows** (referenced by `saga` blocker + DEBUG mode):

| Recipe | Discovery | Notes |
|---|---|---|
| [saga](references/saga.md) | `@Saga\b\|@SagaEventHandler\|@StartSaga\|@EndSaga\|SagaConfigurer` | not-supported — per-saga decision, never auto-rewrite |
| [debug](references/debug.md) | build errors | mode, not a phase. Drives cluster-and-route after a red compile. |

### Single-file classification

User passes a file path or FQ class. Read the file once; for each iterative/one-shot row in the table (top-down), if `Discovery` matches AND `Exclude-when` does not → that row wins. Multiple matches → first wins. User overrides via `AskUserQuestion`.

`config-reads` is checked LAST among the iterative rows because most gateway-injecting / handler classes also have an AF4 `Configuration` import lying around; `config-reads` only wins when the file is genuinely a configuration-reader.

## Recipe communication protocol

Recipes are **pausable workflows**. Each recipe-invocation may emit one of two response types:

| Response | When | Recipe state |
|---|---|---|
| **🔒 `await decision <key>`** | Recipe hit a declared decision point that isn't yet resolved in `inputs.decisions` | alive — resumes after orchestrator returns the answer (no state lost; partial edits stay on disk) |
| **`output { result }`** | Recipe finished (success / skipped / rejected / blocked / failed) | terminal |

The recipe **never calls `AskUserQuestion` directly**. It defers all user-facing prompts to the orchestrator via `await decision`. The orchestrator picks the resolution strategy from its **resolver_mode** (orthogonal to the source-mode SINGLE/PHASED/DEBUG):

| Resolver mode | Behavior on `await decision` |
|---|---|
| `interactive` (default) | already pinned → reuse; auto-policy fires → use; else `AskUserQuestion` |
| `automatic` | already pinned → reuse; auto-policy fires → use; else fail the run (no user to ask — CI guardrail) |
| `dry-run` *(planned)* | stub unresolved decisions as `pause-migration`; never edit files; produce report |

Recipe authors declare auto-policies in each recipe's `## Decision points` section using a small DSL — e.g. `pinned.license == "axoniq-commercial": <option>` / `fallback: ask-user`. Full contract: [references/_template.md](references/_template.md).

### Output schema — five results

```yaml
result: success | skipped | rejected | blocked | failed
target: <FQ class | file path | "n/a">
reason: <one short line>                # required for everything except success
decisions:                              # complete audit trail of decisions resolved during this run
  <recipe-specific keys>
files_touched:                          # explicit — drives `git add`
  - <repo-relative path>
route_to: <recipe>                      # OPTIONAL, only on rejected
notes: <free text>                      # cite blockers.md#B<n> when blocked; surface tool output when failed
```

| `result:` | Orchestrator action |
|---|---|
| `success` | commit `files_touched` + `progress.md`; next item. |
| `skipped` | no commit; next item. |
| `rejected` | no commit; if `route_to:` set, re-route via routing table; else next. |
| `blocked` | recipe commented-out AF4 surface + `TODO[AF5 migration: <key>]` markers; commit `files_touched` + `progress.md`; record blocker in Pinned-decisions; next. |
| `failed` | no commit; surface `reason` + `notes`; `AskUserQuestion`: hand off to `debug` / pause / stop. |

`needs-decision` is **not** a `result:` value — decision points are handled via `await decision` mid-run, never as a terminal output.

Blocker keys (`B1`..`B10`) live in [references/blockers.md](references/blockers.md). Each recipe's `## Decision points` section enumerates which blockers it can surface and the auto-policy for each.

## Orchestrator flow

**One outer loop, one switch.** A single mode-parameterized `next_batch()` step yields units to drain; the orchestrator drains them, then asks `next_batch()` again. The body inside the batch (classify → recipe → act) is identical for every mode — **DEBUG is just PHASED with a different `next_batch()`**. Single-unit modes degenerate (one batch, then empty). **Double-bordered nodes `[[…]]` (also dashed-blue) are subagent-eligible** — read-only or pure-analysis, no `AskUserQuestion`, no git, no shared state mutation.

```mermaid
flowchart TD
    Start([User invokes skill])
    State[ensure_state<br/>INIT if no progress.md · ensure_pinned · resume]

    NextBatch[["next_batch · mode<br/>single → arg once<br/>phased → next pending routing row<br/>debug → recompile + cluster"]]
    Empty{empty?}

    InnerLoop{next unit in batch?}
    Classify[[classify unit → row]]
    Recipe[[recipe.execute<br/>Preflight · Procedure · EndCondition]]
    AwaitDecision{recipe emitted<br/>🔒 await decision?}
    Resolve[resolve_await<br/>pinned · auto-policy · interactive]
    Act{output.result}

    Commit[/commit files_touched + progress.md/]
    NoCommit[no commit]
    CommitBlocked[/commit comment-out + TODO + progress.md/]

    Checkpoint{checkpoint<br/>phased / debug only<br/>continue · pause · stop}

    WrapUp{all routing rows<br/>done in progress.md?}
    Finalize[FINALIZE<br/>cleanup isolated-* · full build]
    Stop([STOP])
    Halt([HALT])

    Start --> State --> NextBatch --> Empty
    Empty -->|yes| WrapUp
    Empty -->|no| InnerLoop

    InnerLoop -->|yes| Classify --> Recipe --> AwaitDecision
    InnerLoop -->|done| Checkpoint

    AwaitDecision -->|yes| Resolve
    AwaitDecision -->|no — output emitted| Act

    Resolve -->|answer| Recipe

    Act -->|success| Commit --> InnerLoop
    Act -->|skipped| NoCommit --> InnerLoop
    Act -->|rejected| NoCommit
    Act -->|blocked| CommitBlocked --> InnerLoop
    Act -->|failed| Halt

    Checkpoint -->|continue / single| NextBatch
    Checkpoint -->|pause / stop| Halt

    WrapUp -->|yes| Finalize --> Stop
    WrapUp -->|no| Stop

    classDef subagent stroke:#1976d2,stroke-width:3px,stroke-dasharray:5 5
    class NextBatch,Classify,Recipe subagent
```

### Subagent boundaries (dashed nodes)

| Step | Why subagent-safe |
|---|---|
| `next_batch` (phased) | discovery greps walk the project read-only |
| `next_batch` (debug) | parses compile output read-only |
| `classify (unit)` | inspects a single file; emits a recipe selection — no edits |
| `recipe.execute` | recipe's Preflight + Procedure run as analysis + edit proposal — **only when the recipe declares `## Subagent guidelines` AND every `## Decision points` entry can resolve via auto-policy or pre-pinned state** (no `fallback: ask-user` left unresolved at fan-out time). Otherwise run in the main session so `await decision` reaches a real `AskUserQuestion`. |

Everything else is **orchestrator-owned**: `ensure_state` / `INIT` issue `AskUserQuestion` for pinned project decisions; `Resolve` decides between auto-policy / pinned / interactive; `Commit` / `CommitBlocked` own git; `Checkpoint` is user-facing; `Finalize` decides on red builds.

### Procedural sketch (for code-style readers)

```
ensure_state()

while True:
    batch = next_batch(mode)              # single → [arg] once;
                                          # phased → next pending routing row's discoveries;
                                          # debug  → recompile + extract next highest-leverage cluster
    if not batch: break

    for unit in batch:
        row     = classify(unit)
        inputs  = build_inputs(unit, row, pinned, decisions={})
        while True:
            response = recipe.execute(row, inputs)
            if response is AwaitDecision:
                answer = resolve_await(response, pinned, resolver_mode)
                inputs.decisions[response.key] = answer
                continue                    # recipe resumes from where it paused
            act(response.output)            # terminal — flat switch on output.result
            break

    if mode in {phased, debug}:
        AskUserQuestion: continue / pause / stop   # checkpoint between batches

wrap_up()                                 # FINALIZE iff progress.md shows every routing row done; otherwise STOP


resolve_await(await, pinned, resolver_mode):
    if await.key in pinned.decisions:
        return pinned.decisions[await.key]
    answer = evaluate_auto_policy(await, pinned)   # see _template.md DSL
    if answer == ASK_USER:
        if resolver_mode == "automatic":
            raise UnresolvableDecision(await.key)   # CI guardrail
        answer = AskUserQuestion(await.question, await.options)
    persist_to_progress_md(await.key, answer)
    return answer
```

`next_batch` is the only source-mode-specific code; `resolve_await` is the only resolver-mode-specific code. Everything else is identical across all mode combinations.

### One-shots

**INIT** (first PHASED run, before the queue):
- `mkdir <target>/.axon4to5-migration/`; seed from `assets/*-template.md`.
- `ensure_pinned()` — mandatory.
- scan project for blockers per [blockers.md](references/blockers.md) Detection greps (saga, mongo-event-store, jdbc-event-store, axon-kafka); record decisions.
- commit `chore(af5-migration): initialize migration`.

**ensure_pinned()** (INIT + first SINGLE run on a virgin project):
- **license** — `recommend_license()` returns `axoniq-commercial` if project depends on `axon-{mongo,kafka,amqp,tracing-opentelemetry}` / any `org.axoniq.*` artifact / uses saga / upcaster / replay / DLQ-on-mongo; else `free-af5`. `AskUserQuestion` with recommendation listed first as `(Recommended) — {reason}`.
- **wiring** — `axon-spring-boot-starter` dep OR `@SpringBootApplication` → `spring-boot`; `DefaultConfigurer.defaultConfiguration` or direct `Configurer` → `framework-config`; else `AskUserQuestion`.
- **build-tool** — `pom.xml` only → `maven`; `build.gradle*` only → `gradle`; both → `AskUserQuestion`; neither → HALT.

**FINALIZE** (any mode — fires when `progress.md` Recipe-status shows every routing row `done` / `skipped`):
- for each `isolated-<X>` scope in `progress.md`: invoke `axon4to5-isolatedtest` with `cleanup: true`.
- promote AF5 deps; remove activation refs from scripts/CI/docs.
- full build: `./mvnw -f <target>/pom.xml clean verify` (Maven) / `./gradlew -p <target> clean build` (Gradle).
- if red, classify: recipe-traceable → reopen that recipe; missed-dep → diff scope deps + retry; env/infra → `AskUserQuestion`.
- commit `chore(af5-migration): remove isolated-* scaffolding`; recommend `/clear`.

Pinned decisions are **never re-asked**. Stored in `progress.md` Pinned-decisions block in fixed order: license → wiring → build-tool → blocker decisions.

## External skills (Skill tool)

- `axon4to5-openrewrite` — bulk first-pass migration. Args: `--framework axon|axoniq --commit false`. Pinned license → framework: `free-af5`→`axon`, `axoniq-commercial`→`axoniq`.
- `axon4to5-isolatedtest` — per-target `isolated-<TargetName>` build scope. Inputs: `target-name`, `build-file` (abs path), `main-sources` (repo-relative), `test-sources` (repo-relative or `[]`), `extra-deps`, `cleanup: false` while iterating / `true` on last green run before commit. Idempotent — augments existing scopes.

**Never** hand-craft `./mvnw -P …` / `./gradlew :test…` / OpenRewrite invocations — that's what the skills are for.

## State directory

`<target>/.axon4to5-migration/`:
- `progress.md` — single source of truth. Rewritten before every commit. Must include `▶︎ RESUME HERE` block pointing at the **next** unit with exact recipe + exact verify command. A fresh session reads this and resumes with zero clarifying questions about state.
- `learnings.md` — append-only narrative. Surprises, manual fixes, blocker keys.
- `index.md` — short README pointing at the above.

Templates: [progress-template.md](assets/progress-template.md), [learnings-template.md](assets/learnings-template.md), [index-template.md](assets/index-template.md).

**Persistence invariant.** Every state change ends with `progress.md` rewritten + committed in the **same commit** as the code change it documents. Never split work and bookkeeping.

**Dirty working tree on resume.** If `git status --porcelain` shows files the orchestrator did not touch, pause and `AskUserQuestion`: stage-only-migration-files (recommended, explicit paths) / let-user-clean-up / skip-this-commit. Never `git add -A`.

## Commits

- One commit per item. Stage **explicit paths only** (touched code + `progress.md` + `learnings.md` if dirty).
- Conventional message. Subject patterns:
  - `chore(af5-migration): initialize migration`
  - `chore(af5-migration): apply OpenRewrite recipe <name>@<version>`
  - `refactor(af5-migration): migrate <kind> <SimpleClassName> to AF5` — kind ∈ {aggregate, event handler, command dispatch in, query dispatch in, query handler, interceptor, configuration reader}
  - `feat(af5-migration): wire AggregateBased{Jpa,AxonServer}EventStorageEngine`
  - `fix(af5-migration): <one-line>` — stabilization
  - `docs(af5-migration): record decision on <recipe>/<target>` — decision-only (no code)
  - `chore(af5-migration): remove isolated-* scaffolding`
- **Never** `git push`, `git commit --amend`, `--no-verify`, commit on `main`/`master`, or `git add -A`.
- **Never** silently delete an AF4 bean / registration / fixture when its AF5 successor is missing — comment it out + `TODO[AF5 migration: <blocker-key>]` + record in `progress.md` + `learnings.md`.

After every non-trivial commit, suggest `/clear` — recipe boundaries especially.

## Anti-patterns

- Running `./mvnw verify` between the openrewrite recipe and FINALIZE (it WILL fail by design — use per-target `axon4to5-isolatedtest` scopes instead).
- Re-running OpenRewrite to "fix" what a per-construct recipe couldn't handle.
- Treating `event-storage-engine` as auto-configured by the Spring Boot starter — the AF5 starter applies AF5 defaults, not a migration of the existing AF4 event store. The explicit `AggregateBased…EventStorageEngine` bean swap is mandatory.
- Editing files outside the recipe's scope to "clean up" — keep diffs atomic.
- Running a recipe in a subagent when its Procedure uses `AskUserQuestion` — those prompts must reach the main conversation.

## Evals

**Functional, with-skill vs baseline.** For each eval the loop:

1. **prep** — `run.py prep` copies the AF4 fixture into a fresh workspace dir and prints two ready-to-paste subagent prompts (one with the skill loaded, one baseline).
2. **execute** — the driving Claude session spawns Agent subagents with those prompts; each writes its migrated AF5 file to `outputs/`.
3. **grade** — `grade.py` greps each output against the eval's assertions (`grep_require` / `grep_forbid`), writes `grading.json`.
4. **aggregate** — `run.py aggregate` collates pass-rate / tokens / wall-clock across with_skill vs without_skill into `benchmark.{json,md}`.

Fixtures are bundled in `evals/fixtures/` via [evals/manifest.tsv](evals/manifest.tsv) + [evals/build.sh](evals/build.sh); the skill stays self-contained without depending on `.knowledge/repositories/`.

```bash
./evals/build.sh                                    # refresh fixtures from upstream
./evals/build.sh check                              # verify hashes; non-zero on drift
./evals/run.py prep --iteration 1 --filter <name>   # set up workspace + print prompts
./evals/run.py grade --iteration 1                  # grade every output present
./evals/run.py aggregate --iteration 1              # render benchmark.{json,md}
./evals/run.py status --iteration 1                 # which evals have outputs / grading?
```

Test cases live in [evals/evals.json](evals/evals.json). See [evals/README.md](evals/README.md) for the schema and how to add a case.
