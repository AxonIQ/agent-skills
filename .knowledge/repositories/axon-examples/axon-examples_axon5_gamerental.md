---
repo_type: axon-examples
repo_name: gamerental (axon5)
submodule_path: .knowledge/repositories/axon-examples/axon5/gamerental
url: https://github.com/smcvb/gamerental.git
branch: af5/5.1.0-demo-day
commit: dbb571f
variant: axon5
language: Java
build_tool: maven
keywords:
  - game rental
  - axon 5
  - axon 5.1.0
  - spring boot 4
  - migration target
  - dcb
  - reactive handlers
migrated_from: axon-examples_axon4_gamerental.md
---

# gamerental — axon5

## Description

Fully migrated GameRental application running on **Axon Framework 5.1.0**.
Same business behavior as the axon4 source — the differences ARE the
migration. This is a complete, working example demonstrating modern Axon 5
patterns layered on Spring Boot 4.

## Patterns / focus areas

- **Axon 5 aggregate / state model** in `command/` — structured for the
  Framework 5 modelling API rather than the legacy `@AggregateIdentifier` /
  `@EventSourcingHandler` pair.
- **Event handling patterns** updated for Axon 5 in `query/` projections.
- **Query model implementation** using the Axon 5 query handler contract.
- **Spring Boot 4 integration** — autoconfiguration class locations and
  property keys updated for the new starter (`axon-spring-boot-starter` on
  5.1.0 alongside `axoniq-framework` autoconfig).
- **AxonIQ Console / Cloud** wiring preserved through the migration; see
  `application.properties` for the relevant keys.

## Migration notes

- The diff between `main` (axon4) and `af5/5.1.0-demo-day` (axon5) IS the
  migration. Treat this pair as a reference for what a complete Axon 4 → 5
  conversion of a CQRS / event-sourced Spring Boot app looks like.
- Migrated against **Axon Framework 5.1.0** and the matching AxonIQ
  Framework release — see the head commit `Alignment with 5.1.0 of AF and
  AAF`. If pointing migration skills at this repo, surface the 5.1.0
  pinning so callers don't conflate it with an older `5.0.x` example.
- Spring Boot 4 brings autoconfig package reorganizations — refer to
  context7 for current Spring Boot 4 docs when comparing against older
  Axon 5 examples on Boot 3.x.
- The application is intentionally a small demo (single Maven module);
  larger production-style examples (multi-module, hexagonal) live
  elsewhere. Do not over-generalize the structure of this repo to apply
  to bigger codebases.

## Highlights

- Build & run: `./mvnw spring-boot:run`. `docker-compose.yaml` boots a
  local Axon Server compatible with 5.1.0.
- Start with `coreapi/` to see the (largely-unchanged) message contracts,
  then read `command/` to see the Axon 5 modelling differences vs. the
  axon4 source.
- The Migration Diff callout in `axon-examples/INDEX.md` has the exact
  `git diff` recipe pairing this with the axon4 source.
- This is the **target state** for the GameRental migration — use it to
  see how Axon 4 patterns land on Axon 5.1.0 + Spring Boot 4.
