# Use case 02 — Handler Interceptor, Spring Boot (with lifecycle hooks)

Handler interceptor that logs commands and wires pre/post lifecycle callbacks. `@Component` stays; shows full `UnitOfWork` → `ProcessingContext` replacement including `onCommit` and `onRollback`.

## Before (AF4)

```java
package io.example.interceptors;

import org.axonframework.commandhandling.CommandMessage;
import org.axonframework.messaging.InterceptorChain;
import org.axonframework.messaging.MessageHandlerInterceptor;
import org.axonframework.messaging.unitofwork.UnitOfWork;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

@Component
public class LoggingCommandHandlerInterceptor implements MessageHandlerInterceptor<CommandMessage<?>> {

    private static final Logger logger = LoggerFactory.getLogger(LoggingCommandHandlerInterceptor.class);

    @Override
    public Object handle(UnitOfWork<? extends CommandMessage<?>> unitOfWork,
                         InterceptorChain interceptorChain) throws Exception {
        CommandMessage<?> command = unitOfWork.getMessage();
        logger.info("Handling command: {}", command.getCommandName());

        unitOfWork.onCommit(uow -> {
            logger.info("Command committed: {}", command.getCommandName());
        });

        unitOfWork.onRollback(uow -> {
            logger.error("Command rolled back: {}", command.getCommandName());
        });

        return interceptorChain.proceed();
    }
}
```

## After (AF5)

```java
package io.example.interceptors;

import org.axonframework.messaging.commandhandling.CommandMessage;
import org.axonframework.messaging.core.MessageHandlerInterceptor;
import org.axonframework.messaging.core.MessageHandlerInterceptorChain;
import org.axonframework.messaging.core.MessageStream;
import org.axonframework.messaging.core.unitofwork.ProcessingContext;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

@Component
public class LoggingCommandHandlerInterceptor implements MessageHandlerInterceptor<CommandMessage> {

    private static final Logger logger = LoggerFactory.getLogger(LoggingCommandHandlerInterceptor.class);

    @Override
    public MessageStream<?> interceptOnHandle(CommandMessage message,
                                              ProcessingContext context,
                                              MessageHandlerInterceptorChain<CommandMessage> chain) {
        logger.info("Handling command: {}", message.getCommandName());

        context.runOnAfterCommit(ctx -> {
            logger.info("Command committed: {}", message.getCommandName());
        });

        context.onError((ctx, error) -> {
            logger.error("Command rolled back: {}", message.getCommandName());
        });

        return chain.proceed(message, context);
    }
}
```

## What changed

- Method: `handle(UnitOfWork<...>, InterceptorChain) throws Exception` → `interceptOnHandle(M, ProcessingContext, Chain)`
- Return: `Object` → `MessageStream<?>`
- `unitOfWork.getMessage()` removed — use `message` parameter directly
- `unitOfWork.onCommit(uow -> ...)` → `context.runOnAfterCommit(ctx -> ...)`
- `unitOfWork.onRollback(uow -> ...)` → `context.onError((ctx, error) -> ...)` — note two-arg lambda
- `return interceptorChain.proceed()` → `return chain.proceed(message, context)`
- `throws Exception` removed from method signature
- Generic: `CommandMessage<?>` → `CommandMessage`
- Removed imports: `org.axonframework.commandhandling.CommandMessage` (AF4), `org.axonframework.messaging.InterceptorChain`, `org.axonframework.messaging.MessageHandlerInterceptor` (AF4), `org.axonframework.messaging.unitofwork.UnitOfWork`
- Added imports: `org.axonframework.messaging.commandhandling.CommandMessage` (AF5), `org.axonframework.messaging.core.MessageHandlerInterceptor`, `org.axonframework.messaging.core.MessageHandlerInterceptorChain`, `org.axonframework.messaging.core.MessageStream`, `org.axonframework.messaging.core.unitofwork.ProcessingContext`

## Caveats

- `onError` callback signature is `(ProcessingContext ctx, Throwable error)` — two args, not one.
- `onPrepareCommit` (AF4) → `runOnPreInvocation` (AF5), not `runOnAfterCommit`. Map carefully: pre-commit is `runOnPreInvocation`, post-commit is `runOnAfterCommit`.
- `context` for handler interceptors is **never null** — no `@Nullable` annotation needed.
