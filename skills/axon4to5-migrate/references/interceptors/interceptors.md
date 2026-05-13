# Recipe: interceptors (Dispatch / Handler)

Atomic migration of ONE class implementing `MessageDispatchInterceptor` or `MessageHandlerInterceptor` (or both). Also owns matching framework-config registration sites.

## Inputs

- `target` — FQ class (required)
- `target_test` — FQ test class (optional)
- `wiring` — `spring-boot` | `framework-config` (pinned)

## Preflight

1. Compile clean?
2. If test class exists, run scoped tests.
3. All green → `AskUserQuestion`: Skip / Deep verify.

## In scope

ONE class that `implements MessageDispatchInterceptor<…>` AND/OR `MessageHandlerInterceptor<…>` (AF4 location `org.axonframework.messaging.*`). Plus matching framework-config registration sites (`MessagingConfigurer.register*Interceptor(...)`).

## Out of scope

- Classes carrying `@CommandHandler` / `@EventHandler` / `@QueryHandler` methods alongside the interceptor interface → `result: rejected`, `next: route-to:<handler recipe>`.
- Annotation-based `@MessageHandlerInterceptor` methods declared inside a handler class — NOT functional in AF5 < 5.2.0; flag in `learnings.md`, leave commented per orchestrator anti-pattern.
- Component-specific scoping via `HandlerInterceptorFactory.of(...)` — surfaced via `AskUserQuestion`, never auto-picked.

## FQN cheat sheet

| AF4 | AF5 |
|---|---|
| `MessageDispatchInterceptor.handle(List<? extends M>)` | `interceptOnDispatch(M, @Nullable ProcessingContext, MessageDispatchInterceptorChain<M>)` |
| `MessageHandlerInterceptor.handle(UnitOfWork<…>, InterceptorChain)` | `interceptOnHandle(M, ProcessingContext, MessageHandlerInterceptorChain<M>)` |
| `InterceptorChain` (synchronous) | typed `MessageDispatchInterceptorChain<M>` / `MessageHandlerInterceptorChain<M>` |
| `UnitOfWork<…>` parameter | **removed**; replaced by `ProcessingContext context` |
| `CurrentUnitOfWork.get()` body call | replaced by injected `context` |
| `uow.onCommit(...)` / `onPrepareCommit(...)` / `onRollback(...)` | `context.runOnAfterCommit(...)` / `runOnPreInvocation(...)` / `onError(...)` |
| Return type `Object` / `BiFunction<Integer, M, M>` | `MessageStream<?>` (call `chain.proceed(message, context)`) |
| `Configurer.registerCommandHandlerInterceptor(...)` | `MessagingConfigurer.registerCommandHandlerInterceptor(...)` (same method names; the configurer type moves) |

## Procedure

### Step 1 — Detect variant

- `implements MessageDispatchInterceptor` → variant `dispatch`
- `implements MessageHandlerInterceptor` → variant `handler`
- both → variant `both` (run dispatch rewrite then handler rewrite)

### Step 2 — Rewrite interface method per variant

**Dispatch:**
- Method name `handle` → `interceptOnDispatch`.
- Signature: `(List<? extends M>)` → `(M, @Nullable ProcessingContext, MessageDispatchInterceptorChain<M>)`.
- Return type: `BiFunction<Integer, M, M>` → `MessageStream<?>`.
- Body's `return (i, msg) -> {...}` flattens to direct single-message form ending `return chain.proceed(message, context);`.

**Handler:**
- Method name `handle` → `interceptOnHandle`.
- Signature: `(UnitOfWork<? extends M>, InterceptorChain)` → `(M, ProcessingContext, MessageHandlerInterceptorChain<M>)`.
- Return type: `Object` → `MessageStream<?>`.
- Body's `return interceptorChain.proceed();` → `return chain.proceed(message, context);`.

### Step 3 — Sweep `UnitOfWork` callsites in the body

