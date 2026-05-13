# Query Gateway Patterns

| Case | Preserve | Rewrite direction |
|---|---|---|
| single response query | public return type | AF5 typed query call and result adaptation |
| sync callback wrapper | callback semantics | completion-stage callback or explicit blocking |
| named query | query name and payload type | AF5 named query metadata/annotation |
| subscription query | initial result + updates | keep split stream/result shape |
| scatter-gather | multi-result semantics and timeout | AF5 streaming/multi-result API; ask if timeout behavior is unclear |

Use `../query-gateway.md` as the source of truth.
