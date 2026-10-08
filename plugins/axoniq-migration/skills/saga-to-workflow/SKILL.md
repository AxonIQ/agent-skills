---
name: saga-to-workflow
description: Upgrade existing Axon sagas to Axoniq workflows while preserving behavior, draining legacy instances, and verifying cutover. Use after the AF5 and DCB prerequisites are ready.
---

# Saga to workflow

Replace a saga process with an Axoniq workflow. New requests start workflows; existing saga instances finish in the legacy runtime. Do not translate stored saga rows into workflow history.

## Scope and entry check

Use `rg` (or the runtime's search tool) to locate `@StartSaga`, `@SagaEventHandler`, `@DeadlineHandler`, command handlers, processor configuration, and the resolved framework dependencies. Read the actual handlers and tests before asserting how the process behaves.

The application must already run its legacy sagas on a compatible Axoniq Framework 5 release, and its workflow event store must support DCB. This skill MUST NOT perform the AF4 to AF5 upgrade, regular-context to DCB conversion, or AF4 saga to AF5 legacy compatibility upgrade. When one is missing, report the prerequisite and continue only independent behavior analysis. Use the [staged upgrade guide](https://docs.axoniq.io/axon-framework-reference/development/migration/) and, when installed, `axon4to5-openrewrite` / `axon4to5-migrate-code` for those earlier stages.

Read [version and API checks](references/api-and-assets.md) before changing dependencies or copying an asset. Check the project's selected release instead of assuming the newest release is compatible.

## Workflow

1. **Inventory behavior.** Read [behavior inventory](references/behavior-inventory.md). Retain a read-only copy or existing revision of the saga source and tests. Record handler effects, command outcomes, associations, timers, event consumers, and unresolved decisions in the project's upgrade notes. Do not require a commit to preserve this evidence.
2. **Derive the workflow.** Read [derivation and patterns](references/derive-workflow.md). Cover every handler, including private helpers and failure branches. Preserve external contracts; record any intentional change in timeout, retry count, ordering, correlation, or late-event handling before implementing it. Resolve ambiguous business behavior with the user.
3. **Implement and test one process.** Keep the process readable in its workflow method and put side effects inside durable steps. Use the [assets](references/api-and-assets.md#assets) as adaptable examples, not a generated specification of the user's saga. Read [verification](references/verification.md) and port the existing behavioral tests.
4. **Prepare coexistence.** Read [coexistence and retirement](references/coexistence-and-retirement.md). Prepare the workflow activation and removal of saga start capability as one coordinated cutover. Retain the old saga handlers, state mapping, and processor position until its instances drain. Validate the cutover in an isolated deployment with persistent state.
5. **Retire only after drain.** Remove the upgraded saga's runtime when evidence proves it has no remaining work. Prepare narrowly scoped storage cleanup separately. Never delete a shared token table or reset unrelated processors.
6. **Report evidence.** Re-read the changed files and report behavior coverage, tests actually run, remaining decisions, runtime verification limitations, and the cutover/drain checklist. Do not describe fixture tests as proof of production durability.

## Non-negotiable behavior constraints

- Register an event wait before the command that can produce its event; also preserve events that may arrive earlier through another path.
- Keep commands and queries inside workflow steps. Code between steps must be deterministic when the workflow replays.
- Distinguish dispatch-only commands from commands whose results the saga handled. Do not introduce compensation for a failure the saga previously ignored without a decision.
- Preserve compensation guards and terminal domain events. A successful business rejection can finish normally; an unrecovered technical failure must use the workflow's failure mechanism.
- Preserve durable workflow and projection tokens during coexistence and retirement. Starting at the head applies to first initialization; it is not a recovery policy for lost tokens.

For processes spanning services or contexts, also read [cross-context processes](references/cross-context.md).
