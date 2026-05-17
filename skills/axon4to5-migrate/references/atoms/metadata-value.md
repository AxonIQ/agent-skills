---
atom-id: metadata-value
title: "@MetaDataValue (AF4) → @MetadataValue (AF5) — casing + package change"
af4-symbols: ["@MetaDataValue", "org.axonframework.messaging.annotation.MetaDataValue"]
af5-symbols: ["@MetadataValue", "org.axonframework.messaging.core.annotation.MetadataValue"]
detect: grep -rn 'MetaDataValue' --include='*.java' .
used-by: [event-processor, query-handler]
---

# @MetaDataValue → @MetadataValue

The annotation for extracting metadata values from message headers changed its **name**, **casing**, and **package**.

| | AF4 | AF5 |
|---|---|---|
| Annotation name | `@MetaDataValue` | `@MetadataValue` |
| Import | `org.axonframework.messaging.annotation.MetaDataValue` | `org.axonframework.messaging.core.annotation.MetadataValue` |

⚠️ Both changes **compile silently** if only one is applied. A stale `@MetaDataValue` annotation compiles against
an AF4 jar but will fail against AF5. An `@MetadataValue` annotation that references the wrong (AF4) import will
also compile in mixed-jar setups but silently receive `null` at runtime.

## Detect

```bash
# Find any occurrence of the old casing (capital D)
grep -rn 'MetaDataValue' --include='*.java' .
```

## Transform

**Remove:**
```java
import org.axonframework.messaging.annotation.MetaDataValue;

// on parameter:
public void on(OrderCreatedEvent event, @MetaDataValue("correlationId") String correlationId) { … }
```

**Add:**
```java
import org.axonframework.messaging.core.annotation.MetadataValue;

// on parameter:
public void on(OrderCreatedEvent event, @MetadataValue("correlationId") String correlationId) { … }
```

Note the casing: `MetaData` (capital D) → `Metadata` (lowercase d after the capital M).

## Verify after migration

```bash
# Confirm zero AF4 occurrences remain (capital-D form)
grep -rn 'MetaDataValue' --include='*.java' .
# Should return no results
```

## Gotchas

- **Both the symbol AND the import must change** — applying only the import change leaves the old `@MetaDataValue`
  symbol unresolved; applying only the annotation rename without the import change causes a runtime null injection.
- **Case matters in the annotation name** — `@MetadataValue` has lowercase `d`; `@MetaDataValue` has uppercase `D`.
  The IDE may not flag this as an error if both are on the classpath during migration.
- **OpenRewrite Phase 1 often leaves `@MetaDataValue` unchanged** — it is not part of the standard OpenRewrite
  recipe for AF4→AF5. Always grep after Phase 1.

## Used By

- **[[event-processor]]** — Step 5 (when `@MetaDataValue` is used on handler parameters)
- **[[query-handler]]** — Step 5 (when `@MetaDataValue` is used on query handler parameters)
