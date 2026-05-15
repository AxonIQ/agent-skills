package io.example.config;

import io.example.interceptors.AuditCommandHandlerInterceptor;
import org.axonframework.config.Configurer;
import org.axonframework.config.DefaultConfigurer;

public class AuditInterceptorNativeConfig {

    public static void configure() {
        Configurer configurer = DefaultConfigurer.defaultConfiguration();
        configurer.registerCommandHandlerInterceptor(config -> new AuditCommandHandlerInterceptor());
    }
}
