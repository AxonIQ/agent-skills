# Version and API checks

The Java assets target Axon/Axoniq Framework **5.4.0** APIs. Resolve the application's chosen versions and inspect their APIs before adapting an asset.

For this baseline:

- Legacy saga modules are `io.axoniq.framework:axoniq-legacy` and `io.axoniq.framework:axoniq-legacy-test`. Their prerequisite upgrade belongs to the main upgrade guide.
- Workflow DSL and tests use `io.axoniq.framework:axoniq-workflow-dsl` and `io.axoniq.framework:axoniq-workflow-test`. Check dependency management: explicitly version modules not managed by the project's BOM.
- `@Workflow` is in `io.axoniq.framework.workflow.annotation`; step definitions, results, exceptions, and status are in `io.axoniq.framework.workflow.dsl.api`.
- The simple context is `io.axoniq.framework.workflow.dsl.simple.SimpleWorkflowContext`.
- `WorkflowModule.defaults(name, SimpleWorkflowContext.class)` discovers its standard context factory; do not copy an obsolete `.workflowContextFactory(...)` call from an older example.
- Spring applications should verify workflow auto-configuration from the selected Axoniq starter. Do not add a removed standalone workflow Spring Boot artifact.

Use [workflow documentation](https://docs.axoniq.io/axon-framework-reference/development/workflows/) for configuration, testing, durable steps, and workflow versioning. When a page or copied sample disagrees with the selected artifact, inspect that release's source/API and compile a focused example. Report a framework failure with its version and reproduction instead of weakening the application's behavior or persistence to hide it.

## Assets

The portable assets are small examples, not an automated converter:

| Asset | Use |
| --- | --- |
| [Steps.java](../assets/java/Steps.java) | Command dispatch/result semantics, early event waits, and payload association helpers; retain only used methods |
| [OrderWorkflow.java](../assets/java/OrderWorkflow.java) | A payment process with early wait registration, timeout compensation, and a terminal event after the point of no return |
| [RecordingCommandGateway.java](../assets/java/RecordingCommandGateway.java) | Thread-safe recording gateway and configurable command failures for tests |
| [OrderWorkflowTest.java](../assets/java/OrderWorkflowTest.java) | Fixture tests for success, dispatch-only failure, timeout, and failed compensation |

Copy main/test assets into the corresponding source sets and adapt package, domain contracts, and namespace. The example assumes public domain records with these components (each in its own Java file):

```java
OrderPlaced(String orderId, long amountCents)
RequestPayment(String orderId, long amountCents)
PaymentConfirmed(String orderId)
CancelPayment(String orderId)
OrderCompleted(String orderId)
OrderCancelled(String orderId, String reason)
```

The example's timeout values and cancellation policy are deliberately constructor inputs: take them from the saga inventory and explicit behavior decisions. It is not a complete order-fulfillment specification and does not model partial payment, stock, or remote-service outcomes.

Tests need JUnit Jupiter and AssertJ plus `axoniq-workflow-test`; the connector-disable example imports `io.axoniq.framework:axon-server-connector`. If no connector is on the classpath, use the fixture setup appropriate for that application rather than adding a production connector solely for the test.

The original repository's Maven analyzer, lint recipes, model checker, sandbox runners, and hooks are not included. No installed-skill command depends on a checkout of that repository.
