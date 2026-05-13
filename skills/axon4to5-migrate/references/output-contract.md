# Recipe Output — worked examples

Schema and orchestrator behavior live in [../SKILL.md](../SKILL.md) §"Output — one shape, six results". This file shows one canonical example per `result:` variant.

```yaml
result: success | skipped | rejected | needs-decision | blocked | failed
target: <FQ class | file path | "n/a">
reason: <one short line>                # required for every variant except success
decisions: { <recipe-specific keys> }
caller-expects:
  commit: true | false
  next:   proceed | ask-user | record-and-skip | halt | route-to:<recipe>
notes: <optional free text>
```

## `success`

```yaml
result: success
target: com.example.giftcard.GiftCard
decisions:
  path: A (Spring Boot)
  variant: simple
  creation-policy: NEVER
  test-fixture: migrated
  snapshotting: none
  deadline-handler: none
caller-expects: { commit: true, next: proceed }
```

## `skipped`

```yaml
result: skipped
target: com.example.giftcard.GiftCard
reason: class already uses @EventSourcedEntity — preflight idempotent
decisions: {}
caller-expects: { commit: false, next: proceed }
```

## `rejected`

```yaml
result: rejected
target: com.example.shipping.ShipmentProjection
reason: target has @EventHandler methods, not @Aggregate — wrong recipe
decisions: {}
caller-expects: { commit: false, next: route-to:event-processor }
notes: discovery grep matched on a legacy @AggregateIdentifier inside a value object — false positive
```

## `needs-decision`

```yaml
result: needs-decision
target: com.example.payment.PaymentSaga
reason: saga has @DeadlineHandler — four-way choice required
decisions:
  saga: pending
  deadline-handler-in-saga: present
caller-expects: { commit: false, next: ask-user }
notes: |
  AskUserQuestion options (verbatim from not-supported.md):
    - migrate-to-event-handler-with-state (BLOCKED — has deadline handler)
    - accept-stays-af4
    - pause-migration
    - remove-feature-first
```

## `blocked`

```yaml
result: blocked
target: com.example.eventstore.EventStoreConfig
reason: JdbcEventStorageEngine has no AF5 successor yet (B2)
decisions:
  jdbc-event-store: defer-until-af5-jdbc
  bean-replaced: "n/a — left commented-out with TODO[AF5 migration: B2]"
caller-expects: { commit: true, next: record-and-skip }
notes: user picked defer-until-af5-jdbc on AskUserQuestion; original @Bean preserved as commented block
```

## `failed`

```yaml
result: failed
target: <target project root>
reason: external skill axon4to5-openrewrite exited non-zero — "Maven build failed: dependency:resolve missing axon-spring-boot-autoconfigure"
decisions:
  framework: axoniq
caller-expects: { commit: false, next: halt }
notes: |
  Working tree clean (external skill rolled back).
  Recommend `debug` mode or manual investigation.
```

## When to emit which

| Situation | Variant |
|---|---|
| Preflight saw the target is already on AF5 | `skipped` |
| Routing matched but inspection shows wrong recipe | `rejected` |
| Recipe finished editing, scoped verify green | `success` |
| `not-supported.md` blocker hit, awaiting user choice | `needs-decision` |
| Blocker resolved as `accept-stays-af4` / `pause` / `defer-until-af5-*` (AF4 surface commented-out + TODO marker) | `blocked` |
| External tool non-zero / scoped verify red after edits / edit conflict | `failed` |
