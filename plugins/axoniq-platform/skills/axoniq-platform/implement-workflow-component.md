# Implementing a WORKFLOW component

A WORKFLOW component is a long-running, event-sourced orchestration powered by the Axoniq Workflow engine (`io.axoniq.framework:axoniq-workflow-*` **0.2.0**) on Axon Framework 5. It starts on a single trigger event, then walks a directed graph of steps — waiting on correlated events (with timeouts), dispatching commands, fanning out via parallel waits, or branching on payload data — until it terminates.

**Always load [implementation-base.md](implementation-base.md) first** for shared package layout, imports, and the "no Axon 4" rule. This skill builds on top.

## Inputs

- `projectId` and `workspaceId` from `./.axoniq` at the repo root.
- `componentId` provided by [SKILL.md](SKILL.md).
- Component spec fetched via MCP: `get_component_details(projectId, componentId)`. For a WORKFLOW the response carries:
  - `triggerEvent` — the event message whose arrival starts the workflow. It becomes `@Workflow(startOnEventClass = <TriggerEvent>::class)`, referencing the event class in `api/events/` — see the `@Workflow` note below,
  - `idProperty` — the correlation key (e.g. `"orderId"`),
  - `entryStep` — the name of the first step to execute,
  - `steps[]` — the list of steps. Each entry has a `kind` (`WAIT` / `DISPATCH` / `SLEEP` / `MULTI` / `WHEN` / `CHOICE` / `FAIL` / `CANCEL`) and the relevant fields for that kind, plus `on*` pointers (`onSuccess`, `onFailure`, `onTimeout`) naming the next step on each outcome. A pointer may name an **earlier** step (a back-edge) — that's a business loop (see "Loops" below). Terminal status: a null `onSuccess` ends the body normally (COMPLETED); a null `onFailure`/`onTimeout` is NOT terminal — the step failure propagates and the engine retries. FAILED / CANCELLED are reached only by routing to an explicit `FAIL` (`ctx.fail`) or `CANCEL` (`ctx.cancel`) step.

Don't read or write spec files on disk — the spec lives on the Platform.

[SKILL.md](SKILL.md) picks the component as eligible in one of two modes:

- **Fresh implementation**: MCP component status is `APPROVED` and no `<component_pkg>/.axoniq` marker exists. Write the marker first, then the workflow class and message references.
- **Extend mode**: marker exists, but the spec (re-fetched via MCP) has different steps or pointers. Diff against the existing workflow class and update only the changed paths. The structured `steps[]` makes the diff direct — no text parsing needed.

## Step DAG → workflow translation overview

The spec is a graph of named steps; each step has `on*` pointers to its successor(s). You translate it into imperative code inside a single `@Workflow` method, following the edges from `entryStep`. **Codegen strategy (hybrid):** if the graph is **acyclic**, emit straight-line code (await/dispatch in sequence, `when`/`if` for branches) as in the examples below. If the graph has a **back-edge** (a pointer to an already-visited step — a loop), emit a **step-dispatch loop** instead so the cycle compiles (see "Loops" below). Eight step kinds map cleanly to engine primitives:

| Step kind                                  | Workflow translation                                                                                                                              |
|---|---|
| `WAIT` (no timeout)                       | `ctx.awaitEvent(name, Event::class.java, associate(payloadProperty(prop), equalsTo(...))) { it.timeout(LONG_WAIT) }` — returns the typed event for downstream steps. The timeout is still explicit: the engine's default is 5 seconds (see "Every step has a timeout"). |
| `WAIT` (with `timeoutSeconds`)            | Same `awaitEvent` with `{ it.timeout(Duration.ofSeconds(N)) }`, **wrapped in try/catch** for `StepTimedOutException` (see "Step timeouts" below) |
| `DISPATCH`                                | `ctx.dispatch(name, Command(...))` — the small `awaitExecute` helper defined in "Class shape" below; it sends through `CommandDispatcher.forContext(pc)` so the send is recorded as a step. Route `onSuccess`/`onFailure` to their target steps; a null `onFailure` propagates so the engine retries. |
| `SLEEP`                                   | `ctx.sleep(name, Duration.ofSeconds(N))`, then continue via `onSuccess`. Used to pace a business poll loop. |
| `MULTI`                                   | Non-blocking `ctx.waitForEvent(...)` for each inner WAIT (returns `WorkflowStepResult`), then race them via `ctx.anyMatch(predicate, results...)` (`ANY`) or `ctx.allMatch(predicate, results...)` (`ALL`) — see "Multi" below. |
| `WHEN`                                    | A Kotlin `when (ctx.workflowPayload()["<property>"] as String?)` over the exact trigger-property value, one arm per case + `else` for default. |
| `CHOICE`                                  | An `if / else if / else` chain — **one arm per ordered branch**, first match wins. Implement each branch's free-text `condition` as the actual boolean against whatever's in scope (a captured `awaitEvent`/`awaitExecute` result, a payload counter, etc.). `default` is the `else`. |
| `FAIL`                                    | `ctx.fail(<exceptionName>("<message>"))` — terminal, ends FAILED. The exception is a normal `RuntimeException` subtype; reference an existing one or create a small one in the component package. |
| `CANCEL`                                  | `ctx.cancel("<reason>")` — terminal, ends CANCELLED. A deliberate, non-error stop. |
| `onSuccess` = null                        | `return` — end of body = COMPLETED |
| `onTimeout` = null                        | leave it: the WAIT's timeout try/catch has no handler branch, so the `StepTimedOutException` propagates and the engine retries. To act on a timeout the spec routes `onTimeout` to a step. (A step timeout never becomes the workflow TIMED_OUT state.) |
| `onFailure` = null                        | **do nothing** — let the command failure propagate out of `execute(...)`; the engine retries it. Do NOT translate this to a `fail`/`return`. |

