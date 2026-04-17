# Configuration in Axon Framework 5

AF5 uses a builder-style configuration API. You compose a `MessagingConfigurer` (or its subtype `EventSourcingConfigurer` when you need the event store), register your modules and components, then call `start()` to get a live `AxonConfiguration`.

---

## Plain Java — minimal application

```java
import org.axonframework.messaging.core.configuration.MessagingConfigurer;
import org.axonframework.eventsourcing.configuration.EventSourcingConfigurer;

public class Application {

    public static void main(String[] args) {
        var config = EventSourcingConfigurer.create()
                // command handlers
                .registerCommandHandlingModule(
                    CommandHandlingModule.named("courses")
                        .commandHandlers()
                        .autodetectedCommandHandlingComponent(
                            c -> new CourseCommandHandler(c.getComponent(EventStore.class))))
                // event handlers
                .eventProcessing(ep -> ep
                    .pooledStreaming(ps -> ps
                        .processor("courses-projection",
                            components -> components.declarative(
                                "courses-handler",
                                c -> new CoursesProjection(repository)))))
                // query handlers
                .queries(q -> q
                    .module(QueryHandlingModule.named("courses-queries")
                        .queryHandlers()
                        .autodetectedQueryHandlingComponent(
                            c -> new CoursesQueryHandler(repository))))
                .start();

        var commands = config.getComponent(CommandGateway.class);
        var queries  = config.getComponent(QueryGateway.class);

        // ... run your application ...

        config.shutdown();
    }
}
```

Use `EventSourcingConfigurer` (instead of plain `MessagingConfigurer`) whenever you need an `EventStore` — i.e., whenever you write DCB command handlers or use `PooledStreamingEventProcessor`.

---

## Command handling module

```java
CommandHandlingModule.named("courses")
    .commandHandlers()
    // Annotation-based (recommended): scans the object for @CommandHandler methods
    .autodetectedCommandHandlingComponent(
        config -> new CourseCommandHandler(config.getComponent(EventStore.class)))
    // Programmatic: register a single lambda handler
    .commandHandler(
        new QualifiedName("faculty.ArchiveCourse"),
        config -> (cmd, ctx) -> {
            // handle
            return MessageStream.fromItems(resultMessage);
        });
```

---

## Event processing

### Subscribing processor — synchronous, in-transaction

```java
configurer.eventProcessing(ep -> ep
    .subscribing(sub -> sub
        .processor("notifications",
            components -> components.declarative(
                "notification-handler",
                c -> new NotificationHandler(emailService)))));
```

### Pooled streaming processor — async, trackable, replayable

```java
configurer.eventProcessing(ep -> ep
    .pooledStreaming(pool -> pool
        .processor("courses-projection",
            components -> components.declarative(
                "courses-handler",
                c -> new CoursesProjection(repository)))));
```

Configure DLQ on a pooled streaming processor using the `extend()` API:

```java
import org.axonframework.messaging.eventhandling.deadletter.DeadLetterQueueConfiguration;

.processor("courses-projection",
    components -> components.declarative("courses-handler",
                                         c -> new CoursesProjection(repository)))
.customized((cfg, c) -> c
    .extend(DeadLetterQueueConfiguration.class,
            () -> new DeadLetterQueueConfiguration().enabled().clearOnReset(true)))
```

See the **`event-handling` guide** for full DLQ configuration details including JDBC and JPA backends.

---

## TagResolver — enabling DCB event tagging

If you use `@EventTag` on event payloads for DCB sourcing, register `AnnotationBasedTagResolver` so tags are stored when events are appended:

```java
import org.axonframework.eventsourcing.eventstore.AnnotationBasedTagResolver;

EventSourcingConfigurer.create()
    .componentRegistry(cr -> cr.registerComponent(
        TagResolver.class,
        config -> new AnnotationBasedTagResolver()));
```

Without this (or an equivalent resolver), events are stored without tags and `SourcingCondition.conditionFor(EventCriteria.havingTags(...))` will return nothing.

---

## Transaction management

Hook in your transaction manager so units of work participate in database transactions:

