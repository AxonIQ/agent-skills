# Topic 8 — Command / event message annotations (worked example)

Observable shape:

- Command classes carry `@TargetAggregateIdentifier` on a single field
  (and optionally `@Revision`, `@RoutingKey`).
- Event classes carry no AF4 annotations — they are raw POJOs / records
  / Kotlin data classes.
- The aggregate root has `@AggregateIdentifier` on a field named (for
  example) `bikeId`.

The skill rewrites annotations **in place**; it does **not** convert
between Java POJO / Java record / Kotlin `data class`. The form of the
declaration is preserved.

## Before — Kotlin `data class` (commands and events colocated)

```kotlin
package io.example.bike.coreapi

import org.axonframework.modelling.command.TargetAggregateIdentifier
import org.axonframework.serialization.Revision

data class RegisterBikeCommand(
    @TargetAggregateIdentifier val bikeId: String,
    val bikeType: String,
    val location: String,
)

data class ReturnBikeCommand(
    @TargetAggregateIdentifier val bikeId: String,
    val location: String,
)

@Revision("1.0")
data class BikeRegisteredEvent(val bikeId: String, val bikeType: String, val location: String)

data class BikeReturnedEvent(val bikeId: String, val location: String)
```

## After — Kotlin `data class` (same form, AF5 annotations)

```kotlin
package io.example.bike.coreapi

import org.axonframework.eventsourcing.annotation.EventTag
import org.axonframework.messaging.commandhandling.annotation.Command
import org.axonframework.messaging.eventhandling.annotation.Event
import org.axonframework.modelling.annotation.TargetEntityId

@Command
data class RegisterBikeCommand(
    @TargetEntityId val bikeId: String,
    val bikeType: String,
    val location: String,
)

@Command
data class ReturnBikeCommand(
    @TargetEntityId val bikeId: String,
    val location: String,
)

@Event(version = "1.0")
data class BikeRegisteredEvent(
    @EventTag(key = "Bike") val bikeId: String,
    val bikeType: String,
    val location: String,
)

@Event
data class BikeReturnedEvent(
    @EventTag(key = "Bike") val bikeId: String,
    val location: String,
)
```

## Before — Java POJO command (with `@RoutingKey`)

```java
package io.example.giftcard.coreapi;

import org.axonframework.commandhandling.RoutingKey;
import org.axonframework.modelling.command.TargetAggregateIdentifier;

public class RedeemCardCommand {
    @TargetAggregateIdentifier
    private final String cardId;

    @RoutingKey
    private final String shardKey;

    private final int amount;
    // constructor + getters omitted
}
```

## After — Java POJO command (`@Command(routingKey = "shardKey")`)

```java
package io.example.giftcard.coreapi;

import org.axonframework.messaging.commandhandling.annotation.Command;
import org.axonframework.modelling.annotation.TargetEntityId;

@Command(routingKey = "shardKey")
public class RedeemCardCommand {
    @TargetEntityId
    private final String cardId;

    private final String shardKey;

    private final int amount;
    // constructor + getters omitted
}
```

## Notes

- **Exactly one** `@EventTag` per event class — the field whose name
  matches the AF4 `@AggregateIdentifier` on the root (`bikeId` for a
  `Bike` aggregate, `cardId` for a `GiftCard`).
- The `key` value is the **simple class name** of the aggregate root,
  not the FQN.
- `@Revision("X")` becomes `@Event(version = "X")` (or
  `@Command(version = "X")`). Do not add `name = ...` / `namespace =
  ...` — keep AF4 defaults to preserve `payloadType`-style storage
  (the `messages.adoc` "first migration step" guidance).
- `@RoutingKey` on a field is replaced with the **class-level**
  `@Command(routingKey = "<fieldName>")` attribute. Drop the field-
  level annotation. Note `routingKey` is the **property name**, not a
  qualified field reference.
- For events with no field that obviously maps to the aggregate id
  (e.g. derived ids, summary events): stop and ask the human via
  `AskUserQuestion`. Do not guess which field to tag.
