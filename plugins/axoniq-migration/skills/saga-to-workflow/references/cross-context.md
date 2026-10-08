# Cross-context processes

Inventory the remote command contract and the events it can produce, including correlation keys, duplicates, ordering, and failure responses. Unknown remote behavior stays an open upgrade decision; a local command stub cannot prove it.

A workflow that waits for a different context's events needs an event source that actually includes that context, plus a gateway that routes commands there. A local workflow event store alone does not provide those connections.

For the selected framework release, verify the supported multi-source event-streaming and distributed-command components in their documentation and source. Check connection lifecycle, context permissions, required licenses, serialization, event ordering, and the composite source's durable tokens. Avoid registering a remote store or bus in a way that replaces the application's own default component.

Keep the workflow's own durable history in its intended DCB store. Preparing another context or converting a regular context is outside this skill; use the upgrade guide for that infrastructure prerequisite.

Register remote answer waits before dispatch. Make correlation unique to the process run, and define late or duplicated remote answers. Test remote failure and timeout as well as successful replies. Preserve the prior contracts when wrapping remote calls in a domain port; moving a command handler's implementation into a workflow step is a redesign, not a mandatory upgrade technique.
