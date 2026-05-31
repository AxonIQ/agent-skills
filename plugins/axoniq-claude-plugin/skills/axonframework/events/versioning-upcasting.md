# Event Versioning and Upcasting in Axon Framework 5

Events are stored indefinitely, so over the lifetime of an application their schema *will* change. This guide covers how to evolve event schemas safely. AF5's primary mechanism is **payload conversion at handling time** — see [events/handling-projections.md](handling-projections.md) for how handlers are written and [event-store/conversion-serialization.md](../event-store/conversion-serialization.md) for the conversion layer. For how events are persisted, see [event-store/primitives.md](../event-store/primitives.md).

> **Read this first.** In Axon Framework 5.0 the classic *upcaster* mechanism is **not yet available**. It is scheduled to return in 5.2.0 ([AxonFramework#3597](https://github.com/AxonFramework/AxonFramework/issues/3597)) with APIs aligned to the new conversion architecture. For 5.0, do your versioning with **payload conversion at handling time**, which already covers the large majority of real-world schema changes. The upcasting section below is conceptual and forward-looking — do not write upcaster code against 5.0.

---

## Identifying an event version

Every event type carries a `MessageType` — a fully qualified name plus a version. You control all three with the `@Event` annotation (`org.axonframework.messaging.eventhandling.annotation.Event`):

```java
import org.axonframework.messaging.eventhandling.annotation.Event;

@Event(
    namespace = "university.faculty",  // defaults to the package name
    name      = "CourseCreated",       // defaults to the simple class name
    version   = "1.0.0"                // defaults to "0.0.1"
)
public record CourseCreated(String courseId, String name, int capacity) {
}
```

| Attribute | Maps to | Default |
|---|---|---|
| `namespace` | `QualifiedName#namespace()` | package name of the class |
| `name` | `QualifiedName#localName()` | simple class name |
| `version` | `MessageType#version()` | `"0.0.1"` (`MessageType.DEFAULT_VERSION`) |

The `name` is the stable business identity stored in the event store; the `version` distinguishes successive shapes of that same event. Changing the Java class name or package does **not** change the stored identity as long as `name`/`namespace` stay fixed — that is what lets you refactor freely.

---

## Payload conversion at handling time

When an event is stored, it keeps its serialized form (JSON, Avro binary, ...) together with its `MessageType`. When a handler needs the event, Axon converts that stored payload into the type the handler asks for — *at handling time*, per handler. Two consequences:

- Different handlers (even in different applications) can read the same stored event as different Java types.
- You evolve handling code without ever rewriting stored events.

### Matching a handler to a stored event

The first parameter's type normally drives both the matched event name and the target representation. When the Java type no longer shares its name with the stored event, pin the match explicitly with `eventName`:

```java
import org.axonframework.messaging.eventhandling.annotation.EventHandler;

class CourseProjection {

    // Reads the stored "CourseCreated" as the original record
    @EventHandler(eventName = "CourseCreated")
    void on(CourseCreated event) {
        repository.save(new CourseView(event.courseId(), event.name(), event.capacity()));
    }
}
```

If unspecified, `eventName` is derived from the payload type (the first parameter) by the configured `MessageTypeResolver`. You can also force the *representation* a handler receives with `payloadType` (defaults to `Object.class`), independent of the first parameter — useful for handlers that work against a raw representation.

### Reading an old event as a new shape

Suppose `CourseCreated` later needs a computed field. Define a new record under the **same** event `name`, add the field, and compute it in a constructor. A handler that asks for the new type triggers conversion of the stored payload into it:

```java
import com.fasterxml.jackson.annotation.JsonAlias;
import org.axonframework.messaging.eventhandling.annotation.Event;
import org.axonframework.messaging.eventhandling.annotation.EventHandler;

@Event(name = "CourseCreated", version = "2.0.0")
public record EnrichedCourseCreated(
    String courseId,
    @JsonAlias("name") String title,   // old field "name" maps onto "title"
    int capacity,
    int seatsRemaining                 // new field, defaulted during conversion
) {
    // Convenience constructor used when no seatsRemaining was stored
    public EnrichedCourseCreated(String courseId, String title, int capacity) {
        this(courseId, title, capacity, capacity);
    }
}

class CapacityProjection {

    @EventHandler
    void on(EnrichedCourseCreated event) {
        // Stored "CourseCreated" payloads are converted to this type on the fly.
        repository.updateSeats(event.courseId(), event.seatsRemaining());
    }
}
```

Meanwhile another handler — possibly in a different service — keeps reading the original shape unchanged:

```java
@EventHandler(eventName = "CourseCreated")
void on(CourseCreated event) {
    // Legacy handling path, still receiving the v1 representation.
}
```

Both handlers consume the *same* stored event; Axon's `Converter` (`org.axonframework.conversion.Converter`) does the per-handler transformation via `convert(input, targetType)`.

### What payload conversion handles without any extra code

| Change | How |
|---|---|
| **Add a field** | Give it a default in a constructor, or let the (de)serializer default it |
| **Remove a field** | Simply omit it from the new type — readers ignore unknown stored fields |
| **Rename a field** | Map old to new with Jackson `@JsonProperty` / `@JsonAlias` |
| **Change a field's type** | The `Converter` transforms compatible types (e.g. `String`→`Integer`, `Date`→`Instant`) |
| **Restructure per handler** | Each handler declares its own Java type for the same event |

> **Jackson defaulting.** With the Jackson-based converter, configure leniency (e.g. `FAIL_ON_UNKNOWN_PROPERTIES = false`) so removed/added fields do not break deserialization of older payloads. `@JsonAlias` is the cleanest way to keep accepting an old field name while exposing a new one.

This is intentionally the path of least resistance: prefer it, and reach for upcasters only when the **stored structure itself** must change in ways conversion cannot express.

---

## Backward- and forward-compatible event design

A few rules keep events evolvable regardless of mechanism:

- **Never reuse a `name` for a semantically different event.** The `name` is the contract; bump `version` for shape changes, mint a new `name` for new meaning.
- **Add, don't repurpose.** Adding optional/defaulted fields is backward compatible. Changing the meaning of an existing field is not — introduce a new field instead.
- **Avoid required fields without defaults** when you cannot backfill them for historical events.
- **Keep payloads serializer-friendly:** stable field names, simple types, records. Lean on `@JsonAlias`/`@JsonProperty` rather than renaming stored keys.
- **Decouple the stored name from the Java type name** via `@Event(name = ...)` so you can rename/move classes without an upcaster.

---

## Upcasting (concept — not available in 5.0)

> **Status.** The upcaster API is **not present in Axon Framework 5.0**; it returns in 5.2.0. The description below is conceptual so you can plan migrations, but there is no supported upcaster class to extend or register in 5.0. Until then, model these scenarios with payload conversion, or stage them for the 5.2.0 upgrade.

Unlike payload conversion (which runs per handler at handling time), **upcasting** transforms how an event is read *from storage*, before any handler sees it — a single transformation applied to all consumers. It is non-destructive: stored events are never rewritten; they are transformed on read.

The model is a **chain**. An upcaster takes an event at version *x* and produces zero or more events at version *x+1*; the output of one upcaster feeds the input of the next. Writing one small upcaster per version step keeps each transformation isolated and easy to reason about. The chain reads the `@Event` `version` to decide whether a given upcaster applies.

Upcasting is the right tool only when conversion cannot do the job — i.e. the stored representation itself must change:

| Scenario | Why conversion is insufficient |
|---|---|
| **Split one event into several** | Conversion is one-to-one per handler; it cannot fan one stored event out into multiple events |
| **Merge several events into one** | Requires reading across multiple stored events |
| **Change event identity** | Changing the stored `MessageType` (qualified name or version) of historical events |
| **Cross-event / contextual transforms** | Moving a field from an earlier event onto a later one needs carried context |
| **One transform for all handlers** | A single stored-level change instead of adjusting every handler |

When the API returns, expect abstractions along these lines (planned, names subject to change):

| Planned type | Shape |
|---|---|
| Single one-to-one upcaster | `canUpcast` + `doUpcast`, one event in/out |
| One-to-many upcaster | `doUpcast` returns a stream — split a "fat" event into finer ones |
| Context-aware (single / multi) | Adds a built context carried across the stream to move fields between events |
| Type-change upcaster | Dedicated to rewriting an event's qualified name/version |

Registration is expected to be ordering-sensitive (each step bridges exactly one version), via the configuration API or, under Spring Boot, Spring's `@Order`. **Do not write this code against 5.0** — track [AxonFramework#3597](https://github.com/AxonFramework/AxonFramework/issues/3597).

---

## Choosing a strategy

| Situation | Use |
|---|---|
| Add/remove/rename a field; change a field type | Payload conversion (define new `@Event` shape + Jackson annotations) |
| Different handlers want different shapes of one event | Payload conversion (per-handler types, `eventName`) |
| Rename/move the Java class, keep stored identity | Keep `@Event(name = ...)` stable — no transform needed |
| Split, merge, or re-identify stored events; cross-event moves | Upcasting — **wait for 5.2.0**; stage the change until then |

For the overwhelming majority of schema changes in AF5.0, payload conversion at handling time is the answer. Reserve upcasting for genuine stored-structure changes, and only once the mechanism ships.
