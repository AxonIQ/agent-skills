---
atom-id: interceptor-dispatch
title: "MessageDispatchInterceptor.handle(List) → interceptOnDispatch(M, @Nullable ProcessingContext, Chain)"
af4-symbols: ["MessageDispatchInterceptor", "handle(List<? extends M>)", "BiFunction<Integer, M, M>", "java.util.List", "java.util.function.BiFunction"]
af5-symbols: ["interceptOnDispatch", "MessageDispatchInterceptorChain", "MessageStream", "org.axonframework.messaging.core.MessageDispatchInterceptor"]
detect: grep -rn 'implements MessageDispatchInterceptor\|BiFunction.*handle.*List' --include='*.java' --include='*.kt' --include='*.scala' .
used-by: [interceptors]
---

# MessageDispatchInterceptor: handle(List) → interceptOnDispatch

AF4 dispatch interceptors processed messages in a batch. The `handle(List<? extends M>)` method returned a
`BiFunction<Integer, M, M>` applied per message. AF5 changes to single-message, async-first: `interceptOnDispatch`
receives one message, modifies it inline, and delegates to the chain.

## Key change

| Element | AF4 | AF5 |
|---------|-----|-----|
| Method | `BiFunction<Integer, M, M> handle(List<? extends M> messages)` | `MessageStream<?> interceptOnDispatch(M message, @Nullable ProcessingContext context, MessageDispatchInterceptorChain<M> chain)` |
| Body | `return (index, msg) -> { ... return modified; }` | inline modify + `return chain.proceed(modifiedMessage, context)` |
| Generic | `CommandMessage<?>` | `CommandMessage` (no wildcard) |

## Transform

**Remove:**
```java
import java.util.List;
import java.util.function.BiFunction;

@Override
public BiFunction<Integer, CommandMessage<?>, CommandMessage<?>> handle(
        List<? extends CommandMessage<?>> messages) {
    return (index, message) -> {
        // modify message
        return modified;
    };
}
```

**Replace with:**
```java
import org.axonframework.messaging.core.MessageDispatchInterceptor;
import org.axonframework.messaging.core.MessageDispatchInterceptorChain;
import org.axonframework.messaging.core.MessageStream;
import org.axonframework.messaging.core.unitofwork.ProcessingContext;
import org.jspecify.annotations.Nullable;

@Override
public MessageStream<?> interceptOnDispatch(
        CommandMessage message,
        @Nullable ProcessingContext context,
        MessageDispatchInterceptorChain<CommandMessage> chain) {
    // modify message
    return chain.proceed(modifiedMessage, context);
}
```

## Import changes

Remove: `java.util.List`, `java.util.function.BiFunction`

Add: `org.axonframework.messaging.core.MessageDispatchInterceptor`, `org.axonframework.messaging.core.MessageDispatchInterceptorChain`, `org.axonframework.messaging.core.MessageStream`, `org.axonframework.messaging.core.unitofwork.ProcessingContext`, `org.jspecify.annotations.Nullable`

## Gotchas

- **`@Nullable ProcessingContext`** — dispatch interceptors run before any active context may exist; `context` may be null. Pass it as-is to `chain.proceed(message, context)` — never null-check to skip the chain.
- **Generic de-wildcard is mandatory** — `CommandMessage<?>` → `CommandMessage`. The AF5 interface declares the type without `<?>`. Leaving the wildcard causes a compile error.
- **BiFunction lambda collapses** — the `(index, msg) ->` batch pattern disappears entirely. Receive one `message`, modify it, forward to `chain.proceed(modified, context)`.
- **Always return `chain.proceed(...)`** — do not construct a `MessageStream` manually; the return value must come from the chain call.

## Used By

- **[[interceptors]]** — Step 2 (variant=dispatch or variant=both)
