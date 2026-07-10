
# Implementing a COMMAND component

A COMMAND component groups command handlers that validate against a single (possibly compound) target identifier. It owns:
- An `@EventSourced` decision-model state class — derived from past events tagged with the target identifier(s).
- One `@CommandHandler` method per command in the spec.
- Events emitted on success.
- Exceptions thrown on validation failure.
- **NO time-bounded behavior in command handlers.** If the spec involves "wait N minutes / hours" or "if X doesn't happen by Y, do Z", the platform emits a separate WORKFLOW component for that — implement it with [implement-workflow-component.md](implement-workflow-component.md). Never use schedulers, virtual-thread sleeps, or `Thread.sleep(...)` in a command handler.

**Always load [implementation-base.md](implementation-base.md) first** — it has the package layout, decision trees, tag rules, AxonTestFixture project-specific setup, and Kotlin gotchas. For framework-level API details (annotation attributes, fixture matchers, command handler parameter resolution) consult the **`axoniq-app-development`** plugin (install it alongside this one from the `axoniq` marketplace):

- `commands/stateless.md` — stateless commands, `EventAppender` (dispatching: `commands/dispatching.md`)
- `commands/decision-models-dcb.md` — DCB with `@EventSourcedEntity` + `@InjectEntity` (Approach A is what we emit)
- `foundations/annotations.md` — `@Command`, `@CommandHandler`, `@Event`, `@InjectEntity` attribute reference
- `testing/basics.md` — full fixture API (matchers: `testing/matchers.md`; advanced: `testing/advanced.md`)

## Inputs

- `projectId` and `workspaceId` from `./.axoniq` at the repo root.
- `componentId` provided by [SKILL.md](SKILL.md).
- Component spec fetched via MCP: `get_component_details(projectId, componentId)`. Returns the handlers, possible events, exceptions, and scenarios inline.
- Referenced message schemas: the same `get_component_details` response carries the message references the component touches; resolve full message details from `get_project(projectId).messages` (single round-trip) and look them up by name. Don't read or write spec files on disk.

[SKILL.md](SKILL.md) picks the component as eligible in one of two modes:

- **Fresh implementation**: component status is `APPROVED` and no `<component_pkg>/.axoniq` marker exists locally. Write all files; create the marker as the first step.
- **Extend mode**: a `.axoniq` marker exists AND the spec (re-fetched via MCP) has handlers / events / exceptions the existing code doesn't reflect (because a later turn on the Platform extended the component). Read the existing State class, CommandHandler class, and event/exception files. Then **add** new methods, fields, events, and exceptions for the missing spec entries. Do NOT rewrite existing files unless their spec definition actually changed — in which case, flag the conflict to the user and ask before touching them. Update / add tests for new handlers. The marker stays as is.

## Files to write

All paths use the placeholders from [implementation-base.md](implementation-base.md). `<component_pkg>` = `{{source_directory}}/{{source_path}}/<componentId-as-snake>/`.

1. **Marker — write this FIRST** → `<component_pkg>/.axoniq` containing `{ "componentId": "<componentId>" }`. See [implementation-base.md](implementation-base.md) for the rationale (interrupt-safety: the marker links the package to the spec component immediately, so a crashed scaffolding run leaves a recoverable state rather than orphan code). In extend mode the marker already exists — leave it alone.

