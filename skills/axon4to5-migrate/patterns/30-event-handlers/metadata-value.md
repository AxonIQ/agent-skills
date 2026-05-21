# @MetaDataValue → @MetadataValue

AF4 used `@MetaDataValue` (capital D) from `org.axonframework.messaging.annotation.MetaDataValue`. AF5 renames
it to `@MetadataValue` (lowercase d) and moves it to a new package.

## Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.messaging.annotation.MetaDataValue` | `org.axonframework.messaging.core.annotation.MetadataValue` |

## Detection

```bash
grep -rn '@MetaDataValue\|import.*MetaDataValue' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

## Axon Framework 4 Code

```java
import org.axonframework.messaging.annotation.MetaDataValue;

@EventHandler
public void on(OrderCreatedEvent event,
               @MetaDataValue("gameId") String gameId,
               @MetaDataValue("playerId") String playerId) {
    // handle
}
```

## Axon Framework 5 Code

```java
import org.axonframework.messaging.core.annotation.MetadataValue;

@EventHandler
public void on(OrderCreatedEvent event,
               @MetadataValue("gameId") String gameId,
               @MetadataValue("playerId") String playerId) {
    // handle
}
```

## Notes

- **Both the annotation name and the import change**: `MetaDataValue` → `MetadataValue` (capital D → lowercase d).
- **Package changes**: `messaging.annotation` → `messaging.core.annotation`.
- **String key is unchanged** — the metadata key string stays the same.
- This annotation is used in `@EventHandler`, `@CommandHandler`, `@QueryHandler` methods, and interceptors —
  update it everywhere.
