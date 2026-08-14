# Fluent Builders and Configuration Choices

## Default Configuration vs Forced Choices

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

## The AF5 Fluent Builder Style

**AF4 used the traditional builder pattern** (avoid this now):
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

### Real-World Examples in the AF5 Codebase

- `EventCriteria.havingTags(...).andBeingOneOfTypes(...)`
- `NamespaceMessageTypeResolver.namespace(...).message(...).fallback(...)`
- `Metadata.with(...).and(...)`
- `MultiStreamableEventSource.combining(...).and(...).comparingTimestamps()`

## Testing Fluent Builders

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
