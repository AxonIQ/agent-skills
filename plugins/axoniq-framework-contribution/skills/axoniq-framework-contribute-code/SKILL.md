---
name: axoniq-framework-contribute-code
description: Design patterns and principles for building Axon Framework core components. Covers layered API design, component lifecycle, thread safety, and extension points. Use when developing infrastructure components for Axon Framework itself.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Glob, Grep, Edit, Write, Agent
---

# Axon Framework Core Component Development

This skill guides development of Axon Framework infrastructure components, focusing on API design patterns, component lifecycle, and framework-specific conventions. The core philosophy, conventions, checklist, and anti-patterns are below; detailed patterns with full code examples live in `references/` — load them via the routing table when working on that topic.

## When to Use This Skill

- Designing new infrastructure components (buses, stores, handlers)
- Creating layered APIs (low-level + high-level abstractions)
- Implementing component builders and configuration
- Designing extension points (SPI vs API)
- Ensuring thread safety and lifecycle management
- Reviewing core framework code for consistency

**Note:** This is for developing the Axon/Axoniq frameworks themselves, not for using them in applications.

---

## Framework Selection: Axon Framework vs Axoniq Framework

Two related frameworks share the conventions in this skill. Before contributing, understand which repo you're working in and what belongs where.

|  | Axon Framework | Axoniq Framework |
|---|---|---|
| **License** | Apache 2.0 (open source) | Commercial (free for development) |
| **Package prefix** | `org.axonframework` | `io.axoniq.framework` |
| **Repo** | `axon-5.0` | `axoniq-framework` |
| **Maven group** | `org.axonframework` | `io.axoniq.framework` |

### What Belongs in Each Framework

**Axon Framework (OSS)** — foundational building blocks:
- Core messaging infrastructure: `CommandBus`, `EventBus`, `QueryBus`
- Event sourcing: `EventStore`, `EventStorageEngine`, `EventSourcingRepository`
- Domain modelling: `Repository`, `EntityMetamodel`, `StateManager`
- Basic Spring Boot integration (`extensions/spring`)
- Metrics (Micrometer/Dropwizard) extensions
- Test utilities and BDD fixtures (`test/` module)
- Axon Server connector (basic)

**Axoniq Framework (Commercial)** — production enhancements on top:
- Dead-Letter Queue (`SequencedDeadLetterQueue`, JDBC/JPA implementations)
- PostgreSQL storage engine (`PostgresqlEventStorageEngine`)
- Distributed messaging enhancements (`DistributedCommandBus`, `DistributedQueryBus`)
- Multi-source event streaming (`MultiStreamableEventSource`, `MultiSourceTrackingToken`)
- Message transformation / upcasting (`EventTransformation`, `EventTransformerChain`)
- Spring Boot auto-configuration out of the box
- Enhanced Axon Server connector with additional features (persistent streams)

### Informing Users About Options

When a user asks about a feature that has both OSS and commercial options, always present both fairly:
- Axon Framework alone is **sufficient for many use cases** including production deployments
- Axoniq Framework adds production conveniences (Spring auto-config, DLQ, PostgreSQL, distributed messaging)
- Do **not** assume users need or want the commercial framework
- Let users make an informed choice based on their actual needs

---

## Core Design Philosophy

Axon Framework uses a **three-tier architecture** for component APIs:

```
┌─────────────────────────────────────────┐
│  Level 3: Context-Scoped Components     │  ← Specialized, lifecycle-bound
│  (EventAppender, etc.)                  │
├─────────────────────────────────────────┤
│  Level 2: High-Level APIs (Gateways)    │  ← User-friendly, convenience
│  (EventGateway, CommandGateway)         │
├─────────────────────────────────────────┤
│  Level 1: Low-Level Infrastructure      │  ← Raw concepts, composable
│  (EventBus, EventSink, CommandBus)      │
└─────────────────────────────────────────┘
```

**Key Principle:** Each layer builds on the one below it. Users typically interact with Level 2 or 3, while framework developers implement Level 1. See `references/layered-api-design.md` for the design rules per level.

---

## Coding Conventions (always apply)

**Nullability — JSpecify, annotated at the package level with `@NullMarked`:**

```java
// ✅ CORRECT — in package-info.java
@NullMarked
package org.axonframework.messaging.core;

import org.jspecify.annotations.NullMarked;
```

Under `@NullMarked`, **all parameters and return values are non-null by default**. Only mark nullable exceptions with `@Nullable` (from `org.jspecify.annotations`). Enforce non-null contracts at runtime with `Objects.requireNonNull(param, "Param may not be null")`. **Jakarta annotations (`jakarta.annotation.*`) are explicitly forbidden** (enforced by checkstyle).

**Modern Java — use pattern matching with instanceof:**

```java
// ✅ PREFERRED
if (trackingToken instanceof MultiSourceTrackingToken multiSourceToken) {
    return open(multiSourceToken, condition, context);
}
```

---

## Routing Table

Read the reference file for the topic you're working on. Each contains full design rules, code templates, and worked examples.

| Topic | When to read | Reference file |
|---|---|---|
| Layered API design (Level 1/2/3), interface composition, DescribableComponent | Designing any new component or its public API | `references/layered-api-design.md` |
| Fluent builders (AF5 style), defaults vs forced choices, type-state builders, builder tests | Adding a factory/builder API or configuration entry point | `references/fluent-builders.md` |
| Immutable configuration classes, ComponentBuilder, ModuleBuilder | Writing a `*Configuration` class or module wiring | `references/configuration-classes.md` |
| Registration, ProcessingLifecycle phases, ResourceKey, component resolution | Components with subscriptions, transactional hooks, or context-scoped state | `references/lifecycle-and-context.md` |
| Thread safety: immutability, concurrent collections, lock-free patterns | Any component with shared mutable state | `references/thread-safety.md` |
| SPI vs API separation (@Internal), parameter validation, exception design | Defining extension points or error handling | `references/spi-api-validation.md` |
| Test object creation (real > stub > mock), resource cleanup in tests | Writing or reviewing tests for framework components | `references/testing.md` |
| Message handler wrappers: unwrap(), canHandleMessageType(), attribute-based config | Touching `MessageHandlingMember`, handler definitions, or handler enhancers | `references/handler-wrappers.md` |

