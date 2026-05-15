---
id: command-gateway
title: Command Gateway
description: Migrates a single top-of-chain class dispatching commands via CommandGateway (REST controller, scheduler, runner) to Axon Framework 5.
order: 3
argument-hint: $SOURCE
---

# Command Gateway

> Top-of-chain class (no active `ProcessingContext`) that holds a `CommandGateway` field and dispatches commands via `.send(...)` / `.sendAndWait(...)`. Covers Spring `@RestController`, `@Scheduled`, `CommandLineRunner`, and equivalent input adapters.
>
> **Gateway vs Dispatcher rule**: `CommandGateway` → top-of-chain (this recipe). `CommandDispatcher` → inside a handler (event-processor recipe Step 4). Do NOT swap here.

## Source

- `$SOURCE` (required) — FQN, file path, or simple class name of the top-of-chain class that injects `CommandGateway` and is NOT a message-handling component.

## Scope

- `$SOURCE` class itself.
- Surrounding method return types that need upgrading to `CompletableFuture<R>` when the controller can serve futures async.
- **CommandBus config-reader companions** — during Research: `grep -RlnE 'config\.commandBus\(\)|findComponent\(CommandBus' --include='*.java' <project>/src`. Any class injecting AF4 `Configuration` and calling these is a companion config-reader; add to scope.

Scope grows during FLOW.md Research; never shrinks. External helpers (e.g. `XxxMetaData.with(...)` returning AF4 `MetaData`) are NOT in scope — flag as follow-up.

## Applicable

Surface check on `$SOURCE` before Research. Cheap reads only.

Decision rule (top-down; first match wins):

1. **Saga** — class annotated `@Saga` OR any method annotated `@SagaEventHandler` / `@StartSaga` / `@EndSaga`. → **Rejected** (route to saga recipe).
2. **Handler class** — any method annotated `@EventHandler` / `@CommandHandler` / `@QueryHandler` / `@SagaEventHandler` / `@MessageHandlerInterceptor`. → **Rejected** with NOTES routing to the appropriate handler recipe. Such a class may also use `CommandGateway`; the handler recipe owns the whole class including any dispatch calls.
3. **CommandGateway caller, AF4 shape** — imports `org.axonframework.commandhandling.gateway.CommandGateway`. → **continue** to Research.
4. **CommandGateway caller, partially migrated** — imports `org.axonframework.messaging.commandhandling.gateway.CommandGateway`. → **continue** to Research; the Success Criteria pre-Apply check decides idempotent-Success vs. continue.
5. **CommandBus config reader** — imports `org.axonframework.config.Configuration` AND calls `config.commandBus()` / `config.findComponent(CommandBus.class)`. No `CommandGateway` import. → **continue** as config-reader target (Toolbox Step 5).
6. **None of the above** — no `CommandGateway` import, no config-reader pattern. → **Rejected** with NOTES naming the failed predicate.

## Blocker

**Emission model — all blockers at once.** Scans during Research (FLOW.md S3) before the Plan-Apply loop. Emits one Blocker result if any fire.

### B1 — Direct `CommandCallback` SPI implementation

Class itself **implements** `org.axonframework.commandhandling.CommandCallback<C, R>` — a reusable SPI implementation, NOT an inline lambda passed to `.send(cmd, callback)`. AF4's `CommandCallback` SPI is removed in AF5. The recipe cannot safely infer the error semantics from the class body alone. Detect: `grep -n 'implements.*CommandCallback' <class file>`.

Inline lambdas passed to `send(cmd, callback)` at call sites ARE rewritten by the Toolbox Step 2 table to `.onSuccess(...).onError(...)` — they do NOT trigger this blocker.

Recipe-specific Option alongside the three defaults:
- `redesign-callback` — pause; caller redesigns as a `.onSuccess(...).onError(...)` chain or `CompletableFuture`-based composition, then re-invokes.

### Unmet project prerequisites

