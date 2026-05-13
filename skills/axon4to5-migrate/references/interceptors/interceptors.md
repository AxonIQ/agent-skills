# Recipe: Interceptor (MessageDispatchInterceptor / MessageHandlerInterceptor)

Atomic migration of ONE class that implements `MessageDispatchInterceptor` or `MessageHandlerInterceptor` (or both). Also owns the matching framework-config registration sites (`MessagingConfigurer.register*Interceptor`).

## Canonical reference

Read these for concepts, full FQN moves and worked before/after examples — NOT repeated here.

- [../../docs/paths/interceptors.adoc](../../docs/paths/interceptors.adoc) — `MessageDispatchInterceptor` / `MessageHandlerInterceptor` interface rewrite, declarative registration via `MessagingConfigurer`, Spring Boot auto-discovery, `@Order` ordering, `HandlerInterceptorFactory.of(...)` component-specific scoping, annotation-based `@MessageHandlerInterceptor` status.
- [../../docs/paths/index.adoc](../../docs/paths/index.adoc) §"Import and package changes" — exhaustive FQN table.
- [../../docs/paths/configuration.adoc](../../docs/paths/configuration.adoc) — `MessagingConfigurer` registration chain (for Path B registration sites).

This recipe holds only mechanical edits, scoped verify, and decision flow.

## Goal

The interceptor class compiles and behaves on AF5 APIs:

- `implements MessageDispatchInterceptor<...>` rewritten to `interceptOnDispatch(message, @Nullable context, chain)` returning `MessageStream<?>`. The AF4 batching `BiFunction<Integer, M, M>` shape is replaced by single-message form.
- `implements MessageHandlerInterceptor<...>` rewritten to `interceptOnHandle(message, context, chain)` returning `MessageStream<?>`. The AF4 `UnitOfWork<...>` parameter is removed; `ProcessingContext` is mandatory and never null during handling.
- All `CurrentUnitOfWork.get()` ThreadLocal reads inside the interceptor body are replaced by the injected `ProcessingContext`. Lifecycle hooks `runOnAfterCommit` / `runOnPreInvocation` / `onError` replace AF4 `unitOfWork.onCommit(...)` / `onPrepareCommit(...)` / `onRollback(...)`.
- Imports moved per the canonical FQN table.
- Path B (framework-config) only: registration site rewritten to the matching `MessagingConfigurer.register*Interceptor(...)` method.
- Path A (Spring Boot): the `@Component` bean is left alone — `InterceptorAutoConfiguration` discovers by generic `Message` type. `@Order` only added/preserved when determinism matters.

## Inputs

- target: FQ class name of the interceptor class (required)
- target_test: FQ test class name (optional — auto-discovered as `<target>Test` if absent)
- wiring: "spring-boot" | "framework-config" (required, supplied by orchestrator from `progress.md` Pinned-decisions)

## End condition

1. Zero compile errors in the interceptor class and its primary test class.
2. If the interceptor has a test class, scoped tests pass.
3. Path B only: every `register*Interceptor(...)` call site for the migrated interceptor resolves against `MessagingConfigurer` and compiles.

## Output

Emit exactly one fenced ```yaml block per the six-variant Output contract
([../output-contract.md](../output-contract.md)). Schema below shows the
`success` shape with all interceptor `decisions` keys; for the other
five variants copy the matching example from `output-contract.md`.

```yaml
result: success | skipped | rejected | needs-decision | blocked | failed
target: <FQ class>
reason: <one short line — required for every variant except success>
decisions:
  path: <A (Spring Boot) | B (framework Configurer)>     # taken from inputs.wiring
  variant: <dispatch | handler | both>
  registration-sites-migrated: <count | "n/a (Path A — auto-discovery)">
  ordering-decision: <none-needed | order-annotations-added | undefined-accepted | paused>
  unit-of-work-callsites: <none | rewritten-to-processing-context>
caller-expects:
  commit: <true | false>
  next: <proceed | ask-user | record-and-skip | halt | route-to:<recipe>>
