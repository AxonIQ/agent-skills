# Component Lifecycle, Context and Resource Management

## Registration Pattern

**Simple lifecycle management:**

```java
@FunctionalInterface
public interface Registration {
    boolean cancel();
}

// Usage
public interface SubscribableEventSource {
    Registration subscribe(@Nonnull BiFunction<List<? extends EventMessage>,
                                               ProcessingContext,
                                               CompletableFuture<?>> eventsBatchConsumer);
}

// Implementation
public class SimpleEventBus implements EventBus {
    private final EventSubscribers eventSubscribers = new EventSubscribers();

    @Override
    public Registration subscribe(@Nonnull BiFunction<List<? extends EventMessage>,
                                                      ProcessingContext,
                                                      CompletableFuture<?>> eventsBatchConsumer) {
        return eventSubscribers.subscribe(requireNonNull(eventsBatchConsumer,
                                                        "Event consumer may not be null"));
    }
}
```

**Pattern Benefits:**
1. **Explicit cleanup** - caller controls deregistration
2. **Functional interface** - can use lambdas
3. **Idempotent cancel()** - safe to call multiple times
4. **Boolean return** - indicates if actually cancelled

## ProcessingLifecycle Hooks

**Phase-based lifecycle with ordering:**

```java
public interface ProcessingLifecycle {
    // Generic phase registration
    ProcessingLifecycle on(@Nonnull Phase phase,
                          @Nonnull Function<ProcessingContext, CompletableFuture<?>> action);

    // Convenience methods for default phases
    default ProcessingLifecycle onPrepareCommit(
            @Nonnull Function<ProcessingContext, CompletableFuture<?>> action) {
        return on(DefaultPhases.PREPARE_COMMIT, action);
    }

    default ProcessingLifecycle onCommit(
            @Nonnull Function<ProcessingContext, CompletableFuture<?>> action) {
        return on(DefaultPhases.COMMIT, action);
    }

    default ProcessingLifecycle onAfterCommit(
            @Nonnull Function<ProcessingContext, CompletableFuture<?>> action) {
        return on(DefaultPhases.AFTER_COMMIT, action);
    }

    // Error handling
    ProcessingLifecycle onError(@Nonnull ErrorHandler action);

    // Completion (success or failure)
    ProcessingLifecycle whenComplete(@Nonnull Consumer<ProcessingContext> action);

    // Guaranteed execution
    default ProcessingLifecycle doFinally(@Nonnull Consumer<ProcessingContext> action) {
        onError((c, p, e) -> action.accept(c));
        whenComplete(action);
        return this;
    }

    enum DefaultPhases implements Phase {
        PRE_INVOCATION(-10000),
        INVOCATION(0),
        POST_INVOCATION(10000),
        PREPARE_COMMIT(20000),
        COMMIT(30000),
        AFTER_COMMIT(40000);

        private final int order;

        DefaultPhases(int order) {
            this.order = order;
        }

        @Override
        public int order() {
            return order;
        }
    }
}
```

**Usage:**
```java
processingContext
    .onPrepareCommit(ctx -> {
        // Validate before commit
        return CompletableFuture.completedFuture(null);
    })
    .onCommit(ctx -> {
        // Persist changes
        return storage.save(ctx.resources());
    })
    .onAfterCommit(ctx -> {
        // Publish events
        return eventBus.publish(ctx, events);
    })
    .doFinally(ctx -> {
        // Always cleanup
        ctx.close();
    });
```

**Design Rules:**
1. **Ordered phases** - integer-based for custom phases
2. **Fluent API** - all methods return this
3. **Async support** - CompletableFuture return values
4. **Convenience + power** - defaults for common, generic for custom
5. **Guaranteed cleanup** - doFinally() for both success and error

## ResourceKey Pattern

**Type-safe context storage:**

```java
public interface Context {
    // Immutable resource management
    <T> Context withResource(@Nonnull ResourceKey<T> key, @Nonnull T resource);
    <T> T resource(@Nonnull ResourceKey<T> key);

    // Type-safe key with identity-based equality
    final class ResourceKey<T> {
        private final String identity;
        private final String label;

        private ResourceKey(@Nullable String label) {
            this.label = label;
            this.identity = "ResourceKey@" + Integer.toHexString(System.identityHashCode(this));
        }

        public static <T> ResourceKey<T> withLabel(@Nullable String label) {
            return new ResourceKey<>(label);
        }

        @Override
        public boolean equals(Object o) {
            return this == o;  // Identity-based
        }

        @Override
        public int hashCode() {
            return System.identityHashCode(this);
        }
    }
}
```

**Usage:**
```java
public class EventAppender {
    // Declare key as static final
    private static final Context.ResourceKey<List<EventMessage>> EVENTS_KEY =
        Context.ResourceKey.withLabel("PendingEvents");

    public void append(ProcessingContext context, EventMessage event) {
        List<EventMessage> events = context.computeResourceIfAbsent(
            EVENTS_KEY,
            () -> new ArrayList<>()
        );
        events.add(event);
    }
}
```

**Design Rules:**
1. **Identity-based equality** - each key instance is unique
2. **Generic type safety** - compiler enforces correct types
3. **Immutable Context** - withResource() returns new instance
4. **Mutable ProcessingContext** - putResource() mutates in place
5. **computeResourceIfAbsent** - for singleton per context

## Component Resolution

**Dependency injection from context:**

```java
public interface ApplicationContext {
    <C> C component(@Nonnull Class<C> componentType);
    <C> C component(@Nonnull Class<C> componentType, @Nonnull String componentName);
}

// Usage in static factory
public static EventAppender forContext(@Nonnull ProcessingContext context) {
    return context.computeResourceIfAbsent(
        RESOURCE_KEY,
        () -> new ProcessingContextEventAppender(
            context,
            context.component(EventSink.class),           // Resolve by type
            context.component(MessageTypeResolver.class)  // Resolve by type
        )
    );
}
```
