# Recipe: `CommandGateway` caller (top-of-chain, non-handler)

Atomic migration of ONE class that dispatches commands via `CommandGateway` from outside any message handler — typically Spring `@RestController`, `@Scheduled` runner, `CommandLineRunner`, or input adapter / service that is the **first cause** of a command and therefore has **no active `ProcessingContext`**.

> **Configuration-reader variant.** If the candidate class instead injects AF4 `Configuration` and reads `commandBus()` to dispatch low-level command messages, follow [configuration-reads.md](configuration-reads.md) instead of this main recipe.

## Canonical reference

- [../../docs/paths/messages.adoc](../../docs/paths/messages.adoc) — `@Command`, `@TargetEntityId`, `@RoutingKey` → `routingKey` consolidation, `MessageType`.
- [../../docs/paths/index.adoc](../../docs/paths/index.adoc) §"Import and package changes" — `CommandGateway` / `CommandDispatcher` package moves.

Recipe holds the AF4 → AF5 call-shape rewrites and the three return-shape paths (MVC / scheduler / reactive).

## Goal

The class compiles on AF5:
- `CommandGateway` import switched to AF5 location.
- `sendAndWait(...)` calls converted to AF5 equivalents (still available).
- AF4 `send(cmd, metadata)` (returned `CompletableFuture<R>`) rewritten through AF5's `CommandResult` shape.
- Surrounding method's return type adapted (e.g. Spring controller `CompletableFuture<R>`) so framework consumes the future.

> **Hard rule — gateway vs dispatcher.** From `CommandDispatcher` Javadoc: gateway for top-of-chain entry points (REST controllers, schedulers, CLI), dispatcher inside another handler. This recipe handles only the gateway side. Handler-resident dispatch goes to the event-processor recipe (or future command/query/saga handler recipes).

## Inputs

- target: FQ class name of the top-of-chain dispatcher (controller / scheduler / runner injecting `CommandGateway`) (required)
- target_test: FQ test class name (optional)
- wiring: "spring-boot" | "framework-config" (required, supplied by orchestrator from progress.md Pinned-decisions)

## End condition

