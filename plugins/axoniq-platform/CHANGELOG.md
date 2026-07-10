# Changelog

All notable changes to the **axoniq-platform** plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- `mark_component_implemented` now takes the **version** you implemented and is rejected if it isn't the
  latest (the spec was edited mid-implementation). On rejection, re-fetch the component, reconcile your
  code with the new spec, and mark again at the new version. Drift detection gains a `PENDING_CHANGES`
  row (implemented version is behind the latest spec).
- Workflow implementation: terminal status is now explicit. A null `onFailure`/`onTimeout` is **not**
  terminal — the step failure propagates and the engine retries it (matching the Axon workflow
  lifecycle). A step-level timeout no longer maps to the workflow `TIMED_OUT` state. FAILED / CANCELLED
  are reached only by routing to a `fail` (`ctx.fail`) / `cancel` (`ctx.cancel`) terminal step. Removed
  the per-step `onCancel` pointer (cancellation is external + terminal, not a per-step branch).
- Workflow DSL now has eight step kinds: `wait`, `dispatch`, `sleep`, `multi`, `when`, `choice`, `fail`,
  `cancel`. `when` is the structured switch on a trigger property (the old `choice`); the new `choice`
  is a free-form ordered `if/else` whose conditions the local agent implements. `sleep` paces a loop.
- Workflows may now contain **back-edge loops** for genuine *business* repetition (polling, decision
  rounds) — never for technical retry or compensation. Codegen is hybrid: straight-line for acyclic
  graphs, a step-dispatch `while` loop when a back-edge is present.

## [0.1.0]

### Added

- Initial release: AxonIQ Platform spec→code implementation skill.
