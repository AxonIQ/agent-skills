# Recipe Contract

Recipes are procedural guides. Run one target at a time unless the recipe
explicitly says a read-only planning fan-out is safe.

## Required Sections

Every `references/<recipe>/<recipe>.md` file should have:

- `## Canonical reference`
- `## Inputs`
- `## Preflight`
- `## Procedure`
- `## End condition`
- `## Output`

Order can vary. Optional sections such as `Goal`, `In scope`, `Out of scope`,
`FQN cheat sheet`, `Caveats`, `Examples`, and `Subagent guidelines` are allowed.

## Run a Recipe

1. Validate inputs against `## Inputs`.
2. Run `## Preflight`. If already migrated, emit `result: skipped`.
3. Read sibling `not-supported.md` first when present; unresolved blockers emit
   `needs-decision` or `blocked`.
4. Run `## Procedure`.
5. Verify `## End condition`.
6. Emit exactly one `## Output` YAML block.

## Output

The only discriminator is `result:`:

```yaml
result: success | skipped | rejected | needs-decision | blocked | failed
target: <file path or FQCN>
reason: <required except straightforward success>
decisions: {}
caller-expects:
  commit: true | false
  next: proceed | ask-user | record-and-skip | halt | route-to:<recipe>
notes: []
```

Worked examples live in [output-contract.md](output-contract.md).

## Subagents

Use a subagent only when the recipe declares `## Subagent guidelines` and the
next work does not require an immediate user decision. The main runner owns
state, edits that cross recipe boundaries, verification, and commits.

If a subagent is used, prompt it with:

> Read `references/<recipe>/<recipe>.md`, execute `## Procedure` for these
> inputs, and return a filled `## Output` block. Do not commit.

## Forbidden in Recipes

- migration phase wording except the exact commit-log phrase
  `Migration Phase #N`;
- sibling recipe links, except the debug recipe whose job is routing;
- recipe-owned edits to `progress.md`, `learnings.md`, or `index.md`;
- duplicated conceptual docs or full FQN tables already present under `docs/`;
- legacy output fields: `needs-user-decision`, `needs-user-decision-reason`,
  `recipe-status`, `skip`.

Recipes may tell the runner what to record, but the runner writes state and
commits.
