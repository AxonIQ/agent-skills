# Recipe defaults

Orchestrator-side defaults applied to every recipe under `references/recipes/`. Recipes may augment but cannot override. Loaded implicitly by FLOW.md — recipes do not link to this file.

## Toolbox baseline

Always in effect; no recipe needs to list it explicitly:

- **Use the Migration paths catalog (`# References`) to assemble the plan.** At FLOW.md S6 (Plan Migration), pick paths whose apply-conditions match current scope, then translate their guidance into concrete edits. Recipe-level `# Toolbox` entries are for *additional* procedures the catalog does not cover.

## Result NOTES / LEARNINGS baselines

The result block has one required free-text field (`NOTES`) and one optional free-text field (`LEARNINGS`); see FLOW.md § Result. The recipe's own `# Result` subsections, if present, append recipe-specific facts on top of the baseline below.

### NOTES — always present, keep it a summary

- One short paragraph or two-three bullets. Why this result; what the caller should look at next.
- Use an outcome emoji to make the result scannable: ✅ Success, 🚧 Blocker, ⏭️ Rejected, ❌ Failure.
- **Do NOT enumerate files changed** — `git diff` is authoritative; duplicating it is noise.
- Mention retries only if non-trivial (e.g., "succeeded on retry after extending scope").

### LEARNINGS — optional, surprise-driven

Include LEARNINGS only when the run was **not** straightforward. Trivial green runs do not need this field — omit it.

Reasons to include LEARNINGS:

- **Didn't work first try** — a step needed a retry, a Plan had to be adjusted after a failed Apply, scope had to be extended after Research stabilised.
- **Framework behaviour differed from the recipe's pseudocode** — e.g. a type signature that wouldn't compile as written, an API that returns a different shape than the recipe assumed.
- **Project-specific quirk forced a decision** — custom bean, naming convention, configuration shape the recipe had to discover and adapt to.
- **Suspected cause for failure** (Failure outcome only) — best current hypothesis even if unconfirmed, so the next iteration starts from there.

Short, scannable bullets. Reference `file:line` whenever possible.

### Per-outcome anchors

- **Success ✅** — NOTES: which Success Criteria passed and whether retries were used. LEARNINGS (optional): record only if the recipe was surprised — e.g. a test expectation had to flip, the AF5 shape differed from the AF4 mental model.
- **Blocker 🚧** — NOTES: name the unresolved item plus its location; caller must resolve before re-running. LEARNINGS (optional): anything beyond the blocker itself that surprised the recipe while researching scope.
- **Rejected ⏭️** — NOTES: which `# Applicable` predicate failed and the observed fact that caused it. LEARNINGS (optional): only if rejection itself was unexpected (e.g. `$SOURCE` looked like an aggregate at first glance but turned out to be a projector after closer inspection).
- **Failure ❌** — NOTES: failing `# Success Criteria` items + the last error **verbatim** (compiler / test / exception tail — do not paraphrase). LEARNINGS: nearly always present here — failure means something didn't work, and the next iteration needs the hypothesis.
