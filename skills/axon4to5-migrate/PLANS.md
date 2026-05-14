# PLANS.md — axon4to5-migrate

Parking lot for forward-looking ideas. Nothing here is implemented yet — do not reference these from `SKILL.md`.

## Future modes

Currently only `single` mode exists. Possible additions (not committed):

- `bulk` — producer enqueues N `(recipe, source)` items discovered via a project-wide scan; processing loop drains them; empty queue → END with aggregated report.
- `interactive` — empty queue loops back to mode selection so the user can chain another migration without re-invoking the skill.

Open questions:

- How to discover sources for `bulk` without false positives? (Grep for `@Aggregate` / `@CommandHandler` etc.)
- Should `Blocker` results in `bulk` abort the batch or just record-and-continue?
- Do we need a `dry-run` cross-cutting flag separate from modes?
