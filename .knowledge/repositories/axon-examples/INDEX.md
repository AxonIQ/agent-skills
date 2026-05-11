# Migrated Example Applications

**For AI Agents:** Use this index to quickly identify relevant repositories for your task. Scan the **Keywords** field to match your task requirements, then read the linked markdown file for comprehensive details about that repository.

## gamerental
Rental-service demo (video game store) showing a complete Axon 4 → Axon 5.1.0 migration of a CQRS / event-sourced Spring Boot application.
**Keywords:** game rental, axon 4, axon 5, axon 5.1.0, cqrs, event sourcing, spring boot 4, migration

- **axon4:** [details](axon-examples_axon4_gamerental.md) — branch `main` · Java · Maven
- **axon5:** [details](axon-examples_axon5_gamerental.md) — branch `af5/5.1.0-demo-day` · Java · Maven

### Migration Diff (gamerental)

**The difference between `axon4/gamerental@main` and `axon5/gamerental@af5/5.1.0-demo-day` IS the migration itself.**

```bash
git -C .knowledge/repositories/axon-examples/axon4/gamerental log -1 --oneline
git -C .knowledge/repositories/axon-examples/axon5/gamerental log -1 --oneline
git diff afdb1c7 dbb571f
```

## bike-rental-extended
Multi-module bike-rental demo whose Axon 5 side migrates the legacy `@Saga` PaymentSaga using a **repository-based state pattern** instead of the Workflow extension — concrete reference for "migration without Workflow".
**Keywords:** bike rental, axon 4, axon 5, saga, payment saga, repository-based state, no workflow extension, deadline limitation, migration

- **axon4:** [details](axon-examples_axon4_bike-rental-extended.md) — branch `af4` · Java · Maven
- **axon5:** [details](axon-examples_axon5_bike-rental-extended.md) — branch `af5` · Java · Maven

### Migration Diff (bike-rental-extended)

**The difference between `axon4/bike-rental-extended@af4` and `axon5/bike-rental-extended@af5` IS the migration itself.**

```bash
git -C .knowledge/repositories/axon-examples/axon4/bike-rental-extended log -1 --oneline
git -C .knowledge/repositories/axon-examples/axon5/bike-rental-extended log -1 --oneline
git diff eaa9ebe 15af118
```
