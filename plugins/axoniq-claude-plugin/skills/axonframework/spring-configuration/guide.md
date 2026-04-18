# Spring Boot Configuration in Axon Framework 5

AF5 auto-configures itself when `axon-spring-boot-starter` is on the classpath. Most components are discovered automatically from the Spring application context — you only need explicit configuration when you want non-default behaviour.

---

## What Spring Boot auto-detects

| What is detected | How | When required |
|---|---|---|
| Any singleton Spring bean whose methods carry `@CommandHandler`, `@EventHandler`, or `@QueryHandler` | `MessageHandlerLookup` (`BeanDefinitionRegistryPostProcessor`) scans the context at startup | No manual registration needed — just annotate and declare as a Spring bean |
| Classes annotated with `@EventSourced` | `SpringEventSourcedEntityLookup` detects all prototype-scoped beans bearing the annotation | Replaces manual `configurer.registerEntity(...)` calls |
| `CorrelationDataProvider` beans | Auto-collected and registered | Declare as `@Bean` to add correlation propagation |
| `EventProcessorDefinition` beans | Auto-collected and applied to the event processing configuration | Declare as `@Bean` to customise or create event processors |
| `CommandGateway`, `QueryGateway`, `EventGateway` | Auto-created as Spring beans | Inject directly; do not construct manually |
| `EventStore` | Auto-created (in-memory default; PostgreSQL when `axoniq-postgresql` is present) | Override by declaring an `EventStorageEngine` or `EventStore` `@Bean` |
| `TagResolver` | Auto-created as `AnnotationBasedTagResolver` | Override by declaring a `TagResolver` `@Bean` |

**Implication**: in a typical Spring Boot application you do not call `EventSourcingConfigurer` directly. Simply annotate your handler classes with `@Component` (or `@Service`, etc.) and declare entity classes with `@EventSourced`. Everything else is wired automatically.

---

## Declaring handlers — nothing extra required

```java
@Component
class CourseCommandHandler {

    @CommandHandler
    void handle(CreateCourse command, EventAppender events) {
        events.append(new CourseCreated(command.courseId(), command.name(), command.capacity()));
    }
}
```

```java
@Component
class CourseProjection {

    @EventHandler
    void on(CourseCreated event) {
        // update read model
    }
}
```

```java
@Component
class CourseQueryHandler {

    @QueryHandler
    CourseView handle(FindCourse query) {
        // return view
    }
}
```

No registration calls. `MessageHandlerLookup` detects any `@Component` singleton with these annotations and registers it automatically.

---

## `@EventSourced` — declaring event-sourced entities

`@EventSourced` is a Spring-specific composite stereotype that combines `@Component` + `@Scope("prototype")` + `@EventSourcedEntity`. Declare it on entity classes that are injected via `@InjectEntity`.

```java
import org.axonframework.extension.spring.stereotype.EventSourced;

@EventSourced
public class CourseState {

    private boolean closed;

    @EventSourcingHandler
    void on(CourseCreated event) { /* initialise */ }

    @EventSourcingHandler
    void on(CourseClosed event) { this.closed = true; }
}
```

`SpringEventSourcedEntityLookup` detects this class and registers it — no `configurer.registerEntity(...)` call needed.

### `@EventSourced` attributes

| Attribute | Type | Default | Purpose |
|---|---|---|---|
| `type` | `String` | Simple class name | Logical type name for the entity |
| `idType` | `Class<?>` | `String.class` | Java type of the entity's identifier; must match the routing key type |
| `tagKey` | `String` | Simple class name | Tag key used to source events for this entity (overridden if an `@EventCriteriaBuilder` method exists) |
| `concreteTypes` | `Class<?>[]` | `{}` | Concrete subclasses for polymorphic entities; required when the entity is abstract |
| `criteriaResolverDefinition` | `Class<? extends CriteriaResolverDefinition>` | `AnnotationBasedEventCriteriaResolverDefinition.class` | How sourcing criteria are resolved; override to use custom logic |
| `entityFactoryDefinition` | `Class<? extends EventSourcedEntityFactoryDefinition>` | `AnnotationBasedEventSourcedEntityFactoryDefinition.class` | How a new entity instance is created |
| `entityIdResolverDefinition` | `Class<? extends EntityIdResolverDefinition>` | `AnnotatedEntityIdResolverDefinition.class` | How the entity ID is extracted from the command; default uses `@TargetEntityId` |

