# Behavior inventory

Keep evidence tied to source paths and handler names. A saga's annotations alone do not describe its business process: follow private helpers, callbacks, reactive error branches, and the handlers of commands it sends. If a command is handled in another service, record the contract as unverified until source or an integration test establishes it.

For each process record:

| Subject | Evidence to preserve |
| --- | --- |
| Start and identity | Every start event; association property; `forceNew`; secondary associations; a key unique for each process run, not merely each customer or asset |
| Handler | Event, association, state read/written, guard, commands, publications, queries, timer changes, and whether it ends the saga |
| Command | Dispatch-only or result observed; synchronous or asynchronous handler; resulting events; external effects; failure behavior; idempotency and duplicate protection |
| Timer | Scheduling point, duration or absolute due time, cancellation paths, rescheduling, retry counter, and timeout effect |
| Compensation | Trigger, guard, ordering, dependent events, failure handling, and the point beyond which compensation no longer applies |
| Consumers | Every consumer of events emitted directly or indirectly by the saga; subscribing versus streaming processors; required metadata |
| Persistence | Existing saga type/name, serialized state, association rows, processor name/namespace, serializer, token store, scheduler state |

## Derive control flow from evidence

Construct the process graph from event/command causality and guards, not source-file order. A flag written by one handler and read by another suggests a dependency; it does not prove events arrive in that order. A saga can accept events in orders that a sequential workflow would miss.

Record representative input traces, with their expected commands, events, timer actions, and terminal outcome. Include success, rejection, technical failure, timeout, duplicate event, reordered event, compensation failure, and restart while waiting. Compare workflow traces against this baseline.

For each difference write the old behavior, proposed behavior, reason, and decision. Common differences:

- **Added timeout:** a saga waited indefinitely, but the selected workflow API needs a timeout. Decide its duration and what happens to late answers.
- **Command timeout:** a command may commit after the step times out. Decide idempotency, retry, and compensation for that late commit.
- **Retry bound:** preserve attempts and backoff. A saga that retried without limit needs an explicit decision if the workflow policy is bounded.
- **Late or out-of-order event:** a saga association accepted it before the workflow would register its wait, or after a workflow branch settles.
- **Changed failure visibility:** awaiting a previously dispatch-only command, ignoring an error, or compensating a new class of failure changes behavior.
- **Changed identity/event contract:** different process key, terminal event, payload, metadata, ordering, or consumer routing.

Multiple start events, dynamic rescheduling, reactive branching, and processes spanning several sagas need explicit design. Mark uncertain edges unresolved rather than inventing a mechanical conversion.

If analysis outputs from another tool are available, use them as evidence with their coverage limits. This skill does not bundle the original repository's OpenRewrite analyzer, equivalence checker, or agent hooks; do not claim those checks ran.
