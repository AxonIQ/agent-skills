# Thread Safety Patterns

## Immutability First

**Prefer immutable designs:**

```java
// Immutable message
public interface EventMessage extends Message {
    // All methods return values, no mutation
    String getIdentifier();
    Instant getTimestamp();

    // Derivation returns new instance
    EventMessage withMetadata(Metadata metadata);
    EventMessage andMetadata(Metadata metadata);
}

// Immutable context
public interface Context {
    // Returns new instance, doesn't mutate
    <T> Context withResource(@Nonnull ResourceKey<T> key, @Nonnull T resource);
}
```

## Concurrent Collections

**For mutable shared state:**

```java
public class SimpleCommandBus implements CommandBus {
    // Thread-safe subscription map
    private final ConcurrentMap<QualifiedName, CommandHandler> subscriptions =
        new ConcurrentHashMap<>();

    @Override
    public SimpleCommandBus subscribe(@Nonnull QualifiedName name,
                                     @Nonnull CommandHandler commandHandler) {
        CommandHandler handler = requireNonNull(commandHandler,
                                               "Given command handler cannot be null.");

        // Atomic check-and-set
        var existingHandler = subscriptions.putIfAbsent(
            requireNonNull(name, "The command name cannot be null."),
            handler
        );

        if (existingHandler != null && existingHandler != handler) {
            throw new DuplicateCommandHandlerSubscriptionException(name, existingHandler, handler);
        }
        return this;
    }
}
```

**Thread-Safe Collections:**
1. **ConcurrentHashMap** - for subscription maps, handler registries
2. **CopyOnWriteArrayList** - for listener lists (read-heavy)
3. **AtomicReference** - for single mutable values
4. **Atomic operations** - putIfAbsent, computeIfAbsent

## Synchronization Strategies

**When to synchronize:**

```java
public class DefaultEventStoreTransaction implements EventStoreTransaction {
    // Lock-free for reads
    private final AtomicReference<ConsistencyMarker> consistencyMarker =
        new AtomicReference<>();

    // Copy-on-write for appends
    private final CopyOnWriteArrayList<EventMessage> appendedEvents =
        new CopyOnWriteArrayList<>();

    @Override
    public void appendEvent(@Nonnull EventMessage event) {
        // Thread-safe add
        appendedEvents.add(requireNonNull(event, "Event may not be null"));
    }

    @Override
    public CompletableFuture<Void> commit() {
        // Atomic swap
        consistencyMarker.updateAndGet(current -> {
            // Compute new marker
            return newMarker;
        });

        return storageEngine.appendEvents(condition, context, taggedEvents)
                            .thenCompose(AppendTransaction::commit);
    }
}
```

**Synchronization Rules:**
1. **Avoid synchronized blocks** - use concurrent collections
2. **Lock-free when possible** - atomic operations
3. **Immutable by default** - mutation only when necessary
4. **Document thread safety** - javadoc @ThreadSafe annotation
