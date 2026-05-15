---
repo_type: axon-examples
repo_name: cinema (axon4)
submodule_path: .knowledge/repositories/axon-examples/axon4/cinema
url: https://github.com/MateuszNaKodach/Cinema.EventSourcing.VerticalSlice.Kotlin.Axon4.Spring.git
branch: main
commit: af9a841
variant: axon4
language: Kotlin
build_tool: gradle
architecture: Vertical Slice
keywords:
  - cinema
  - axon 4
  - kotlin
  - gradle
  - vertical slice
  - event sourcing
  - event store api
  - no aggregates
  - event modeling
  - ddd
migrated_to: []
---

# cinema — axon4

## Description

Kotlin/Gradle Axon 4 demo of a Cinema domain built with DDD, Event Storming,
Event Modeling, and Event Sourcing. Vertical-slice modules: `adminnotifications`,
`dayschedule`, `issues`, `payments`, `reservations`, `seatsblocking`. Spring
Boot 3.5.8, Kotlin 2.3.0, Java 21, Axon 4.12.1, PostgreSQL event store (or
Axon Server).

**Status:** Awaiting Axon 5 migration. No counterpart yet.

## Patterns / focus areas

- **EXOTIC — no aggregates.** This example does **not** use
  `@AggregateIdentifier` / `@Aggregate` / `AggregateLifecycle`. Command-side
  state is sourced and appended directly through the `EventStore` interface
  via a custom Kotlin SDK layer in
  `src/main/kotlin/com/dddheroes/sdk/application/EventStoreExtensions.kt`
  (`sourceSingle`, `sourceMulti`, `append`, `inSingleStreamTransaction`,
  `inMultiStreamTransaction`).
- Vertical-slice per use case under
  `src/main/kotlin/com/dddheroes/cinema/modules/<slice>/write/<usecase>/`.
- Event sourcing on event streams identified by `EventStreamId`, not on
  Axon aggregate roots.
- Multi-stream transactions for use cases that span more than one event
  stream (e.g. `seatsblocking` placing across multiple seats).
- AxonIQ Console + Spring AI MCP server integration (`SpringApplication`
  exposes domain via MCP at `/sse`).
- PostgreSQL `domain_event_entry` table with LOB payload/meta columns —
  README documents the SQL access patterns.

## Migration relevance / scope caveat

- **Likely out of scope for most aggregate-centric migration skills.** The
  classical Axon 4 → 5 paths (state-based aggregate → `@EventSourcedEntity`,
  saga → repository-based state, etc.) do not apply directly here because
  there is no aggregate model to translate. A migration skill should either
  detect the pattern and skip, or follow a different track that maps the
  custom `EventStore` SDK onto Axon 5 sourcing/appending primitives.
- **Gradle (Kotlin DSL) build.** This is the first axon-examples entry that
  is not Maven (`build.gradle.kts`, `settings.gradle.kts`, Gradle wrapper).
  Any tool the migration skills rely on must be validated against Gradle —
  in particular **OpenRewrite** (we currently invoke it through Maven; the
  Gradle `rewrite-gradle-plugin` is a separate pathway and needs explicit
  verification before assuming parity).

## Highlights

- Start reading at `src/main/kotlin/com/dddheroes/sdk/application/EventStoreExtensions.kt`
  — it's the heart of the "no-aggregate" pattern and the thing every slice
  composes against.
- For a concrete slice that uses the SDK, see
  `src/main/kotlin/com/dddheroes/cinema/modules/reservations/write/cancelreservation/`
  and `.../seatsblocking/write/blockseats/` (multi-stream transaction).
- Build & run: `./gradlew build -x test` then
  `docker compose -f docker-compose.axon.yaml up` and `./gradlew bootRun`.
  Tests: `./gradlew test` (Testcontainers + PostgreSQL).
- Java toolchain pinned to **21**, Axon `4.12.1`, Kotlin `2.3.0`, Spring
  Boot `3.5.8` (build.gradle.kts:13-29).
- Domain context lives in `BUSINESS_DOMAIN.md` and Miro Event Model linked
  from README.md.
- Watch out: there is a `CLAUDE.md` at the repo root — the
  `block-knowledge-repositories-claude-read.sh` hook will block reads of it
  from `.knowledge/repositories/...`; consult it only by opening the file
  from the live working copy if needed, not via this submodule path.