Walk the DAG from `entryStep`. Each `on*` pointer becomes a *sequence* in the linear body. A `FAIL`/`CANCEL` step is a leaf: emit `ctx.fail(...)` / `ctx.cancel(...)` and stop that branch. Where two paths converge on the same step (typical in failure flows), generate the step once and let both branches `return` afterwards — workflows don't have a `goto` so converging paths need each branch to drive itself to completion.

**Workflows never publish events directly.** Only command handlers emit events. When the spec implies "after step X, announce Y", model it as a `DISPATCH` to a COMMAND component whose handler emits Y. Don't call `eventGateway.publish(...)` from inside the workflow body.

## Files to write

`<component_pkg>` = `{{source_directory}}/{{source_path}}/<componentId-as-snake>/`.

1. **Marker — write this FIRST** → `<component_pkg>/.axoniq` containing `{ "componentId": "<componentId>" }`. See [implementation-base.md](implementation-base.md) for the rationale. In extend mode the marker already exists — leave it alone.

2. **Trigger event** → `{{source_directory}}/{{source_path}}/api/events/<TriggerEvent>{{file_extension}}`
   - Reference, don't redefine, if it already exists (a COMMAND component likely emits it).

3. **Waited events** → each `WaitStep.eventName` references an event in `api/events/`. Reference, don't redefine.

4. **Dispatched commands** → each `DispatchStep.commandName` and lifecycle command references `api/commands/`. Reference, don't redefine.

