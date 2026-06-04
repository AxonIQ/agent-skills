---
name: axoniq-framework-contribute-review
description: For Axon Framework contributors. Performs comprehensive code reviews against AF5 contributor standards: analyzes changed files, checks Antora documentation, verifies test coverage, and ensures compliance with AF5 patterns. Provides actionable fix suggestions that can be applied immediately.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash, Task, Edit, Write
---

# Code Review Skill for Axon Framework

This skill performs systematic code reviews following the comprehensive checklist compiled from Axon Framework review patterns. It not only identifies issues but **provides concrete fix suggestions** that can be applied immediately to the codebase.

## When to Use This Skill

- Before committing code to review it against AF5 standards
- When reviewing a pull request
- To verify a branch is ready for review
- To check if changes meet documentation requirements
- To validate test coverage and quality gates

## Philosophy: Solutions, Not Just Problems

This skill is designed to be **helpful and actionable**:
- ✅ Identifies issues AND suggests specific fixes
- ✅ Provides before/after code examples
- ✅ Can apply fixes immediately when requested
- ✅ Explains WHY changes are needed
- ✅ Acknowledges what's done well
- ❌ Not just a list of complaints

## How This Skill Works

The skill performs a systematic review in the following order:

1. **Detect Changed Files** - Identifies what has been modified
2. **Identify Review Hotspots** - Flags areas needing extra human attention
3. **Critical Requirements Check** - Verifies must-have items
4. **API Design Review** - Checks fluent APIs, naming, null safety
5. **Code Quality Review** - Examines error handling, performance, type safety
6. **Architecture Review** - Validates patterns and modularity
7. **Documentation Review** - Verifies Antora docs and JavaDoc
8. **Test Coverage Review** - Checks tests and quality gates
9. **Generate Review Report with Fix Suggestions** - Actionable improvements
10. **Offer to Apply Fixes** - Can apply suggested changes immediately

## Interactive Fix Workflow

When issues are found, this skill provides an interactive workflow:

1. **Issue Identified** → Describe the problem clearly
2. **Fix Suggested** → Provide specific code changes (before/after)
3. **User Decides** → Developer can:
   - Ask to apply the fix immediately: "Apply fix #1"
   - Request modifications: "Can you adjust fix #2 to also handle X?"
   - Decline: "Skip this one"
   - Apply all: "Apply all suggested fixes"

### Example Interaction

```
Skill: Found 3 issues. Here are suggested fixes:

FIX #1 (BLOCKING): Add missing @since tag
File: EventStore.java:456
Current:
    /**
     * Reads events from the store.
     */
    public Stream<DomainEventMessage<?>> readEvents(String aggregateId) {

Suggested:
    /**
     * Reads events from the store.
     *
     * @since 5.1.0
     */
    public Stream<DomainEventMessage<?>> readEvents(String aggregateId) {

User: Apply fix #1
Skill: ✅ Applied fix #1 to EventStore.java

User: Apply all remaining fixes
Skill: ✅ Applied fixes #2 and #3
```

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

First, determine the scope of changes:

```bash
# Check git status
git status --short

# Get diff stats
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

# Check for files touching multiple concerns
git diff --name-only | while read f; do
  echo "$f: $(git diff $f | grep -c '^@@')"
done | awk '$2 > 5'
```

**Categorize hotspots by type:**
1. **Core Logic Changes** - Files central to the PR's purpose
2. **Structural Changes** - Classes with refactored methods, new fields, inheritance changes
3. **API Changes** - New public methods, changed signatures, deprecated APIs
4. **Complex Logic** - Dense conditionals, nested loops, error handling changes
5. **Cross-cutting Concerns** - Security, threading, transactions, resource management

**For each hotspot, note:**
- File path and change magnitude
- Why it's a hotspot (core logic, complexity, API change)
- Specific areas to focus on
- Review questions for human attention

### Step 3: Read Changed Files

Read all modified files to understand the changes:
- Java source files (.java)
- Test files (*Test.java)
- Documentation files in /docs
- Configuration files

### Step 4: Apply Review Checklist

Use the comprehensive checklist from `../../code-review-checklist.md` to systematically review:

#### Critical Requirements (BLOCKING)

