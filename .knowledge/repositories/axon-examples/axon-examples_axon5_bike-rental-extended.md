---
repo_type: axon-examples
repo_name: bike-rental-extended (axon5)
submodule_path: .knowledge/repositories/axon-examples/axon5/bike-rental-extended
url: https://github.com/MateuszNaKodach/bike-rental-extended.git
branch: af5
commit: 15af118
variant: axon5
language: Java
build_tool: maven
architecture: Multi-module (microservices)
keywords:
  - bike rental
  - axon 5
  - saga
  - repository-based state
  - payment saga
  - no workflow extension
  - deadline limitation
  - migration target
migrated_from: axon-examples_axon4_bike-rental-extended.md
---

# bike-rental-extended — axon5

## Description

BikeRental migrated to **Axon Framework 5 without the Workflow extension**.
This is an **alternative migration strategy** to the (planned) Workflow
extension approach: the legacy `@Saga`-based `PaymentSaga` is replaced by a
**repository-based state management pattern**. Same multi-module layout as
the axon4 source — `core-api`, `payment`, `rental`, `frontend`,
`microservices` — with only the rental/payment modules meaningfully
changed.

The diff against the `af4` branch IS the migration. Treat this pair as the
**most concrete reference for "Axon 5 migration without Workflow"** in this
knowledge base.

## Patterns / focus areas

- **Repository-based PaymentSaga** in
  `rental/src/main/java/io/axoniq/demo/bikerental/rental/paymentsaga/`:
  - `PaymentState.java` — saga state as a regular persistent entity.
  - `PaymentStateRepository.java` — Spring Data repository owning the state.
  - `PaymentSaga.java` — event handler that loads state, mutates, saves.
  - Replaces the Axon-4 `@Saga` / `@SagaEventHandler` annotation pair
    entirely.
- **Axon 5 command handling** — see `PaymentCommandHandler.java` in the
  `payment/` module (new file vs. axon4 side).
- **Aggregates** — `Bike` and `Payment` reshaped for the Axon 5 modelling
  API.
- **Queries** — `GetStatusQuery.java` (new file in `payment/`) explicitly
  defines the query contract.

## Migration notes

- **PaymentSaga migration strategy.** Migrated using a **repository-based
  state management pattern** instead of the Workflow extension (which was
  not yet released at the time). This is one of two viable Axon 5 saga
  strategies — Workflow extension OR repository-based — and they have
  different trade-offs. Migration skills should ask the user which they
  prefer before producing code, and surface this repo as the reference
  for the repository-based path.
- **`@DeadlineHandler` was REMOVED, not replaced.** The axon4 `PaymentSaga`
  uses two deadlines — `cancelPayment` (30s timeout that aborts the
  rental) and `retryPayment` (5s retry on failure) — plus a
  `DeadlineManager` bean in `RentalApplication.java`. **All of this is
  gone on the af5 side**: no `@DeadlineHandler`, no `DeadlineManager`, no
  `scheduleDeadline` calls. The cancel-on-timeout and retry-on-failure
  behaviors are simply dropped. Without the Workflow extension there is
  **no standard Axon 5 mechanism for saga timeouts/deadlines**; reinstating
  this behavior requires a custom solution (scheduler + event, external
  job runner, etc.). Flag this whenever a migration target uses
  `@DeadlineHandler` — the user must explicitly accept the dropped
  behavior or build the replacement.
- **Multi-module impact is local.** Only `rental/` and `payment/` change
  in any meaningful way; `core-api/`, `frontend/`, and `microservices/`
  are essentially untouched. Useful signal when scoping migration PRs on
  similar codebases.
- **No Workflow extension dependency.** `pom.xml` deliberately omits any
  Workflow extension coordinate; if generating a Workflow-based migration
  you should NOT use this repo as a Maven dependency reference.

## Highlights

- Build: `./mvnw package`. Run as in the axon4 side
  (`create-microservices.sh` or independent modules).
- **Start here**: read
  `rental/.../paymentsaga/PaymentState.java` →
  `PaymentStateRepository.java` → `PaymentSaga.java` in that order. The
  repository-based pattern only makes sense when you see the state and
  repository first.
- Diff the `paymentsaga/` directory between this side and the axon4 side
  to see the strategy change in isolation — that diff is the core
  migration artifact this repo is here to document.
- See `axon-examples/INDEX.md` for the exact `git diff` command pinning
  branches `af4` and `af5`.
- This is the **concrete reference for "migration without Workflow
  extension"** — point migration skills here when the user opts out of
  the Workflow extension, and point them at the gamerental pair (or a
  future Workflow-based example) when they opt in.