1. Zero compile errors in the class itself.
2. The surrounding method's return type flows the dispatch result correctly (no leftover `void` where the framework expected a future, no leftover blocking where async was intended).
3. Verify decided by user — often integration test or manual smoke-check (the request thread shouldn't block; controller should return `CompletableFuture<R>` async to Spring).

## Output

- target: <FQ class>
- decisions:
    - path: <A (Spring Boot) | B (framework Configurer)>     # taken from inputs.wiring
    - return-shape: <mvc | scheduler | reactive>
- needs-user-decision: <true | false>
- needs-user-decision-reason: <text> (only when true)
- notes: optional

## Preflight

1. Read the file. Already imports `org.axonframework.messaging.commandhandling.gateway.CommandGateway`?
2. Check compilation problems on the file. Zero AND no `commandGateway.send(cmd, metadata)` line that returns `CommandResult` instead of `CompletableFuture`?
3. If both clean → STOP. `AskUserQuestion`: Skip / Deep verify.
4. Only proceed if user picks **Deep verify** or step 1/2 reported failures.

## In scope

ONE class that:
- Imports `org.axonframework.commandhandling.gateway.CommandGateway` (AF4 location), AND
- Holds it as class-level dependency (typically constructor-injected, sometimes field-injected), AND
- Calls `commandGateway.send(...)` and/or `commandGateway.sendAndWait(...)`, AND
- Is **NOT** a message-handling component — no methods annotated `@EventHandler`, `@CommandHandler`, `@QueryHandler`, `@MessageHandlerInterceptor`, `@SagaEventHandler`, or any `@MessageHandler` meta-annotation.

## Out of scope

- Handler-resident dispatch (in-handler calls to gateway/dispatcher) — see event-processor recipe.
- Mixed class (some methods are handlers, some top-of-chain dispatchers): run handler recipe FIRST; this recipe touches non-handler methods on follow-up.
- Custom callback class implementing AF4's `CommandCallback` SPI directly — that SPI was removed; flag for user.
- Helper class (e.g. `XxxMetaData.with(...)`) returning AF4 `MetaData` — shared across many call sites; lives in another package; flag for user as a follow-up.

## FQN cheat sheet

| Element | AF4 | AF5 |
|---|---|---|
| `CommandGateway` (interface) | `org.axonframework.commandhandling.gateway.CommandGateway` | `org.axonframework.messaging.commandhandling.gateway.CommandGateway` |
| `CommandResult` (new in AF5) | n/a | `org.axonframework.messaging.commandhandling.gateway.CommandResult` |
| `Metadata` | `org.axonframework.messaging.MetaData` | `org.axonframework.messaging.core.Metadata` |
| `CommandExecutionException` | `org.axonframework.commandhandling.CommandExecutionException` | `org.axonframework.messaging.commandhandling.CommandExecutionException` |

## Procedure

### 1. Locate candidate

If user named target, use it. Otherwise:

```bash
grep -rln --include='*.java' --include='*.kt' \
  'org.axonframework.commandhandling.gateway.CommandGateway' \
  <target>/src
```

From that list, exclude files with handler annotations:

```bash
grep -L \
  -e '@EventHandler' \
  -e '@CommandHandler' \
  -e '@QueryHandler' \
  -e '@MessageHandlerInterceptor' \
  -e '@SagaEventHandler' \
  <files-from-previous-step>
```

Pick first remaining (lexical order).

### 2. Update `CommandGateway` import

Single-line change. Switch import to AF5 FQN. Constructor / field type / variable name stay the same — `CommandGateway` is still the right interface for top-of-chain callers in AF5. Do **NOT** replace with `CommandDispatcher` (that's reserved for in-handler use).

**How the gateway is obtained (path-conditional, no code change here):**
- **Path A (Spring Boot):** `CommandGateway` is auto-created as a Spring bean by the AF5 starter. Constructor injection / `@Autowired` field continue to work without changes.
- **Path B (framework Configurer):** the live `AxonConfiguration` returned by `EventSourcingConfigurer.create().…start()` is the source. The class typically receives the gateway via constructor from the bootstrap that built the configuration:
  ```java
  var config         = configurer.start();
  var commandGateway = config.getComponent(CommandGateway.class);
  var controller     = new MyController(commandGateway);
  ```
  Steps 3–5 are identical in both paths.

### 3. Rewrite call sites — AF4 → AF5 shape table

> **Critical**: AF5's no-arg `commandGateway.send(cmd)` returns `CommandResult`, **NOT** `CompletableFuture`. AF5's `commandGateway.send(cmd, metadata)` also returns `CommandResult`. Any AF4 line `CompletableFuture<R> f = commandGateway.send(cmd[, metadata])` compiles in AF4 but **NOT** in AF5.

| AF4 call | AF5 replacement | Returns |
|---|---|---|
| `commandGateway.send(cmd)` — result discarded (statement, no assignment) | `commandGateway.send(cmd)` — unchanged (returned `CommandResult` discarded) | `CommandResult` |
| `commandGateway.send(cmd)` assigned to `CompletableFuture<Void>` | `commandGateway.send(cmd, Void.class)` (preferred). For `.allOf`-style fan-in over raw `Message` futures: `.send(cmd).getResultMessage()` | `CompletableFuture<Void>` / `CompletableFuture<? extends Message>` |
| `commandGateway.send(cmd)` assigned to typed `CompletableFuture<R>` | `commandGateway.send(cmd, R.class)` | `CompletableFuture<R>` |
| `commandGateway.send(cmd, metadata)` returning `CompletableFuture<Void>` (AF4) | `commandGateway.send(cmd, metadata).resultAs(Void.class)` | `CompletableFuture<Void>` |
| `commandGateway.send(cmd, metadata)` returning typed `CompletableFuture<R>` (AF4) | `commandGateway.send(cmd, metadata).resultAs(R.class)` | `CompletableFuture<R>` |
| `commandGateway.send(cmd, callback)` (AF4 `CommandCallback` SPI — removed) | `commandGateway.send(cmd).onSuccess(...).onError(...)` — keep behavior identical, do NOT silently change error semantics | `CommandResult` (chained) |
| `R = commandGateway.sendAndWait(cmd, R.class)` in a Spring `@RestController` (or other future-friendly caller) | **Preferred:** change method return type from `R` to `CompletableFuture<R>` and use `commandGateway.send(cmd, R.class)`. **Fallback:** keep `sendAndWait(...)` — import-only change | `CompletableFuture<R>` (preferred) / `R` (fallback) |
| `commandGateway.sendAndWait(cmd)` in runner / `@Scheduled void` / `main` / test | unchanged — import only (caller cannot accept a future) | `Object` |
| `commandGateway.sendAndWait(cmd, R.class)` in runner / `@Scheduled void` / `main` / test | unchanged — import only (caller cannot accept a future) | `R` |
| `commandGateway.sendAndWait(cmd, timeout, unit)` (AF4 — no AF5 overload) | **Preferred:** `commandGateway.send(cmd, R.class).orTimeout(timeout, unit)` returning `CompletableFuture<R>` if the caller accepts a future. **Fallback:** `commandGateway.send(cmd, R.class).orTimeout(timeout, unit).join()` to preserve blocking (AF5 rule: never `.join()` / `.get()` without a timeout) | `CompletableFuture<R>` (preferred) / `R` (fallback) |

Notes:
- `CommandResult` is **NOT** a `CompletableFuture`. Anywhere AF4 code assigned `commandGateway.send(...)` to a `CompletableFuture` variable or returned it from a `CompletableFuture<R>` method, use `.resultAs(R.class)` (or the convenience `.send(cmd, R.class)` when no metadata) to obtain a real future. Use `.getResultMessage().thenApply(m -> ...)` only when the `Message` itself (metadata, identifier) is needed.
- `commandGateway.send(cmd, R.class)` (default method) is shorthand for `commandGateway.send(cmd).resultAs(R.class)`. Prefer it when no metadata is involved.
- `Void.class` is a valid argument to `.resultAs(...)` and to `.send(cmd, Void.class)`.

#### Prefer non-blocking when possible

Spring serves `CompletableFuture<R>` async out of the box — same HTTP response, no request-thread blocking. So when the surrounding method *can* return a `CompletableFuture`, **prefer** rewriting:

- `R sendAndWait(cmd, R.class)` returning `R` from a controller → method returns `CompletableFuture<R>`, body returns `commandGateway.send(cmd, R.class)`.
- Same applies to `ResponseEntity<R>` / `Mono<R>` / `Flux<R>` (project-specific bridges via `Mono.fromFuture(...)`).
- Use `.thenApply(...)` for post-dispatch shaping (e.g. wrapping the result in `ResponseEntity.ok(...)`).
- Add the `java.util.concurrent.CompletableFuture` import when introducing it.

Keep `sendAndWait(...)` only when the caller genuinely cannot accept a future: `CommandLineRunner`, `ApplicationRunner`, `@Scheduled void`, `main(...)`, integration tests asserting on the return value.

**Rule:** if changing the *return type* to `CompletableFuture<R>` is behavior-preserving (Spring controller, reactive method, or any caller already composing futures), do it. Otherwise only the import changes.

### 4. Adapt the surrounding method's return type

Three common shapes (driven by the "Prefer non-blocking" rule above):

**Spring MVC controller** — Spring serves `CompletableFuture<R>` async out of the box. **Prefer**: return `CompletableFuture<R>` from the handler method and pipe the dispatch result through `.resultAs(R.class)` or `.send(cmd, R.class)`. Use `.thenApply(...)` for response shaping:

```java
@PutMapping("/things/{id}")
CompletableFuture<Void> putThings(...) {
    var command = ...;
    return commandGateway.send(command, MyMetadata.with(...))
                         .resultAs(Void.class);
}
```

```java
@PostMapping("/things")
CompletableFuture<ResponseEntity<R>> createThing(...) {
    return commandGateway.send(command, R.class)
                         .thenApply(ResponseEntity::ok);
}
```

When introducing `CompletableFuture` here, add the `java.util.concurrent.CompletableFuture` import.

**Scheduler / runner returning `void`** — AF5's `sendAndWait(...)` still exists. Keep it when the surrounding method must run to completion before returning (cron jobs, startup runners, integration tests asserting on the return). Import-only change.

**Reactive return type (Mono / Flux)** — Bridge the AF5 `CompletableFuture` from `.resultAs(R.class)` (or `.send(cmd, R.class)`) into the reactive type the method already returns (`Mono.fromFuture(...)`). Project-specific.

#### Kotlin

Translate Java rewrite shapes mechanically: replace `R.class` with `R::class.java`. Do **NOT** introduce coroutines, `await()`, `suspend` keywords, or other Kotlin idioms — that is a refactor, not a migration. See [examples/06-payment-controller-kotlin.md](examples/06-payment-controller-kotlin.md).

### 5. Verify nothing else

- Stale imports — remove remaining `org.axonframework.commandhandling.*` AF4 imports no longer referenced.
- Try/catch on `CommandExecutionException` — FQN moved. Update if present.
- AF4 `CommandCallback` implementations — flag for user, don't silently change error semantics. End state: **no `CommandCallback` SPI references remain** in the migrated class (either rewritten to `.onSuccess(...).onError(...)` chains or flagged out of scope).
- New `CompletableFuture` introduced for an async rewrite? Confirm the `java.util.concurrent.CompletableFuture` import is present.

> Don't introduce abstractions or refactors not required by the AF5 API change.

## Verify (against End condition)

Compile-only is sufficient since this recipe touches a single class. Invoke the external `axon4to5-isolatedtest` skill (see [../verification.md](../verification.md)):

```
Skill: axon4to5-isolatedtest
Inputs:
  target-name: <ClassSimpleName>
  build-file: <target>/pom.xml | <target>/build.gradle(.kts)
  main-sources:
    - src/main/java/<…>/<Class>.java
  test-sources: []                              # compile-only run
  extra-deps:
    - org.axonframework:axon-messaging:${axon5.version}
  cleanup: false
```

If an integration test exists for this controller/runner, prefer running it — pass it via `test-sources` and add `axon-test` to `extra-deps`.

## Examples

Pick the example that matches the candidate file's shape:

| Pattern | Example |
|---|---|
| `.send(cmd, metadata)` returning `CompletableFuture<Void>` (Spring `@RestController`) | [examples/01-heroes-builddwelling-restcontroller.md](examples/01-heroes-builddwelling-restcontroller.md) |
| `.send(cmd)` whose value flows into `CompletableFuture<Void>` or `CompletableFuture<R>` | [examples/02-payment-controller-send-future.md](examples/02-payment-controller-send-future.md) |
| Controller chains multiple sends (`.allOf`, `.thenCompose`, reactive `Mono.fromFuture`) | [examples/03-rental-controller-orchestration.md](examples/03-rental-controller-orchestration.md) |
| AF4 `CommandCallback` SPI (anonymous or inline) | [examples/04-rental-dispatcher-callback.md](examples/04-rental-dispatcher-callback.md) |
| `sendAndWait(...)` (controller / runner / scheduler / timeout overload) | [examples/05-change-course-capacity-sendandwait.md](examples/05-change-course-capacity-sendandwait.md) |
| Kotlin syntax (`T::class.java`, primary constructors, expression bodies) | [examples/06-payment-controller-kotlin.md](examples/06-payment-controller-kotlin.md) |
