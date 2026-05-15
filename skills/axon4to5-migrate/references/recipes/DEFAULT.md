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
- **Blocker 🚧** — NOTES: name the unresolved item plus its location; caller must resolve before re-running. LEARNINGS (optional): anything beyond the blocker itself that surprised the recipe while researching scope. OPTIONS: required — see § Blocker OPTIONS baselines below.
- **Rejected ⏭️** — NOTES: which `# Applicable` predicate failed and the observed fact that caused it. LEARNINGS (optional): only if rejection itself was unexpected (e.g. `$SOURCE` looked like an aggregate at first glance but turned out to be a projector after closer inspection).
- **Failure ❌** — NOTES: failing `# Success Criteria` items + the last error **verbatim** (compiler / test / exception tail — do not paraphrase). LEARNINGS: nearly always present here — failure means something didn't work, and the next iteration needs the hypothesis.

## Success Criteria baseline

Per-recipe `# Success Criteria` inherits these checks. Recipes may **add** criteria (e.g. recipe-specific structural invariants) but MUST NOT remove the baseline. Aggregation rule: **all criteria match** (AND); recipe extensions keep AND unless the recipe explicitly overrides.

### Baseline criteria — always in effect

1. **Compile-clean** — every file in `# Scope` (main + test sources) compiles against Axon 5 dependencies. Missing-symbol errors against files OUTSIDE `# Scope` mean the scope is too narrow — re-research at FLOW.md S2, do NOT silence with excludes.
2. **Tests green** — if `# Scope` contains test classes that use `AggregateTestFixture`, every `@Test` method passes. Zero `@Test` methods in scope counts as criterion not-applicable (not match) — surface "no test coverage" as a **Learning** in the result block. Tests that do NOT use `AggregateTestFixture` (e.g. integration tests, Mockito-only tests, Spring context tests) are **out of scope** — do not include them in `test-sources`, do not fail on them, do not attempt to fix them.
3. **No silent behavioural regressions in the scoped slice** — assertions in migrated tests reflect AF5 semantics (record-style `payload()` / `metaData()` accessors, AF5 exception types). A flipped expectation that matches AF5 reality counts as match; silently weakened assertions do NOT.

### Verification — `axon4to5-isolatedtest` Skill (default mechanism)

Recipes MUST verify (1) and (2) by invoking the `axon4to5-isolatedtest` Skill — do NOT hand-craft `./mvnw -P...` / `./gradlew :test...` commands. The Skill scopes compile+test to one self-contained build profile / Gradle source-set per target, derived from `# Source` and `# Scope`.

Invocation template (recipes reuse verbatim; fill brackets from current scope):

```yaml
Skill: axon4to5-isolatedtest
Inputs:
  target-name: <SimpleClassName>          # simple class name of $SOURCE (PascalCase). Drives the scope id.
  build-file: <abs path to pom.xml | build.gradle(.kts)>   # the module that owns $SOURCE, not the reactor parent.
  main-sources: [<repo-relative paths to every main file in # Scope>]
  test-sources: [<repo-relative paths to every test file in # Scope>]   # [] when no test class exists.
  extra-deps:  [<axon5 coordinates needed by the slice, e.g. org.axonframework:axon-modelling>]
  cleanup: false                          # set true ONLY on the recipe's final green run before commit.
```

Behaviour:

- Adds / augments an `isolated-<TargetName>` Maven profile (or Gradle source-set). Idempotent — re-invocation augments include lists, never replaces.
- Returns compile result + test counts. A red compile or red test flips the recipe's S5 check to **mismatch**.
- `cleanup: true` removes the scope iff compile + tests are both green; on non-green runs the scope is always kept.

**Multi-module:** `build-file` MUST point to the module that owns `$SOURCE`, never the reactor parent `pom.xml`.

### Idempotency / pre-Apply check

`# Success Criteria` is evaluated **on first visit to FLOW.md S5** (before any Apply) AND after each Apply. If the baseline criteria already match on the first visit:

- Recipe returns **Success** with `NOTES: edits=none (idempotent)` per FLOW.md.
- Do NOT ask the user "skip vs deep-verify" — FLOW.md owns the loop; no extra decision point at this stage.

### Out of scope for the baseline

- Project-wide `clean verify` / full-module test run — happens once at the orchestrator's FINALIZE step after every `isolated-*` scope is cleaned up. Not a recipe-level Success Criterion.
- Cross-recipe verification (e.g. "the projector still receives events from the migrated aggregate") — recipe boundaries are deliberately narrow; integration concerns belong to the orchestrator.
- **Tests not backed by `AggregateTestFixture`** — integration tests, Mockito-only tests, Spring context tests, and any test class that does not directly use `AggregateTestFixture` are out of scope. Do NOT add them to `test-sources`, do NOT treat their failures as a recipe-level criterion, and do NOT attempt to fix them.

## Blocker Options baselines

On `Result: Blocker`, the recipe MUST enumerate continuation paths in an **Options** list (see FLOW.md § Result). The three baseline options below are **always** present in every Blocker result — recipes do not need to restate them, but must not remove them. Recipes MAY extend the list when there is a genuine recipe-specific path.

- [ ] **skip** — keep `$SOURCE` in its current partial state (whatever edits the recipe applied before halting stay). The queue moves on; the blocked item shows up in the final report so the caller knows to revisit it.
- [ ] **revert** — undo every edit this recipe applied to `$SOURCE` and any of its in-scope dependencies; restore the pre-recipe state. Use when the partial state is worse than no migration at all. The queue moves on; the item shows in the final report as reverted.
- [ ] **solve-manually** — pause this item. Surface the blocker to the caller so they can fix it by hand outside the skill, then re-invoke the skill to continue.

## Blocker resolution strategy

Delegated to [`BLOCKER_RESOLUTION.md`](BLOCKER_RESOLUTION.md). Recipes do not implement resolution logic — they only emit the **Options** list above.
