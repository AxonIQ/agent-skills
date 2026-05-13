---
name: axon4to5-aggregate
description: Migrates a single Axon Framework 4 Aggregate (with commands and events) into the Axon Framework 5 Entity.
argument-hint: <Source>
---

# axon4to5-aggregate

Follow the procedure to match success criteria.

## Input

- `<Source>` (required) — fully qualified class name or file path of the Axon 4 Aggregate to migrate (the class
  annotated with `@Aggregate` or containing `@AggregateIdentifier`). All commands, events, and members of this aggregate
  are in scope for migration.

## Scope

- `<Source>` aggregate
- Commands and events of the aggregate
- Everything that is needed to make the `Success Criteria` pass. But be conservative, only what is needed!

## Prerequisites

- ``

## Applicable

It's possible that some work was already done - annotation changed etc. So you must also recognize it's already looks
like Axon Framework 5 aggregate, but the `Success Criteria` are not met.

1. Check if the `<Source>` is `State Based` aggregate, not `Event Sourced`.
    1. yes: return `Rejected` output
    2. no: continue
2. Check if it's an Aggregate and have `@EventSourcingHandler`
    1. yes: continue
    2. no: return `Rejected` output

## Success Criteria
If any of the following is not true, then the success criteria are not met.

1. No compilation errors in the Aggregate and commands, events.
2. No compilation errors in the Aggregate Test file (is exist), do not add tests if not exist.
3. **Always** invoke via the Skill tool `axon4to5-isolatedtest` and check if the test passes.

## References

Available resources, read them only if the read condition is met.

### Migration Paths

### Toolbox

### Examples

## Output

### Success

Only if the whole `Success Criteria` pass.

<Template>
<!-- TODO: Fill during iterations. -->

</Template>

<Example>
<!-- TODO: Fill during iterations. -->
</Example>

### Blocker

The migration spotted part that have no clear migration path (like Deadlines).

### Rejected

The migration is not applicable to this component.

### Failure
<!-- TODO: Fill during iterations. -->

## Gotchas

<!-- TODO: Fill during iterations. -->

## Procedure

1. Check if the `<Source>` is applicable to this migration.
    1. yes: continue
    2. no: return `Rejected` output
2. Check the `Success Criteria`.
    1. pass: return `Success` output
    2. otherwise: continue
3. Research the `Scope` of this migration.
4. Based on the `Success Criteria` and `Scope` read `References` and prepare the `Migration Plan`.
5. Apply the planned `Migration Plan`.
6. Check if the `Success Criteria` is met after executing the `Migration Plan`.
    1. yes: return `Success` output
    2. no(already retried): return to step 4, but before research Axon Framework 5 API from source on classpath and
       docs (use `Context7` MCP if available)
    3. no: repeat from step 4 (max 1 retry)
    4. no(still failing after retry and applied step 2): return `Failure` output