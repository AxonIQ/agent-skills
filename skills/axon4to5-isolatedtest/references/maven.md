# Maven path — isolated-<TargetName> profile

Maven scopes compilation via `maven-compiler-plugin`'s `<includes>` / `<testIncludes>`. Those settings are **not exposed as user properties** — they live in POM `<configuration>`. To activate or deactivate them on demand, wrap them in a profile.

## 1. Install (or augment) the profile

If `<profile><id>isolated-<TargetName></id>` does NOT exist, append the snippet below as a child of `<profiles>` (create the `<profiles>` parent if needed). If it exists, **merge** new patterns into `<includes>` / `<testIncludes>` — dedupe by exact path string.

Copy from [../assets/maven-profile.xml](../assets/maven-profile.xml) — replace the placeholders:

- `<TargetName>` — the input `target-name` (PascalCase).
- `<relpath-under-src-main-java>` — paths from `main-sources` input (drop the `src/main/java/` or `src/main/kotlin/` prefix).
- `<relpath-under-src-test-java>` — paths from `test-sources` input (drop the `src/test/java/` or `src/test/kotlin/` prefix).

The snippet template:

```xml
<profile>
    <id>isolated-<TargetName></id>
    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <configuration>
                    <includes>
                        <include>com/example/foo/Target.java</include>
                        <!-- one entry per main-source file -->
                    </includes>
                    <testIncludes>
                        <testInclude>com/example/foo/TargetTest.java</testInclude>
                        <!-- one entry per test-source file -->
                    </testIncludes>
                </configuration>
            </plugin>
        </plugins>
    </build>
</profile>
```

### Extra dependencies (rare)

Only when the input `extra-deps` is non-empty. Otherwise the profile inherits the main `<dependencies>` block — that is the default and is correct for the typical case.

If extra deps ARE needed, add them inside the same `<profile>` block:

```xml
<dependencies>
    <dependency>
        <groupId>group</groupId>
        <artifactId>artifact</artifactId>
        <version>${some.version}</version>
    </dependency>
</dependencies>
```

## 2. Per-file vs per-package includes

- **Per-file** (precise, verbose): `com/example/foo/Bar.java`. **Default to this** — narrow scope is the point.
- **Per-package** (concise, forward-friendly): `com/example/foo/**/*.java`. Use only when the target file plus all its helpers genuinely live in one package and nothing else there matters.

Wildcards pull in unrelated files (`*Controller.java`, `*Config.java`, …) that may fail to compile under whatever invariant the caller is checking. If unsure, start per-file. The compiler will tell you what's missing.

## 3. Kotlin sources in a Maven project

The `maven-compiler-plugin` does NOT compile `.kt` files — that's `kotlin-maven-plugin`'s job, and its source roots are configured separately (typically via `<sourceDirs>`). For a Kotlin/Maven project, scoping by file is more involved and depends on how the project wires Kotlin compilation.

**If the project is pure Java/Maven** → follow the snippet above as-is.

**If the project is Kotlin/Maven** → the `<includes>` mechanism above scopes Java compilation only. Either:
- Migrate the test target to be invoked via a single specific test class (`-Dtest=<FQ>`) without source-set scoping, OR
- Wrap the kotlin-maven-plugin's `<sourceDirs>` configuration inside the same profile to point at a temporary directory containing only the scoped files.

This skill's default snippet targets the common case (Java/Maven). Document any Kotlin/Maven deviation in the **notes** field of the output.

## 4. Verify

### Compile-only check (fast — start here)

```bash
./mvnw -f <build-file> -P isolated-<TargetName> test-compile \
  -DskipTests \
  -DfailIfNoTests=false \
  -Dsurefire.failIfNoSpecifiedTests=false
```

### Scoped test run

```bash
./mvnw -f <build-file> -P isolated-<TargetName> test \
  -Dtest='<FQTestClass1>,<FQTestClass2>' \
  -DfailIfNoTests=false \
  -Dsurefire.failIfNoSpecifiedTests=false
```

### Why both `failIfNoTests=false` AND `surefire.failIfNoSpecifiedTests=false`

- `-DfailIfNoTests=false` — for the surefire `test` phase generally. Prevents failure on modules with no tests at all.
- `-Dsurefire.failIfNoSpecifiedTests=false` — for the `-Dtest=…` filter. Prevents `No tests matching pattern "…" were executed!` on modules where the pattern matches nothing.

Multi-module reactors (`-pl <a>,<b>`) need **both** because `-pl` includes modules that may not contain a class matching the `-Dtest=…` pattern.

## 5. Multi-module reactors

The profile goes in **each module the scope touches**. The parent POM does not help — Maven's `maven-compiler-plugin` settings scope per-module.

Run from the reactor root with `-pl`:

```bash
./mvnw -f <reactor-root>/pom.xml -P isolated-<TargetName> -pl module-a,module-b test \
  -Dtest='<FQ>' -DfailIfNoTests=false -Dsurefire.failIfNoSpecifiedTests=false
```

## 6. Combined verification (multiple targets)

Activate several profiles at once. Maven merges the `<includes>` across the active profiles:

```bash
./mvnw -f <build-file> -P isolated-Foo,isolated-Bar test \
  -Dtest='FooTest,BarTest' \
  -DfailIfNoTests=false -Dsurefire.failIfNoSpecifiedTests=false
```

## Cleanup

Two triggers — automatic (per-target, when `cleanup=true`) and manual (end-of-work, all scopes at once).

### Automatic — `cleanup=true` input

After a green test run, remove ONLY the `isolated-<TargetName>` profile that was just verified. Steps:

1. Locate the `<profile>` whose `<id>` equals `isolated-<TargetName>` in the build file.
2. Delete the entire `<profile>...</profile>` block.
3. If that was the only profile, delete the surrounding `<profiles>...</profiles>` element too.
4. Re-run the project's normal compile (no `-P` flag) to confirm the file is still well-formed — but DO NOT re-run the full project build; that's not this skill's job.

Skip automatic cleanup when:
- The compile-only check failed.
- The test run failed (any non-zero Surefire failure or error count).
- Zero tests executed AND the user clearly meant for tests to run (record this in the output `notes` field; the user decides).

Report the kept/removed state truthfully in the skill output.

### Manual — end-of-work, all scopes at once

When the surrounding module compiles and tests pass cleanly **without any `isolated-*` profile activated**, delete every remaining `isolated-*` profile from the affected POMs in a single commit (e.g. `chore: remove isolated-* scaffolding`). The audit trail belongs in commit history — not in build-file blocks.

Until that condition is true, leave the scopes alone; sibling work may still need them.

## NEVER

- Pass `-Dmaven.compiler.includes=…` or `-Dmaven.compiler.testIncludes=…` from the command line. Those properties are NOT supported by `maven-compiler-plugin` — they're silently ignored. The POM `<configuration>` (inside a profile) is the only supported way.
- Use `<excludes>` to silence compile errors. Narrow the `<includes>` instead.
- Run `./mvnw clean verify` with a profile activated. The full verify is the goal state — it must pass without `-P isolated-*`.
