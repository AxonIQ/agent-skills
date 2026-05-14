package com.example.config;

import org.axonframework.eventsourcing.eventstore.EmbeddedEventStore;
import org.axonframework.eventsourcing.eventstore.EventStorageEngine;
import org.axonframework.extensions.mongo.eventsourcing.eventstore.MongoEventStorageEngine;
import org.axonframework.serialization.Serializer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class EventStoreConfigMongoBlocker {

    @Bean
    public EmbeddedEventStore eventStore(EventStorageEngine storageEngine) {
        return EmbeddedEventStore.builder()
                .storageEngine(storageEngine)
                .build();
    }

    @Bean
    public EventStorageEngine storageEngine(Serializer serializer) {
        return MongoEventStorageEngine.builder()
                .eventSerializer(serializer)
                .build();
    }
}
