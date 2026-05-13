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

Route candidate files to recipes under `references/<recipe>/`, run each, commit per item. State lives in `<target>/.axon4to5-migration/progress.md`.

**Out of scope:** SQL, DDL, data migration, event-store row copies, snapshot rewrites. Code only. `move-to-*` blocker options are code-rewrite choices; user owns the data move.

## Modes

| `$ARGUMENTS` | Mode | Flow |
|---|---|---|
| empty / `phased` | **PHASED** | Walk routing table top-down; resumable from `progress.md`. |
| `debug` | **DEBUG** | Run compile, cluster errors by root cause, route highest-leverage cluster, repeat. |
| `<file path or FQ class>` | **SINGLE** | Auto-route, run one recipe, commit, stop. |

Bad path → surface error, do NOT fall back to phased. Ambiguous → `AskUserQuestion`.

## Routing table

Single source of truth: phase order + discovery + single-file auto-routing.

| Recipe | Mode | Phase | Discovery (grep) | exclude-when |
|---|---|---|---|---|
| [openrewrite](references/openrewrite.md) | one-shot | 1 | n/a — project on `org.axonframework.*`, not yet AF5 BOM | — |
| [aggregate](references/aggregate/aggregate.md) | iterative | 2 | `@Aggregate\b\|@AggregateRoot\b` | — |
| [event-processor](references/event-processor/event-processor.md) | iterative | 3 | `@ProcessingGroup\|org\.axonframework\.eventhandling\.EventHandler` | — |
| [command-gateway](references/command-gateway/command-gateway.md) | iterative | 4 | `org\.axonframework\.commandhandling\.gateway\.CommandGateway` | `@EventHandler\|@CommandHandler\|@QueryHandler\|@MessageHandlerInterceptor` |
| [query-gateway](references/query-gateway/query-gateway.md) | iterative | 5 | `org\.axonframework\.queryhandling\.QueryGateway` | `@EventHandler\|@CommandHandler\|@QueryHandler` |
| [query-handler](references/query-handler/query-handler.md) | iterative | 6 | `org\.axonframework\.queryhandling\.QueryHandler` | — |
| [interceptors](references/interceptors/interceptors.md) | iterative | 7 | `implements\s+MessageDispatchInterceptor\b\|implements\s+MessageHandlerInterceptor\b` | `@CommandHandler\|@EventHandler\|@QueryHandler` |
| [event-storage-engine](references/event-storage-engine/event-storage-engine.md) | one-shot | 8 | n/a — declares `EventStorageEngine` / `EmbeddedEventStore` / `AxonServerEventStore` bean | — |
| [saga](references/saga/saga.md) | not-supported | n/a | `@Saga\b\|@SagaEventHandler\|@StartSaga\|@EndSaga\|SagaConfigurer` | — |
| [debug](references/debug/debug.md) | triage | n/a | build errors | — |

**Single-file routing.** Read the file; walk rows by ascending `Phase`; first row where Discovery matches AND exclude-when does NOT wins. Ties → lowest Phase. User can override via `AskUserQuestion`.

## Recipe output — six results

Every recipe emits one fenced ```yaml block:

```yaml
result: success | skipped | rejected | needs-decision | blocked | failed
target: <FQ class | file path | "n/a">
reason: <one short line>                 # required for everything except success
decisions: { <recipe-specific keys> }
caller-expects:
  commit: true | false
  next:   proceed | ask-user | record-and-skip | halt | route-to:<recipe>
notes: <optional>
```

| `result:` | Orchestrator does |
|---|---|
| `success` | commit code + `progress.md`; next item. |
| `skipped` | no commit; next item. |
| `rejected` | no commit; if `next == route-to:<recipe>` re-route, else next. |
| `needs-decision` | `AskUserQuestion` with `notes` options. fix → re-run recipe; defer → commit `progress.md` only; stop → HALT. |
| `blocked` | comment-out AF4 surface + `TODO[AF5 migration: <key>]`. If `commit: true` commit code + `progress.md`; else commit `progress.md` only. |
| `failed` | no commit; surface; `AskUserQuestion`: hand off to `debug` / pause / stop. |

## Orchestrator flow

```
ORCHESTRATE($ARGUMENTS):
  target = resolve_and_validate()           # exists, has pom.xml/build.gradle, git repo
  mode   = parse($ARGUMENTS)

  SINGLE: ensure_pinned(); row = route(arg); run_recipe(row, arg); /clear; STOP

  DEBUG:  loop until green or stopped:
            compile target → diagnostics
            (row, item) = cluster_by_root_cause()
            run_recipe(row, item)
            if compile output unchanged → AskUserQuestion: surface/skip-defer/stop

  PHASED: if no progress.md → INIT
          else: read progress.md; handle dirty tree; confirm resume
          for each routing-table row not yet done:
            items = discover(row) − deferred − unsupported
            for item in items: run_recipe(row, item)
            AskUserQuestion: continue/pause/stop
          FINALIZE


run_recipe(row, item):
  inputs = { target: item, wiring: pinned, build-tool: pinned, license: pinned }
  output = execute(row.recipe, inputs)      # ## Preflight → ## Procedure → ## End condition
  act(output)                               # switch on output.result — see table above


