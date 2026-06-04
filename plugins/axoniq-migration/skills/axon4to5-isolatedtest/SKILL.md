---
name: axon4to5-isolatedtest
description: Internal helper, invoked ONLY by other skills (e.g. axon4to5-migrate). Scopes Maven/Gradle compile+test to ONE target class plus all classes required for it to compile, via per-target profile or source-set. Do NOT auto-trigger from user prompts.
allowed-tools: Bash, Read, Edit, Write, Grep, Glob
argument-hint: <TargetName> [build-file=<path>] [cleanup=true|false]
user-invocable: false
effort: medium
model: haiku
---

# axon4to5-isolatedtest

## Goal

Add (or extend) ONE self-contained build-scope unit per target so:

- Compilation is scoped to the target class plus all classes required for it to compile (helpers, dependencies, tests).
- Test runs hit only the target's test classes.
- The scope is independent — adding or removing it does not affect siblings.
- The scope is reversible — deleting the block reverses the change.

A target is a single class identified by its **simple name** (e.g., `ResourcesPool`, `PaymentId`). The scope id grammar:

```
isolated-<TargetName>         # Maven profile id (used verbatim — TargetName stays PascalCase)
isolated<TargetName>          # Gradle source-set name (camelCase already; <TargetName> is PascalCase)
```

`<TargetName>` = simple class name only. Java identifier chars only.

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `target-name` | yes | — | Simple class name, PascalCase. Drives the scope id. |
| `build-file` | no | deduced | Absolute path to `pom.xml` or `build.gradle(.kts)`. Deduce from the project. |
| `main-sources` | no | deduced | Repo-relative paths under `src/main/{java,kotlin}` for files to compile in scope. Deduce from the target's imports and the project layout. |
| `test-sources` | no | deduced | Repo-relative paths under `src/test/{java,kotlin}` for tests to run in scope. Deduce from the project — usually `<TargetName>Test` and its siblings. |
| `extra-deps` | no | `[]` | Extra dependency coordinates to add only to this scope. Rare — most projects rely on inherited deps. |
| `cleanup` | no | `false` | If `true`, remove the `isolated-<TargetName>` scope from the build file after a green test run (compile + tests both pass). If `false`, leave the scope in place so the user can iterate or re-run. On non-green runs the scope is always kept regardless. |

## Pick the path

Detect build tool from `build-file` extension/name:

| Build file | Path | Reference |
|---|---|---|
| `pom.xml` | Maven profile | [references/maven.md](references/maven.md) |
| `build.gradle.kts` / `build.gradle` | Gradle source-set + Test task | [references/gradle.md](references/gradle.md) |

Each reference file is self-contained: it owns the install steps, the verify commands, and the cleanup steps for its build tool.

## Why per-target scoping

One scope per `<TargetName>`, never a shared scope across targets:

- **Parallel-friendly** — concurrent invocations on different targets touch disjoint scopes; no edit race on shared include lists.
- **Clean rollback** — a failed run leaves ONE self-contained block to delete; no grep-and-pick across mixed entries.
- **Bisect-friendly** — `git bisect` across commits that add or remove scopes sees stable siblings.

Do NOT collapse multiple targets into one shared `isolated-*` scope — you lose all three properties.

## When to run

- **First time** for a target → create `isolated-<TargetName>` scope.
- **Re-running** for the same target → augment the existing scope's include list (add transitive helpers surfaced by compile errors). Idempotent: re-running augments, never replaces.
- **Different target** → create a new scope, do not touch sibling `isolated-*` scopes.
- **Combined verification** → activate / invoke multiple `isolated-*` scopes in one command to verify several targets together; see references for the exact syntax.

## Preflight

1. Does a scope `isolated-<TargetName>` (Maven) / `isolated<TargetName>` (Gradle) already exist in `build-file`?
2. If yes AND its include list covers `main-sources` ∪ `test-sources` → skip install, jump to verify.
3. If yes BUT some inputs are missing from the include list → **augment** (merge new entries, dedupe **by exact path string**). Never replace.

Use `Grep` to detect existing scopes:

```bash
# Maven
grep -E "<id>isolated-<TargetName></id>" <build-file>
# Gradle (Kotlin DSL)
grep -E "isolated<TargetName>" <build-file>
```

