# Gradle path — isolated<TargetName> source-set + Test task

Gradle scopes compilation via **source sets**. Each source set has its own compile task, its own dependency configurations (`<setName>Implementation`, `<setName>TestImplementation`, …), and compiles independently of the project's `main` / `test` source sets. A custom `Test` task wired to the source set runs only those tests.

## 1. Install (or augment) the source set

If a source set named `isolated<TargetName>` does NOT exist, append the snippet from [../assets/gradle-kotlin-dsl.gradle.kts](../assets/gradle-kotlin-dsl.gradle.kts) (Kotlin DSL) or [../assets/gradle-groovy-dsl.gradle](../assets/gradle-groovy-dsl.gradle) (Groovy DSL) to the relevant subproject's build file. If it already exists, **merge** the new file paths into the source set's `include(...)` list — dedupe.

Replace the placeholders:

- `<TargetName>` — the input `target-name` (PascalCase).
- `<relpath-under-src-main-...>` — paths from `main-sources` (drop `src/main/{java,kotlin}/`).
- `<relpath-under-src-test-...>` — paths from `test-sources` (drop `src/test/{java,kotlin}/`).

### Kotlin DSL skeleton (works for Java, Kotlin, or mixed sources)

```kotlin
sourceSets {
    create("isolated<TargetName>") {
        java {
            srcDir("src/main/java")
            srcDir("src/main/kotlin")
            include(
                "com/example/foo/Target.kt",  // or .java
                // one entry per main-source file
            )
        }
    }
    create("isolated<TargetName>Test") {
        java {
            srcDir("src/test/java")
            srcDir("src/test/kotlin")
            include(
                "com/example/foo/TargetTest.kt",
                // one entry per test-source file
            )
        }
        compileClasspath += sourceSets["isolated<TargetName>"].output
        runtimeClasspath += sourceSets["isolated<TargetName>"].output
    }
}

configurations {
    named("isolated<TargetName>Implementation") {
        extendsFrom(configurations["implementation"])
    }
    named("isolated<TargetName>RuntimeOnly") {
        extendsFrom(configurations["runtimeOnly"])
    }
    named("isolated<TargetName>TestImplementation") {
        extendsFrom(configurations["testImplementation"])
    }
    named("isolated<TargetName>TestRuntimeOnly") {
        extendsFrom(configurations["testRuntimeOnly"])
    }
}

tasks.register<Test>("testIsolated<TargetName>") {
    description = "Run tests for <TargetName> in isolation."
    group = "verification"
    testClassesDirs = sourceSets["isolated<TargetName>Test"].output.classesDirs
    classpath = sourceSets["isolated<TargetName>Test"].runtimeClasspath
    useJUnitPlatform()
}
```

### Why both `srcDir("src/main/java")` and `srcDir("src/main/kotlin")`

Listing both lets the same source-set block compile pure-Java, pure-Kotlin, and mixed targets without editing. The `include(...)` patterns gate which files actually compile — empty dirs are no-ops. The Kotlin Gradle plugin (`kotlin("jvm")`) reacts to source-set creation and auto-registers `compileIsolated<TargetName>Kotlin`. The Java plugin registers `compileIsolated<TargetName>Java`.

### Why `extendsFrom` and NOT `(configurations["implementation"])` as a dependency

Passing a `Configuration` directly as a dependency was removed in Gradle 8:

```kotlin
// FAILS on Gradle 8+ with "Adding a Configuration as a dependency is no longer allowed":
"isolated<TargetName>Implementation"(configurations["implementation"])
```

Use the `configurations { ... extendsFrom(...) }` block instead. It carries over the external library deps from the parent configuration without coupling to the parent's output.

### Why NOT `sourceSets["main"].output`

A natural-looking line like:

```kotlin
"isolated<TargetName>Implementation"(sourceSets["main"].output)
```

makes the regular `compileMain` a dependency of `compileIsolated<TargetName>`. That **undoes isolation** — if the main source set fails to compile, the isolated one fails too. The whole point of this skill is to keep working when `main` is broken.

