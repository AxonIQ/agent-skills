package io.axoniq.demo.bikerental.common;

import org.axonframework.commandhandling.CommandMessage;
import org.axonframework.messaging.MessageDispatchInterceptor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Instant;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.function.BiFunction;

/**
 * Command dispatch interceptor that logs information about dispatched commands.
 * This interceptor is invoked before commands are dispatched to the command bus.
 */
public class DispatchTimeCommandDispatchInterceptor implements MessageDispatchInterceptor<CommandMessage<?>> {

    private static final Logger logger = LoggerFactory.getLogger(DispatchTimeCommandDispatchInterceptor.class);

    @Override
    public BiFunction<Integer, CommandMessage<?>, CommandMessage<?>> handle(
            List<? extends CommandMessage<?>> messages) {
        return (index, command) -> {
            // Return the command unmodified (you could modify it here if needed)
            return command.withMetaData(Map.of("dispatchTime", Instant.now().toString()));
        };
    }
}
