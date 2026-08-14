# Crafting Fix Suggestions

How to turn a review finding into an actionable, immediately-applicable fix.

## Principles for Good Fix Suggestions

1. **Be Specific** - Show exact before/after code
2. **Explain Why** - Don't just say what's wrong, explain the reasoning
3. **Provide Context** - Reference checklist items, past PRs, or standards
4. **Consider Impact** - Note any imports, dependencies, or side effects
5. **Make it Actionable** - User should be able to apply immediately

## Fix Template Structure

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

## Types of Fixes to Generate

### 1. JavaDoc Fixes (Very Common)
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

### 2. Annotation Fixes
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

### 3. Exception Type Fixes
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

### 4. Visibility Fixes
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

### 5. Data Structure Fixes
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

### 6. Pattern Matching Modernization
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

### 7. Handler Wrapper Pattern Fixes
**Easy to automate:** YES (Common in HandlerEnhancerDefinition implementations)
- Replace `instanceof` checks with `canHandleMessageType()`
- Remove unnecessary unwrapping that loses wrapper chain
- Remove specific handler interface implementations from wrappers

For the full rationale and pattern catalogue, see
`../../axoniq-framework-contribute-code/references/handler-wrappers.md`.

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

### 8. Fluent API Pattern Fixes
**Complex:** Requires significant refactoring
- Don't auto-fix, but provide detailed guidance

**Example:**
```markdown
FIX #5 (WARNING): Convert to AF5 fluent style
This requires refactoring the builder pattern. I can help with this.
See: ../../axoniq-framework-contribute-code/references/fluent-builders.md

Would you like me to refactor this builder to AF5 style?
```

## Fix Prioritization

When multiple fixes are available:

1. **Group by severity** - BLOCKING first, then WARNINGS, then SUGGESTIONS
2. **Number sequentially** - FIX #1, FIX #2, etc.
3. **Batch related fixes** - All JavaDoc fixes together
4. **Provide bulk actions** - "Apply all JavaDoc fixes", "Apply all blocking fixes"

## Applying Fixes

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

## When NOT to Auto-Fix

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

## Batch Fix Operations

Support these batch commands:

- "Apply all fixes" - All automated fixes
- "Apply blocking fixes only" - Only severity BLOCKING
- "Apply all JavaDoc fixes" - All documentation fixes
- "Apply fixes #1, #3, #5" - Specific set
- "Skip fix #2" - Exclude specific fix
