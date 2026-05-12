---
repo_type: axon-examples
repo_name: heroes (axon5)
submodule_path: .knowledge/repositories/axon-examples/axon5/heroes
url: https://github.com/MateuszNaKodach/HeroesOfDomainDrivenDesign.EventSourcing.Java.Axon.Spring.git
branch: af5-migrated
commit: d86f99c
variant: axon5
language: Java
build_tool: maven
architecture: Vertical Slice (Bounded Contexts)
keywords:
  - heroes of ddd
  - homm3
  - axon 5
  - axon 5 migration
  - event sourcing
  - event modeling
  - ddd
  - vertical slice
  - bounded contexts
  - spring boot
  - mcp server
  - aggregate event publisher
migrated_from: axon-examples_axon4_heroes.md
---

# heroes — axon5

## Description

`heroes` migrated from Axon Framework 4.13.1 to Axon Framework 5 on the
`af5-migrated` branch. Same HOMM3 educational DDD domain, same vertical
slice / bounded-context layout, same Java 23 + Spring Boot + Maven
toolchain — the difference IS the migration. Each bounded context
(`resourcespool`, `creaturerecruitment`, `calendar`, `astrologers`,
`armies`, `maintenance`) is migrated independently, so this repo doubles
as a per-BC migration cookbook.

## Patterns / focus areas

- Same vertical-slice / bounded-context package layout as the axon4
  side — package paths are stable, so a directory-level diff cleanly
  surfaces every migration touch point.
- Axon 5 event-sourced modeling per BC (write side reworked from AF4
  aggregates).
- `AggregateEventPublisher` used to publish multiple events from a
  single command path (see the latest fix on
  `creaturerecruitment/automation` — astrologer multi-publish).
- MCP server (SSE) preserved end-to-end.

## Migration notes

- **Per-bounded-context migration.** Use the BC package as the diff
  unit. Migration skills should iterate BC by BC rather than touching
  the whole module tree at once.
- **AggregateEventPublisher multi-publish** — the latest fix on this
  branch (`d86f99c`) was specifically about emitting multiple events
  from a single aggregate command in the migrated model; flag this
  pattern when migration targets fan out events from one handler.
- **Astrologer automation tests** were stabilised on this branch — the
  automation slice under `creaturerecruitment/automation/` is a good
  example of a migrated process / reactor.
- **Spring Modulith dependencies were removed** in the axon4 baseline
  just before migration (commit `fbae554`); the af5 branch starts from
  that clean state, so don't expect Modulith APIs on either side.
- **Tooling parity preserved** — Java 23, Maven wrapper, Docker
  Compose, Swagger, and MCP-SSE endpoints all behave the same after
  the migration; runtime contract is unchanged.

## Highlights

- Java 23 required; build & run identical to axon4: `./mvnw install
  -DskipTests`, `docker compose up`, then `./mvnw spring-boot:run` or
  `./mvnw test`.
- Best entry point: `com.dddheroes.heroesofddd.creaturerecruitment` —
  the migrated write/read/automation slices map 1:1 against the axon4
  layout, so it's the cleanest before/after comparison.
- The diff against `axon-examples_axon4_heroes.md` is the migration
  artifact — see the Migration Diff callout in
  `axon-examples/INDEX.md`.
- Don't chase the whole branch in one go — pick a single bounded
  context (e.g. `resourcespool`) and migrate it end-to-end before
  moving to the next.
