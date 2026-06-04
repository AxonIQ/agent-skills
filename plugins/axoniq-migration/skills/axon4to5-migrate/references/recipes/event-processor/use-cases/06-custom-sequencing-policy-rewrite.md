# 06 — Custom `SequencingPolicy` rewrite

**Why this case is interesting:** Built-in policies (`MetadataSequencingPolicy`, `SequentialPerAggregatePolicy`, etc.) cover most projects, but some need a class-level custom policy that derives the sequence id from event payload + metadata. The interface, method signature, return wrapping, and accessor names all change. Wrong-shaped migration compiles cleanly under generics but returns wrong sequence ids — events get out-of-order or wrongly serialised at the processor level.

**Apply-condition:** scope contains a class implementing the AF4 `SequencingPolicy<EventMessage<?>>` interface that `$SOURCE` depends on.

## Before (AF4)

```java
package com.dddheroes.heroesofddd.shared.sequencing;

import com.dddheroes.heroesofddd.shared.metadata.GameMetaData;
import org.axonframework.eventhandling.EventMessage;
import org.axonframework.eventhandling.async.SequencingPolicy;

public class TenantAndGameSequencingPolicy implements SequencingPolicy<EventMessage<?>> {

    @Override
    public Object getSequenceIdentifierFor(EventMessage<?> event) {
        String tenant = (String) event.getMetaData().get(GameMetaData.TENANT_KEY);
        String gameId = (String) event.getMetaData().get(GameMetaData.GAME_ID_KEY);
        if (tenant == null || gameId == null) {
            return null;   // full-concurrency fallback
        }
        return tenant + ":" + gameId;
    }
}
```

The policy is registered via `EventProcessingConfigurer.assignSequencingPolicy("MyProcessor", c -> c.getComponent(TenantAndGameSequencingPolicy.class))` or as a `@Bean` referenced from YAML.

## After (AF5)

```java
package com.dddheroes.heroesofddd.shared.sequencing;

import com.dddheroes.heroesofddd.shared.metadata.GameMetaData;
import org.axonframework.messaging.core.ProcessingContext;
import org.axonframework.messaging.core.sequencing.SequencingPolicy;
import org.axonframework.messaging.eventhandling.EventMessage;

import java.util.Optional;

public class TenantAndGameSequencingPolicy implements SequencingPolicy {

    @Override
    public Optional<Object> sequenceIdentifierFor(EventMessage message, ProcessingContext context) {
        String tenant = (String) message.metaData().get(GameMetaData.TENANT_KEY);
        String gameId = (String) message.metaData().get(GameMetaData.GAME_ID_KEY);
        if (tenant == null || gameId == null) {
            return Optional.empty();   // full-concurrency fallback
        }
        return Optional.of(tenant + ":" + gameId);
    }
}
```

Class registration via the projector:

```java
@Component
@Namespace("MyProcessor")
@SequencingPolicy(type = TenantAndGameSequencingPolicy.class)
public class MyProjector { … }
```

## What changed

- **Interface swap**: `org.axonframework.eventhandling.async.SequencingPolicy` → `org.axonframework.messaging.core.sequencing.SequencingPolicy`. The generic parameter (`<EventMessage<?>>`) is GONE — AF5 binds the message type via reflection at registration time.
- **Method rename + signature change**:
  - Name: `getSequenceIdentifierFor` → `sequenceIdentifierFor`.
  - Argument list: AF4 took one `EventMessage<?>` parameter; AF5 takes `EventMessage message, ProcessingContext context`. The context is bound by the framework — usually ignored inside the policy body.
  - Return type: `Object` → `Optional<Object>`.
- **Accessor renames** inside the body:
  - `event.getPayload()` → `message.payload()`.
  - `event.getMetaData()` → `message.metaData()`.
- **Return wrapping**: `return value;` → `return Optional.of(value);`; `return null;` → `return Optional.empty();`. Returning bare `null` from `Optional<Object>` compiles but throws NPE downstream at processor scheduling.
- **`EventMessage` import**: `org.axonframework.eventhandling.EventMessage` → `org.axonframework.messaging.eventhandling.EventMessage`. (Same simple name; only the package changed.)
- **Registration**: from `assignSequencingPolicy(...)` / YAML to class-level `@SequencingPolicy(type = TenantAndGameSequencingPolicy.class)` on the projector. The custom policy class itself is referenced by `type = ...`; there is no `parameters = "..."` for custom policies (only built-in policies like `MetadataSequencingPolicy` use `parameters`).

## Caveats

- **`Object` → `Optional<Object>` is the silent regression.** A naive "rename + recompile" that keeps `return null` compiles cleanly because `null` is assignable to `Optional<Object>`. The processor scheduler then NPEs at runtime. Always grep the rewritten policy for `return null` and replace with `Optional.empty()`.
- **The `ProcessingContext context` parameter is rarely used.** Most custom policies ignore it. AF5 exposes it for advanced cases (e.g. "sequence by current request id from the context"), but if the AF4 body didn't need it, the AF5 body doesn't either.
- **`message.payload()` is now a record-style accessor** returning the event payload type directly, not wrapped in `EventMessage.getPayload()`. Existing casts like `(MyEvent) event.getPayload()` become `(MyEvent) message.payload()`.
- **The generic parameter on the interface is gone**, but the parameter on the policy method is preserved as `EventMessage` (also without `<?>` in AF5 — `Message` and its subtypes are non-generic). If a project has `SequencingPolicy<DomainEvent>` (custom narrowing), the AF5 form drops the narrowing and the policy body must cast `message.payload()` explicitly.
- **Class-level annotation registration** (`@SequencingPolicy(type = TenantAndGameSequencingPolicy.class)`) is the AF5 preferred form. The AF4 `assignSequencingPolicy(...)` API is gone; do NOT carry it over.
