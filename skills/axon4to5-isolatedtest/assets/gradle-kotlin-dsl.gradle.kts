// Per-target isolated source set + Test task (Kotlin DSL).
// Copy into the relevant subproject's build.gradle.kts.
// Replace placeholders:
//   <TargetName> — simple class name (PascalCase): e.g. ResourcesPool, PaymentId.
//   <relpath>    — repo-relative file paths under src/main/{java,kotlin}
//                  and src/test/{java,kotlin}.
//
// Pure-Java sources: use srcDir("src/main/java") / srcDir("src/test/java").
// Kotlin or mixed sources: include srcDir("src/main/kotlin") too. The Kotlin
// Gradle plugin compiles .kt files in any source set as long as kotlin("jvm")
// is applied at project level.
//
// See ../references/gradle.md for verify commands and cleanup.

sourceSets {
    create("isolated<TargetName>") {
        java {
            srcDir("src/main/java")
            srcDir("src/main/kotlin")
            include(
                "<relpath under src/main/{java,kotlin}>.<java|kt>",
                // one entry per main-source file
            )
        }
    }
    create("isolated<TargetName>Test") {
        java {
            srcDir("src/test/java")
            srcDir("src/test/kotlin")
            include(
                "<relpath under src/test/{java,kotlin}>.<java|kt>",
                // one entry per test-source file
            )
        }
        compileClasspath += sourceSets["isolated<TargetName>"].output
        runtimeClasspath += sourceSets["isolated<TargetName>"].output
    }
}

// Inherit the project's dependencies WITHOUT pulling in the main / test
// source-set OUTPUTS. The whole point of isolation is to keep working even
// when the regular `main` / `test` source sets fail to compile. We extend
// the dependency configurations (which carry the external libs) but skip
// `sourceSets["main"].output` — that would trigger `compileMain` and undo
// the isolation. If the target needs a helper from `main`, add its source
// path to the source set's `include(...)` list above.
//
// `extendsFrom` is required since Gradle 8: passing a Configuration directly
// as a dependency (`isolated<TargetName>Implementation(configurations["implementation"])`)
// is no longer allowed and fails at configuration time.
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

// Optional: extra deps that should ONLY be active in this scope.
// dependencies {
//     "isolated<TargetName>TestImplementation"("group:artifact:version")
// }

tasks.register<Test>("testIsolated<TargetName>") {
    description = "Run tests for <TargetName> in isolation."
    group = "verification"
    testClassesDirs = sourceSets["isolated<TargetName>Test"].output.classesDirs
    classpath = sourceSets["isolated<TargetName>Test"].runtimeClasspath
    useJUnitPlatform()
}