1. **Reference Guide Documentation**
   - Search for changes in `/docs/reference-guide/modules/**/*.adoc`
   - If feature changes exist without reference guide updates, flag as BLOCKING
   - Verify new pages are added to appropriate `nav.adoc` in the module
   - Path: `/docs/reference-guide/modules/[module-name]/pages/`

   **Module Selection Guide:**
   - Event store/sourcing changes → `events/` module
   - Command handling changes → `commands/` module
   - Query handling changes → `queries/` module
   - Saga changes → `sagas/` module
   - Messaging infrastructure → `messaging-concepts/` module
   - Deadline management → `deadlines/` module
   - Metrics/monitoring → `monitoring/` module
   - Testing utilities → `testing/` module
   - Performance → `tuning/` module
   - Breaking changes → `migration/` module
   - New version features → `release-notes/` module

2. **JavaDoc Completeness**
   - Check for missing `@since` tags on new public/protected methods
   - Verify `@author` tags when refactoring code
   - Confirm `@Nullable` annotations on nullable parameters/returns (under `@NullMarked`, non-null is the default)
   - Flag any use of Jakarta `@Nonnull`/`@Nullable` — these are **forbidden** by checkstyle
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

5. **Fluent API Pattern (AF5 Style)**
   - Flag any `builder()` patterns on infrastructure components
   - Verify fluent chaining methods return appropriate types
   - Check for descriptive static factory methods
   - Reference: `../axon-framework-5-patterns/SKILL.md`

6. **Null Safety**
   - Check for null checks before dereferencing (use `Objects.requireNonNull` at method/constructor entry)
   - Verify `@Nullable` on nullable parameters/return types (JSpecify; non-null is the default under `@NullMarked`)
   - Flag any Jakarta `@Nonnull`/`@Nullable` — use JSpecify instead
   - Look for potential NPE vulnerabilities

7. **Method Visibility**
   - Check if methods could be more restrictive
   - Flag unnecessary public methods

#### Code Quality Review

8. **Error Handling**
   - Search for generic exceptions (avoid `IllegalStateException`, prefer `AxonConfigurationException`)
   - Check for swallowed exceptions
   - Verify error messages have context

9. **Performance**
   - Look for `LinkedList` usage (suggest `LinkedHashMap` for lookups)
   - Check for unnecessary object creation in loops
   - Review concurrency patterns

10. **Type Safety**
    - Check for unchecked casts
    - Verify generic type usage
    - Look for raw types

#### Documentation Review

11. **Reference Guide Documentation Structure**
    ```bash
    # Check for reference guide documentation files
    find docs/reference-guide/modules -name "*.adoc" -type f

    # Look for navigation updates
    grep -r "xref:" docs/reference-guide/modules/

    # Check if nav.adoc was updated
    git diff docs/reference-guide/modules/*/nav.adoc
    ```

12. **JavaDoc Quality**
    - Class-level documentation explains purpose
    - Public methods have complete JavaDoc
    - Examples provided for complex APIs
    - Parameters use concise descriptions (no sentence-style caps)

#### Architecture Review

13. **Design Patterns**
    - Verify `ConfigurationEnhancer` usage for cross-cutting concerns
    - Check for proper use of predicates/filters
    - Look for decorator patterns

14. **Dependencies**
    - Check for circular dependencies
    - Verify minimal coupling

15. **Review Hotspots** (Areas requiring extra human attention)
    Identify classes/areas where code smells are most likely. Flag these for focused review:

    **Hotspot Indicators:**
    - Classes with significant structural changes (>50 lines modified, method refactoring, field additions)
    - Core classes essential to the PR's purpose (the "why" of the change)
    - New public APIs or significant API changes
    - Complex logic changes (nested conditions, loops, error handling)
    - Classes handling cross-cutting concerns (security, transactions, threading)
    - Files with multiple unrelated changes (scope creep indicator)
    - Large files (>500 lines) with modifications

    **When to Flag as Hotspot:**
    ```bash
    # Check for large structural changes
    git diff --stat | awk '$2 > 50 { print $1 }'

    # Classes with method signature changes
    git diff | grep -E "^[+-].*public.*\(" | sort | uniq -c
    ```

    **Report Format:**
    Each hotspot should include:
    - File path and reason for flagging
    - Type of change (structural, core logic, API change)
    - Specific areas to focus human review on
    - Why this area is sensitive/risky

