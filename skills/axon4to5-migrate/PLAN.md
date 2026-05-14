# PLAN.md — Features to incorporate from legacy variants

Comparison sources:
- **A** = `agent-skills-final/skills/axon4to5-migrate` (current)
- **B** = `agent-skills/skills/axon4to5-migrate` (legacy 1)
- **C** = `agent-skills-clones/agent-skills-claude` (legacy 2)

---

## 1. DEBUG mode (triage from build errors)

**Source:** B + C  
**Status in A:** missing

B and C both expose a third invocation mode alongside PHASED / SINGLE:

```
DEBUG: compile full project → cluster diagnostic output →
       identify highest-leverage error cluster →
       route that cluster to the matching recipe →
       re-compile → repeat until green (or ask user)
```

**Why valuable:** Users often arrive mid-migration with a red build and no clear next step.
DEBUG gives a mechanical entry point without requiring them to identify which recipe applies.
Also useful after an abrupt session end that left the tree in a partially-migrated state.

**Spec sketch:**
- New `mode=debug` argument value.
- Step 1: run full compile (no isolated scope), collect all errors.
- Step 2: group errors by affected class/package into clusters (similar import prefix, same annotation type, etc.).
- Step 3: for the largest/highest-leverage cluster, look up which routing-table recipe matches via discovery grep.
- Step 4: execute that recipe for affected files.
- Step 5: recompile; if still red loop from step 2; if green → done.
- Escape: if loop stalls (no cluster matches a recipe) → surface to user with `AskUserQuestion`.

---

## 2. INIT / FINALIZE lifecycle in project mode

**Source:** B + C  
**Status in A:** partial — durability.md covers state but INIT/FINALIZE steps are implicit

### 2a. INIT step

B and C both have an explicit INIT phase on first PHASED/project run:

- Create `.axon4to5-migration/` state dir from templates.
- **Pin three mandatory decisions once and store in `progress.md`:**
  1. `license` — detect whether project uses commercial AxonIQ artifacts; compute recommendation (`axon` vs `axoniq`); ask if ambiguous.
  2. `wiring` — detect Spring Boot vs native Configurer style; ask if ambiguous.
  3. `build-tool` — detect Maven vs Gradle; ask if ambiguous.
- Scan the routing table for blockers detected at project level (e.g. `@DeadlineHandler`, Mongo extension) and record them in progress.md before any recipe runs.
- Emit one commit: `chore(af5-migration): initialize migration`.

**Why valuable:** Currently `framework` and `configuration` are passed as CLI args, which pushes the detection burden to the user. INIT moves detection into the skill, makes the choice auditable in `progress.md`, and ensures every recipe downstream reads from a pinned value rather than re-detecting.

### 2b. FINALIZE step

After all routing-table rows are done:

- For each `isolated-<X>` Maven profile / Gradle source-set: call `axon4to5-isolatedtest cleanup:true`.
- Promote AF5 BOM / dependency versions from isolated profiles back to `<dependencies>` or `build.gradle`.
- Run full build (no isolated scope); if red → classify failure (recipe gap / missed dep / env) and reopen relevant phase or ask user.
- Update `progress.md` to done.
- Emit one commit: `chore(af5-migration): remove isolated-* scaffolding`.

**Why valuable:** The current skill leaves cleanup implicit. FINALIZE makes the "done" state explicit and ensures no isolated scaffolding leaks into the final codebase.

---

## 3. Six-variant Output contract

**Source:** B + C  
**Status in A:** four outcomes used (success/rejected/blocked/failure); `skipped` and `needs-decision` not formalized

B and C define a strict discriminated union for every recipe return:

| `result` | Meaning | Commit? |
|---|---|---|
| `success` | end-condition passed | code + progress.md |
| `skipped` | already migrated; no-op | none |
| `rejected` | wrong recipe; may `route_to` another | none |
| `needs-decision` | human choice required; pause | none |
| `blocked` | AF5 feature gap; comment-out + TODO | progress.md only (or code if partial) |
| `failed` | unexpected error | none; surface + ask |

**Why valuable:**
- `skipped` prevents re-applying recipes on already-migrated code (idempotency without special-casing).
- `needs-decision` is distinct from `blocked` — blocked = AF5 has no feature; needs-decision = user must pick between valid options (e.g. which event-store backend).
- `route_to` on `rejected` enables automatic re-routing (e.g. a file that looks like a command-gateway but is actually a config-reader).

---

## 4. Routing table — `exclude-when` conditions

**Source:** B + C  
**Status in A:** routing table exists but lacks exclusion predicates

B and C tag each routing-table row with an `exclude-when` pattern:

```
command-gateway  | CommandGateway            | exclude: @CommandHandler | @EventHandler | @QueryHandler | @MessageHandlerInterceptor
query-gateway    | QueryGateway              | exclude: @CommandHandler | @EventHandler | @QueryHandler
interceptors     | MessageDispatchInterceptor| exclude: @CommandHandler | @EventHandler | @QueryHandler
```

**Why valuable:** Without exclusions, handler classes that _inject_ a gateway get falsely matched by the gateway recipes. Exclusions reduce false positives during project-mode discovery at near-zero cost.

---

## 5. Auto-policies per blocker

**Source:** C primarily  
**Status in A:** `auto=true` blanket-skips all blockers

C associates each blocker (B1–B10) with an `auto-policy` field:

```
B3 (SagaTestFixture)     → auto-policy: surface-and-skip-test (recommended)
B4 (@DeadlineHandler)    → auto-policy: pause (recommended)
B5 (MongoTokenStore)     → auto-policy: ask-user (fallback)
B7 (axon-kafka)          → auto-policy: ask-user (fallback)
```

