package com.example.config;

import org.axonframework.axonserver.connector.AxonServerConfiguration;
import org.axonframework.axonserver.connector.AxonServerConnectionManager;
import org.axonframework.axonserver.connector.event.axon.AxonServerEventStore;
import org.axonframework.common.configuration.AxonConfiguration;
import org.axonframework.config.Configurer;
import org.axonframework.config.DefaultConfigurer;

public class EventStoreConfigNativeAxonServer {

    public AxonConfiguration buildConfiguration() {
        Configurer configurer = DefaultConfigurer.defaultConfiguration();

        configurer.configureEventStore(config ->
            AxonServerEventStore.builder()
                    .configuration(config.getComponent(AxonServerConfiguration.class))
                    .axonServerConnectionManager(config.getComponent(AxonServerConnectionManager.class))
                    .build()
        );

        return configurer.buildConfiguration();
    }
}
