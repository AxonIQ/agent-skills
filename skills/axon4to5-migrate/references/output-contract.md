# Output Contract

Every recipe emits one fenced YAML block. The top-level `result:` is the only
branch key.

```yaml
result: success | skipped | rejected | needs-decision | blocked | failed
target: <FQCN, file, or project root>
reason: <required except straightforward success>
decisions: {}
caller-expects:
  commit: true | false
  next: proceed | ask-user | record-and-skip | halt | route-to:<recipe>
notes: []
```

## Result Meanings

| `result` | Use when | Commit? | Next |
|---|---|---|---|
| `success` | Recipe changed code and end condition is green. | yes | `proceed` |
| `skipped` | Target was already migrated; no edits. | no | `proceed` |
| `rejected` | Target belongs to another recipe or no recipe. | no | `proceed` or `route-to:<recipe>` |
| `needs-decision` | A human choice is required before edits continue. | no | `ask-user` |
| `blocked` | Known unsupported/deferred AF5 gap was recorded. | maybe | `record-and-skip` |
| `failed` | Unexpected tool, edit, or verify failure. | no | `halt` |

## Minimal Examples

```yaml
result: success
target: org.example.Faculty
decisions:
  variant: simple
caller-expects:
  commit: true
  next: proceed
notes: []
```

```yaml
result: rejected
target: org.example.BillingProjection
reason: "class is an event handler, not a command-gateway caller"
decisions: {}
caller-expects:
  commit: false
  next: route-to:event-processor
notes: []
```

```yaml
result: needs-decision
target: org.example.PaymentSaga
reason: "AF4 saga has deadline handlers; no automatic AF5 saga migration"
decisions:
  classification: deadline-blocked
caller-expects:
  commit: false
  next: ask-user
notes:
  - "Options: accept-stays-af4 / pause-migration / remove-feature-first"
```

```yaml
result: blocked
target: org.example.AxonConfig
reason: "JdbcEventStorageEngine has no AF5 drop-in equivalent"
decisions:
  event-storage-engine.B2: defer-until-af5-jdbc
caller-expects:
  commit: false
  next: record-and-skip
notes: []
```

```yaml
result: failed
target: org.example.Projection
reason: "scoped compile still fails after rewrite"
decisions: {}
caller-expects:
  commit: false
  next: halt
notes:
  - "<paste concise tool/build summary>"
```

## Legacy Fields Are Forbidden

Do not emit `needs-user-decision`, `needs-user-decision-reason`,
`recipe-status`, or `skip`. Fold those meanings into `result`, `reason`,
`decisions`, and `caller-expects`.