INIT (first PHASED run only):
  mkdir <target>/.axon4to5-migration/; seed from assets/*-template.md
  ensure_pinned()                            # MANDATORY before any recipe
  for each not-supported row with hits: AskUserQuestion accept-stays-af4/pause/remove-feature-first
  commit "chore(af5-migration): initialize migration"


ensure_pinned():                              # called from INIT AND from SINGLE
  license:    recommend_license() → AskUserQuestion with rec listed first as "(Recommended) — {reason}"
              free-af5 | axoniq-commercial
              rec = axoniq-commercial if: axon-{mongo,kafka,amqp,tracing-opentelemetry}, org.axoniq.* dep,
                                          saga/upcaster/replay/DLQ-on-mongo (features not in free AF5)
              else: free-af5
  wiring:     axon-spring-boot-starter dep OR @SpringBootApplication      → spring-boot
              DefaultConfigurer.defaultConfiguration / direct Configurer   → framework-config
              else AskUserQuestion
  build-tool: pom.xml only → maven; build.gradle* only → gradle; both → AskUserQuestion; neither → HALT


FINALIZE (after every row done):
  for each isolated-<X> scope in progress.md: invoke axon4to5-isolatedtest cleanup:true
  promote AF5 deps; remove activation refs from scripts/CI/docs
  full build:  maven → ./mvnw -f <target>/pom.xml clean verify
               gradle → ./gradlew -p <target> clean build
  if red, classify: recipe-traceable → reopen phase; missed-dep → diff scope deps + retry;
                    env/infra → AskUserQuestion
  commit "chore(af5-migration): remove isolated-* scaffolding"; recommend /clear
```

Pinned decisions are **never re-asked**. Stored in `progress.md` Pinned-decisions block in fixed order: license → wiring → build-tool → not-supported decisions.

## External skills (Skill tool)

- `axon4to5-openrewrite` — bulk Phase 1 migration. Args: `--framework axon|axoniq --commit false`. Pinned license → framework: `free-af5`→`axon`, `axoniq-commercial`→`axoniq`.
- `axon4to5-isolatedtest` — per-target `isolated-<TargetName>` build scope. Inputs: `target-name`, `build-file` (abs path), `main-sources` (repo-relative), `test-sources` (repo-relative or `[]`), `extra-deps`, `cleanup: false` while iterating / `true` on last green run before commit. Idempotent — augments existing scopes.

**Never** hand-craft `./mvnw -P …` / `./gradlew :test…` / OpenRewrite invocations — that's what the skills are for.

## State directory

`<target>/.axon4to5-migration/`:
- `progress.md` — single source of truth. Rewritten before every commit. Must include `▶︎ RESUME HERE` block pointing at the **next** unit with exact recipe + exact verify command. A fresh session reads this and resumes with zero clarifying questions about state.
- `learnings.md` — append-only narrative. Surprises, manual fixes, blocker keys.
- `index.md` — short README pointing at the above.

Templates: [assets/](assets/).

**Persistence invariant.** Every state change ends with `progress.md` rewritten + committed in the **same commit** as the code change. Never split work and bookkeeping.

**Dirty working tree on resume.** If `git status --porcelain` shows files the orchestrator did not touch, pause and `AskUserQuestion`: stage-only-migration-files (recommended, explicit paths) / let-user-clean-up / skip-this-commit. Never `git add -A`.

## Commits

- One commit per item. Stage **explicit paths only** (touched code + `progress.md` + `learnings.md` if dirty).
- Conventional message. Subject patterns:
  - `chore(af5-migration): initialize migration`
  - `chore(af5-migration): apply OpenRewrite recipe <name>@<version> (Migration Phase #1)`
  - `refactor(af5-migration): migrate <kind> <SimpleClassName> to AF5 (Migration Phase #N)` — kind ∈ {aggregate, event handler, command dispatch in, query dispatch in, query handler, configuration class}
  - `feat(af5-migration): wire AggregateBased{Jpa,AxonServer}EventStorageEngine (Migration Phase #8)`
  - `fix(af5-migration): <one-line>` — stabilization
  - `docs(af5-migration): record decision on <recipe>/<target>` — decision-only (no code)
  - `chore(af5-migration): remove isolated-* scaffolding`
- **Never** `git push`, `git commit --amend`, `--no-verify`, commit on `main`/`master`, or `git add -A`.
- **Never** silently delete an AF4 bean / registration / fixture when its AF5 successor is missing — comment it out + `TODO[AF5 migration: <blocker-key>]` + record in `progress.md` + `learnings.md`.

After every non-trivial commit, suggest `/clear` — phase boundaries especially.

## Anti-patterns

- Running `./mvnw verify` between Migration Phase #1 and FINALIZE (it WILL fail by design — use per-target `axon4to5-isolatedtest` scopes instead).
- Re-running OpenRewrite to "fix" what a per-construct recipe couldn't handle.
- Treating `event-storage-engine` as auto-configured by the Spring Boot starter — the AF5 starter applies AF5 defaults, not a migration of the existing AF4 event store. The explicit `AggregateBased…EventStorageEngine` bean swap is mandatory.
- Editing files outside the recipe's scope to "clean up" — keep diffs atomic.
- Running a recipe in a subagent when its Procedure uses `AskUserQuestion` — those prompts must reach the main conversation.

## Evals

Executable. Real AF4↔AF5 pairs from `.knowledge/repositories/axon-examples/` drive the suite — one bash runner + one `.case` file per scenario, each with `require:` / `forbid:` grep patterns against the AF5 reference.

```bash
./skills/axon4to5-migrate/evals/run.sh          # all cases
./skills/axon4to5-migrate/evals/run.sh aggregate # filter by name substring
```

See [evals/README.md](evals/README.md) for the case format and coverage table.
