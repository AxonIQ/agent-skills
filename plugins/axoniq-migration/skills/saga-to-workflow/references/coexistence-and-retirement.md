# Coexistence and retirement

## Preconditions

The legacy saga already runs on AF5 and can resume existing serialized state. Resolve framework-upgrade, serializer, token, and legacy deadline compatibility before this cutover. Do not change the draining saga's type, state shape, association keys, processor identity/namespace, or scheduler semantics as part of workflow conversion.

Prove the workflow behavior before activating it for new requests. Keep the legacy command handlers needed by draining instances, even when the workflow uses a different path.

## Establish a cutover boundary

Prepare one coordinated transition:

1. Record the producer pause or another explicit event boundary and the workflow processor's durable starting position.
2. Prevent every old deployment from starting the upgraded saga type, typically by removing its `@StartSaga` annotations while retaining the associated event handlers for existing instances.
3. Enable the workflow definition on the same business start event. Ensure its initial position excludes historical starts already owned by sagas and includes every start after the boundary.
4. Verify that the relevant processors are ready and their positions are durable before allowing new starts.

A rolling deployment can briefly run a saga starter and a workflow starter together. A workflow processor first initialized at the head can also skip events published before it becomes ready. Do not substitute a fixed sleep or an assumed deployment timestamp for a tested boundary. Coordinate producer quiescence or an explicit routing/token strategy appropriate to the deployment.

The 5.4.0 workflow engine initializes a new processor at the head by default. Check the resolved version and actual processor name; a blanket override for a processor called `Workflow` may not target the application's module. Existing tokens determine resume position. Losing them and restarting at the current head can skip active work; resetting to the tail can start workflows for historical saga starts. Neither is a recovery strategy.

## Prove coexistence

Use an isolated deployment with representative persistent event, token, saga, and scheduler stores:

- Seed an unfinished legacy saga and historical start events before cutover.
- Deploy the coexistence version at the chosen boundary.
- Confirm no new workflow is caused by a historical start.
- Publish a new start and confirm exactly one workflow, with no new saga instance.
- Complete the old saga and the new workflow independently.
- Restart while a workflow waits; verify progress resumes without duplicate business effects or lost events.
- Exercise the draining saga's timeout/retry path if it has scheduled work.

Keep saga test evidence. Tests that relied on `@StartSaga` may need a legacy baseline harness or seeded persisted state after start capability is removed; do not delete those assertions merely because the fixture can no longer create a fresh instance.

## Drain and rollback

Observe remaining saga instances per upgraded type and tenant, pending scheduled work, dead-lettered/failed processing, and oldest instance age. Zero rows alone is not proof that every in-flight command or scheduled job is settled. Define the observation interval from the actual process lifetime and operational evidence; an unbounded process may need explicit intervention.

Rollback after workflows have started must retain a runtime capable of completing those workflows. Re-enabling saga starts while workflow starts remain enabled duplicates new processes; removing the workflow definition can strand its existing histories. Prepare a boundary-aware rollback or forward fix and test it in the same sandbox.

## Retire

Once drain is verified:

1. Remove only the drained saga type and its registration, deadline bridge, and obsolete tests. Preserve useful behavior assertions in workflow tests or a upgrade regression suite.
2. Remove `axoniq-legacy` / `axoniq-legacy-test` only when no other saga or legacy feature requires them.
3. Keep JPA and its transaction configuration if tokens, projections, or other application data use it.
4. Prepare storage cleanup scoped to the retired type/tenant/processor and to scheduler jobs it owned. Shared saga, association, scheduler, and token tables may serve other components.
5. Never drop the shared token table. Never remove workflow or projection tokens. Removing a retired saga processor's rows is a separate, specifically scoped cleanup after every deployment that uses that processor is gone.

Run an end-to-end workflow and a restart test after retirement. Record the drain evidence and exactly which runtime components and storage objects were removed.