notes: <optional free text — verbatim AskUserQuestion options for needs-decision>
```

## Preflight

1. Read [not-supported.md](not-supported.md) IF present in this folder — none today, slot reserved for future blockers (e.g. annotation-based `@MessageHandlerInterceptor` methods inside a handler class — NOT functional until AF 5.2.0 per the canonical doc).
2. Check compile errors on the file. If zero AND the test class compiles too:
3. Run scoped tests if they exist.
4. If green AND no blocker fired → STOP. `AskUserQuestion`: Skip / Deep verify.
5. Only proceed on **Deep verify** or compile/test failure.

## In scope

ONE class — Spring `@Component` (Path A) **or** plain Java/Kotlin registered via the framework `Configurer` (Path B) — that:

- `implements MessageDispatchInterceptor<...>` (`org.axonframework.messaging.MessageDispatchInterceptor` in AF4), AND/OR
- `implements MessageHandlerInterceptor<...>` (`org.axonframework.messaging.MessageHandlerInterceptor` in AF4).

Also in scope: the matching registration site(s) — `Configurer.registerCommandHandlerInterceptor(...)` / `registerDispatchInterceptor(...)` / etc. in framework-config code paths.

## Out of scope

- Classes carrying `@CommandHandler` / `@EventHandler` / `@QueryHandler` methods alongside the interceptor interface — those belong to the matching handler recipe; surface to orchestrator with `result: rejected`, `caller-expects.next: route-to:<event-processor | command-gateway | query-handler>`.
- Annotation-based `@MessageHandlerInterceptor` methods declared inside a handler class — NOT functional in AF5 < 5.2.0; flag via `learnings.md` and leave commented per the orchestrator's anti-pattern rules.
- Component-specific interceptor scoping via `HandlerInterceptorFactory.of(...)` — recipe surfaces it via AskUserQuestion when the user signals a single-component interceptor; recipe does not auto-pick.

## FQN cheat sheet (recipe-specific quick lookup)

Full table lives in [../../docs/paths/index.adoc](../../docs/paths/index.adoc) and [../../docs/paths/interceptors.adoc](../../docs/paths/interceptors.adoc). Only the moves that change **how a single class is edited** are duplicated here:

| Element | AF4 → AF5 short form |
|---|---|
| `MessageDispatchInterceptor.handle(List<? extends M>)` | `interceptOnDispatch(M message, @Nullable ProcessingContext context, MessageDispatchInterceptorChain<M> chain)` |
| `MessageHandlerInterceptor.handle(UnitOfWork<...>, InterceptorChain)` | `interceptOnHandle(M message, ProcessingContext context, MessageHandlerInterceptorChain<M> chain)` |
| `InterceptorChain` (synchronous) | typed `MessageDispatchInterceptorChain<M>` / `MessageHandlerInterceptorChain<M>` |
| `UnitOfWork<...>` parameter | removed; replaced by `ProcessingContext context` |
| `CurrentUnitOfWork.get()` body call | replaced by injected `context` |
| `uow.onCommit(...)` / `onPrepareCommit(...)` / `onRollback(...)` | `context.runOnAfterCommit(...)` / `runOnPreInvocation(...)` / `onError(...)` |
| Return type `Object` / `BiFunction<Integer, M, M>` | `MessageStream<?>` (call `chain.proceed(message, context)`) |
| `Configurer.registerCommandHandlerInterceptor(...)` | `MessagingConfigurer.registerCommandHandlerInterceptor(...)` (same name; see canonical doc table for full method family) |

## Procedure

1. Detect variant.
   - `implements\s+MessageDispatchInterceptor\b` present → variant=dispatch
   - `implements\s+MessageHandlerInterceptor\b` present → variant=handler
   - both present → variant=both (run dispatch rewrite then handler rewrite on the same class)
2. Rewrite the interface method per variant — find/replace pivots only:
   - dispatch: method name `handle` → `interceptOnDispatch`; signature `(List<? extends M>)` → `(M, @Nullable ProcessingContext, MessageDispatchInterceptorChain<M>)`; return `BiFunction<Integer, M, M>` → `MessageStream<?>`; body's `return (i, msg) -> {...}` lambda flattens to direct single-message form ending in `return chain.proceed(message, context);`.
   - handler: method name `handle` → `interceptOnHandle`; signature `(UnitOfWork<? extends M>, InterceptorChain)` → `(M, ProcessingContext, MessageHandlerInterceptorChain<M>)`; return `Object` → `MessageStream<?>`; body's `return interceptorChain.proceed();` → `return chain.proceed(message, context);`.
3. Sweep the body for `CurrentUnitOfWork.get()`, `unitOfWork.onCommit(...)`, `unitOfWork.onPrepareCommit(...)`, `unitOfWork.onRollback(...)`, `unitOfWork.getResource(...)`. Rewrite via injected `context` per the FQN cheat sheet. Code samples live in canonical doc.
4. Update imports per the FQN cheat sheet and the full table in [../../docs/paths/index.adoc](../../docs/paths/index.adoc).
5. Pick path from pinned `wiring` decision (recipes do NOT re-detect):
   - inputs.wiring == "spring-boot"      → Path A
   - inputs.wiring == "framework-config" → Path B
6. Run path Steps (see ### Path A / ### Path B).
7. Migrate the matching test class if one exists.
   - `Mockito.mock(InterceptorChain.class)` → mock the typed chain (`MessageDispatchInterceptorChain<M>` or `MessageHandlerInterceptorChain<M>` — pick by variant).
   - `UnitOfWork` mocks → construct/inject a `ProcessingContext` (real, not mocked) per the canonical doc's test-fixture guidance.
8. Run scoped verify via `axon4to5-isolatedtest` (Skill tool — see [../verification.md](../verification.md)).
9. Verify against `## End condition`.
10. Emit `## Output`.

