# 05 — Native processor wiring: `MessagingConfigurer.eventProcessing(...)` (Path B)

**Why this case is interesting:** Non-Spring projects used the AF4 `EventProcessingConfigurer` / `EventProcessingModule` API. AF5 routes everything through `MessagingConfigurer.eventProcessing(...)` — a fluent block that takes processor type, name, and a module-level configuration in one shot. The old `EventProcessingConfigurer` interface is gone.

**Apply-condition:** `configuration=native` AND the project's Configurer block calls `configurer.eventProcessing().registerPooledStreamingEventProcessor(...)` (or `registerSubscribingEventProcessor(...)`).

## Before (AF4)

```java
import org.axonframework.config.Configurer;
import org.axonframework.config.DefaultConfigurer;
import org.axonframework.config.EventProcessingConfigurer;

public class Bootstrap {

    public static void main(String[] args) {
        Configurer configurer = DefaultConfigurer.defaultConfiguration();

        configurer.eventProcessing()
                  .registerPooledStreamingEventProcessor(
                          "ReadModel_Dwelling",
                          org.axonframework.config.Configuration::eventStore,
                          (config, builder) -> builder.initialSegmentCount(8).batchSize(100)
                  )
                  .assignHandlerTypesMatching(
                          "ReadModel_Dwelling",
                          type -> type.getPackageName().startsWith("com.dddheroes.heroesofddd.creaturerecruitment.read")
                  )
                  .registerEventHandler(c -> new DwellingReadModelProjector(c.getComponent(DwellingReadModelRepository.class)));

        configurer.buildConfiguration().start();
    }
}
```

## After (AF5)

```java
import org.axonframework.eventsourcing.configuration.EventSourcingConfigurer;
import org.axonframework.messaging.core.configuration.MessagingConfigurer;

public class Bootstrap {

    public static void main(String[] args) {
        EventSourcingConfigurer eventSourcing = EventSourcingConfigurer.create();

        eventSourcing.messaging(messaging ->
            messaging.eventProcessing(eventProcessing ->
                eventProcessing.pooledStreaming(pooledStreaming ->
                    pooledStreaming.processor("ReadModel_Dwelling", module ->
                        module.eventHandlingComponents(components ->
                                  components.autodetected(cfg ->
                                      new DwellingReadModelProjector(
                                          cfg.getComponent(DwellingReadModelRepository.class)
                                      )
                                  )
                              )
                              .customized((cfg, conf) -> conf.batchSize(100).initialSegmentCount(8))
                    )
                )
            )
        );

        eventSourcing.start();
    }
}
```

For subscribing processors, swap `.pooledStreaming(...)` for `.subscribing(...)`:

```java
eventProcessing.subscribing(subscribing ->
    subscribing.processor("SomeGroup", module ->
        module.eventHandlingComponents(...)
              .notCustomized()
    )
)
```

## What changed

- **Top-level configurer**: AF4 `DefaultConfigurer.defaultConfiguration()` returning a `Configurer` → AF5 `EventSourcingConfigurer.create()` (event-sourcing-aware) or `MessagingConfigurer.create()` (messaging-only). The build/start lifecycle moves from `configurer.buildConfiguration().start()` to `configurer.start()` directly.
- **Event-processing entry point**: AF4 `configurer.eventProcessing()` returning an `EventProcessingConfigurer` → AF5 `.messaging(m -> m.eventProcessing(ep -> ...))` taking a fluent consumer.
- **Processor registration**: AF4 `.registerPooledStreamingEventProcessor(name, eventStoreSupplier, customizer)` → AF5 `.pooledStreaming(ps -> ps.processor(name, module -> ...))`. The event-store wiring is implicit; no manual `eventStore` supplier needed.
- **Handler registration**: AF4 `.registerEventHandler(cfg -> new MyProjector(cfg.getComponent(Repo.class)))` plus a separate `.assignHandlerTypesMatching(...)` → AF5 `module.eventHandlingComponents(components -> components.autodetected(cfg -> new MyProjector(...)))`. The matcher is implicit — `autodetected(...)` includes the component for the surrounding processor.
- **Customisation**: AF4 `(config, builder) -> builder.batchSize(100)` (2 args) → AF5 `(cfg, conf) -> conf.batchSize(100)` (still 2 args but on a different builder type). Use `.notCustomized()` when there were no AF4 customisations.
- **Module FQNs**: `org.axonframework.messaging.core.configuration.MessagingConfigurer`, `org.axonframework.eventsourcing.configuration.EventSourcingConfigurer`. The `EventProcessorModule` / `PooledStreamingEventProcessorModule` types are accessed through the fluent block; you rarely import them directly.

## Caveats

- **DO NOT use `EventProcessorDefinition` here.** That bean type is Spring-Boot-specific (`org.axonframework.extension.spring.config.EventProcessorDefinition`). Native projects always use the fluent `MessagingConfigurer.eventProcessing(...)` block.
- **Side-by-side AF4 + AF5 doesn't compile.** The AF4 `EventProcessingConfigurer` interface is gone in AF5; the old method calls won't resolve. Delete the entire AF4 chain in the same commit as introducing the AF5 fluent block.
- **`autodetected(...)` vs explicit handler matching.** The AF5 fluent block does the matching through `autodetected(...)` (the framework adopts the component for the surrounding processor). If the AF4 project used a custom `type -> …` predicate, the AF5 form is either `autodetected` plus class-level `@Namespace` on each component (recommended) or a custom `components.matching(...)` call (rare).
- **`notCustomized()` is mandatory when omitting customisation.** Forgetting it leaves the builder in an "uninitialised" state and start fails. Always close with either `.customized(...)` or `.notCustomized()`.
- **Subscribing vs pooled defaults**: AF4 default was `Tracking`; AF5 has no `Tracking`. The default is `pooledStreaming`. Only register `subscribing` when the AF4 source explicitly did so.
- **Per-slice projects** (vertical-slice layouts where each bounded context has its own `static MessagingConfigurer configure(MessagingConfigurer)` method) put the fluent block inside that per-slice method. The recipe migrates the slice that owns `$SOURCE`'s processor; other slices are out of scope.
