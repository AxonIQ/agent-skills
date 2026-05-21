# @ProcessingGroup → @Namespace (Event Processor Routing)

AF4 grouped event handlers with `@ProcessingGroup("name")`. AF5 renames this to `@Namespace("name")`. The
string value is a binding contract and must match all external references (YAML config, processor definitions).

## Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.config.ProcessingGroup` | `org.axonframework.messaging.core.annotation.Namespace` |

## Detection

```bash
grep -rn 'import org\.axonframework\.config\.ProcessingGroup\|@ProcessingGroup' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

## Axon Framework 4 Code

```java
import org.axonframework.config.ProcessingGroup;

@ProcessingGroup("orders")
@Component
public class OrderProjector {
    // @EventHandler methods...
}
```

## Axon Framework 5 Code

```java
import org.axonframework.messaging.core.annotation.Namespace;

@Namespace("orders")
@Component
public class OrderProjector {
    // @EventHandler methods...
}
```

## Verify external references

After renaming, grep the repository for the **old group string** to find all places that must also be updated:

```bash
grep -rn '"orders"' \
  --include='*.java' --include='*.kt' --include='*.scala' --include='*.yaml' --include='*.properties' .
```

Places to update:
- `application.yaml`: rename the `axon.eventhandling.processors.<name>.*` segment if needed.
- `EventProcessorDefinition.pooledStreaming("orders")` in Spring `@Bean` config.
- `MessagingConfigurer.eventProcessing(…).processor("orders", …)` in native config.

## Notes

- **OpenRewrite Phase 1** usually swaps the annotation but may leave the AF4 import. Always grep for the old import.
- **String case-sensitivity** — `"Orders"` ≠ `"orders"`. YAML key, annotation value, and any processor-definition
  argument must all be identical.
- A **namespace mismatch silently drops all events** at runtime — there is no compile-time signal.
