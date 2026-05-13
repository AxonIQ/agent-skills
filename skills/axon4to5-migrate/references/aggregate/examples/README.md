# Aggregate Patterns

Use these as recognition patterns, not copy/paste examples.

| Case | AF4 signal | AF5 direction | Extra reference |
|---|---|---|---|
| simple aggregate | `@Aggregate`, constructor command handler, `apply(...)` | `@EventSourced`, entity creator, `EventAppender` | `../aggregate.md` |
| creation policy | `@CreationPolicy` | split create/update behavior by tests | `../creation-policy-decision.md` |
| multi-entity | `@AggregateMember` collection | `@EntityMember` plus explicit routing/tagging | `../multi-entity-migration.md` |
| polymorphic | abstract root/subtypes | `@EventSourcedEntity(concreteTypes=...)` or documented declarative registration | `../polymorphism-migration.md` |
| fixture | `AggregateTestFixture` | `AxonTestFixture` | `../test-fixture-mapping.md` |

Prefer the canonical docs under `docs/paths/` for complete code shapes.
