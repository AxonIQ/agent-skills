---
id: "interceptors"
title: "Interceptors"
description: Migrates a single AF4 MessageDispatchInterceptor or MessageHandlerInterceptor to AF5 async API — method rename, UnitOfWork removal, ProcessingContext injection, and registration-site update.
order: 6
argument-hint: $SOURCE
---

# Interceptors

> Single AF4 interceptor class → AF5 async-first interceptor. Same contract preserved. Dispatch interceptors: `handle(List<...>)` → `interceptOnDispatch(M, @Nullable ProcessingContext, Chain)`. Handler interceptors: `handle(UnitOfWork, InterceptorChain)` → `interceptOnHandle(M, ProcessingContext, Chain)`. `UnitOfWork` gone — lifecycle hooks move to `ProcessingContext` callbacks. Path A (Spring Boot): `@Component` stays, `InterceptorAutoConfiguration` auto-discovers. Path B (native): rewrite registration call receiver from `Configurer` to `MessagingConfigurer`.

## Source

- `$SOURCE` (required) — FQN, file path, or simple class name of an AF4 interceptor class. Implements `MessageDispatchInterceptor<M>`, `MessageHandlerInterceptor<M>`, or both. May be partially migrated (imports updated but method signatures still AF4).

## Scope

- `$SOURCE` class.
- Path B only: the single registration call(s) for `$SOURCE` in the project's Configurer file (grep `register(Command|Event|Query)?(Handler|Dispatch)Interceptor`). Only `$SOURCE`'s site — not every interceptor in the file.

Scope never shrinks. Sibling interceptors, aggregates, event processors, and unrelated config are NEVER in scope.

## Blocker

### B1 — `@MessageHandlerInterceptor` annotation on method

`@MessageHandlerInterceptor` used as a **method annotation** (inline interceptor method inside a handler class). Not functional in AF5 < 5.2.0 — no migration path within this recipe. Detect: `grep -nE '@MessageHandlerInterceptor' <file>`. Distinguish: a class *implementing* `MessageHandlerInterceptor<M>` (interface) is fully migratable — only the *annotation* form triggers B1.

### Unmet project prerequisites

- Project does not compile pre-recipe — `axon4to5-isolatedtest` Skill cannot establish a baseline. Surface as Blocker `prerequisite-not-compiling`.

## Out of Scope

- Sibling interceptors.
- Handler classes (`@CommandHandler`, `@EventHandler`, `@QueryHandler`).
- Application-wide Configurer bootstrap beyond the single registration call for `$SOURCE`.
- DLQ, deadline, scheduler wiring.
- Logging changes, package renames, formatting.

## Applicable

Surface check before Research. Cheap reads only.

Decision rule (top-down; first match wins):

1. **`@MessageHandlerInterceptor` annotation on any method** (not interface impl) → continue to Research to emit Blocker B1.
2. **`implements MessageDispatchInterceptor<…>`** in class declaration → continue; `variant=dispatch`.
3. **`implements MessageHandlerInterceptor<…>`** in class declaration → continue; `variant=handler`.
4. **Both** implements clauses present → continue; `variant=both`.
5. **Handler class** — annotated `@CommandHandler` / `@EventHandler` / `@QueryHandler` with no interceptor interface → **Rejected** (route to handler recipe).
6. **None of the above** → **Rejected**.

## Success Criteria

Extends DEFAULT.md baseline. All DEFAULT criteria (compile-clean, tests green, no silent regressions) plus:

### Recipe-specific structural invariants

1. **No AF4 method signatures survive**:
   - No `BiFunction<Integer, M, M> handle(List<? extends M> messages)`.
   - No `Object handle(UnitOfWork<? extends M> unitOfWork, InterceptorChain interceptorChain)`.

2. **AF5 method signatures present per variant**:
   - Dispatch: `MessageStream<?> interceptOnDispatch(M message, @Nullable ProcessingContext context, MessageDispatchInterceptorChain<M> chain)`.
   - Handler: `MessageStream<?> interceptOnHandle(M message, ProcessingContext context, MessageHandlerInterceptorChain<M> chain)`.

3. **`UnitOfWork` gone** — no `org.axonframework.messaging.unitofwork.UnitOfWork` import, no `CurrentUnitOfWork.get()`.

4. **`InterceptorChain` gone** — no `org.axonframework.messaging.InterceptorChain` import.

5. **AF5 imports present**:
   - `org.axonframework.messaging.core.MessageDispatchInterceptor` (dispatch variant).
   - `org.axonframework.messaging.core.MessageHandlerInterceptor` (handler variant).
   - `org.axonframework.messaging.core.MessageStream`.
   - `org.axonframework.messaging.core.unitofwork.ProcessingContext`.
   - `org.jspecify.annotations.Nullable` (dispatch variant — `@Nullable` on context parameter).

