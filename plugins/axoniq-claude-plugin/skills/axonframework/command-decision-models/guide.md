# Command Decision Models (DCB) in Axon Framework 5

Many commands need to consult past state before deciding whether to accept or reject. The traditional answer is an aggregate. AF5 offers a more precise alternative: **scope the state to what the command actually needs to decide**.

> **Start here, not with aggregates.** An aggregate loads everything ever recorded for an identity. A decision model loads only the events that are relevant to this specific decision — nothing more.

---

## The Pattern in One Sentence

For each command, define: *(1) which past events are relevant*, *(2) what minimal state to fold them into*, and *(3) what new event(s) to emit if the decision is valid* — then let the event store enforce that no conflicting write happened concurrently.

---

## Step 1 — Tag your events

Tags are key-value pairs stored with each event. They are the lookup vocabulary for sourcing state later. Declare them by annotating fields (or methods) on your event payload with `@EventTag`:

```java
import org.axonframework.eventsourcing.annotation.EventTag;

record CourseCreated(
        @EventTag(key = "course") String courseId,   // stored as Tag("course", courseId)
        String name,
        int capacity
) {}

record StudentEnrolled(
        @EventTag(key = "course") String courseId,
        @EventTag(key = "student") String studentId
) {}
```

The tag key is what you filter by when sourcing. Choose keys that are stable and meaningful across all events in the same decision boundary.

---

## Step 2 — Define a minimal decision state

The decision state is a plain value object. It holds only what the command needs to decide. Model it as a record or a class with explicit `apply` methods:

```java
import org.axonframework.messaging.eventhandling.EventMessage;

// State needed to decide "EnrollStudent": current enrolment count and whether this student is already in
record EnrolmentState(int enrolled, int capacity, boolean studentAlreadyEnrolled) {

    static EnrolmentState empty() {
        return new EnrolmentState(0, 0, false);
    }

    EnrolmentState apply(EventMessage<?> event, String studentId) {
        // Switch on the message type name — do NOT switch on event.payload(), which returns
        // byte[] in distributed setups. The type name equals ClassName.class.getName() by default.
        // Use payloadAs(SomeClass.class) to deserialize once the type is known;
        // pass a Converter as a second argument if custom deserialization is needed.
        return switch (event.type().name()) {
            case "com.example.CourseCreated" -> {
                var e = event.payloadAs(CourseCreated.class);
                yield new EnrolmentState(0, e.capacity(), false);
            }
            case "com.example.StudentEnrolled" -> {
                var e = event.payloadAs(StudentEnrolled.class);
                yield new EnrolmentState(
                        enrolled + 1,
                        capacity,
                        studentAlreadyEnrolled || e.studentId().equals(studentId));
            }
            default -> this;
        };
    }
}
```

Keep it small. If you find yourself adding fields "just in case", they probably belong in a different decision model.

---

## Step 3 — Source, decide, append

Wire the decision model into a command handler using `EventStoreTransaction`. The transaction tracks what you sourced and enforces consistency at commit time.

```java
import org.axonframework.eventsourcing.eventstore.EventStore;
import org.axonframework.eventsourcing.eventstore.SourcingCondition;
import org.axonframework.messaging.eventstreaming.EventCriteria;

class EnrolmentCommandHandler {

    private final EventStore eventStore;

    EnrolmentCommandHandler(EventStore eventStore) {
        this.eventStore = eventStore;
    }

    @CommandHandler
    void handle(EnrollStudent command, ProcessingContext context, EventAppender events) {
        var tx = eventStore.transaction(context);

        // 1. Declare what events are relevant to this decision
        var criteria = EventCriteria.havingTags("course", command.courseId());

        // 2. Source those events and fold into decision state
        var state = tx.source(SourcingCondition.conditionFor(criteria))
                      .reduce(EnrolmentState.empty(),
                              (s, entry) -> s.apply(entry.message(), command.studentId()))
                      .orTimeout(30, TimeUnit.SECONDS)
                      .join();

        // 3. Apply business rules
        if (state.studentAlreadyEnrolled()) {
            throw new DuplicateEnrolmentException(command.studentId(), command.courseId());
        }
        if (state.enrolled() >= state.capacity()) {
            throw new CourseFullException(command.courseId());
        }

        // 4. Append the result — the transaction enforces no concurrent conflict on 'criteria'
        events.append(new StudentEnrolled(command.courseId(), command.studentId()));
    }
}
```

**What happens at commit:** The transaction records the sourcing criteria and the position reached. At commit, the event store verifies that no matching events were appended after that position by a concurrent transaction. If there was a conflict, `AppendEventsTransactionRejectedException` is thrown.

---

## Step 4 — Handle conflicts

When two commands race over the same criteria, the second one to commit loses. Retry by re-sourcing and re-deciding:

```java
@CommandHandler
void handle(EnrollStudent command, ProcessingContext context, EventAppender events) {
    int attempts = 0;
    while (true) {
        try {
            tryEnrol(command, context, events);
            return;
        } catch (AppendEventsTransactionRejectedException e) {
            if (++attempts >= 3) throw e;
            // The transaction context is spent; a new attempt needs a fresh context.
            // In practice, retry is typically handled at the command bus level via RetryScheduler.
        }
    }
}
```

In most setups, configure a `RetryScheduler` on the command bus to retry on `AppendEventsTransactionRejectedException` automatically rather than retrying in handler code.

---

## Crossing multiple decision boundaries

A single command sometimes needs state from more than one independent boundary. Source both, and the transaction tracks consistency across all of them:

```java
@CommandHandler
void handle(TransferStudent command, ProcessingContext context, EventAppender events) {
    var tx = eventStore.transaction(context);

    // Source from two independent tag boundaries
    var sourceCriteria = EventCriteria.havingTags("course", command.fromCourseId());
    var targetCriteria = EventCriteria.havingTags("course", command.toCourseId());

    var sourceState = tx.source(SourcingCondition.conditionFor(sourceCriteria))
                        .reduce(EnrolmentState.empty(), (s, e) -> s.apply(e.message(), command.studentId()))
                        .orTimeout(30, TimeUnit.SECONDS).join();

    var targetState = tx.source(SourcingCondition.conditionFor(targetCriteria))
                        .reduce(EnrolmentState.empty(), (s, e) -> s.apply(e.message(), command.studentId()))
                        .orTimeout(30, TimeUnit.SECONDS).join();

    // Validate against both states
    if (!sourceState.studentAlreadyEnrolled()) throw new NotEnrolledException(...);
    if (targetState.enrolled() >= targetState.capacity()) throw new CourseFullException(...);

    // Append — the transaction covers both sourced boundaries
    events.append(new StudentTransferred(command.studentId(), command.fromCourseId(), command.toCourseId()));
}
```

---

## When to still use an aggregate

Aggregates remain appropriate when:
- Every command targeting an entity always reads all events for that entity's identity — the boundary is completely stable.
- The entity has lifecycle behaviour (creation, deletion) that naturally scopes commands.

Even then, prefer sourcing the aggregate state directly via `EventStoreTransaction` over `EventSourcingRepository` — you gain explicit criteria control.

---

## Relationship to other guides

- **`command-handling`** — writing stateless handlers that don't read past state
- **`event-store-primitives`** — reference for `SourcingCondition`, `AppendCondition`, `ConsistencyMarker`, and `EventCriteria` APIs used here
