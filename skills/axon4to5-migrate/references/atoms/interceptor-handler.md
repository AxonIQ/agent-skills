---
atom-id: interceptor-handler
title: "MessageHandlerInterceptor.handle(UnitOfWork, InterceptorChain) → interceptOnHandle(M, ProcessingContext, Chain)"
af4-symbols: ["MessageHandlerInterceptor", "handle(UnitOfWork", "InterceptorChain", "org.axonframework.messaging.InterceptorChain", "org.axonframework.messaging.unitofwork.UnitOfWork"]
af5-symbols: ["interceptOnHandle", "MessageHandlerInterceptorChain", "org.axonframework.messaging.core.MessageHandlerInterceptor"]
detect: grep -rn 'implements MessageHandlerInterceptor\|UnitOfWork.*InterceptorChain' --include='*.java' --include='*.kt' --include='*.scala' .
used-by: [interceptors]
---

# MessageHandlerInterceptor: handle(UnitOfWork, InterceptorChain) → interceptOnHandle

AF4 handler interceptors received a `UnitOfWork` and `InterceptorChain`. AF5 replaces both with
`ProcessingContext` and a typed `MessageHandlerInterceptorChain<M>`. The chain call changes from
`chain.proceed()` (no args) to `chain.proceed(message, context)`.

## Key change

| Element | AF4 | AF5 |
|---------|-----|-----|
| Method | `Object handle(UnitOfWork<? extends M> unitOfWork, InterceptorChain interceptorChain) throws Exception` | `MessageStream<?> interceptOnHandle(M message, ProcessingContext context, MessageHandlerInterceptorChain<M> chain)` |
| Chain call | `interceptorChain.proceed()` | `chain.proceed(message, context)` |
| Return | `Object` | `MessageStream<?>` from `chain.proceed(...)` |
| Generic | `CommandMessage<?>` | `CommandMessage` (no wildcard) |

## Transform

**Remove:**
```java
import org.axonframework.messaging.unitofwork.UnitOfWork;
import org.axonframework.messaging.InterceptorChain;

@Override
public Object handle(UnitOfWork<? extends CommandMessage<?>> unitOfWork,
                     InterceptorChain interceptorChain) throws Exception {
    Object result = interceptorChain.proceed();
    return result;
}
```

**Replace with:**
```java
import org.axonframework.messaging.core.MessageHandlerInterceptor;
import org.axonframework.messaging.core.MessageHandlerInterceptorChain;
import org.axonframework.messaging.core.MessageStream;
import org.axonframework.messaging.core.unitofwork.ProcessingContext;

@Override
public MessageStream<?> interceptOnHandle(
        CommandMessage message,
        ProcessingContext context,
        MessageHandlerInterceptorChain<CommandMessage> chain) {
    return chain.proceed(message, context);
}
```

## Import changes

Remove: `org.axonframework.messaging.unitofwork.UnitOfWork`, `org.axonframework.messaging.InterceptorChain`

Add: `org.axonframework.messaging.core.MessageHandlerInterceptor`, `org.axonframework.messaging.core.MessageHandlerInterceptorChain`, `org.axonframework.messaging.core.MessageStream`, `org.axonframework.messaging.core.unitofwork.ProcessingContext`

## UnitOfWork callsite replacements

When the handler body used `UnitOfWork` lifecycle hooks, apply [[unit-of-work]] atom's lifecycle table:

| AF4 | AF5 |
|-----|-----|
| `unitOfWork.getMessage()` | use `message` parameter directly |
| `CurrentUnitOfWork.get()` | use `context` parameter |
| `unitOfWork.onCommit(uow -> {...})` | `context.runOnAfterCommit(ctx -> {...})` |
| `unitOfWork.onPrepareCommit(uow -> {...})` | `context.runOnPreInvocation(ctx -> {...})` |
| `unitOfWork.onRollback(uow -> {...})` | `context.onError((ctx, err) -> {...})` |
| `unitOfWork.onCleanup(uow -> {...})` | `context.doFinally(ctx -> {...})` |

## Gotchas

- **`chain.proceed()` → `chain.proceed(message, context)`** — must pass both args. The zero-arg form does not exist in AF5.
- **`ProcessingContext` is NOT `@Nullable` here** — unlike dispatch interceptors, the context is always present during handling.
- **Generic de-wildcard is mandatory** — `CommandMessage<?>` → `CommandMessage`. Wildcard causes a compile error.
- **`throws Exception` removed** — the AF5 signature does not declare checked exceptions.
- **`unitOfWork.getMessage()` → use `message` param** — the message is now directly available as the first parameter.

## Used By

- **[[interceptors]]** — Steps 3 & 4 (variant=handler or variant=both)
