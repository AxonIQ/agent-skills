---
name: axon4to5-<component>
description: <one line, starts with "Migrates a single ...">
argument-hint: <Source>
---

# axon4to5-<component>

> Authoring template for a single recipe. The orchestrator binds each section below by **its heading** to the `Recipe section` column in `_contract.md`. Keep the section names exactly as written; everything inside them is recipe-specific content. Do not describe control flow, retries, or result emission here — those live in `_contract.md`.
>
> Each section explains *what the section is for* and *what format it must be in*. `<example>` blocks are drawn from the original aggregate-recipe sketch.

## Input

What `<Source>` identifies — fully qualified class name or file path. State the shape the recipe expects.

<example>
- `<Source>` (required) — fully qualified class name or file path of the Axon 4 Aggregate to migrate (the class annotated with `@Aggregate` or containing `@AggregateIdentifier`). All commands, events, and members of this aggregate are in scope for migration.
</example>

## Scope

What counts as "owned" by `<Source>` for this recipe.

<example>
- `<Source>` aggregate
- Commands and events of the aggregate
- Everything that is needed to make the `Success Criteria` pass. But be conservative, only what is needed!
</example>

## Out of Scope

Negative constraints — things the recipe must refuse to touch even if tempted.

<example>
- Sibling aggregates, projections, sagas
- `application.properties` / Spring config beans
- Logging changes, package renames, formatting
- Anything that doesn't move a red `Success Criteria` item to green
</example>

## Prerequisites

Assumptions about the project before the recipe runs. The orchestrator does not enforce these — the recipe may treat a missing prerequisite as a `Rejected` cause.

<example>
- ``
</example>

## Applicable

Predicates evaluated against `<Source>`'s surface (annotations / type markers). Each predicate is a single observable fact. State the decision rule (AND / OR / heuristic) explicitly. The recipe should also tolerate partial migration (some Axon 5 patterns already applied, but `Success Criteria` not yet green).

<example>
It's possible that some work was already done - annotation changed etc. So you must also recognize it's already looks like an Axon Framework 5 aggregate, but the `Success Criteria` are not met.

1. Check if the `<Source>` is `State Based` aggregate, not `Event Sourced`.
    1. yes: return `Rejected` output
    2. no: continue
2. Check if it's an Aggregate and has `@EventSourcingHandler`.
    1. yes: continue
    2. no: return `Rejected` output
</example>

## Success Criteria

Concrete, verifiable checks (compile output, isolated test result, type re-reads). Recipe authors must phrase each criterion so a re-evaluation answers "green or red" deterministically.

<example>
If any of the following is not true, then the success criteria are not met.

1. No compilation errors in the Aggregate and commands, events.
2. No compilation errors in the Aggregate Test file (if exists). Do not add tests if not exist.
3. **Always** invoke via the `Skill` tool `axon4to5-isolatedtest` and check that the test passes.
</example>

## References

Recipe playbook. Three subsections; each entry has an explicit *read-condition* (a fact about scope that triggers loading the entry).

<example>
Available resources, read them only if the read-condition is met.

### Migration Paths

<!-- TODO: Fill during iterations. -->

### Toolbox

<!-- TODO: Fill during iterations. -->

### Examples

<!-- TODO: Fill during iterations. -->
</example>

## Gotchas

Known constructs with no Axon 5 migration path. Each entry: one line "what it is + where to spot it".

<example>
<!-- TODO: Fill during iterations. -->
</example>

## Result

Per-outcome `NOTES` guidance the recipe author should write into the result block. The block format itself is fixed by `_contract.md`.

### Success

<example>
<!-- TODO: Fill during iterations. -->
</example>

### Blocker

<example>
The migration spotted a part that has no clear migration path (like Deadlines).
</example>

### Rejected

<example>
The migration is not applicable to this component.
</example>

### Failure

<example>
<!-- TODO: Fill during iterations. -->
</example>
