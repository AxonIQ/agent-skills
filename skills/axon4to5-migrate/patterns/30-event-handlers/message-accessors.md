# Message Accessor Renames

AF4 used JavaBean-style getter methods on `Message` objects (`getPayload()`, `getMetaData()`, etc.). AF5 renames
these to plain property-style accessors without the `get` prefix.

## Import Mappings

| AF4 method | AF5 method |
|-----------|-----------|
| `message.getPayload()` | `message.payload()` |
| `message.getMetaData()` | `message.metaData()` |
| `message.getIdentifier()` | `message.identifier()` |
| `message.getTimestamp()` | `message.timestamp()` |
| `event.getPayloadType()` | `event.payloadType()` |
| `message.getMetaData().get("key")` | `message.metaData().get("key")` |

## Detection

```bash
grep -rn '\.getPayload()\|\.getMetaData()\|\.getIdentifier()\|\.getTimestamp()\|\.getPayloadType()' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

## Axon Framework 4 Code

```java
@MessageHandlerInterceptor
public Object intercept(UnitOfWork<? extends CommandMessage<?>> uow, InterceptorChain chain) {
    Object payload = uow.getMessage().getPayload();
    Map<String, Object> meta = uow.getMessage().getMetaData();
    String id = uow.getMessage().getIdentifier();
    return chain.proceed();
}
```

## Axon Framework 5 Code

```java
@Override
public MessageStream<?> interceptOnHandle(
        CommandMessage message,
        ProcessingContext context,
        MessageHandlerInterceptorChain<CommandMessage> chain) {
    Object payload = message.payload();
    MetaData meta = message.metaData();
    String id = message.identifier();
    return chain.proceed(message, context);
}
```

## Notes

- **`MetaData` type in AF5** — `message.metaData()` returns `org.axonframework.messaging.MetaData` which is a
  `Map<String, Object>`. Non-String values stored as metadata must be stringified (`toString()`) when accessed
  via `@MetadataValue` since the annotation injects `String`.
- **Applies to all `Message` subtypes**: `CommandMessage`, `EventMessage`, `QueryMessage`.
- **Inside `@EventSourcingHandler`**: payload is the event itself (method parameter) — no accessor needed.
- **Inside test lambdas**: `events.get(0).getPayload()` → `(YourEventType) events.get(0).payload()`.
- **OpenRewrite status:** Full — `ChangeMethodName` rules (in `axon4-to-axon5-messaging.yml`) rewrite `getPayload`/`getMetaData`/`getIdentifier`/`getTimestamp`/`getPayloadType` and the `withMetaData`/`andMetaData` siblings.