5. **Workflow class** → `<component_pkg>/<ComponentName>Workflow{{file_extension}}`

   **Imports — exact package names for `axoniq-workflow` 0.2.0 (do NOT invent):**
   ```kotlin
   import io.axoniq.workflow.dsl.api.EventAssociationsUtils.equalsTo
   import io.axoniq.workflow.dsl.api.EventAssociationsUtils.payloadProperty
   import io.axoniq.workflow.dsl.simple.SimpleWorkflowContext
   import io.axoniq.workflow.runtime.api.annotation.Workflow
   import io.axoniq.workflow.runtime.api.execution.state.StepFailedException
   import io.axoniq.workflow.runtime.api.execution.state.StepTimedOutException
   import io.axoniq.workflow.runtime.api.execution.state.WorkflowStepResult
   import io.axoniq.workflow.runtime.api.payload.PayloadProcessor
   import io.axoniq.workflow.runtime.association.Associations.associate
   import org.axonframework.messaging.commandhandling.gateway.CommandDispatcher
   import org.springframework.stereotype.Component
   import java.time.Duration
   import java.util.concurrent.TimeUnit
   ```

   Note these specifics — they trip people up (every one of these has bitten implementers):
   - `associate` is a static on **`io.axoniq.workflow.runtime.association.Associations`**. `payloadProperty` and `equalsTo` are statics on **`io.axoniq.workflow.dsl.api.EventAssociationsUtils`**. There is no `AssociationsUtils` (that was 0.1.0).
   - `StepTimedOutException` and `StepCancellationException` are subtypes of `StepFailedException`; all three live under **`io.axoniq.workflow.runtime.api.execution.state`** (NOT `runtime.api.exception` — there is no such package). `WorkflowStatus` lives under `runtime.api.execution.status`.
   - The `@Workflow` trigger attribute is **`startOnEventClass = <TriggerEvent>::class`** (or `startOnEventName = "<namespace>.<EventName>"`; exactly one of the two). There is no `startOnEvent`. Prefer the class form: the engine resolves it through the application's `MessageTypeResolver`, the same one that typed the event when the command handler published it, so it matches in production **and** in the test fixture. The name form matches only where the resolver is annotation-based (production), not in the fixture.
   - Set **`workflowNamespace`** and **`workflowName`** explicitly. They name the workflow's own events in the event store (`<workflowName>#ExecuteStarted`, `<stepName>Started`, ...); without them the namespace is empty and the name is derived from the class and method name, which then silently changes when either is renamed. Use the project's event namespace and `<ComponentName>Workflow`.
   - The typed `awaitEvent(name, Event::class.java, associations) { customizer }` returns the deserialised event. Its only signature takes the step customizer, and that is where the timeout goes: `{ it.timeout(Duration.ofSeconds(N)) }`. There is no `Duration` positional argument.
   - The lifecycle hook annotations are `@WorkflowCompletedHandler` / `@WorkflowFailedHandler` / `@WorkflowCancelledHandler` / `@WorkflowTimedOutHandler` (a handler method takes `(status: WorkflowStatus, ctx: SimpleWorkflowContext)`). `@OnSuccess` / `@OnFailure` / `@OnCancellation` / `@OnTimeout` do not exist in 0.2.0. `@WorkflowTimedOutHandler` does **NOT** fire when a step's `awaitEvent(...)` exceeds its timeout — see "Step timeouts" below.
   - `SimpleWorkflowContext.awaitExecute(name, ResultClass, Supplier)` still exists for a value-returning action, but a command dispatch needs the step's `ProcessingContext`, so DISPATCH steps use the `PayloadProcessor` form via the `dispatch` helper below.
   - The spec's workflow-level `onSuccess` commands are just DISPATCH steps that happen at the end of the workflow body — the workflow succeeds by reaching the end of `execute(...)` normally. Don't reach for a lifecycle handler for them.

   ## Every step has a timeout

   The engine gives **every** step a timeout, `awaitEvent` and `waitForEvent` included, and the default is **5 seconds**. A WAIT whose spec has no `timeoutSeconds` therefore still needs an explicit, generous timeout or it times out five seconds after it started. Declare one constant in the workflow class and use it for every untimed wait:

   ```kotlin
   private companion object {
       val LONG_WAIT: Duration = Duration.ofDays(30)
   }
   ```

   The timeout is measured from the step's STARTED event, so after a crash and replay the remaining time is what is left of the original window, not a fresh window.

   ## Step timeouts — use try/catch, NOT a lifecycle handler

   When a step's `awaitEvent(...)` exceeds its timeout, it throws `StepTimedOutException` (the *step* status is `TIMED_OUT` — this does **not** put the *workflow* in the TIMED_OUT state). If the spec gives the wait an `onTimeout` pointer, wrap the `awaitEvent` in a try/catch and, in the catch, do whatever that pointer's step is (dispatch a compensating command, `ctx.fail(...)`, `ctx.cancel(...)`, or continue to the next step). If `onTimeout` is **null**, do **not** catch it — let the exception propagate so the engine retries (per the spec's "null onTimeout is not terminal").

   Catch `StepTimedOutException`, not the broader `StepFailedException`: a cancelled or failed wait is a different outcome than "the user didn't pay in time" and must not be routed to the timeout branch.

   Per-step timeout pattern:

   ```kotlin
   val confirmation = try {
       ctx.awaitEvent(
           "<stepName>",
           <Event>::class.java,
           associate(payloadProperty("<correlationProperty>"), equalsTo(<idValue>)),
       ) { it.timeout(Duration.ofSeconds(<timeoutSeconds>)) }
   } catch (e: StepTimedOutException) {
       // The spec's onTimeout step for this wait.
       ctx.dispatch("<stepName>Timeout", <TimeoutCommand>(/* fields from ctx.workflowPayload() */))
       return  // Stop the workflow body — subsequent steps would assume the wait succeeded.
   }
   // happy path: continue with subsequent steps using `confirmation`
   ```

   Mapping from the spec to this pattern:
   - The spec's workflow-level `onTimeout` list of commands is what gets dispatched from the catch block of the WAIT step that "owns" the timeout. If multiple WAIT steps could time out, attribute the `onTimeout` commands to the most natural owner (typically the first WAIT, since later steps don't run after a timeout). If the spec is ambiguous, replicate the catch block per WAIT.
   - Wrap each WAIT step in its own try/catch so subsequent steps don't run after a timeout.
   - Dispatch the timeout commands through `ctx.dispatch(...)` — same at-least-once guarantee as a normal DISPATCH step.

   ## Multi — parallel waits with `waitForEvent` + `anyMatch` / `allMatch`

   When the spec has a `MULTI` step racing two or more WAITs (typical: "either confirmation X arrives OR cancellation Y arrives, whichever first"), open each wait with the non-blocking `ctx.waitForEvent(...)` and then combine the resulting `WorkflowStepResult`s with `ctx.anyMatch(...)` or `ctx.allMatch(...)`.

   **Key distinction from a single WAIT:**

   - `ctx.awaitEvent(name, EventClass, associations) { customizer }` — **blocking**. Returns the event itself. Use for a single WAIT step.
   - `ctx.waitForEvent(name, EventClass, associations) { customizer }` — **non-blocking**. Returns a `WorkflowStepResult` handle representing an in-flight wait. Combine multiple via `anyMatch` / `allMatch`.

   **Combinators:**

   - `ctx.anyMatch(predicate: Predicate<WorkflowStepResult>, vararg results: WorkflowStepResult): CombinatorWorkflowStepResult` — completes when **any** inner result matches the predicate.
   - `ctx.allMatch(predicate: Predicate<WorkflowStepResult>, vararg results: WorkflowStepResult): CombinatorWorkflowStepResult` — completes when **all** inner results match.

   Call `.await()` on the combinator before reading it. `WorkflowStepResult` exposes `isCompleted()`, `success()`, `failure()`, `timeout()`, `canceled()`, `result()` (the matched event payload as a map) and `getStepName()` (`.stepName` in Kotlin) — there is **no** `completed` property and **no** `completedStepName()`. The combinator (`CombinatorWorkflowStepResult`) exposes `matched()` / `unmatched()`; the winning inner step is `matched().firstOrNull()`.

   > ⚠️ **The predicate MUST be `{ it.success() }`, not `{ it.isCompleted() }`.** On a WAIT that hits its timeout, `isCompleted()` returns **true** — so `{ it.isCompleted() }` matches a timed-out wait and routes to its "arrived" branch (e.g. mark-bike-in-use instead of reject-on-timeout). With `success()`, a timed-out wait is NOT matched, so `matched()` comes back empty and control correctly falls to the else/timeout branch.

   **Pattern for `MULTI ANY` (race — first to arrive wins):**

   ```kotlin
   val rentalId = ctx.workflowPayload().getValue("rentalId") as String

   // Open both waits non-blocking; each returns a handle, not the event.
   val payCompleted = ctx.waitForEvent(
       "awaitPaymentCompleted",
       PaymentCompleted::class.java,
       associate(payloadProperty("rentalId"), equalsTo(rentalId)),
   ) { it.timeout(Duration.ofSeconds(120)) }
   val payCancelled = ctx.waitForEvent(
       "awaitPaymentCancelled",
       PaymentCancelled::class.java,
       associate(payloadProperty("rentalId"), equalsTo(rentalId)),
   ) { it.timeout(Duration.ofSeconds(120)) }

   // Race them — first to SUCCEED wins. (success(), not isCompleted(): a timed-out wait is
   // "completed" but not successful — see the warning above.)
   val winner = ctx.anyMatch({ it.success() }, payCompleted, payCancelled)
   winner.await()

   // Branch on which inner step succeeded; matched() is empty if all timed out → else branch.
   when (winner.matched().firstOrNull()?.stepName) {
       "awaitPaymentCompleted" -> ctx.dispatch("markBikeInUse", MarkBikeInUse(rentalId = rentalId))
       "awaitPaymentCancelled" -> ctx.dispatch("rejectRental", RejectRental(rentalId = rentalId, reason = "PAYMENT_CANCELLED"))
       else -> ctx.dispatch("rejectOnTimeout", RejectRental(rentalId = rentalId, reason = "TIMEOUT"))  // the spec's onTimeout
   }
   ```

   **Pattern for `MULTI ALL` (gather — wait for every inner to complete):**

   ```kotlin
   val partA = ctx.waitForEvent("partA", PartAReceived::class.java, associate(...)) { it.timeout(Duration.ofSeconds(N)) }
   val partB = ctx.waitForEvent("partB", PartBReceived::class.java, associate(...)) { it.timeout(Duration.ofSeconds(N)) }
   ctx.allMatch({ it.success() }, partA, partB).await()
   // Both arrived — read payloads off the individual results (`partA.result()`) if needed.
   ```

   **Mapping from the spec:**

   - The MULTI's `innerSteps` list → one `ctx.waitForEvent(...)` per name, in the same order.
   - MULTI mode `ANY` → `ctx.anyMatch(...)`; mode `ALL` → `ctx.allMatch(...)`.
   - MULTI's per-inner `on*` pointers → branches in the `when (winner.matched().firstOrNull()?.stepName) { ... }`.
   - MULTI's `timeoutSeconds` → `{ it.timeout(Duration.ofSeconds(N)) }` on each inner `waitForEvent` (every inner times out if none completes within the window; the `else` branch in `when` handles that case for `anyMatch`).

   Do NOT replace `waitForEvent` with `awaitEvent` inside a MULTI — `awaitEvent` is blocking and would serialise the waits instead of racing them.

   ## Class shape

   ```kotlin
   @Component
   class <ComponentName>Workflow {

       @Workflow(
           idProperty = "<idProperty>",
           startOnEventClass = <TriggerEvent>::class,
           workflowNamespace = "<project-namespace>",   // same value as the project's @Event(namespace = ...)
           workflowName = "<ComponentName>Workflow",
       )
       fun execute(ctx: SimpleWorkflowContext) {
           val <idProperty> = ctx.workflowPayload().getValue("<idProperty>") as String

           // -------------- WAIT step (with try/catch for step timeout) --------------
           val confirmation = try {
               ctx.awaitEvent(
                   "<stepName>",
                   <Event>::class.java,
                   associate(payloadProperty("<correlationProperty>"), equalsTo(<idProperty>)),
               ) { it.timeout(Duration.ofSeconds(<timeoutSeconds>)) }
           } catch (e: StepTimedOutException) {
               // Spec.onTimeout commands are dispatched here.
               ctx.dispatch("<stepName>Timeout", <TimeoutCommand>(/* fields */))
               return
           }

           // -------------- DISPATCH step (at-least-once via awaitExecute) --------------
           ctx.dispatch("<stepName>", <Command>(/* fields from ctx.workflowPayload(), confirmation, ... */))

           // -------------- Final on-success DISPATCH (one per command in spec.onSuccess) --------------
           // The workflow succeeds by reaching the end of this body.
           ctx.dispatch("<stepName>OnSuccess", <OnSuccessCommand>(/* fields */))
       }

       /**
        * A DISPATCH step: an `execute` step whose action sends the command through the step's own
        * ProcessingContext. The step is recorded in the workflow's history, so after a crash a
        * completed dispatch is skipped on replay and an unconfirmed one is re-run (at-least-once).
        * The command itself is bounded by COMMAND_TIMEOUT; the step's own timeout stays long on
        * purpose, see "Testing the workflow".
        */
       private fun SimpleWorkflowContext.dispatch(stepName: String, command: Any) {
           awaitExecute(stepName, emptyMap(), PayloadProcessor { pc, _ ->
               CommandDispatcher.forContext(pc).send(command).resultMessage
                   .orTimeout(COMMAND_TIMEOUT.toSeconds(), TimeUnit.SECONDS)
                   .join()
               emptyMap()
           }) { it.timeout(LONG_WAIT) }
       }

       private companion object {
           val COMMAND_TIMEOUT: Duration = Duration.ofSeconds(5)
           val LONG_WAIT: Duration = Duration.ofDays(30)
       }

       // FAILED / CANCELLED terminals come from FAIL / CANCEL steps in the body (ctx.fail / ctx.cancel),
       // NOT from lifecycle handlers. Only add @WorkflowFailedHandler / @WorkflowCancelledHandler if you
       // separately need cleanup when the whole workflow is failed/cancelled (rare; the step DAG does not
       // model these hooks). Do NOT add @WorkflowTimedOutHandler for step-level timeouts — those are
       // handled by try/catch above.
   }
   ```

   The workflow class has no constructor dependencies: commands go out through `CommandDispatcher.forContext(pc)` inside the step action, which is what lets the test fixture instantiate it with `{ <ComponentName>Workflow() }`. Don't inject a `CommandGateway` and call `sendAndWait` from a `Supplier` — that dispatch would run outside the step's `ProcessingContext`.

   Keep the two timeouts in `dispatch` as they are. `COMMAND_TIMEOUT` on the command result is the real bound (wall clock). The step timeout is `LONG_WAIT` because an `execute` step measures its deadline from the STARTED event's timestamp while the check uses the configured clock; in the test fixture, where `timePasses(...)` moves only the configured clock, a dispatch step with the default 5-second timeout that starts after a 61-second jump is expired before it runs. `waitForEvent` steps don't have this problem (their start time comes from the configured clock).

   A dispatched command's result is available when a later step needs it: `CommandDispatcher.forContext(pc).send(command).resultAs(<Result>::class.java).join()` inside the `PayloadProcessor`, returned as an entry of the step's result map.

   FAILED / CANCELLED terminals come from `FAIL` / `CANCEL` steps in the body (`ctx.fail` / `ctx.cancel`), **not** from lifecycle hooks — and a step's `onFailure` pointer is a successor, never a handler (a null `onFailure` is retried, not terminal). Only add `@WorkflowFailedHandler` / `@WorkflowCancelledHandler` for the rare case where the *whole workflow* needs cleanup on failure/cancellation. **Never** generate `@WorkflowTimedOutHandler` for step-level event-wait timeouts. **Never** generate a completed-handler for the success commands — they are inline `dispatch(...)` calls at the end of the workflow body.

