# Skill quality checklist

Run before declaring a generated `axon4to5-<scope>` skill ready. Every item
is a yes/no — gaps must be fixed, not waved away.

## Frontmatter

- [ ] `name` matches directory and starts with `axon4to5-`.
- [ ] `description` includes: what it migrates, trigger phrases the user
      would say, the word "atomic", behavior-preserving constraint, and
      that it supports both Spring Boot and plain (non-Spring) projects.
- [ ] `allowed-tools` lists only what the procedure actually uses.
- [ ] `argument-hint` set (e.g. target class or file path).

## Self-containment

- [ ] No path outside the skill directory referenced in the procedure.
- [ ] `references/docs/` contains the relevant `.adoc` file(s), with the
      `paths/` subtree preserved.

## Procedure

- [ ] Selection rule is explicit and deterministic.
- [ ] Procedure reads the relevant `.adoc` files under `references/docs/`
      before any edit — selected via the References routing table, not by
      loading every file every run.
- [ ] SKILL.md carries a References routing table with one row per
      `.adoc` / example file (or directory) and a **concrete load
      condition** (e.g. *source flavor is Spring Boot*, *target is
      `--configuration-mode=axon-configuration`*, *Variant V triggers*,
      *fallback*). "Always" rows are present only when the file is
      genuinely needed on every run.
- [ ] `--configuration-mode` argument is exposed with values `spring-boot`
      and `axon-configuration`, default `spring-boot`. The procedure
      echoes the resolved value back to the human.
- [ ] The target output flavor is taken **only** from
      `--configuration-mode` — never detected from surrounding code.
- [ ] The source flavor (AF4 Spring Boot vs AF4 plain Axon) is
      recognized from the candidate's code, with recognition rules
      sourced from `references/docs/`.
- [ ] All four AF4-source × AF5-target combinations are covered. Wiring
      diffs for each pair live either in the transformation steps or in
      `references/examples/`.
- [ ] Procedure includes an explicit "check whether the goal is already
      reached" step before any edit. Fully-migrated candidates produce
      zero diff and a "already migrated" report. Partially-migrated
      candidates only get the missing edits.
- [ ] Procedure ends with `git diff` + `AskUserQuestion` for human review.
      Zero diff is an acceptable success outcome.
- [ ] No reliance on `mvn compile` / `gradle build` as the success signal.
- [ ] No mention of version-control actions, pushing, or orchestration as
      the skill's responsibility. The skill stops at "diff produced, human
      informed".

## Generic vs project-specific

- [ ] No project name, package, or module path appears in the procedure or
      transformation instructions.
- [ ] Variants (if any) route on observable input shape — annotation, base
      class, payload type — never on project identity.
- [ ] Project-specific quirks live in `references/examples/NN-<short>.md`.

## Language coverage

- [ ] Examples cover Java OR Kotlin; the body trusts the LLM to translate.

## End-user framing

- [ ] No references to `reflect`, the parent generator, or the
      contributor-side iteration loop. The generated skill reads as a
      standalone tool for an end user.
- [ ] No "Notes for the maintainer" or repo-contributor sections.

## Size

- [ ] SKILL.md body under ~300 lines.
- [ ] No reference file links to another reference file (one-hop rule).
- [ ] All routing/dispatch logic lives in SKILL.md, not in references.
