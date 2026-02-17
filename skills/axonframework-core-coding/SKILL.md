---
name: axonframework-core-coding
description: Design patterns and principles for building Axon Framework core components. Covers layered API design, component lifecycle, thread safety, and extension points. Use when developing infrastructure components for Axon Framework itself.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Glob, Grep, Edit, Write, Task
---

# Axon Framework Core Component Development

This skill guides development of Axon Framework infrastructure components, focusing on API design patterns, component lifecycle, and framework-specific conventions.

## When to Use This Skill

- Designing new infrastructure components (buses, stores, handlers)
- Creating layered APIs (low-level + high-level abstractions)
- Implementing component builders and configuration
- Designing extension points (SPI vs API)
- Ensuring thread safety and lifecycle management
- Reviewing core framework code for consistency

**Note:** This is for developing Axon Framework itself, not for using it in applications.

## Core Design Philosophy

### The Layered API Principle

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

**Key Principle:** Each layer builds on the one below it. Users typically interact with Level 2 or 3, while framework developers implement Level 1.

---

## 1. Layered API Design

### Level 1: Low-Level Infrastructure APIs

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

### Level 2: High-Level Gateway APIs

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

### Level 3: Context-Scoped Components

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

---

## 2. Interface Composition Pattern

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

---

## 3. Default Configuration vs Forced Choices

### Sensible Defaults Pattern

**When to provide defaults:**
- Common use case is obvious
- Safe fallback exists
- Trade-offs are minimal

**Example - SimpleEventBus:**
```java
public class SimpleEventBus implements EventBus {
    // Zero-arg constructor - works immediately
    public SimpleEventBus() {
        super();
    }

    @Override
    public CompletableFuture<Void> publish(@Nullable ProcessingContext context,
                                           @Nonnull List<EventMessage> events) {
        if (context == null) {
            // Sensible default: immediate publication
            eventSubscribers.notifySubscribers(events, context);
            return FutureUtils.emptyCompletedFuture();
        }

        // Enhanced mode: defer until context commits
        registerEventPublishingHooks(context, events);
        return FutureUtils.emptyCompletedFuture();
    }
}
```

**Pattern Benefits:**
1. **Progressive disclosure** - basic mode first, advanced later
2. **Zero configuration** - works out of the box
3. **Context awareness** - behavior adapts to presence of context
4. **Backward compatible** - new features don't break existing usage

### Forced Choice Pattern

**When to force choices:**
- Multiple valid approaches exist
- No clear "best" option
- Configuration affects behavior significantly
- User must understand trade-offs

**Example - Type-State Builder:**
```java
public interface CommandHandlingModule extends Module, ModuleBuilder<CommandHandlingModule> {

    // Entry point - forces module name
    static SetupPhase named(@Nonnull String moduleName) {
        return new SimpleCommandHandlingModule(moduleName);
    }

    // Phase 1: Setup (cannot skip)
    interface SetupPhase {
        CommandHandlerPhase commandHandlers();

        default CommandHandlerPhase commandHandlers(
                @Nonnull Consumer<CommandHandlerPhase> configurationLambda) {
            CommandHandlerPhase phase = commandHandlers();
            requireNonNull(configurationLambda,
                          "The command handler configuration lambda cannot be null.")
                    .accept(phase);
            return phase;
        }
    }

    // Phase 2: Handler Registration (type-safe)
    interface CommandHandlerPhase extends ModuleBuilder<CommandHandlingModule> {
        CommandHandlerPhase commandHandler(
                @Nonnull QualifiedName commandName,
                @Nonnull ComponentBuilder<CommandHandler> commandHandlerBuilder);

        CommandHandlerPhase commandHandlingComponent(
                @Nonnull ComponentBuilder<CommandHandlingComponent> handlingComponentBuilder);
    }
}
```

**Usage:**
```java
CommandHandlingModule.named("checkout-module")  // Must provide name (no default)
    .commandHandlers()                           // Explicit phase entry
    .commandHandler(...)                         // Add handlers
    .commandHandler(...);
```

**Design Rules:**
1. **Type-state pattern** - each phase is different interface
2. **Linear flow** - can only move forward
3. **Descriptive factory names** - not just builder()
4. **Lambda shortcuts** - optional inline configuration
5. **Compile-time safety** - impossible to skip required steps

---

## 3a. AF5 Fluent Builder Pattern

### The AF5 Style vs AF4 Style

