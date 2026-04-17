# Testing AF5 Applications

AF5 tests follow a **Given → When → Then** structure provided by `AxonTestFixture`. The fixture wires up a real (in-memory) AF5 configuration so tests exercise actual framework behaviour rather than mocks.

Test class conventions (from CLAUDE.md):
- JUnit 5 always; assertions via AssertJ
- `// given` / `// when` / `// then` section comments
- `@Nested` classes to group tests for the same method or scenario
- Test events created via `EventTestUtils`

---

## Setup

```java
class EnrolmentCommandHandlerTest {

    AxonTestFixture fixture;

    @BeforeEach
    void setUp() {
        var configurer = MessagingConfigurer.create();
        // Register your command handlers, event handlers, etc.
        configurer.commands(cmd -> cmd.module(
            CommandHandlingModule.named("enrolment")
                .commandHandlers()
                .autodetectedCommandHandlingComponent(c -> new EnrolmentCommandHandler(
                    c.getComponent(EventStore.class)
                ))
        ));
        fixture = AxonTestFixture.with(configurer);
    }

    @AfterEach
    void tearDown() {
        fixture.stop();
    }
}
```

---

## Given — seeding prior state

The Given phase populates the recording event store before the When action runs.

```java
// Single event
fixture.given()
       .event(new CourseCreated("course-1", "DDD", 30))

// Multiple events in one unit of work
       .events(new CourseCreated("course-1", "DDD", 30),
               new StudentEnrolled("course-1", "student-A"))

// Event with metadata
       .event(new CourseCreated("course-1", "DDD", 30),
              Metadata.with("source", "admin"))

// No prior events — makes the intent explicit
       .noPriorActivity()
```

### Seeding tagged events (DCB tests)

Command handlers that use `EventStoreTransaction` source events by tag. Seed tagged events so the handler finds the right state:

```java
import org.axonframework.messaging.eventstreaming.Tag;
import org.axonframework.eventsourcing.eventstore.GenericTaggedEventMessage;

var courseCreated = new CourseCreated("course-1", "DDD", 30);
var tagged = new GenericTaggedEventMessage<>(
        GenericEventMessage.asEventMessage(courseCreated),
        Set.of(new Tag("course", "course-1")));

fixture.given()
       .event(tagged)
       .when()
       .command(new EnrollStudent("course-1", "student-A"))
       ...
```

The tags must match what `@EventTag` on your event payload would have produced at real append time.

---

## When — the action under test

```java
// Dispatch a command
.when().command(new EnrollStudent("course-1", "student-A"))

// Dispatch a command with metadata
.when().command(new EnrollStudent("course-1", "student-A"),
                Metadata.with("userId", "admin"))

// Publish an event (for testing event handlers / projections)
.when().event(new CourseCreated("course-1", "DDD", 30))
```

---

## Then — assertions

### Events published

```java
// Exact payload match (uses deep-equals by default)
.then().events(new StudentEnrolled("course-1", "student-A"))

// Multiple events in order
.then().events(new StudentEnrolled("course-1", "student-A"),
               new EnrolmentConfirmed("course-1", "student-A"))

// No events expected
.then().noEvents()

// Custom assertion on the event list
.then().eventsSatisfy(events -> {
    assertThat(events).hasSize(1);
    assertThat(events.get(0).payload()).isInstanceOf(StudentEnrolled.class);
})
```

### Command handler result

```java
// Handler completed without exception
.then().success()

// Handler returned a specific value
.then().success()
       .resultMessagePayload(new EnrolmentId("enrol-42"))

// Custom assertion on the result
.then().resultMessagePayloadSatisfies(EnrolmentId.class,
        id -> assertThat(id.value()).startsWith("enrol-"))
```

### Exceptions

```java
// Handler threw a specific exception type
.then().exception(CourseFullException.class)

// Exception type and message substring
.then().exception(CourseFullException.class, "course-1 is at capacity")

// Custom assertion on the thrown exception
.then().exceptionSatisfies(ex -> {
    assertThat(ex).isInstanceOf(CourseFullException.class);
    assertThat(ex.getMessage()).contains("course-1");
})
```

