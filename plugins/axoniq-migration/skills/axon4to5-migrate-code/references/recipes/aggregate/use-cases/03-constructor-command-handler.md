# 03 — Constructor-style `@CommandHandler` (creation via annotated constructor)

**Why this case is interesting:** The AF4 idiom of `public Entity(CreationCommand)` doesn't map 1:1 to AF5. There are three valid AF5 shapes (Patterns 1/2/3 in [aggregates/index.adoc](../../../docs/paths/aggregates/index.adoc) § `@EntityCreator` patterns). Pattern 3 — `@EntityCreator(<OriginEvent>)` — is the smallest behavioural diff for AF4 constructor-style handlers and is the recipe's default when no `@CreationPolicy` was declared. Wrong-pattern compiles cleanly and fails at runtime.

**Apply-condition:** `$SOURCE` has at least one `@CommandHandler` constructor (creation via annotated constructor, not `@CreationPolicy`).

## Before (AF4)

```java
import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.eventsourcing.EventSourcingHandler;
import org.axonframework.modelling.command.AggregateIdentifier;
import org.axonframework.spring.stereotype.Aggregate;
import static org.axonframework.modelling.command.AggregateLifecycle.apply;

@Aggregate
public class Game {

    @AggregateIdentifier
    private String gameIdentifier;
    private int stock;

    @CommandHandler
    public Game(RegisterGameCommand command) {                  // ← creation via annotated constructor
        apply(new GameRegisteredEvent(command.getGameIdentifier(), command.getTitle()));
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
    }

    public Game() { /* required by Axon */ }
}
```

## After (AF5) — Pattern 3 (creation-from-origin-event)

```java
import org.axonframework.eventsourcing.annotation.EventSourcedEntity;
import org.axonframework.eventsourcing.annotation.EventSourcingHandler;
import org.axonframework.eventsourcing.annotation.reflection.EntityCreator;
import org.axonframework.messaging.commandhandling.annotation.CommandHandler;
import org.axonframework.messaging.eventhandling.gateway.EventAppender;

@EventSourcedEntity(tagKey = "Game", idType = String.class)
public class Game {

    private String gameIdentifier;
    private int stock;

    @EntityCreator
    public Game(GameRegisteredEvent event) {                    // ← AF4 ctor → @EntityCreator on the origin event
        this.gameIdentifier = event.gameIdentifier();
        this.stock = 1;
    }

    @CommandHandler
    public static void handle(RegisterGameCommand cmd, EventAppender appender) {   // ← static creation handler
        appender.append(new GameRegisteredEvent(cmd.gameIdentifier(), cmd.title()));
    }

    @CommandHandler
    public void handle(RentGameCommand cmd, EventAppender appender) {
        if (stock <= 0) throw new IllegalStateException("insufficient stock");
        appender.append(new GameRentedEvent(gameIdentifier, cmd.renter()));
    }
}
```

## Alternative AF5 shapes

- **Pattern 1 — no-arg `@EntityCreator`** + instance `@CommandHandler` for the creation command:
  ```java
  @EntityCreator
  public Game() { }                                              // empty entity materialised by framework

  @CommandHandler
  public void handle(RegisterGameCommand cmd, EventAppender appender) {
      if (gameIdentifier != null) throw new IllegalStateException("already registered");
      appender.append(new GameRegisteredEvent(cmd.gameIdentifier(), cmd.title()));
  }
  ```
  Use when the AF4 source had `@CreationPolicy(CREATE_IF_MISSING)` — the framework materialises an empty entity, the instance handler runs, the AF5 `@EventSourcingHandler` then seeds the state.

- **Pattern 2 — identifier-only `@EntityCreator`** + static creation handler:
  ```java
  @EntityCreator
  public Game(@InjectEntityId String gameIdentifier) {
      this.gameIdentifier = gameIdentifier;
  }
  ```
  Less common for AF4 constructor-style migrations; reserved for cases where the identifier is the only seed and the rest of state comes from a single canonical creation event.

## Decision table

| AF4 shape | AF5 shape | Reasoning |
|---|---|---|
| `public Entity(CreationCommand)` (no `@CreationPolicy`) | **Pattern 3** — `@EntityCreator(OriginEvent)` + static `@CommandHandler` factory | Smallest behavioural diff: the creation event still drives state. |
| `@CreationPolicy(ALWAYS) void handle(CreationCommand)` | **Pattern 1** or **Pattern 3** + static `@CommandHandler` | AF5 framework throws `EntityAlreadyExistsForCreationalCommandHandlerException` on collision. |
| `@CreationPolicy(CREATE_IF_MISSING) void handle(...)` | **Pattern 1** — no-arg `@EntityCreator` + instance `@CommandHandler` | The handler runs against a freshly-materialised empty entity. See [aggregates/index.adoc](../../../docs/paths/aggregates/index.adoc) § Removal of `@CreationPolicy`. |
| `@CreationPolicy(NEVER) void handle(...)` (or absent) | Pattern N/A — instance `@CommandHandler` only (no `@EntityCreator` change) | Entity must already exist; default flow. |

## What changed

- AF4 annotated constructor → AF5 **static** `@CommandHandler` factory taking `EventAppender`. The constructor's role (instantiating the entity) is taken over by a separate `@EntityCreator`.
- `@EntityCreator(OriginEvent)` (Pattern 3) replaces the AF4 framework-only no-arg constructor AND the AF4 `@EventSourcingHandler(OriginEvent)` body — both jobs collapse into the AF5 creator constructor. (The original `@EventSourcingHandler(OriginEvent)` can be deleted; its work moves into the `@EntityCreator` body.)
- `AggregateLifecycle.apply(...)` → `appender.append(...)` per usual.

## Caveats

- **No compile-time signal for wrong pattern.** Pattern 1 with a NPE on null state, Pattern 3 with a missing `@EventSourcingHandler(OriginEvent)` body, both compile. Verify by running the entity's tests via `axon4to5-isolatedtest`.
- **Static AF5 creation handler can throw `EntityAlreadyExistsForCreationalCommandHandlerException`** when the entity already exists. If the AF4 source allowed re-registration (rare — usually it threw inside the constructor body), prefer Pattern 1.
- **Pattern 3 + leftover `@EventSourcingHandler(OriginEvent)`** double-seeds the entity. After moving the seeding logic into `@EntityCreator(OriginEvent)`, **delete** the matching `@EventSourcingHandler` to avoid double-mutation when sourcing past events.
- Spring metadata (`@Profile`, `@ExceptionHandler`) on aggregate methods is NOT touched — preserve verbatim. They are Axon / Spring annotations whose imports survive into AF5 unchanged.
