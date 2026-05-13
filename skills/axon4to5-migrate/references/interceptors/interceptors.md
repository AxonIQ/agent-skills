# Recipe: interceptors

Migrate one AF4 `MessageDispatchInterceptor` or `MessageHandlerInterceptor`
class and, for framework-config projects, its registration site.

## Canonical reference

- [../../docs/paths/interceptors.adoc](../../docs/paths/interceptors.adoc)
- [../../docs/paths/configuration.adoc](../../docs/paths/configuration.adoc)
- [../../docs/paths/index.adoc](../../docs/paths/index.adoc)

## Goal

The interceptor compiles on AF5, keeps dispatch/handler behavior, and preserves
ordering/scoping decisions.

## Inputs

- `target`: interceptor FQCN or file path.
- `wiring`: `spring-boot` or `framework-config`.
- `target_test`: optional.

## Preflight

1. Reject classes that also contain command/event/query handlers; route to the
   handler recipe first.
2. If no AF4 interceptor interface remains, emit `skipped` or `rejected`
   depending on whether it was already migrated.

## Procedure

1. Classify variant:

   | Signal | Variant |
   |---|---|
   | `MessageDispatchInterceptor` | dispatch |
   | `MessageHandlerInterceptor` | handler |
   | both interfaces | both |

2. Rewrite method shape:

   | Variant | AF5 method direction |
   |---|---|
   | dispatch | `interceptOnDispatch(message, @Nullable context, chain)` returning `MessageStream<?>` |
   | handler | `interceptOnHandle(message, context, chain)` returning `MessageStream<?>` |

3. Replace `CurrentUnitOfWork` / `UnitOfWork` lifecycle calls with the
   provided `ProcessingContext`.
4. Update imports and chain/proceed calls.
5. Apply registration path:

   | `wiring` | Action |
   |---|---|
   | `spring-boot` | Keep component bean; add/preserve `@Order` only when deterministic order mattered. |
   | `framework-config` | Move `register*Interceptor(...)` calls to AF5 `MessagingConfigurer` APIs. |

6. If component-specific scoping is visible but ambiguous, emit
   `needs-decision`; do not guess between global and scoped interception.
7. Verify with `axon4to5-isolatedtest`.

## End condition

- AF4 interceptor interfaces/imports are gone.
- Handler/dispatch chains continue by calling AF5 `chain.proceed(...)`.
- Registration and ordering compile for the pinned wiring style.

## Output

```yaml
result: success | skipped | rejected | needs-decision | blocked | failed
target: <FQCN>
reason: <required except straightforward success>
decisions:
  variant: dispatch | handler | both
  registration: spring-auto | framework-config | none
  ordering: preserved | not-needed | needs-decision
caller-expects:
  commit: true | false
  next: proceed | ask-user | record-and-skip | halt | route-to:<recipe>
notes: []
```