**AF4 used traditional builder pattern** (avoid this now):
```java
// ❌ AF4 style - don't use anymore
MyComponent.builder()
    .addItem("name1", item1)
    .addItem("name2", item2)
    .build();
```

**AF5 uses fluent APIs with descriptive methods**:
```java
// ✅ AF5 style - preferred
MyComponent.combining("name1", item1)
    .and("name2", item2)
    .comparingUsing(comparator);

// Or with defaults
MyComponent.combining("name1", item1)
    .and("name2", item2)
    .withDefaults();
```

### Implementation Structure

**Complete fluent builder template:**

```java
/**
 * Description of what this component does.
 * <p>
 * Example usage:
 * <pre>{@code
 * MyComponent component = MyComponent
 *     .combining("item1", source1)
 *     .and("item2", source2)
 *     .comparingUsing(customComparator);
 * }</pre>
 *
 * @author Your Name
 * @since 5.1.0
 */
public class MyComponent {

    private final Map<String, Item> items;
    private final Comparator<Item> comparator;

    /**
     * Creates a new component by combining multiple items.
     * This is the starting point for the fluent builder API.
     *
     * @param itemName A unique name identifying the first item.
     * @param item The first item to include.
     * @return An ItemCollector for adding more items and configuring the component.
     */
    public static ItemCollector combining(@Nonnull String itemName, @Nonnull Item item) {
        return new ItemCollectorImpl(itemName, item);
    }

    /**
     * Constructs the component from the collected items and configuration.
     *
     * @param items The map of items, keyed by their unique names.
     * @param comparator The comparator to use for ordering items.
     */
    protected MyComponent(Map<String, Item> items, Comparator<Item> comparator) {
        this.items = Collections.unmodifiableMap(new LinkedHashMap<>(items));
        this.comparator = comparator;
    }

    /**
     * Returns the map of items managed by this component.
     * Package-private for testing purposes.
     *
     * @return An unmodifiable map of item names to their corresponding items.
     */
    Map<String, Item> items() {
        return items;
    }

    // ... component implementation methods ...

    /**
     * Intermediate builder for collecting items before creating the component.
     * Allows adding multiple items and provides terminal operations for creating the final instance.
     */
    public interface ItemCollector {

        /**
         * Adds another item to the collection.
         *
         * @param itemName A unique name identifying the item.
         * @param item The item to add.
         * @return This ItemCollector for fluent chaining.
         * @throws IllegalArgumentException if the itemName is already used.
         */
        ItemCollector and(@Nonnull String itemName, @Nonnull Item item);

        /**
         * Creates the component using default comparison (natural ordering).
         *
         * @return A configured component instance.
         */
        MyComponent withDefaults();

        /**
         * Creates the component using a custom comparator.
         *
         * @param comparator The comparator to use when ordering items.
         * @return A configured component instance.
         */
        MyComponent comparingUsing(@Nonnull Comparator<Item> comparator);
    }

    /**
     * Implementation of the ItemCollector that collects items and creates the final instance.
     */
    private static class ItemCollectorImpl implements ItemCollector {

        private final Map<String, Item> itemMap;

        ItemCollectorImpl(String initialName, Item initialItem) {
            this.itemMap = new LinkedHashMap<>();
            addItem(initialName, initialItem);
        }

        @Override
        public ItemCollector and(@Nonnull String itemName, @Nonnull Item item) {
            addItem(itemName, item);
            return this;
        }

        private void addItem(String name, Item item) {
            Objects.requireNonNull(name, "itemName must not be null");
            Objects.requireNonNull(item, "item must not be null");
            Assert.isFalse(itemMap.containsKey(name),
                          () -> "Item name '" + name + "' is already used. Item names must be unique.");
            itemMap.put(name, item);
        }

        @Override
        public MyComponent withDefaults() {
            return comparingUsing(Comparator.naturalOrder());
        }

        @Override
        public MyComponent comparingUsing(@Nonnull Comparator<Item> comparator) {
            Objects.requireNonNull(comparator, "comparator must not be null");
            return new MyComponent(itemMap, comparator);
        }
    }
}
```

### Key Design Elements

1. **Descriptive static factory** - `combining()` not `builder()`
2. **Public intermediate interface** - `ItemCollector` for discoverability
3. **Private implementation** - Hide implementation details
4. **Early validation** - Validate in `and()`, not at terminal operation
5. **Unmodifiable collections** - `Collections.unmodifiableMap(new LinkedHashMap<>())`
6. **Package-private accessor** - For test validation
7. **Multiple terminal operations** - `withDefaults()`, `comparingUsing()`

### Testing Fluent Builders