## End condition

Run in this order — fail fast on the cheaper check:

1. The build file contains a well-formed `isolated-<TargetName>` scope.
2. **Compile-only check first** — passes against the scope (or fails on missing symbols you EXPECTED, signalling the include list is too narrow). Do NOT proceed to step 3 until compile is green.
3. **Scoped test run** — green (or fails on legitimate work that's the caller's job to fix — never on missing symbols from files OUTSIDE the include list).

## NEVER

- Use `<excludes>` (Maven) or source-set `exclude(...)` (Gradle) to silence compile errors — defeats the purpose. If the include list is too broad, narrow it.
- Mutate a sibling `isolated-*` scope to "borrow" its files. Each target owns exactly one scope.
- Activate `isolated-*` scopes in CI by default — these are working scaffolds, not production scope.
- Leave `isolated-*` scopes in the build file once the surrounding module compiles and tests pass cleanly without them — see the **Cleanup** section in [maven.md](references/maven.md#cleanup) / [gradle.md](references/gradle.md#cleanup).
- Pass `-Dmaven.compiler.includes=…` or `-Dmaven.compiler.testIncludes=…` from the command line — those properties are silently ignored by `maven-compiler-plugin`. The scope MUST live in the POM (inside the profile).

## Output (what to report back)

ALWAYS use this exact template. The user reads this summary to know what was verified, how to re-run it manually, and whether the build file still contains scaffolding.

````markdown
## axon4to5-isolatedtest: <TargetName>

**Build file**: <absolute path>
**Build tool**: maven | gradle
**Scope id**: isolated-<TargetName> | isolated<TargetName>

### Files in scope
- Main: <count> file(s)
  - <relpath 1>
  - <relpath 2>
- Test: <count> file(s)
  - <relpath 1>

### Compile result
✅ passed | ❌ failed — `<compile-only command, copy-pasteable>`

### Test result
✅ N passed, 0 failed | ❌ N passed, M failed (or 0 executed when no `@Test` methods exist)
- `<FQTestClass1>` — <tests run> passed
- `<FQTestClass2>` — <tests run> passed, <failures> failed
  - <failure name>: <one-line reason>

Re-run manually:
```
<scoped test command, copy-pasteable, including the -Dtest=... filter or :testIsolated<Target> task>
```

### Scaffolding status
- `cleanup` input: true | false
- Scope in build file: **kept** | **removed**
  - If kept: delete it later with `git checkout <build-file>` or by hand. See the **Cleanup** section in references/<maven|gradle>.md.
  - If removed: the build file is back to its pre-skill state; the verification commands above will no longer work — re-invoke the skill if you need to re-verify.

### Notes
<optional — e.g. "Augmented existing scope with 2 new files", "Compile failed naming `Foo.java` outside the include list — add it and re-run", "`cleanup=true` requested but skipped because tests failed">
````

### Field rules

- **Compile result** — paste the EXACT command you ran, not a template. The user must be able to copy and re-run without edits.
- **Test result** — quote real counts from the build output (`Tests run: N, Failures: M` for surefire; the JUnit XML report's `tests=` / `failures=` attrs for Gradle). Don't summarize as "passed" if zero tests executed — say `0 executed` and flag that the target test class may have no `@Test` methods.
- **Scaffolding status** — this is the truth-telling field. Be explicit: `kept` means the user's repo has uncommitted edits to the build file; `removed` means the file is restored. Never claim `removed` if any part of the scope (configurations block, source set, task, profile) is still in the file.

## Common pitfall — transitive references leak

`javac` and `kotlinc` pull in classes referenced from kept files even if those classes are NOT in the include list. If `Kept.java` imports `Broken.java`, you must either add `Broken.java` to includes or fix `Broken.java`. The compiler error names the file to add. See [references/transitive-references.md](references/transitive-references.md).

## Fallback: RunTests.java JUnit launcher

If your project pins a JUnit Platform version that doesn't publish a working `junit-platform-console-launcher`, use [scripts/RunTests.java](scripts/RunTests.java) — a minimal launcher that takes FQ test class names and exits 0/1. Usage instructions are in the file's header comment.