```java
import org.axonframework.messaging.core.unitofwork.transaction.TransactionManager;

// JPA
configurer.componentRegistry(cr -> cr.registerComponent(
    TransactionManager.class,
    config -> new EntityManagerTransactionManager(entityManagerFactory)));

// No-op (default — suitable for in-memory/testing)
configurer.componentRegistry(cr -> cr.registerComponent(
    TransactionManager.class,
    config -> NoTransactionManager.INSTANCE));
```

---

## CorrelationDataProvider

Metadata to propagate automatically from incoming messages to all outgoing messages:

```java
import org.axonframework.messaging.core.correlation.CorrelationDataProvider;

configurer.componentRegistry(cr -> cr.registerComponent(
    CorrelationDataProvider.class,
    config -> message -> {
        var carry = new HashMap<String, String>();
        if (message.metadata().containsKey("traceId")) {
            carry.put("traceId", (String) message.metadata().get("traceId"));
        }
        if (message.metadata().containsKey("userId")) {
            carry.put("userId", (String) message.metadata().get("userId"));
        }
        return carry;
    }));
```

---

## Accessing components at runtime

After `start()`, retrieve any registered component from the live configuration:

```java
var config        = configurer.start();
var commandGateway = config.getComponent(CommandGateway.class);
var queryGateway   = config.getComponent(QueryGateway.class);
var eventGateway   = config.getComponent(EventGateway.class);
var eventStore     = config.getComponent(EventStore.class);
```

---

## Interceptors

Register interceptors via `MessagingConfigurer` (see the **`interceptors` guide** for the implementation patterns):

```java
configurer
    .registerCommandDispatchInterceptor(c -> new BeanValidationInterceptor<>())
    .registerCommandHandlerInterceptor(c -> new AuditLoggingInterceptor())
    .registerEventDispatchInterceptor(c -> new CorrelationEnrichingInterceptor<>());
```

---

## Spring Boot

When `extensions/spring` is on the classpath, Spring Boot auto-configuration wires `CommandGateway`, `QueryGateway`, `EventGateway`, and the command/event/query buses automatically. Annotate your handler classes with `@Component` (or `@Service`) and they are discovered and registered.

Customise via `application.yml` properties or by declaring `@Bean`s of `MessagingConfigurer`, `EventProcessingConfigurer`, etc. — Spring auto-configuration backs off when you provide your own.

```yaml
axon:
  event-processing:
    processors:
      courses-projection:
        mode: pooled-streaming
```

```java
@Configuration
class AxonConfig {

    @Bean
    TagResolver tagResolver() {
        return new AnnotationBasedTagResolver();
    }

    @Bean
    CorrelationDataProvider traceIdProvider() {
        return message -> Map.of("traceId",
                (String) message.metadata().getOrDefault("traceId", "unknown"));
    }
}
```

---

## Event store backends

`EventSourcingConfigurer` defaults to an **in-memory event store** (`InMemoryEventStorageEngine`), which is convenient for testing but not suitable for production.

### PostgreSQL (AxonIQ Framework — commercial)

The AxonIQ Framework PostgreSQL connector provides a production-grade `EventStorageEngine` with support for DCB tag-based indexing. Add the dependency:

```xml
<dependency>
    <groupId>io.axoniq.framework</groupId>
    <artifactId>axoniq-postgresql</artifactId>
</dependency>
```

Then register it:

```java
import io.axoniq.framework.postgresql.PostgresqlEventStorageEngine;

EventSourcingConfigurer.create()
    .componentRegistry(cr -> cr.registerComponent(
        EventStorageEngine.class,
        config -> new PostgresqlEventStorageEngine(dataSource, eventConverter, entitlementManager)))
    ...
```

With Spring Boot and `axoniq-postgresql` on the classpath, `PostgresqlAutoConfiguration` wires this automatically. Configure the datasource via standard Spring Boot datasource properties.

AxonIQ Framework is free for non-production use; production deployments require a paid subscription. See [axoniq.io/pricing](https://www.axoniq.io/pricing).

---

## Shutdown

Always shut down cleanly to flush in-flight event processors and release resources:

```java
Runtime.getRuntime().addShutdownHook(new Thread(config::shutdown));
```