## Step generation rules

Walk the graph from `entry`. For each step, generate the engine equivalent inline in the `execute(...)` body (or as a `when (step)` arm in the dispatch-loop form — see "Loops"). Follow `on*` pointers to determine what comes next. **Terminal outcomes are explicit, not guessed**: a null `onSuccess` is `return` (COMPLETED); a null `onFailure`/`onTimeout` is left alone so the failure propagates and the engine retries (do NOT translate it to a `return` or a `fail`); a branch that ends FAILED / CANCELLED routes to an explicit `fail` / `cancel` step.

| DSL step    | Workflow code |
|---|---|
| `wait {name} for {Event} by {prop} [timeout {N}]` | `ctx.awaitEvent(name, Event::class.java, associate(payloadProperty(prop), equalsTo(<idValue>))) { it.timeout(Duration.ofSeconds(N)) }` — without a spec timeout use `{ it.timeout(LONG_WAIT) }`. With `timeout`, wrap in try/catch (see "Step timeouts"). |
| `dispatch {name} {Command}` | `ctx.dispatch(name, Command(/* fields */))`. Follow `onSuccess`/`onFailure` to their target steps; a null `onFailure` propagates and the engine retries. |
| `sleep {name} {N}s` | `ctx.sleep(name, Duration.ofSeconds(N))`, then continue via `onSuccess`. |
| `multi {name} {any\|all} [...]` | Open each inner WAIT via the non-blocking `ctx.waitForEvent(name, EventClass, associate(...)) { it.timeout(...) }` (returns a `WorkflowStepResult`), then join with `ctx.anyMatch(predicate, results...)` for `any` or `ctx.allMatch(predicate, results...)` for `all`. Both return a `CombinatorWorkflowStepResult`; call `.await()` on it. See "Multi" above for the full pattern. |
| `when {name} by {prop}` | `when (ctx.workflowPayload()[prop] as String?) { "STRIPE" -> { ... }; "PAYPAL" -> { ... }; else -> { ... default branch ... } }`. Switch on the exact trigger-property value. |
| `choice {name}` (`if cond -> tgt`…) | `if / else if / else` — one arm per ordered branch, first match wins. Implement each free-text `condition` as the real boolean against whatever's in scope (a captured `awaitEvent`/`awaitExecute` result, a payload value). `else` = the `default`. |
| `fail {name} {ExceptionName} ["{message}"]` | `ctx.fail(ExceptionName("message"))` — terminal, ends FAILED. Reference an existing exception or create a small `RuntimeException` subtype in the component package. |
| `cancel {name} ["{reason}"]` | `ctx.cancel("reason")` — terminal, ends CANCELLED. |