**Use @Nested classes to organize tests:**

```java
class MyComponentTest {

    // Behavioral tests at top level
    @Test
    void shouldProcessItemsCorrectly() {
        MyComponent component = MyComponent.combining("item1", item1)
                                          .and("item2", item2)
                                          .withDefaults();
        // Test behavior
    }

    // Builder API tests in nested class
    @Nested
    class BuilderApiTest {

        @Test
        void combiningWithDefaults() {
            Item item = mock(Item.class);

            MyComponent result = MyComponent
                    .combining("item1", item)
                    .withDefaults();

            // Validate using package-private accessor
            assertNotNull(result);
            assertEquals(1, result.items().size());
            assertEquals(item, result.items().get("item1"));
        }

        @Test
        void combiningRejectsDuplicateNames() {
            assertThrows(IllegalArgumentException.class, () ->
                    MyComponent.combining("item1", item1)
                               .and("item1", item2) // duplicate
                               .withDefaults()
            );
        }

        @Test
        void combiningRejectsNullName() {
            //noinspection DataFlowIssue  // Intentionally passing null
            assertThrows(NullPointerException.class, () ->
                    MyComponent.combining(null, item)
            );
        }

        @Test
        void itemsReturnsUnmodifiableMap() {
            MyComponent result = MyComponent
                    .combining("item1", item)
                    .withDefaults();

            assertThrows(UnsupportedOperationException.class, () ->
                    result.items().put("new", item2)
            );
        }
    }
}
```

### Test Validation Rules

1. **Validate actual state** - Don't just check non-null
2. **Test immutability** - Verify collections are unmodifiable
3. **Test null rejection** - Use `//noinspection DataFlowIssue`
4. **Test duplicate rejection** - Verify error messages
5. **Use package-private accessors** - Enable proper validation

### Modern Java Patterns

**Use pattern matching with instanceof:**

```java
// ✅ PREFERRED: Modern pattern matching
if (trackingToken instanceof MultiSourceTrackingToken multiSourceToken) {
    return open(multiSourceToken, condition, context);
}

// ❌ AVOID: Old-style casting
if (trackingToken instanceof MultiSourceTrackingToken) {
    MultiSourceTrackingToken multiSourceToken = (MultiSourceTrackingToken) trackingToken;
    return open(multiSourceToken, condition, context);
}
```

### Annotation Standards

**Always use Jakarta annotations:**

```java
// ✅ CORRECT
import jakarta.annotation.Nonnull;
import jakarta.annotation.Nullable;

public void method(@Nonnull String param, @Nullable Object optional) { }
```

**Never use JSpecify:**

```java
// ❌ WRONG - Don't use jspecify
import org.jspecify.annotations.NonNull;
import org.jspecify.annotations.Nullable;
```

---

## Test Object Creation Strategy

### Prefer Real Objects Over Mocks

**Hierarchy of test object creation:**

1. **Real objects** - When simple to create
2. **Stub implementations** - When behavior is simple but construction is complex
3. **Mocks** - Only when necessary for verification

### Real Objects (PREFERRED)

Use real framework objects when they're straightforward to create:

```java
// ✅ PREFERRED: Real message objects
private static QueryMessage queryMessage(QualifiedName name) {
    return new GenericQueryMessage(new MessageType(name), "test-payload");
}

private static CommandMessage commandMessage(Object payload) {
    return new GenericCommandMessage(MessageType.fromPayload(payload), payload);
}

private static EventMessage eventMessage(Object payload) {
    return new GenericEventMessage(MessageType.fromPayload(payload), payload);
}

// Usage in tests
@Test
void componentProcessesQuery() {
    QueryMessage query = queryMessage(new QualifiedName("TestQuery"));
    component.handle(query);
    // assertions
}
```

**Benefits:**
- Tests use actual framework objects
- More realistic test scenarios
- Less brittle than mocks
- Easier to maintain

### Stub Implementations (GOOD)

Create stub implementations for tracking behavior:

```java
// ✅ GOOD: Stub for tracking invocations
private static class StubConnector implements BusConnector {
    final Set<QualifiedName> subscriptions = new HashSet<>();
    final AtomicInteger callCount = new AtomicInteger(0);
    final List<Message> receivedMessages = new ArrayList<>();

    @Override
    public void subscribe(QualifiedName name) {
        subscriptions.add(name);
        callCount.incrementAndGet();
    }

    @Override
    public void send(Message message) {
        receivedMessages.add(message);
        callCount.incrementAndGet();
    }

    // Other interface methods with sensible defaults
    @Override
    public void describeTo(ComponentDescriptor descriptor) {
        descriptor.describeProperty("name", "StubConnector");
    }
}
```