```java
@EventSourced(idType = UUID.class, tagKey = "course")
public class CourseState { ... }
```

---

## `@Namespace` — routing event handlers to processors

`@Namespace` marks a class (or its package) so that `EventHandlerSelector.matchesNamespaceOnType()` can assign it to the matching processor.

```java
import org.axonframework.messaging.core.annotation.Namespace;

@Namespace("courses")
@Component
class CourseProjection {

    @EventHandler
    void on(CourseCreated event) { ... }
}
```

Place on:
- A class → applies to that class
- `package-info.java` → applies to all classes in the package
- A module descriptor → applies to all classes in the module

The namespace value is matched against processor definitions that use `pooledStreamingMatching(name)` or `subscribingMatching(name)` (see below).

---

## `EventProcessorDefinition` — custom event processor configuration

Declare an `EventProcessorDefinition` bean to control which event handlers go into which processor and how that processor is configured. Auto-configuration collects all `EventProcessorDefinition` beans at startup.

### Factory methods

| Method | Processor type | Handler selection |
|---|---|---|
| `pooledStreaming(name)` | `PooledStreamingEventProcessor` | Manual — supply a selector |
| `pooledStreamingMatching(name)` | `PooledStreamingEventProcessor` | Auto — matches handlers whose `@Namespace` equals `name` |
| `subscribing(name)` | `SubscribingEventProcessor` | Manual — supply a selector |
| `subscribingMatching(name)` | `SubscribingEventProcessor` | Auto — matches handlers whose `@Namespace` equals `name` |

`pooledStreamingMatching` and `subscribingMatching` are shorthands for calling `assigningHandlers(EventHandlerSelector.matchesNamespaceOnType(name))` automatically.

### Fluent API flow

```
EventProcessorDefinition.pooledStreaming("myProcessor")   // 1. choose type + name
    .assigningHandlers(selector)                           // 2. assign handlers
    .customized(config -> config.batchSize(10))            // 3. configure (or .notCustomized())
```

`pooledStreamingMatching` / `subscribingMatching` skip step 2:

```
EventProcessorDefinition.pooledStreamingMatching("courses")  // assigns by @Namespace("courses")
    .customized(config -> config.maxClaimedSegments(4))
```

### `EventHandlerSelector` — the selector predicate

`EventHandlerSelector` is a functional interface (`Predicate<EventHandlerDescriptor>`). Use a lambda or the built-in factory:

```java
// Lambda — match by bean name prefix
EventHandlerSelector selector = descriptor -> descriptor.beanName().startsWith("order");

// Built-in — match by @Namespace value
EventHandlerSelector selector = EventHandlerSelector.matchesNamespaceOnType("orders");
```

`EventHandlerDescriptor` provides:
- `beanName()` — Spring bean name
- `beanType()` — Java type (`null` if Spring cannot resolve it)
- `beanDefinition()` — Spring `BeanDefinition`
- `resolveBean()` — actual bean instance

`matchesNamespaceOnType(namespace)` searches for `@Namespace` in this order: class → enclosing classes → package → module. Returns `false` if the type cannot be resolved.

### Full example

```java
@Configuration
class ProcessorConfig {

    @Bean
    EventProcessorDefinition coursesProcessor() {
        return EventProcessorDefinition.pooledStreamingMatching("courses")
                .customized(config -> config
                        .initialSegmentCount(8)
                        .maxClaimedSegments(4)
                        .batchSize(10));
    }

    @Bean
    EventProcessorDefinition notificationsProcessor() {
        return EventProcessorDefinition.subscribing("notifications")
                .assigningHandlers(descriptor ->
                        descriptor.beanType() != null
                        && descriptor.beanType().getPackageName().startsWith("com.example.notifications"))
                .notCustomized();
    }
}
```

---

## `PooledStreamingEventProcessorConfiguration` reference

All methods return `PooledStreamingEventProcessorConfiguration` for fluent chaining.