**Where command/event payload fields come from** — read them off the workflow's payload (`ctx.workflowPayload()["orderId"]`; the trigger event's fields) or off captured prior-event results (`val confirmation = ctx.awaitEvent(...); confirmation.txnId`). The DSL doesn't carry an explicit payload-mapping — pass the data the command's constructor needs from whichever scope it's available in.

**When `on*` pointers converge** — two failure branches that both flow into `cancel-order` need each branch to dispatch `cancel-order` itself (or jump to a helper function in the same class). For acyclic graphs there's no `goto`; extracting the convergent step into a `private fun cancelOrder(ctx: SimpleWorkflowContext) = ctx.dispatch("cancel-order", CancelOrder(...))` and calling it from both branches keeps the body readable. (Heavy convergence is also a signal to use the dispatch-loop form below.)

## Loops — back-edges and the step-dispatch form

A pointer may target an **earlier** step (a back-edge), forming a loop. **Only ever for a genuine *business* loop** — the process really repeats:
- **Polling**: `dispatch check → choice (ready? → exit : keep) → sleep → back to check`.
- **Decision rounds**: `wait decision → choice (approved? → publish : request-changes) → request-changes → back to wait`.

**Never** emit a loop to retry a failed command (that's the step's own concern — make the command idempotent; the runtime handles re-delivery) or to compensate (compensation is a *forward* path to compensating dispatches + a `fail`/`cancel` leaf). If the spec contains such a loop, treat it as a spec smell and raise it via `chat_with_platform`.