If the target genuinely needs a helper class that lives in `main`, add the helper's source path to the source set's `include(...)` list. It compiles inside the isolated scope, beside the target.

## 2. Per-file vs per-package includes

Default to per-file. Per-package wildcards (`com/example/foo/**/*.kt`) pull in unrelated files (Controllers, Configs, …) that may not compile under the scope's invariants. Reach for wildcards only when the package is genuinely one coherent unit.

## 3. Verify

### Compile-only check (fast — start here)

```bash
./gradlew compileIsolated<TargetName>Kotlin   # Kotlin sources
./gradlew compileIsolated<TargetName>Java     # Java sources
```

Both tasks are auto-generated. For mixed sources, run both — Gradle will skip the one whose source set is empty.

### Scoped test run

```bash
./gradlew testIsolated<TargetName>
```

## 4. Multi-project builds

The source-set + Test task goes in **each subproject's** `build.gradle(.kts)` that the scope touches. Invoke per-subproject:

```bash
./gradlew :module-a:testIsolated<TargetName> :module-b:testIsolated<TargetName>
```

Gradle silently skips subprojects that don't define the task — no equivalent of Maven's `-Dsurefire.failIfNoSpecifiedTests` gotcha.

## 5. Combined verification (multiple targets)

```bash
./gradlew testIsolatedFoo testIsolatedBar
```

Each source set is independent — order doesn't matter.

## Cleanup

Two triggers — automatic (per-target, when `cleanup=true`) and manual (end-of-work, all scopes at once).

### Automatic — `cleanup=true` input

After a green test run, remove ONLY the `isolated<TargetName>` scope that was just verified. Steps:

1. Delete the `sourceSets { create("isolated<TargetName>") { ... } create("isolated<TargetName>Test") { ... } }` blocks. If the file uses one shared `sourceSets { ... }` block for multiple scopes, remove only the two `create("isolated<TargetName>"...)` entries — leave siblings untouched.
2. Delete the `configurations { named("isolated<TargetName>Implementation") { ... } named("isolated<TargetName>RuntimeOnly") { ... } named("isolated<TargetName>TestImplementation") { ... } named("isolated<TargetName>TestRuntimeOnly") { ... } }` entries.
3. Delete the `tasks.register<Test>("testIsolated<TargetName>") { ... }` block.
4. Run `./gradlew help -q` (or any cheap no-op task) to confirm the build file still parses. DO NOT run the full project build — that's not this skill's job.

Skip automatic cleanup when:
- `compileIsolated<TargetName>{Java,Kotlin}` failed.
- `testIsolated<TargetName>` reported any failures (check `build/test-results/testIsolated<TargetName>/*.xml` for `failures>0` or `errors>0`).
- Zero tests executed AND the user clearly meant for tests to run (record in output `notes`).

Report the kept/removed state truthfully in the skill output.

### Manual — end-of-work, all scopes at once

When the surrounding module compiles and tests pass cleanly **without any `isolated*` task referenced**, delete from the affected `build.gradle(.kts)`:

1. Every source set whose name starts with `isolated`.
2. Every `Test` task with the `testIsolated` prefix.
3. The matching `configurations { named(...) { extendsFrom(...) } }` lines for those scopes.

Do it in a single commit — the audit trail belongs in commit history, not in build-file blocks.

## NEVER

- Use `exclude(...)` to silence compile errors in a scoped source set. Narrow the `include(...)` list instead.
- Depend on `sourceSets["main"].output` from the isolated source set — that re-couples to broken main.
- Pass `configurations["implementation"]` directly as a dependency — fails in Gradle 8+. Use `extendsFrom`.
- Reach into another `isolated*` source set's outputs from your own.
- Run `./gradlew build` and expect `isolated*` source sets to be skipped — they WILL run as part of `check`. Use `./gradlew build -x testIsolated<TargetName>` if you need to skip explicitly.
