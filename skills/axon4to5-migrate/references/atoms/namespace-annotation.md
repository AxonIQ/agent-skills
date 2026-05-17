---
atom-id: namespace-annotation
title: "@ProcessingGroup → @Namespace (class-level event processor grouping)"
af4-symbols: ["@ProcessingGroup", "org.axonframework.config.ProcessingGroup"]
af5-symbols: ["@Namespace", "org.axonframework.messaging.core.annotation.Namespace"]
detect: grep -rn 'import org.axonframework.config.ProcessingGroup\|@ProcessingGroup' --include='*.java' --include='*.kt' --include='*.scala' .
used-by: [event-processor, query-handler]
---

# @ProcessingGroup → @Namespace

AF4 grouped event handlers into a processing group with `@ProcessingGroup("group-name")`. AF5 renames this to
`@Namespace("group-name")`. The string value is a **binding contract** that must match all external references
(YAML config, `EventProcessorDefinition`, `MessagingConfigurer.eventProcessing(…)`).

## Detect

```bash
grep -rn 'import org\.axonframework\.config\.ProcessingGroup\|@ProcessingGroup' --include='*.java' --include='*.kt' --include='*.scala' .
```

## Import change

**Remove:**
```java
import org.axonframework.config.ProcessingGroup;
```

**Add:**
```java
import org.axonframework.messaging.core.annotation.Namespace;
```

## Annotation change

Replace the class-level annotation on every event-handling class:

```java
// AF4
@ProcessingGroup("orders")
public class OrderProjector { … }

// AF5
@Namespace("orders")
public class OrderProjector { … }
```

## String contract — verify external references

After renaming, grep the repository for the **old** group string to find all references that also need updating:

```bash
grep -rn '"orders"' --include='*.java' --include='*.kt' --include='*.scala' --include='*.yaml' --include='*.properties' .
```

References to update:
- `application.yaml`: `axon.eventhandling.processors.orders.*` keys — rename the `orders` segment if needed.
- `EventProcessorDefinition.pooledStreaming("orders")` (Spring Path A wiring).
- `MessagingConfigurer.eventProcessing(…).processor("orders", …)` (native Path B wiring).
- `getModuleConfiguration("EventProcessor[orders]")` in config-reader companions.

⚠️ A mismatch silently drops all events at runtime — there is no compile-time signal.

## Gotchas

- **OpenRewrite Phase 1 usually swaps `@ProcessingGroup` → `@Namespace`** but may leave the AF4 import in place.
  Always grep for the AF4 import after Phase 1.
- **String case-sensitivity** — `"Orders"` ≠ `"orders"`. The YAML key, the annotation value, and the
  `EventProcessorDefinition` argument must all be identical.
- **`@ProcessingGroup` without explicit string** — if the AF4 annotation used the default (empty string or
  class-level package), the string in `@Namespace` must match that implicit value. Check AF4 YAML for
  `axon.eventhandling.processors.<implicit-value>.*` to determine what the effective name was.

## Used By

- **[[event-processor]]** — common steps 1 (always; every event-handling class)
- **[[query-handler]]** — Step 4 (when `@ProcessingGroup` present on the query handler class)
