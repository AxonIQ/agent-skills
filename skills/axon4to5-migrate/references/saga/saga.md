# Recipe: saga

AF4 sagas are project-wide blockers. This recipe records a decision per saga
and gives a small migration path only for simple sagas that can become regular
event-handling components with explicit state.

## Canonical reference

- [../../docs/paths/index.adoc](../../docs/paths/index.adoc) — unsupported AF5
  areas.
- [../../docs/paths/projectors-event-processors.adoc](../../docs/paths/projectors-event-processors.adoc)
- [../../docs/paths/test-fixtures.adoc](../../docs/paths/test-fixtures.adoc)

## Goal

Do not pretend sagas are automatically migrated. Either record that the saga
stays/defer/removes, or guide a simple rewrite into a normal AF5 event handler.

## Inputs

- `target`: saga FQCN.
- `wiring`: `spring-boot` or `framework-config`.

## Preflight

1. Confirm the target has `@Saga`, `@SagaEventHandler`, `@StartSaga`,
   `@EndSaga`, or `SagaConfigurer`.
2. Detect deadline use. Deadlines block the simple migration path.
3. Detect association complexity. Multiple dynamic associations or custom
   association values block the simple migration path.

## Procedure

1. **Classify the saga.**

   | Signal | Classification |
   |---|---|
   | `@DeadlineHandler` / `DeadlineManager` | `deadline-blocked` |
   | simple start/end events, state reconstructable from events | `event-sourced-state-candidate` |
   | state must be queried or has non-event-derived fields | `jpa-state-candidate` |
   | complex associations / custom scheduler / external workflow | `manual` |

2. **Ask for one decision.**

   | Option | When valid | Result |
   |---|---|---|
   | `migrate-to-event-handler-with-state` | no deadlines and simple associations | user rewrites or reruns target through `event-processor` after state class exists |
   | `accept-stays-af4` | user keeps this slice on AF4 deps for now | `blocked` |
   | `pause-migration` | user needs design decision | `blocked` |
   | `remove-feature-first` | user will delete/refactor saga separately | `blocked` |

3. **If migration is chosen, use one of two shapes.**

   | Shape | Use when | Code sketch |
   |---|---|---|
   | event-sourced state | state can be rebuilt from events | state entity plus event handler using `@InjectEntity` / AF5 entity loading |
   | JPA state | state must be queryable or not event-derived | Spring component event handler plus repository-owned state |

4. **Testing direction.**
   - `SagaTestFixture` does not carry forward.
   - Use `AxonTestFixture` for event-sourced state shape.
   - Use ordinary Spring/repository tests for JPA state shape.

5. **Record the decision.**
   - The migration runner writes `progress.md` and `learnings.md`.
   - No automatic success is emitted for a saga decision.

## End condition

One decision is recorded for the saga. If migration was chosen, the actual code
rewrite is a follow-up through `event-processor` or ordinary application code,
not a hidden saga auto-port.

## Output

```yaml
result: needs-decision | blocked
target: <FQCN>
reason: <why this saga cannot be auto-migrated>
decisions:
  saga-decision: migrate-to-event-handler-with-state | accept-stays-af4 | pause-migration | remove-feature-first
  classification: deadline-blocked | event-sourced-state-candidate | jpa-state-candidate | manual
caller-expects:
  commit: false
  next: ask-user | record-and-skip
notes: []
```

## Caveats

- Axoniq Workflows or a custom scheduler may be the right long-term answer for
  deadline-heavy sagas, but this recipe does not implement that migration.
- Do not delete saga code silently. Preserve the audit trail until the user
  removes or rewrites it.
