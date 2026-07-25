# Testing Framework Components

For fluent-builder-specific tests, see `fluent-builders.md`. For configuration-class test requirements, see `configuration-classes.md`.

## Test Object Creation Strategy

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

## Resource Cleanup in Tests

Components that create resources must be cleaned up in tests.

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
