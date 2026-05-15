package com.example.config;

import org.axonframework.config.AxonConfiguration;
import org.axonframework.eventsourcing.eventstore.EmbeddedEventStore;
import org.axonframework.eventsourcing.eventstore.EventStorageEngine;
import org.axonframework.eventsourcing.eventstore.jpa.JpaEventStorageEngine;
import org.axonframework.messaging.interceptors.BeanValidationInterceptor;
import org.axonframework.spring.messaging.unitofwork.SpringTransactionManager;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.transaction.PlatformTransactionManager;

import javax.persistence.EntityManagerFactory;

@Configuration
public class EventStoreConfigSpringJpa {

    @Bean
    public EmbeddedEventStore eventStore(EventStorageEngine storageEngine,
                                         AxonConfiguration config) {
        return EmbeddedEventStore.builder()
                .storageEngine(storageEngine)
                .messageMonitor(config.messageMonitor(EmbeddedEventStore.class, "eventStore"))
                .build();
    }

    @Bean
    public EventStorageEngine storageEngine(EntityManagerFactory entityManagerFactory,
                                            PlatformTransactionManager transactionManager) {
        return JpaEventStorageEngine.builder()
                .entityManagerProvider(entityManagerFactory::createEntityManager)
                .transactionManager(new SpringTransactionManager(transactionManager))
                .build();
    }
}
