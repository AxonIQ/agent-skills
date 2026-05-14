# Use case 01 — Dispatch Interceptor, Spring Boot

Dispatch interceptor enriches a command with metadata before it reaches the bus. `@Component` stays; `InterceptorAutoConfiguration` discovers by generic type.

## Before (AF4)

```java
package io.axoniq.demo.bikerental.common;

import org.axonframework.commandhandling.CommandMessage;
import org.axonframework.messaging.MessageDispatchInterceptor;
import org.springframework.stereotype.Component;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.function.BiFunction;

@Component
public class DispatchTimeCommandDispatchInterceptor implements MessageDispatchInterceptor<CommandMessage<?>> {

    @Override
    public BiFunction<Integer, CommandMessage<?>, CommandMessage<?>> handle(
            List<? extends CommandMessage<?>> messages) {
        return (index, command) -> {
            return command.withMetaData(Map.of("dispatchTime", Instant.now().toString()));
        };
    }
}
```

## After (AF5)

```java
package io.axoniq.demo.bikerental.common;

import org.axonframework.messaging.commandhandling.CommandMessage;
import org.axonframework.messaging.core.MessageDispatchInterceptor;
import org.axonframework.messaging.core.MessageDispatchInterceptorChain;
import org.axonframework.messaging.core.MessageStream;
import org.axonframework.messaging.core.unitofwork.ProcessingContext;
import org.jspecify.annotations.Nullable;
import org.springframework.stereotype.Component;

import java.time.Instant;
import java.util.Collections;

@Component
public class DispatchTimeCommandDispatchInterceptor implements MessageDispatchInterceptor<CommandMessage> {

    @Override
    public MessageStream<?> interceptOnDispatch(CommandMessage message,
                                                @Nullable ProcessingContext context,
                                                MessageDispatchInterceptorChain<CommandMessage> chain) {
        CommandMessage enrichedMessage = message.andMetadata(
                Collections.singletonMap("dispatchTime", Instant.now().toString())
        );
        return chain.proceed(enrichedMessage, context);
    }
}
```

## What changed

- Method: `handle(List<...>)` → `interceptOnDispatch(M, @Nullable ProcessingContext, Chain)`
- Return: `BiFunction<Integer, M, M>` → `MessageStream<?>`
- Body: batch-lambda collapsed — receive one `message`, modify inline, call `chain.proceed(modified, context)`
- Generic: `CommandMessage<?>` → `CommandMessage` (no wildcard)
- `withMetaData(Map.of(...))` → `andMetadata(Collections.singletonMap(...))` — AF5 message accessor
- Removed imports: `java.util.List`, `java.util.function.BiFunction`, `java.util.Map`, `org.axonframework.commandhandling.CommandMessage` (AF4), `org.axonframework.messaging.MessageDispatchInterceptor` (AF4)
- Added imports: `org.axonframework.messaging.commandhandling.CommandMessage` (AF5), `org.axonframework.messaging.core.MessageDispatchInterceptor`, `org.axonframework.messaging.core.MessageDispatchInterceptorChain`, `org.axonframework.messaging.core.MessageStream`, `org.axonframework.messaging.core.unitofwork.ProcessingContext`, `org.jspecify.annotations.Nullable`, `java.util.Collections`
- `@Component` unchanged — Path A auto-discovery

## Caveats

- `context` is `@Nullable` — may be `null` when dispatching from outside a handler (HTTP endpoint). Pass it as-is to `chain.proceed(enrichedMessage, context)` — never null-guard it.
- `Map.of(...)` → `Collections.singletonMap(...)` is a style choice; either compiles. The key change is `withMetaData` → `andMetadata`.
