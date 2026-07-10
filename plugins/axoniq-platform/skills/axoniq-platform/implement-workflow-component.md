# Implementing a WORKFLOW component

A WORKFLOW component is a long-running, event-sourced orchestration powered by Axon Framework 5's `@Workflow`. It starts on a single trigger event, then walks a directed graph of steps — waiting on correlated events (with optional timeouts), dispatching commands, fanning out via parallel waits, or branching on payload data — until it terminates.

**Always load [implementation-base.md](implementation-base.md) first** for shared package layout, imports, and the "no Axon 4" rule. This skill builds on top.

## Inputs

- `projectId` and `workspaceId` from `./.axoniq` at the repo root.
- `componentId` provided by [SKILL.md](SKILL.md).
- Component spec fetched via MCP: `get_component_details(projectId, componentId)`. For a WORKFLOW the response carries:
  - `triggerEvent` — the event message whose arrival starts the workflow. Derive `@Workflow startOnEvent` from this as the Axon **message-type string** `"<event-namespace>.<EventName>"` (the same `namespace`/`name` declared on the event class's `@Event(...)` annotation), NOT the Java FQN — see the `startOnEvent` note below,
  - `idProperty` — the correlation key (e.g. `"orderId"`),
  - `entryStep` — the name of the first step to execute,
  - `steps[]` — the list of steps. Each entry has a `kind` (`WAIT` / `DISPATCH` / `SLEEP` / `MULTI` / `WHEN` / `CHOICE` / `FAIL` / `CANCEL`) and the relevant fields for that kind, plus `on*` pointers (`onSuccess`, `onFailure`, `onTimeout`) naming the next step on each outcome. A pointer may name an **earlier** step (a back-edge) — that's a business loop (see "Loops" below). Terminal status: a null `onSuccess` ends the body normally (COMPLETED); a null `onFailure`/`onTimeout` is NOT terminal — the step failure propagates and the engine retries. FAILED / CANCELLED are reached only by routing to an explicit `FAIL` (`ctx.fail`) or `CANCEL` (`ctx.cancel`) step.

Don't read or write spec files on disk — the spec lives on the Platform.

[SKILL.md](SKILL.md) picks the component as eligible in one of two modes:

- **Fresh implementation**: MCP component status is `APPROVED` and no `<component_pkg>/.axoniq` marker exists. Write the marker first, then the workflow class and message references.
- **Extend mode**: marker exists, but the spec (re-fetched via MCP) has different steps or pointers. Diff against the existing workflow class and update only the changed paths. The structured `steps[]` makes the diff direct — no text parsing needed.

## Step DAG → AF5 translation overview

The spec is a graph of named steps; each step has `on*` pointers to its successor(s). You translate it into imperative code inside a single `@Workflow` method, following the edges from `entryStep`. **Codegen strategy (hybrid):** if the graph is **acyclic**, emit straight-line code (await/dispatch in sequence, `when`/`if` for branches) as in the examples below. If the graph has a **back-edge** (a pointer to an already-visited step — a loop), emit a **step-dispatch loop** instead so the cycle compiles (see "Loops" below). Eight step kinds map cleanly to AF5 primitives:

| Step kind                                  | AF5 translation                                                                                                                              |
|---|---|
| `WAIT` (no timeout)                       | `ctx.awaitEvent(name, Event::class.java, associate(payloadProperty(prop), equalsTo(...)))` — captures the event payload for downstream steps |
| `WAIT` (with `timeoutSeconds`)            | Same `awaitEvent` with a `Duration.ofSeconds(N)` argument **wrapped in try/catch** for `StepFailedException` (see "Step timeouts" below) |
| `DISPATCH`                                | `ctx.awaitExecute(name, Void::class.java, Supplier { commandGateway.sendAndWait(Command(...)); null })`. Route `onSuccess`/`onFailure` to their target steps; a null `onFailure` propagates so the engine retries. |
| `SLEEP`                                   | `ctx.sleep(name, Duration.ofSeconds(N))`, then continue via `onSuccess`. Used to pace a business poll loop. |
| `MULTI`                                   | Non-blocking `ctx.waitFor(...)` for each inner WAIT (returns `WorkflowStepResult`), then race them via `ctx.anyMatch(predicate, results...)` (`ANY`) or `ctx.allMatch(predicate, results...)` (`ALL`) — see "Multi" below. |
| `WHEN`                                    | A Kotlin `when (ctx.workflowPayload().get(property) as String?)` over the exact trigger-property value, one arm per case + `else` for default. |
| `CHOICE`                                  | An `if / else if / else` chain — **one arm per ordered branch**, first match wins. Implement each branch's free-text `condition` as the actual boolean against whatever's in scope (a captured `awaitEvent`/`awaitExecute` result, a payload counter, etc.). `default` is the `else`. |
| `FAIL`                                    | `ctx.fail(<exceptionName>("<message>"))` — terminal, ends FAILED. The exception is a normal `RuntimeException` subtype; reference an existing one or create a small one in the component package. |
| `CANCEL`                                  | `ctx.cancel("<reason>")` — terminal, ends CANCELLED. A deliberate, non-error stop. |
| `onSuccess` = null                        | `return` — end of body = COMPLETED |
| `onTimeout` = null                        | leave it: the WAIT's timeout try/catch has no handler branch, so the `StepFailedException` propagates and the engine retries. To act on a timeout the spec routes `onTimeout` to a step. (A step timeout never becomes the workflow TIMED_OUT state.) |
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

   **Imports — exact package names for `axon-workflow` 0.1.0 (do NOT invent):**
   ```kotlin
   import io.axoniq.workflow.runtime.api.annotation.Workflow
   import io.axoniq.workflow.runtime.api.annotation.OnFailure
   import io.axoniq.workflow.runtime.api.annotation.OnCancellation
   import io.axoniq.workflow.runtime.api.execution.status.WorkflowStatus
   import io.axoniq.workflow.runtime.api.execution.state.StepFailedException
   import io.axoniq.workflow.runtime.association.PayloadPropertyValueRetriever.payloadProperty
   import io.axoniq.workflow.dsl.simple.SimpleWorkflowContext
   import io.axoniq.workflow.dsl.simple.SimpleWorkflowContext.equalsTo
   import io.axoniq.workflow.dsl.api.AssociationsUtils.associate
   import java.util.function.Supplier
   ```

   Note these specifics — they trip people up (every one of these has bitten implementers):
   - `associate` is on **`io.axoniq.workflow.dsl.api.AssociationsUtils`** (NOT `Associations`).
   - `payloadProperty` is on **`io.axoniq.workflow.runtime.association.PayloadPropertyValueRetriever`** — a different package from `associate`.
   - `equalsTo` is a static helper on **`io.axoniq.workflow.dsl.simple.SimpleWorkflowContext`** (NOT on `AssociationsUtils`).
   - `WorkflowStatus` lives under **`io.axoniq.workflow.runtime.api.execution.status`** (the lifecycle hook annotations are under `runtime.api.annotation` — different sub-package).
   - `StepFailedException` lives under **`io.axoniq.workflow.runtime.api.execution.state`** (NOT `runtime.api.exception` — there is no such package).
   - The `@Workflow` annotation parameter is **`startOnEvent`**, a String containing the **Axon message-type** of the trigger event — `"<event-namespace>.<EventName>"` (the same `namespace` + `name` declared on the event class's `@Event(namespace = "...", name = "...")` annotation). NOT the Java FQN, and NOT `startOnEventClass = TriggerEvent::class`. The runtime registers workflow definitions in a map keyed by this message-type string and matches incoming events by the same key (e.g. `cycloforge.BikeRequested` — versions append as `#<version>` when published but `startOnEvent` only needs `namespace.name`). If you put the Java FQN here, the registry never matches the incoming event type and the workflow silently never triggers — no error is logged. To verify in tests, `PrettyPrintingRecordingEventStore`'s `workflowDefinitions` section shows what was registered; the string there must match the published event's type.
   - `@OnTimeout` does **NOT** fire when a step's `awaitEvent(...)` exceeds its `Duration` — see "Step timeouts" below. Don't import or use it for that case.
   - `ctx.awaitExecute(name, ResultClass, lambda)` is **overloaded** between `Function<Map<String, Object>, T>` and `Supplier<T>`. From Kotlin, the compiler can't pick — wrap the lambda in `Supplier { ... }` explicitly. Java callers don't have this problem because lambda target-typing handles it.
   - The spec's workflow-level `onSuccess` commands are **NOT** dispatched via `@OnSuccess`. They are just DISPATCH steps that happen at the end of the workflow body — the workflow succeeds by reaching the end of `execute(...)` normally. Don't import `@OnSuccess`.

   ## Step timeouts — use try/catch, NOT @OnTimeout

   When a step's `awaitEvent(...)` exceeds its `Duration`, it throws `StepFailedException` (the *step* status is `TIMED_OUT` — this does **not** put the *workflow* in the TIMED_OUT state). If the spec gives the wait an `onTimeout` pointer, wrap the `awaitEvent` in a try/catch and, in the catch, do whatever that pointer's step is (dispatch a compensating command, `ctx.fail(...)`, `ctx.cancel(...)`, or continue to the next step). If `onTimeout` is **null**, do **not** catch it — let the `StepFailedException` propagate so the engine retries (per the spec's "null onTimeout is not terminal").

   The `@OnTimeout` lifecycle annotation fires for a different concern (the whole-workflow overall timeout) — **not** for step-level event-wait timeouts. Do not rely on it to handle "the user didn't pay in time".

   Per-step timeout pattern:

   ```kotlin
   try {
       val confirmation = ctx.awaitEvent(
           "<stepName>",
           <Event>::class.java,
           associate(
               payloadProperty("<correlationProperty>"),
               equalsTo(ctx.workflowPayload().get("<idProperty>")),
           ),
           Duration.ofSeconds(<timeoutSeconds>),
       )
       // happy path: continue with subsequent steps using `confirmation`
   } catch (e: StepFailedException) {
       // The wait timed out (or otherwise failed/was cancelled).
       // Dispatch the timeout-handling command(s) from the spec's onTimeout list.
       // NOTE: Supplier { ... } wrapper is required to disambiguate the awaitExecute overload from Kotlin.
       ctx.awaitExecute("<stepName>Timeout", Void::class.java, Supplier {
           commandGateway.sendAndWait(<TimeoutCommand>(/* fields from ctx.workflowPayload() */))
           null
       })
       return  // Stop the workflow body — subsequent steps would assume the wait succeeded.
   }
   ```

   Mapping from the spec to this pattern:
   - The spec's workflow-level `onTimeout` list of commands is what gets dispatched from the catch block of the WAIT step that "owns" the timeout. If multiple WAIT steps could time out, attribute the `onTimeout` commands to the most natural owner (typically the first WAIT, since later steps don't run after a timeout). If the spec is ambiguous, replicate the catch block per WAIT.
   - Wrap each WAIT step in its own try/catch so subsequent steps don't run after a timeout.
   - Dispatch the timeout commands inside `ctx.awaitExecute(...)` — same at-least-once guarantee as a normal DISPATCH step.

   ## Multi — parallel waits with `waitFor` + `anyMatch` / `allMatch`

   When the spec has a `MULTI` step racing two or more WAITs (typical: "either confirmation X arrives OR cancellation Y arrives, whichever first"), use the non-blocking `ctx.waitFor(...)` API and then combine the resulting `WorkflowStepResult`s with `ctx.anyMatch(...)` or `ctx.allMatch(...)`.

   **Key distinction from a single WAIT:**

   - `ctx.awaitEvent(name, EventClass, associations, [timeout])` — **blocking**. Returns the event payload directly. Use for a single WAIT step.
   - `ctx.waitFor(name, EventClass, associations, [timeout])` — **non-blocking**. Returns a `WorkflowStepResult` handle representing an in-flight wait. Combine multiple via `anyMatch` / `allMatch`.

   **Combinators:**

   - `ctx.anyMatch(predicate: Predicate<WorkflowStepResult>, vararg results: WorkflowStepResult): CombinatorWorkflowStepResult` — completes when **any** inner result matches the predicate.
   - `ctx.allMatch(predicate: Predicate<WorkflowStepResult>, vararg results: WorkflowStepResult): CombinatorWorkflowStepResult` — completes when **all** inner results match.

   `WorkflowStepResult` (0.1.0) exposes `isCompleted()`, `success()`, `failure()`, `timeout()`, and `getStepName()` (`.stepName` in Kotlin) — there is **no** `completed` property and **no** `completedStepName()`. The combinator (`CombinatorWorkflowStepResult`) exposes `matched()` / `unmatched()`; the winning inner step is `matched().firstOrNull()`.

   > ⚠️ **The predicate MUST be `{ it.success() }`, not `{ it.isCompleted() }`.** On a WAIT that hits its timeout, `isCompleted()` returns **true** — so `{ it.isCompleted() }` matches a timed-out wait and routes to its "arrived" branch (e.g. mark-bike-in-use instead of reject-on-timeout). With `success()`, a timed-out wait is NOT matched, so `matched()` comes back empty and control correctly falls to the else/timeout branch.

   **Pattern for `MULTI ANY` (race — first to arrive wins):**

   ```kotlin
   // Open both waits non-blocking; each returns a handle, not the event.
   val payCompleted = ctx.waitFor(
       "awaitPaymentCompleted",
       PaymentCompleted::class.java,
       associate(payloadProperty("rentalId"), equalsTo(ctx.workflowPayload().get("rentalId"))),
       Duration.ofSeconds(120),
   )
   val payCancelled = ctx.waitFor(
       "awaitPaymentCancelled",
       PaymentCancelled::class.java,
       associate(payloadProperty("rentalId"), equalsTo(ctx.workflowPayload().get("rentalId"))),
       Duration.ofSeconds(120),
   )

   // Race them — first to SUCCEED wins. (success(), not isCompleted(): a timed-out wait is
   // "completed" but not successful — see the warning above.)
   val winner = ctx.anyMatch({ it.success() }, payCompleted, payCancelled)

   // Branch on which inner step succeeded; matched() is empty if all timed out → else branch.
   when (winner.matched().firstOrNull()?.stepName) {
       "awaitPaymentCompleted" -> ctx.awaitExecute("markBikeInUse", Void::class.java, Supplier {
           commandGateway.sendAndWait(MarkBikeInUse(rentalId = ctx.workflowPayload().get("rentalId") as String))
           null
       })
       "awaitPaymentCancelled" -> ctx.awaitExecute("rejectRental", Void::class.java, Supplier {
           commandGateway.sendAndWait(RejectRental(rentalId = ctx.workflowPayload().get("rentalId") as String, reason = "PAYMENT_CANCELLED"))
           null
       })
       else -> {
           // Both timed out — handle the spec's onTimeout.
           ctx.awaitExecute("rejectOnTimeout", Void::class.java, Supplier {
               commandGateway.sendAndWait(RejectRental(rentalId = ctx.workflowPayload().get("rentalId") as String, reason = "TIMEOUT"))
               null
           })
       }
   }
   ```

   **Pattern for `MULTI ALL` (gather — wait for every inner to complete):**

   ```kotlin
   val partA = ctx.waitFor("partA", PartAReceived::class.java, associate(...), Duration.ofSeconds(N))
   val partB = ctx.waitFor("partB", PartBReceived::class.java, associate(...), Duration.ofSeconds(N))
   ctx.allMatch({ it.success() }, partA, partB)
   // Both arrived — read payloads off the individual results if needed.
   ```

   **Mapping from the spec:**

   - The MULTI's `innerSteps` list → one `ctx.waitFor(...)` per name, in the same order.
   - MULTI mode `ANY` → `ctx.anyMatch(...)`; mode `ALL` → `ctx.allMatch(...)`.
   - MULTI's per-inner `on*` pointers → branches in the `when (winner.matched().firstOrNull()?.stepName) { ... }`.
   - MULTI's `timeoutSeconds` → `Duration.ofSeconds(N)` on each inner `waitFor` (the runtime treats every inner as timed out if none completes within the window; the `else` branch in `when` handles that case for `anyMatch`).

   Do NOT replace `waitFor` with `awaitEvent` inside a MULTI — `awaitEvent` is blocking and would serialise the waits instead of racing them.

   ## Class shape

   ```kotlin
   @Component
   class <ComponentName>Workflow(
       private val commandGateway: CommandGateway,
   ) {

       @Workflow(
           idProperty = "<idProperty>",
           // Axon message-type — "<namespace>.<EventName>" from the trigger event's @Event annotation.
           // NOT the Java FQN: the runtime keys workflows by this string and silently fails to trigger if it doesn't match.
           startOnEvent = "<event-namespace>.<TriggerEventName>",
       )
       fun execute(ctx: SimpleWorkflowContext) {
           // -------------- WAIT step (with try/catch for step timeout) --------------
           val confirmation = try {
               ctx.awaitEvent(
                   "<stepName>",
                   <Event>::class.java,
                   associate(
                       payloadProperty("<correlationProperty>"),
                       equalsTo(ctx.workflowPayload().get("<idProperty>")),
                   ),
                   Duration.ofSeconds(<timeoutSeconds>),
               )
           } catch (e: StepFailedException) {
               // Spec.onTimeout commands are dispatched here.
               ctx.awaitExecute("<stepName>Timeout", Void::class.java, Supplier {
                   commandGateway.sendAndWait(<TimeoutCommand>(/* fields */))
                   null
               })
               return
           }

           // -------------- DISPATCH step (at-least-once via awaitExecute) --------------
           // Supplier { ... } wrapper required to disambiguate the awaitExecute overload from Kotlin.
           ctx.awaitExecute("<stepName>", Void::class.java, Supplier {
               commandGateway.sendAndWait(
                   <Command>(/* fields from ctx.workflowPayload() and prior step results */)
               )
               null
           })

           // -------------- Final on-success DISPATCH (one per command in spec.onSuccess) --------------
           // The workflow succeeds by reaching the end of this body. Spec's onSuccess commands are
           // dispatched here as ordinary awaitExecute calls — NOT via @OnSuccess.
           ctx.awaitExecute("<stepName>OnSuccess", Void::class.java, Supplier {
               commandGateway.sendAndWait(<OnSuccessCommand>(/* fields */))
               null
           })
       }

       // FAILED / CANCELLED terminals come from FAIL / CANCEL steps in the body (ctx.fail / ctx.cancel),
       // NOT from lifecycle hooks. Only add @OnFailure / @OnCancellation if you separately need cleanup
       // when the whole workflow is failed/cancelled (rare; the step DAG does not model these hooks).
       // Do NOT add @OnTimeout for step-level timeouts — those are handled by try/catch above.
       // Do NOT add @OnSuccess — success commands are inline DISPATCH steps at the end of the body.
   }
   ```

   FAILED / CANCELLED terminals come from `FAIL` / `CANCEL` steps in the body (`ctx.fail` / `ctx.cancel`), **not** from lifecycle hooks — and a step's `onFailure` pointer is a successor, never an `@OnFailure` hook (a null `onFailure` is retried, not terminal). Only add `@OnFailure` / `@OnCancellation` for the rare case where the *whole workflow* needs cleanup on failure/cancellation. **Never** generate `@OnTimeout` for step-level event-wait timeouts. **Never** generate `@OnSuccess` — success commands are inline `awaitExecute(...)` calls at the end of the workflow body.

   The `@Workflow.startOnEvent` value is the **Axon message-type** of the trigger event — `"<event-namespace>.<EventName>"` matching the `namespace` and `name` arguments on the event class's `@Event(...)` annotation. Read those values off the event class itself (e.g. `@Event(namespace = "cycloforge", name = "BikeRequested")` → `"cycloforge.BikeRequested"`); do NOT compute a Java FQN from the package layout — the runtime keys by the message-type string, not the class name, and a Java FQN will silently never match.

## Step generation rules

Walk the graph from `entry`. For each step, generate the AF5 equivalent inline in the `execute(...)` body (or as a `when (step)` arm in the dispatch-loop form — see "Loops"). Follow `on*` pointers to determine what comes next. **Terminal outcomes are explicit, not guessed**: a null `onSuccess` is `return` (COMPLETED); a null `onFailure`/`onTimeout` is left alone so the failure propagates and the engine retries (do NOT translate it to a `return` or a `fail`); a branch that ends FAILED / CANCELLED routes to an explicit `fail` / `cancel` step.

| DSL step    | AF5 code |
|---|---|
| `wait {name} for {Event} by {prop} [timeout {N}]` | `ctx.awaitEvent(name, Event::class.java, associate(payloadProperty(prop), equalsTo(ctx.workflowPayload().get(idProperty)))` + optional `, Duration.ofSeconds(N))`. With `timeout`, wrap in try/catch (see "Step timeouts"). |
| `dispatch {name} {Command}` | `ctx.awaitExecute(name, Void::class.java, Supplier { commandGateway.sendAndWait(Command(/* fields */)); null })`. Follow `onSuccess`/`onFailure` to their target steps; a null `onFailure` propagates and the engine retries. |
| `sleep {name} {N}s` | `ctx.sleep(name, Duration.ofSeconds(N))`, then continue via `onSuccess`. |
| `multi {name} {any\|all} [...]` | Open each inner WAIT via the non-blocking `ctx.waitFor(name, EventClass, associate(...), Duration)` (returns a `WorkflowStepResult`), then join with `ctx.anyMatch(predicate, results...)` for `any` or `ctx.allMatch(predicate, results...)` for `all`. Both return a `CombinatorWorkflowStepResult`. See "Multi" below for the full pattern. |
| `when {name} by {prop}` | `when (ctx.workflowPayload().get(prop) as String?) { "STRIPE" -> { ... }; "PAYPAL" -> { ... }; else -> { ... default branch ... } }`. Switch on the exact trigger-property value. |
| `choice {name}` (`if cond -> tgt`…) | `if / else if / else` — one arm per ordered branch, first match wins. Implement each free-text `condition` as the real boolean against whatever's in scope (a captured `awaitEvent`/`awaitExecute` result, a payload value). `else` = the `default`. |
| `fail {name} {ExceptionName} ["{message}"]` | `ctx.fail(ExceptionName("message"))` — terminal, ends FAILED. Reference an existing exception or create a small `RuntimeException` subtype in the component package. |
| `cancel {name} ["{reason}"]` | `ctx.cancel("reason")` — terminal, ends CANCELLED. |

**Where command/event payload fields come from** — read them off the workflow's payload (`ctx.workflowPayload().get("orderId")`) or off captured prior-event results (`val confirmation = ctx.awaitEvent(...); confirmation.txnId`). The DSL doesn't carry an explicit payload-mapping — pass the data the command's constructor needs from whichever scope it's available in.

**When `on*` pointers converge** — two failure branches that both flow into `cancel-order` need each branch to dispatch `cancel-order` itself (or jump to a helper function in the same class). For acyclic graphs there's no `goto`; extracting the convergent step into a `private fun cancelOrder(ctx: SimpleWorkflowContext) = ctx.awaitExecute("cancel-order", ...)` and calling it from both branches keeps the body readable. (Heavy convergence is also a signal to use the dispatch-loop form below.)

## Loops — back-edges and the step-dispatch form

A pointer may target an **earlier** step (a back-edge), forming a loop. **Only ever for a genuine *business* loop** — the process really repeats:
- **Polling**: `dispatch check → choice (ready? → exit : keep) → sleep → back to check`.
- **Decision rounds**: `wait decision → choice (approved? → publish : request-changes) → request-changes → back to wait`.

**Never** emit a loop to retry a failed command (that's the step's own concern — make the command idempotent; the runtime handles re-delivery) or to compensate (compensation is a *forward* path to compensating dispatches + a `fail`/`cancel` leaf). If the spec contains such a loop, treat it as a spec smell and raise it via `chat_with_platform`.

**Codegen for a graph with a back-edge — use a step-dispatch loop** (straight-line inlining can't express a cycle). Drive a `var step` through a `while`, one `when` arm per step; a successor is "return the next step name", a back-edge just returns an earlier name, terminals `return`/`fail`/`cancel`:

```kotlin
@Workflow(idProperty = "requestId", startOnEvent = "cycloforge.ServerRequested")
fun execute(ctx: SimpleWorkflowContext) {
    var step: String? = "start"
    while (step != null) {
        step = when (step) {
            "start" -> { ctx.awaitExecute("start", Void::class.java, Supplier { commandGateway.sendAndWait(StartProvisioning(/*…*/)); null }); "check" }
            "check" -> { val s = ctx.awaitExecute("check", ProvisioningStatus::class.java, Supplier { commandGateway.sendAndWait(CheckProvisioningStatus(/*…*/)) }); ctx.setPayload("check", mapOf("status" to s)); "decide" }
            "decide" -> {
                val status = ctx.workflowPayload().get("status")
                when {
                    status == "FAILED"  -> "give-up"
                    status == "RUNNING" -> "wait"     // ← keep polling
                    else                -> "mark-ready"
                }
            }
            "wait"       -> { ctx.sleep("wait", Duration.ofSeconds(30)); "check" }   // ← back-edge
            "mark-ready" -> { ctx.awaitExecute("mark-ready", Void::class.java, Supplier { commandGateway.sendAndWait(MarkServerReady(/*…*/)); null }); null }  // COMPLETED
            "give-up"    -> { ctx.fail(ProvisioningFailedException("provisioning did not complete")); null }
            else -> null
        }
    }
}
```

For an **acyclic** graph, prefer the straight-line form (it reads better). Use the dispatch loop only when there's a back-edge. Step names passed to `ctx.await*` are re-used across loop iterations — the runtime event-sources each re-entry; verify the replay behavior against your `axon-workflow` version if a looped workflow's history looks off.

## Why `awaitExecute` (not fire-and-forget)

Workflows are durable — they survive process restarts. If you used `commandGateway.send(cmd, null)` directly (fire-and-forget), the workflow couldn't tell whether the command was actually dispatched on a previous run. Wrapping the dispatch in `ctx.awaitExecute(...)` records the step's completion in the workflow's persistent state, so:

- If the dispatch completed before a crash, the resumed workflow skips it.
- If the dispatch did NOT complete, the resumed workflow re-runs it.

This gives at-least-once delivery. Make the dispatched command idempotent on the receiver side (the COMMAND component handles that — its decision model rejects duplicate operations) so the at-least-once doesn't cause double-effects.

## Version pairing

`axon-workflow` **0.1.0** requires **Axon Framework 5.1.x**. Pin `io.axoniq.framework:axoniq-framework-bom` to **5.1.2** (matching `axoniq-platform-client` 5.1.1), and keep `axon-workflow` / `axon-workflow-test` on the matched set. Do **not** let the BOM float to **5.2.0-RC1**: it removed `GenericEventMessage.clock`, which the workflow runtime reads reflectively when creating a workflow → `NoSuchFieldError` at workflow-creation time. That's a **runtime** failure (the app, not just tests) — if a freshly generated project throws `NoSuchFieldError` mentioning `clock`, it's a framework/workflow version mismatch, not your code.

> ⚠️ **Check this first when scaffolding a WORKFLOW.** The downloaded skeleton fills the framework version from the **latest** release on Maven Central, so a fresh project may already be on **5.2.0+** and will hit the error above the moment a workflow is created. Before implementing a workflow, open `pom.xml` (or `build.gradle.kts`) and pin the `axoniq-framework-bom` version to **5.1.2**. This is a one-line change in the generated project — you do not need to touch anything on the Platform.

## Testing the workflow

Write a workflow test for every component you scaffold. The workflow framework ships a dedicated test base — `AbstractDeclarativeTestBase` — that runs the real workflow against scheduled events; no mocking. (`axon-workflow` is a separate AxonIQ product, so it isn't covered by the `axoniq-app-development` plugin's testing guides — see `testing/basics.md` / `testing/advanced.md` there only for general AF5 fixture testing.) The pattern is:

1. **Add the test dependency** — `io.axoniq.framework.workflow:axon-workflow-test:<version>` (test scope). Pair the version with your `axon-workflow` runtime and framework — see **Version pairing** below.
2. **Pick a context type** — `SimpleWorkflowContext` is the default; only roll your own when the workflow needs custom shared state.
3. **Extend `io.axoniq.workflow.runtime.test.AbstractDeclarativeTestBase<T>`** and pass the DSL/context type + a context-factory builder through the super constructor: `AbstractDeclarativeTestBase(Class<T> dslType, ComponentBuilder<WorkflowContextFactory<T>> contextFactoryBuilder)`.
4. **Declare the workflow under test** by overriding **`getDeclaredDefinition()`** (SINGULAR) → `Function<DetectionPhase<T>, FinalizedPhase<T>>`. For an annotated `@Workflow` class use the **single-arg** `d.autodetected({ MyWorkflow() })` — it reads the trigger (`startOnEvent`) and id property off the annotation. (There is **no** 2-arg `autodetected(builder, contextType)`.)
5. **Override `configure()`** — `protected UnaryOperator<WorkflowConfigurer>` — with the **two essential registrations** shown in the skeleton: disable `AxonServerConfigurationEnhancer`, and register `AnnotationMessageTypeResolver`. Skip either and the test hangs on startup or never triggers (see the notes).
6. **Schedule events** via `delayedPublisher.addSchedules(listOf(ofMillis(<t>, <event>), ...))` to drive the trigger AND the awaited events. Pick offsets that respect step ordering.
7. **Start the engine** with `delayedPublisher.start()`. The workflow engine is an event handler, so publishing the scheduled events drives it — there is **no** `workflowEngine.runWorkflows(...)` call.
8. **Assert** via Awaitility on `workflowHistoryRepository`: `state().workflowStatus()` (`COMPLETED` / `FAILED` / `TIMED_OUT` / `CANCELLED`) and `state().workflowStepNames()` for the executed step sequence.

Example skeleton (Kotlin — same shape in Java, just swap class syntax):

```kotlin
class PaymentWindowWorkflowTest : AbstractDeclarativeTestBase<SimpleWorkflowContext>(
    SimpleWorkflowContext::class.java,
    { SimpleWorkflowContextFactory() },
) {
    // SINGULAR getDeclaredDefinition, returning Function<DetectionPhase, FinalizedPhase>.
    // autodetected takes ONE arg — it reads startOnEvent + idProperty from the @Workflow annotation.
    override fun getDeclaredDefinition(): Function<DetectionPhase<SimpleWorkflowContext>, FinalizedPhase<SimpleWorkflowContext>> =
        Function { d -> d.autodetected({ PaymentWindowWorkflow() }) }

    // TWO essential registrations — omit either and the test does not work:
    //  1. disableEnhancer(AxonServerConfigurationEnhancer) — with the Axon Server + Axoniq Platform
    //     starters on the classpath the connector enhancer is ServiceLoader-discovered and the test
    //     hangs on startup, failing with ProcessRetriesExhaustedException. FQN:
    //     io.axoniq.framework.axonserver.connector.configuration.AxonServerConfigurationEnhancer
    //  2. register AnnotationMessageTypeResolver — the bare WorkflowConfigurer uses a CLASS-based
    //     MessageTypeResolver, so the incoming event's type never matches the workflow's
    //     `startOnEvent` ("namespace.name") and the workflow never triggers. AnnotationMessageTypeResolver
    //     reads @Event(namespace, name), so the types line up.
    override fun configure(): UnaryOperator<WorkflowConfigurer> = UnaryOperator { configurer ->
        configurer.componentRegistry { cr ->
            cr.disableEnhancer(AxonServerConfigurationEnhancer::class.java)
            cr.registerComponent(MessageTypeResolver::class.java) { AnnotationMessageTypeResolver() }
        }
    }

    @Test
    fun `completes happy path when payment arrives before timeout`() {
        delayedPublisher.addSchedules(listOf(
            ofMillis(500,  OrderPlaced(orderId = "order-1", customerId = "cust-1", total = 99.99)),
            ofMillis(2_000, PaymentReceived(orderId = "order-1", txnId = "txn-1")),
        ))
        delayedPublisher.start()   // publishing the scheduled events drives the engine — no manual "run" call.

        await().atMost(30, TimeUnit.SECONDS).untilAsserted {
            assertThat(workflowHistoryRepository.findAll())
                .isNotEmpty
                .allMatch { it.state().workflowStatus().isTerminal }
        }

        val history = workflowHistoryRepository.findAll().single()
        assertThat(history.state().workflowStatus()).isEqualTo(WorkflowStatus.COMPLETED)
        assertThat(history.state().workflowStepNames()).containsExactly(
            "awaitPayment",   // WaitStep
            "shipOrder",      // success hook → dispatch
        )
    }

    @Test
    fun `dispatches cancel when payment doesn't arrive within window`() {
        delayedPublisher.addSchedules(listOf(
            ofMillis(500, OrderPlaced(orderId = "order-1", customerId = "cust-1", total = 99.99)),
            // No PaymentReceived — let the WaitStep timeout fire.
        ))
        delayedPublisher.start()

        await().atMost(<timeoutSeconds + buffer>, TimeUnit.SECONDS).untilAsserted {
            val history = workflowHistoryRepository.findAll().single()
            assertThat(history.state().workflowStatus()).isEqualTo(WorkflowStatus.TIMED_OUT)
            assertThat(history.state().workflowStepNames()).contains("cancelOrder")
        }
    }
}
```

Key test types (import verbatim — easy to guess wrong):

- `io.axoniq.workflow.runtime.test.AbstractDeclarativeTestBase`
- `io.axoniq.framework.axonserver.connector.configuration.AxonServerConfigurationEnhancer`
- `MessageTypeResolver` / `AnnotationMessageTypeResolver` (AF5 messaging) and `WorkflowConfigurer` — needed only for the `configure()` override.
- `java.util.function.Function` (getDeclaredDefinition return type) and `java.util.function.UnaryOperator` (configure return type).

What to cover (one test per scenario):

- **Happy path** — trigger event + every awaited event arrives in order; assert `COMPLETED` and the step sequence.
- **Each timeout** — for each `WaitStep` with a `timeoutSeconds`, drive the trigger but omit the awaited event; assert `TIMED_OUT` and that the timeout-handling dispatches landed in `workflowStepNames`.
- **Each `fail` terminal** — drive the inputs that route to a `fail` step; assert `FAILED` and that the workflow stopped at that point.
- **Each `cancel` terminal** — drive the inputs that route to a `cancel` step; assert `CANCELLED`.

Notes:

- The test runs the **real** workflow engine against an in-memory event store — no mocks, no `AxonTestFixture` (the fixture targets command-side aggregates, not workflows).
- **The `configure()` override needs BOTH registrations** (see the skeleton):
  - `cr.disableEnhancer(AxonServerConfigurationEnhancer::class.java)` — with the Axon Server + Axoniq Platform starters on the classpath the connector enhancer is ServiceLoader-discovered; without disabling it the test hangs on startup and fails with `ProcessRetriesExhaustedException`. (Only this enhancer — `AxoniqPlatformEventsourcingConfigurerEnhancer` no longer needs disabling.)
  - `cr.registerComponent(MessageTypeResolver::class.java) { AnnotationMessageTypeResolver() }` — the bare `WorkflowConfigurer` uses a **class-based** `MessageTypeResolver`, so the incoming event's type never matches the workflow's `startOnEvent` (`"namespace.name"`) and the workflow silently never triggers. `AnnotationMessageTypeResolver` reads `@Event(namespace, name)` so the types align. Easy to miss because there's no error — the test just times out with an empty history.
- Pick `ofMillis(...)` offsets short for happy paths (sub-second is fine) but for timeout tests make the `WaitStep.timeoutSeconds` the load-bearing wait — the test waits for the real timer to fire.
- Events must carry the correlation property the workflow's `workflowIdProvider` extracts (e.g. `orderId`). If they don't, the step never matches.

## Boundaries

- Don't put validation logic in workflow steps. Validation lives in the dispatched command's handler.
- Do wrap each `wait` with a `timeout` in try/catch and route to the `onTimeout` pointer's step. `@OnTimeout` is for whole-workflow termination, not step-level event-wait timeouts.
- Don't redefine events/commands; reference shared ones from `api/events` and `api/commands`.
- Don't import from Axon Framework 4.
- Don't use `AxonTestFixture` for workflow tests — it targets command handlers. Use `AbstractDeclarativeTestBase` as shown above.
- Don't try to splice DSL changes into an existing workflow class by hand — when the DSL body changes, regenerate the `execute(...)` body from the new DAG.

## When to stop and ask

- The DSL fails to parse, or contains a step kind you don't recognise (`workflow_dsl.md` defines exactly eight: `wait`, `dispatch`, `sleep`, `multi`, `when`, `choice`, `fail`, `cancel`). Workflows never publish events themselves — only command handlers do; if the spec implies the workflow should "emit" something, dispatch a command to a COMMAND component instead.
- A `wait` step's `correlationProperty` isn't a field on the awaited event's payload — that's a Platform-side spec issue; surface via `chat_with_platform` (or capture as a `QUESTION` note).
- The DSL declares a `multi` step with semantics not covered by `ctx.anyMatch` / `ctx.allMatch` (e.g. quorum, "first N of M") — confirm with `chat_with_platform` before writing speculative code.
- The component package already exists with a different `componentId` in `.axoniq`.
- Compile fails after writing files.
