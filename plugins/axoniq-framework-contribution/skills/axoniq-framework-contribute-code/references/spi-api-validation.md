# SPI vs API Separation, Validation and Error Handling

## @Internal for SPIs

**Mark implementation interfaces:**

```java
@Internal
public interface EventStorageEngine extends DescribableComponent {
    // SPI methods - for implementers only
    CompletableFuture<AppendTransaction<?>> appendEvents(
        @Nonnull AppendCondition condition,
        @Nullable ProcessingContext context,
        @Nonnull List<TaggedEventMessage<?>> events
    );

    MessageStream<EventMessage> source(@Nonnull SourcingCondition condition);
    MessageStream<EventMessage> stream(@Nonnull StreamingCondition condition);

    interface AppendTransaction<R> {
        CompletableFuture<R> commit();
        void rollback();
        CompletableFuture<ConsistencyMarker> afterCommit(R commitResult);
    }
}
```

## Public User-Facing APIs

**Hide SPI behind clean API:**

```java
// Public API - what users interact with
public interface EventStore extends StreamableEventSource, EventBus, DescribableComponent {
    EventStoreTransaction transaction(@Nonnull ProcessingContext processingContext);
    ConsistencyMarker convert(TrackingToken trackingToken);
}

// Implementation connects API to SPI
public class StorageEngineBackedEventStore implements EventStore {
    private final EventStorageEngine eventStorageEngine;  // SPI (hidden)
    private final EventBus eventBus;

    @Override
    public EventStoreTransaction transaction(@Nonnull ProcessingContext processingContext) {
        return processingContext.computeResourceIfAbsent(
            eventStoreTransactionKey,
            () -> {
                // Delegate to SPI
                var transaction = new DefaultEventStoreTransaction(
                    eventStorageEngine,
                    processingContext,
                    this::tagEvents
                );

                // Integrate with event bus
                transaction.onAppend(events ->
                    eventBus.publish(processingContext, events).join()
                );

                return transaction;
            }
        );
    }
}
```

**Separation Strategy:**
1. **@Internal on SPI** - clear signal to users
2. **Public API hides details** - users never see SPI
3. **Implementation class connects** - delegates to SPI
4. **SPI for extensibility** - custom storage engines
5. **API for usability** - easy to use correctly

### Worked Example: EventStore API/SPI Separation

**Public API:**
```java
EventStore.transaction(context).appendEvent(event);
```

**Internal SPI:**
```java
@Internal
EventStorageEngine.appendEvents(condition, context, taggedEvents);
```

## Parameter Validation

**Every public method validates:**

```java
public SimpleCommandBus subscribe(@Nonnull QualifiedName name,
                                 @Nonnull CommandHandler commandHandler) {
    // Validate immediately with descriptive messages
    CommandHandler handler = requireNonNull(commandHandler,
                                           "Given command handler cannot be null.");
    QualifiedName validatedName = requireNonNull(name,
                                                 "The command name cannot be null.");

    var existingHandler = subscriptions.putIfAbsent(validatedName, handler);

    // Business rule validation
    if (existingHandler != null && existingHandler != handler) {
        throw new DuplicateCommandHandlerSubscriptionException(name, existingHandler, handler);
    }

    return this;
}
```

**Validation Rules:**
1. **requireNonNull everything** - even @Nonnull parameters (defense in depth)
2. **Descriptive messages** - specify parameter name and requirement
3. **Fail fast** - validate at method entry
4. **Business rules** - custom exceptions with context

## Exception Design

**Use specific exception types:**

```java
// Configuration errors - non-transient
public class AxonConfigurationException extends AxonNonTransientException {
    public AxonConfigurationException(String message) {
        super(message);
    }

    public AxonConfigurationException(String message, Throwable cause) {
        super(message, cause);
    }
}

// Specific business rule violation
public class DuplicateCommandHandlerSubscriptionException extends AxonConfigurationException {
    public DuplicateCommandHandlerSubscriptionException(QualifiedName commandName,
                                                       CommandHandler existingHandler,
                                                       CommandHandler newHandler) {
        super(String.format(
            "Cannot subscribe command handler [%s] to command [%s]. " +
            "A handler [%s] is already subscribed to this command.",
            newHandler, commandName, existingHandler
        ));
    }
}
```

**Exception Strategy:**
1. **Specific types** - enables targeted catch blocks
2. **Rich context** - include all relevant information
3. **Non-transient for config** - don't retry configuration errors
4. **Extend AxonException** - consistent exception hierarchy
