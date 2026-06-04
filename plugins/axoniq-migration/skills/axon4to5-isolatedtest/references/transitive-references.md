# Transitive references — why your include list grows

Both `javac` and `kotlinc` resolve **every** symbol referenced from the files they compile. The compiler does NOT stop at the boundary of your `<includes>` / `include(...)` list — if a kept file imports a non-kept class, the compiler reads the non-kept class file (or `.java`/`.kt` source) to resolve symbols.

## What this means in practice

You list `Target.java` in the scope. `Target.java` imports `Helper.java`. The compiler will:

1. Find `Helper.java` on the source path (Maven `src/main/java`, Gradle source set's `srcDir`).
2. Try to compile it (because no compiled `.class` exists in the scope's output dir).
3. Fail if `Helper.java` references something that needs the scope's restricted classpath / dependencies and that something is missing.

This is the **transitive reference leak**. It surfaces as `cannot find symbol` or `package X does not exist` errors naming files you did NOT put in the include list.

## How to respond

When the compiler fails on a file outside the scope:

1. **Read the error.** It names the file path.
2. **Decide**: is this file part of the unit you're isolating, or is it a true dependency of the target that should be in `main` already?
3. **Action A** — file belongs in scope → add its repo-relative path to the scope's `<includes>` / `include(...)` and re-run.
4. **Action B** — file is foreign to your target and should compile cleanly on its own → fix it first (outside this skill's job) and re-run.

## When the include list grows past ~10 files

If the target keeps pulling in transitive helpers indefinitely, that's a signal that the unit isn't really isolatable — the target leans on too much surrounding code. Options:

- Widen the scope intentionally to include the helper cluster as a single unit.
- Refactor (extract the target's collaborators to a smaller surface) before invoking the skill again.
- Stop using per-target scoping for this target and verify against the full module instead.

## Why per-package wildcards bite

`com/example/foo/**/*.java` looks like a shortcut but pulls in **every** file in the package — including ones that aren't direct helpers and may break under the scope's invariants. Per-file is verbose but precise. Reach for wildcards only when the package is genuinely a single coherent unit.

## Gradle source-set caveat

Source sets compile as **independent compilation units**. The skill's default snippet does NOT wire `sourceSets["main"].output` onto the isolated source set — that would couple to broken `main` and undo isolation (see [gradle.md](gradle.md#why-not-sourcesetsmainoutput)). Instead the snippet uses `extendsFrom` to inherit the external library configurations only.

Consequence: if `Target.kt` references a helper that lives in `main`, the helper is NOT on the compile classpath. You must add its source path to the source set's `include(...)` list — it then compiles inside the isolated scope, beside the target.

The Maven `<includes>` model has the same constraint — the symptom shows up differently because Maven's compile reads source directly from `src/main/java` regardless of whether `main` compiled.
