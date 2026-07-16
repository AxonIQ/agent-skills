# Use case 04 — Annotation-based interceptor (B1 Blocker)

`@MessageHandlerInterceptor` used as a **method annotation** inside a handler class. This is NOT the same as implementing the `MessageHandlerInterceptor<M>` interface. Not functional in AF5 < 5.2.0. Recipe halts with Blocker B1.

## Source (triggers B1)

```java
package io.example.handlers;

import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.commandhandling.CommandMessage;
import org.axonframework.messaging.InterceptorChain;
import org.axonframework.messaging.interceptors.MessageHandlerInterceptor;
import org.springframework.stereotype.Component;

@Component
public class OrderCommandHandler {

    @CommandHandler
    public String handle(CreateOrderCommand cmd) {
        return "created";
    }

    @MessageHandlerInterceptor(messageType = CommandMessage.class)
    public Object intercept(CommandMessage<?> message, InterceptorChain chain) throws Exception {
        // pre-handling interceptor logic
        return chain.proceed();
    }
}
```

## Expected result

```
return BLOCKER

> **Result:** 🚧 Blocker
> **Source:** `io.example.handlers.OrderCommandHandler`
> **Recipe:** axon4to5-interceptors
>
> **Notes:** B1 — `@MessageHandlerInterceptor` annotation on method `intercept(...)` at `OrderCommandHandler.java:17`. Using this annotation to declare inline interceptor methods is not supported in AF5 < 5.2.0. The `MessageHandlerInterceptor<M>` *interface* is fully migratable; this *annotation* form requires AF5 5.2.0+.
>
> **Options:**
> - [ ] **skip** — keep `OrderCommandHandler` as-is; queue moves on. On AF5 < 5.2.0 the inline interceptor is silently ignored at runtime.
> - [ ] **revert** — undo any edits; restore pre-recipe state.
> - [ ] **solve-manually** — extract the interceptor method into a standalone class implementing `MessageHandlerInterceptor<CommandMessage>` (fully migratable today), or on AF5 5.2.0+ rewrite it to an annotated `@CommandHandlerInterceptor` method (`MessageHandlerInterceptorChain` parameter, `MessageStream` return).
```

## What distinguishes annotation from interface

| Form | Class declaration | Detectable by |
|------|-------------------|---------------|
| Interface (migratable) | Java `implements` / Kotlin `:` `MessageHandlerInterceptor<CommandMessage>` | `grep 'MessageHandlerInterceptor'` on the class declaration |
| Annotation (B1) | `@MessageHandlerInterceptor` on a method | `grep '@MessageHandlerInterceptor'` |

The annotation may appear on a class that also has `@CommandHandler` / `@EventHandler` methods — that's the expected pattern for the inline style. The interface implementation appears on a dedicated interceptor class without handler annotations.