- Project does not compile pre-recipe → Blocker `prerequisite-not-compiling`.

## Out of Scope

- Handler-resident dispatch (calls to `CommandGateway` / `CommandDispatcher` inside `@EventHandler` / `@CommandHandler` / `@QueryHandler` bodies) — event-processor recipe Step 4 owns that.
- Mixed class (handler + top-of-chain): run the handler recipe first; this recipe touches non-handler methods on follow-up only after handler migration is complete.
- External helper classes returning AF4 `MetaData` (`org.axonframework.messaging.MetaData`) — flag for follow-up; do not migrate in-scope.
- Adding tests when none exist — surface "no test coverage" as Learning.
- Logging changes, package renames, formatting.

## References

- [messages.adoc](../../docs/paths/messages.adoc) — *apply-condition:* always. Covers `CommandGateway` package move, `@Command`, `@TargetEntityId`, `MessageType`.
- [configuration.adoc](../../docs/paths/configuration.adoc) — *apply-condition:* `configuration=native` OR any config-reader class is in scope. Covers `AxonConfiguration` / `Configuration` split, `getOptionalComponent(...)`, component lookup model.

## Success Criteria

Extends DEFAULT.md baseline. DEFAULT's three baseline criteria stay in force. Recipe adds:

### Recipe-specific structural invariants

For every file in `# Scope`:

1. **No AF4 `CommandGateway` import** — `org.axonframework.commandhandling.gateway.CommandGateway` must not appear.
2. **No `CompletableFuture` variable assigned from bare `send(...)` result** — every AF4 assignment `CompletableFuture<R> f = commandGateway.send(cmd[, metadata])` is rewritten through `CommandResult` (`.resultAs(R.class)`, `.send(cmd, R.class)`, or `.getResultMessage()`).
3. **No stale AF4 `commandhandling.*` imports** — none of: `org.axonframework.commandhandling.CommandExecutionException`, `org.axonframework.commandhandling.gateway.*`.
4. **`CommandCallback` SPI gone** — no `import org.axonframework.commandhandling.CommandCallback` and no anonymous / lambda usage remains in `$SOURCE`.
5. **Config-reader migration (when in scope)** — when a config-reader class is in scope: no `org.axonframework.config.Configuration` import; `CommandBus` import is `org.axonframework.messaging.commandhandling.CommandBus`; no `config.commandBus()` / `findComponent(CommandBus.class)` calls remain.

Aggregation rule: **all match (AND)**.

### Verification

Use `axon4to5-isolatedtest` per DEFAULT.md § Verification. `target-name`: simple class name of `$SOURCE`. `main-sources`: `[$SOURCE file]`. `test-sources`: `[]` (compile-only default) unless an integration test exists.

`extra-deps` baseline: `org.axonframework:axon-messaging`. Add `org.axonframework.extensions.spring:axon-spring-boot-starter` for `configuration=spring`.

## Toolbox

### Step 1 — Import swap

*Apply-condition:* always.

Replace AF4 import:
```
import org.axonframework.commandhandling.gateway.CommandGateway;
```
with AF5 import:
```
import org.axonframework.messaging.commandhandling.gateway.CommandGateway;
```

Field type, constructor parameter name, and variable name unchanged — only the package moves.

**How gateway is obtained (no code change):**
- **Path A (Spring Boot):** AF5 starter auto-creates the bean. Constructor / `@Autowired` unchanged.
- **Path B (native Configurer):** obtain from live `AxonConfiguration`:
  ```java
  var config         = configurer.start();
  var commandGateway = config.getComponent(CommandGateway.class);
  ```

### Step 2 — Rewrite call sites

*Apply-condition:* always.

**Critical:** AF5 `commandGateway.send(cmd)` and `commandGateway.send(cmd, metadata)` return `CommandResult`, NOT `CompletableFuture`. Any AF4 line assigning to `CompletableFuture<R>` compiles in AF4 but FAILS in AF5.

