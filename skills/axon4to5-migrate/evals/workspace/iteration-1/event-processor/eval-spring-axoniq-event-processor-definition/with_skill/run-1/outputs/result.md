**Result:** ✅ Success
**Source:** `com.example.config.AxonProcessorConfigSpring`
**Recipe:** axon4to5-event-processor

**Notes:** Replaced the AF4 `@Bean ConfigurerModule configureProjectors()` body with `@Bean EventProcessorDefinition readModelDwellingProcessor()` using the fluent builder `EventProcessorDefinition.pooledStreaming("ReadModel_Dwelling").assigningHandlers(...).customized(...)`. Removed AF4 imports `org.axonframework.config.ConfigurerModule` and `org.axonframework.config.EventProcessingConfigurer`; added `org.axonframework.extension.spring.config.EventProcessorDefinition`. `@Configuration` annotation and class name preserved. Namespace string `ReadModel_Dwelling` kept intact (binding contract with the projector's `@Namespace`).
