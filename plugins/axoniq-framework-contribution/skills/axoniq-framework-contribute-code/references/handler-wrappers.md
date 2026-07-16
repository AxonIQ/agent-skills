# Message Handler Wrapper Patterns

## The unwrap() Pattern

**Core Principle:** Never use `instanceof` checks on message handlers. Always use `canHandleMessageType()` to check message compatibility and `unwrap()` to access specific wrapper types.

## Why instanceof Fails with Wrappers

Handler wrappers follow a chain pattern where each wrapper extends `WrappedMessageHandlingMember` but **does NOT implement** specific handler interfaces like `EventHandlingMember`:

```
┌─────────────────────────────────────────────┐
│  ReplayBlockingMessageHandlingMember        │  ← Extends WrappedMessageHandlingMember
│  (does NOT implement EventHandlingMember)   │     (instanceof EventHandlingMember = false)
├─────────────────────────────────────────────┤
│  SequencingPolicyEventMessageHandlingMember │  ← Extends WrappedMessageHandlingMember
│  (does NOT implement EventHandlingMember)   │     (instanceof EventHandlingMember = false)
├─────────────────────────────────────────────┤
│  MethodEventMessageHandlingMember           │  ← Implements EventHandlingMember
│  (the actual handler)                       │     (instanceof EventHandlingMember = true)
└─────────────────────────────────────────────┘
```

**Problem:** `instanceof EventHandlingMember` checks only see through to the base handler, missing all the wrapper layers that add critical behavior.

## Correct Patterns

### 1. Checking Message Type Compatibility

**❌ WRONG - instanceof breaks with wrappers:**
```java
@Override
public <T> MessageHandlingMember<T> wrapHandler(@Nonnull MessageHandlingMember<T> original) {
    // This fails if original is wrapped by a generic wrapper
    if (original instanceof EventHandlingMember) {
        return new SomeWrapper<>(original);
    }
    return original;
}
```

**✅ CORRECT - canHandleMessageType() works through wrappers:**
```java
@Override
public <T> MessageHandlingMember<T> wrapHandler(@Nonnull MessageHandlingMember<T> original) {
    // Works regardless of wrapper layers
    if (!original.canHandleMessageType(EventMessage.class)) {
        return original;
    }
    return new SomeWrapper<>(original);
}
```

### 2. Accessing Specific Handler Types

**❌ WRONG - casting loses type safety:**
```java
EventHandlingMember<T> eventHandler = (EventHandlingMember<T>) handler;
```

**✅ CORRECT - unwrap() with error handling:**
```java
EventHandlingMember<T> eventHandler = handler.unwrap(EventHandlingMember.class)
    .orElseThrow(() -> new IllegalStateException(
        "Handler declares EventMessage support but doesn't unwrap to EventHandlingMember"
    ));
```

### 3. Preserving the Wrapper Chain

**❌ WRONG - unwrapping loses wrappers:**
```java
private void processHandlers() {
    model.getUniqueHandlers(targetClass, EventMessage.class)
         .forEach(handler -> {
             // This unwraps to the base handler, losing all wrapper behavior!
             EventHandlingMember<T> eventHandler = handler.unwrap(EventHandlingMember.class)
                     .orElseThrow(...);
             registerHandler(eventHandler);  // Wrappers lost!
         });
}
```

**✅ CORRECT - preserve the full chain:**
```java
private void processHandlers() {
    model.getUniqueHandlers(targetClass, EventMessage.class)
         .forEach(handler -> {
             // Verify compatibility but don't unwrap - preserve wrapper chain
             if (!handler.canHandleMessageType(EventMessage.class)) {
                 throw new IllegalStateException(...);
             }
             registerHandler(handler);  // Full wrapper chain preserved!
         });
}

// Method signatures accept MessageHandlingMember, not EventHandlingMember
private void registerHandler(MessageHandlingMember<T> handler) {
    // Can unwrap to specific types when needed
    Optional<SequencingPolicyMember> policy = handler.unwrap(SequencingPolicyMember.class);
    // ...
}
```

## Wrapper Implementation Guidelines

**Wrappers should NOT implement specific handler interfaces:**

```java
// ✅ CORRECT - only extends WrappedMessageHandlingMember
private static class ReplayBlockingMessageHandlingMember<T>
        extends WrappedMessageHandlingMember<T> {
    // Does NOT implement EventHandlingMember
    // This keeps the wrapper generic and composable
}

// ❌ WRONG - implementing EventHandlingMember
private static class ReplayBlockingMessageHandlingMember<T>
        extends WrappedMessageHandlingMember<T>
        implements EventHandlingMember<T> {  // Don't do this!
    // This creates unnecessary coupling and complexity
}
```

