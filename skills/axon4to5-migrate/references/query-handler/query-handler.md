# Recipe: query-handler

Migrate one class with AF4 `@QueryHandler` methods.

## Canonical reference

- [../../docs/paths/messages.adoc](../../docs/paths/messages.adoc)
- [../../docs/paths/index.adoc](../../docs/paths/index.adoc)

## Goal

Query handler methods compile on AF5 and keep the same query names, payloads,
response shapes, and side effects.

## Inputs

- `target`: handler FQCN or file path.
- `wiring`: `spring-boot` or `framework-config`.
- `target_test`: optional.

## Preflight

1. If no `@QueryHandler` exists, emit `rejected`.
2. If the class already uses AF5 query-handler imports and tests pass, emit
   `skipped`.

## Procedure

1. Move `@QueryHandler` and related query annotations to AF5 packages.
2. Preserve method names, payload parameters, and return types unless they
   expose removed AF4 types.
3. Update named-query annotations and message metadata annotations per the
   canonical docs.
4. If the method needs AF5 context/dispatch objects, add them as method
   parameters instead of using AF4 static/thread-local access.
5. Keep Spring/component annotations or framework-config registration according
   to pinned `wiring`.
6. Verify with `axon4to5-isolatedtest`.

## End condition

- No AF4 query-handler imports remain.
- Query names and response contracts are preserved.
- Scoped compile/tests pass or the result is classified.

## Output

```yaml
result: success | skipped | rejected | needs-decision | blocked | failed
target: <FQCN>
reason: <required except straightforward success>
decisions:
  named-queries: preserved | none | changed-with-reason
  context-parameters-added: []
caller-expects:
  commit: true | false
  next: proceed | ask-user | record-and-skip | halt | route-to:<recipe>
notes: []
```
