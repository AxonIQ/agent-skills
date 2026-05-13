# Query Handler Patterns

| Case | Preserve | Rewrite direction |
|---|---|---|
| simple handler | payload and return type | move annotations/imports only |
| named query | query name | preserve name in AF5 annotation/metadata |
| mixed event/query component | both handler contracts | run event-processor first, then query-handler if needed |
| context-dependent handler | metadata/context access | add AF5 context parameter; avoid thread-local/static access |

Use `../query-handler.md` as the source of truth.