| Method | Default | Purpose |
|---|---|---|
| `initialSegmentCount(int)` | `16` | Segments created at first startup (no-op if tokens already exist) |
| `maxClaimedSegments(int)` | unlimited | Maximum segments a single instance will claim |
| `batchSize(int)` | `1` | Events processed per transaction — increase for throughput when handlers are idempotent |
| `tokenClaimInterval(long ms)` | `5000` | Wait time after a failed claim attempt before retrying |
| `claimExtensionThreshold(long ms)` | `5000` | How often a work package extends its token claim while idle |
| `enableCoordinatorClaimExtension()` | off | Lets the coordinator extend claims on behalf of work packages (useful when batch processing is long) |
| `eventSource(StreamableEventSource)` | from config | Override the event source (e.g. for multi-source streaming) |
| `tokenStore(TokenStore)` | from config | Override the token store |
| `coordinatorExecutor(ScheduledExecutorService)` | from config | Thread pool for the coordinator |
| `workerExecutor(ScheduledExecutorService)` | from config | Thread pool for work packages |
| `errorHandler(ErrorHandler)` | `PropagatingErrorHandler` | Override error handling strategy |
| `initialToken(Function<TrackingTokenSource, CompletableFuture<TrackingToken>>)` | replay from head | Override where processing starts on first run |
| `eventCriteria(Function<Set<QualifiedName>, EventCriteria>)` | `havingAnyTag().andBeingOneOfTypes(...)` | Override event filtering criteria |
| `withInterceptor(MessageHandlerInterceptor<EventMessage>)` | none | Add a handler interceptor for this processor |

---

## `SubscribingEventProcessorConfiguration` reference

| Method | Purpose |
|---|---|
| `eventSource(SubscribableEventSource)` | Override the event bus/source |
| `errorHandler(ErrorHandler)` | Override error handling |
| `unitOfWorkFactory(UnitOfWorkFactory)` | Override unit of work lifecycle |
| `withInterceptor(MessageHandlerInterceptor<EventMessage>)` | Add a handler interceptor |

---

## `application.yml` processor properties

`@ConfigurationProperties("axon.eventhandling")` binds processor settings by name. These are overridden by programmatic `EventProcessorDefinition.customized(...)` settings when both are present.

```yaml
axon:
  eventhandling:
    processors:
      courses:
        mode: POOLED                   # POOLED (default) or SUBSCRIBING
        initial-segment-count: 16      # segments on first run
        max-claimed-segments: 4        # max segments per instance (optional)
        batch-size: 1                  # events per transaction
        token-claim-interval: 5000     # ms between claim retries
        token-claim-interval-time-unit: MILLISECONDS
        thread-count: 4                # worker threads
        token-store: tokenStore        # Spring bean name of the TokenStore
        source:                        # Spring bean name of the event source (optional)
        sequencing-policy:             # Spring bean name of SequencingPolicy (optional)
      notifications:
        mode: SUBSCRIBING
```

Valid values for `mode`: `POOLED`, `SUBSCRIBING`.

---

## Correlation data providers

Declare any number of `CorrelationDataProvider` beans — all are auto-registered:

```java
@Bean
CorrelationDataProvider traceIdProvider() {
    return message -> {
        var carry = new java.util.HashMap<String, Object>();
        if (message.metadata().containsKey("traceId")) {
            carry.put("traceId", message.metadata().get("traceId"));
        }
        return carry;
    };
}
```

---

## Common configuration overrides via `@Bean`

| Bean type | Effect |
|---|---|
| `TagResolver` | Override tag resolution (default: `AnnotationBasedTagResolver`) |
| `EventStorageEngine` | Replace the in-memory default (e.g. `PostgresqlEventStorageEngine`) |
| `TransactionManager` | Provide JPA or custom transaction management |
| `TokenStore` | Provide a durable token store for pooled streaming processors |
| `CorrelationDataProvider` | Add metadata propagation (multiple beans supported) |
| `EventProcessorDefinition` | Define or customise event processors (multiple beans supported) |

When you declare any of these, Spring Boot auto-configuration backs off and uses your bean instead.
