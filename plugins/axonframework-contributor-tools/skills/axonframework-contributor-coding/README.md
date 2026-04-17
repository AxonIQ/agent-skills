# Axon Framework Contributor Coding Skill

Comprehensive guide for developing Axon Framework and Axoniq Framework core infrastructure components, focusing on API design patterns, component lifecycle, and framework-specific conventions.

## Purpose

This skill is for **contributing to the Axon/Axoniq frameworks themselves**, not for using them in applications. It covers both:

- **Axon Framework** (`org.axonframework`) — Apache 2.0 open source, foundational building blocks
- **Axoniq Framework** (`io.axoniq.framework`) — Commercial (free for development), adds DLQ, PostgreSQL, distributed messaging, Spring Boot auto-configuration

Both frameworks share identical coding conventions. Axoniq Framework builds on top of Axon Framework.

## What's Covered

### 1. Layered API Design (Three-Tier Architecture)
- **Level 1 (Infrastructure)**: Low-level APIs with raw message types, explicit context
- **Level 2 (Gateways)**: High-level APIs with object payloads, convenience methods
- **Level 3 (Context-Scoped)**: Lifecycle-bound components with static factories

### 2. Design Patterns
- Interface composition pattern (DescribableComponent, EventBus)
- Registration pattern for lifecycle management
- ProcessingLifecycle hooks with ordered phases
- ResourceKey for type-safe context storage
- ComponentBuilder for dependency injection
- Type-state builders for forced choices

### 3. Thread Safety
- Immutability first
- Concurrent collections (ConcurrentHashMap, CopyOnWriteArrayList)
- Lock-free algorithms with atomic operations
- Documented thread safety guarantees

### 4. SPI vs API Separation
- @Internal annotation for SPIs
- Clean public APIs that hide implementation details
- Extensibility through well-defined SPIs

### 5. Component Configuration
- Sensible defaults when obvious
- Forced choices with phased builders when not obvious
- ComponentBuilder pattern for lazy construction
- Validation with descriptive error messages

## Usage

```bash
/axonframework-contributor-coding
```

This will load the skill and make it available during your coding session. Use it when:

- Designing new infrastructure components
- Creating layered APIs (low-level + high-level + context-scoped)
- Implementing component builders and configuration
- Designing extension points (SPI vs API)
- Ensuring thread safety and lifecycle management
- Reviewing core framework code for consistency

## Key Design Principles

### The Layered Principle

Every feature should have up to three levels:

```java
// Level 1: Infrastructure (raw concepts)
EventSink.publish(ProcessingContext, List<EventMessage>)

// Level 2: Gateway (user-friendly)
EventGateway.publish(List<Object>)
EventGateway.publish(Object...)

// Level 3: Context-scoped (specialized)
EventAppender.forContext(context).append(Object...)
```

### Sensible Defaults vs Forced Choices

**Use defaults when:**
- Common use case is obvious
- Safe fallback exists
- Trade-offs are minimal

**Force choices when:**
- Multiple valid approaches exist
- No clear "best" option
- User must understand trade-offs

## Examples in SKILL.md

The skill includes detailed examples of:

1. **EventBus/EventGateway/EventAppender** - Complete three-tier system
2. **CommandHandlingModule** - Type-state builder with forced choices
3. **EventStore API/SPI** - Separation of concerns
4. **Registration and ProcessingLifecycle** - Lifecycle management
5. **ResourceKey pattern** - Type-safe context storage

## Design Checklist

When creating a new component, verify:

- [ ] Correct abstraction level (low/high/context-scoped)
- [ ] Interface composition where appropriate
- [ ] Extends DescribableComponent
- [ ] Sensible defaults or phased builder
- [ ] ComponentBuilder for dependencies
- [ ] Thread-safe with documented guarantees
- [ ] SPI marked with @Internal
- [ ] All parameters validated
- [ ] Specific exception types with context
- [ ] Complete JavaDoc with examples

## Anti-Patterns

The skill documents common mistakes to avoid:

- ❌ Builder pattern on infrastructure components (use fluent APIs)
- ❌ Mutable message objects (prefer immutability)
- ❌ Public constructors for context-scoped components (use static factories)
- ❌ Swallowing exceptions (propagate with context)
- ❌ Synchronous blocking in async methods

## File Structure

```
.claude/skills/axonframework-core-coding/
├── SKILL.md     # Complete skill with all patterns and examples (1128 lines)
└── README.md    # This file - overview and quick reference
```

## Integration with Other Skills

### With code-review
```bash
/code-review  # Will check adherence to patterns in this skill
```

### With axon-framework-5-patterns
```bash
/axon-framework-5-patterns  # For fluent API and builder patterns
```

## Quick Pattern Lookup

### Creating a Low-Level Infrastructure Component

```java
public interface MyComponent extends DescribableComponent {
    // Primary method with all parameters
    CompletableFuture<Result> execute(@Nullable ProcessingContext context,
                                      @Nonnull List<Message> messages);

    // Minimal convenience overload
    default CompletableFuture<Result> execute(@Nullable ProcessingContext context,
                                              Message... messages) {
        return execute(context, Arrays.asList(messages));
    }
}
```

### Creating a High-Level Gateway

```java
public interface MyGateway {
    // Accept Objects, not Messages
    CompletableFuture<Result> execute(@Nullable ProcessingContext context,
                                      @Nonnull List<?> items);

    // Many convenience overloads
    default CompletableFuture<Result> execute(List<?> items) {
        return execute(null, items);
    }

    default CompletableFuture<Result> execute(Object... items) {
        return execute(null, Arrays.asList(items));
    }
}
```

### Creating a Context-Scoped Component

```java
public interface MyAppender extends DescribableComponent {
    ResourceKey<MyAppender> RESOURCE_KEY = ResourceKey.withLabel("MyAppender");

    // Static factory - singleton per context
    static MyAppender forContext(@Nonnull ProcessingContext context) {
        return context.computeResourceIfAbsent(
            RESOURCE_KEY,
            () -> new MyAppenderImpl(
                context,
                context.component(MyInfrastructure.class)
            )
        );
    }

    // Fire-and-forget
    void append(@Nonnull List<?> items);
}
```

### Creating a Type-State Builder

```java
public interface MyModule extends Module, ModuleBuilder<MyModule> {
    // Entry point forces required parameter
    static SetupPhase named(@Nonnull String name) {
        return new MyModuleImpl(name);
    }

    // Phase 1: Required setup
    interface SetupPhase {
        ConfigPhase configure();
    }

    // Phase 2: Optional configuration
    interface ConfigPhase extends ModuleBuilder<MyModule> {
        ConfigPhase withOption(@Nonnull String option);
    }
}
```

## Related Documentation

- **Code Review Checklist**: `../../code-review-checklist.md`
- **AF5 Patterns**: `../axon-framework-5-patterns/SKILL.md`
- **Reference Guide**: `/docs/reference-guide/modules/`

## Maintenance

This skill is derived from analyzing the Axon Framework 5.x codebase, specifically:
- Event publishing stack (EventSink/EventGateway/EventAppender)
- Command handling (CommandBus/CommandGateway)
- Event store architecture (EventStore/EventStorageEngine)
- Configuration system (ModuleBuilder/ComponentBuilder)
- Context and resource management (ProcessingContext/ResourceKey)

When new patterns emerge in the framework, update SKILL.md to document them.

---

**Remember:** This skill documents framework internals. For application development using Axon Framework, refer to the user documentation in `/docs/reference-guide/`.
