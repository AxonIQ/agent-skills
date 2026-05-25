package com.example.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.axonframework.config.Configurer;
import org.axonframework.serialization.Serializer;
import org.axonframework.serialization.json.JacksonSerializer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * AF4 Spring Boot configuration that exposes a Jackson-backed Serializer bean.
 * Migration target: rename to AF5 Converter SPI under org.axonframework.conversion.
 */
@Configuration
public class SerializerConfig {

    @Bean
    public Serializer serializer(ObjectMapper objectMapper) {
        return JacksonSerializer.builder()
                .objectMapper(objectMapper)
                .build();
    }

    public void register(Configurer configurer, Serializer serializer) {
        configurer.configureSerializer(c -> serializer);
    }
}
