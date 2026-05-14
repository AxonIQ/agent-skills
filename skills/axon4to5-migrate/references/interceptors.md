# Recipe: interceptors (Dispatch / Handler)

Atomic migration of ONE class implementing `MessageDispatchInterceptor` or `MessageHandlerInterceptor` (or both). Also owns matching framework-config registration sites.

## Inputs

```yaml
target: <FQ class>                                 # required
target_test: <FQ test class>                       # optional
wiring: spring-boot | framework-config              # pinned project decision
decisions: { ... }                                  # see ## Decision points
```

## Preflight

1. For each entry in `## Decision points` with `trigger: detected-at-preflight`, run its Detection. If it fires AND the key isn't in `inputs.decisions` → **🔒 await decision** for that key.
2. **Reject mismatched classes**: if the candidate also declares `@CommandHandler` / `@EventHandler` / `@QueryHandler` / `@SagaEventHandler`, this isn't an interceptor recipe target — `output { result: rejected, route_to: <handler recipe>, reason: "handler annotations present" }`, exit.
3. **Reject annotation-based `@MessageHandlerInterceptor`** declared inside a handler class — NOT functional in AF5 < 5.2.0. `output { result: blocked }` with `notes: "annotation-based interceptor not in AF5 < 5.2.0; leave commented, defer"`.
4. Idempotency: compile clean? tests green? → **🔒 await decision** [`skip-or-deep-verify`](#skip-or-deep-verify).

## Decision points

### single-component-scoping

- **Trigger**: triggered-in-procedure (only on Path A — Spring Boot — when the candidate's name or comments suggest single-component intent, e.g. `OrderAggregateInterceptor`)
- **Question**: > "Interceptor `<name>` looks scoped to one component (per its name/comments). Spring auto-discovery applies it globally by message type. Confirm scoping intent?"
- **Options**:
    - `apply-globally` *(Recommended when AF4 had it global)* — leave `@Component`; AF5 `InterceptorAutoConfiguration` discovers by `Message` type
    - `scope-to-component-via-factory` — use `HandlerInterceptorFactory.of(...)` to scope to one component (replaces the implicit AF4 scope)
    - `pause-migration` — stop; user clarifies intent first
- **Auto-policy**:
    - `fallback: ask-user`
- **Effect**:
    - `apply-globally` → leave `@Component` annotation as-is; no factory wrapping
    - `scope-to-component-via-factory` → emit a `@Bean HandlerInterceptorFactory<...>` wrapping the interceptor; remove `@Component` from the impl class
    - `pause-migration` → `output { result: blocked }`, exit

### ordering

- **Trigger**: triggered-in-procedure (only on Path A — Spring Boot — when multiple interceptors of the same `Message` type exist in the project AND AF4 relied on registration insertion order)
- **Detection**: count of classes implementing the same `MessageHandlerInterceptor<M>` / `MessageDispatchInterceptor<M>` for the same `M`; if > 1, trigger fires.
- **Question**: > "Multiple `<message type>` interceptors exist in the project. AF5 auto-discovery has no implicit ordering. Preserve AF4 insertion order via `@Order`?"
- **Options**:
    - `preserve-via-@Order` *(Recommended when AF4 relied on order)* — add `@Order(N)` to each interceptor; recipe asks user for the ordinal
    - `accept-undefined-order` — leave ordering to Spring's default; potential behavior change if AF4 relied on it
    - `pause` — stop; user audits interceptor interactions first
- **Auto-policy**:
    - `fallback: ask-user`
- **Effect**:
    - `preserve-via-@Order` → ask follow-up for ordinal; add `@Order(N)` import + annotation
    - `accept-undefined-order` → no annotation added; record in `output.notes`
    - `pause` → `output { result: blocked }`, exit

### skip-or-deep-verify

- **Trigger**: triggered-in-procedure (only when Preflight idempotency check finds clean compile + green tests)
- **Question**: > "Interceptor appears already migrated. Skip or deep-verify?"
- **Options**:
    - `skip` *(Recommended)* — `output { result: skipped }`
    - `deep-verify` — diff vs AF4 baseline; continue to Procedure if any silent loss detected
- **Auto-policy**:
    - `pinned.resolver_mode == "automatic": skip`
    - `fallback: ask-user`
- **Effect**:
    - `skip` → exit with `result: skipped`.
    - `deep-verify` → continue.

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
| `Configurer.registerCommandHandlerInterceptor(...)` | `MessagingConfigurer.registerCommandHandlerInterceptor(...)` (method names unchanged; configurer type moves) |

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

#### Path A — Spring Boot (`wiring == spring-boot`)

- Leave `@Component` alone. `InterceptorAutoConfiguration` auto-discovers by the generic `Message` type — `<CommandMessage>` against command bus, `<EventMessage>` against event bus, `<Message<?>>` against all three.
- **🔒 await decision** [`single-component-scoping`](#single-component-scoping) only if the class name / comments suggest scoped intent.
- **🔒 await decision** [`ordering`](#ordering) only if multiple interceptors of the same `Message` type exist in the project.

#### Path B — framework Configurer (`wiring == framework-config`)

- Grep registration sites: `register(Command|Event|Query)?(Handler|Dispatch)Interceptor` in framework-config sources.
- Rewrite AF4 `Configurer.registerCommandHandlerInterceptor(...)` → AF5 `MessagingConfigurer.registerCommandHandlerInterceptor(...)`. Method names unchanged; the configurer type moves.
- Re-grep after the event-storage-engine recipe ran — it may have deferred some registrations.
- Same `single-component-scoping` decision applies (in Path B, use `HandlerInterceptorFactory.of(...)` at the registration site).

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
result: success | skipped | rejected | blocked | failed
target: <FQ class>
reason: <one short line>
decisions:
  path: A (Spring Boot) | B (framework Configurer)
  variant: dispatch | handler | both
  registration-sites-migrated: <count> | "n/a (Path A — auto-discovery)"
  single-component-scoping: apply-globally | scope-to-component-via-factory | pause-migration | n/a
  ordering: preserve-via-@Order | accept-undefined-order | pause | n/a
  unit-of-work-callsites: none | rewritten-to-processing-context
files_touched:
  - <repo-relative path>
route_to: <handler recipe>                # only on rejected (handler annotations on class)
notes: <free text>
```

## Subagent guidelines

```yaml
subagent_type: general-purpose
isolation: none
parallelism: per-item
on_unexpected_condition: keep-edits-and-fail
prompt-framing: |
  Atomic per-interceptor rewrite. Do NOT touch handler classes.
  If candidate also declares @CommandHandler/@EventHandler/@QueryHandler, return
  output { result: rejected, route_to: <handler recipe> } per Preflight rule.
```

**Eligibility**: subagent-eligible only AFTER `single-component-scoping`, `ordering`, `skip-or-deep-verify` are resolved (each is `fallback: ask-user`).

## Reference pairs (AF4 → AF5)

- **`MessageHandlerInterceptor<CommandMessage<?>>` with `UnitOfWork` body sweep, Spring Boot:** [evals/fixtures/axon4/heroes/PaidCommandInterceptor.java](../evals/fixtures/axon4/heroes/PaidCommandInterceptor.java). **AF5 paired file does not exist in the bundled examples** — the heroes AF5 project does not yet ship a migrated interceptor. The recipe's mechanical rewrite (Steps 1–7 above) is the reference; no eval case yet.
