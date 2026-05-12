# Event-sourced aggregate, Spring Boot → Spring Boot

Observable shape that triggers this variant:

- Class annotated with `@Aggregate` from
  `org.axonframework.spring.stereotype.Aggregate`.
- At least one `@EventSourcingHandler` method on the class.
- Creation command handled by an annotated constructor that calls
  `AggregateLifecycle.apply(...)`.

AF4 source flavor: Spring Boot
AF5 target flavor (`--configuration-mode`): `spring-boot`

## Before (Java)

```java
import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.eventsourcing.EventSourcingHandler;
import org.axonframework.modelling.command.AggregateIdentifier;
import org.axonframework.modelling.command.AggregateCreationPolicy;
import org.axonframework.modelling.command.CreationPolicy;
import org.axonframework.spring.stereotype.Aggregate;

import static org.axonframework.modelling.command.AggregateLifecycle.apply;

@Aggregate(snapshotTriggerDefinition = "bikeSnapshotDefinition")
public class Bike {

    @AggregateIdentifier
    private String bikeId;

    private boolean isAvailable;

    public Bike() {
    }

    @CommandHandler
    @CreationPolicy(AggregateCreationPolicy.ALWAYS)
    public void handle(RegisterBikeCommand command) {
        apply(new BikeRegisteredEvent(command.getBikeId(),
                                      command.getBikeType(),
                                      command.getLocation()));
    }

    @CommandHandler
    public void handle(ReturnBikeCommand command) {
        if (this.isAvailable) {
            throw new IllegalStateException("Bike was already returned");
        }
        apply(new BikeReturnedEvent(command.getBikeId(), command.getLocation()));
    }

    @EventSourcingHandler
    protected void handle(BikeRegisteredEvent event) {
        this.bikeId = event.getBikeId();
        this.isAvailable = true;
    }

    @EventSourcingHandler
    protected void handle(BikeReturnedEvent event) {
        this.isAvailable = true;
    }
}
```

## After (Java)

```java
import org.axonframework.eventsourcing.annotation.EventSourcingHandler;
import org.axonframework.eventsourcing.annotation.reflection.EntityCreator;
import org.axonframework.extension.spring.stereotype.EventSourced;
import org.axonframework.messaging.commandhandling.annotation.CommandHandler;
import org.axonframework.messaging.eventhandling.gateway.EventAppender;

@EventSourced
public class Bike {

    private String bikeId;

    private boolean isAvailable;

    @EntityCreator
    public Bike() {
    }

    @CommandHandler
    public static void handle(RegisterBikeCommand command, EventAppender appender) {
        appender.append(new BikeRegisteredEvent(command.bikeId(),
                                                command.bikeType(),
                                                command.location()));
    }

    @CommandHandler
    public void handle(ReturnBikeCommand command, EventAppender appender) {
        if (this.isAvailable) {
            throw new IllegalStateException("Bike was already returned");
        }
        appender.append(new BikeReturnedEvent(command.bikeId(), command.location()));
    }

    @EventSourcingHandler
    protected void handle(BikeRegisteredEvent event) {
        this.bikeId = event.bikeId();
        this.isAvailable = true;
    }

    @EventSourcingHandler
    protected void handle(BikeReturnedEvent event) {
        this.isAvailable = true;
    }
}
```

## Notes

- The `snapshotTriggerDefinition` attribute on `@Aggregate` was dropped —
  `@EventSourced` does not accept it. The diff summary in step 7 must
  mention this so the human can re-introduce snapshotting separately.
- `@CreationPolicy(ALWAYS)` was removed alongside the move to a static
  creation handler. The static handler naturally implements "fail if
  instance already exists" via `EntityCreator` semantics; behaviorally
  equivalent for `ALWAYS`.
- The constructor stayed no-arg (`@EntityCreator` Pattern 1). The
  identifier is set by the existing `@EventSourcingHandler` for
  `BikeRegisteredEvent`.
- Command payload accessors changed from `command.getBikeId()` to
  `command.bikeId()` because the core-api commands were migrated to
  records in the AF5 sample. That is a **separate** core-api migration
  — this skill must not invent record conversions. If the AF4 commands
  are still POJOs at the time of running this skill, leave the
  `getXxx()` calls intact; downstream skills handle the core-api move.
- Imports `AggregateLifecycle`, `@AggregateIdentifier`, `@CreationPolicy`,
  `AggregateCreationPolicy`, and the static `apply` import are all
  removed.
