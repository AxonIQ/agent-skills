package com.example.config;

// AF4 Spring @Configuration that wires a pooled streaming processor + handler matcher + customisation,
// to be migrated to AF5 @Bean EventProcessorDefinition per use-case 04.

import org.axonframework.extension.spring.config.EventProcessorDefinition;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class AxonProcessorConfigSpring {

    @Bean
    public EventProcessorDefinition readModelDwellingProcessor() {
        return EventProcessorDefinition.pooledStreaming("ReadModel_Dwelling")
                .assigningHandlers(descriptor -> descriptor.beanType().getPackageName()
                        .startsWith("com.dddheroes.heroesofddd.creaturerecruitment.read"))
                .customized(config -> config.initialSegmentCount(8).batchSize(100));
    }
}
