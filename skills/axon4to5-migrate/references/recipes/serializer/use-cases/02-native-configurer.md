# Use case 02 — Native `Configurer` (`configureSerializer`)

**Why interesting:** Non-Spring projects wire serialization through the `Configurer` fluent API (`configureSerializer` / `configureMessageSerializer` / `configureEventSerializer`). AF5 moves this to `MessagingConfigurer.componentRegistry(...)` with explicit `registerComponent` calls — a structural shift, not a method rename.

## Before (AF4)

```java
public void configure(Configurer configurer) {
    configurer.configureSerializer(c -> JacksonSerializer.defaultSerializer())
              .configureMessageSerializer(c -> JacksonSerializer.defaultSerializer())
              .configureEventSerializer(c -> JacksonSerializer.defaultSerializer());
}
```

Imports:
```java
import org.axonframework.config.Configurer;
import org.axonframework.serialization.json.JacksonSerializer;
```

## After (AF5)

```java
public void configure(MessagingConfigurer configurer, ObjectMapper objectMapper) {
    configurer.componentRegistry(registry -> {
        Converter generalConverter = new JacksonConverter(objectMapper);
        registry.registerComponent(GeneralConverter.class, c -> new DelegatingGeneralConverter(generalConverter));
        registry.registerComponent(MessageConverter.class, c -> new DelegatingMessageConverter(generalConverter));
        registry.registerComponent(EventConverter.class, c -> new DelegatingEventConverter(generalConverter));
    });
}
```

Imports (two artifacts):
```java
import org.axonframework.conversion.Converter;
import org.axonframework.conversion.GeneralConverter;
import org.axonframework.conversion.DelegatingGeneralConverter;
import org.axonframework.conversion.jackson.JacksonConverter;
import org.axonframework.messaging.core.conversion.MessageConverter;
import org.axonframework.messaging.core.conversion.DelegatingMessageConverter;
import org.axonframework.messaging.eventhandling.conversion.EventConverter;
import org.axonframework.messaging.eventhandling.conversion.DelegatingEventConverter;
```

## What changed

- `Configurer.configureSerializer*(...)` → `MessagingConfigurer.componentRegistry(registry -> registry.registerComponent(...))`.
- Each of the three serializer levels maps to a `registerComponent` call keyed by `GeneralConverter.class` / `MessageConverter.class` / `EventConverter.class`.
- `JacksonSerializer.defaultSerializer()` → `new JacksonConverter(objectMapper)` wrapped in the matching `Delegating*Converter`.
- The shared `generalConverter` instance is reused as the delegate for all three — `DelegatingEventConverter(Converter)` and `DelegatingMessageConverter(Converter)` both accept it.

## Caveats

- **`Converter` is in `org.axonframework.conversion`**, but `MessageConverter` / `EventConverter` are under `org.axonframework.messaging.*.conversion`. Mixed import roots are correct here, not a mistake.
- If AF4 only called `configureSerializer` (no message/event specialisation), register just `GeneralConverter` — the framework derives the rest.
- `ObjectMapper` is supplied by the caller's wiring; if AF4 used `defaultSerializer()` with no custom mapper, a `new JacksonConverter()` (no-arg) is equivalent.