**When to use stubs:**
- Tracking method invocations
- Testing integration between components
- Need default behavior for multiple methods
- Want to verify call counts or arguments

### Mocks (USE SPARINGLY)

Reserve mocks for cases where stubs aren't practical:

```java
// ⚠️ Only when necessary
Connector connector = mock(Connector.class);
when(connector.connect()).thenReturn(connection);

component.process(query);

verify(connector).connect();
verify(connector).send(any());
```

**When mocks are acceptable:**
- Complex external dependencies
- Need to verify specific interactions
- Behavior is difficult to stub
- Testing error conditions

---

## Resource Cleanup in Tests

### Always Clean Up Resources

Components that create resources must be cleaned up in tests:

**Resources requiring cleanup:**
- ExecutorServices and thread pools
- Temporary files and directories
- Database connections
- Network connections
- File handles

### Single-Use Resource Pattern

```java
@Test
void componentCreatesWorkingExecutor() {
    ExecutorService executor = component.createExecutor();

    try {
        // Test assertions
        assertNotNull(executor);
        assertInstanceOf(ThreadPoolExecutor.class, executor);

        // Test functionality
        CompletableFuture<String> future = CompletableFuture.supplyAsync(
            () -> "result",
            executor
        );
        assertEquals("result", future.join());
    } finally {
        executor.shutdown(); // Always cleanup
    }
}
```

### Shared Resource Pattern

```java
private ExecutorService executorService;
private TempDirectory tempDir;
private DatabaseConnection connection;

@BeforeEach
void setUp() {
    executorService = component.createExecutor();
    tempDir = TempDirectory.create();
    connection = database.connect();
}

@AfterEach
void cleanup() {
    if (executorService != null) {
        executorService.shutdown();
    }
    if (tempDir != null) {
        tempDir.delete();
    }
    if (connection != null) {
        connection.close();
    }
}
```

### Why Resource Cleanup Matters

1. **Thread leaks** - Unshutdown ExecutorServices leak threads
2. **File descriptor exhaustion** - Too many open files causes failures
3. **CI reliability** - Tests must not leave resources hanging
4. **Test independence** - Resources from one test shouldn't affect others

**Common mistake:**
```java
// ❌ BAD: Executor never shutdown
@Test
void testExecutor() {
    ExecutorService executor = component.createExecutor();
    // assertions...
    // Missing: executor.shutdown()
}
```

### Real-World Examples

AF5 codebase examples:
- `EventCriteria.havingTags(...).andBeingOneOfTypes(...)`
- `NamespaceMessageTypeResolver.namespace(...).message(...).fallback(...)`
- `Metadata.with(...).and(...)`
- `MultiStreamableEventSource.combining(...).and(...).comparingTimestamps()`

---

## 4. Configuration Class Design

### Immutable Configuration Pattern

Configuration classes should be immutable, with modification methods returning new instances:

**Structure:**
```java
public final class ComponentConfiguration {

    private static final int DEFAULT_THREADS = 10;
    private static final int DEFAULT_CAPACITY = 1000;

    @Nonnull
    private final ExecutorServiceFactory executorServiceFactory;
    private final Supplier<BlockingQueue<Runnable>> queueSupplier;
    private final boolean autoRetry;

    // Private constructor with all parameters
    private ComponentConfiguration(
            @Nonnull ExecutorServiceFactory executorServiceFactory,
            @Nonnull Supplier<BlockingQueue<Runnable>> queueSupplier,
            boolean autoRetry) {
        this.executorServiceFactory = executorServiceFactory;
        this.queueSupplier = queueSupplier;
        this.autoRetry = autoRetry;
    }

    /**
     * Constructs a default {@code ComponentConfiguration} with the following settings:
     * <ul>
     *     <li>Thread count: 10</li>
     *     <li>Queue capacity: 1000</li>
     *     <li>Auto-retry: enabled</li>
     * </ul>
     */
    public ComponentConfiguration() {
        this(DEFAULT_EXECUTOR_FACTORY.apply(DEFAULT_THREADS),
             () -> new LinkedBlockingQueue<>(DEFAULT_CAPACITY),
             true);
    }

    // Modification methods return NEW instance
    public ComponentConfiguration threadCount(int threads) {
        return new ComponentConfiguration(
                DEFAULT_EXECUTOR_FACTORY.apply(threads), // Modified
                queueSupplier,                            // Preserved
                autoRetry                                 // Preserved
        );
    }

    public ComponentConfiguration queueCapacity(int capacity) {
        return new ComponentConfiguration(
                executorServiceFactory,                      // Preserved
                () -> new LinkedBlockingQueue<>(capacity),   // Modified
                autoRetry                                    // Preserved
        );
    }

    public ComponentConfiguration autoRetry(boolean enabled) {
        return new ComponentConfiguration(
                executorServiceFactory,  // Preserved
                queueSupplier,           // Preserved
                enabled                  // Modified
        );
    }

    // Accessors
    public ExecutorServiceFactory executorServiceFactory() {
        return executorServiceFactory;
    }

    public boolean autoRetry() {
        return autoRetry;
    }

    // Factory method for component creation
    public ExecutorService createExecutor() {
        return executorServiceFactory.create(this, queueSupplier.get());
    }
}
```

