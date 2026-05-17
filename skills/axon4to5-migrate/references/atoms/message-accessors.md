---
atom-id: message-accessors
title: "Message accessor renames — getPayload() → payload(), getMetaData() → metaData()"
af4-symbols: ["getPayload()", "getMetaData()", "getIdentifier()", "getPayloadType()", "getTimestamp()", "getResponseType()", "getUpdateResponseType()"]
af5-symbols: ["payload()", "metaData()", "identifier()", "payloadType()", "timestamp()", "responseType()", "updateResponseType()"]
detect: grep -rn '\.getPayload()\|\.getMetaData()\|\.getIdentifier()\|\.getPayloadType()\|\.getTimestamp()' --include='*.java' .
used-by: [event-processor, saga, query-handler, interceptors]
---

# Message Accessor Renames

AF4 used JavaBean-style `get*()` accessors on `Message` implementations. AF5 renamed all of them to remove the
`get` prefix, following modern Java record-style conventions. This is a purely mechanical rename — behaviour is
unchanged.

## Detect

```bash
grep -rn '\.getPayload()\|\.getMetaData()\|\.getIdentifier()\|\.getPayloadType()\|\.getTimestamp()' --include='*.java' .
```

## Rename table

| AF4 (getter) | AF5 (accessor) | Interface |
|---|---|---|
| `message.getPayload()` | `message.payload()` | `Message` |
| `message.getMetaData()` | `message.metaData()` | `Message` |
| `message.getIdentifier()` | `message.identifier()` | `Message` |
| `message.getPayloadType()` | `message.payloadType()` | `Message` |
| `event.getTimestamp()` | `event.timestamp()` | `EventMessage` |
| `query.getResponseType()` | `query.responseType()` | `QueryMessage` |
| `sub.getUpdateResponseType()` | `sub.updateResponseType()` | `SubscriptionQueryMessage` |

## Common locations

- `@EventHandler` method bodies that inspect the event message directly.
- `SequencingPolicy.getSequenceIdentifierFor(EventMessage)` bodies (see [[sequencing-policy]]).
- `MessageHandlerInterceptor` / `@MessageHandlerInterceptor` bodies.
- Test assertions using `.payload()` / `.metaData()` on messages returned by fixtures.
- Lambda expressions inside `eventsSatisfy(events -> …)` in test fixtures.

## Example — EventHandler body

```java
// AF4
@EventHandler
public void on(GenericDomainEventMessage<?> event) {
    String id = event.getAggregateIdentifier();
    Object payload = event.getPayload();
    MetaData meta = event.getMetaData();
}

// AF5
@EventHandler
public void on(GenericDomainEventMessage<?> event) {
    String id = event.aggregateIdentifier();
    Object payload = event.payload();
    Map<String, String> meta = event.metaData();
}
```

## Metadata type change

In AF5, `Metadata` (formerly `MetaData`) is `Map<String, String>` — all values are strings. Code that cast
metadata values to non-String types must be updated to parse strings (e.g., `Integer.parseInt(meta.get("key"))`).

## Gotchas

- **OpenRewrite Phase 1 covers most of these** — grep after Phase 1 to catch any remaining occurrences.
- **`getMetaData()` → `metaData()` (not `getMetadata()`)** — the AF4 name had capital D; the AF5 name has no get
  prefix but retains the lowercase d after the M.
- **`Metadata` type is now `Map<String, String>`** — if the code stored non-String values in metadata (e.g.,
  `Integer`), it will fail at compile time or runtime. Migrate the serialization to/from string at the boundary.
- **Test fixtures** — inside `eventsSatisfy(events -> …)` lambdas, `events.get(0).getPayload()` must become
  `events.get(0).payload()`.

## Used By

- **[[event-processor]]** — common steps 3 (accessor renames inside handler bodies)
- **[[interceptors]]** — Step 2/3 when interceptor body uses `message.getMetaData()` / `message.getPayload()` / `message.andMetaData(...)`
- **[[saga]]** — Step 4 when handler bodies use `event.getPayload()` / `event.getMetaData()`
- **[[sequencing-policy]]** — SequencingPolicy body uses `event.payload()` / `event.metaData()`
- **[[test-fixture]]** — test assertion lambdas
