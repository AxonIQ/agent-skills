package com.example.config;

import org.axonframework.axonserver.connector.AxonServerConfiguration;
import org.axonframework.axonserver.connector.AxonServerConnectionManager;
import org.axonframework.axonserver.connector.event.axon.AxonServerEventStore;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class EventStoreConfigSpringAxonServer {

    @Bean
    public AxonServerEventStore eventStore(AxonServerConfiguration serverConfig,
                                           AxonServerConnectionManager connectionManager) {
        return AxonServerEventStore.builder()
                .configuration(serverConfig)
                .axonServerConnectionManager(connectionManager)
                .build();
    }
}