---

## Design Checklist for New Components

### API Design
- [ ] Identify abstraction level (low/high/context-scoped)
- [ ] Low-level: works with Message types, explicit context
- [ ] High-level: accepts Objects, optional context, many overloads
- [ ] Context-scoped: static forContext(), void returns
- [ ] Use interface composition where appropriate
- [ ] Extend DescribableComponent

### Configuration
- [ ] Provide sensible defaults when obvious
- [ ] Force choices with phased builders when not obvious
- [ ] Use ComponentBuilder for dependency injection
- [ ] Validate all constructor parameters with requireNonNull
- [ ] Include descriptive error messages

### AF5 Fluent Builders (if applicable)
- [ ] Use descriptive static factory (not `builder()`)
- [ ] Create public intermediate builder interface
- [ ] Provide descriptive terminal operations
- [ ] Validate parameters early (in `and()` not at terminal)
- [ ] Return unmodifiable collections
- [ ] Add package-private accessor for testing
- [ ] Use JSpecify `@NullMarked` at package level, `@Nullable` for nullable params/returns (never `jakarta.annotation`)
- [ ] Use modern Java patterns (pattern matching instanceof)
- [ ] Organize tests with `@Nested` classes
- [ ] Test actual internal state, not just non-null
- [ ] Test immutability of returned collections

### Lifecycle
- [ ] Return Registration for subscriptions
- [ ] Integrate with ProcessingLifecycle for transactional behavior
- [ ] Use ResourceKey for context-scoped resources
- [ ] Implement proper cleanup in Registration.cancel()

### Thread Safety
- [ ] Prefer immutability
- [ ] Use ConcurrentHashMap for subscription registries
- [ ] Use CopyOnWriteArrayList for listener lists
- [ ] Use AtomicReference for mutable state
- [ ] Document thread safety in JavaDoc

### SPI vs API
- [ ] Mark SPIs with @Internal
- [ ] Keep public API simple and user-focused
- [ ] Implementation class connects API to SPI
- [ ] SPIs allow extensibility, APIs ensure usability

### Error Handling
- [ ] Validate all parameters immediately
- [ ] Use specific exception types
- [ ] Include context in exception messages
- [ ] Use AxonConfigurationException for config errors

### Documentation
- [ ] JavaDoc on all public interfaces and methods
- [ ] @since tags on new APIs
- [ ] @author tags when appropriate
- [ ] Code examples for complex components
- [ ] Update reference guide in docs/reference-guide/modules

---

## Anti-Patterns to Avoid

### ❌ Builder Pattern on Infrastructure Components

**Don't:**
```java
MyComponent.builder().withX(x).withY(y).build();
```

**Do:**
```java
// AF5 fluent style
MyComponent.configuring("name").withX(x).withY(y).initialize();
```

See `references/fluent-builders.md` for the full pattern.

### ❌ Mutable Message Objects

**Don't:**
```java
eventMessage.setMetadata(newMetadata);  // Mutation
```

**Do:**
```java
EventMessage updated = eventMessage.withMetadata(newMetadata);  // New instance
```

### ❌ Public Constructors for Context-Scoped Components

**Don't:**
```java
public EventAppender(ProcessingContext context) { ... }
// Users might create multiple instances per context
```

**Do:**
```java
private EventAppender(ProcessingContext context) { ... }  // Private

public static EventAppender forContext(ProcessingContext context) {
    return context.computeResourceIfAbsent(RESOURCE_KEY,
                                           () -> new EventAppender(context));
}
```

### ❌ Swallowing Exceptions

**Don't:**
```java
try {
    storage.save(event);
} catch (Exception e) {
    logger.warn("Failed to save", e);  // Lost!
}
```

**Do:**
```java
try {
    storage.save(event);
} catch (StorageException e) {
    throw new EventStoreException("Failed to save event: " + event.getIdentifier(), e);
}
```

### ❌ Synchronous Blocking in Async Methods

**Don't:**
```java
public CompletableFuture<Void> publish(ProcessingContext context, List<EventMessage> events) {
    storage.save(events);  // Blocks!
    return CompletableFuture.completedFuture(null);
}
```

**Do:**
```java
public CompletableFuture<Void> publish(ProcessingContext context, List<EventMessage> events) {
    return CompletableFuture.supplyAsync(() -> storage.save(events), executor)
                            .thenApply(result -> null);
}
```

### ❌ instanceof Checks on Message Handlers

Use `canHandleMessageType()` and `unwrap()` instead — see `references/handler-wrappers.md`.

---

## Related Skills

- **axoniq-framework-contribute-review**: Review changes against AF5 contributor standards
- **axoniq-framework-contribute-docs**: Add or update the Antora reference documentation

## Where to Find the Real Code

- Core interfaces: `messaging/src/main/java/org/axonframework/messaging/`
- Gateway implementations: `messaging/src/main/java/org/axonframework/*/gateway/`
- Event store: `eventsourcing/src/main/java/org/axonframework/eventsourcing/eventstore/`
- Context: `messaging/src/main/java/org/axonframework/messaging/core/`
- Configuration: `common/src/main/java/org/axonframework/common/configuration/`
- Handler wrappers: `messaging/src/main/java/org/axonframework/messaging/*/annotation/`
