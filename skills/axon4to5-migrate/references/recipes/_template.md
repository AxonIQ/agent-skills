---
name: axon4to5-<component>
description: <one-line, starts with "Migrates a single ...">
argument-hint: <Source>
---

# axon4to5-<component>

> Template for every recipe in `references/recipes/`. Copy this file, rename, fill TODOs.
> The parent skill `axon4to5-migrate` invokes this procedure as a nested sub-flow and only reads the final `## Result` block.

## Input

- `<Source>` (required) — fully qualified class name **or** file path identifying the Axon 4 component to migrate.
  Everything *belonging to* `<Source>` (its commands, events, members) is in scope; siblings are not.

## Scope

- `<Source>` itself
- Owned commands / events / members
- Only what is required to satisfy `Success Criteria` (be conservative)

## Out of Scope

- Siblings, other aggregates / projections / sagas
- Cross-cutting refactors (logging, package moves, dependency bumps)
- Anything that doesn't move `Success Criteria` from red → green

## Prerequisites

- (optional) `axon4to5-openrewrite` bulk recipe has been applied
- Project compiles before this recipe runs (record current state in Decision Log otherwise)

## Applicable

The recipe may run on a *partially migrated* `<Source>` — recognize Axon 5 patterns and continue if `Success Criteria` are not yet green.

Detect checks (run in order, first failing check → `Rejected`):

1. `<Source>` is a `<...component-specific predicate...>` <!-- TODO -->
2. `<Source>` uses `<...Axon 4 marker...>` <!-- TODO -->

## Success Criteria

All of the following MUST be true. If any is false → not done.

1. No compilation errors in `<Source>` and its owned types
2. No compilation errors in the matching test file (if it exists — do not create new tests)
3. `axon4to5-isolatedtest` skill (invoked via `Skill` tool) passes for `<Source>`
4. Behavior preserved: <!-- TODO: component-specific invariants, e.g. "no DCB introduced", "AggregateBasedEventStorageEngine kept" -->

## References

Read only when its read-condition matches the current state.

### Migration Paths

<!-- TODO: routing table — when context is X, migrate to Axon 5 construct Y -->

### Toolbox

<!-- TODO: list of Axon 5 APIs / annotations / types this recipe may reach for -->

### Examples

<!-- TODO: minimal before/after snippets -->

## Gotchas

<!-- TODO: known traps discovered during iterations -->

## Phase implementations

> Flow control (sequencing, retry budget, result emission) is owned by the parent `axon4to5-migrate` SKILL.md — see its **Recipe sub-flow** mermaid. Step numbers below match that diagram. This recipe only fills in *what to do* inside each step.

### Step 1 — Applicable?

Lightweight check on `<Source>` alone: "is this recipe the right tool?". Look at annotations / type markers — do NOT read the full owned graph yet. The recipe owns the decision rule — predicates may be combined with AND, OR, weighted heuristics, or partial-migration tolerance as appropriate. Document the rule explicitly in § `Applicable`.

### Step 2 — Define Scope (Research, initial pass)

Read `<Source>` and its owned types only (commands, events, members) to produce the initial scope inventory. Do NOT wander to siblings or cross-cutting code. This inventory may be extended later by the Research loop (see step 3).

### Step 3 — Read References (Research, loops with step 2)

Load only sections of `Migration Paths`, `Toolbox`, `Examples` matching constructs currently in scope (skip what's irrelevant). If References reveal that additional files / types belong in scope (e.g. a snapshot trigger referenced by the aggregate, a related event class) → extend the scope inventory and return to step 2 (re-read only the newly-affected References). The Research loop exits when scope stabilizes and References for everything in scope are loaded.

Output (loop result): the stable scope inventory annotated with the migration paths from References.

### Step 4 — Blocker in scope?

Scan the scope inventory for constructs with **no entry in Migration Paths** (e.g. Deadlines, custom CommandBus interceptors, ConflictResolver). Found → `Blocker`. This is the **only** step from which `Blocker` may be emitted.

### Step 5 — Check Success Criteria

Single check, visited at least once and re-visited after every Apply. Evaluation logic is identical regardless of edit state:

1. Compile `<Source>` + owned types.
2. Compile the matching test file if it exists.
3. Invoke `axon4to5-isolatedtest` via the `Skill` tool for `<Source>`.
4. Check the behavior invariants listed in `Success Criteria`.

Visit context (tracked by orchestrator, not by the recipe):

- **first visit, no edits yet** — green → `Success` (idempotent re-run); red → go to step 6.
- **after Apply, attempts left** — green → `Success`; red → consult Axon 5 sources / context7, then back to step 6.
- **after Apply, retry exhausted** — red → `Failure`.

### Step 6 — Build Migration Plan

Produce a bullet list of concrete edits derived from References + scope inventory, sufficient to flip every red `Success Criteria` item to green.

### Step 7 — Apply Migration Plan

Constraints when executing edits:

- Stay within `Scope`.
- No drive-by refactors (formatting, renames, import cleanup beyond what edits require).

## Result

The orchestrator parses exactly **one** `RESULT:` line. The rest of the block is human-readable context.

```
RESULT: <Success|Blocker|Rejected|Failure>
SOURCE: <fully qualified name or path of <Source>>
RECIPE: axon4to5-<component>
FILES_CHANGED: [<path>, ...]
NOTES: <one short paragraph — why this result, what to look at next>
```

### Success

Emitted only when **all** `Success Criteria` are green.

<Template>
RESULT: Success
SOURCE: <Source>
RECIPE: axon4to5-<component>
FILES_CHANGED: [...]
NOTES: <what was migrated; any deferred follow-ups>
</Template>

<Example>
<!-- TODO: real example after first successful run -->
</Example>

### Blocker

Emitted when the recipe encountered a component that has no clear Axon 5 migration path yet (e.g. Deadlines, custom CommandBus interceptors). The codebase may be left in a partially-migrated state — `NOTES` MUST describe what is left and why.

### Rejected

Emitted when `Applicable` checks fail — the recipe is not the right tool for this `<Source>`. No edits made.

### Failure

Emitted only after the retry budget is exhausted and `Success Criteria` are still red. `NOTES` MUST list the failing criteria and the last error output verbatim.
