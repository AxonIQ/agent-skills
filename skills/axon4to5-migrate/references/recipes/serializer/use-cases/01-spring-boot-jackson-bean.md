# Use case 01 — Spring Boot + Jackson `@Bean Serializer`

**Why interesting:** The most common shape — a `@Configuration` class with one `@Bean Serializer` built from `JacksonSerializer`, often with a `RevisionResolver`. The swap is straightforward, but the converter types come from **two different artifacts** — the single trap that makes a naive `import org.axonframework.conversion.*` fail to compile.

## Before (AF4)

```java
@Configuration
public class AxonSerializationConfig {

    @Bean
    @Primary
    public Serializer axonJsonSerializer(ObjectMapper objectMapper) {
        return JacksonSerializer.builder()
                .objectMapper(objectMapper)
                .revisionResolver(new AnnotationRevisionResolver())
                .build();
    }
}
```

Imports:
```java
import org.axonframework.serialization.Serializer;
import org.axonframework.serialization.json.JacksonSerializer;
import org.axonframework.serialization.AnnotationRevisionResolver;
```

## After (AF5)

```java
@Configuration
public class ConversionConfig {

    @Bean
    @Primary
    public GeneralConverter converter(ObjectMapper objectMapper) {
        return new DelegatingGeneralConverter(new JacksonConverter(objectMapper));
    }

    @Bean
    public MessageConverter messageConverter(GeneralConverter generalConverter) {
        return new DelegatingMessageConverter(generalConverter);
    }

    @Bean
    public EventConverter eventConverter(MessageConverter messageConverter) {
        return new DelegatingEventConverter(messageConverter);
    }
}
```

Imports (two artifacts — `axon-conversion` and `axon-messaging`):
```java
import org.axonframework.conversion.GeneralConverter;
import org.axonframework.conversion.DelegatingGeneralConverter;
import org.axonframework.conversion.jackson.JacksonConverter;
import org.axonframework.messaging.core.conversion.MessageConverter;
import org.axonframework.messaging.core.conversion.DelegatingMessageConverter;
import org.axonframework.messaging.eventhandling.conversion.EventConverter;
import org.axonframework.messaging.eventhandling.conversion.DelegatingEventConverter;
```

## What changed

- `@Bean Serializer` → `@Bean @Primary GeneralConverter`. The `Serializer` interface and `JacksonSerializer` are removed; `JacksonConverter` is the replacement, wrapped in `DelegatingGeneralConverter`.
- `JacksonConverter` takes the `ObjectMapper` directly (`new JacksonConverter(objectMapper)`); no builder.
- `RevisionResolver` wiring **dropped** — `AnnotationRevisionResolver` / `FixedValueRevisionResolver` / `MavenArtifactRevisionResolver` have no AF5 successor.
- Added `MessageConverter` and `EventConverter` beans — present here because this app serialized both messages and events. If AF4 had only the one general `@Bean Serializer`, the `GeneralConverter` bean alone suffices and auto-config derives the rest.

## Caveats

- **`MessageConverter` / `EventConverter` are NOT in `org.axonframework.conversion`.** They live under `org.axonframework.messaging.core.conversion` and `org.axonframework.messaging.eventhandling.conversion` respectively (both in `axon-messaging`). Importing them from `conversion` is the classic compile failure.
- **`DelegatingEventConverter`** accepts either a `Converter` or a `MessageConverter` — passing `messageConverter` (as above) or the general converter both compile.
- If event payloads relied on `@Revision` for upcasting, dropping the resolver is a behavioural change — surface as a Learning; resolving it is out of this recipe's scope.
