# Aggregate Blockers

Run these checks before editing an aggregate.

## Blocker Table

| Key | Detection | Why it blocks | Options |
|---|---|---|---|
| `B1` | `snapshotTriggerDefinition`, `Snapshotter`, `SnapshotTriggerDefinition` | AF5 snapshot wiring differs and may need separate policy design. | `pause-migration`, `remove-feature-first`, `accept-no-snapshots` when tests prove safe |
| `B3` | map-typed `@AggregateMember` | Multi-entity routing/tagging needs explicit design. | `pause-migration`, `remove-feature-first` |
| `B4` | `SagaTestFixture` in aggregate test area | Sagas are not automatically migrated. | `route-to:saga`, `pause-migration` |
| `B5` | `@DeadlineHandler` or `DeadlineManager` in aggregate | Deadline behavior needs workflow/scheduler decision. | `pause-migration`, `remove-feature-first`, `accept-stays-af4` |

## Procedure

1. Run the detection grep for the target class, its nested entities, and primary
   test file.
2. If no blocker fires, continue the aggregate recipe.
3. If a blocker fires and there is no pinned decision, emit `needs-decision`
   with the options from the table.
4. If the user chooses a non-AF5/deferred path, emit `blocked` and record the
   key in `decisions`.
5. If code is commented out because of a blocker, add
   `TODO[AF5 migration: <key>]` and keep enough AF4 context to restore later.

## Output Decision Keys

Use stable keys:

- `aggregate.B1.snapshotting`
- `aggregate.B3.map-member`
- `aggregate.B4.saga-fixture`
- `aggregate.B5.deadline`
