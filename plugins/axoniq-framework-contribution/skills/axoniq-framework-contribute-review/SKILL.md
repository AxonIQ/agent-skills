---
name: axoniq-framework-contribute-review
description: For Axon Framework contributors. Performs comprehensive code reviews against AF5 contributor standards: analyzes changed files, checks Antora documentation, verifies test coverage, and ensures compliance with AF5 patterns. Provides actionable fix suggestions that can be applied immediately.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash, Agent, Edit, Write
---

# Code Review Skill for Axon Framework

This skill performs systematic code reviews against Axon Framework 5 contributor standards. It not only identifies issues but **provides concrete fix suggestions** that can be applied immediately.

**Supporting files** — load when needed:
- `quick-reference.md` — top-10 issues, fast checks, grep patterns, severity decision tree
- `references/fix-patterns.md` — how to craft fix suggestions per issue type (JavaDoc, annotations, exceptions, visibility, handler wrappers, ...) and batch-apply them
- `templates/review-report-template.md` — the report structure to fill in

## When to Use This Skill

- Before committing code to review it against AF5 standards
- When reviewing a pull request
- To verify a branch is ready for review
- To check if changes meet documentation requirements
- To validate test coverage and quality gates

## Philosophy: Solutions, Not Just Problems

- ✅ Identifies issues AND suggests specific fixes with before/after code
- ✅ Can apply fixes immediately when requested
- ✅ Explains WHY changes are needed
- ✅ Acknowledges what's done well
- ❌ Not just a list of complaints

## Interactive Fix Workflow

1. **Issue Identified** → Describe the problem clearly
2. **Fix Suggested** → Provide specific code changes (before/after)
3. **User Decides** → Developer can:
   - Ask to apply the fix immediately: "Apply fix #1"
   - Request modifications: "Can you adjust fix #2 to also handle X?"
   - Decline: "Skip this one"
   - Apply all: "Apply all suggested fixes"

When applying a fix: re-read the file first (it may have changed), apply with the Edit tool, confirm what changed, and keep count of applied vs remaining fixes. See `references/fix-patterns.md` for fix templates, batch commands, and when NOT to auto-fix.

## Review Process

### Step 0: Identify Framework Context

Before anything else, determine which framework is being reviewed:

```bash
# Check package names to identify the framework
grep -r "^package " --include="*.java" | head -5
```

| Package prefix | Framework | License |
|---|---|---|
| `org.axonframework` | Axon Framework | Apache 2.0 (OSS) |
| `io.axoniq.framework` | Axoniq Framework | Commercial |

**Feature boundary check** — flag if a change seems misplaced:
- Core messaging, event sourcing, modelling, basic Spring, test utilities → Axon Framework (OSS)
- DLQ (JDBC/JPA), PostgreSQL storage, distributed messaging, Spring Boot auto-config → Axoniq Framework

Both frameworks share the same coding conventions. The review checklist applies equally to both.

### Step 1: Identify Changed Files

```bash
git status --short
git diff --stat
# For PR reviews, compare against target branch
git diff main...HEAD --name-only
```

### Step 2: Identify Review Hotspots

Before diving into detailed review, identify areas requiring extra scrutiny:

```bash
# Find files with significant changes (>50 lines)
git diff --stat | awk '$2 > 50 { print $1 " (" $2 " lines)" }'

# Find files with method signature changes
git diff | grep -B2 -A2 "^[+-].*public.*\(" | grep "^[+-]"

# Find new public classes/interfaces
git diff | grep "^+public class\|^+public interface"
```

**Hotspot indicators:** classes with significant structural changes (>50 lines, method refactoring, field additions); core classes essential to the PR's purpose; new public APIs or signature changes; complex logic changes (nested conditions, loops, error handling); cross-cutting concerns (security, threading, transactions, resources); files with multiple unrelated changes (scope creep); large files (>500 lines) with modifications.

**For each hotspot, note:** file path and change magnitude, why it's a hotspot, specific areas to focus on, and review questions for human attention. Hotspots aren't necessarily bugs — they flag where code smells are most likely, deserving extra human scrutiny.

### Step 3: Read Changed Files

Read all modified files to understand the changes: Java sources, test files, documentation in `/docs`, configuration files.

### Step 4: Apply Review Checklist

#### Critical Requirements (BLOCKING)

1. **Reference Guide Documentation**
   - Search for changes in `/docs/reference-guide/modules/**/*.adoc`
   - If feature changes exist without reference guide updates, flag as BLOCKING
   - Verify new pages are added to appropriate `nav.adoc` in the module
   - Module selection: event store/sourcing → `events/`; commands → `commands/`; queries → `queries/`; sagas → `sagas/`; messaging infrastructure → `messaging-concepts/`; deadlines → `deadlines/`; metrics/monitoring → `monitoring/`; testing utilities → `testing/`; performance → `tuning/`; breaking changes → `migration/`; new version features → `release-notes/`

