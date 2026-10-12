---
id: saga
title: Legacy saga
description: Adapt an existing Axon Framework 4 saga and its fixture tests to Axoniq Framework 5 legacy APIs while preserving state, associations, processor identity, and behavior.
order: 7
argument-hint: $SOURCE
---

# Legacy saga

Adapt an existing saga to `axoniq-legacy`. Keep its serialized state and association model so running instances can continue. Saga-to-workflow redesign belongs to the separate [saga-to-workflow skill](../../../../saga-to-workflow/SKILL.md).

This recipe changes source and wiring only. It does not deploy, convert stored data, upgrade contexts to DCB, stop new saga starts, or drain running instances.

## Source

`$SOURCE`: FQN, file path, or simple name of a Java or Kotlin class using `@Saga`, `@SagaEventHandler`, `@StartSaga`, or `@EndSaga`.

## Scope

- The selected saga, its message types and collaborators needed to compile it.
- Its existing `SagaTestFixture` tests and their supporting types.
- Dependency declarations and saga-specific configuration needed for the selected class, including its original processor name.

Extend scope during Research when these files refer to further required types. Shared configuration changes must preserve other processors and sagas.

## Blocker

Check before Apply:

- **Unsupported target:** the selected release does not contain the required legacy APIs, or `framework=axon` excludes the Axoniq dependency. Keep this item blocked; do not silently change the selected framework or version. This recipe targets legacy APIs in **5.4.0**. Do not assume the same APIs exist in an older stable release.
- **Unsupported deadlines:** the saga uses `DeadlineManager`, `@DeadlineHandler`, or scheduler state without a verified equivalent in the selected release. Verify legacy deadline support in the selected release. Preserve deadline code, cancellation, persisted schedules, and tests. Require a separately verified replacement or continued AF4 execution until those instances drain; neither commenting out deadlines nor deleting assertions resolves this blocker.
- **Unknown persistence compatibility:** saga payload type/format, association mapping, store, or original processor name cannot be established. Do not infer these from a new empty database.
- **Unresolved prerequisite:** unrelated compilation failures or missing dependencies prevent verification of the scoped slice. Normal AF4 API errors in the selected saga after OpenRewrite are work for this recipe, not grounds for skipping its tests.

Use the baseline `skip`, `revert`, and `solve-manually` Options. Recommend `skip` for an unsupported release or deadline dependency; it defers the item and does not mean upgrade success. A request to redesign the process should hand off to `saga-to-workflow` after its prerequisites are satisfied.

## Out of Scope

- Workflow design, process cutover, removal of `@StartSaga`, drainage, and retirement.
- Saga payload conversion, schema upgrades, resetting tokens, context upgrade, and deployment.
- Rebuilding saga state as a new JPA entity or repository.
- Sibling processes and unrelated refactoring.

## Applicable

Evaluate the source surface, including resolved annotation imports:

1. A saga stereotype or saga handler/lifecycle annotation is present: continue. The legacy module deliberately preserves these names, so this includes already adapted sagas.
2. An aggregate with event-sourcing handlers: Rejected; route to `aggregate`.
3. An ordinary event handler/projector without saga annotations: Rejected; route to `event-processor`. A prior stateful rewrite is not evidence of successful legacy upgrade.
4. Otherwise: Rejected; report the observed source shape.

## Success Criteria

All DEFAULT.md baseline criteria and the following must pass:

1. The selected release resolves the correct legacy runtime and test artifacts. Scoped code and existing saga fixture tests compile and pass.
2. Saga class identity, serialized business fields, association keys, handler correlation, completion behavior, and existing start behavior are preserved. No new state store is introduced.
3. Static lifecycle calls and injected collaborator fields are adapted to handler parameters. Saga event handlers remain synchronous; fire-and-forget sends and calls that wait for command results preserve their original semantics and error handling.
4. The original processor name is preserved, including any `@ProcessingGroup` replacement with `@Namespace`. Configuration keeps the existing saga and token stores; no initial-token reset or table deletion is introduced.
5. No deadline behavior or test assertion was removed to obtain a green build. Missing runtime prerequisites remain explicit blockers.

### Verification

Include every existing test for this saga that uses `SagaTestFixture` in `axon4to5-isolatedtest` inputs. Keep its assertions for active saga counts, associations, dispatched commands, and completion. Use `io.axoniq.framework:axoniq-legacy-test` for the 5.4.0 target, and stop or close the fixture after each test. Verify any fixture API adaptation against the selected release.