6. **Generic de-wildcarded** — `<CommandMessage<?>>` → `<CommandMessage>`, `<EventMessage<?>>` → `<EventMessage>`, etc. No wildcard on the message type.

7. **Path B only** — every `register*Interceptor(...)` call for `$SOURCE` uses `MessagingConfigurer` not AF4 `Configurer`.

Aggregation rule: **all match (AND)**.

### Verification

Use `axon4to5-isolatedtest` Skill per DEFAULT.md § Verification. `target-name` = simple class name of `$SOURCE`.

`extra-deps` baseline: `org.axonframework:axon-messaging`. Add `org.axonframework.extensions.spring:axon-spring-boot-starter` (or `io.axoniq.framework:…` when `framework=axoniq`) for `configuration=spring`.

## References

- [interceptors.adoc](../../docs/paths/interceptors.adoc) — *apply-condition:* always. Covers `interceptOnDispatch` / `interceptOnHandle` signatures, `ProcessingContext` lifecycle hooks, Spring auto-discovery, `MessagingConfigurer` registration methods, `@Order`, component-scoping factory pattern.
- [configuration.adoc](../../docs/paths/configuration.adoc) — *apply-condition:* `configuration=native` AND Path B registration site is in scope.
- [messages.adoc](../../docs/paths/messages.adoc) — *apply-condition:* interceptor body references `message.getMetaData()` / `message.getPayload()` / `message.withMetaData(...)` / `message.andMetaData(...)`.

### Atoms (code-change recipes — single-responsibility API transformations)

Load each atom whose apply-condition matches current scope. Atoms are the **canonical** source for exact
imports, before/after patterns, and gotchas for each API change; they replace inline repetition in the Toolbox.

| Atom file | Apply-condition |
|-----------|-----------------|
| [../../atoms/interceptor-dispatch.md](../../atoms/interceptor-dispatch.md) | `variant=dispatch` or `variant=both` |
| [../../atoms/interceptor-handler.md](../../atoms/interceptor-handler.md) | `variant=handler` or `variant=both` |
| [../../atoms/processing-context.md](../../atoms/processing-context.md) | handler variant AND body uses `UnitOfWork` lifecycle hooks |
| [../../atoms/message-accessors.md](../../atoms/message-accessors.md) | interceptor body uses `message.getMetaData()` / `message.getPayload()` / `message.andMetaData(...)` |

## Toolbox

> **Atom-based execution.** Atoms for this recipe are pre-loaded during Research (FLOW.md S3) per the
> `### Atoms` table above. Consult the loaded atom file for complete before/after, exact imports, and gotchas.
> The steps below provide ordering and apply-conditions; the atoms provide the HOW.

### Step 1 — Detect variant

*Apply-condition:* always.

Grep `$SOURCE`:
- `implements MessageDispatchInterceptor` → `variant=dispatch`
- `implements MessageHandlerInterceptor` → `variant=handler`
- both → `variant=both`
- `@MessageHandlerInterceptor` on a method → emit Blocker B1 (stop here)

### Step 2 — Rewrite dispatch method

*Apply-condition:* `variant=dispatch` or `variant=both`.

Apply **[[interceptor-dispatch]] atom** — covers `handle(List<M>)` → `interceptOnDispatch(M, @Nullable ProcessingContext, Chain)`, BiFunction lambda collapse, generic de-wildcard, and all import changes.

### Step 3 — Rewrite handler method

*Apply-condition:* `variant=handler` or `variant=both`.

Apply **[[interceptor-handler]] atom** — covers `handle(UnitOfWork, InterceptorChain)` → `interceptOnHandle(M, ProcessingContext, Chain)`, `chain.proceed()` → `chain.proceed(message, context)`, generic de-wildcard, and all import changes.

### Step 4 — Sweep `UnitOfWork` callsites

*Apply-condition:* handler variant AND body uses `UnitOfWork` lifecycle hooks.

Apply **[[processing-context]] atom** lifecycle table — covers `unitOfWork.onCommit` → `context.runOnAfterCommit`, `onRollback` → `context.onError`, `onCleanup` → `context.doFinally`, etc. Note: `unitOfWork.getMessage()` is replaced by the `message` parameter directly available in `interceptOnHandle`.

### Step 5 — Pick path and configure

*Apply-condition:* always.

**Path A — Spring Boot** (`configuration=spring`): verify `@Component` (or `@Bean`) present. `InterceptorAutoConfiguration` discovers all `MessageDispatchInterceptor<M>` / `MessageHandlerInterceptor<M>` beans and registers by generic `M` type. No explicit registration needed. If class name/comments suggest single-component intent (e.g., `OrderAggregateInterceptor`), surface in NOTES — do NOT block or add factory automatically.

