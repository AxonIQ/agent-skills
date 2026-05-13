# Recipe: aggregate

Migrate one AF4 aggregate class to the AF5 event-sourced entity model.

## Canonical reference

- [../../docs/paths/index.adoc](../../docs/paths/index.adoc) — package moves.
- [../../docs/paths/messages.adoc](../../docs/paths/messages.adoc) — message annotations.
- [../../docs/paths/test-fixtures.adoc](../../docs/paths/test-fixtures.adoc) — fixture rewrite.
- `annotation-cheatsheet.md`, `creation-policy-decision.md`,
  `multi-entity-migration.md`, `polymorphism-migration.md`,
  `test-fixture-mapping.md` — load only when the target needs that case.

## Goal

The aggregate and its primary tests compile on AF5 with the same event-sourced
behavior. The entity is registered through Spring auto-discovery or
`EventSourcedEntityModule`, depending on pinned `wiring`.

## Inputs

- `target`: aggregate FQCN or file path.
- `wiring`: `spring-boot` or `framework-config`.
- `target_test`: optional; default is `<target>Test` if present.

## Preflight

1. Read `not-supported.md` and run its blocker checks.
2. If the class already has `@EventSourcedEntity` / `@EventSourced` and tests
   pass, emit `skipped`.
3. If the class lacks aggregate annotations or event-sourcing handlers, emit
   `rejected`.

## Procedure

Work top to bottom. Do not branch deeper than the named variant/path tables.

1. **Classify the aggregate.**

   | Signal | Variant | Extra reference |
   |---|---|---|
   | no members/subtypes | `simple` | this file |
   | `@AggregateMember` / child entities | `multi-entity` | `multi-entity-migration.md` |
   | inheritance / abstract aggregate root / concrete subtypes | `polymorphic` | `polymorphism-migration.md` |

2. **Rewrite class annotations and constructors.**
   - Remove AF4 `@Aggregate` / `@AggregateRoot`.
   - Add AF5 entity annotations from `annotation-cheatsheet.md`.
   - Ensure the AF5 entity creator shape exists.
   - Preserve field initialization and invariants.

3. **Rewrite command handlers.**
   - Keep command routing and validation behavior.
   - Replace `AggregateLifecycle.apply(...)` with `EventAppender` flow.
   - Resolve `@CreationPolicy` using `creation-policy-decision.md`; do not
     guess when test behavior differs.

4. **Rewrite event sourcing handlers.**
   - Keep state transitions exactly as before.
   - Update imports and annotation names.
   - Apply variant-specific member/subtype rules when classified above.

5. **Rewrite message annotations.**
   - Move `@TargetAggregateIdentifier`, routing keys, revisions, and event
     annotations according to the canonical message doc.
   - Do not rename message fields unless AF5 annotation names require it.

6. **Register the entity.**

   | `wiring` | Action |
   |---|---|
   | `spring-boot` | Prefer component/entity auto-discovery. Add Spring stereotype only when the project already uses it for Axon components. |
   | `framework-config` | Register `EventSourcedEntityModule.autodetected(...)` in the existing `EventSourcingConfigurer` chain. If the chain cannot be found, emit `needs-decision` with the exact class that still needs registration. |

7. **Migrate tests if present.**
   - Replace AF4 aggregate fixtures with `AxonTestFixture`.
   - Apply every relevant row in `test-fixture-mapping.md`.
   - Treat runtime NPEs in creation handlers as behavior mismatches, not
     fixture noise.

8. **Verify with `axon4to5-isolatedtest`.**
   - `target-name`: aggregate simple name.
   - `main-sources`: aggregate, commands, events, child entities, configurer
     registration if touched.
   - `test-sources`: primary aggregate tests.
   - `extra-deps`: AF5 modelling, eventsourcing, test modules as needed.

## End condition

- Target class has no AF4 aggregate annotations/imports.
- Command and event-sourcing handlers compile on AF5 APIs.
- Variant-specific child/subtype registrations compile.
- Primary tests pass or the recipe emits a classified `blocked`/`failed`.
- No unsupported AF4 surface was deleted without a TODO/blocker record.

## Output

```yaml
result: success | skipped | rejected | needs-decision | blocked | failed
target: <FQCN>
reason: <required except straightforward success>
decisions:
  variant: simple | multi-entity | polymorphic
  wiring: spring-boot | framework-config
  creation-policy: none | constructor | existing-instance | deferred
  blockers: []
caller-expects:
  commit: true | false
  next: proceed | ask-user | record-and-skip | halt | route-to:<recipe>
notes: []
```

## Subagent guidelines

- `parallelism`: per-item planning only.
- Subagents may inspect and return a plan. The migration runner applies edits,
  invokes isolated verification, updates state, and commits.
