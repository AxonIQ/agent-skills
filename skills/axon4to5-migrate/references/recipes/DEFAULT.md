# Recipe defaults

Orchestrator-side defaults applied to every recipe under `references/recipes/`. Recipes may augment but cannot override. Loaded implicitly by FLOW.md — recipes do not link to this file.

## Source file conventions

Applies to **every** discovery, `# Scope`, `# Applicable`, and `# Blocker` grep/glob in every recipe.

- **Language is `.java` OR `.kt`.** JVM projects are routinely mixed. A recipe's `# Use cases` show Java shapes, but the same Axon annotations/imports apply verbatim to Kotlin — never skip a `.kt` file because the examples are Java.
- **Source directory is NOT a language signal.** Kotlin files frequently live under `src/main/java/` (and vice-versa). In a mixed project anything is possible. NEVER scope a scan to `src/main/kotlin/` or filter candidates by directory.
- **Key on Axon annotations / content, not path or extension.** When globbing, cover both extensions (`**/*.{java,kt}`); when grepping by annotation (`@Aggregate`, `@Saga`, `@ProcessingGroup`, `@QueryHandler`, …) let the annotation be the filter — match across all source roots regardless of where the file sits.
- **Filename-pattern globs are heuristics, not gates.** `*Configuration.java`, `<target>Test`, etc. are hints; extend them to `.kt` (`*Configuration.{java,kt}`, `extends|:` for Kotlin supertypes) and never reject a real match for failing the `.java` shape.
- **Don't over-narrow.** Broadening a grep to catch a missed file must not tighten it for other concepts — keep annotation matches as wide as before. A file missed this way is an `other:gradle-kt-under-java`-class learning.

## Toolbox baseline

Always in effect; no recipe needs to list it explicitly:

- **Use the Migration paths catalog (`# References`) to assemble the plan.** At FLOW.md S6 (Plan Migration), pick paths whose apply-conditions match current scope, then translate their guidance into concrete edits. Recipe-level `# Toolbox` entries are for *additional* procedures the catalog does not cover.

## Result NOTES / LEARNINGS baselines

The result block carries a required free-text `NOTES` field and a required `LEARNINGS` section — one dated entry per fired trigger, or an explicit `none` on a clean run; see FLOW.md § Result. The recipe's own `# Result` subsections, if present, append recipe-specific facts on top of the baseline below.

### NOTES — always present, keep it a summary

- One short paragraph or two-three bullets. Why this result; what the caller should look at next.
- Use an outcome emoji to make the result scannable: ✅ Success, 🚧 Blocker, ⏭️ Rejected, ❌ Failure.
- **Do NOT enumerate files changed** — `git diff` is authoritative; duplicating it is noise.
- Mention retries only if non-trivial (e.g., "succeeded on retry after extending scope").

### Learning Triggers

**This is the canonical list. FLOW.md, DURABILITY.md, and the recipe template reference it by name — do not restate it elsewhere.**

**Governing rule (the principle):** write a learning for **any surprise, discovery, or deviation that would help a later item or recipe run more smoothly.** Learnings are forward-looking aids: future runs read them (recipes consult `# Gotchas`; the orchestrator reads `learnings.md` on surprise). If you learned something the recipe docs did not already tell you, the next run should inherit it. *That* is the test — not a fixed checklist.

A learning is **not only a record of what failed**. It is just as valuable — often more — when the migration **succeeded despite a difficulty**: something was problematic, you found the way through, and you record both the problem **and how you solved it**. That is exactly the feedback that lets the recipe (and its `# Gotchas`) absorb the difficulty so the next iteration runs smoother. Put the solution in the entry's `**Resolution:**`; treat the entry as feedback aimed at improving the recipe, not just a diary of trouble.

**Mandatory floor (non-exhaustive).** Each named case below is an objective condition; whenever one holds, a learning is **required** — never hand-wave it as "trivial". The list is a **floor, not a ceiling**: a surprise matching none of them but meeting the governing rule above is *equally* required, recorded under `other:<short-tag>`.

