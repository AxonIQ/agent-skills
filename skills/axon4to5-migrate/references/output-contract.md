# Output contract — worked examples

Canonical examples for the six-variant Output union defined in
[../SKILL.md](../SKILL.md) §"Output contract — six variants". Every recipe's
`## Output` MUST emit a fenced ```yaml block whose top-level
`result:` is exactly one of: `success | skipped | rejected | needs-decision | blocked | failed`.

The migration runner branches on `result:` alone. `decisions:` keys are
recipe-specific and feed the commit body. `caller-expects:` is a
self-describing hint for the caller (migration runner or parent subagent).
`notes:` is free text.

## When to emit which variant

| Situation in the recipe | Variant |
|---|---|
| Preflight saw the target is already on AF5 (idempotent re-run) | `skipped` |
| Routing matched but inspection shows wrong recipe (e.g. `aggregate` invoked on a class with `@EventHandler` only) | `rejected` |
| Recipe finished editing, scoped verify green, end-condition met | `success` |
| `not-supported.md` blocker hit and `AskUserQuestion` has not yet been answered | `needs-decision` |
| Blocker resolved as `accept-stays-af4` / `pause-migration` / `defer-until-af5-*` — AF4 surface kept (commented-out + TODO marker) | `blocked` |
| External tool exit non-zero with rollback, scoped verify red after edits, edit conflict — no known recovery from inside the recipe | `failed` |

## Six examples

### `success`

```yaml
result: success
target: com.example.giftcard.GiftCard
reason: aggregate migrated, scoped verify green
decisions:
  path: A (Spring Boot)
  variant: simple
  creation-policy: NEVER
  test-fixture: migrated
  snapshotting: none
  deadline-handler: none
caller-expects:
  commit: true
  next: proceed
notes: ""
```

### `skipped`

```yaml
result: skipped
target: com.example.giftcard.GiftCard
reason: class already uses @EventSourcedEntity — preflight idempotent
decisions: {}
caller-expects:
  commit: false
  next: proceed
notes: ""
```

### `rejected`

```yaml
result: rejected
target: com.example.shipping.ShipmentProjection
reason: target has @EventHandler methods, not @Aggregate — wrong recipe
decisions: {}
caller-expects:
  commit: false
  next: route-to:event-processor
notes: "discovery grep matched on a legacy @AggregateIdentifier inside a value object — false positive"
```

### `needs-decision`

```yaml
result: needs-decision
target: com.example.payment.PaymentSaga
reason: saga has @DeadlineHandler — four-way choice required
decisions:
  saga: pending
  deadline-handler-in-saga: present
caller-expects:
  commit: false
  next: ask-user
notes: |
  AskUserQuestion options (verbatim from not-supported.md):
    - migrate-to-event-handler-with-state (BLOCKED — has deadline handler)
    - accept-stays-af4
    - pause-migration
    - remove-feature-first
```

### `blocked`

```yaml
result: blocked
target: com.example.eventstore.EventStoreConfig
reason: JdbcEventStorageEngine has no AF5 successor yet (B2)
decisions:
  jdbc-event-store: defer-until-af5-jdbc
  bean-replaced: "n/a — left commented-out with TODO[AF5 migration: B2]"
caller-expects:
  commit: true
  next: record-and-skip
notes: "user picked defer-until-af5-jdbc on AskUserQuestion; original @Bean preserved as commented block per Anti-patterns rule"
```

### `failed`

```yaml
result: failed
target: <target project root>
reason: external skill axon4to5-openrewrite exited non-zero — "Maven build failed: dependency:resolve missing axon-spring-boot-autoconfigure"
decisions:
  framework: axoniq
caller-expects:
  commit: false
  next: halt
notes: |
  Working tree clean (external skill rolled back).
  Recommend `debug` mode or manual investigation.
```

## Schema reference

```yaml
result: success | skipped | rejected | needs-decision | blocked | failed
target: <FQ class | file path | "n/a">
reason: <one short line — required for every variant except success>
decisions:
  <recipe-specific key>: <value>
  # ... freeform; migration runner copies these into the commit body verbatim.
caller-expects:
  commit: <true | false>
  next: <proceed | ask-user | record-and-skip | halt | route-to:<recipe>>
notes: <optional free text — verbatim AskUserQuestion options for needs-decision,
        external tool output for failed, etc.>
```

## What changed vs. the legacy shape

Removed (forbidden by SKILL.md lint):

- `needs-user-decision: <true|false>` → fold into `result: needs-decision`
- `needs-user-decision-reason: <text>` → fold into `reason:`
- `recipe-status: <success | failed | skipped-already-applied | bailed-*>` → fold into `result:`
- `skip: true` → fold into `result: skipped`

Kept verbatim:

- `target:` — same semantics, same values.
- `decisions:` — same recipe-specific keys (path, variant, blocker resolution keys from `not-supported.md`, …). They still feed the commit body.
- `notes:` — same free-text channel.