Do not exclude failing saga fixture tests or replace them with compile-only validation. When none exist, report `no-test-coverage` under the baseline contract. Isolated verification proves the code slice only: report persisted-state restart/continuation and durable-token checks as deployment gates for the full upgrade guide, not as tests this recipe already ran.

## References

- [Saga upgrade](https://docs.axoniq.io/axon-framework-reference/development/migration/paths/sagas/) - always read for legacy source adaptation, configuration, and persistence constraints. This development page can be ahead of the selected release; resolve differences against that release's source or JARs. Its current Spring starter wording predates the move: 5.4.0 uses `io.axoniq.framework:axoniq-spring-boot-starter`.
- [OpenRewrite recipe source](https://github.com/AxonIQ/AxonFramework/tree/main/migration) - when checking automatic transformations. `org.axonframework.migration.Axon4ToAxon5Legacy` adapts lifecycle and dispatcher access; it does not convert saga instances into workflow instances.
- [Messages](../../docs/paths/messages.adoc) - when handler message APIs changed.
- [Token store upgrade](../../docs/paths/token-store.adoc) - when recording a schema prerequisite for the broader upgrade; do not apply schema changes here.

The generated `references/docs/paths/sagas.adoc` snapshot can predate legacy support. It is not the authority for this recipe; do not edit the generated snapshot or follow its removed-SPI guidance.

## Toolbox

1. Record the target dependency version, serialized saga identity and fields, all association keys, original processor name, store configuration, command dispatch behavior, and tests. Read the resolved classes before choosing signatures.
2. Align dependencies within scope. The 5.4.0 target uses `io.axoniq.framework:axoniq-legacy` and `io.axoniq.framework:axoniq-legacy-test` (test scope). For Spring Boot use `axoniq-spring-boot-starter`. If OpenRewrite output adds `org.axonframework:axon-legacy` or `axon-legacy-test`, correct those coordinates. Retain the `org.axonframework.*` Java packages of legacy saga types.
3. Keep `@Saga`, `@SagaEventHandler`, `@StartSaga`, and `@EndSaga` as appropriate to the existing behavior. Add a `SagaLifecycle` method parameter where static lifecycle calls were used. Call its instance methods without changing association keys or values.
4. Replace injected `CommandGateway` fields with a `CommandDispatcher` handler parameter. Move other injected resources to the handlers that use them. Keep business-state fields; moving collaborators must not change the serialized business state. Preserve `send` as fire-and-forget; for `sendAndWait`, await the selected release's command result before the handler returns and preserve exception semantics. Do not return incomplete asynchronous work from a legacy saga handler.
5. Replace `@ProcessingGroup("originalName")` with `@Namespace("originalName")`. Check explicitly configured names too. Keep the same durable stores and verify resolution of handler parameters; do not silently accept an in-memory fallback. For native configuration verify `SagaConfigurer` registration against the selected release.
6. Adapt fixture setup and teardown, retain behavioral assertions, then run isolated verification. Record the runtime checks still required before deployment.

## Use cases

- [01-legacy-saga-spring.md](use-cases/01-legacy-saga-spring.md) - Spring saga without unsupported deadline dependencies.
- [02-deadline-blocker.md](use-cases/02-deadline-blocker.md) - deadline behavior has no verified equivalent in the selected release.
- [03-rejected-not-a-saga.md](use-cases/03-rejected-not-a-saga.md) - source was routed to the wrong recipe.

## Gotchas

- Legacy class names and packages can look like AF4. Classpath provenance, source signatures, and passing tests determine completion; grepping for `org.axonframework.modelling.saga` is not a failure check.
- Removing `@StartSaga` belongs to coordinated cutover. Doing it during mechanical source adaptation can stop new business processes prematurely.
- A processor rename loses access to its existing token. A fresh processor starting at the head can miss events needed by running sagas.
- A green fixture using an in-memory store does not prove JPA transaction behavior or deserialization of persisted AF4 saga instances.

## Result

Emit exactly one FLOW.md Result block with `Recipe: axon4to5-saga`, Notes, and Learnings.

- **Success:** summarize source adaptation and fixture results, target release, and remaining deployment gates. Never claim instance upgrade or production cutover from isolated tests.
- **Blocker:** name the incompatible API, deadline, or prerequisite and its location; include baseline Options and a project-specific blocker Learning.
- **Rejected:** name the observed predicate and correct recipe; make no edits.
- **Failure:** list unmet criteria and the last compiler/test error verbatim. Keep failing tests visible.
