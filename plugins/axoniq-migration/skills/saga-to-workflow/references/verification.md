# Verify behavior and durability

Port each existing saga test by its business assertion, not by a one-to-one annotation rewrite. Keep a coverage matrix from original handler/branch to workflow step and test. Add tests for previously uncovered behavior discovered during the inventory.

## Fixture tests

Use the `WorkflowTestFixture` for the selected release. The bundled Java example targets 5.4.0 APIs. It releases execute steps explicitly; the fixture does not automatically run every command step.

| Saga assertion | Workflow assertion |
| --- | --- |
| A command was dispatched | Recorded command type, payload, order, and count, not just the existence of a step |
| An event advances the saga | Publish it, release any resulting execute steps, and assert the expected waits/outcome |
| Time elapsed | First assert the expected wait exists, then advance the fixture clock |
| No active saga after rejection | Expected terminal domain event and the chosen workflow terminal status |
| Failure callback compensates | Inject command failure on a result-aware step and assert its compensation guards |

Cover happy path, each failure event, timeout-only versus general failure, duplicate and reordered events, late success after timeout, retry attempts/backoff, compensation failure, and failure after the point of no return. Include null start fields and representative serialized numeric values.

Use barriers before advancing time: a published event is processed asynchronously, and a wait must be registered before its timeout can be exercised. Keep test deadlines distinct so advancing one does not inadvertently expire an unrelated step. If a fixture cannot exercise retry exhaustion or restart faithfully, cover those with an integration test and report the limitation; do not silently skip that branch.

## Runtime verification

Fixture success does not validate Spring wiring, serialization, token transactions, scheduler recovery, or the production event store. Run the coexistence scenarios in [coexistence and retirement](coexistence-and-retirement.md) against an isolated persistent deployment.

Check the workflow's terminal event and downstream effects, not only HTTP success or an application startup log. A command accepted by a controller may still lead to a failed or stalled workflow. Inspect processor errors, failed token updates, duplicate effects, and pending executions.

Preserve the intended storage and transaction model while investigating a failure. Do not replace persistent tokens with in-memory tokens, suppress an exception, or discard a handler to make a upgrade smoke test pass.

## Report

List tests and runtime checks actually executed, their results, unresolved semantic differences, and evidence of old-saga drain. Static review and sample-template tests are useful but do not establish behavioral equivalence for an arbitrary application. Do not claim an automated analyzer, lint gate, or model checker exists unless it is installed and actually ran.
