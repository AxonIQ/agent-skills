package com.example.config;

// AF4 non-Spring bootstrap that wires a pooled streaming processor via EventProcessingConfigurer.
// AF5 equivalent uses MessagingConfigurer.eventProcessing(...) — see use-case 05.

import org.axonframework.config.Configurer;
import org.axonframework.config.DefaultConfigurer;

public class AxonProcessorConfigNative {

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
                          type -> type.getPackageName()
                                      .startsWith("com.dddheroes.heroesofddd.creaturerecruitment.read")
                  )
                  .registerEventHandler(c -> new DwellingReadModelProjector(
                          c.getComponent(DwellingReadModelRepository.class)
                  ));

        configurer.buildConfiguration().start();
    }
}