| AF4 call | AF5 replacement | Returns |
|---|---|---|
| `commandGateway.send(cmd)` — result discarded | unchanged | `CommandResult` (discarded) |
| `commandGateway.send(cmd)` → `CompletableFuture<Void>` | `commandGateway.send(cmd, Void.class)` | `CompletableFuture<Void>` |
| `commandGateway.send(cmd)` → `CompletableFuture<R>` | `commandGateway.send(cmd, R.class)` | `CompletableFuture<R>` |
| `commandGateway.send(cmd, metadata)` → `CompletableFuture<Void>` | `commandGateway.send(cmd, metadata).resultAs(Void.class)` | `CompletableFuture<Void>` |
| `commandGateway.send(cmd, metadata)` → `CompletableFuture<R>` | `commandGateway.send(cmd, metadata).resultAs(R.class)` | `CompletableFuture<R>` |
| `commandGateway.send(cmd, callback)` inline lambda | `commandGateway.send(cmd).onSuccess(...).onError(...)` | `CommandResult` |
| `commandGateway.sendAndWait(cmd)` in `@RestController` | **Preferred:** upgrade return to `CompletableFuture<Void>` + `send(cmd, Void.class)`. **Fallback:** keep `sendAndWait` — import-only | `CompletableFuture<Void>` / `Object` |
| `commandGateway.sendAndWait(cmd, R.class)` in `@RestController` | **Preferred:** upgrade return to `CompletableFuture<R>` + `send(cmd, R.class)`. **Fallback:** keep — import-only | `CompletableFuture<R>` / `R` |
| `commandGateway.sendAndWait(cmd)` in runner / `@Scheduled void` / `main` | unchanged — import-only | `Object` |
| `commandGateway.sendAndWait(cmd, R.class)` in runner / `@Scheduled void` / `main` | unchanged — import-only | `R` |
| `commandGateway.sendAndWait(cmd, timeout, unit)` (no AF5 overload) | **Preferred:** `send(cmd, R.class).orTimeout(timeout, unit)`. **Fallback:** `…orTimeout(t, u).join()` (never bare `.join()` without timeout) | `CompletableFuture<R>` / `R` |

Notes:
- `commandGateway.send(cmd, R.class)` is shorthand for `commandGateway.send(cmd).resultAs(R.class)`. Prefer when no metadata.
- `Void.class` is valid for `.resultAs(...)`.
- Use `.getResultMessage().thenApply(m -> ...)` only when the `Message` object (metadata, identifier) is needed downstream.

### Step 3 — Prefer non-blocking; adapt return type

*Apply-condition:* `$SOURCE` is a Spring `@RestController` (or equivalent future-friendly caller) AND has `sendAndWait(...)` calls.

Spring serves `CompletableFuture<R>` async out-of-the-box — same HTTP response, no thread blocking. **Prefer** upgrading:
- Method return type `R` → `CompletableFuture<R>`.
- Body `sendAndWait(cmd, R.class)` → `send(cmd, R.class)`.
- Add `import java.util.concurrent.CompletableFuture;` when introducing it.

Keep `sendAndWait(...)` only when caller genuinely cannot accept a future: `CommandLineRunner`, `ApplicationRunner`, `@Scheduled void`, `main(...)`, integration tests asserting on the return value.

Common shapes:

```java
// Spring MVC — send with metadata, Void result
@PutMapping("/{id}")
CompletableFuture<Void> update(...) {
    return commandGateway.send(cmd, metadata).resultAs(Void.class);
}

// Spring MVC — send, typed result
@PostMapping
CompletableFuture<ResponseEntity<R>> create(...) {
    return commandGateway.send(cmd, R.class).thenApply(ResponseEntity::ok);
}

// Reactive bridge
Mono<R> handle(...) {
    return Mono.fromFuture(commandGateway.send(cmd, R.class));
}
```