### Configuration Design Principles

1. **Use `final` class** - Prevent inheritance
2. **All fields `final`** - Enforce immutability
3. **Private constructor** - Takes all parameters
4. **Public default constructor** - Sets sensible defaults with javadoc
5. **Modification methods** - Return new instances
6. **Preserve unmodified fields** - When creating new instances
7. **Fluent naming** - Use `withX()`, `threadCount()`, `enabled()` style
8. **Document defaults** - Constructor javadoc lists all defaults

### Testing Requirements for Configuration Classes

Every configuration class must have tests verifying:

**1. Default Values**
```java
@Test
void defaultConfigurationHasExpectedValues() {
    ComponentConfiguration config = new ComponentConfiguration();

    assertTrue(config.autoRetry());
    ExecutorService executor = config.createExecutor();
    assertInstanceOf(ThreadPoolExecutor.class, executor);

    ThreadPoolExecutor threadPool = (ThreadPoolExecutor) executor;
    assertEquals(10, threadPool.getCorePoolSize());

    executor.shutdown();
}
```

**2. Modification Methods**
```java
@Test
void threadCountCreatesExecutorWithCorrectSize() {
    ComponentConfiguration config = new ComponentConfiguration()
            .threadCount(20);

    ExecutorService executor = config.createExecutor();
    ThreadPoolExecutor threadPool = (ThreadPoolExecutor) executor;
    assertEquals(20, threadPool.getCorePoolSize());

    executor.shutdown();
}
```

**3. Immutability**
```java
@Test
void configurationIsImmutable() {
    ComponentConfiguration original = new ComponentConfiguration();
    ComponentConfiguration modified = original.threadCount(5);

    assertNotSame(original, modified);

    // Verify original unchanged
    ExecutorService originalExec = original.createExecutor();
    assertEquals(10, ((ThreadPoolExecutor) originalExec).getCorePoolSize());

    originalExec.shutdown();
    modified.createExecutor().shutdown();
}
```

**4. Fluent Chaining**
```java
@Test
void fluentChainingPreservesAllSettings() {
    ComponentConfiguration config = new ComponentConfiguration()
            .threadCount(20)
            .autoRetry(false)
            .queueCapacity(2000);

    assertFalse(config.autoRetry());

    ExecutorService executor = config.createExecutor();
    assertEquals(20, ((ThreadPoolExecutor) executor).getCorePoolSize());

    executor.shutdown();
}
```

**5. Null Safety**
```java
@Test
void rejectsNullExecutorService() {
    ComponentConfiguration config = new ComponentConfiguration();

    //noinspection DataFlowIssue
    assertThrows(NullPointerException.class,
                () -> config.customExecutor(null));
}
```

**6. Component Creation**
```java
@Test
void createExecutorProducesWorkingInstance() {
    ComponentConfiguration config = new ComponentConfiguration();
    ExecutorService executor = config.createExecutor();

    try {
        CompletableFuture<String> future = CompletableFuture.supplyAsync(
            () -> "result",
            executor
        );
        assertEquals("result", future.join());
    } finally {
        executor.shutdown();
    }
}
```

**7. Multiple Calls Create Different Instances**
```java
@Test
void multipleCallsCreateDifferentInstances() {
    ComponentConfiguration config = new ComponentConfiguration();

    ExecutorService executor1 = config.createExecutor();
    ExecutorService executor2 = config.createExecutor();

    assertNotSame(executor1, executor2);

    executor1.shutdown();
    executor2.shutdown();
}
```

---

## 5. Component Lifecycle Patterns

### Registration Pattern

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

