# 04 — Spring processor wiring: `EventProcessorDefinition` (Path A)

**Why this case is interesting:** AF5 Spring projects replace the AF4 `@Bean ConfigurerModule` that called `EventProcessingConfigurer.registerPooledStreamingEventProcessor(...)` with a single `@Bean EventProcessorDefinition`. The new bean owns the processor type (`pooledStreaming` or `subscribing`), handler matching, and customisation in one fluent builder. The AF4 `EventProcessingConfigurer` API is gone — keeping it side-by-side causes startup failures.

**Apply-condition:** `configuration=spring` AND the project's `@Configuration` class registers `$SOURCE`'s processor via the AF4 `EventProcessingConfigurer` API (`registerPooledStreamingEventProcessor(...)` / `registerSubscribingEventProcessor(...)` / `assignHandlerTypesMatching(...)`).

## Before (AF4)

```java
import org.axonframework.config.ConfigurerModule;
import org.axonframework.config.EventProcessingConfigurer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class AxonConfig {

    @Bean
    public ConfigurerModule configureProjectors() {
        return configurer -> {
            EventProcessingConfigurer processing = configurer.eventProcessing();
            processing.registerPooledStreamingEventProcessor(
                          "ReadModel_Dwelling",
                          org.axonframework.config.Configuration::eventStore,
                          (config, builder) -> builder.initialSegmentCount(8)
                                                      .batchSize(100)
                      )
                      .assignHandlerTypesMatching(
                          "ReadModel_Dwelling",
                          type -> type.getPackageName()
                                      .startsWith("com.dddheroes.heroesofddd.creaturerecruitment.read")
                      );
        };
    }
}
```

## After (AF5)

```java
import org.axonframework.extension.spring.config.EventProcessorDefinition;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class AxonConfig {

    @Bean
    public EventProcessorDefinition readModelDwellingProcessor() {
        return EventProcessorDefinition
                .pooledStreaming("ReadModel_Dwelling")
                .assigningHandlers(descriptor -> descriptor.beanType().getPackageName()
                                                .startsWith("com.dddheroes.heroesofddd.creaturerecruitment.read"))
                .customized(config -> config.initialSegmentCount(8).batchSize(100));
    }
}
```

For subscribing processors, swap `.pooledStreaming(...)` for `.subscribing(...)`:

```java
@Bean
public EventProcessorDefinition someSubscribingProcessor() {
    return EventProcessorDefinition.subscribing("SomeGroup")
                                   .assigningHandlers(descriptor -> /* … */);
}
```

## What changed

- AF4 `@Bean ConfigurerModule` returning a `Configurer` lambda → AF5 `@Bean EventProcessorDefinition` returning a fluent builder.
- Import: `org.axonframework.config.ConfigurerModule` and `org.axonframework.config.EventProcessingConfigurer` removed; `org.axonframework.extension.spring.config.EventProcessorDefinition` added. The `.extension.spring.config.` package is mandatory — the bean is Spring-Boot-specific.
- `registerPooledStreamingEventProcessor(name, eventStoreSupplier, customizer)` → `.pooledStreaming(name).customized(customizer)`. The event-store wiring is inferred from the configurer; no manual `eventStore` reference needed.
- `assignHandlerTypesMatching(name, predicate)` → `.assigningHandlers(descriptor -> predicate)`. The predicate's argument is now a `HandlerDescriptor` exposing `beanType()`, not a raw `Class<?>` — call `descriptor.beanType().getPackageName()` etc.
- The customisation closure signature changes too: AF4 `(config, builder) -> builder.initialSegmentCount(8)` → AF5 `config -> config.initialSegmentCount(8)`. The new closure is a single-arg setter chain on the `EventProcessorSettings` builder.

## Coexistence with YAML

`EventProcessorDefinition` `@Bean` and YAML properties are both valid AF5 inputs. The `@Bean` takes precedence when both define the same processor, but YAML can still set knobs the bean doesn't override:

```yaml
# application.yaml — drives the same processor's defaults
axon:
  eventhandling:
    processors:
      ReadModel_Dwelling:
        mode: pooled
        thread-count: 8
```

The `@Bean` here adds handler-matching + `initialSegmentCount` / `batchSize`, the YAML sets `thread-count`. Result is the union, with `@Bean` winning on overlap. Choose ONE source of truth per processor in real projects — mixing is OK during migration but should be cleaned up.

## Caveats

- **Mixed AF4 + AF5 wiring fails at startup.** Spring picks up the AF5 `@Bean EventProcessorDefinition` first; a stale `@Bean ConfigurerModule` that still references `EventProcessingConfigurer.registerPooledStreamingEventProcessor(...)` either fails (no such method on the AF5 `Configurer`) or is silently shadowed. Delete the AF4 wiring in the same commit.
- **`subscribing` processors are NOT the default.** AF4's default was `Tracking`; AF5's default is `pooledStreaming`. Use `subscribing` only when the AF4 source explicitly registered a subscribing processor.
- **Handler-matching closure differs.** The AF4 form took a `Class<?>` predicate; the AF5 form takes a `HandlerDescriptor`. Existing predicates that called `type.getPackageName()` work by going through `descriptor.beanType().getPackageName()`. Predicates that called more advanced reflection (e.g. `type.getDeclaredMethods()`) need re-thinking.
- **`EventProcessorDefinition.subscribing(...)`** exists for completeness but is rarely used in greenfield AF5 — most projects move to `pooledStreaming` for the throughput / resume semantics.
- **DO NOT use `MessagingConfigurer.eventProcessing(...)` in a Spring app.** That fluent block is the native (Path B) equivalent — see use-case 05. Spring projects always use `@Bean EventProcessorDefinition`.