**Why:** Wrappers that don't implement specific handler interfaces remain generic and composable. Code should use `unwrap()` to find specific types, not rely on `instanceof`.

## Using Attributes for Configuration

**Pattern:** Use `@HasHandlerAttributes` on annotations to translate annotation values to handler attributes. This allows wrappers to work through wrapper layers.

```java
// Annotation with @HasHandlerAttributes
@HasHandlerAttributes
@Target({ElementType.METHOD, ElementType.TYPE})
@Retention(RetentionPolicy.RUNTIME)
public @interface SequencingPolicy {
    Class<? extends org.axonframework.messaging.core.sequencing.SequencingPolicy> type();
    String[] parameters() default {};
}

// Wrapper checks attributes (works through wrappers)
@Override
public <T> MessageHandlingMember<T> wrapHandler(@Nonnull MessageHandlingMember<T> original) {
    if (!original.canHandleMessageType(EventMessage.class)) {
        return original;
    }

    // Check attributes set by @HasHandlerAttributes
    Optional<Class<? extends SequencingPolicy>> policyType =
            original.attribute(HandlerAttributes.SEQUENCING_POLICY_TYPE);

    // Fallback to class-level annotation if needed
    if (policyType.isEmpty()) {
        policyType = original.unwrap(Method.class)
                .map(Method::getDeclaringClass)
                .map(clazz -> clazz.getAnnotation(SequencingPolicy.class))
                .map(SequencingPolicy::type);
    }

    if (policyType.isEmpty()) {
        return original;
    }

    return new SequencingPolicyWrapper<>(original, policyType.get());
}
```

## Real-World Examples

**Example 1: ReplayAwareMessageHandlerWrapper**
```java
// Uses canHandleMessageType() instead of instanceof
if (!original.canHandleMessageType(EventMessage.class)) {
    return original;
}

// Checks attribute (works through wrappers)
boolean isReplayAllowed = (boolean) original
        .attribute(HandlerAttributes.ALLOW_REPLAY)
        .orElse(true);
```

**Example 2: MethodSequencingPolicyEventHandlerDefinition**
```java
// Uses canHandleMessageType() to detect event handlers
if (!original.canHandleMessageType(EventMessage.class)) {
    return original;
}

// Uses attributes (set by @HasHandlerAttributes)
Optional<Class<? extends SequencingPolicy>> policyType =
        original.attribute(HandlerAttributes.SEQUENCING_POLICY_TYPE);
```

**Example 3: AnnotatedEventHandlingComponent**
```java
// Preserves wrapper chain by not unwrapping
private void initializeHandlersBasedOnModel() {
    model.getUniqueHandlers(target.getClass(), EventMessage.class)
         .forEach(handler -> {
             // Verify compatibility but don't unwrap
             if (!handler.canHandleMessageType(EventMessage.class)) {
                 throw new IllegalStateException(...);
             }
             registerHandler(handler);  // Pass full wrapper chain
         });
}

// Accepts MessageHandlingMember to work with any wrapper
private void registerHandler(MessageHandlingMember<? super T> handler) {
    // Can unwrap to specific wrapper types when needed
    Optional<SequencingPolicyMember> policy =
        handler.unwrap(SequencingPolicyMember.class);
}
```

## Common Mistakes to Avoid

1. **Using instanceof for handler type checks** → Use `canHandleMessageType()`
2. **Unwrapping handlers unnecessarily** → Preserve the wrapper chain
3. **Making wrappers implement specific handler interfaces** → Only extend `WrappedMessageHandlingMember`
4. **Casting instead of unwrapping** → Use `unwrap()` with proper error handling
5. **Reading annotations directly** → Use attributes set by `@HasHandlerAttributes`

## Testing Handler Wrappers

```java
@Nested
class WrappedHandlerScenarios {
    @Test
    void wrapsHandlerThatIsAlreadyWrappedByGenericWrapper() {
        // given
        StubEventHandlingMember eventMember = new StubEventHandlingMember("TestEvent");
        GenericWrapper<Object> wrappedMember = new GenericWrapper<>(eventMember);

        // when
        MessageHandlingMember<Object> result = testSubject.wrapHandler(wrappedMember);

        // then - should work through the wrapper
        assertThat(result).isNotSameAs(wrappedMember);
        assertThat(result.unwrap(EventHandlingMember.class))
                .hasValue(eventMember);
    }
}

// Generic wrapper that does NOT implement EventHandlingMember
private static class GenericWrapper<T> extends WrappedMessageHandlingMember<T> {
    GenericWrapper(MessageHandlingMember<T> delegate) {
        super(delegate);
    }
}
```
