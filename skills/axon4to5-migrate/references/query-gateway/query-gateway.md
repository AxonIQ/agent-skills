# Recipe: query-gateway

Migrate one top-of-chain caller that injects AF4 `QueryGateway`.

## Canonical reference

- [../../docs/paths/messages.adoc](../../docs/paths/messages.adoc)
- [../../docs/paths/index.adoc](../../docs/paths/index.adoc)
- [configuration-reads.md](configuration-reads.md) for direct query-bus reads.

## Goal

The caller performs the same point-to-point, subscription, or scatter-gather
query using AF5 APIs.

## Inputs

- `target`: caller FQCN or file path.
- `wiring`: `spring-boot` or `framework-config`.
- `target_test`: optional.

## Preflight

1. Reject handler classes; route them to `query-handler` or `event-processor`.
2. If no AF4 `QueryGateway` import/use remains, emit `skipped`.

## Procedure

1. Replace injected `QueryGateway` with the AF5 query API used by the project.
2. Rewrite calls by query shape:

   | AF4 shape | AF5 direction |
   |---|---|
   | single response | dispatch query and adapt completion stage/result wrapper |
   | `ResponseTypes.*` wrapper | remove wrapper; use typed AF5 query API |
   | named query / `@Query` | preserve query name and payload contract |
   | subscription query | keep initial result/update stream split |
   | scatter-gather | preserve multi-result streaming semantics; ask if old timeout behavior is ambiguous |

3. Preserve public method signatures where possible.
4. Update message annotations per the canonical message doc.
5. If the class reads `queryBus()` or `queryUpdateEmitter()`, apply
   `configuration-reads.md`.
6. Verify with `axon4to5-isolatedtest`.

## End condition

- No AF4 `QueryGateway` or `ResponseTypes` import/use remains.
- Query name, payload, response type, and streaming behavior are preserved.
- Scoped compile/tests pass or the result is classified.

## Output

```yaml
result: success | skipped | rejected | needs-decision | blocked | failed
target: <FQCN>
reason: <required except straightforward success>
decisions:
  query-shapes: []
  named-query-preserved: true | false | n/a
caller-expects:
  commit: true | false
  next: proceed | ask-user | record-and-skip | halt | route-to:<recipe>
notes: []
```
