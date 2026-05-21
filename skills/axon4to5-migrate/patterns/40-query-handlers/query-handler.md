# @QueryHandler — Import Package Move

The `@QueryHandler` annotation moved to a new package in AF5. The annotation's behavior and method signatures
are unchanged.

## Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.queryhandling.QueryHandler` | `org.axonframework.messaging.queryhandling.annotation.QueryHandler` |
| `org.axonframework.queryhandling.QueryUpdateEmitter` | `org.axonframework.messaging.queryhandling.QueryUpdateEmitter` |

## Detection

```bash
grep -rn 'import org\.axonframework\.queryhandling\.QueryHandler' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

## Axon Framework 4 Code

```java
import org.axonframework.queryhandling.QueryHandler;

@Component
public class OrderQueryHandler {

    @QueryHandler
    public OrderView handle(GetOrderByIdQuery query) {
        return repository.findById(query.orderId()).orElse(null);
    }

    @QueryHandler
    public List<OrderView> handle(GetAllOrdersQuery query) {
        return repository.findAll();
    }
}
```

## Axon Framework 5 Code

```java
import org.axonframework.messaging.queryhandling.annotation.QueryHandler;

@Component
public class OrderQueryHandler {

    @QueryHandler
    public OrderView handle(GetOrderByIdQuery query) {
        return repository.findById(query.orderId()).orElse(null);
    }

    @QueryHandler
    public List<OrderView> handle(GetAllOrdersQuery query) {
        return repository.findAll();
    }
}
```

## Notes

- **Only the import changes** — annotation name, attributes, and method signatures are identical.
- **`@QueryHandler(queryName = "…")` pattern**: if any handler used `queryName` to decouple the handler from a
  specific query class, this must be migrated to a `@Query`-annotated payload record — see the `query-payload-record`
  atom in `references/atoms/`.
- **`QueryUpdateEmitter`** import also changes — see the `query-update-emitter` atom in `references/atoms/`.
