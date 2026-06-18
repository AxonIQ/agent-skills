---
repo_type: axon-examples
repo_name: heroes (axon4)
repo_path: .knowledge/repositories/axon-examples/axon4/heroes
url: https://github.com/MateuszNaKodach/HeroesOfDomainDrivenDesign.EventSourcing.Java.Axon.Spring.git
branch: master
commit: fbae554
variant: axon4
language: Java
build_tool: maven
architecture: Vertical Slice (Bounded Contexts)
keywords:
  - heroes of ddd
  - homm3
  - axon 4
  - axon 4.13
  - event sourcing
  - event modeling
  - ddd
  - vertical slice
  - bounded contexts
  - spring boot
  - mcp server
migrated_to:
  - axon-examples_axon5_heroes.md
---

# heroes — axon4

## Description

Educational DDD / Event Modeling reference application based on the
**Heroes of Might & Magic III** domain (HOMM3). Java 23 + Spring Boot +
Axon Framework 4.13.1 + Axon Server 2026.0.0. Demonstrates the full
software-development flow advocated by the dddheroes.com blog series:
domain knowledge crunching, Event Storming, Event Modeling, then
implementation with DDD building blocks and event sourcing.

This is the **axon4 source side** of an AF4 → AF5 migration pair; the
counterpart on the `af5-migrated` branch is the migrated target.

## Patterns / focus areas

- **Vertical slice / Bounded Contexts** — top-level packages per BC
  under `com.dddheroes.heroesofddd`: `resourcespool`, `creaturerecruitment`,
  `calendar`, `astrologers`, `armies`, `maintenance`, `shared`.
- Per-slice sub-packages: `write/`, `read/`, `events/`,
  `automation/`, `application/` — write/read separation by folder.
- Classic Axon 4 building blocks: `@AggregateIdentifier`,
  `@EventSourcingHandler`, `@CommandHandler`, `@EventHandler`,
  projection-style read models, automation slices for process logic.
- Spring Boot autoconfiguration for Axon 4; Axon Server as event store.
- MCP server exposed over SSE (`/sse`) so AI assistants can drive the
  domain directly — useful for demos and Claude-Code integration.
- Includes a `docker-compose.yaml` to bring up Axon Server locally.

## Highlights

- Java 23 required; build & run: `./mvnw install -DskipTests`,
  `docker compose up`, then `./mvnw spring-boot:run` or `./mvnw test`.
- Best entry point: `com.dddheroes.heroesofddd.creaturerecruitment` —
  the most complete bounded context with write/read/automation/events
  slices — and its aggregate(s) under `creaturerecruitment/write/`.
- REST + Swagger at `http://localhost:3773/swagger-ui/index.html`;
  MCP SSE endpoint at `http://localhost:3773/sse`.
- Bounded-context boundaries are the migration unit — compare each BC
  package between the axon4 and axon5 sides rather than the whole tree.
- Companion blog series: <https://dddheroes.com/>.
