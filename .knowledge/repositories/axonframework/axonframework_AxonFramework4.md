---
repo_type: axonframework
repo_name: AxonFramework4
submodule_path: .knowledge/repositories/axonframework/AxonFramework4
url: https://github.com/AxonIQ/AxonFramework.git
branch: axon-4.13.x
keywords:
  - axon 4
  - aggregate
  - saga
  - tracking event processor
  - migration source
  - spring boot 3
---

# AxonFramework4

## Purpose

Canonical source tree for the Axon Framework 4 maintenance line
(`axon-4.13.x`). This is the migration **source** that migration skills
read from when transforming Axon 4 applications to Axon 5 — aggregates,
sagas, tracking event processors, the legacy event store, and the
Spring Boot 3 autoconfigure stack all live here.

## Feature highlights

- **`@Aggregate` / `@AggregateRoot`** — the classic aggregate model that
  Axon 5 replaces with `EventSourcedEntity` and DCB.
- **Sagas** — the long-running process model under `modelling/`; Axon 5
  replaces these with repository-based state.
- **Tracking Event Processors** — under `messaging/`; the event
  processing primitives that Axon 5 reimagines.
- **Sequenced Dead-Letter Queue** — the original DLQ implementation
  (moved to [[axonframework_AxoniqFramework]] for Axon 5).
- **Disruptor command bus** — high-throughput command handling under
  `disruptor/`.
- **Legacy module** — `legacy/` carries shims for older APIs preserved
  across the 4.x line.

## Key paths

- `messaging/` — command/event/query buses and tracking processors.
- `modelling/` — aggregates, sagas, command/event handlers.
- `eventsourcing/` — Axon 4 event store and snapshotting.
- `spring/` and `spring-boot-autoconfigure/` — Spring Boot 3 wiring.
- `spring-boot-3-integrationtests/`, `spring-boot-4-integrationtests/` —
  cross-version compatibility tests.
- `migration/` — Axon 4 → 5 migration tooling shipped on the 4.x line.
- `axon-4-api-changes.md` — top-level change log of API evolution
  within the 4.x series; useful when pinning what was added when.

## Highlights

- Reference docs (in-repo): `docs/` — start with `docs/README.md` and
  `docs/_reference/` / `docs/old-reference-guide/`. Prefer these over
  the public site; this tree is the source of truth for the
  `axon-4.13.x` branch.
- Use this as the migration **source** when reading Axon 4 code that
  needs to be ported; the target is [[axonframework_AxonFramework5]].
- Sagas under `modelling/` rarely have a 1:1 mapping in Axon 5 — read
  the Axon 5 [[axonframework_AxonFramework5]] modelling docs before
  attempting a saga port.
- `axon-4-api-changes.md` is the quickest path to "what changed when"
  within the 4.x line — check it before assuming an API exists in
  `axon-4.13.x`.
