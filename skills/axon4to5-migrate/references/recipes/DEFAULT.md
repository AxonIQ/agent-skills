# Recipe defaults

Orchestrator-side defaults applied to every recipe under `references/recipes/`. Recipes may augment but cannot override. Loaded implicitly by FLOW.md — recipes do not link to this file.

## Toolbox baseline

Every recipe's Plan stage (FLOW.md S6) implicitly has one tool: **consult the migration paths declared in `# References` whose apply-condition matches current scope, and assemble the migration plan from them.** The recipe's own `## Toolbox` is for anything *not* covered by a migration path — recipe-specific procedures, scripts, or transformations.

## Result NOTES baselines

Baseline content for the `NOTES:` line of the recipe result block (see FLOW.md § Result). The recipe's own `# Result` subsections, if present, append recipe-specific facts on top of the baseline.

### Success

State whether the recipe was idempotent or made changes:

- If no edits applied: `edits=none (idempotent)`; the component already satisfied all `# Success Criteria`.
- If edits applied: list the files changed (paths relative to repo root) and any follow-ups the caller should perform (e.g., regenerate Spring config, re-run integration tests outside this recipe's scope).

### Blocker

Name the unresolved item plus where to look:

- For an in-scope unmigrateable construct: name the construct (e.g., `@Deadline handler`) and its location (`file:line`). One short reason why this recipe cannot migrate it.
- For an unmet project prerequisite: name the prerequisite (e.g., "build does not compile pre-migration") and what the caller must restore before re-running.

Caller is expected to resolve the blocker and re-invoke the recipe.

### Rejected

Name the `# Applicable` predicate that failed and the observed fact that caused it. The recipe did not apply any edits.

### Failure

Retry budget was exhausted (2 Applies). Required content:

- Which `# Success Criteria` items are still mismatching.
- The **last error verbatim** (compiler output, test failure message, exception trace tail) — do not paraphrase.

The caller decides whether to retry manually, escalate, or open a Gotchas entry for the next iteration of the recipe.