Kotlin: replace `R.class` with `R::class.java`. Do NOT introduce coroutines, `suspend`, or `await()` — that is a refactor.

### Step 4 — Verify remaining stale imports

*Apply-condition:* always.

- `CommandExecutionException` in a try/catch → update: `org.axonframework.commandhandling.CommandExecutionException` → `org.axonframework.messaging.commandhandling.CommandExecutionException`.
- Any remaining `org.axonframework.commandhandling.*` imports → delete.
- Introduced `CompletableFuture`? Confirm `import java.util.concurrent.CompletableFuture;` is present.

### Step 5 — CommandBus config-reader migration

*Apply-condition:* `$SOURCE` matched Applicable predicate 5 OR Research found a companion config-reader in scope.

**Path A (Spring Boot):** `AxonConfiguration` is auto-created as a Spring bean; constructor injection unchanged.
**Path B (native Configurer):** pass the live `AxonConfiguration` returned by `configurer.build().start()` as a constructor argument.

1. **Switch injected type** — `Configuration` (AF4: `org.axonframework.config.Configuration`) → `Configuration` (AF5: `org.axonframework.common.configuration.Configuration`). If class also touches root lifecycle → use `AxonConfiguration` (`org.axonframework.common.configuration.AxonConfiguration`).
2. **Rewrite lookups**:

| AF4 call | AF5 replacement |
|---|---|
| `config.commandBus()` | `axonConfig.getOptionalComponent(CommandBus.class).orElseThrow()` |
| `config.findComponent(CommandBus.class)` | `axonConfig.getOptionalComponent(CommandBus.class)` |

Use `.orElseThrow(...)` when AF4 assumed presence; propagate `Optional` otherwise.

3. **Sweep imports** — remove `org.axonframework.config.Configuration`, `org.axonframework.commandhandling.CommandBus`. Add `org.axonframework.common.configuration.Configuration` (or `AxonConfiguration`), `org.axonframework.messaging.commandhandling.CommandBus`.

## Use cases

- [01-rest-controller-send-with-metadata.md](use-cases/01-rest-controller-send-with-metadata.md) — *apply-condition:* `$SOURCE` is a Spring `@RestController` AND uses `commandGateway.send(cmd, metadata)` returning `CompletableFuture<Void>` or `CompletableFuture<R>`.
- [02-rest-controller-sendandwait-to-async.md](use-cases/02-rest-controller-sendandwait-to-async.md) — *apply-condition:* `$SOURCE` is a Spring `@RestController` AND uses `commandGateway.sendAndWait(...)` (blocking call upgradeable to async).
- [03-scheduler-runner-sendandwait.md](use-cases/03-scheduler-runner-sendandwait.md) — *apply-condition:* `$SOURCE` is a `@Scheduled` method or `CommandLineRunner` / `ApplicationRunner` using `sendAndWait` (caller cannot accept a future — import-only change).
- [04-command-callback-inline-rewrite.md](use-cases/04-command-callback-inline-rewrite.md) — *apply-condition:* `$SOURCE` passes an inline lambda or anonymous class as `CommandCallback` to `commandGateway.send(cmd, callback)`.
- [05-rejected-handler-class.md](use-cases/05-rejected-handler-class.md) — *apply-condition:* `$SOURCE` has any method annotated `@EventHandler` / `@CommandHandler` / `@QueryHandler` (predicate 2 fires).

## Gotchas