### Path A — Spring Boot

#### Condition

- inputs.wiring == "spring-boot"

#### Steps

- Leave `@Component` annotation alone. AF5 `InterceptorAutoConfiguration` auto-discovers by the interceptor's generic `Message` type — `MessageHandlerInterceptor<CommandMessage>` is registered against the command bus, `<EventMessage>` against the event bus, `<Message<?>>` against all three. See canonical doc §"Spring Boot interceptor registration".
- Single-component scoping: if the user's intent (revealed during AskUserQuestion or visible in code comments / class name like `OrderAggregateInterceptor`) is that the interceptor must only apply to one entity/component, surface `HandlerInterceptorFactory.of(...)` via AskUserQuestion — options: `apply-globally` (Recommended — preserves AF4 behavior if AF4 had it global) / `scope-to-component-via-factory` / `pause-migration`. Recipe does NOT auto-pick.
- Ordering: if multiple interceptors of the same message type exist and AF4 relied on registration insertion order, AskUserQuestion: `preserve-via-@Order` (Recommended) / `accept-undefined-order` / `pause`. Add `@Order(N)` to each only on `preserve-via-@Order`.

### Path B — framework Configurer

#### Condition

- inputs.wiring == "framework-config"

#### Steps

- Locate registration sites: grep `register(Command|Event|Query)?(Handler|Dispatch)Interceptor` in framework-config sources (`MessagingConfigurer.create()` / `EventSourcingConfigurer.create()` call chains).
- Rewrite AF4 `Configurer.registerCommandHandlerInterceptor(...)` → AF5 `MessagingConfigurer.registerCommandHandlerInterceptor(...)`. Method names are unchanged; what moves is the configurer type. The full method family (all-message-types / command-only / event-only / query-only, handler / dispatch) is tabled in canonical doc §"Declarative interceptor registration".
- Some registration sites may already have been touched by the storage/configuration recipe — re-grep after that recipe ran to catch any registrations it deferred.
- Component-specific scoping via `HandlerInterceptorFactory.of(...)`: same AskUserQuestion as Path A; recipe does not auto-pick.

## Subagent guidelines

- subagent_type: general-purpose

- isolation: none

- prompt-framing: |
  Atomic per-interceptor rewrite. Do NOT touch handler classes (those belong to event-processor / command-gateway / query-handler recipes). If the candidate class also declares `@CommandHandler` / `@EventHandler` / `@QueryHandler` methods, surface that to the orchestrator with `result: rejected`, `caller-expects.next: route-to:<the matching handler recipe>` — it indicates a wrong-recipe routing.

- parallelism: per-item
