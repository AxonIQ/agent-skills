# Configuration Class Design

## Immutable Configuration Pattern

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

## Configuration Design Principles

1. **Use `final` class** - Prevent inheritance
2. **All fields `final`** - Enforce immutability
3. **Private constructor** - Takes all parameters
4. **Public default constructor** - Sets sensible defaults with javadoc
5. **Modification methods** - Return new instances
6. **Preserve unmodified fields** - When creating new instances
7. **Fluent naming** - Use `withX()`, `threadCount()`, `enabled()` style
8. **Document defaults** - Constructor javadoc lists all defaults

## Testing Requirements for Configuration Classes

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

## ComponentBuilder Pattern

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

## ModuleBuilder Pattern

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
