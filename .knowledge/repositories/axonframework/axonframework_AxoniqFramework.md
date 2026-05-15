---
repo_type: axonframework
repo_name: AxoniqFramework
submodule_path: .knowledge/repositories/axonframework/AxoniqFramework
url: https://github.com/AxonIQ/axoniq-framework.git
branch: main
keywords:
  - commercial axon
  - dead-letter queue
  - snapshots
  - axon server connector
  - distributed buses
  - postgresql event store
  - spring boot 4
---

# AxoniqFramework

## Purpose

Commercial companion to Axon Framework 5. Provides advanced features that
were part of the basic Axon Framework 4 distribution but are not included in
the open-source Axon Framework 5 core — most importantly sequenced
dead-letter queues, snapshots for `EventSourcedEntity`, AxonServer
integration, distributed command/query/event buses, and a PostgreSQL event
store. Reference this repo when migrating an Axon 4 application that
relies on any of those features and the OSS Axon 5 core alone is not
enough.

## Feature highlights

- **Sequenced Dead-Letter Queue** — handles failed event processing while
  preserving sequencing guarantees within a processing group.
- **Snapshots for `EventSourcedEntity`** — optimizes aggregate state
  reconstruction in Axon 5's new entity model.
- **AxonServer integration** — connector plus the managed event store for
  enterprise deployments.
- **Distributed command/query/event buses** — Spring Boot 4 support for
  multi-node deployments.
- **PostgreSQL extension** — alternative event store implementation for
  teams that do not run AxonServer.

## Key paths

- `messaging/axoniq-dead-letter/` — sequenced DLQ implementation.
- `messaging/axoniq-distributed-messaging/` — distributed buses for
  command, query, and event messaging across nodes.
- `messaging/axoniq-event-streaming/` — streaming primitives that back
  AxonServer and PostgreSQL event store integrations.
- `connector/axon-server-connector/` — AxonServer client connector.
- `connector/axoniq-postgresql/` — PostgreSQL event store extension.
- `examples/` — runnable sample projects exercising the commercial
  features end-to-end.
- `integrationtests/` — cross-module integration tests; useful as
  executable documentation of how the pieces compose.

## Highlights

- Use this as the migration target when an Axon 4 application depends on
  DLQ, snapshots, distributed buses, AxonServer, or a JDBC/PostgreSQL
  event store — the OSS [[axonframework_AxonFramework5]] core does not
  cover those features.
- Start with `examples/` to see end-to-end wiring before diving into the
  individual `messaging/` and `connector/` modules.
- Spring Boot 4 is the supported baseline for distributed messaging —
  consult context7 for Spring Boot 4 changes when wiring this in (per
  the user's standing rule on Spring Boot 4 docs).
