# Migration Skill Template

Skeleton for a generated `axon4to5-<scope>` skill. The generator (the
`migration-skill-creator` parent) owns the iteration loop and reflection;
the generated skill is consumed by **end users** migrating their own
projects. It must read as a standalone migration tool, not as a contributor
artifact of this repo.

Copy the fenced block below into the new skill's `SKILL.md`, then fill
every `<...>` placeholder. Strip sections that genuinely do not apply, but
the default expectation is that all of them stay.

Keep the generated skill **project-agnostic** (framework terms only) and
**atomic** (one candidate per run). Project-specific knowledge lives in
`references/examples/`, never in the procedure.

---

```markdown
---
name: axon4to5-<scope>
description: >
  Migrate ONE <source-construct> to <target-construct> in an Axon Framework 4
  project being upgraded to AF5. Use when the user says "migrate <source>",
  "convert <source-construct>", or describes a <scope> step. Atomic — exactly
  one candidate per run. Behavior-preserving: AF4 semantics, no DCB, legacy
  event store retained. Reads either Spring Boot or plain Axon Configuration
  AF4 source; output flavor is controlled by the `--configuration-mode`
  argument (default `spring-boot`).
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(git diff:*), AskUserQuestion
argument-hint: "[--configuration-mode=spring-boot|axon-configuration] [target class or file path]"
---

# <Source> → <Target>: <Scope>

## Goal

Transform a single <source-construct> instance into <target-construct> while
preserving AF4 semantics.

**Done when**:

- diff produced (or zero diff — the candidate may already be on AF5 form
  thanks to a prior pass, an OpenRewrite recipe, or a hand edit), and the
  human reviewer accepts the result.
- If technically possible to verify: the touched classes compile without
  errors, and tests of the migrating concept (e.g. that Aggregate / Saga /
  handler) pass — when such tests exist.

The project as a whole is expected to remain broken until peer constructs
catch up — that is normal mid-migration. Do **not** treat full project
build success as a gate.

**Idempotency.** Earlier tooling (OpenRewrite recipes, manual edits,
prior runs of this skill) may have already applied some or all of the
target form. The skill must check the candidate against the AF5 target
shape **first** and short-circuit when the goal is already reached — no
re-edit, no spurious diff, just report "already migrated".

## What this migrates

- **From**: <concrete identifier — annotation, class shape, config key>
- **To**: <concrete AF5 form, with canonical API reference>
- **Scope per run**: exactly one candidate (see Selection rule)
- **Languages**: Java, Kotlin (translate examples as needed)
- **Source side (AF4)**: this skill recognizes the construct in either
  Spring Boot or plain Axon Configuration AF4 code. The recognition rules
  are in `references/docs/` (the AF4 forms covered by the migration-path).
- **Target side (AF5)**: chosen by the caller via the
  `--configuration-mode` argument — not detected. Cross-flavor migrations
  are valid (e.g. AF4 plain-Axon → AF5 Spring Boot).

## Arguments

Parse from `$ARGUMENTS`:

| Argument | Values | Default | Meaning |
|----------|--------|---------|---------|
| `--configuration-mode` | `spring-boot` \| `axon-configuration` | `spring-boot` | Target AF5 wiring flavor |
| positional | class name, FQN, or file path | (empty) | Pin the candidate; otherwise selection rule applies |

The source flavor is **not** an argument — the skill reads what is there.
The target flavor is **always** an argument and the default is
`spring-boot`. The four AF4→AF5 combinations are all valid:

| AF4 source | `--configuration-mode` | AF5 output |
|------------|------------------------|------------|
| Spring Boot | `spring-boot` (default) | Spring Boot |
| Spring Boot | `axon-configuration` | plain Axon Configuration |
| plain Axon | `spring-boot` (default) | Spring Boot |
| plain Axon | `axon-configuration` | plain Axon Configuration |

## Selection rule

1. If the user names a target (class name, file path) in `$ARGUMENTS`, use it.
2. Otherwise: `Grep` for the source pattern (Spring or plain Axon form),
   take the **first** match by lexical file path.
3. Never migrate more than one candidate per run.

## Procedure

1. **Parse arguments.** Read `$ARGUMENTS`. Resolve
   `--configuration-mode` (default `spring-boot`) and any positional
   target. Echo the resolved values back to the human so the choice is
   visible.

2. **Select and read the relevant migration-path doc(s).** Consult the
   References routing table below and read **only** the `.adoc` files
   whose load condition matches this run (e.g. the section that covers
   the source flavor identified in step 4, or the target form selected by
   `--configuration-mode`). Do not load every file under
   `references/docs/` by default — the procedure handles many sub-cases
   and most runs need only a subset. If step 4 later shows you picked the
   wrong sub-case, return here and load the matching doc instead. Do not
   paraphrase from memory.

3. **Locate the candidate.** Use `Grep` with the pattern:
   <concrete grep pattern — must match both Spring and plain Axon forms>
   Apply the selection rule above.

4. **Identify the source flavor** of the candidate by reading its
   surrounding code (annotations, imports, neighbouring registration
   code). This is observation only — it determines which AF4 form you are
   reading, not the output. The output flavor is the one passed in
   `--configuration-mode`.

5. **Check whether the goal is already reached.** Compare the candidate
   against the AF5 target shape described in `references/docs/` for the
   selected `--configuration-mode`. Prior work (an OpenRewrite recipe, a
   manual edit, an earlier run of this skill) may have already applied
   the target form fully or partially. Outcomes:

    - **Fully migrated** — report "already on AF5 target form, nothing to
      do" and jump to step 8 with an empty diff. This is a success.
    - **Partially migrated** — record which parts already match the
      target and which still need work. Step 6 must only edit the parts
      that still need it. Re-applying already-migrated edits is forbidden.
    - **Not migrated** — proceed normally.

6. **Apply the transformation** — follow the steps under "Transformation
   instructions" below. Pick the row in each step's matrix that matches
   (source flavor read in step 4) × (target flavor from
   `--configuration-mode`). Skip sub-steps that step 5 marked as already
   complete. Use `Edit` for in-place changes.

7. **Show the diff.** Run `git diff <changed-files>` and summarize:
    - Files touched (or "none — already migrated")
    - Imports added/removed
    - Source flavor → target flavor (e.g. `Spring Boot → axon-configuration`)
    - Which parts step 5 found already migrated, if any
    - Behavior preserved / behavior intentionally changed (should be none)

8. **Stop and hand control to the human via `AskUserQuestion`**:
    - Accept — the human takes it from here
    - Reject — surface the diff issue; the human decides next steps
    - Adjust — apply the human's correction and re-present the diff

   Do **not** rely on `mvn compile` / `gradle build` passing as a success
   signal. Peer constructs are still on AF4 mid-migration; build is expected
   to be red.

   The skill's responsibility ends at "diff produced, human informed".
   Everything downstream — version control, running the app, sequencing
   the next migration — is outside this skill's scope.

> **Fallback only**: if `references/docs/` and the transformation
> instructions below leave a genuine gap (unknown API shape, ambiguous
> target form), surface the gap to the human and stop. Do not invent the
> missing knowledge.

## Transformation instructions

<This is the heart of the skill. Keep steps concrete, generic, and
backed by the migration-path .adoc. Best step is often just "follow
references/docs/<file>.adoc section X". Each step that touches
configuration MUST cover the four AF4-flavor × AF5-flavor combinations
that the matrix in "Arguments" describes — even when the result is "same
as Spring Boot output above". Project-specific lessons belong in
`references/examples/`, not inline here.>

### Source recognition (read both AF4 forms)

Before any edit, the skill must recognize the candidate regardless of how
AF4 wired it. From `references/docs/`, derive a recognition table like:

| AF4 form | What to look for |
|----------|------------------|
| Spring Boot | <e.g. `@Aggregate` discovered via component scan; `@SpringBootApplication` present> |
| plain Axon | <e.g. class registered on `AxonConfiguration` builder; no Spring annotations> |

Use this table only to read the input. The output is dictated by
`--configuration-mode`.

### Transformation steps

**Step 1** — <imperative action, e.g. "Replace `@Aggregate` with
`@EventSourcedEntity` and add `@EntityId` to the identifier field.">

The class body changes the same way regardless of flavor. The
**registration / wiring** changes depend on the AF4 source × AF5 target
pair:

| AF4 source → AF5 target | Wiring change |
|-------------------------|---------------|
| Spring Boot → Spring Boot | <e.g. swap `@Aggregate` for `@EventSourcedEntity`; component scan still picks it up> |
| Spring Boot → axon-configuration | <e.g. remove Spring annotation; register the entity explicitly on `AxonConfiguration` and remove Spring-managed bean wiring> |
| plain Axon → Spring Boot | <e.g. add `@EventSourcedEntity` + component-scannable stereotype; drop the explicit registration on the configuration builder> |
| plain Axon → axon-configuration | <e.g. swap registration call to the AF5 equivalent on `AxonConfiguration`> |

Before (class body, both flavors):
```java
<minimal AF4 snippet — class body only>
```

After (class body, both flavors):
```java
<minimal AF5 snippet — class body only>
```

Wiring before / after — per row in the table above, kept in
`references/examples/` to avoid bloating SKILL.md.

Why: <one line — the semantic the .adoc relies on>

**Step 2** — <next action>

<same shape: class-body diff once, wiring diff per AF4×AF5 row>

## Variants

<Document divergent patterns observed across projects. Route on observable
input shape (annotation present/absent, base class, payload type), never on
project identity.>

| Variant | Trigger | Example file |
|---------|---------|--------------|
| <name> | <observable shape> | `references/examples/<NN>-<short>.md` |

## References

Reference files are **conditionally loaded**. The generator (this skill's
author) fills the routing table below with one row per file or directory
and a concrete condition. The skill loads a row only when its condition
matches the current run — never "all docs every time", never "all
examples every time".

Standard condition shapes (combine as needed):

- *always* — required on every run (use sparingly; usually an `index.md`
  or a top-level overview).
- *source flavor is X* — load when step 4 observes AF4 form X.
- *target is `--configuration-mode=X`* — load when the caller chose X.
- *source flavor X → target X* — load only for one cell of the
  AF4×AF5 matrix.
- *Variant V triggers* — load when the candidate matches Variant V's
  observable shape (from the Variants table above).
- *fallback* — load only when steps 2/5 leave a gap.

Fill in for this skill:

| Topic | File | Load when |
|-------|------|-----------|
| <e.g. core .adoc section for this construct> | `references/docs/<area>/<file>.adoc` | always |
| <e.g. Spring-specific .adoc> | `references/docs/<area>/<spring-file>.adoc` | source flavor is Spring Boot **or** target is `--configuration-mode=spring-boot` |
| <e.g. plain-Axon-specific .adoc> | `references/docs/<area>/<plain-file>.adoc` | source flavor is plain Axon **or** target is `--configuration-mode=axon-configuration` |
| <Variant V example> | `references/examples/<NN>-<short>.md` | Variant V triggers (see Variants) |

## MUST / MUST NOT

| MUST | MUST NOT |
|------|----------|
| Read the `.adoc` rows in the References table whose load condition matches this run, before any edit | Paraphrase migration knowledge from memory |
| Load reference files conditionally per the References routing table | Load every file under `references/docs/` or `references/examples/` on every run |
| Check the candidate against the AF5 target shape first; report "already migrated" and stop with zero diff when the goal is reached | Re-apply edits to code already on the target form; produce spurious diffs |
| Migrate exactly one candidate per run | Sweep all matches in a single run |
| Honour `--configuration-mode` (default `spring-boot`) for the output flavor | Detect the target flavor from surrounding code — the argument decides |
| Recognize the AF4 source in either Spring Boot or plain Axon form | Refuse to migrate because the source flavor differs from the target |
| Preserve AF4 behavior | Introduce DCB or other AF5 patterns that change semantics |
| End with diff + `AskUserQuestion` for human review | Touch version control, run the app, or claim success on build/compile |
| Route Variants on observable shape | Route on project name or file path |
| Append new project quirks to `references/examples/` | Edit existing examples to overwrite |
```

---

## Skeletons for the reference files

### `references/examples/01-<short-variant>.md`

```markdown
# <short variant description>

Observable shape that triggers this variant: <annotation / base class /
payload type — never project name>.

AF4 source flavor: <Spring Boot | axon-configuration>
AF5 target flavor (`--configuration-mode`): <spring-boot | axon-configuration>

**Before** (`<lang>`):
```<lang>
<original AF4 construct + its wiring, smallest reproducible form>
```

**After** (`<lang>`):
```<lang>
<migrated AF5 construct + its wiring under the chosen configuration-mode>
```

**Notes**: <anything LLM-specific worth remembering — gotchas, surrounding
edits the human had to make manually, why this differs from the canonical
form in `references/docs/`>.
```