**Codegen for a graph with a back-edge — use a step-dispatch loop** (straight-line inlining can't express a cycle). Drive a `var step` through a `while`, one `when` arm per step; a successor is "return the next step name", a back-edge just returns an earlier name, terminals `return`/`fail`/`cancel`:

```kotlin
@Workflow(
    idProperty = "requestId",
    startOnEventClass = ServerRequested::class,
    workflowNamespace = "cycloforge",
    workflowName = "ServerProvisioningWorkflow",
)
fun execute(ctx: SimpleWorkflowContext) {
    val requestId = ctx.workflowPayload().getValue("requestId") as String
    var step: String? = "start"
    while (step != null) {
        step = when (step) {
            "start" -> { ctx.dispatch("start", StartProvisioning(requestId)); "check" }
            "check" -> {
                val checked = ctx.awaitExecute("check", emptyMap(), PayloadProcessor { pc, _ ->
                    val status = CommandDispatcher.forContext(pc)
                        .send(CheckProvisioningStatus(requestId))
                        .resultAs(ProvisioningStatus::class.java)
                        .orTimeout(COMMAND_TIMEOUT.toSeconds(), TimeUnit.SECONDS)
                        .join()
                    mapOf("status" to status.name)
                }) { it.timeout(LONG_WAIT) }
                ctx.setPayload("record-status", mapOf("status" to checked["status"]))
                "decide"
            }
            "decide" -> {
                when (ctx.workflowPayload()["status"]) {
                    "FAILED"  -> "give-up"
                    "RUNNING" -> "wait"     // ← keep polling
                    else      -> "mark-ready"
                }
            }
            "wait"       -> { ctx.sleep("wait", Duration.ofSeconds(30)); "check" }   // ← back-edge
            "mark-ready" -> { ctx.dispatch("mark-ready", MarkServerReady(requestId)); null }  // COMPLETED
            "give-up"    -> { ctx.fail(ProvisioningFailedException("provisioning did not complete")); null }
            else -> null
        }
    }
}
```

For an **acyclic** graph, prefer the straight-line form (it reads better). Use the dispatch loop only when there's a back-edge. Step names passed to `ctx.await*` are re-used across loop iterations — the runtime event-sources each re-entry; verify the replay behavior against your `axoniq-workflow` version if a looped workflow's history looks off.

## Why `awaitExecute` (not fire-and-forget)

Workflows are durable — they survive process restarts. If you sent a command from plain code between steps (a `CommandGateway` call outside any step), the workflow couldn't tell whether the command was actually dispatched on a previous run. Wrapping the dispatch in an `execute` step (`ctx.dispatch(...)` above is `awaitExecute` with the send as the step action) records the step's completion in the workflow's persistent state, so:

- If the dispatch completed before a crash, the resumed workflow skips it.
- If the dispatch did NOT complete, the resumed workflow re-runs it.

This gives at-least-once delivery. Make the dispatched command idempotent on the receiver side (the COMMAND component handles that — its decision model rejects duplicate operations) so the at-least-once doesn't cause double-effects.

## Version pairing

The skeleton declares `io.axoniq.framework:axoniq-workflow-spring-boot` (runtime + Spring Boot auto-configuration) and `io.axoniq.framework:axoniq-workflow-test` (test scope) at **0.2.0**, next to the `axoniq-framework-bom` at the latest 5.x release (5.3.x at the time of writing). That combination is verified: 0.2.0 is built against Axon Framework 5.2.0 and runs on 5.3.x.

Do **not** pin the BOM to 5.1.x and do **not** switch to `io.axoniq.framework.workflow:axon-workflow-*` 0.1.0. The library was renamed; 0.1.0 reads a field (`GenericEventMessage.clock`) that no longer exists in 5.2+, and the app fails at startup with `NoSuchFieldError ... clock`. If you see that error, the project is on the old coordinates: fix the build file, not the framework version.

0.2.0 is compiled with Kotlin 2.4. A project whose Kotlin compiler is older than 2.4 cannot read its metadata and fails to compile against it; the skeleton resolves the Kotlin version from Maven Central, so a fresh download is fine, an older checkout needs `kotlin.version` bumped.

The Spring Boot auto-configuration registers every `@Component` with a `@Workflow` method and provides the `SimpleWorkflowContextFactory`; no configuration class is needed. The workflow add-on prints a licence/entitlement notice at startup, which is informational for development.

## Testing the workflow

Write a workflow test for every component you scaffold. The test module ships a BDD fixture, `WorkflowTestFixture`, that runs the real workflow engine in **stepping mode**: events you publish drive the workflow, execute steps (your `dispatch(...)` calls) stop at the gate until the test releases them, and time is under the test's control. No mocks, no Axon Server, no `AxonTestFixture` (that one targets command handlers). (`axoniq-workflow` is a separate AxonIQ product, so it isn't covered by the `axoniq-app-development` plugin's testing guides.)

1. **Test dependency** — `io.axoniq.framework:axoniq-workflow-test` (test scope), same version as the runtime; the skeleton already declares it.
2. **Build the module** with `WorkflowTestFixture.workflowModule(SimpleWorkflowContext::class.java, { SimpleWorkflowContextFactory() }, { <ComponentName>Workflow() })`. The third lambda instantiates the workflow class — which is why it has no constructor dependencies.
3. **Create the fixture** with `WorkflowTestFixture.of(module) { configurer -> ... }` and disable the Axon Server connector enhancer in the customizer: with the Axon Server and Axoniq Platform starters on the classpath the connector enhancer is ServiceLoader-discovered, and without disabling it the fixture hangs on startup trying to connect.
4. **Drive** with `publishEvent(...)` (the trigger and the awaited events), `executionExists()` right after the trigger (it selects the started workflow; every step assertion and release below works on the selected execution and fails with "No workflow execution or workflow history is currently selected" without it), `executeReturning("<stepName>", emptyMap())` to release a dispatch step with a fake successful result (the command is **not** sent), `execute("<stepName>")` to run the real action instead, `executeFailing("<stepName>", StepFailedException("..."))` to fail it, and `timePasses(Duration)` to fire step timeouts.
5. **Assert** with `workflowFinished(WorkflowStatus.COMPLETED | FAILED | CANCELLED)`, `stepsPassed(...)`, `waitingIn(...)`, `step(name, StepStatus)`, `payloadContains(...)`.
6. **Stop** the fixture in `@AfterEach` with `fixture.then().stop()`.

Example (Kotlin — same shape in Java, just swap class syntax):

```kotlin
import io.axoniq.framework.axonserver.connector.configuration.AxonServerConfigurationEnhancer
import io.axoniq.workflow.dsl.simple.SimpleWorkflowContext
import io.axoniq.workflow.dsl.simple.SimpleWorkflowContextFactory
import io.axoniq.workflow.runtime.api.execution.status.WorkflowStatus
import io.axoniq.workflow.runtime.test.fixture.GivenWhen
import io.axoniq.workflow.runtime.test.fixture.Then
import io.axoniq.workflow.runtime.test.fixture.WorkflowTestFixture
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import java.time.Duration

class PaymentWindowWorkflowTest {

    private lateinit var fixture: WorkflowTestFixture<GivenWhen.Phase, Then.Phase>

    @BeforeEach
    fun setUp() {
        val module = WorkflowTestFixture.workflowModule(
            SimpleWorkflowContext::class.java,
            { SimpleWorkflowContextFactory() },
            { PaymentWindowWorkflow() },
        )
        fixture = WorkflowTestFixture.of(module) { configurer ->
            configurer.componentRegistry { it.disableEnhancer(AxonServerConfigurationEnhancer::class.java) }
        }
    }

    @AfterEach
    fun tearDown() = fixture.then().stop()

    @Test
    fun `ships the order when payment arrives before the window closes`() {
        fixture.given()
            .publishEvent(OrderPlaced(orderId = "order-1", customerId = "cust-1", total = 99.99))
            .executionExists()

        fixture.`when`()
            .publishEvent(PaymentReceived(orderId = "order-1", txnId = "txn-1"))
            .executeReturning("shipOrder", emptyMap())

        fixture.then()
            .workflowFinished(WorkflowStatus.COMPLETED)
            .stepsPassed("awaitPayment", "shipOrder")
    }

    @Test
    fun `cancels the order when payment doesn't arrive within the window`() {
        fixture.given()
            .publishEvent(OrderPlaced(orderId = "order-1", customerId = "cust-1", total = 99.99))
            .executionExists()

        fixture.`when`()
            .timePasses(Duration.ofSeconds(<timeoutSeconds> + 1L))
            .executeReturning("awaitPaymentTimeout", emptyMap())

        fixture.then()
            .workflowFinished(WorkflowStatus.COMPLETED)
            .stepsPassed("awaitPayment", "awaitPaymentTimeout")
    }
}
```

Key test types (import verbatim — easy to guess wrong):

- `io.axoniq.workflow.runtime.test.fixture.WorkflowTestFixture`, `GivenWhen`, `Then` (the phase types are `GivenWhen.Phase` / `Then.Phase`).
- `io.axoniq.workflow.dsl.simple.SimpleWorkflowContextFactory`.
- `io.axoniq.framework.axonserver.connector.configuration.AxonServerConfigurationEnhancer`.
- `io.axoniq.workflow.runtime.api.execution.status.WorkflowStatus` and, for `step(name, status)`, `io.axoniq.workflow.runtime.api.execution.status.StepStatus`.

What to cover (one test per scenario):

- **Happy path** — trigger event + every awaited event arrives in order, every dispatch released; assert `COMPLETED` and the step sequence with `stepsPassed`.
- **Each timeout** — for each `WaitStep` with a `timeoutSeconds`, publish the trigger, advance time past the window with `timePasses`, release the timeout dispatch; assert the terminal status the spec routes to and that the timeout step ran.
- **Each `fail` terminal** — drive the inputs that route to a `fail` step; assert `workflowFinished(WorkflowStatus.FAILED)`.
- **Each `cancel` terminal** — drive the inputs that route to a `cancel` step; assert `workflowFinished(WorkflowStatus.CANCELLED)`.

Notes:

- In stepping mode a dispatch step does not finish on its own. If an assertion times out with the workflow "waiting in" a step, the test forgot to release it with `executeReturning(...)` / `execute(...)`.
- Advance time once per test, past the wait you are testing. Any `execute` step that starts after the jump must have a timeout longer than the jump (the `dispatch` helper's `LONG_WAIT` covers this); a `sleep` that starts after the jump ends immediately, because its deadline is measured from the STARTED timestamp.
- This example was verified against a downloaded skeleton on axoniq-workflow 0.2.0 / Axon Framework 5.3.2 / Kotlin 2.4: both tests green in under two seconds.
- The method names are `execute`, `executeReturning`, `executeFailing` (the reference guide's `executeStep*` spelling belongs to a later release).
- `when` is a Kotlin keyword: write `fixture.\`when\`()`.
- `timePasses` moves the fixture clock and runs the due timeout tasks; wall-clock waits are never needed.
- Events must carry the correlation property the workflow's `idProperty` and associations read (e.g. `orderId`). If they don't, the trigger never starts a workflow and the waits never match.
- Every test runs the engine with the bare configurer's class-based `MessageTypeResolver`; `startOnEventClass` and the typed `awaitEvent` / `waitForEvent` resolve through the same resolver, so types line up. That is the reason to prefer `startOnEventClass` over `startOnEventName`.