- **`CommandResult` is NOT `CompletableFuture`** — most common compile error. AF4's `send(cmd, metadata)` returned `CompletableFuture<Void>` directly; AF5's returns `CommandResult`. Any AF4 code assigning to `CompletableFuture<Void> f = ...` or returning from a `CompletableFuture<Void>` method fails in AF5. Always append `.resultAs(Void.class)` or use `.send(cmd, Void.class)`.
- **`send(cmd, R.class)` convenience shorthand** — default method for `send(cmd).resultAs(R.class)`. Prefer when no metadata.
- **`sendAndWait` still exists in AF5** — import-only for scheduler / runner callers. Do NOT remove when the caller cannot accept a future.
- **`sendAndWait(cmd, timeout, unit)` overload is gone** — rewrite to `send(cmd, R.class).orTimeout(timeout, unit)` (future) or `.orTimeout(...).join()` (blocking — never bare `.join()` without timeout).
- **`CommandGateway` stays `CommandGateway`** — never swap to `CommandDispatcher` in this recipe. `CommandDispatcher` is for inside handlers only.
- **`CommandCallback` SPI removed** — inline lambdas at call sites can become `.onSuccess(...).onError(...)`. Classes implementing `CommandCallback` directly are Blocker B1.
- **Metadata helper may not compile** — if `$SOURCE` calls `XxxMetaData.with(...)` returning AF4 `org.axonframework.messaging.MetaData`, the file will still fail to compile after this recipe (the helper needs its own migration). Flag in NOTES; do not attempt to migrate the helper from inside this recipe.
- **`CommandExecutionException` FQN moved** — `org.axonframework.commandhandling.CommandExecutionException` → `org.axonframework.messaging.commandhandling.CommandExecutionException`. Easy to miss inside catch blocks.
- **Config-reader: `Configuration` vs `AxonConfiguration`** — use read-only `Configuration` when the class never touches root lifecycle (start/stop); use `AxonConfiguration` otherwise. Wrong choice compiles but fails at runtime when lifecycle methods are absent on the interface.

## Result

Inherits DEFAULT.md baseline.

### Success

Say **"return SUCCESS"**, then **MUST emit** the result block (schema: FLOW.md § Result). `Recipe:` field is `axon4to5-command-gateway`. Include as Learning: any flagged follow-ups (stale `XxxMetaData.with(...)` helper, external `CommandCallback` implementation not in scope).

### Blocker

Say **"return BLOCKER"**, then **MUST emit** the result block (schema: FLOW.md § Result). `Recipe:` field is `axon4to5-command-gateway`. NOTES name each detected blocker. Options block: three DEFAULT.md baselines + for B1: `redesign-callback` option.

Example (B1):

```
return BLOCKER

> **Result:** 🚧 Blocker
> **Source:** `com.example.OrderDispatcher`
> **Recipe:** axon4to5-command-gateway
>
> **Notes:** 1 blocker detected. `OrderDispatcher.java:8` implements `CommandCallback<CreateOrderCommand, String>` directly — AF4 `CommandCallback` SPI removed in AF5. Error semantics unclear from the implementation body alone.
>
> **Options:**
>
> _For B1 (CommandCallback SPI):_
> - [ ] **redesign-callback** — pause; redesign as `.onSuccess(...).onError(...)` chain or `CompletableFuture`-based composition, re-invoke.
> - [ ] **skip** — keep `OrderDispatcher` in current partial state; queue moves on.
> - [ ] **revert** — undo recipe edits; restore pre-recipe state.
> - [ ] **solve-manually** — pause; caller handles redesign, then re-invokes.
```

### Rejected

Say **"return REJECTED"**, then **MUST emit** the result block (schema: FLOW.md § Result). `Recipe:` field is `axon4to5-command-gateway`. NOTES name the failed predicate and route to the appropriate sister recipe.

Example:

```
return REJECTED

> **Result:** ⏭️ Rejected
> **Source:** `com.example.automation.WhenOrderPlacedProcessor`
> **Recipe:** axon4to5-command-gateway
>
> **Notes:** Applicable predicate 2 failed — class has `@EventHandler` methods. This is an event-handling component, not a top-of-chain caller. Route to the event-processor recipe; it owns in-handler command dispatch (Step 4).
```

### Failure

Say **"return FAILURE"**, then **MUST emit** the result block (schema: FLOW.md § Result). NOTES: failing Success Criteria + last error verbatim. LEARNINGS nearly always present.
