---
repo_type: axonframework
repo_name: extension-workflow
submodule_path: .knowledge/repositories/axonframework/extension-workflow
url: https://github.com/AxonIQ/extension-workflow.git
branch: axoniq-workflow-0.1.x
keywords:
  - workflow
  - durable execution
  - saga replacement
  - axon 5 extension
  - workflow dsl
  - process management
  - axoniq workflow
---

# extension-workflow

## Purpose

AxonIQ Workflow extension for Axon Framework 5 — a durable-execution engine that
provides the modern replacement for the Saga pattern, which is no longer part of
core Axon Framework 5. Use this as the reference when migrating Axon 4 sagas to
a Framework 5 workflow.

## Feature highlights

- **Workflow DSL** — imperative `workflow { … }` builder for long-running
  business processes (credit checks, order fulfillment, onboarding) with
  `execute`, `waitForEvent`, timeouts, and structured success/failure returns.
- **Durable execution runtime** — event-sourced state, crash-safe resume, and
  concurrent process handling built on Axon Framework 5 primitives.
- **Spring Boot autoconfiguration** — drop-in starter that wires the runtime
  into a Framework 5 app.
- **Test fixtures and simulator** — first-class test harness plus a simulator
  module for exercising long-running flows deterministically.
- **Example apps** — `examples/bike-rental` and `examples/simple` show
  end-to-end usage of the DSL against the runtime.

## Key paths

- `dsl/` — Workflow DSL: imperative builder API and the surface a Saga
  migration targets.
- `runtime/` — Durable workflow engine; event-sourced state and resume logic.
- `spring-boot/` — Spring Boot starter / autoconfigure module.
- `test/` — Test fixtures and assertion DSL for workflows.
- `simulator/` — Deterministic simulator for long-running workflow flows.
- `examples/bike-rental`, `examples/simple` — runnable example workflows.
- `docs/` — In-repo Antora docs (see Highlights for entry points).

## Highlights

- Reference docs (in-repo): `docs/getting-started/` and `docs/reference/` —
  start here. Prefer these over the public site; this branch's `docs/`
  tree is the source of truth for the checked-out version.
- Use-case walkthroughs live in `docs/_use-cases/`; recurring patterns are
  collected in `docs/_playbook/` — useful when mapping a specific Axon 4
  saga to its workflow equivalent.
- For Saga → Workflow migration, start by reading `dsl/` (the API surface
  a migrated saga lands on) and then `examples/simple` for a minimal
  end-to-end mapping.
- Class-diagram and engine overview live at the top of `docs/`
  (`workflow-class-diagram.drawio.png`, `task-queue-based-engine.png`) —
  good orientation before diving into `runtime/`.
