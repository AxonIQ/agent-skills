---
name: axon4to5-<component>
description: <one line, starts with "Migrates a single ...">
argument-hint: $SOURCE
---

# axon4to5-<component>

> Authoring template for a single recipe. The orchestrator binds each section below by **its heading** to the matching diagram node in `SKILL.md` (§ Recipe sub-flow). Keep the section names exactly as written; everything inside them is recipe-specific content. Do not describe control flow, retries, or result emission here — those live in `SKILL.md`.
>
> Each section explains *what the section is for* and *what format it must be in*. `<example>` blocks are drawn from the original aggregate-recipe sketch.

## Input

What `$SOURCE` identifies — fully qualified class name or file path. State the shape the recipe expects.

<example>
- `$SOURCE` (required) — fully qualified class name or file path of the Axon 4 Aggregate to migrate (the class annotated with `@Aggregate` or containing `@AggregateIdentifier`). All commands, events, and members of this aggregate are in scope for migration.
</example>

## Scope

What counts as "owned" by `$SOURCE` for this recipe.

<example>
- `$SOURCE` aggregate
- Commands and events of the aggregate
- Everything that is needed to make the `Success Criteria` pass. But be conservative, only what is needed!
</example>

## Blocker

Constructs the recipe explicitly declares as **unmigrateable** — could be due to no known migration path, a case too complex for this recipe, or a recipe-specific exclusion. If any of these is found in scope, the recipe emits `Blocker`. Each entry: one line "what it is + how to spot it + why we can't migrate".

<example>
- `@Deadline` handlers — Deadlines API is being redesigned in Axon 5; no stable migration path yet.
- `@CommandHandlerInterceptor` on aggregate methods — no direct Axon 5 equivalent; requires manual restructuring outside this recipe's competence.
- `ConflictResolver` parameter on handlers — DCB-only concept in Axon 5; preserving Axon 4 semantics needs manual rewrite.
</example>

## Out of Scope

Negative constraints — things the recipe must refuse to touch even if tempted.

<example>
- Sibling aggregates, projections, sagas
- `application.properties` / Spring config beans
- Logging changes, package renames, formatting
- Anything that doesn't flip a mismatched `Success Criteria` item to a matching state
</example>

## Prerequisites

Assumptions about the project before the recipe runs. The orchestrator does not enforce these — the recipe may treat a missing prerequisite as a `Rejected` cause.

<example>
- ``
</example>

## Applicable

Predicates evaluated against `$SOURCE`'s surface (annotations / type markers). Each predicate is a single observable fact. State the decision rule (AND / OR / heuristic) explicitly. The recipe should also tolerate partial migration (some Axon 5 patterns already applied, but `Success Criteria` not yet matching).

<example>
It's possible that some work was already done - annotation changed etc. So you must also recognize it's already looks like an Axon Framework 5 aggregate, but the `Success Criteria` are not met.

1. Check if the `$SOURCE` is `State Based` aggregate, not `Event Sourced`.
    1. yes: return `Rejected` output
    2. no: continue
2. Check if it's an Aggregate and has `@EventSourcingHandler`.
    1. yes: continue
    2. no: return `Rejected` output
</example>

## Success Criteria

Concrete, verifiable checks (compile output, isolated test result, type re-reads). Each criterion must answer `match` or `mismatch` deterministically. State the **aggregation rule** explicitly — does the recipe require all criteria to match, a subset, or weighted? The recipe owns the verdict on whether the migration is done.

<example>
If any of the following is not true, then the success criteria are not met.

1. No compilation errors in the Aggregate and commands, events.
2. No compilation errors in the Aggregate Test file (if exists). Do not add tests if not exist.
3. **Always** invoke via the `Skill` tool `axon4to5-isolatedtest` and check that the test passes.

Aggregation rule: all three criteria must match.
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

Free-text notes accumulated from previous migrations and iterations — lessons learned, edge cases discovered, things that surprised the author. Not a rigid format; bullets, paragraphs, or short stories all welcome. The recipe (and the LLM running it) may consult these any time relevant — typically while planning or adjusting.

<example>
- Spring `@Configuration` classes wired the old `Repository` directly — after the migration, that bean disappears; check Spring config before claiming Success.
- First attempt at `Order` aggregate failed because a `@MetaData` field on the command was silently dropped — remember to verify metadata propagation after the rename.
- The isolated test sometimes fails on Windows due to file-locking on the event store — re-run once before treating it as a real failure.
</example>

## Result

Per-outcome `NOTES` guidance the recipe author should write into the result block. The block format itself is fixed by `SKILL.md` (§ Result emission).

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
