# 02 — Native Configurer, straight migration (Path B)

**Why this case is interesting:** Path B replaces `@EventSourced` (Spring stereotype) with `@EventSourcedEntity` (framework annotation) AND requires explicit registration through the `EventSourcingConfigurer`. The annotation choice is non-cosmetic: choosing wrong leaves the entity un-registered at startup.

**Apply-condition:** `configuration=native` AND no `@AggregateMember` AND no polymorphism AND no `snapshotTriggerDefinition`.

## Before (AF4)

```java
package io.axoniq.demo.gamerental.command;

import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.eventsourcing.EventSourcingHandler;
import org.axonframework.modelling.command.AggregateIdentifier;
import org.axonframework.spring.stereotype.Aggregate;

import static org.axonframework.modelling.command.AggregateLifecycle.apply;

@Aggregate
class Game {

    @AggregateIdentifier
    private String gameIdentifier;
    private int stock;
    private Set<String> renters;

    @CommandHandler
    public Game(RegisterGameCommand command) {
        apply(new GameRegisteredEvent(command.getGameIdentifier(),
                                      command.getTitle(), command.getReleaseDate(),
                                      command.getDescription(),
                                      command.isSingleplayer(), command.isMultiplayer()));
    }

    @CommandHandler
    public void handle(RentGameCommand command) {
        if (stock <= 0) throw new IllegalStateException("insufficient stock");
        apply(new GameRentedEvent(gameIdentifier, command.getRenter()));
    }

    @EventSourcingHandler
    public void on(GameRegisteredEvent event) {
        this.gameIdentifier = event.getGameIdentifier();
        this.stock = 1;
        this.renters = new HashSet<>();
    }

    @EventSourcingHandler
    public void on(GameRentedEvent event) {
        this.stock--;
        this.renters.add(event.getRenter());
    }

    public Game() { /* Required by Axon */ }
}
```

Plus, somewhere in the bootstrap:

```java
// AF4 — usually via Spring auto-discovery; for the native form:
AggregateConfigurer.defaultConfiguration(Game.class);
```

## After (AF5)

```java
package io.axoniq.demo.gamerental.command;

import org.axonframework.eventsourcing.annotation.EventSourcedEntity;
import org.axonframework.eventsourcing.annotation.EventSourcingHandler;
import org.axonframework.eventsourcing.annotation.reflection.EntityCreator;
import org.axonframework.messaging.commandhandling.annotation.CommandHandler;
import org.axonframework.messaging.eventhandling.gateway.EventAppender;

@EventSourcedEntity(tagKey = "Game", idType = String.class)
public class Game {

    private String gameIdentifier;
    private int stock;
    private Set<String> renters;

    @EntityCreator
    public Game(GameRegisteredEvent event) {            // Pattern 3 — creation-from-origin-event
        this.gameIdentifier = event.gameIdentifier();
        this.stock = 1;
        this.renters = new HashSet<>();
    }

    @CommandHandler
    public static void handle(RegisterGameCommand cmd, EventAppender appender) {
        appender.append(new GameRegisteredEvent(cmd.gameIdentifier(), cmd.title(),
                                                 cmd.releaseDate(), cmd.description(),
                                                 cmd.singleplayer(), cmd.multiplayer()));
    }

    @CommandHandler
    public void handle(RentGameCommand cmd, EventAppender appender) {
        if (stock <= 0) throw new IllegalStateException("insufficient stock");
        appender.append(new GameRentedEvent(gameIdentifier, cmd.renter()));
    }

    @EventSourcingHandler
    public Game on(GameRentedEvent event) {
        this.stock--;
        this.renters.add(event.renter());
        return this;
    }
}
```

Configurer wiring (typically in `*Configuration.java`, `*Application.java`, or `*Bootstrap.java`):

```java
EventSourcingConfigurer.create()
    .registerEntity(EventSourcedEntityModule.autodetected(String.class, Game.class))
    .registerCommandHandlingModule(...)
    .start();
```

## What changed

- `@Aggregate` (Spring stereotype) → `@EventSourcedEntity(tagKey = "Game", idType = String.class)` (framework annotation, `org.axonframework.eventsourcing.annotation.EventSourcedEntity`). NO `.extension.spring.` package here — that's Path A only.
- The annotated constructor `public Game(RegisterGameCommand)` is split:
  - Creation command becomes a **static** `@CommandHandler` factory taking `EventAppender`.
  - A new `@EntityCreator` constructor takes the origin event (`GameRegisteredEvent`) and seeds the state directly. This is Pattern 3 from [aggregates/index.adoc](../../../docs/paths/aggregates/index.adoc) § `@EntityCreator` patterns — the smallest behavioural diff for AF4 constructor-style creation handlers.
- `@AggregateIdentifier` removed; `gameIdentifier` stays plain.
- All `@CommandHandler` / `@EventSourcingHandler` imports move to AF5 packages (`.messaging.` / `.annotation.` infixes).
- `AggregateLifecycle.apply(...)` → `appender.append(...)`; `EventAppender appender` parameter on every `@CommandHandler`.
- AF4 `AggregateConfigurer.defaultConfiguration(Game.class)` → `EventSourcedEntityModule.autodetected(String.class, Game.class)` registered through `configurer.registerEntity(...)`. The first generic parameter (`String.class`) MUST match `idType` on `@EventSourcedEntity`.
- `@ExceptionHandler` on aggregate methods stays as-is — it is an Axon interceptor, not a Spring annotation, and AF5 keeps the import.

## Caveats

- Mixing the two annotations is a classic mistake: do NOT emit `@EventSourced` under `configuration=native`. `@EventSourced` is the Spring stereotype; the framework Configurer only picks up `@EventSourcedEntity`.
- The `idType` first parameter of `EventSourcedEntityModule.autodetected(...)` must match the `idType` on `@EventSourcedEntity`. Mismatch → "no entity registered for id type X" at runtime, not at compile time.
- If the AF4 bootstrap also called `withSubtypes(...)`, you're in polymorphic territory — use case 06.
- If the AF4 bootstrap cannot be located (no `*Configuration.java` / `*Application.java` / `*Bootstrap.java`), emit Blocker `configurer-file-not-found` rather than guessing.
