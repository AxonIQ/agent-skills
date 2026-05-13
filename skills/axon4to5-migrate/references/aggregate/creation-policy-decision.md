# Creation Policy Decisions

Use this only when the target aggregate used AF4 `@CreationPolicy` /
`AggregateCreationPolicy`.

## Decision Table

| AF4 policy | AF5 direction | Verify by |
|---|---|---|
| absent | ordinary instance command handler | existing tests |
| `ALWAYS` | explicit creator path; fail if entity already exists | creation + duplicate tests |
| `CREATE_IF_MISSING` | creator path plus existing-instance behavior | tests for both absent and present entity |
| `NEVER` | instance handler only | not-found / existing tests |

OpenRewrite may already have removed annotations and added an entity creator.
Do not add duplicate creators; verify the behavior.

## Procedure

1. Find every command handler that had or implied creation policy behavior.
2. Identify whether the command should create a new entity, update an existing
   entity, or support both.
3. Implement the smallest AF5 shape that preserves tests:

   | Need | Shape |
   |---|---|
   | create only | entity creator emits initial event |
   | update only | instance handler appends events |
   | create if missing | creator handles absent state; instance handler handles present state |

4. Run aggregate fixture tests. A compile-green rewrite is not enough; wrong
   creation semantics often fail only at runtime.
5. If tests cannot express the behavior, record `needs-decision` rather than
   inventing semantics.

## Common Gotcha

If a former `CREATE_IF_MISSING` handler reads fields from null state, AF5 may
throw an NPE where AF4 created implicitly. Fix by splitting creation and update
paths, not by swallowing the NPE.

## Do Not

- Reintroduce AF4 annotations.
- Treat `CREATE_IF_MISSING` as ordinary update-only handling.
- Delete duplicate-command behavior tests.
