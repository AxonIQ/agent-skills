# QueryUpdateEmitter — Constructor Field → Method Parameter

AF4 injected `QueryUpdateEmitter` as a constructor field. AF5 enforces method-level injection — the emitter
becomes a parameter on each `@EventHandler` that calls it. The `emit()` signature gains a `Class<Q>` first
argument.

## Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.queryhandling.QueryUpdateEmitter` | `org.axonframework.messaging.queryhandling.QueryUpdateEmitter` |

## Detection

**Pre-migration (AF4 original):**

```bash
grep -rn 'QueryUpdateEmitter' --include='*.java' --include='*.kt' --include='*.scala' .
```

**Post-OpenRewrite (partial AF5 shape):**

```bash
# Import moved by ChangePackage, but field/constructor injection still present
# AI moves it to a method parameter and adds Class<Q> arg to emit(...).
grep -rn 'private.*QueryUpdateEmitter\|QueryUpdateEmitter\s\+[a-z][A-Za-z0-9_]*\s*[;,)]\|\.emit\s*(' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

Use the AF4 grep during Step 2 Assessment to scope the work. Use the post-OR grep during Step 4 Validate when the compile loop points at this pattern.

## Axon Framework 4 Code

```java
import org.axonframework.queryhandling.QueryUpdateEmitter;

@ProcessingGroup("queries")
@Component
public class OrderProjection {

    private final QueryUpdateEmitter updateEmitter;

    public OrderProjection(QueryUpdateEmitter updateEmitter) {
        this.updateEmitter = updateEmitter;
    }

    @EventHandler
    public void on(OrderPlacedEvent event) {
        updateEmitter.emit(q -> true, new OrderDto(event));
    }
}
```

## Axon Framework 5 Code

```java
import org.axonframework.messaging.queryhandling.QueryUpdateEmitter;

@Namespace("queries")
@Component
public class OrderProjection {

    // No QueryUpdateEmitter field or constructor parameter

    @EventHandler
    public void on(OrderPlacedEvent event, QueryUpdateEmitter updateEmitter) {
        updateEmitter.emit(GetOrderQuery.class, q -> true, new OrderDto(event));
    }
}
```

## emit() signature change

| AF4 | AF5 |
|-----|-----|
| `emit(predicate, update)` | `emit(QueryClass.class, predicate, update)` |

The query class is the first argument — it matches the `@QueryHandler` first parameter type.

## Notes

- **Remove the constructor field and injection entirely** — do not keep both.
- **Add `QueryUpdateEmitter` as a parameter** to every `@EventHandler` that calls `emit(…)`.
- **The query class argument is required** — `emit(q -> true, dto)` does not compile in AF5.
- **OpenRewrite status:** Partial — `ChangePackage` (in `axon4-to-axon5-messaging.yml`) moves `QueryUpdateEmitter` to `messaging.queryhandling`; AI converts the constructor field to a method parameter and adds the `Class<Q>` first argument to `emit(...)`.