16. **Message Handler Wrapper Patterns** (CRITICAL for handler enhancers)
    - ❌ NEVER use `instanceof` to check handler types → Use `canHandleMessageType()`
    - ❌ NEVER unwrap handlers unnecessarily → Preserve the wrapper chain
    - ✅ Use `canHandleMessageType(MessageClass.class)` to check compatibility
    - ✅ Use `unwrap(SpecificType.class)` only when accessing specific wrapper functionality
    - ✅ Handler wrappers should NOT implement specific handler interfaces (e.g., `EventHandlingMember`)
    - ✅ Use `@HasHandlerAttributes` on annotations and check attributes (not annotations directly)
    - ✅ Accept `MessageHandlingMember` in method signatures, not specific handler types

    **Common Issues to Flag:**
    ```java
    // ❌ WRONG - instanceof breaks with generic wrappers
    if (handler instanceof EventHandlingMember) { ... }

    // ❌ WRONG - unwrapping loses wrapper chain behavior
    EventHandlingMember unwrapped = handler.unwrap(EventHandlingMember.class).orElseThrow();
    registerHandler(unwrapped);  // Lost all wrapper behavior!

    // ❌ WRONG - wrapper implements specific handler interface
    class MyWrapper<T> extends WrappedMessageHandlingMember<T>
            implements EventHandlingMember<T> { ... }

    // ✅ CORRECT - canHandleMessageType works through wrappers
    if (!handler.canHandleMessageType(EventMessage.class)) { ... }

    // ✅ CORRECT - preserve wrapper chain
    registerHandler(handler);  // Pass full chain, unwrap only when needed

    // ✅ CORRECT - wrapper doesn't implement specific interfaces
    class MyWrapper<T> extends WrappedMessageHandlingMember<T> { ... }
    ```

    **Search patterns to detect issues:**
    ```bash
    # Find instanceof checks on handlers (likely wrong)
    grep -r "instanceof.*HandlingMember" --include="*.java"

    # Find handler unwrapping (review if wrapper chain is preserved)
    grep -r "\.unwrap(.*HandlingMember\.class)" --include="*.java"

    # Find wrappers that implement specific handler interfaces (likely wrong)
    grep -A2 "extends WrappedMessageHandlingMember" --include="*.java" | grep "implements.*HandlingMember"
    ```

### Step 5: Generate Review Report with Actionable Fixes

Create a structured report with **concrete fix suggestions** for each issue:

```markdown
# Code Review Report

## Summary
- Files Changed: X
- Issues Found: Y total (Z blocking, W warnings, V suggestions)
- Review Hotspots: N (areas needing extra human attention)
- Fixes Available: [Number of automated fixes ready]

## SUGGESTED FIXES

### FIX #1 (BLOCKING): Add missing @since tag
**File:** `ComponentClass.java:456`
**Severity:** BLOCKING ❌
**Issue:** New public method without @since tag
**Why:** All public/protected methods must have @since tags per AF5 standards

**Current code:**
```java
/**
 * Processes items from the specified source.
 */
