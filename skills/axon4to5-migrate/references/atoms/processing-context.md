---
atom-id: processing-context
title: "UnitOfWork → ProcessingContext — InterceptorChain.proceedSync + injection"
af4-symbols: ["UnitOfWork", "CurrentUnitOfWork", "InterceptorChain.proceed()", "org.axonframework.messaging.unitofwork"]
af5-symbols: ["ProcessingContext", "InterceptorChain.proceedSync(context)", "org.axonframework.messaging.core.ProcessingContext"]
detect: grep -rn 'UnitOfWork\|CurrentUnitOfWork\|InterceptorChain' --include='*.java' --include='*.kt' --include='*.scala' .
used-by: [interceptors, event-processor, saga]
---

# UnitOfWork → ProcessingContext

AF4 used a `ThreadLocal`-backed `UnitOfWork` to manage per-message processing state. AF5 replaces this with
`ProcessingContext` passed explicitly as a method parameter throughout all infrastructure interfaces.

## Key design change

| Concept | AF4 | AF5 |
|---|---|---|
| Current context | `CurrentUnitOfWork.get()` (ThreadLocal) | `ProcessingContext context` parameter |
| Nesting | `parent()` / `root()` methods | Removed — no nesting |
| Lifecycle operations | `start()` / `commit()` / `rollback()` | Not directly callable; framework manages |
| Error handling | `onRollback(handler)` | `context.onError(handler)` / `context.doFinally(handler)` |
| Resources | `resources().put(key, value)` | `context.getOrComputeResource(key, factory)` |

## Part 1 — InterceptorChain.proceed()

In AF4, `@MessageHandlerInterceptor` methods called `chain.proceed()` (no parameters). In AF5, `proceed` is
replaced by `proceedSync(context)` and requires the active `ProcessingContext` to be passed:

**Remove:**
```java
import org.axonframework.messaging.MessageHandlerInterceptor;
import org.axonframework.messaging.unitofwork.UnitOfWork;

@MessageHandlerInterceptor
public Object intercept(MyMessage message, UnitOfWork<?> unitOfWork, InterceptorChain chain) throws Exception {
    // pre-handling
    Object result = chain.proceed();
    // post-handling
    return result;
}
```

**Replace with:**
```java
import org.axonframework.messaging.core.ProcessingContext;

@MessageHandlerInterceptor
public void intercept(MyMessage message, InterceptorChain chain, ProcessingContext context) {
    // pre-handling
    chain.proceedSync(context);
    // post-handling
}
```

The method signature can also inject `ProcessingContext` separately and pass it to `proceedSync`.

## Part 2 — Inject ProcessingContext in message handlers

In any message handler that previously accessed `CurrentUnitOfWork`, declare `ProcessingContext context` as a
method parameter. The framework injects it automatically.

```java
// AF4
@EventHandler
public void on(OrderShippedEvent event) {
    UnitOfWork<?> uow = CurrentUnitOfWork.get();
    uow.onCleanup(u -> cache.evict(orderId));
}

// AF5
@EventHandler
public void on(OrderShippedEvent event, ProcessingContext context) {
    context.doFinally(ctx -> cache.evict(orderId));
}
```

## Lifecycle phase equivalents

| AF4 | AF5 |
|---|---|
| `uow.onCommit(handler)` | `context.onComplete(handler)` (success only) |
| `uow.onRollback(handler)` | `context.onError(handler)` |
| `uow.onCleanup(handler)` | `context.doFinally(handler)` (success and error) |
| `uow.afterCommit(handler)` | `context.afterCommit(handler)` |
| `uow.resources().put(key, val)` | `context.getOrComputeResource(ResourceKey.of(key), k -> val)` |

## Part 3 — Remove CurrentUnitOfWork entirely

`CurrentUnitOfWork.get()` — and the entire `CurrentUnitOfWork` class — is removed in AF5. Any code that relied on
it must be rewritten to receive `ProcessingContext` as a parameter. If this is in a utility class that cannot
easily receive a parameter, pass the `ProcessingContext` through the call chain.

## Gotchas

- **`chain.proceed()` → `chain.proceedSync(context)`** — missing the `context` argument causes a compile error;
  the method no longer exists without it.
- **`ProcessingContext` is NOT `UnitOfWork`** — the AF5 `UnitOfWork` interface still exists (as an implementation
  of `ProcessingContext`) but is not intended for direct user access. Program against `ProcessingContext`.
- **No nesting** — the AF4 UnitOfWork had `parent()` / `root()` for nested message handling. AF5 has no equivalent.
  Code that used nesting for transactional grouping must be redesigned.
- **Correlation data is gone from context** — `UnitOfWork#correlationData()` / `#getCorrelationData()` do not
  exist on `ProcessingContext`. Correlation is handled by the framework automatically.

## Used By

- **[[interceptors]]** — Step 4 (`@MessageHandlerInterceptor` bodies that used `UnitOfWork` lifecycle hooks)
- **[[event-processor]]** — when handler methods reference `CurrentUnitOfWork` or `UnitOfWork`
- **[[saga]]** — referenced by [[interceptor-handler]] for lifecycle hook replacements
