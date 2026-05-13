# Evals — axon4to5-migrate

Scenario-based evals. Each `NN-*.md` file is one scenario: setup, prompt, expected behavior, pass/fail signals. Run manually in a session with the skill loaded — there is no automated harness yet.

A future automation can read these files as YAML-fronted scenarios and exec the prompt in a sandbox project; for now they're a checklist for human review when the skill changes.

## Scenarios

| # | File | Mode exercised | What it pins down |
|---|---|---|---|
| 01 | [01-routing-aggregate.md](01-routing-aggregate.md) | SINGLE | A file with `@Aggregate` + `@EventSourcingHandler` routes to `aggregate` — not `event-processor`. |
| 02 | [02-routing-command-gateway-vs-handler.md](02-routing-command-gateway-vs-handler.md) | SINGLE | Exclude-when rule: a class that injects `CommandGateway` AND has `@CommandHandler` routes to its handler recipe, not `command-gateway`. |
| 03 | [03-init-license-mandatory.md](03-init-license-mandatory.md) | PHASED first run | INIT asks license BEFORE any recipe runs, including openrewrite. SINGLE mode on a virgin project does the same via `ensure_pinned()`. |
| 04 | [04-resume-phased.md](04-resume-phased.md) | PHASED resume | Fresh session reads `progress.md`, confirms via `AskUserQuestion`, picks up the next item with no re-prompts for pinned decisions. |
| 05 | [05-dirty-tree-on-resume.md](05-dirty-tree-on-resume.md) | PHASED resume | When the working tree has user WIP, orchestrator pauses with three options instead of sweeping into the migration commit. |
| 06 | [06-blocker-comments-not-deletes.md](06-blocker-comments-not-deletes.md) | any | `result: blocked` keeps the AF4 surface commented-out + `TODO[AF5 migration: <key>]`. Never silent delete. |
| 07 | [07-debug-mode-clusters.md](07-debug-mode-clusters.md) | DEBUG | Debug mode clusters errors by root cause, not by message; routes ONE cluster, recompiles, re-clusters. |
| 08 | [08-finalize-cleanup.md](08-finalize-cleanup.md) | FINALIZE | After every row is done, FINALIZE invokes `axon4to5-isolatedtest cleanup:true` per scope, promotes deps, runs full build with no scope active. |
| 09 | [09-no-data-migration.md](09-no-data-migration.md) | any | Skill never emits SQL/DDL, never copies event-store rows. `move-to-*` blocker options are code-rewrite choices; user owns the data move. |

## Pass criteria

A scenario passes when the orchestrator's behavior in that session matches **every** check in the scenario's "Expected behavior" list. A single check failing = scenario fails; record which check failed.

## Adding a new scenario

1. Pick the next `NN`.
2. Use [_template.md](_template.md).
3. Frame the scenario as: starting state → user input → expected orchestrator actions (numbered) → pass/fail signals.
4. Add a row in the table above.
