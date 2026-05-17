---
atom-id: query-handler-annotation
title: "@QueryHandler import move: org.axonframework.queryhandling → messaging.queryhandling.annotation"
af4-symbols: ["org.axonframework.queryhandling.QueryHandler"]
af5-symbols: ["org.axonframework.messaging.queryhandling.annotation.QueryHandler"]
detect: grep -rn 'import org.axonframework.queryhandling.QueryHandler' --include='*.java' .
used-by: [query-handler]
---

# @QueryHandler Import Package Move

AF4 placed `@QueryHandler` in `org.axonframework.queryhandling`. AF5 moves it to
`org.axonframework.messaging.queryhandling.annotation`.

## Transform

```java
// AF4
import org.axonframework.queryhandling.QueryHandler;

// AF5
import org.axonframework.messaging.queryhandling.annotation.QueryHandler;
```

The annotation and its usage are unchanged. Only the package moves.

## Gotchas

- **No behavioral change** — import swap only. `@QueryHandler` still marks handler methods.
- **`queryName` attribute is a separate concern** — handled by [[query-payload-record]] atom.
- **Partial migration** — if `org.axonframework.messaging.queryhandling.annotation.QueryHandler` is already present and the AF4 form is absent, this atom is a no-op.

## Used By

- **[[query-handler]]** — Step 1 (always)
