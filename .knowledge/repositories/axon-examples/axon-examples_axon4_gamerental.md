---
repo_type: axon-examples
repo_name: gamerental (axon4)
repo_path: .knowledge/repositories/axon-examples/axon4/gamerental
url: https://github.com/smcvb/gamerental.git
branch: main
commit: afdb1c7
variant: axon4
language: Java
build_tool: maven
keywords:
  - game rental
  - axon 4
  - aggregate
  - cqrs
  - event sourcing
  - spring boot
  - migration source
migrated_to:
  - axon-examples_axon5_gamerental.md
---

# gamerental — axon4

## Description

GameRental application in its original state using Axon Framework 4. A demo
rental-service domain (video game store) built with the classic Axon 4 stack:
aggregate roots, `@EventSourcingHandler`, query projections, and Spring Boot
autoconfiguration. The repository is structured as a sequence of `step#`
branches representing the lifecycle of the application during live-coding
talks; the `main` branch carries the integrated state.

This is the **starting point** for the migration to Axon Framework 5 — the
diff against `axon-examples_axon5_gamerental.md` IS the migration.

## Patterns / focus areas

- **Aggregate roots** under `io.axoniq.demo.gamerental.command` using
  `@AggregateIdentifier` and `@EventSourcingHandler` (Axon 4 style).
- **Core API** package (`coreapi`) holding commands, events, queries, and
  query responses as POJOs.
- **Query projections** under `query` package, using `@EventHandler` and
  `@QueryHandler` against a read model.
- **REST controllers** dispatching commands and queries via the Axon 4
  `CommandGateway` / `QueryGateway`.
- **Spring Boot autoconfiguration** wiring everything via
  `axon-spring-boot-starter`.

## Highlights

- Build & run: `./mvnw spring-boot:run`. Requires Axon Server (see
  `docker-compose.yaml` to start one locally).
- Start with `coreapi/` to understand the message contracts, then read
  `command/` for the `Game` and `Rental` aggregates — these are the most
  visible Axon 4 patterns that change in the Axon 5 migration.
- The repo uses numbered `step#` branches for live-coding presentations.
  `main` is the integrated end state and the correct migration source.
- Use this side to understand **what needs to change** when applying
  Axon 4 → 5 migration patterns. Pair it with the axon5 detail file for
  the target patterns.
