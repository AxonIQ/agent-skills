# Changelog

All notable changes to the **axoniq-platform** plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Workflow implementation targets **axoniq-workflow 0.2.0** (`io.axoniq.framework:axoniq-workflow-*`, Axon
  Framework 5.2+, verified on 5.3.2). The old `io.axoniq.framework.workflow:axon-workflow-*` 0.1.0 coordinates and the
  "pin the BOM to 5.1.2" instruction are gone: 0.1.0 does not start on AF 5.2+ (`NoSuchFieldError:
  GenericEventMessage.clock`). The skill now uses the 0.2.0 API: `startOnEventClass` / `startOnEventName` instead of
  `startOnEvent`, explicit `workflowNamespace` / `workflowName`, `@Workflow*Handler` lifecycle handlers instead of
  `@On*`, `Associations.associate` + `EventAssociationsUtils`, typed `awaitEvent` / `waitForEvent` with a step
  customizer, `StepTimedOutException`, command dispatch through `CommandDispatcher.forContext(pc)`, and the BDD
  `WorkflowTestFixture` instead of `AbstractDeclarativeTestBase`.
- Command handlers inject state as `Optional<State>` (or a nullable Kotlin type): on AF 5.3 a command for an entity
  without events no longer gets a freshly created state, it gets no entity.
- QUERY components get unit tests by default (projection handlers + query handlers, no Spring context).
- New rule in SKILL.md: when applying a spec delta to an already implemented component, report suspected bugs outside
  the delta instead of fixing them silently. The components table's new **Version** column
  (`v2 (v1 implemented)`) is what tells the two situations apart.
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