public Stream<ResultMessage> process(String identifier) {
```

**Suggested fix:**
```java
/**
 * Processes items from the specified source.
 *
 * @param identifier the source identifier
 * @return stream of result messages
 * @since 5.1.0
 */
public Stream<ResultMessage> process(String identifier) {
```

**To apply:** Say "Apply fix #1" or "Apply all fixes"

---

### FIX #2 (WARNING): Use AxonConfigurationException
**File:** `ComponentConfig.java:123`
**Severity:** WARNING ⚠️
**Issue:** Using generic exception for configuration error
**Why:** Configuration errors should use AxonConfigurationException for consistency

**Current code:**
```java
throw new IllegalStateException("Component not configured");
```

**Suggested fix:**
```java
throw new AxonConfigurationException("Component not configured");
```

**Impact:** Need to import `org.axonframework.common.AxonConfigurationException`
**To apply:** Say "Apply fix #2"

---

### FIX #3 (SUGGESTION): Reduce method visibility
**File:** `ComponentImpl.java:789`
**Severity:** SUGGESTION 💡
**Issue:** Public method only used internally
**Why:** Minimizing public API surface improves maintainability

**Current code:**
```java
public void validateInternalState(List<Message> items) {
```

**Suggested fix:**
```java
protected void validateInternalState(List<Message> items) {
```

**To apply:** Say "Apply fix #3"

## DOCUMENTATION NEEDED

### DOC #1 (BLOCKING): Add Antora documentation
**Issue:** New feature added without user-facing documentation
**Required:** Add documentation in appropriate `docs/reference-guide/modules/[module]/pages/`
**Should cover:**
- Overview of the new feature
- Usage examples
- Configuration options
- Migration notes (if applicable)

I can help create a documentation template. Say "Generate doc template for DOC #1"

## REVIEW HOTSPOTS 🔥

Areas where code smells or design issues are most likely. Human reviewers should focus extra attention here:

### HOTSPOT #1: Core Business Logic Change
**File:** `AnnotatedEventHandlingComponent.java` (124 lines changed)
**Type:** Structural + Core Logic
**Why flagged:** Central to this PR's handler wrapper chain preservation fix
**Focus areas:**
- Method `initializeHandlersBasedOnModel()` - Changed from unwrapping to preserving wrapper chain
- Method `registerHandler()` - Signature changed from `EventHandlingMember` to `MessageHandlingMember`
- Verify wrapper chain is actually preserved through the call stack
- Check if downstream code expects `EventHandlingMember` specifically

**Review questions:**
- Are there other callers that might be affected by the signature change?
- Does the new approach handle edge cases (empty handlers, null wrappers)?
- Is error handling appropriate for the new flow?

### HOTSPOT #2: New Public API Surface
**File:** `HandlerAttributes.java` (2 constants added)
**Type:** API Addition
**Why flagged:** New public constants affect handler attribute contracts
**Focus areas:**
- Are constant names following existing conventions?
- Should these be documented in migration guide?
- Are tests covering attribute usage through the wrapper chain?

**Review questions:**
- Could these attributes conflict with existing ones?
- Is the naming consistent with other `HandlerAttributes` constants?
- Are there other places that should use these attributes?

## POSITIVE FINDINGS ✅

- ✅ Excellent test coverage (all new methods tested)
- ✅ Clear JavaDoc examples provided for complex APIs
- ✅ Proper null safety with @Nullable/@Nonnull annotations
- ✅ Good use of AF5 fluent API patterns
- ✅ Configuration class has comprehensive tests

## SUMMARY BY SEVERITY

**BLOCKING (must fix before commit):** 2
- FIX #1: Missing @since tag
- DOC #1: Missing Antora documentation

**WARNINGS (should fix):** 1
- FIX #2: Use AxonConfigurationException

**SUGGESTIONS (nice to have):** 1
- FIX #3: Reduce method visibility

**REVIEW HOTSPOTS (human attention needed):** 2
- HOTSPOT #1: AnnotatedEventHandlingComponent.java - Core logic change
- HOTSPOT #2: HandlerAttributes.java - API surface expansion

> 🔥 **Hotspots** flag areas where code smells are most likely. These aren't necessarily bugs, but deserve extra scrutiny from human reviewers due to complexity, structural changes, or being core to the PR's purpose.

## QUICK ACTIONS

To fix all issues quickly:
- "Apply all fixes" - Applies FIX #1, #2, #3
- "Apply blocking fixes only" - Applies FIX #1
- "Generate doc template for DOC #1" - Creates documentation outline
- "Show me FIX #2 in detail" - Explains specific fix
- "Explain HOTSPOT #1" - Provides more context on a hotspot

## FILES REVIEWED
[List with assessment]
```

## Severity Levels

### BLOCKING ❌
Issues that prevent approval:
- Missing Antora documentation for feature changes
- Missing or incomplete JavaDoc on public APIs
- Apparent lack of test coverage (<80%)
- Breaking changes without migration docs
- Security vulnerabilities
- Resource leaks

### WARNING ⚠️
Issues that should be addressed but may not block:
- Missing `@author` tags
- Method visibility could be reduced
- Performance concerns (non-critical)
- Code duplication
- Missing null safety annotations

### SUGGESTION 💡
Improvements and best practices:
- Better naming
- Additional test cases
- Code organization
- Documentation enhancements

## Quick Review Mode

For a fast review focusing only on critical items:

```bash
# Check for doc changes
git diff --name-only | grep "^docs/"

# Check for test files
git diff --name-only | grep "Test.java$"

# Check for breaking changes
git diff | grep -E "(@Deprecated|public.*\(|protected.*\()"
```

Then apply only the BLOCKING checklist items.

## Comprehensive Review Mode

For a thorough review:

1. Read all changed files completely
2. Apply full checklist from `code-review-checklist.md`
3. Cross-reference with `axon-framework-5-patterns` skill
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

## Crafting Fix Suggestions

### Principles for Good Fix Suggestions

1. **Be Specific** - Show exact before/after code
2. **Explain Why** - Don't just say what's wrong, explain the reasoning
3. **Provide Context** - Reference checklist items, past PRs, or standards
4. **Consider Impact** - Note any imports, dependencies, or side effects
5. **Make it Actionable** - User should be able to apply immediately

### Fix Template Structure

For each issue, provide:

```markdown
### FIX #[N] ([SEVERITY]): [Brief Title]
**File:** `[file.java:line]`
**Severity:** [BLOCKING/WARNING/SUGGESTION] [emoji]
**Issue:** [What's wrong]
**Why:** [Explain the reasoning - reference standards/patterns]

**Current code:**
```java
[actual code from file]
```

**Suggested fix:**
```java
[corrected code]
```

**Impact:** [Any imports needed, side effects, or considerations]
**To apply:** Say "Apply fix #[N]"
```

### Types of Fixes to Generate

#### 1. JavaDoc Fixes (Very Common)
**Easy to automate:** YES
- Add missing `@since` tags
- Add missing `@author` tags
- Add missing `@param` or `@return` docs
- Fix sentence-style capitalization in parameter docs
- Add constructor javadoc with defaults
- Clarify ambiguous terminology

**Example - Method JavaDoc:**
```java
// Before
/**
 * Processes items.
 */
public Stream<ResultMessage> process(String identifier) {

// After
/**
 * Processes items from the specified source.
 *
 * @param identifier the source identifier
 * @return stream of result messages
 * @since 5.1.0
 */
public Stream<ResultMessage> process(String identifier) {
```

**Example - Constructor JavaDoc:**
```java
// Before
public ComponentConfiguration() {

// After
/**
 * Constructs a default {@code ComponentConfiguration} with the following settings:
 * <ul>
 *     <li>Thread count: 10</li>
 *     <li>Queue capacity: 1000</li>
 *     <li>Auto-retry: enabled</li>
 * </ul>
 */
public ComponentConfiguration() {
```

**Example - Terminology Clarity:**
```java
// Before (ambiguous - "prefer" could mean priority)
/**
 * Indicates whether local handlers are preferred over remote ones.
 */

// After (clear - explains fallback behavior)
/**
 * Indicates whether local handlers are used directly when available, bypassing
 * remote dispatch. When no local handler is available, the request is dispatched
 * remotely through the connector.
 */
```

#### 2. Annotation Fixes
**Easy to automate:** YES
- Add `@Nullable` for parameters/return values that may be null
- Verify `package-info.java` has `@NullMarked` (non-null is the default under it)
- Fix wrong annotation library (jakarta → jspecify — jakarta is **forbidden** by checkstyle)

**Example — missing @Nullable:**
```java
// Before (nullable parameter not marked)
public void process(String id, Object payload) {

// After (JSpecify — only @Nullable needed, non-null is default under @NullMarked)
public void process(String id, @Nullable Object payload) {
```

**Impact:** May need to add `import org.jspecify.annotations.Nullable;` and ensure `package-info.java` has `@NullMarked`.

**Example — wrong annotation library:**
```java
// ❌ WRONG — jakarta annotations are forbidden
import jakarta.annotation.Nonnull;
import jakarta.annotation.Nullable;

// ✅ CORRECT — use JSpecify
import org.jspecify.annotations.Nullable;
// (non-null is default under @NullMarked — no @Nonnull needed)
```

#### 3. Exception Type Fixes
**Easy to automate:** YES
- Replace generic exceptions with `AxonConfigurationException`

**Example:**
```java
// Before
throw new IllegalStateException("EventStore not configured");

// After
throw new AxonConfigurationException("EventStore not configured");
```

**Impact:** Need `import org.axonframework.common.AxonConfigurationException;`

#### 4. Visibility Fixes
**Easy to automate:** YES (but verify intent first)
- Reduce method visibility when appropriate

**Example:**
```java
// Before
public void internalHelper() {

// After
protected void internalHelper() {
```

**Caveat:** Ask if unsure whether method is part of public API

#### 5. Data Structure Fixes
**Moderate automation:** Requires understanding usage
- Replace `LinkedList` with `LinkedHashMap` for lookup-heavy code

**Example:**
```java
// Before
private final LinkedList<Item> cache = new LinkedList<>();
// ... frequent lookups with cache.contains()

// After
private final LinkedHashMap<String, Item> cache = new LinkedHashMap<>();
```

**Impact:** May need to adjust add/remove logic

#### 6. Pattern Matching Modernization
**Easy to automate:** YES
- Convert old-style instanceof to pattern matching

**Example:**
```java
// Before
if (token instanceof MultiSourceToken) {
    MultiSourceToken mst = (MultiSourceToken) token;
    return mst.getPosition();
}

// After
if (token instanceof MultiSourceToken mst) {
    return mst.getPosition();
}
```

#### 7. Handler Wrapper Pattern Fixes
**Easy to automate:** YES (Common in HandlerEnhancerDefinition implementations)
- Replace `instanceof` checks with `canHandleMessageType()`
- Remove unnecessary unwrapping that loses wrapper chain
- Remove specific handler interface implementations from wrappers

**Example 1 - Type Check:**
```java
// Before
@Override
public <T> MessageHandlingMember<T> wrapHandler(@Nonnull MessageHandlingMember<T> original) {
    if (original instanceof EventHandlingMember) {
        return new MyWrapper<>(original);
    }
    return original;
}

// After
@Override
public <T> MessageHandlingMember<T> wrapHandler(@Nonnull MessageHandlingMember<T> original) {
    if (!original.canHandleMessageType(EventMessage.class)) {
        return original;
    }
    return new MyWrapper<>(original);
}
```

**Example 2 - Preserve Wrapper Chain:**
```java
// Before
private void initializeHandlers() {
    model.getUniqueHandlers(targetClass, EventMessage.class)
         .forEach(handler -> {
             // Loses wrapper chain!
             EventHandlingMember<T> eventHandler = handler.unwrap(EventHandlingMember.class)
                     .orElseThrow(...);
             registerHandler(eventHandler);
         });
}

// After
private void initializeHandlers() {
    model.getUniqueHandlers(targetClass, EventMessage.class)
         .forEach(handler -> {
             // Preserves wrapper chain
             if (!handler.canHandleMessageType(EventMessage.class)) {
                 throw new IllegalStateException(...);
             }
             registerHandler(handler);  // Pass full chain
         });
}

// Update method signature
private void registerHandler(MessageHandlingMember<? super T> handler) {  // Not EventHandlingMember
    // Can unwrap to specific types when needed
    Optional<SequencingPolicy> policy = handler.unwrap(SequencingPolicyMember.class)
                                               .map(SequencingPolicyMember::sequencingPolicy);
    // ...
}
```

**Example 3 - Wrapper Class Definition:**
```java
// Before
private static class MyWrapper<T> extends WrappedMessageHandlingMember<T>
        implements EventHandlingMember<T> {  // Don't implement specific interfaces
    // ...
}

// After
private static class MyWrapper<T> extends WrappedMessageHandlingMember<T> {
    // No need to implement EventHandlingMember - unwrap() handles it
    // ...
}
```

**Impact:**
- May need to update method signatures from `EventHandlingMember` to `MessageHandlingMember`
- May need to add `import org.axonframework.messaging.eventhandling.EventMessage;`
- Tests using `instanceof` checks should be updated to use `unwrap()` pattern

#### 8. Fluent API Pattern Fixes
**Complex:** Requires significant refactoring
- Don't auto-fix, but provide detailed guidance

**Example:**
```markdown
FIX #5 (WARNING): Convert to AF5 fluent style
This requires refactoring the builder pattern. I can help with this.
See: .claude/skills/axon-framework-5-patterns/SKILL.md

Would you like me to refactor this builder to AF5 style?
```

### Fix Prioritization

When multiple fixes are available:

1. **Group by severity** - BLOCKING first, then WARNINGS, then SUGGESTIONS
2. **Number sequentially** - FIX #1, FIX #2, etc.
3. **Batch related fixes** - All JavaDoc fixes together
4. **Provide bulk actions** - "Apply all JavaDoc fixes", "Apply all blocking fixes"

### Applying Fixes

When user requests a fix:

1. **Verify current state** - Re-read the file to ensure it hasn't changed
2. **Apply using Edit tool** - Use exact string replacement
3. **Confirm success** - Report what was changed
4. **Track what's applied** - Keep count of applied fixes

**Example Application:**
```
User: Apply fix #1

Skill:
✅ Applied FIX #1: Added @since 5.1.0 tag to EventStore.readEvents()
   File: EventStore.java:456

Remaining fixes: 3 (1 blocking, 2 warnings)
Would you like to apply more? Say "Apply fix #2" or "Apply all remaining"
```

### When NOT to Auto-Fix

Some issues require discussion, not automatic fixes:

- **Architecture changes** - Requires design decisions
- **Breaking changes** - Need justification and migration docs
- **Performance optimizations** - May have trade-offs
- **Missing documentation** - Need content from developer
- **Missing tests** - Need to understand intended behavior

For these, provide **guidance** instead:

```markdown
DOC #1 (BLOCKING): Add Antora documentation
**Required:** Documentation in docs/reference-guide/modules/events/pages/

I can generate a documentation template covering:
- Feature overview
- Usage examples
- Code samples

Say "Generate doc template for DOC #1" and I'll create a starting point.
```

### Batch Fix Operations

Support these batch commands:

- "Apply all fixes" - All automated fixes
- "Apply blocking fixes only" - Only severity BLOCKING
- "Apply all JavaDoc fixes" - All documentation fixes
- "Apply fixes #1, #3, #5" - Specific set
- "Skip fix #2" - Exclude specific fix

## Test Quality Patterns

### Test Object Creation Strategy

When reviewing tests, assess the quality of test object creation:

**Prefer this hierarchy:**
1. **Real objects** - When straightforward to create
2. **Stub implementations** - When behavior is simple but construction is complex
3. **Mocks** - Only when necessary for verification

**Example - Real objects (PREFERRED):**
```java
// ✅ Use real message objects with factory methods
private static QueryMessage queryMessage(QualifiedName name) {
    return new GenericQueryMessage(new MessageType(name), "test-payload");
}

// In test:
QueryMessage query = queryMessage(new QualifiedName("TestQuery"));
```

**Example - Stub implementations (GOOD):**
```java
// ✅ Stub for tracking behavior
private static class StubConnector implements BusConnector {
    final Set<QualifiedName> subscriptions = new HashSet<>();
    final AtomicInteger callCount = new AtomicInteger(0);

    @Override
    public void subscribe(QualifiedName name) {
        subscriptions.add(name);
        callCount.incrementAndGet();
    }
}
```

**Example - Mocks (USE SPARINGLY):**
```java
// ⚠️ Only when necessary for complex verification
BusConnector connector = mock(BusConnector.class);
verify(connector).subscribe(eq(queryName));
```

### Resource Cleanup in Tests

**Check that tests clean up resources:**
- ExecutorServices must be shutdown
- Temporary files/directories must be deleted
- Database connections must be closed
- Network connections must be closed

**Pattern verification:**
```java
// ✅ Good - cleanup in finally block
@Test
void testExecutorCreation() {
    ExecutorService executor = component.createExecutor();
    try {
        // test assertions
    } finally {
        executor.shutdown();
    }
}

// ✅ Good - cleanup in @AfterEach
@AfterEach
void cleanup() {
    if (executorService != null) {
        executorService.shutdown();
    }
}
```

## Integration with Other Skills

### Use with axon-framework-5-patterns
When reviewing builder patterns or infrastructure components:
```
Invoke: axon-framework-5-patterns
Then: code-review
```

### Use with git commit workflow
After staging changes but before committing:
```
Run: /code-review
```

## Review Checklist Reference

The complete review checklist is available in:
`../../code-review-checklist.md`

This includes:
- 27 major review categories
- Detailed criteria for each category
- Examples from actual PRs
- Common issues and solutions
- Quick reference for top 10 most common feedback items

## Automated Checks to Verify

While performing the review, remind about these automated checks:

```bash
# SonarQube (CI will run this)
# - Coverage: ≥ 80% on new code
# - Duplication: ≤ 3%
# - Reliability: A rating
# - Security: A rating

# Documentation linting
# - Vale linter for Antora docs
# - Run on CI

# Build verification
# - All modules build successfully
# - No compiler warnings
```

## Example Usage

### Reviewing Current Changes
```
User: /code-review
Skill: [Checks git status, reads changed files, applies checklist, generates report]
```

### Reviewing a Specific Branch
```
User: /code-review feature/my-feature
Skill: [Compares against main branch, performs comprehensive review]
```

### Quick Pre-Commit Check
```
User: /code-review --quick
Skill: [Runs only BLOCKING checks for fast feedback]
```

## Output Format

The skill will output an **interactive, actionable review report** with:

1. **Executive Summary** - Quick overview with fix counts
2. **Suggested Fixes** - Numbered fixes with before/after code
3. **Documentation Needs** - Items requiring developer input
4. **Positive Findings** - What's done well
5. **Quick Actions** - Commands to apply fixes immediately

Example:
```
# Code Review Report

## Summary
- Files Changed: 3
- Issues Found: 4 (2 blocking, 1 warning, 1 suggestion)
- Automated Fixes Available: 3

---

## SUGGESTED FIXES

### FIX #1 (BLOCKING): Add missing @since tag
**File:** `EventStore.java:456`
**Issue:** New public method without @since tag
**Why:** All public/protected members must have @since tags (AF5 standard)

**Current code:**
```java
/**
 * Reads events from the store.
 */
public Stream<DomainEventMessage<?>> readEvents(String aggregateId) {
```

**Suggested fix:**
```java
/**
 * Reads events from the store.
 *
 * @param aggregateId the aggregate identifier
 * @return stream of domain events for the aggregate
 * @since 5.1.0
 */
public Stream<DomainEventMessage<?>> readEvents(String aggregateId) {
```

**To apply:** Say "Apply fix #1" or "Apply all fixes"

---

### FIX #2 (WARNING): Use AxonConfigurationException
**File:** `EventStoreConfig.java:123`
**Issue:** Generic exception for configuration error
**Why:** Use AxonConfigurationException for consistency

**Current code:**
```java
throw new IllegalStateException("EventStore not configured");
```

**Suggested fix:**
```java
throw new AxonConfigurationException("EventStore not configured");
```

**Impact:** Add import `org.axonframework.common.AxonConfigurationException`
**To apply:** Say "Apply fix #2"

---

### FIX #3 (SUGGESTION): Reduce method visibility
**File:** `EventStoreImpl.java:789`
**Issue:** Public method only used internally
**Why:** Minimize public API surface

**Current code:**
```java
public void validateEventSequence(List<DomainEventMessage<?>> events) {
```

**Suggested fix:**
```java
protected void validateEventSequence(List<DomainEventMessage<?>> events) {
```

**To apply:** Say "Apply fix #3"

---

## DOCUMENTATION NEEDED

### DOC #1 (BLOCKING): Add Antora documentation
**Issue:** New feature without user-facing documentation
**Required:** Documentation in docs/reference-guide/modules/events/pages/
**Should cover:**
- Feature overview
- Usage examples
- API reference

**Action:** Say "Generate doc template for DOC #1" for a starting point

---

## POSITIVE FINDINGS ✅

- ✅ Excellent test coverage in EventStoreTest.java
- ✅ Proper null safety with @Nullable/@Nonnull
- ✅ Good use of AF5 fluent patterns

---

## QUICK ACTIONS

Ready to fix these issues?
- "Apply all fixes" - Applies FIX #1, #2, #3
- "Apply blocking fixes only" - Applies FIX #1
- "Apply fix #[N]" - Apply specific fix
- "Generate doc template for DOC #1" - Create documentation outline
- "Show me fix #[N] in detail" - Explain specific fix further

---

**Current Status:** 2 BLOCKING issues (1 fix available, 1 needs docs)
**After applying all fixes:** 1 BLOCKING issue remaining (DOC #1)
```

## Tips for Effective Reviews

1. **Read the checklist first** - Familiarize yourself with common issues
2. **Focus on blocking items initially** - Don't let perfect be the enemy of good
3. **Provide specific file:line references** - Make it easy to find issues
4. **Suggest solutions** - Don't just point out problems
5. **Acknowledge good work** - Positive findings motivate
6. **Be constructive** - Frame feedback as improvements, not criticisms
7. **Consider context** - Understand the intent before suggesting changes

## Review Report Template

See `templates/review-report-template.md` for a reusable report structure.

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

---

*This skill references: `../../code-review-checklist.md` for comprehensive criteria*
*Related skills: `axon-framework-5-patterns` for API design validation*
