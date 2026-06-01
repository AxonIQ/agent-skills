# Use case 03 — Handler Interceptor, Native Config (registration site rewrite)

Standalone handler interceptor without Spring. Path B — explicit registration in Configurer. Shows both the interceptor class rewrite AND the registration call rewrite from `Configurer` to `MessagingConfigurer`.

## Before (AF4)

**Interceptor class:**

```java
package io.example.interceptors;

import org.axonframework.commandhandling.CommandMessage;
import org.axonframework.messaging.InterceptorChain;
import org.axonframework.messaging.MessageHandlerInterceptor;
import org.axonframework.messaging.unitofwork.UnitOfWork;

public class AuditCommandHandlerInterceptor implements MessageHandlerInterceptor<CommandMessage<?>> {

    @Override
    public Object handle(UnitOfWork<? extends CommandMessage<?>> unitOfWork,
                         InterceptorChain interceptorChain) throws Exception {
        // pre-handle audit
        Object result = interceptorChain.proceed();
        // post-handle audit
        return result;
    }
}
```

**Registration site (Configurer file):**

```java
import org.axonframework.config.Configurer;
import org.axonframework.config.DefaultConfigurer;

Configurer configurer = DefaultConfigurer.defaultConfiguration();
configurer.registerCommandHandlerInterceptor(config -> new AuditCommandHandlerInterceptor());
```

## After (AF5)

**Interceptor class:**

```java
package io.example.interceptors;

import org.axonframework.messaging.commandhandling.CommandMessage;
import org.axonframework.messaging.core.MessageHandlerInterceptor;
import org.axonframework.messaging.core.MessageHandlerInterceptorChain;
import org.axonframework.messaging.core.MessageStream;
import org.axonframework.messaging.core.unitofwork.ProcessingContext;

public class AuditCommandHandlerInterceptor implements MessageHandlerInterceptor<CommandMessage> {

    @Override
    public MessageStream<?> interceptOnHandle(CommandMessage message,
                                              ProcessingContext context,
                                              MessageHandlerInterceptorChain<CommandMessage> chain) {
        // pre-handle audit
        return chain.proceed(message, context);
        // post-handle audit belongs in runOnAfterCommit if needed
    }
}
```

**Registration site (Configurer file):**

```java
import org.axonframework.messaging.core.config.MessagingConfigurer;

MessagingConfigurer configurer = MessagingConfigurer.create();
configurer.registerCommandHandlerInterceptor(config -> new AuditCommandHandlerInterceptor());
```

## What changed

**Interceptor class:**
- Method: `handle(UnitOfWork, InterceptorChain) throws Exception` → `interceptOnHandle(M, ProcessingContext, Chain)`
- Return: `Object` → `MessageStream<?>`; intermediate result variable eliminated
- Chain: `interceptorChain.proceed()` → `chain.proceed(message, context)` as direct return
- Generic: `CommandMessage<?>` → `CommandMessage`
- Removed imports: `org.axonframework.commandhandling.CommandMessage` (AF4), `org.axonframework.messaging.InterceptorChain`, `org.axonframework.messaging.MessageHandlerInterceptor` (AF4), `org.axonframework.messaging.unitofwork.UnitOfWork`
- Added imports: AF5 equivalents

**Registration site:**
- Receiver type: `Configurer` (AF4) → `MessagingConfigurer` (AF5)
- Factory: `DefaultConfigurer.defaultConfiguration()` → `MessagingConfigurer.create()`
- Method name **unchanged**: `registerCommandHandlerInterceptor(...)` stays the same
- Import: `org.axonframework.config.Configurer` + `org.axonframework.config.DefaultConfigurer` removed; `org.axonframework.messaging.core.config.MessagingConfigurer` added

## Caveats

- Method names on `MessagingConfigurer` are identical to AF4 `Configurer` for typed interceptors (`registerCommandHandlerInterceptor`, `registerEventHandlerInterceptor`, `registerQueryHandlerInterceptor`). **Exception**: AF4 generic `registerDispatchInterceptor(...)` → AF5 typed `registerCommandDispatchInterceptor(...)` / `registerEventDispatchInterceptor(...)` / `registerQueryDispatchInterceptor(...)` — pick the correct typed form based on the interceptor's generic `M` type.
- AF4 post-handle logic stored in a local variable (`Object result = interceptorChain.proceed()`) cannot have a direct equivalent when the chain is async. Move post-handle logic into `context.runOnAfterCommit(...)` instead.