**Path B — native** (`configuration=native`): grep project Configurer for `register(Command|Event|Query)?(Handler|Dispatch)Interceptor` for `$SOURCE`. Rewrite receiver from `Configurer` to `MessagingConfigurer`. Method names are identical except: AF4 generic `registerDispatchInterceptor` → AF5 typed `registerCommandDispatchInterceptor` / `registerEventDispatchInterceptor` / `registerQueryDispatchInterceptor`. Update import for `MessagingConfigurer`.

## Use cases

- [01-dispatch-spring-boot.md](use-cases/01-dispatch-spring-boot.md) — *apply-condition:* `variant=dispatch` AND `configuration=spring`.
- [02-handler-spring-boot.md](use-cases/02-handler-spring-boot.md) — *apply-condition:* `variant=handler` AND `configuration=spring`, body has `UnitOfWork` lifecycle hooks.
- [03-handler-native-config.md](use-cases/03-handler-native-config.md) — *apply-condition:* `configuration=native` AND Path B registration site in scope.
- [04-annotation-blocker.md](use-cases/04-annotation-blocker.md) — *apply-condition:* `@MessageHandlerInterceptor` annotation detected on a method (B1).

## Gotchas

- **`ProcessingContext` is `@Nullable` for dispatch, mandatory for handler.** Dispatch interceptors run before any context may exist. Pass `context` as-is to `chain.proceed(message, context)` — never short-circuit the chain based on null context.
- **Generic de-wildcard is mandatory.** `CommandMessage<?>` → `CommandMessage`. AF5 interfaces declare the message type without `<?>`. Leaving the wildcard causes a compile error.
- **BiFunction lambda collapses.** The AF4 batch-lambda `return (index, msg) -> { return modified; }` becomes inline: receive one `message`, modify it, call `chain.proceed(modified, context)`. The `index` and `List` concepts disappear entirely.
- **Lifecycle hook names AND signatures changed.** `onCommit` → `runOnAfterCommit`; `onPrepareCommit` → `runOnPreInvocation`; `onRollback` → `onError`. Lambda parameter: `UnitOfWork<M>` → `ProcessingContext` (or `(ctx, err)` for `onError`).
- **Path B: method names are identical; only receiver type changes.** `MessagingConfigurer.registerCommandHandlerInterceptor(...)` keeps the same method name as AF4. AF4 generic `registerDispatchInterceptor` → AF5 typed `registerCommandDispatchInterceptor` (or event/query variant as appropriate).
- **`@Order` preserved.** Preserve any existing `@Order(n)` annotation — AF5 `InterceptorAutoConfiguration` respects it. Add `@Order` only when a deterministic order is actually required.
- **Annotation B1 vs interface.** `@MessageHandlerInterceptor` as a method annotation is NOT the same as implementing the `MessageHandlerInterceptor<M>` interface. The interface is migratable today; the annotation requires AF5 5.2.0+. Always verify which form is present before proceeding.
- **`andMetaData` → `andMetadata` accessor rename.** AF5 message API uses `andMetadata(...)` (lowercase d). Covered by [messages.adoc](../../docs/paths/messages.adoc) — reference it when body uses AF4 `andMetaData` / `withMetaData` calls.

## Result

Inherits DEFAULT.md baseline.

### Success

Say **"return SUCCESS"**, then **MUST emit** the result block (schema: FLOW.md § Result). `Recipe:` field is `axon4to5-interceptors`. NOTES: variant migrated (dispatch / handler / both), path (A / B), registration sites updated if Path B.

### Blocker

Say **"return BLOCKER"**, then **MUST emit** the result block (schema: FLOW.md § Result). `Recipe:` field is `axon4to5-interceptors`. NOTES: name blocker (B1 annotation form / prerequisite-not-compiling) with `file:line`. OPTIONS: DEFAULT.md baselines (skip / revert / solve-manually).

Example (B1):

```
return BLOCKER

> **Result:** 🚧 Blocker
> **Source:** `com.example.OrderCommandHandler`
> **Recipe:** axon4to5-interceptors
>
> **Notes:** B1 detected — `@MessageHandlerInterceptor` used as method annotation at `OrderCommandHandler.java:34`. Not functional in AF5 < 5.2.0. No migration path; requires AF5 5.2.0+ or manual rewrite to standalone interceptor class.
>
> **Options:**
> - [ ] **skip** — keep `$SOURCE` in current state; queue moves on.
> - [ ] **revert** — undo any edits; restore pre-recipe state.
> - [ ] **solve-manually** — upgrade to AF5 5.2.0+ or extract to standalone `MessageHandlerInterceptor<M>` implementation.
```

### Rejected

Say **"return REJECTED"**, then **MUST emit** the result block (schema: FLOW.md § Result). `Recipe:` field is `axon4to5-interceptors`. NOTES: which predicate failed.

### Failure

Say **"return FAILURE"**, then **MUST emit** the result block (schema: FLOW.md § Result). NOTES: failing Success Criteria + last compiler error verbatim. LEARNINGS: hypothesis for next iteration.
