# MessageDispatchInterceptor — handle(List) → interceptOnDispatch

AF4 dispatch interceptors processed messages in a batch: `handle(List<? extends M>)` returned a
`BiFunction<Integer, M, M>` applied per message. AF5 changes to single-message: `interceptOnDispatch`
receives one message, modifies it inline, and delegates to the chain.

## Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.messaging.MessageDispatchInterceptor` | `org.axonframework.messaging.core.MessageDispatchInterceptor` |
| `java.util.List` | *(remove)* |
| `java.util.function.BiFunction` | *(remove)* |
| — | `org.axonframework.messaging.core.MessageDispatchInterceptorChain` |
| — | `org.axonframework.messaging.core.MessageStream` |
| — | `org.axonframework.messaging.core.unitofwork.ProcessingContext` |

## Detection

**Pre-migration (AF4 original):**

```bash
grep -rn 'implements MessageDispatchInterceptor\|BiFunction.*handle.*List' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

**Post-OpenRewrite (partial AF5 shape):**

```bash
# Signature rewritten by MigrateMessageInterceptorSignatures, body left alone.
# OR injects a `// TODO #LLM` class-level comment pointing at the migration doc.
grep -rn 'interceptOnDispatch\|// TODO #LLM' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

Use the AF4 grep during Step 2 Assessment to scope the work. Use the post-OR grep during Step 4 Validate when the compile loop points at this pattern.

## Axon Framework 4 Code

```java
import java.util.List;
import java.util.function.BiFunction;
import org.axonframework.messaging.MessageDispatchInterceptor;

public class MyDispatchInterceptor implements MessageDispatchInterceptor<CommandMessage<?>> {

    @Override
    public BiFunction<Integer, CommandMessage<?>, CommandMessage<?>> handle(
            List<? extends CommandMessage<?>> messages) {
        return (index, message) -> {
            // modify message
            return GenericCommandMessage.asCommandMessage(message.getPayload())
                .withMetaData(message.getMetaData().and("extra", "value"));
        };
    }
}
```

## Axon Framework 5 Code

```java
import org.axonframework.messaging.core.MessageDispatchInterceptor;
import org.axonframework.messaging.core.MessageDispatchInterceptorChain;
import org.axonframework.messaging.core.MessageStream;
import org.axonframework.messaging.core.unitofwork.ProcessingContext;
import org.jspecify.annotations.Nullable;

public class MyDispatchInterceptor implements MessageDispatchInterceptor<CommandMessage> {

    @Override
    public MessageStream<?> interceptOnDispatch(
            CommandMessage message,
            @Nullable ProcessingContext context,
            MessageDispatchInterceptorChain<CommandMessage> chain) {
        CommandMessage modified = message.withMetadata(
            message.metadata().andWith("extra", "value")
        );
        return chain.proceed(modified, context);
    }
}
```

## Notes

- **Generic type loses wildcard** — `CommandMessage<?>` → `CommandMessage` (no wildcard).
- **Method name change** — `handle` → `interceptOnDispatch`.
- **Return type change** — `BiFunction<Integer, M, M>` → `MessageStream<?>`.
- **Always call `chain.proceed(modified, context)`** at the end — returning without calling it drops the message.
- **OpenRewrite status:** Partial — `ChangeType` moves the interface to `messaging.core.MessageDispatchInterceptor` and `MigrateMessageInterceptorSignatures` rewrites the method signature; AI rewrites the body (single-message processing, `chain.proceed(modified, context)`).
