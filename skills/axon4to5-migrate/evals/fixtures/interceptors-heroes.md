# Eval fixture — `interceptors` on `PaidCommandInterceptor`

**AF4:** `axon4/heroes/.../resourcespool/write/withdraw/PaidCommandInterceptor.java`
**AF5 reference:** (not present in AF5 heroes — the recipe's mechanical rewrite is the reference).

`MessageHandlerInterceptor<CommandMessage<?>>` implementation. The AF4 class reads from the `UnitOfWork`, calls into a repository for cost validation, then proceeds.

## Trigger

```
/axon4to5-migrate src/main/java/com/dddheroes/heroesofddd/resourcespool/write/withdraw/PaidCommandInterceptor.java
```

## Must-haves

### Method rewrite (variant = `handler`)

- ✅ Method name `handle` → `interceptOnHandle`.
- ✅ Signature `(UnitOfWork<? extends CommandMessage<?>>, InterceptorChain)` → `(CommandMessage<?>, ProcessingContext, MessageHandlerInterceptorChain<CommandMessage<?>>)`.
- ✅ Return type `Object` → `MessageStream<?>`.
- ✅ Body `return interceptorChain.proceed();` → `return chain.proceed(message, context);`.
- ✅ Any `unitOfWork.getMessage()` rewritten to use the injected `CommandMessage<?>` parameter directly.

### Imports

- ✅ Removed: `org.axonframework.messaging.MessageHandlerInterceptor`, `org.axonframework.messaging.InterceptorChain`, `org.axonframework.messaging.unitofwork.UnitOfWork`, `org.axonframework.commandhandling.CommandMessage`.
- ✅ Added: `org.axonframework.messaging.MessageHandlerInterceptor` (AF5 location), `MessageHandlerInterceptorChain`, `org.axonframework.messaging.unitofwork.ProcessingContext`, `org.axonframework.messaging.MessageStream`, and the AF5 `CommandMessage` (`org.axonframework.messaging.commandhandling.CommandMessage`).

### `UnitOfWork` body sweep

- ✅ `CurrentUnitOfWork.get()` (if any) → `context`.
- ✅ `unitOfWork.onCommit(...)` → `context.runOnAfterCommit(...)`.
- ✅ `unitOfWork.onPrepareCommit(...)` → `context.runOnPreInvocation(...)`.
- ✅ `unitOfWork.onRollback(...)` → `context.onError(...)`.

### Path A — Spring Boot

- ✅ `@Component` left alone (or added if missing) — `InterceptorAutoConfiguration` auto-discovers by generic `Message` type.
- ✅ Single-component scoping question raised via `AskUserQuestion` if class name hints at it (this class is named for a particular command flow — surface).

## Anti-patterns

- ❌ `UnitOfWork` parameter kept (must be replaced by `ProcessingContext`).
- ❌ Body returns `Object` cast to `MessageStream` instead of properly returning `MessageStream<?>`.
- ❌ Class also has `@CommandHandler` etc. — recipe must `result: rejected` with `next: route-to:<handler recipe>` instead of rewriting.

## Output contract

```yaml
result: success
target: com.dddheroes.heroesofddd.resourcespool.write.withdraw.PaidCommandInterceptor
decisions:
  path: A (Spring Boot)
  variant: handler
  registration-sites-migrated: "n/a (Path A — auto-discovery)"
  ordering-decision: none-needed
  unit-of-work-callsites: rewritten-to-processing-context
caller-expects: { commit: true, next: proceed }
```
