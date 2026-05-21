# MessageHandlerInterceptor — Handle Method Signature Migration

AF4 handler interceptors implemented `MessageHandlerInterceptor<M>` with a `handle(UnitOfWork, InterceptorChain)`
method. AF5 replaces this with `interceptOnHandle(M, ProcessingContext, MessageHandlerInterceptorChain<M>)`.
The chain call changes from no-arg `chain.proceed()` to `chain.proceed(message, context)`.

## Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.messaging.unitofwork.UnitOfWork` | *(remove)* |
| `org.axonframework.messaging.InterceptorChain` | *(remove)* |
| `org.axonframework.messaging.MessageHandlerInterceptor` | `org.axonframework.messaging.core.MessageHandlerInterceptor` |
| — | `org.axonframework.messaging.core.MessageHandlerInterceptorChain` |
| — | `org.axonframework.messaging.core.MessageStream` |
| — | `org.axonframework.messaging.core.unitofwork.ProcessingContext` |

## Detection

```bash
grep -rn 'implements MessageHandlerInterceptor\|UnitOfWork.*InterceptorChain\|InterceptorChain.*UnitOfWork' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

## Axon Framework 4 Code

```java
import org.axonframework.messaging.MessageHandlerInterceptor;
import org.axonframework.messaging.unitofwork.UnitOfWork;
import org.axonframework.messaging.InterceptorChain;

public class AuthInterceptor implements MessageHandlerInterceptor<CommandMessage<?>> {

    @Override
    public Object handle(
            @Nonnull UnitOfWork<? extends CommandMessage<?>> unitOfWork,
            @Nonnull InterceptorChain interceptorChain) throws Exception {
        CommandMessage<?> cmd = unitOfWork.getMessage();
        String playerId = (String) cmd.getMetaData().get("playerId");
        validate(playerId);
        return interceptorChain.proceed();
    }
}
```

## Axon Framework 5 Code

```java
import org.axonframework.messaging.core.MessageHandlerInterceptor;
import org.axonframework.messaging.core.MessageHandlerInterceptorChain;
import org.axonframework.messaging.core.MessageStream;
import org.axonframework.messaging.core.unitofwork.ProcessingContext;

public class AuthInterceptor implements MessageHandlerInterceptor<CommandMessage> {

    @Override
    public @NonNull MessageStream<?> interceptOnHandle(
            @NonNull CommandMessage message,
            @NonNull ProcessingContext context,
            @NonNull MessageHandlerInterceptorChain<CommandMessage> chain) {
        String playerId = (String) message.metaData().get("playerId");
        validate(playerId);
        return chain.proceed(message, context);
    }
}
```

## Dispatching commands from within an interceptor (AF5)

Instead of loading aggregates via `Repository`, use `CommandDispatcher.forContext(context)`:

```java
// AF4 — loading aggregate directly
Repository<ResourcesPool> repo = ...;
repo.loadOrCreate(id, () -> new ResourcesPool(id))
    .execute(rp -> rp.handle(cmd));

// AF5 — dispatch via CommandDispatcher bound to the current ProcessingContext
CommandDispatcher.forContext(context)
    .send(withdrawCommand)
    .resultAs(Void.class)
    .join();
```

## Key changes

| Element | AF4 | AF5 |
|---------|-----|-----|
| Method name | `handle` | `interceptOnHandle` |
| Parameters | `UnitOfWork<? extends M>, InterceptorChain` | `M, ProcessingContext, MessageHandlerInterceptorChain<M>` |
| Return type | `Object` | `MessageStream<?>` |
| Chain call | `interceptorChain.proceed()` | `chain.proceed(message, context)` |
| Generic bound | `CommandMessage<?>` | `CommandMessage` (no wildcard) |
| Checked exceptions | `throws Exception` | removed |
| Access message | `unitOfWork.getMessage()` | use `message` parameter directly |

## UnitOfWork lifecycle hook replacements

| AF4 | AF5 |
|-----|-----|
| `unitOfWork.onCommit(uow -> {…})` | `context.runOnAfterCommit(ctx -> {…})` |
| `unitOfWork.onPrepareCommit(uow -> {…})` | `context.runOnPreInvocation(ctx -> {…})` |
| `unitOfWork.onRollback(uow -> {…})` | `context.onError((ctx, err) -> {…})` |
| `unitOfWork.onCleanup(uow -> {…})` | `context.doFinally(ctx -> {…})` |

## Notes

- **`chain.proceed()` → `chain.proceed(message, context)`** — must pass both arguments. Zero-arg form does not exist.
- **Generic de-wildcard is mandatory** — `CommandMessage<?>` → `CommandMessage`. Wildcard causes a compile error.
- **`throws Exception` removed** — the AF5 signature does not declare checked exceptions.
- **`ProcessingContext` is not `@Nullable`** here — always present during handling.
