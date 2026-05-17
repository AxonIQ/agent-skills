---
atom-id: saga-annotation
title: "@Saga → @Component @DisallowReplay class-level annotation swap"
af4-symbols: ["@Saga", "org.axonframework.spring.stereotype.Saga", "org.axonframework.extension.spring.stereotype.Saga"]
af5-symbols: ["@Component", "@DisallowReplay", "org.axonframework.messaging.eventhandling.replay.annotation.DisallowReplay"]
detect: grep -rn '@Saga\|stereotype.*Saga' --include='*.java' --include='*.kt' --include='*.scala' .
used-by: [saga]
---

# @Saga → @Component @DisallowReplay

AF5 removed the Saga SPI entirely. The `@Saga` class annotation is replaced by `@Component @DisallowReplay`.

## Why @DisallowReplay is mandatory

Without `@DisallowReplay`, a full event replay re-fires every `@EventHandler` on the migrated component and
creates duplicate JPA state rows. `@DisallowReplay` blocks the processor during replay — only live events
build state.

## Transform

**Remove:**
```java
// either of these AF4 import paths — grep for both
import org.axonframework.spring.stereotype.Saga;
import org.axonframework.extension.spring.stereotype.Saga;

@Saga
public class PaymentSaga {
```

**Replace with:**
```java
import org.springframework.stereotype.Component;
import org.axonframework.messaging.eventhandling.replay.annotation.DisallowReplay;

@Component
@DisallowReplay
public class PaymentSaga {
```

## AF4 @Saga import paths (both must be removed)

- `org.axonframework.spring.stereotype.Saga` (older integration module)
- `org.axonframework.extension.spring.stereotype.Saga` (newer Extension model)

## Gotchas

- **Both import paths must be removed** — grep for both; if both are present, remove both.
- **`@Autowired` on fields** — AF4 `@Saga` commonly used `@Autowired` field injection. Remove `@Autowired` from `CommandGateway` / `DeadlineManager` fields here; constructor injection follows in the saga recipe Step 6.
- **No `@Namespace` for sagas** — sagas are NOT event processors; they do not get `@ProcessingGroup` → `@Namespace` treatment. Never add `@Namespace` to a saga class.

## Used By

- **[[saga]]** — Step 1 (always)