Rewrite via the injected `context`:
- `CurrentUnitOfWork.get()` → `context`.
- `unitOfWork.onCommit(...)` → `context.runOnAfterCommit(...)`.
- `unitOfWork.onPrepareCommit(...)` → `context.runOnPreInvocation(...)`.
- `unitOfWork.onRollback(...)` → `context.onError(...)`.
- `unitOfWork.getResource(...)` → resolve via `context` API.

### Step 4 — Update imports per the cheat sheet

### Step 5 — Pick path from pinned `wiring`

### Path A — Spring Boot

- Leave `@Component` alone. `InterceptorAutoConfiguration` auto-discovers by the generic `Message` type — `<CommandMessage>` against command bus, `<EventMessage>` against event bus, `<Message<?>>` against all three.
- **Single-component scoping** — if the user's intent (visible in name like `OrderAggregateInterceptor` or revealed in comments) is to apply only to one entity, `AskUserQuestion`: `apply-globally` *(Recommended — matches AF4 if AF4 had it global)* / `scope-to-component-via-factory` (`HandlerInterceptorFactory.of(...)`) / `pause-migration`.
- **Ordering** — if multiple interceptors of same message type exist and AF4 relied on registration order, `AskUserQuestion`: `preserve-via-@Order` *(Recommended)* / `accept-undefined-order` / `pause`. Only on `preserve-via-@Order` add `@Order(N)`.

### Path B — framework Configurer

- Grep registration sites: `register(Command|Event|Query)?(Handler|Dispatch)Interceptor` in framework-config sources.
- Rewrite AF4 `Configurer.registerCommandHandlerInterceptor(...)` → AF5 `MessagingConfigurer.registerCommandHandlerInterceptor(...)`. Method names unchanged; the configurer type moves.
- Re-grep after the event-storage-engine recipe ran — it may have deferred some registrations.
- Component-specific scoping same `AskUserQuestion` as Path A.

### Step 6 — Test class

If a test exists:
- `Mockito.mock(InterceptorChain.class)` → mock the typed chain (`MessageDispatchInterceptorChain<M>` / `MessageHandlerInterceptorChain<M>` — pick by variant).
- `UnitOfWork` mocks → construct/inject a real `ProcessingContext` (don't mock).

### Step 7 — Verify + emit Output

## End condition

1. Zero compile errors in the class + its test class.
2. If a test class exists, scoped tests pass via `axon4to5-isolatedtest`.
3. Path B: every `register*Interceptor(...)` site for this interceptor resolves against `MessagingConfigurer` and compiles.

## Output

```yaml
result: success | skipped | rejected | needs-decision | blocked | failed
target: <FQ class>
reason: <one short line>
decisions:
  path: A (Spring Boot) | B (framework Configurer)
  variant: dispatch | handler | both
  registration-sites-migrated: <count> | "n/a (Path A — auto-discovery)"
  ordering-decision: none-needed | order-annotations-added | undefined-accepted | paused
  unit-of-work-callsites: none | rewritten-to-processing-context
caller-expects: { commit: <bool>, next: <…> }
notes: <…>
```

## Subagent guidelines

```yaml
subagent_type: general-purpose
isolation: none
parallelism: per-item
prompt-framing: |
  Atomic per-interceptor rewrite. Do NOT touch handler classes.
  If candidate also declares @CommandHandler/@EventHandler/@QueryHandler, return result:rejected
  with next: route-to:<handler recipe>.
```

## Reference pairs (AF4 → AF5)

- **`MessageHandlerInterceptor<CommandMessage<?>>` with `UnitOfWork` body sweep, Spring Boot:** `axon4/heroes/.../resourcespool/write/withdraw/PaidCommandInterceptor.java` (AF5 paired file not present — the recipe's mechanical rewrite IS the reference; see [evals/fixtures/interceptors-heroes.md](../../evals/fixtures/interceptors-heroes.md) for the must-haves).
