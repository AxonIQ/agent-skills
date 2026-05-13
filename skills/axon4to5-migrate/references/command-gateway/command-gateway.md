# Recipe: command-gateway (top-of-chain caller)

Atomic migration of ONE class dispatching commands via `CommandGateway` from outside any message handler — typically Spring `@RestController`, `@Scheduled`, `CommandLineRunner`, or input adapter.

> If the class instead injects AF4 `Configuration` and reads `commandBus()`, use [configuration-reads.md](configuration-reads.md).

**Gateway vs Dispatcher rule** (from `CommandDispatcher` Javadoc): `CommandGateway` for top-of-chain entry points (no active `ProcessingContext`); `CommandDispatcher` for inside another handler. Handler-resident dispatch belongs to the relevant handler recipe.

## Inputs

- `target` — FQ class (required)
- `target_test` — FQ test class (optional)
- `wiring` — `spring-boot` | `framework-config` (pinned)

## Preflight

1. Already imports AF5 `org.axonframework.messaging.commandhandling.gateway.CommandGateway`?
2. Zero compile problems AND no `.send(cmd, metadata)` line typed as `CompletableFuture`?
3. Both clean → `AskUserQuestion`: Skip / Deep verify. Proceed only on Deep verify or failure.

## In scope

ONE class that imports AF4 `CommandGateway`, holds it as class-level dep, calls `.send(...)` / `.sendAndWait(...)`, AND is NOT a message-handling component (no `@EventHandler` / `@CommandHandler` / `@QueryHandler` / `@MessageHandlerInterceptor` / `@SagaEventHandler`).

## FQN cheat sheet

| Element | AF4 | AF5 |
|---|---|---|
| `CommandGateway` | `org.axonframework.commandhandling.gateway.CommandGateway` | `org.axonframework.messaging.commandhandling.gateway.CommandGateway` |
| `CommandResult` (new) | n/a | `org.axonframework.messaging.commandhandling.gateway.CommandResult` |
| `Metadata` | `org.axonframework.messaging.MetaData` | `org.axonframework.messaging.core.Metadata` |
| `CommandExecutionException` | `org.axonframework.commandhandling.CommandExecutionException` | `org.axonframework.messaging.commandhandling.CommandExecutionException` |

## Procedure

### Step 1 — Locate

User-named target, else first file matching `CommandGateway` AF4 import AND NOT matching `@EventHandler|@CommandHandler|@QueryHandler|@MessageHandlerInterceptor|@SagaEventHandler`.

### Step 2 — Update `CommandGateway` import

