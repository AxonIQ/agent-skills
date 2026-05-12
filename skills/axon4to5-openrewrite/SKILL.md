---
name: axon4to5-openrewrite
description: Apply the Axon Framework 4 → 5 OpenRewrite bulk-migration recipe (maven or gradle, free or commercial variant). Use when the user says "run openrewrite", "apply axon migration recipe", "axon4to5-openrewrite", "migrate to axon 5", or "migrate to axoniq 5". Detects build tool, picks the recipe by --framework, runs, offers to commit. Idempotent — safe to re-run.
argument-hint: --framework {axon|axoniq} [--commit {true|false}]
---

# Goal

Run the Axon 4→5 OpenRewrite recipe in the user's project. Nothing else. Report success/failure and offer the standard commit.

**Done when**: `scripts/migrate.sh <framework>` exits 0 and the project has changes vs its prior state.

**Compilation is NOT a success criterion.** The OpenRewrite recipe cannot perform the full Axon 4 → 5 migration on its own — there will be missing parts that require manual follow-up (custom code paths, removed APIs without 1:1 replacements, ambiguous mappings). A non-compiling project after the recipe is the expected baseline for the next step, not a failure of this skill.

# Inputs

- `framework` ∈ {`axon`, `axoniq`} — extract from `--framework <value>` in user's message. Default = `axon` if absent.
- `commit` ∈ {`true`, `false`, _absent_} — extract from `--commit <value>` in user's message. Controls post-run commit behaviour (see **Commit** below). Absent = ask interactively.
- CWD = user's target project root (where `pom.xml` or `build.gradle[.kts]` lives).
- Recipe artifact version is pinned in `references/recipe-version` (single source — edit there to bump).

# Steps

1. Resolve `framework`. Reject anything other than `axon` / `axoniq` with one line, stop.
2. Confirm CWD has `pom.xml` OR `build.gradle[.kts]`. If not, stop with one line.
3. Run: `<skill-dir>/scripts/migrate.sh <framework>`
   - The script self-locates and picks maven vs gradle.
   - Stream stdout/stderr to the user.
4. Exit 0 → go to **Commit**. Exit ≠ 0 → go to **Failure routing**.
5. **Cleanup contract**: do not write any files into the user's project beyond what the recipe itself produces. The bundled `assets/init.gradle` is referenced by absolute path; never copied in.

# Commit

Single canonical message (do NOT customize per run):

```
COMMIT_MESSAGE_TEMPLATE:
chore(axon): apply Axon 4 → 5 OpenRewrite migration (--framework <FRAMEWORK>)
```

Substitute `<FRAMEWORK>` with the actual value (`axon` or `axoniq`). Use the result verbatim.

- `--commit true` → `git add -A && git commit -m "<message>"`. No prompt.
- `--commit false` → leave changes staged and unstaged as the recipe left them. No commit, no prompt.
- _absent_ (default) → ask the user: [commit now] / [leave staged] / [discard]. On "commit now" use the message verbatim.

NEVER commit on failure. NEVER customize the message per run.

# Failure routing

Match the error output, then apply:

- **`Could not find artifact org.axonframework:axon-migration:...`** — the recipe artifact didn't resolve from any configured repository (Maven Central, Sonatype snapshots, mavenLocal). Surface the error to the user verbatim along with the version from `references/recipe-version` and the repositories the build tried. Do NOT instruct the user to install it themselves — they may not have source access. Ask: [retry] / [abort].
- **`Unsupported class file major version` / `class file version`** — build wrapper too old for the current JDK. Go to **Wrapper bump** below; that's the preferred recovery. Fallback only if wrapper bump fails or user declines: ask user to set `JAVA_HOME` to a JDK matching the wrapper.
- **Recipe parse/apply error pointing at a specific source file** — surface the offending file path + last 50 log lines. Ask: [retry] / [abort].
- **Anything else** — ask the user [retry] / [abort], with failed command + exit code + last 50 log lines.

# Wrapper bump (recovery action)

Triggered ONLY by the "Unsupported class file major version" routing rule. NEVER preemptively.

Procedure:
1. Detect the wrapper file:
   - Gradle → `gradle/wrapper/gradle-wrapper.properties`
   - Maven → `.mvn/wrapper/maven-wrapper.properties`
   If absent, skip wrapper bump — fall back to the `JAVA_HOME` workaround.
2. Look up the **latest stable release** of Gradle or Maven via `WebFetch` (`https://services.gradle.org/versions/current` for Gradle, `https://maven.apache.org/download.cgi` for Maven) or `WebSearch` if WebFetch is unavailable. Cache the result for the rest of this run.
3. Read the wrapper file's `distributionUrl`. If the current version is already ≥ the latest stable, the JDK error has a different cause — surface output and ask the user.
4. Edit the `distributionUrl` to point at the latest stable. Trust your knowledge of the Gradle/Maven wrapper format.
5. Re-run `migrate.sh <framework>`.
6. The wrapper-properties change is part of the diff and is captured by the canonical commit — no separate commit.

User messaging:
- Before bumping: `🔧 Build wrapper too old for JDK <DETECTED>. Bumping <Gradle|Maven> wrapper to <LATEST> and retrying…`
- If retry succeeds: continue normal success flow.
- If retry still fails: full failure path; surface both attempts to the user.

# User messages (standardized)

Use these verbatim. Substitute `<FRAMEWORK>` and `<BUILD>` (`maven` or `gradle`).

- Start: `🔧 Running Axon 4→5 OpenRewrite recipe (<BUILD>, --framework <FRAMEWORK>)…`
- Success: `✅ Migration recipe applied. Review the diff before committing.`
- Success + auto-commit: `✅ Migration recipe applied and committed.`
- Failure: `❌ Migration failed (exit <CODE>). See output above. <next-action>`
- Missing artifact: `❌ Recipe artifact org.axonframework:axon-migration:<VERSION> did not resolve from any configured repository. Verify network access and the repositories your build is configured to use.`
- JDK mismatch: `❌ Build wrapper too old for JDK <DETECTED>. Attempting wrapper bump…` (then see Wrapper bump section)

# Must / must not

MUST:
- Be idempotent: re-running on an already-migrated project is a no-op (the recipe handles this).
- Use the canonical commit message verbatim.
- Smoke-test the cleanup contract before claiming success.

MUST NOT:
- Run `mvn compile` / `mvn verify` / `./gradlew build` / any other compilation check to "validate" the result. Compilation is out of scope; see Goal.
- Modify the user's project as a recovery step.
- Run any per-module recipe (only the two top-level recipes are supported).
- Copy `init.gradle` into the user's project.
- Skip the commit prompt outside of auto mode.
