---
id: "<component>"
title: "<Human Readable Name>"
description: <one line, starts with "Migrates a single ...">
argument-hint: $SOURCE
---

# <Human Readable Name>

> Authoring template for a single recipe. The orchestrator binds each section below by **its heading** to the matching diagram node in `SKILL.md` (§ Recipe sub-flow). Keep the section names exactly as written; everything inside them is recipe-specific content. Do not describe control flow, retries, or result emission here — those live in `SKILL.md`.
>
> Each section explains *what the section is for* and *what format it must be in*. `<example>` blocks are drawn from the original aggregate-recipe sketch.

## Source

What `$SOURCE` is for this recipe — fully qualified class name or file path. State the shape the recipe expects. Read by FLOW.md S1 before evaluating `# Applicable`.

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

Things the recipe declares as **unresolvable from inside the recipe** — the caller must fix them before re-running. Two categories, both emit `Blocker`:

1. **In-scope unmigrateable constructs** — no known migration path, case too complex for this recipe, or recipe-specific exclusion.
2. **Unmet project-level prerequisites** — facts about the project the recipe assumes hold (build state, classpath, dependencies). The recipe does not enforce these proactively; it surfaces them as `Blocker` when a Success Criterion or Apply step would otherwise hit them blind.

Each entry: one line "what it is + how to spot it + why this recipe can't proceed".

<example>
- `@Deadline` handlers — Deadlines API is being redesigned in Axon 5; no stable migration path yet.
- `@CommandHandlerInterceptor` on aggregate methods — no direct Axon 5 equivalent; requires manual restructuring outside this recipe's competence.
- `ConflictResolver` parameter on handlers — DCB-only concept in Axon 5; preserving Axon 4 semantics needs manual rewrite.
- Project does not compile pre-migration — prerequisite; caller must restore a green build before this recipe can verify Success Criteria.
</example>

## Out of Scope

Negative constraints — things the recipe must refuse to touch even if tempted.

<example>
- Sibling aggregates, projections, sagas
- `application.properties` / Spring config beans
- Logging changes, package renames, formatting
- Anything that doesn't flip a mismatched `Success Criteria` item to a matching state
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

Recipe playbook — pointers to the **Migration paths catalog**. Each entry has an explicit *apply-condition* (a fact about scope that triggers loading the entry). Read by FLOW.md S3 (Research) and re-consulted at S6 (Plan Migration).

<example>
Pick entries from the **Migration paths catalog** (see `SKILL.md` § Migration paths catalog — `references/docs/paths/*.adoc`). Each entry MUST declare an **apply-condition** — a fact about current scope that triggers loading the file.

Format:

```
- path: aggregates/multi-entity-migration.adoc
  apply-condition: scope contains at least one `@AggregateMember`-typed member
```

Do NOT copy content from the catalog into the recipe — only the path and the apply-condition. Do NOT invent paths; only use files that exist under `references/docs/paths/`.
</example>

## Toolbox

Recipe-specific scripts, prompts, pre-baked transformations, or step-by-step procedures consulted at FLOW.md S6 (Plan Migration) — anything NOT already covered by a migration path in `# References`. Each entry has an *apply-condition*. The baseline tool ("use migration paths to assemble the plan") is always in effect and does NOT need to be listed here (see `references/recipes/DEFAULT.md` § Toolbox baseline).

<example>
- name: Migration procedure
  apply-condition: always
  steps:
    1. Rename the aggregate class from `*Aggregate` suffix to `*Entity` (Axon 5 naming).
    2. Replace `@Aggregate` with `@EventSourcedEntity`.
    3. For each `@CommandHandler` constructor → factory method returning the entity.
    4. For each `@EventSourcingHandler` → keep signature, verify state mutation pattern matches Axon 5.
    5. Re-wire repository injection points (Axon 5 uses `EventSourcingRepository<Entity, Id>` directly).
    6. Run the isolated test via `axon4to5-isolatedtest` skill.
</example>

## Examples

Worked examples the LLM can imitate at FLOW.md S6 (Plan Migration). Each entry MUST declare an *apply-condition* — a fact about current scope that triggers loading the example.

<example>
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

**Recipe-specific augmentation only.** Baseline `NOTES` content per outcome is defined in `references/recipes/DEFAULT.md`; that always applies first. Add anything below only when this recipe needs to record fields the default does not cover (e.g., a recipe-specific decision the LLM made, an artifact path, a follow-up the caller should know about). The result block format itself (`RESULT/SOURCE/RECIPE/NOTES`) is fixed by FLOW.md.

### Success

<example>
<!-- TODO: Fill during iterations. -->
</example>

### Blocker

<example>
<!-- TODO: Fill during iterations. -->
</example>

### Rejected

<example>
<!-- TODO: Fill during iterations. -->
</example>

### Failure

<example>
<!-- TODO: Fill during iterations. -->
</example>
