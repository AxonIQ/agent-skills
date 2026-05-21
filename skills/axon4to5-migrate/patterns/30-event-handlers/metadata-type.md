# Metadata Type Change

AF4 `Metadata` implemented `Map<String, Object>` — values were arbitrary objects. AF5 `Metadata` implements
`Map<String, String>` — values are strings only. Code that stored or read non-string metadata values must
be updated to serialize/deserialize to/from `String`.

## Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.messaging.MetaData` | `org.axonframework.messaging.core.Metadata` |

Note the capitalisation change: `MetaData` (AF4) → `Metadata` (AF5).

## Detection

```bash
grep -rn 'org\.axonframework\.messaging\.MetaData\|MetaData\.with\|MetaData\.emptyInstance\|Map<String, Object>' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

## Axon Framework 4 Code

```java
import org.axonframework.messaging.MetaData;

// AF4 — values are Object
MetaData meta = MetaData.with("userId", userId).and("role", role);
Object val = meta.get("userId");        // returns Object
String userId = (String) meta.get("userId");

// As a parameter type
public void dispatch(CreateOrderCommand cmd, MetaData meta) { ... }
```

## Axon Framework 5 Code

```java
import org.axonframework.messaging.core.Metadata;

// AF5 — values are String
Metadata meta = Metadata.from(Map.of("userId", userId.toString(), "role", role.toString()));
String userId = meta.get("userId");     // already String, no cast

// As a parameter type
public void dispatch(CreateOrderCommand cmd, Metadata meta) { ... }
```

## Notes

- **Rename the import and the type** — `MetaData` → `Metadata`.
- **Cast non-string values to `String`** when storing (or use `toString()`).
- **Remove casts when reading** — values are already `String`.
- If you stored serialized objects (JSON, etc.) in metadata, the serialisation contract is unchanged;
  just ensure the stored value is a `String`.
- `MetaData.emptyInstance()` → `Metadata.emptyInstance()` (same method name, new type).
- `MetaData.with(key, value)` → `Metadata.from(Map.of(key, value.toString()))`.