2. **JavaDoc Completeness**
   - Check for missing `@since` tags on new public/protected methods
   - Verify `@author` tags when refactoring code
   - Confirm `@Nullable` annotations on nullable parameters/returns (under `@NullMarked`, non-null is the default)
   - Flag any use of Jakarta `@Nonnull`/`@Nullable` — these are **forbidden** by checkstyle; use JSpecify
   - Look for class-level JavaDoc with examples
   - Verify constructor javadoc documents defaults (especially for configuration classes)
   - Check for ambiguous terminology that users might misinterpret
   - Ensure `@param`/`@return`/`@throws` tags use **fragment style** (lowercase, no trailing period)

3. **Test Coverage**
   - Check if new/modified classes have corresponding test files
   - Look for test methods covering new public methods
   - Flag if tests appear insufficient for 80% coverage
   - Verify configuration classes have comprehensive tests

4. **Configuration Class Testing** (if configuration classes modified)
   - Default values documented and tested
   - Immutability verified (methods return new instances)
   - Fluent chaining tested (multiple modifications preserve all settings)
   - Null rejection tested where applicable
   - Factory methods produce working components
   - Resource cleanup in tests (ExecutorServices, connections, etc.)

5. **Breaking Changes**
   - Search for API signature changes
   - Check if deprecation markers exist
   - Verify migration documentation if breaking

#### API Design Review

6. **Fluent API Pattern (AF5 Style)**
   - Flag any `builder()` patterns on infrastructure components
   - Verify fluent chaining methods return appropriate types
   - Check for descriptive static factory methods
   - Reference: `../axoniq-framework-contribute-code/references/fluent-builders.md`

7. **Null Safety**
   - Check for null checks before dereferencing (use `Objects.requireNonNull` at method/constructor entry)
   - Verify `@Nullable` on nullable parameters/return types (JSpecify; non-null is the default under `@NullMarked`)
   - Flag any Jakarta `@Nonnull`/`@Nullable` — use JSpecify instead
   - Look for potential NPE vulnerabilities

8. **Method Visibility**
   - Check if methods could be more restrictive
   - Flag unnecessary public methods

#### Code Quality Review

9. **Error Handling**
   - Search for generic exceptions (avoid `IllegalStateException`, prefer `AxonConfigurationException`)
   - Check for swallowed exceptions
   - Verify error messages have context

10. **Performance**
    - Look for `LinkedList` usage (suggest `LinkedHashMap` for lookups)
    - Check for unnecessary object creation in loops
    - Review concurrency patterns

11. **Type Safety**
    - Check for unchecked casts
    - Verify generic type usage
    - Look for raw types

#### Documentation Review

12. **Reference Guide Documentation Structure**
    ```bash
    find docs/reference-guide/modules -name "*.adoc" -type f
    grep -r "xref:" docs/reference-guide/modules/
    git diff docs/reference-guide/modules/*/nav.adoc
    ```

13. **JavaDoc Quality**
    - Class-level documentation explains purpose
    - Public methods have complete JavaDoc
    - Examples provided for complex APIs
    - Parameters use concise descriptions (no sentence-style caps)

#### Architecture Review

14. **Design Patterns**
    - Verify `ConfigurationEnhancer` usage for cross-cutting concerns
    - Check for proper use of predicates/filters
    - Look for decorator patterns

15. **Dependencies**
    - Check for circular dependencies
    - Verify minimal coupling

16. **Message Handler Wrapper Patterns** (CRITICAL for handler enhancers)
    - ❌ NEVER use `instanceof` to check handler types → Use `canHandleMessageType()`
    - ❌ NEVER unwrap handlers unnecessarily → Preserve the wrapper chain
    - ✅ Use `unwrap(SpecificType.class)` only when accessing specific wrapper functionality
    - ✅ Handler wrappers should NOT implement specific handler interfaces (e.g., `EventHandlingMember`)
    - ✅ Use `@HasHandlerAttributes` on annotations and check attributes (not annotations directly)
    - ✅ Accept `MessageHandlingMember` in method signatures, not specific handler types

    Full pattern catalogue with before/after examples: `../axoniq-framework-contribute-code/references/handler-wrappers.md`.

    **Search patterns to detect issues:**
    ```bash
    # Find instanceof checks on handlers (likely wrong)
    grep -r "instanceof.*HandlingMember" --include="*.java"

    # Find handler unwrapping (review if wrapper chain is preserved)
    grep -r "\.unwrap(.*HandlingMember\.class)" --include="*.java"

    # Find wrappers that implement specific handler interfaces (likely wrong)
    grep -A2 "extends WrappedMessageHandlingMember" --include="*.java" | grep "implements.*HandlingMember"
    ```

#### Test Quality Review

17. **Test Object Creation** — prefer real objects (factory methods for messages), then stubs for tracking behavior, mocks only when necessary for verification. Flag mocked message objects.
18. **Resource Cleanup in Tests** — ExecutorServices shutdown, temp files deleted, connections closed; cleanup in `finally` or `@AfterEach`. Flag ExecutorService without shutdown.

    Detailed patterns: `../axoniq-framework-contribute-code/references/testing.md`.