### Commands dispatched as side effects

```java
// Assert that a command was dispatched during event handling
.then().commands(new SendEnrolmentConfirmation("course-1", "student-A"))

// No commands dispatched
.then().noCommands()
```

### Async assertions (streaming event processors)

When the When phase publishes an event that triggers an async event processor:

```java
.when().event(new CourseCreated("course-1", "DDD", 30))
.then().await(then -> then.commands(
        new NotifyCourseAvailable("course-1")))   // default 5 s timeout

// With explicit timeout
.then().await(then -> then.events(new NotificationSent("course-1")),
              Duration.ofSeconds(10))
```

---

## Chaining scenarios

```java
fixture.given()
       .event(new CourseCreated("course-1", "DDD", 30))
       .when().command(new EnrollStudent("course-1", "student-A"))
       .then().events(new StudentEnrolled("course-1", "student-A"))
       .and()   // ← returns to Given for the next scenario
       .given()
       .event(new CourseCreated("course-2", "EDA", 10))
       .when().command(new EnrollStudent("course-2", "student-B"))
       .then().success();
```

---

## EventTestUtils

Use `EventTestUtils` (in `messaging` test sources) to create generic test events when the specific payload doesn't matter:

```java
import static org.axonframework.messaging.eventhandling.EventTestUtils.*;

List<EventMessage<?>> events = createEvents(3);   // payloads: Integer 0, 1, 2
EventMessage<?> single     = createEvent(42);      // payload: Integer 42
EventMessage<?> wrapped    = asEventMessage(new CourseCreated("c", "DDD", 30));
```

---

## Matchers

For richer assertions beyond exact equality, use the `Matchers` factory:

```java
import static org.axonframework.test.matchers.Matchers.*;
import static org.hamcrest.Matchers.*;

// Deep field-by-field equality (ignores transient fields by default)
deepEquals(new StudentEnrolled("course-1", "student-A"))

// Ordered exact sequence with no extras
exactSequenceOf(
    messageWithPayload(instanceOf(StudentEnrolled.class)),
    messageWithPayload(instanceOf(EnrolmentConfirmed.class)),
    andNoMore())

// Sequence allowing gaps
sequenceOf(
    messageWithPayload(hasProperty("studentId", equalTo("student-A"))))

// Any of the list
listWithAnyOf(messageWithPayload(instanceOf(StudentEnrolled.class)))
```

Pass a Hamcrest `Matcher` to `.eventsMatch(matcher)` or `.commandsMatch(matcher)`:

```java
.then().eventsMatch(exactSequenceOf(
    messageWithPayload(deepEquals(new StudentEnrolled("course-1", "student-A"))),
    andNoMore()))
```

---

## Ignoring fields in deep equality

Register field filters to ignore generated or timestamp fields:

```java
fixture = AxonTestFixture.with(configurer, c -> c
        .registerIgnoredField(StudentEnrolled.class, "enrolledAt")
        .registerIgnoredField(StudentEnrolled.class, "enrollmentId"));
```

---

## JUnit 5 structure example

```java
class EnrolmentCommandHandlerTest {

    AxonTestFixture fixture;

    @BeforeEach void setUp() { /* ... */ }
    @AfterEach  void tearDown() { fixture.stop(); }

    @Nested
    class WhenEnrollingStudent {

        @Test
        void publishesStudentEnrolledEvent() {
            // given
            fixture.given()
                   .event(tagged(new CourseCreated("c1", "DDD", 30), "course", "c1"));
            // when / then
            fixture.when()
                   .command(new EnrollStudent("c1", "s1"))
                   .then()
                   .events(new StudentEnrolled("c1", "s1"));
        }

        @Test
        void rejectsWhenCourseFull() {
            // given
            fixture.given()
                   .event(tagged(new CourseCreated("c1", "DDD", 1), "course", "c1"))
                   .event(tagged(new StudentEnrolled("c1", "s-existing"), "course", "c1"));
            // when / then
            fixture.when()
                   .command(new EnrollStudent("c1", "s-new"))
                   .then()
                   .exception(CourseFullException.class);
        }
    }
}
```
