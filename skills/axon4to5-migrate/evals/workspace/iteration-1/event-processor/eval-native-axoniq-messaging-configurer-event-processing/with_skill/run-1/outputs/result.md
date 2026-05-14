**Result:** ✅ Success
**Source:** `com.example.config.AxonProcessorConfigNative`
**Recipe:** axon4to5-event-processor

**Notes:**
- Replaced AF4 `DefaultConfigurer.defaultConfiguration()` + `EventProcessingConfigurer.registerPooledStreamingEventProcessor(...)` chain with the AF5 `EventSourcingConfigurer.create()` + `MessagingConfigurer.eventProcessing(...)` fluent block (Path B — native).
- Dropped imports: `org.axonframework.config.Configurer`, `org.axonframework.config.DefaultConfigurer`. The implicit AF4 `EventProcessingConfigurer` reference is also gone.
- Added imports: `org.axonframework.eventsourcing.configuration.EventSourcingConfigurer`, `org.axonframework.messaging.configuration.MessagingConfigurer`.
- Processor name `ReadModel_Dwelling` preserved as the binding contract; matches the projector's `@Namespace` value and any external references.
- Handler registration migrated from `.registerEventHandler(...)` + `.assignHandlerTypesMatching(...)` to `module.eventHandlingComponents(components -> components.autodetected(cfg -> new DwellingReadModelProjector(cfg.getComponent(DwellingReadModelRepository.class))))` — the AF5 fluent block adopts the component for the surrounding processor.
- Customisation `(config, builder) -> builder.initialSegmentCount(8).batchSize(100)` preserved as `.customized((cfg, conf) -> conf.batchSize(100).initialSegmentCount(8))`.
- Lifecycle moved from `configurer.buildConfiguration().start()` to `eventSourcing.start()`.
- Did NOT introduce `org.axonframework.extension.spring.config.EventProcessorDefinition` — that bean type is Spring-only (Path A); this is the native Path B per use-case 05.

**Learnings:**
- None flagged: no DLQ, no `@EventHandlerInterceptor`, no orphaned `@Bean SequencingPolicy` in scope (file is a non-Spring bootstrap, not the projector class).
