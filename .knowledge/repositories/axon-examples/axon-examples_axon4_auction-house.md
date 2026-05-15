---
repo_type: axon-examples
repo_name: auction-house (axon4)
submodule_path: .knowledge/repositories/axon-examples/axon4/auction-house
url: https://github.com/AxonIQ/auction-house-axon-observability-demo.git
branch: migration-ready/af5
variant: axon4
language: Kotlin
build_tool: maven
architecture: Microservices (multi-module Maven)
keywords:
  - auction house
  - axon 4
  - observability
  - opentelemetry
  - prometheus
  - grafana
  - inspector axon
  - microservices
  - multi-module
  - kotlin
  - maven
  - migration-ready
---

# auction-house — axon4

## Description

Full-fledged microservices demo using Axon Framework 4 and Axon Server, monitored end-to-end with OpenTelemetry,
Prometheus, Grafana, Jaeger, OpenSearch and Inspector Axon. The `migration-ready/af5` branch is the Axon 4 source
state prepared for an Axon 4 → Axon 5 migration: dependencies and code shapes have been pre-aligned so the diff
against the future axon5 side is the migration itself.

**Status:** Awaiting Axon 5 migration. The counterpart `axon-examples/axon5/auction-house` does not exist yet.

## Patterns / focus areas

- **Multi-module Maven layout** — parent POM aggregates `core`, `services`, `frontend`, `frontend-landing`.
- **Services tier** (`services/`) is itself an aggregator with sub-modules:
  - `service-interfaces` — shared command/event/query API.
  - `service-auctions` — auction lifecycle commands and event-sourced model.
  - `service-auction-query` — projections / query handlers.
  - `service-auction-object-registry` — catalog of biddable items.
  - `service-participants` — simulated bidders (scalable, autonomous).
  - `service-allinclusive` — single-process all-in-one bundle used for the "light" stack.
- **Spring Boot 3.1.0** on Java 17 with **Kotlin 2.2.0** — close to but not at Spring Boot 4.
- **Axon Framework 4.7.4** with Axon Server clustering and messaging.
- **Observability stack baked in**: OpenTelemetry tracing → Jaeger query + OpenSearch; Prometheus scraping +
  Grafana dashboards; Inspector Axon for Axon-specific telemetry.
- **Chaos hook** via Axon FireStarter for fault-injection demos.
- Companion infra (`infrastructure/full`, `infrastructure/light`) ships docker-compose stacks; the "full" stack
  includes a 3-node Axon Server EE cluster and requires an `axoniq.license` file.

## Highlights

- This is a **Kotlin + Maven + multi-module** project — different shape from the gamerental (Java/Maven, single
  module) and bike-rental-extended (Java/Maven, multi-module) examples. Reach for it when a migration target
  has the same Kotlin/Maven/multi-module profile.
- Branch `migration-ready/af5` (commit `ad23c30`, "prepare for af5 migration") is the **pre-migration** state.
  When the axon5 counterpart is added, the diff between these two refs IS the migration artifact.
- Start reading at `services/service-auctions` for the event-sourced model, then `service-auction-query` for
  projections — together they form the canonical CQRS slice in this demo.
- Build with `./mvnw -DskipTests package`. Run via `docker compose -f infrastructure/light/docker-compose.yaml up -d`
  for the no-license path; the full stack needs an Axon Server EE license.
- Observability wiring lives in module-level `application.yaml` files and the Spring Boot starters — useful
  reference for any migration that needs to preserve OpenTelemetry/Inspector instrumentation across AF4 → AF5.
- Frontend modules (`frontend`, `frontend-landing`) are out of scope for Axon migration work but ship in the
  same repo; ignore them unless touching the demo UX.