**Why valuable:** Not all blockers are equal. `B3 SagaTestFixture` is low-risk to skip silently; `B4 @DeadlineHandler` should pause (removing it accidentally breaks runtime behavior). Per-blocker policies make `auto=true` safe enough to use in CI-like scenarios while still protecting dangerous blockers.

**Spec sketch:**
- Each blocker definition in `BLOCKER_RESOLUTION.md` (or a new `references/blockers.md`) gains an `auto-policy` field.
- When `auto=true`, the skill reads the blocker's `auto-policy` instead of always skipping.
- Values: `skip` | `pause` | `surface-and-skip` | `ask-user`.

---

## 6. `config-reads` recipe

**Source:** B + C  
**Status in A:** missing

B and C have a dedicated recipe for migrating code that reads the Axon `Configuration` object directly:

```java
// AF4 — reads from Configuration
Configuration config = ...;
config.commandBus();
config.queryBus();
config.eventProcessingConfiguration().eventProcessorByProcessingGroup(...);
```

These patterns appear in integration tests, lifecycle beans, and custom configurers. They are NOT covered by aggregate / event-processor / gateway recipes.

**Why valuable:** Production projects frequently have test infrastructure or configuration modules that directly access `Configuration`. Without this recipe they silently stay broken after the main migration phases complete.

**Spec sketch:**
- New recipe `references/recipes/config-reads/RECIPE.md`.
- Discovery grep: `\.commandBus()\|\.queryBus()\|\.eventProcessor` (on `Configuration` receiver).
- Scope: the file containing the accessor call + any wiring class that registers it.
- Phase: after interceptors (last iterative phase) or as part of event-store phase.

---

## 7. Fan-out readonly subagent pattern

**Source:** B + C  
**Status in A:** `execution=subagent` dispatches full recipe subagents (including edits)

B and C describe a two-stage parallelism model:

1. **Fan-out (readonly):** spawn one subagent per discovered item; each subagent reads the file, consults references, and produces a _migration plan_ (structured markdown with proposed edits — no file writes).
2. **Apply (serial, main session):** orchestrator reads each plan, applies edits, runs isolated verify, commits.

**Why valuable:**
- Subagents that also write create merge conflicts and interleaved commits that are hard to recover.
- Read-only subagents are safe to run in unlimited parallelism.
- Main session owns all state mutations → progress.md stays consistent.

**Spec sketch:**
- Recipe adds `## Subagent guidelines` section declaring `mode: readonly-analysis`.
- Orchestrator, when `max-subagents > 0`, fans out analysis subagents, collects plans, then applies them in the main session sequentially.
- Blockers that require `AskUserQuestion` always force inline (no subagent for that item).

---

## 8. Anti-silent-deletion rule (explicit)

**Source:** B + C  
**Status in A:** mentioned in BLOCKER_RESOLUTION.md but not enforced as a hard rule

B and C both have an explicit, hard prohibition:

> When an AF4 construct has no AF5 successor, NEVER delete it. Comment it out and emit a `// TODO[AF5 migration: <blocker-key>] <reason>` marker.

This rule applies even on `auto=true` runs.

**Why valuable:** Deleted AF4 code is invisible in the blame/log once the migration commit lands. A commented-out `@DeadlineHandler` with a TODO marker is immediately obvious to any engineer who opens the file, and is trivially restored when AF5 adds the feature.

**Spec sketch:**
- Add as a `## MUST NOT` item in SKILL.md (not just in BLOCKER_RESOLUTION.md).
- Each blocker that results in code removal must explicitly state the comment-out format.
- Blocked items include the `blocker-key` in the commit message notes.

---

## 9. PHASED mode — continue / pause / stop checkpoints

**Source:** B + C  
**Status in A:** project mode drains the whole queue without mid-phase checkpoints

B and C add an `AskUserQuestion(continue / pause / stop)` between phases:

```
Phase 2 (aggregates) complete — 3 success, 1 blocked.
→ [continue] [pause] [stop]
```

**Why valuable:**
- Users can inspect migrated code before committing to the next phase.
- Pause lets a user run the app, spot issues, fix manually, then resume.
- Stop gracefully closes the state file so the next session can resume cleanly.

**Spec sketch:**
- After each routing-table row drains, emit a brief phase summary (N success / M blocked / K failed).
- Prompt user: continue / pause / stop (unless `auto=true`).
- If pause/stop: write `progress.md` resume pointer + emit a checkpoint commit.

---

## 10. Dirty working tree handling on resume

**Source:** C  
**Status in A:** not addressed

C adds a check on resume: if `git status --porcelain` shows unstaged files not belonging to the last known recipe scope, the orchestrator asks:

> Unexpected dirty files detected. How to proceed?
> - Stage only migration files and continue
> - Let me clean up manually (pause)
> - Skip this commit and continue

**Why valuable:** Sessions that end abruptly (context limit, crash, forced exit) can leave partial edits. Resuming blindly may commit unrelated work or lose it silently.

---

## Priority summary

| # | Feature | Impact | Effort | Suggested order |
|---|---|---|---|---|
| 2a | INIT step + pinned decisions | High | Medium | 1 |
| 3 | Six-variant Output contract | High | Low | 2 |
| 4 | Routing table exclude-when | High | Low | 3 |
| 5 | Per-blocker auto-policies | High | Low | 4 |
| 6 | config-reads recipe | Medium | Medium | 5 |
| 9 | Phase checkpoints | Medium | Low | 6 |
| 1 | DEBUG mode | Medium | High | 7 |
| 7 | Fan-out readonly subagents | Medium | Medium | 8 |
| 2b | FINALIZE step | Medium | Medium | 9 |
| 8 | Anti-silent-deletion (explicit) | Low | Low | 10 |
| 10 | Dirty tree handling on resume | Low | Low | 11 |