### Step 5: Generate Review Report

Fill in the structure from `templates/review-report-template.md`. The report contains, in order:

1. **Executive Summary** — files changed, issue counts by severity, fixes available, overall status
2. **SUGGESTED FIXES** — numbered, severity-tagged fixes with before/after code and "To apply" actions (see `references/fix-patterns.md` for the per-type templates)
3. **DOCUMENTATION NEEDED** — items requiring developer input, with offer to generate doc templates
4. **REVIEW HOTSPOTS 🔥** — areas for focused human attention, each with focus areas and review questions
5. **POSITIVE FINDINGS ✅** — what's done well
6. **SUMMARY BY SEVERITY** — blocking / warnings / suggestions / hotspots
7. **QUICK ACTIONS** — batch commands ("Apply all fixes", "Apply blocking fixes only", "Generate doc template for DOC #1")
8. **FILES REVIEWED** — list with assessment

### Step 6: Offer to Apply Fixes

After presenting the report, offer the batch actions above and process them per the Interactive Fix Workflow.

## Severity Levels

### BLOCKING ❌
Issues that prevent approval: missing Antora documentation for feature changes; missing or incomplete JavaDoc on public APIs; apparent lack of test coverage (<80%); breaking changes without migration docs; security vulnerabilities; resource leaks.

### WARNING ⚠️
Should be addressed but may not block: missing `@author` tags; method visibility could be reduced; non-critical performance concerns; code duplication; missing null safety annotations.

### SUGGESTION 💡
Improvements and best practices: better naming; additional test cases; code organization; documentation enhancements.

See the severity decision tree in `quick-reference.md` when unsure.

## Quick Review Mode

For a fast review focusing only on critical items, run the "Fast Checks" from `quick-reference.md`:

```bash
git diff --name-only | grep "^docs/"          # doc changes
git diff --name-only | grep "Test.java$"      # test files
git diff | grep -E "(@Deprecated|public.*\(|protected.*\()"  # breaking changes
```

Then apply only the BLOCKING checklist items.

## Comprehensive Review Mode

For a thorough review:

1. Read all changed files completely
2. Apply the full checklist above
3. Cross-reference with the `axoniq-framework-contribute-code` skill's design patterns
4. Check related files that might be affected
5. Review test files in detail
6. Examine documentation structure

## Common Review Patterns

### New Feature Added
1. ✅ Check `/docs` for new documentation
2. ✅ Verify test coverage
3. ✅ Check JavaDoc completeness
4. ✅ Review API design (fluent patterns)
5. ✅ Verify no breaking changes to existing APIs

### Bug Fix
1. ✅ Verify fix is targeted and minimal
2. ✅ Check for regression tests
3. ✅ Review error handling
4. ✅ Confirm no breaking changes

### Refactoring
1. ✅ Verify `@author` tags preserved or updated
2. ✅ Check tests still pass and cover refactored code
3. ✅ Ensure no behavioral changes
4. ✅ Review method visibility

### Breaking Change
1. ✅ Verify marked with ! in commit/PR title
2. ✅ Check migration documentation exists
3. ✅ Confirm justification provided
4. ✅ Review storage implications
5. ✅ Check release notes updated

## Automated Checks to Verify

While performing the review, remind about these automated checks:

- **SonarQube (CI)**: coverage ≥ 80% on new code, duplication ≤ 3%, reliability A, security A
- **Documentation linting**: Vale linter for Antora docs (runs on CI)
- **Build verification**: all modules build, no compiler warnings

## Frequently Checked Items

Based on analysis of 20+ PRs, these are checked most frequently:

1. ✅ `@since` tags on new public/protected members (VERY COMMON)
2. ✅ `@author` tags when refactoring (COMMON)
3. ✅ Antora documentation in `/docs` (CRITICAL)
4. ✅ Test coverage ≥ 80% (ENFORCED)
5. ✅ JSpecify `@Nullable` on nullable params/returns; `@NullMarked` on packages (Jakarta forbidden)
6. ✅ Use `AxonConfigurationException` not generic exceptions
7. ✅ Method visibility minimized
8. ✅ No `LinkedList` for lookup-heavy operations
9. ✅ Breaking changes justified and documented
10. ✅ Resource cleanup (try-with-resources)

## Tips for Effective Reviews

1. **Focus on blocking items initially** - Don't let perfect be the enemy of good
2. **Provide specific file:line references** - Make it easy to find issues
3. **Suggest solutions** - Don't just point out problems
4. **Acknowledge good work** - Positive findings motivate
5. **Consider context** - Understand the intent before suggesting changes

---

*Related skills: `axoniq-framework-contribute-code` for the design patterns this review checks against; `axoniq-framework-contribute-docs` for writing the missing documentation.*
