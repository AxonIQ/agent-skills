---
repo_type: axonframework
repo_name: AxonFramework5
submodule_path: .knowledge/repositories/axonframework/AxonFramework5
url: https://github.com/AxonIQ/AxonFramework.git
branch: feat/migration-skills
keywords:
  - axon 5
  - dynamic consistency boundary
  - event sourced entity
  - reactive
  - migration target
  - axon test fixture
---

# AxonFramework5

## Purpose

Canonical source tree for Axon Framework 5. This is the reference for the
new APIs that migration skills target — command/event handling, the new
event store, the Dynamic Consistency Boundary (DCB) modelling primitives
that replace Axon 4 aggregates, and the reactive return-type contract.

## Feature highlights

- **Dynamic Consistency Boundary (DCB)** — replaces the aggregate root
  pattern as the unit of consistency; lives under `modelling/`.
- **`EventSourcedEntity`** — Axon 5's state-based entity model, the
  successor to `@Aggregate`.
- **Reactive command/event handlers** — `CompletableFuture`/`Mono` are
  first-class return types.
- **New event store SPI** — see `eventsourcing/` for storage engine
  contracts.
- **AxonTestFixture** — Spring-Boot-friendly test harness under `test/`.
- **Migration helpers** — `migration/` contains tooling that bridges
  Axon 4 and Axon 5 concepts.

## Key paths

- `messaging/` — message buses and gateway interfaces.
- `modelling/` — DCB, `EventSourcedEntity`, state-based modelling.
- `eventsourcing/` — event store and snapshotting SPI.
- `test/` — `AxonTestFixture` and assertion DSL.
- `migration/` — utilities for moving Axon 4 code to Axon 5.
- `examples/` — runnable samples for the new APIs.
- `axon-5/` — top-level integration aggregator for the v5 modules.

## Highlights

- Official docs: <https://docs.axoniq.io/axon-framework-reference/5.0/>
- Start with `modelling/` when reasoning about state — DCB is the new
  mental model and most migration confusion lives there.
- Reactive return types are illustrated end-to-end in the Spring Boot
  autoconfigure integration tests.
- For commercial features missing here (DLQ, snapshots for
  `EventSourcedEntity`, AxonServer connector, distributed buses,
  PostgreSQL event store) see [[axonframework_AxoniqFramework]].
- Source pair for migration diffs against [[axonframework_AxonFramework4]].