## Boundaries

- Don't put validation logic in workflow steps. Validation lives in the dispatched command's handler.
- Do wrap each `wait` with a `timeout` in try/catch and route to the `onTimeout` pointer's step. `@WorkflowTimedOutHandler` is for whole-workflow termination, not step-level event-wait timeouts.
- Don't redefine events/commands; reference shared ones from `api/events` and `api/commands`.
- Don't import from Axon Framework 4, and don't use the 0.1.0 names (`startOnEvent`, `AssociationsUtils`, `ctx.waitFor`, `@OnFailure`, `AbstractDeclarativeTestBase`).
- Don't use `AxonTestFixture` for workflow tests — it targets command handlers. Use `WorkflowTestFixture` as shown above.
- Don't try to splice DSL changes into an existing workflow class by hand — when the DSL body changes, regenerate the `execute(...)` body from the new DAG.

## When to stop and ask

- The DSL fails to parse, or contains a step kind you don't recognise (`workflow_dsl.md` defines exactly eight: `wait`, `dispatch`, `sleep`, `multi`, `when`, `choice`, `fail`, `cancel`). Workflows never publish events themselves — only command handlers do; if the spec implies the workflow should "emit" something, dispatch a command to a COMMAND component instead.
- A `wait` step's `correlationProperty` isn't a field on the awaited event's payload — that's a Platform-side spec issue; surface via `chat_with_platform` (or capture as a `QUESTION` note).
- The DSL declares a `multi` step with semantics not covered by `ctx.anyMatch` / `ctx.allMatch` (e.g. quorum, "first N of M") — confirm with `chat_with_platform` before writing speculative code.
- The component package already exists with a different `componentId` in `.axoniq`.
- Compile fails after writing files.
