package com.example.config;

// AF4 Spring @Configuration that wires a pooled streaming processor + handler matcher + customisation,
// to be migrated to AF5 @Bean EventProcessorDefinition per use-case 04.

import org.axonframework.config.ConfigurerModule;
import org.axonframework.config.EventProcessingConfigurer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class AxonProcessorConfigSpring {

    @Bean
    public ConfigurerModule configureProjectors() {
        return configurer -> {
            EventProcessingConfigurer processing = configurer.eventProcessing();
            processing.registerPooledStreamingEventProcessor(
                            "ReadModel_Dwelling",
                            org.axonframework.config.Configuration::eventStore,
                            (config, builder) -> builder.initialSegmentCount(8).batchSize(100)
                    )
                    .assignHandlerTypesMatching(
                            "ReadModel_Dwelling",
                            type -> type.getPackageName()
                                        .startsWith("com.dddheroes.heroesofddd.creaturerecruitment.read")
                    );
        };
    }
}