2. **Commands and command results** → `{{source_directory}}/{{source_path}}/api/commands/<MessageName>{{file_extension}}`
   - One file per command and per command result.
   - Field types only from: `String`, `Integer`, `Boolean`, `Decimal`, `BigDecimal`, `DateTime`, `Date`, `List<T>`. No fabricated types.
   - **Annotate each command with `@Command(routingKey = "<idField>")`** — see [implementation-base.md](implementation-base.md#command-routing----commandroutingkey-----is-required). Required for `@InjectEntity` resolution.
   - For compound identifiers: declare ONE shared `TargetIdentifier` (or domain-named identifier like `SessionEnrollmentIdentifier`) class at the package level — not nested per command. All commands sharing a model reference it via `@TargetEntityId fun modelIdentifier(): SharedTargetIdentifier`. Annotate those commands `@Command(routingKey = "modelIdentifier")`.

3. **Events** → `{{source_directory}}/{{source_path}}/api/events/<EventName>{{file_extension}}`
   - One file per event in the spec's `possibleEvents`.
   - Annotate with `@Event(namespace = "<project-namespace>", name = "<EventName>")` — always set both. See [implementation-base.md](implementation-base.md#event-namespace--always-set-eventnamespace-name) for the namespace rule.
   - Tag keys come from the spec's message-property `tagKey` field. Never invent.

4. **No scheduling code.** Time-bounded behavior lives in a separate WORKFLOW component. See [implement-workflow-component.md](implement-workflow-component.md).

5. **Exceptions** → `<component_pkg>/<ExceptionName>{{file_extension}}`
   - One per declared `ComponentException`.
   - Live with the handler that throws them. Do NOT create a separate `api/exception/` package.

6. **State model** → `<component_pkg>/<ComponentName>State{{file_extension}}`
   - `@EventSourced` (Spring stereotype from `org.axonframework.extension.spring.stereotype`; combines `@EventSourcedEntity` + `@Component`) with `idType` per the decision tree in implementation-base.
   - `@EntityCreator` constructor (per the decision tree).
   - `@JvmStatic @EventCriteriaBuilder` (Kotlin) / static (Java) building `EventCriteria.havingTags(...).andBeingOneOfTypes("...")`.
   - `@EventSourcingHandler` per event the model evolves on.

   > ⚠️ **Use `@EventSourcingHandler` here — NEVER `@EventHandler`.** They are different annotations in different packages:
   > - `@EventSourcingHandler` → `org.axonframework.eventsourcing.annotation.EventSourcingHandler` — used inside `@EventSourced` / `@EventSourcedEntity` state classes; invoked by the framework while it rebuilds state from past events before each command.
   > - `@EventHandler` → `org.axonframework.messaging.eventhandling.annotation.EventHandler` — used in QUERY components and EXTERNAL_SYSTEM stubs; invoked by the event-processor machinery, NOT during sourcing.
   >
   > If you put `@EventHandler` on a state-class method, the framework will *not* invoke it during sourcing. The state silently stays at its initial value, every `if (state.isAlready...) throw ...` returns false, and the first command always succeeds — usually with the wrong outcome. Cross-check the import line before declaring the state class complete.

   **Required imports for the state file** (copy verbatim — do not paraphrase or shorten):

   ```kotlin
   import org.axonframework.extension.spring.stereotype.EventSourced
   import org.axonframework.eventsourcing.annotation.EventSourcingHandler
   import org.axonframework.eventsourcing.annotation.EventCriteriaBuilder
   import org.axonframework.eventsourcing.annotation.reflection.EntityCreator
   import org.axonframework.eventsourcing.annotation.reflection.InjectEntityId   // only if @EntityCreator takes an id parameter
   import org.axonframework.messaging.eventstreaming.EventCriteria
   // Tag import — look it up in the axoniq-app-development plugin's event-store/primitives.md guide before using.
   ```

   In Java, the same FQNs without the `import` keyword's trailing line. See [implementation-base.md](implementation-base.md#imports-that-are-easy-to-get-wrong) for the full annotation/import reference and the `@EventHandler` vs `@EventSourcingHandler` disambiguation table.

### State-population discipline (rules #1–3)

Every state field exists because some validation needs it. Every validation needs a value the moment the command handler runs. Therefore every state field **must be populated entirely from the events** the criteria builder pulls. Three rules — violating any of them produces a state that compiles, looks correct, and silently makes the wrong decision at runtime.

**Rule #1 — events must be self-contained.** An event carries every value needed to populate the state fields it touches. Never write an `@EventSourcingHandler` that says "I need this value but it's not on the event" — that's a sign the event is missing a property, not a sign that the handler should look the value up elsewhere. If you find yourself wanting to fetch from a repository inside `@EventSourcingHandler`, stop and add the missing property to the event in the spec instead.

```kotlin
// WRONG — handler can't populate `price` because the event doesn't carry it
@EventSourcingHandler
fun on(event: ItemAddedToCart) {
    cartItems.add(CartItem(event.productId, event.quantity, /* price = ??? */))
    // ← AI typically leaves a "// TODO: get price from ProductCreated events" comment here.
    //   The list silently stays half-populated forever.
}
```

```kotlin
// RIGHT — the event carries everything the state needs
@EventSourcingHandler
fun on(event: ItemAddedToCart) {
    cartItems.add(CartItem(event.productId, event.quantity, event.price))
}
```

**Rule #2 — every state field must be populated by some `@EventSourcingHandler`.** If `<ComponentName>State` declares a field, at least one event the criteria builder pulls must populate it. A field that's declared but never assigned is a dead field — either remove it from state (the validation doesn't actually need it) or add an event that populates it (the validation does need it, and the spec is missing an event).

Audit step before declaring complete: for every state field, point to the `@EventSourcingHandler` that assigns it. If you can't, fix one side or the other.

**Rule #3 — collections require explicit population.** A `MutableList`, `MutableMap`, or `MutableSet` field needs `.add(...)`, `.put(...)`, `.remove(...)` calls inside `@EventSourcingHandler` methods. Just declaring `val items: MutableList<Item> = mutableListOf()` populates nothing.

```kotlin
@EventSourced
class CartState {
    private val items: MutableList<CartItem> = mutableListOf()
    private var totalCents: Long = 0L

    @EventSourcingHandler
    fun on(event: ItemAddedToCart) {
        items.add(CartItem(event.productId, event.quantity, event.priceCents))
        totalCents += event.priceCents * event.quantity
    }

    @EventSourcingHandler
    fun on(event: ItemRemovedFromCart) {
        val removed = items.removeAt(items.indexOfFirst { it.productId == event.productId })
        totalCents -= removed.priceCents * removed.quantity
    }

    fun items(): List<CartItem> = items.toList()
    fun totalCents(): Long = totalCents
}
```

**Rule #4 — every lifecycle/status field must be CONSULTED by every state-changing command handler.** Symmetrical to Rule #2. If `<ComponentName>State` declares a status / lifecycle field (e.g. `var status: RentalStatus`, `var orderState: OrderState`, `var settled: Boolean`), then every `@CommandHandler` in this component that appends a transition event MUST first read that field and decide whether the transition is permitted. Two outcomes are valid:

- Return silently (idempotent no-op) if the current status already represents the command's effect, OR a competing terminal command has already won.
- Throw a precondition exception if the transition is genuinely invalid and the caller needs to know.

A status field that's populated by `@EventSourcingHandler`s but never read by `@CommandHandler`s is the canonical silent-corruption shape: every command appends regardless of state, the event stream accumulates conflicting transitions, and the read model goes wrong on whichever event arrived last. The component compiles, scenario tests pass (each scenario isolates one command), and the bug only surfaces when commands interleave in production.

Audit step before declaring complete: for every status/lifecycle field, point to the `if (state.<field> != <expected>) { return }` (or `throw`) check in every command handler that emits a transition event for this state. If any handler is missing one, add it. See [State-machine guards (idempotency)](#state-machine-guards-idempotency) below for the canonical pattern.

(There is also a derivation-time rule that events must have the properties state needs — that's handled server-side by the Platform AI. If an event is missing a property your event-sourcing handler needs, fix it via `chat_with_platform` rather than working around it locally.)

## State-machine guards (idempotency)

**Every command handler should be idempotent against its own current state.** Three concrete sources of duplicate or conflicting commands you cannot prevent at the dispatch layer:

1. **Workflow re-delivery.** Workflows use `ctx.awaitExecute(...)` for at-least-once delivery (see [implement-workflow-component.md](implement-workflow-component.md)) — after a crash/resume, the workflow re-dispatches commands whose persistent step record didn't confirm.
2. **MULTI ANY losing-branch race.** A workflow with `multi any` racing several waits can dispatch a terminal command from one branch's `onSuccess`, then have the OTHER branch fire its own terminal command before the first one's event reaches the read model. Both commands land on the aggregate; the second must no-op rather than corrupt state.
3. **Ordinary client retries / double-clicks.** A UI retry after a slow response, a browser double-click, an at-least-once HTTP gateway — all produce a duplicate command.

**Pattern**: every `@CommandHandler` checks the current state before appending. The check is cheap because the state is already loaded via `@InjectEntity`.

```kotlin
@CommandHandler
fun handle(
    command: <Command>,
    @InjectEntity(idProperty = "<property-or-method>") state: <ComponentName>State,
    eventAppender: EventAppender,
) {
    // 1. Idempotency guard — if the current state already represents this command's effect,
    //    OR a competing terminal command has already won, return silently. NO exception.
    //    Picking "return silently" vs "throw" depends on caller expectations:
    //    - Workflow-dispatched / retry-prone: return silently (workflow doesn't want to fail).
    //    - User-initiated where the UI must show "already done": throw a domain exception.
    if (state.<lifecycleField> != <ExpectedStatusToTransitionFrom>) return

    // 2. Precondition validation — business rules whose failure the caller needs to know
    //    (e.g. "course is full", "amount exceeds balance"). These throw declared exceptions.
    if (<precondition fails>) throw <Exception>(...)

    // 3. Append the event.
    eventAppender.append(<Event>(...))
}
```

**Which lifecycle values count as "already done"?**

- For a transition command (e.g. `MarkBikeInUse` moving `REQUESTED → IN_USE`): guard with `if (state.status != REQUESTED) return`. This catches BOTH re-delivery (status already `IN_USE`) AND competing-terminal (status already `REJECTED`).
- For an initialization command (e.g. `RegisterBike` creating a new entity): guard against re-registration with `if (state.exists) return` or use a tag-uniqueness exception per the spec.
- For an unconditional "record this" command with no lifecycle implication: no guard needed, but verify with the spec whether the command really lacks lifecycle context.

**Anti-patterns:**

- ❌ `if (<event already emitted>)` — checking for a specific past event by name. The guard reads CURRENT STATE, not event history. State is what `@InjectEntity` gives you; history is what you should leave to the event store.
- ❌ Guarding on `event.timestamp < state.lastTransitionAt` — clock-based ordering doesn't work in event-sourced systems. The state machine is the source of truth.
- ❌ Skipping the guard "because the workflow won't re-deliver" — workflows DO re-deliver across crashes, and even if they didn't, points 2 and 3 above stand.

7. **Command handler component** → `<component_pkg>/<ComponentName>CommandHandler{{file_extension}}`
   - Spring `@Component`.
   - One `@CommandHandler` method per command. The body is **always** three ordered phases — guard, precondition, append — see [State-machine guards (idempotency)](#state-machine-guards-idempotency) for the rationale.
     ```kotlin
     @CommandHandler
     fun handle(
         command: <Command>,
         @InjectEntity(idProperty = "<property-or-method>") state: <ComponentName>State,
         eventAppender: EventAppender,
     ) {
         // 1. Idempotency guard against current lifecycle/status state.
         //    Required for every command that transitions a state machine.
         if (state.<lifecycleField> != <ExpectedStatusToTransitionFrom>) return

         // 2. Precondition validation — declared exceptions only.
         if (<precondition fails>) throw <Exception>(...)

         // 3. Append the event.
         eventAppender.append(<Event>(...))
     }
     ```

8. **Tests** → `{{source_test_directory}}/{{source_path}}/<componentId-as-snake>/<ComponentName>AxonFixtureTest{{file_extension}}`
   - Package: `<base>.<componentId-as-snake>` — preserve underscores; never collapse.
   - Use the base setup from [implementation-base.md](implementation-base.md).
   - Generate at least:
     - One happy-path test per command (given prior events → when command → then expected events).
     - One test per declared exception (given prior events → when command → then exception).
     - One test per `scenario` from the spec (the spec's `scenarios` field describes given/when/then in plain text — translate to fixture calls).
     - **One re-delivery test per command that drives a lifecycle transition** — give the prior transition event, send the same command again, expect `.then().success()` with NO events. This proves the idempotency guard from section 7 is in place.
     - **One cross-terminal interleaving test for every pair of terminal commands operating on the same state** — give command A's success event as the prior state, send command B, expect `.then().success()` with NO events. The second terminal command must no-op because the lifecycle has already left the transition-from state.

   The last two are NOT in the spec's `scenarios` field — that field describes each command in isolation. You need to enumerate the interleavings yourself by looking at the component's command set and which of them are terminal transitions on the same lifecycle field.

   Concrete example for a bike-rental `rental-lifecycle` component with three terminal commands on `rentalId` (`MarkBikeInUse`, `RejectRentalPaymentTimeout`, `RejectRentalPaymentCancelled`):
   - 3 re-delivery tests (one per command).
   - 6 cross-terminal tests (every ordered pair of distinct terminals).
   - All 9 expect `.then().success()` with no events — proving each guard catches the conflicting prior transition.

## AxonTestFixture usage in this codebase

For the full Given/When/Then API see the **`axoniq-app-development`** plugin's `testing/basics.md` guide. The shortlist below is the subset we emit by default — these are the methods every component test in this codebase actually uses:

- `fixture.given().noPriorActivity()` — explicit empty state
- `fixture.given().event(<Event>(...))` — single seed event (chainable)
- `fixture.given().event(...).event(...)` — multiple
- `.when().command(<Command>(...))`
- `.then().success()`
- `.then().events(<Event>(...), <Event>(...))`
- `.then().eventsSatisfy { events -> /* assertions */ }`
- `.then().exceptionSatisfies { ex -> assertThat(ex)... }`

> Always pass **plain event payload objects** to `fixture.given().event(...)` — see the `GenericTaggedEventMessage` pitfall in [implementation-base.md](implementation-base.md). The fixture resolves `@EventTag` automatically; manual tag construction is a bug.

The command itself carries the target identifier. Never call `expectTargetIdentifier()` / `withTargetIdentifier()` — those methods don't exist.

## Compound-identifier sanity check

If the spec declares a compound identifier (multiple `tagKeys` on the COMMAND messages):

- The shared identifier class has a primary constructor with all parts (e.g. `data class SessionEnrollmentIdentifier(val sessionId: String, val userId: String)`).
- Every command using this model has `@TargetEntityId fun modelIdentifier()` returning the shared identifier.
- The state class is `@EventSourced(idType = SessionEnrollmentIdentifier::class)`.
- Every `@CommandHandler` uses `@InjectEntity(idProperty = "modelIdentifier")` — the method name, no parentheses.
- The state's `@EntityCreator` is empty (`constructor()`) **if** the model is shared by multiple commands; otherwise it takes `@InjectEntityId id: SessionEnrollmentIdentifier`.

If any of these conditions are inconsistent in the spec (e.g. one command has `modelIdentifier()`, another doesn't), STOP and tell the user — that's a Platform-side issue, not something to paper over locally.

## When to stop and ask

- The spec contains a property type not in the supported list.
- The compound-identifier sanity check fails.
- The component package already exists with a different `componentId` in `.axoniq`.
- Compile or tests fail. Surface failures verbatim and let [SKILL.md](SKILL.md) decide whether to retry or escalate.

## Boundaries

- Don't touch other components' packages.
- Don't redefine events/commands/queries that already exist under `api/`. Reference them via FQN.
- Don't modify the per-package `.axoniq` of any component other than this one.
- Don't import from Axon Framework 4.