### ProcessingLifecycle Hooks

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

---

## 5. Context and Resource Management

### ResourceKey Pattern

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

### Component Resolution

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

---

## 6. Thread Safety Patterns

### Immutability First

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

### Concurrent Collections

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

### Synchronization Strategies

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

---

## 7. SPI vs API Separation

### @Internal for SPIs

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

### Public User-Facing APIs

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

---

## 8. Validation and Error Handling

### Parameter Validation

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

### Exception Design

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

---

## 9. ComponentBuilder and Configuration

### ComponentBuilder Pattern

**Lazy construction with dependency injection:**

```java
@FunctionalInterface
public interface ComponentBuilder<C> {
    C build(@Nonnull Configuration config);
}

// Usage in module configuration
public interface CommandHandlerPhase extends ModuleBuilder<CommandHandlingModule> {
    CommandHandlerPhase commandHandler(
        @Nonnull QualifiedName commandName,
        @Nonnull ComponentBuilder<CommandHandler> commandHandlerBuilder
    );
}

// Example usage
module.commandHandlers()
      .commandHandler(
          new QualifiedName("RenameCourse"),
          config -> new RenameCourseHandler(
              config.getComponent(Repository.class),     // Resolve dependencies
              config.getComponent(EventStore.class)       // from configuration
          )
      );
```

**Pattern Benefits:**
1. **Lazy construction** - components built after full configuration
2. **Dependency resolution** - builder receives Configuration
3. **Type safety** - generic ensures correct return type
4. **Functional** - use lambdas for simple cases
5. **Testable** - easy to inject mocks via Configuration

### ModuleBuilder Pattern

**Phased module construction:**

```java
public interface ModuleBuilder<M extends Module> {
    M build();
}

// Fluent API with terminal operation
CommandHandlingModule module =
    CommandHandlingModule.named("checkout")
        .commandHandlers(handlers -> handlers
            .commandHandler(...)
            .commandHandler(...)
        )
        .build();  // Terminal operation
```

---

## 10. DescribableComponent Pattern

### Component Introspection

**Every infrastructure component:**

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

---

## Design Checklist for New Components

When creating a new Axon Framework component:

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
- [ ] Use `jakarta.annotation` (never `org.jspecify`)
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
MyComponent.builder()
    .withX(x)
    .withY(y)
    .build();
```

**Do:**
```java
// AF5 fluent style
MyComponent.configuring("name")
    .withX(x)
    .withY(y)
    .initialize();
```

See: `axon-framework-5-patterns` skill for fluent API design.

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
public class EventAppender {
    public EventAppender(ProcessingContext context) { ... }
}

// Users might create multiple instances
EventAppender appender1 = new EventAppender(context);
EventAppender appender2 = new EventAppender(context);  // Different instance!
```

**Do:**
```java
public class EventAppender {
    private EventAppender(ProcessingContext context) { ... }  // Private

    public static EventAppender forContext(ProcessingContext context) {
        return context.computeResourceIfAbsent(RESOURCE_KEY,
                                               () -> new EventAppender(context));
    }
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

---

## Examples from Codebase

### Example 1: Three-Tier Event Publishing

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

### Example 2: Command Handling Module

**Phased builder with forced choices:**
```java
CommandHandlingModule.named("checkout")              // Must provide name
    .commandHandlers(handlers -> handlers            // Explicit phase
        .commandHandler(cmdName, (cmd, ctx) -> {})  // Add handlers
        .commandHandlingComponent(cfg -> component)  // Or full component
    )
    .build();                                        // Terminal operation
```

### Example 3: EventStore API/SPI Separation

**Public API:**
```java
EventStore.transaction(context).appendEvent(event);
```

**Internal SPI:**
```java
@Internal
EventStorageEngine.appendEvents(condition, context, taggedEvents);
```

---

## Related Skills

- **axon-framework-5-patterns**: Fluent API and builder patterns
- **code-review**: Review checklist including API design standards
- **code-documentation**: JavaDoc standards for framework components

---

## References

- Core interfaces: `messaging/src/main/java/org/axonframework/messaging/`
- Gateway implementations: `messaging/src/main/java/org/axonframework/*/gateway/`
- Event store: `eventsourcing/src/main/java/org/axonframework/eventsourcing/eventstore/`
- Context: `messaging/src/main/java/org/axonframework/messaging/core/`
- Configuration: `common/src/main/java/org/axonframework/common/configuration/`

---

*This skill focuses on Axon Framework internals. For application development using Axon, see user documentation.*
