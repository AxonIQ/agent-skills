# Layered API Design

Axon Framework uses a **three-tier architecture** for component APIs. Each layer builds on the one below it: users typically interact with Level 2 or 3, while framework developers implement Level 1.

## Level 1: Low-Level Infrastructure APIs

**Characteristics:**
- Work with raw message types (EventMessage, CommandMessage)
- Require explicit ProcessingContext parameter
- Minimal convenience methods
- Composable through interface inheritance
- Return CompletableFuture for async operations

**Example - EventSink (low-level):**
```java
public interface EventSink extends DescribableComponent {
    // Primary method - full control
    CompletableFuture<Void> publish(@Nullable ProcessingContext context,
                                    @Nonnull List<EventMessage> events);

    // Single convenience method
    default CompletableFuture<Void> publish(@Nullable ProcessingContext context,
                                            EventMessage... events) {
        return publish(context, Arrays.asList(events));
    }
}
```

**Design Rules:**
1. **One primary method** with all parameters
2. **Minimal defaults** - only obvious convenience variants
3. **Explicit nullability** - @Nullable for optional context
4. **Message types** - work with EventMessage, not Object
5. **Async by default** - return CompletableFuture

## Level 2: High-Level Gateway APIs

**Characteristics:**
- Accept Object payloads (auto-conversion to messages)
- Multiple convenience overloads
- Optional ProcessingContext with null default
- Type-safe result handling
- Delegate to Level 1 APIs

**Example - EventGateway (high-level):**
```java
public interface EventGateway {
    // Primary method
    CompletableFuture<Void> publish(@Nullable ProcessingContext context,
                                    @Nonnull List<?> events);

    // Convenience overloads
    default CompletableFuture<Void> publish(@Nullable ProcessingContext context,
                                            Object... events) {
        return publish(context, Arrays.asList(events));
    }

    default CompletableFuture<Void> publish(@Nonnull List<?> events) {
        return publish(null, events);
    }

    default CompletableFuture<Void> publish(Object... events) {
        return publish(null, events);
    }
}
```

**Implementation Pattern:**
```java
public class DefaultEventGateway implements EventGateway {
    private final EventSink eventSink;  // Delegate to Level 1
    private final MessageTypeResolver messageTypeResolver;

    public DefaultEventGateway(@Nonnull EventSink eventSink,
                               @Nonnull MessageTypeResolver messageTypeResolver) {
        this.eventSink = requireNonNull(eventSink, "EventSink may not be null");
        this.messageTypeResolver = requireNonNull(messageTypeResolver,
                                                  "MessageTypeResolver may not be null");
    }

    @Override
    public CompletableFuture<Void> publish(@Nullable ProcessingContext context,
                                           @Nonnull List<?> events) {
        // Convert Objects → EventMessages
        List<EventMessage> eventMessages =
            events.stream()
                  .map(event -> EventPublishingUtils.asEventMessage(event, messageTypeResolver))
                  .collect(Collectors.toList());

        // Delegate to low-level API
        return eventMessages.isEmpty()
                ? FutureUtils.emptyCompletedFuture()
                : eventSink.publish(context, eventMessages);
    }
}
```

**Design Rules:**
1. **Accept Object payloads** - user shouldn't create messages
2. **Many convenience methods** - cover common use cases
3. **Delegate to Level 1** - gateways wrap infrastructure APIs
4. **Handle edge cases** - empty lists, null contexts, etc.
5. **Type conversion** - use utility classes for message creation

## Level 3: Context-Scoped Components

**Characteristics:**
- Bound to ProcessingContext lifecycle
- Static factory methods (no public constructors)
- Singleton per context (computeResourceIfAbsent)
- Fire-and-forget semantics (void return)
- Automatic lifecycle management

**Example - EventAppender (context-scoped):**
```java
public interface EventAppender extends DescribableComponent {
    // Type-safe resource key
    Context.ResourceKey<ProcessingContextEventAppender> RESOURCE_KEY =
        Context.ResourceKey.withLabel("EventAppender");

    // Static factory - context-scoped singleton
    static EventAppender forContext(@Nonnull ProcessingContext context) {
        requireNonNull(context, "ProcessingContext may not be null");
        return context.computeResourceIfAbsent(
            RESOURCE_KEY,
            () -> new ProcessingContextEventAppender(
                context,
                context.component(EventSink.class),
                context.component(MessageTypeResolver.class)
            )
        );
    }

    // Fire-and-forget API
    void append(@Nonnull List<?> events);

    default void append(Object... events) {
        append(Arrays.asList(events));
    }
}
```

**Design Rules:**
1. **Static factory only** - forContext() pattern
2. **ResourceKey for singleton** - one instance per context
3. **Component resolution** - context.component() for dependencies
4. **Void return type** - events committed with context lifecycle
5. **No manual lifecycle** - context manages cleanup

## Interface Composition Pattern

### Small, Focused Interfaces

Break functionality into composable interfaces:

```java
// Marker interface - pure composition
public interface EventBus extends SubscribableEventSource,
                                  EventSink,
                                  DescribableComponent {
    // Empty - behavior comes from parent interfaces
}
```

**When to use:**
- Component combines multiple concerns naturally
- Each parent interface has single responsibility
- No conflicting method signatures
- All combinations are valid

### Interface Hierarchy Design

```java
// Base publishing interface
public interface EventSink extends DescribableComponent {
    CompletableFuture<Void> publish(@Nullable ProcessingContext context,
                                    @Nonnull List<EventMessage> events);
}

// Subscription capability
public interface SubscribableEventSource {
    Registration subscribe(@Nonnull BiFunction<List<? extends EventMessage>,
                                               ProcessingContext,
                                               CompletableFuture<?>> eventsBatchConsumer);
}

// Combined interface
public interface EventBus extends SubscribableEventSource, EventSink, DescribableComponent {
    // Inherits publish() from EventSink
    // Inherits subscribe() from SubscribableEventSource
    // Inherits describeTo() from DescribableComponent
}
```

**Design Rules:**
1. **Single responsibility per interface** - one verb each
2. **DescribableComponent everywhere** - all infrastructure components
3. **Marker interfaces OK** - when pure composition suffices
4. **Avoid diamond problems** - careful with default methods

## DescribableComponent Pattern

Every infrastructure component implements DescribableComponent for introspection:

```java
@FunctionalInterface
public interface DescribableComponent {
    void describeTo(@Nonnull ComponentDescriptor descriptor);
}

// Implementation
public class SimpleEventBus implements EventBus {
    private final Context.ResourceKey<List<EventMessage>> eventsKey;
    private final EventSubscribers eventSubscribers;

    @Override
    public void describeTo(@Nonnull ComponentDescriptor descriptor) {
        descriptor.describeProperty("eventsKey", eventsKey);
        descriptor.describeProperty("eventSubscribers", eventSubscribers);
        descriptor.describeProperty("subscriberCount", eventSubscribers.size());
    }
}
```

**Benefits:**
1. **Diagnostics** - debugging and monitoring
2. **Consistency** - all components describable
3. **Tooling** - enables management UIs
4. **Testing** - verify configuration

## Worked Example: Three-Tier Event Publishing

**Tier 1 - Infrastructure:**
```java
EventSink.publish(ProcessingContext, List<EventMessage>)
```

**Tier 2 - Gateway:**
```java
EventGateway.publish(ProcessingContext, List<Object>)
EventGateway.publish(List<Object>)
EventGateway.publish(Object...)
```

**Tier 3 - Context-Scoped:**
```java
EventAppender.forContext(context).append(Object...)
```
