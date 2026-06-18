---
repo_type: axon-examples
repo_name: bike-rental-extended (axon4)
repo_path: .knowledge/repositories/axon-examples/axon4/bike-rental-extended
url: https://github.com/MateuszNaKodach/bike-rental-extended.git
branch: af4
commit: eaa9ebe
variant: axon4
language: Java
build_tool: maven
architecture: Multi-module (microservices)
keywords:
  - bike rental
  - axon 4
  - saga
  - payment saga
  - deadlines
  - cqrs
  - event sourcing
  - multi-module maven
  - migration source
migrated_to:
  - axon-examples_axon5_bike-rental-extended.md
---

# bike-rental-extended — axon4

## Description

BikeRental application in its **original Axon Framework 4 state**, extended
into a multi-module Maven project (`core-api`, `payment`, `rental`,
`frontend`, `microservices`). Showcases the **classic Axon 4 Saga pattern**
for distributed transactions across the rental and payment bounded contexts,
including deadline handling.

This is the source for an alternative Axon 5 migration that deliberately
avoids the Workflow extension — see
`axon-examples_axon5_bike-rental-extended.md` for the target patterns and
trade-offs.

## Patterns / focus areas

- **`@Saga`-based PaymentSaga** at
  `rental/src/main/java/io/axoniq/demo/bikerental/rental/paymentsaga/PaymentSaga.java`
  — coordinates rental → payment → completion using `@SagaEventHandler` and
  `@DeadlineHandler`. This is the most important file to read first.
- **Aggregate roots** — `Bike` (in `rental/`) and `Payment` (in `payment/`),
  Axon-4 style with `@AggregateIdentifier` and `@EventSourcingHandler`.
- **Snapshots** — `BikeSnapshotDefinition.java` demonstrates Axon 4
  snapshotting.
- **Query projections** — `BikeStatusProjection` and
  `PaymentStatusProjection` writing to JPA repositories.
- **Deadlines** — `PaymentSaga` uses two `@DeadlineHandler`s:
  `cancelPayment` (30s timeout that aborts the rental) and `retryPayment`
  (5s retry on failure), plus a `DeadlineManager` bean in
  `RentalApplication.java`. **On the af5 side these are REMOVED, not
  replaced** — without the Workflow extension Axon 5 has no standard
  deadline mechanism, so the cancel-on-timeout and retry-on-failure
  behaviors are dropped in the migration.

## Highlights

- Build: `./mvnw package`. Run modules independently (`payment`, `rental`,
  `frontend`) or use `create-microservices.sh`. Requires Axon Server (see
  README for setup).
- Start with `rental/.../paymentsaga/PaymentSaga.java` — the saga IS the
  reason this example exists. Compare it side-by-side against the axon5
  variant to see the repository-based state pattern.
- The `core-api` module holds shared messages and is unaffected by the
  migration in any meaningful way — focus migration attention on `rental/`
  and `payment/`.
- This side intentionally uses `@DeadlineHandler` so the migration
  limitation on the Axon 5 side is observable, not hypothetical.