| tag | always a learning when… |
|-----|-------------------------|
| `retry` | a 2nd Apply attempt was consumed (FLOW.md retry budget used). |
| `compile-error` | a compile error occurred that this recipe's `# Toolbox` / `# Gotchas` did **not** predict. |
| `api-shape` | an import path, class name, or method signature differed from what the recipe docs predicted. |
| `project-shape` | project annotations / deps / module layout forced a deviation from the recipe's `# Use cases` or `# Toolbox`. |
| `investigation` | a step needed external investigation (`javap` on a jar, grep to find a package, context7 MCP). |
| `blocker` | a blocker was detected (regardless of how it was resolved). |
| `secondary-module` | a microservices / secondary module had a different shape needing separate handling. |
| `no-test-coverage` | Success Criterion "tests green" was not-applicable (zero `AggregateTestFixture` tests in scope). |
| `other:<tag>` | any other surprise / discovery meeting the governing rule (e.g. `other:gradle-kt-under-java`). |

### LEARNINGS — one entry per fired trigger; explicit `none` otherwise

The `**Learnings:**` field is **always present** — silence is never allowed. Its value is one of:

- **One complete dated entry per fired trigger** — see FLOW.md § Result for the in-block shape and DURABILITY.md § `learnings.md` schema for the persisted shape. Each entry's `**Trigger:**` field names its tag, so the taxonomy lives in the entries themselves. Short, scannable, `file:line` whenever possible.
- **`none — <one-clause why>`** — only on a genuinely clean run (zero triggers fired). This is a deliberate, auditable claim ("nothing worth telling the next recipe"); the orchestrator may challenge it.

**Validation (orchestrator-side).** A Result with neither entries nor an explicit `none` is an error: inline → orchestrator writes the missing learning itself before committing; subagent → re-request it.

### Per-outcome anchors

- **Success ✅** — NOTES: which Success Criteria passed and whether retries were used. LEARNINGS: one entry per fired trigger (e.g. a test expectation had to flip, the AF5 shape differed from the AF4 mental model); a first-Apply idempotent green run → `none — <why>`.
- **Blocker 🚧** — NOTES: name the unresolved item plus its location; caller must resolve before re-running. LEARNINGS: always a `blocker` entry; add any further surprises hit while researching scope. OPTIONS: required — see § Blocker OPTIONS baselines below.
- **Rejected ⏭️** — NOTES: which `# Applicable` predicate failed and the observed fact that caused it. LEARNINGS: an entry only if rejection itself was a surprise (e.g. `$SOURCE` looked like an aggregate but turned out to be a projector); a routine rejection → `none — <why>`.
- **Failure ❌** — NOTES: failing `# Success Criteria` items + the last error **verbatim** (compiler / test / exception tail — do not paraphrase). LEARNINGS: effectively always present — `retry` and `compile-error` almost always fired, and the next iteration needs the hypothesis.

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

A recipe MAY mark **exactly one** option `(Recommended)`. In `auto=true` the orchestrator picks the `(Recommended)` option; with none marked it falls back to `skip` (see `BLOCKER_RESOLUTION.md § Auto mode`). Mark a non-`skip` option `(Recommended)` **only when it is safe to auto-apply** — otherwise leave `skip` as the implicit recommendation so auto mode defers rather than making a risky judgment call.

- [ ] **skip** — keep `$SOURCE` in its current partial state (whatever edits the recipe applied before halting stay). The queue moves on; the blocked item shows up in the final report so the caller knows to revisit it.
- [ ] **revert** — undo every edit this recipe applied to `$SOURCE` and any of its in-scope dependencies; restore the pre-recipe state. Use when the partial state is worse than no migration at all. The queue moves on; the item shows in the final report as reverted.
- [ ] **solve-manually** — pause this item. Surface the blocker to the caller so they can fix it by hand outside the skill, then re-invoke the skill to continue.

## Blocker resolution strategy

Delegated to [`BLOCKER_RESOLUTION.md`](BLOCKER_RESOLUTION.md). Recipes do not implement resolution logic — they only emit the **Options** list above.