Single-line change — AF4 → AF5 FQN. Constructor / field type / variable name unchanged. Do NOT replace with `CommandDispatcher` (that's reserved for in-handler).

How the gateway is obtained:
- **Path A (Spring Boot):** auto-created bean by AF5 starter. Constructor injection / `@Autowired` unchanged.
- **Path B (framework Configurer):** from the live `AxonConfiguration`:
  ```java
  var config         = configurer.start();
  var commandGateway = config.getComponent(CommandGateway.class);
  ```

### Step 3 — Rewrite call sites

**Critical:** AF5 `commandGateway.send(cmd)` and `commandGateway.send(cmd, metadata)` return `CommandResult`, NOT `CompletableFuture`. Any AF4 line `CompletableFuture<R> f = commandGateway.send(cmd[, metadata])` compiles in AF4 but FAILS in AF5.

| AF4 call | AF5 replacement | Returns |
|---|---|---|
| `commandGateway.send(cmd)` discarded (statement) | unchanged (`CommandResult` discarded) | `CommandResult` |
| `commandGateway.send(cmd)` assigned to `CompletableFuture<Void>` | `commandGateway.send(cmd, Void.class)` (or `.send(cmd).getResultMessage()` for `.allOf`-style fan-in) | `CompletableFuture<Void>` |
| `commandGateway.send(cmd)` assigned to typed `CompletableFuture<R>` | `commandGateway.send(cmd, R.class)` | `CompletableFuture<R>` |
| `commandGateway.send(cmd, metadata)` AF4 → `CompletableFuture<Void>` | `commandGateway.send(cmd, metadata).resultAs(Void.class)` | `CompletableFuture<Void>` |
| `commandGateway.send(cmd, metadata)` AF4 → typed `CompletableFuture<R>` | `commandGateway.send(cmd, metadata).resultAs(R.class)` | `CompletableFuture<R>` |
| `commandGateway.send(cmd, callback)` (AF4 `CommandCallback` — **removed**) | `commandGateway.send(cmd).onSuccess(...).onError(...)` | `CommandResult` |
| `R = commandGateway.sendAndWait(cmd, R.class)` in Spring `@RestController` | **Preferred:** change method return type to `CompletableFuture<R>` + use `send(cmd, R.class)`. **Fallback:** keep `sendAndWait(...)` (import-only) | `CompletableFuture<R>` / `R` |
| `commandGateway.sendAndWait(cmd[, R.class])` in runner / `@Scheduled void` / `main` / test | unchanged — import only | `Object` / `R` |
| `commandGateway.sendAndWait(cmd, timeout, unit)` (no AF5 overload) | **Preferred:** `send(cmd, R.class).orTimeout(timeout, unit)` (future). **Fallback:** `…orTimeout(t, u).join()` to preserve blocking (never `.join()` / `.get()` without timeout) | `CompletableFuture<R>` / `R` |

Notes:
- `commandGateway.send(cmd, R.class)` is shorthand for `.send(cmd).resultAs(R.class)`.
- `Void.class` is valid for `.resultAs(...)` and `.send(cmd, Void.class)`.
- Use `.getResultMessage().thenApply(m -> ...)` only when the `Message` (metadata, identifier) is needed.

### Step 4 — Prefer non-blocking; adapt return type

If changing the surrounding method's return to `CompletableFuture<R>` is behavior-preserving (Spring serves futures async out-of-the-box — same HTTP response, no thread blocking), **do it**. Keep `sendAndWait(...)` only when caller genuinely can't accept a future (`CommandLineRunner`, `@Scheduled void`, `main`, integration tests asserting on the return).

Three common shapes:

**Spring MVC controller:**
```java
@PutMapping("/things/{id}")
CompletableFuture<Void> putThings(...) {
    return commandGateway.send(cmd, MyMetadata.with(...)).resultAs(Void.class);
}

@PostMapping("/things")
CompletableFuture<ResponseEntity<R>> createThing(...) {
    return commandGateway.send(cmd, R.class).thenApply(ResponseEntity::ok);
}
```

Add `import java.util.concurrent.CompletableFuture;` when introducing it.

**Scheduler / runner returning `void`:** keep `sendAndWait(...)` — import-only change.

**Reactive (Mono/Flux):** bridge via `Mono.fromFuture(commandGateway.send(cmd, R.class))`.

**Kotlin:** mechanical translation — `R.class` → `R::class.java`. Do NOT introduce coroutines / `suspend` / `await()` — that's a refactor, not a migration.

### Step 5 — Verify nothing else

- Stale AF4 `org.axonframework.commandhandling.*` imports — remove.
- `CommandExecutionException` catch — update FQN if present.
- AF4 `CommandCallback` impls — flag for user; don't silently change error semantics. End state: **no `CommandCallback` SPI refs remain** (either rewritten to `.onSuccess(...).onError(...)` or flagged out of scope).
- New `CompletableFuture` introduced? Confirm `import java.util.concurrent.CompletableFuture;`.

Do not introduce abstractions or refactors not required by the API change.

## End condition

1. Zero compile errors in the class.
2. Surrounding method's return type flows the dispatch result correctly (no leftover `void` where a future is expected; no leftover blocking where async was intended).
3. Compile-only via `axon4to5-isolatedtest`:
   ```
   target-name: <ClassSimpleName>
   main-sources: [<Class>.java]
   test-sources: []                       # or integration test if exists + add axon-test dep
   extra-deps: [axon-messaging]
   ```

## Output

```yaml
result: success | skipped | rejected | needs-decision | blocked | failed
target: <FQ class>
reason: <one short line>
decisions:
  path: A (Spring Boot) | B (framework Configurer)
  return-shape: mvc | scheduler | reactive
caller-expects: { commit: <bool>, next: <…> }
notes: <…>
```

## Out of scope

- Handler-resident dispatch → relevant handler recipe.
- Mixed class (some methods are handlers, some top-of-chain) — run handler recipe first; this recipe touches non-handler methods on follow-up.
- Custom `CommandCallback` impls — flag, don't silently rewrite error semantics.
- Helper class returning AF4 `MetaData` (`XxxMetaData.with(...)`) — shared elsewhere; flag follow-up.
