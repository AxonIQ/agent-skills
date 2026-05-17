---
atom-id: query-update-emitter
title: "QueryUpdateEmitter: constructor field → method param; emit() 2-arg → 3-arg (class + predicate + update)"
af4-symbols: ["QueryUpdateEmitter", "org.axonframework.queryhandling.QueryUpdateEmitter", "updateEmitter.emit(predicate, update)"]
af5-symbols: ["org.axonframework.messaging.queryhandling.QueryUpdateEmitter", "emit(QueryClass.class, predicate, update)"]
detect: grep -rn 'QueryUpdateEmitter' --include='*.java' --include='*.kt' --include='*.scala' .
used-by: [query-handler]
---

# QueryUpdateEmitter: Constructor Field → Method Parameter

AF4 injected `QueryUpdateEmitter` as a constructor field. AF5 enforces method-level injection — the emitter
becomes a parameter on each `@EventHandler` method that calls it. The `emit()` signature also gains a
`Class<Q>` first argument.

## Part 1 — Remove constructor field; add method parameter

**Remove:**
```java
// AF4
public class OrderProjection {
    private final QueryUpdateEmitter updateEmitter;

    public OrderProjection(QueryUpdateEmitter updateEmitter) {
        this.updateEmitter = updateEmitter;
    }
}
```

**Replace with (field + constructor param removed):**
```java
// AF5
public class OrderProjection {
    // No QueryUpdateEmitter field
}
```

Add `QueryUpdateEmitter updateEmitter` as a parameter to each `@EventHandler` that calls `updateEmitter.*`:

```java
// AF4
@EventHandler
public void on(OrderPlacedEvent event) {
    updateEmitter.emit(q -> true, orderDto);
}

// AF5
@EventHandler
public void on(OrderPlacedEvent event, QueryUpdateEmitter updateEmitter) {
    updateEmitter.emit(GetOrderQuery.class, q -> true, orderDto);
}
```

## Part 2 — emit() 2-arg → 3-arg

AF5 `emit()` requires the query class as the first argument:

| AF4 | AF5 |
|-----|-----|
| `emit(predicate, update)` | `emit(QueryClass.class, predicate, update)` |
| `emit(q -> "findAll".equals(q.getQueryName()), update)` | `emit(FindAllQuery.class, q -> true, update)` |

**Predicate type change** — AF4 predicate received `QueryMessage<Q, ?>` (envelope). AF5 predicate receives `Q`
(payload directly). `q.getQueryName()` no longer exists on the predicate argument.

## Import changes

Remove: `org.axonframework.queryhandling.QueryUpdateEmitter`
Add: `org.axonframework.messaging.queryhandling.QueryUpdateEmitter`

Also fix `@EventHandler` import on **touched methods only** (do not migrate untouched `@EventHandler` methods):
- Remove: `org.axonframework.eventhandling.EventHandler`
- Add: `org.axonframework.messaging.eventhandling.annotation.EventHandler`

## Gotchas

- **`emit(String.class, predicate, update)` was an AF4 named-query workaround** — replace `String.class` with the `@Query`-annotated payload record (e.g., `emit(FindByIdQuery.class, q -> q.id().equals(id), update)`).
- **Predicate type changes** — update any predicate that accessed `q.getQueryName()` or `q.getPayload()`.
- **Fix `@EventHandler` only on touched methods** — the event-processor recipe owns untouched `@EventHandler` imports.
- **Field injection is unsupported in AF5** — the framework will not inject `QueryUpdateEmitter` at the field level.

## Used By

- **[[query-handler]]** — Step 3 (when `QueryUpdateEmitter` is constructor-injected)
