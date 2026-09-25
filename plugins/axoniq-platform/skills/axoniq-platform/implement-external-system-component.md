
# Implementing an EXTERNAL_SYSTEM component

An EXTERNAL_SYSTEM component is a stub for an integration with a third-party system. The implementation direction is **command-in / event-out**: our system dispatches a command to the external system, the external system handles it (the real integration: HTTP call, message queue, etc.), and publishes an outcome event back into our system. We can't know the system's internals, so locally we generate a placeholder that:
1. Handles a command via `@CommandHandler` (the action's `message`).
2. Logs that the integration would be performed.
3. Publishes an outcome event (drawn from the component's `publishedEvents`) to represent the response.

The user fills in the actual integration (HTTP call, message queue, etc.) later. A WORKFLOW can `wait` on the published outcome event.

**Always load [implementation-base.md](implementation-base.md) first** — same package layout, same marker rules, same "no Axon 4" rule. For framework-level API details consult the **`axoniq-app-development`** plugin (install it alongside this one from the `axoniq` marketplace):

- `commands/stateless.md` — `@CommandHandler` parameter resolution (including `ProcessingContext`)
- `events/publishing.md` — `EventGateway.publish(...)` semantics (event handling/projections: `events/handling-projections.md`)
- `foundations/annotations.md` — `@CommandHandler` attribute reference

## Inputs

- `projectId` and `workspaceId` from `./.axoniq` at the repo root.
- `componentId` provided by [SKILL.md](SKILL.md).
- Component spec fetched via MCP: `get_component_details(projectId, componentId)`. Returns `actions` with `message` (= the COMMAND this external system handles) inline, plus `publishedEvents` (= the events the external system publishes back into our system).
- Referenced message schemas: resolved from the same `get_component_details` response, or from `get_project(projectId).messages` when you need a cross-component lookup. Don't read or write spec files on disk.

[SKILL.md](SKILL.md) picks the component as eligible in one of two modes:

- **Fresh implementation**: MCP component status is `APPROVED` and no `<component_pkg>/.axoniq` marker exists. Write the stub service + messages + marker.
- **Extend mode**: marker exists, but the spec's `actions` list (re-fetched via MCP) has new entries. Read the existing service class. **Add** new `@CommandHandler` methods for the new actions; create any new outcome events. Leave existing methods alone unless their spec changed.

## Files to write

`<component_pkg>` = `{{source_directory}}/{{source_path}}/<componentId-as-snake>/`.

1. **Marker — write this FIRST** → `<component_pkg>/.axoniq` containing `{ "componentId": "<componentId>" }`. See [implementation-base.md](implementation-base.md) for the rationale. In extend mode the marker already exists — leave it alone.

2. **Handled commands** → `{{source_directory}}/{{source_path}}/api/commands/<CommandName>.kt`
   - One per action's `message` (the command the external system handles).
   - Reference, don't redefine, if it already exists (was written by another component). Otherwise create it from the spec (with `@Command(namespace = "<project-namespace>", name = "<CommandName>")`).

3. **Outcome events** → `{{source_directory}}/{{source_path}}/api/events/<EventName>.kt`
   - One per `publishedEvents` entry on the component.
   - Reference, don't redefine, if it already exists. Otherwise create it from the spec (with `@Event(namespace = "<project-namespace>", name = "<EventName>")`).

4. **Service class** → `<component_pkg>/<ComponentName>Service.kt`

   ```kotlin
   import org.axonframework.messaging.commandhandling.annotation.CommandHandler
   import org.axonframework.messaging.eventhandling.gateway.EventGateway
   import org.axonframework.messaging.core.unitofwork.ProcessingContext
   import org.slf4j.LoggerFactory
   import org.springframework.stereotype.Service

   @Service
   class <ComponentName>Service(
       private val eventGateway: EventGateway,
   ) {
       private val logger = LoggerFactory.getLogger(javaClass)

       @CommandHandler
       fun handle(command: <HandledCommand>, processingContext: ProcessingContext) {
           logger.info("External system: would perform <action description> for {}", command)
           // TODO: replace with the real integration (HTTP, queue, etc.)
           eventGateway.publish(processingContext, <OutcomeEvent>(/* fields from command */))
       }
   }
   ```

   - One `@CommandHandler` method per action in the spec.
   - Pass `processingContext` to `eventGateway.publish(...)` so the publication joins the active unit of work.
   - The body is a stub — log + publish the outcome event. Leave a `TODO:` comment so the user knows to replace it.

## After scaffolding — surface the obvious next step

The stub always logs and publishes a synthetic outcome event. That's intentional — generating real provider integrations is the user's call (different vendor, different SDK version, different auth approach). After writing the files, **explicitly tell the user** that this is a stub and what the natural next step is. Example wording:

> Scaffolded `<ComponentName>Service` as a **stub** — it handles `<HandledCommand>`, logs it, and publishes `<OutcomeEvent>` synthetically. The natural next step is replacing the stub with a real integration.
>
> When you're ready, just say "implement the real <action description> integration" and I can:
> - ask which provider/SDK you want (e.g. for payments: Stripe, Adyen, Mollie)
> - read the latest provider docs and wire up the actual call
> - add error handling, retry policy, and tests against the provider's sandbox or a WireMock fixture
> - replace the synthetic event publication with one driven by the real API response
>
> Until then, the stub will compile and let the rest of the system flow correctly with synthetic data.

This is more than a `TODO:` comment — it's a direct hand-off, so the user knows exactly what to ask for next without having to figure out the right phrasing themselves.

## What EXTERNAL_SYSTEM components do NOT get

- No state model.
- No JPA entity / repository.
- No REST controller (the spec doesn't describe an inbound API; if an HTTP endpoint is needed, that's a follow-up the user adds manually).
- No tests by default — the stub has no business logic to verify. Skip them unless the user explicitly asks.

## When to stop and ask

- The component lists multiple `publishedEvents` and the choice between them depends on command content / integration outcome — generate the multi-event publication with a TODO comment, and tell the user to fill in the branching logic.
- The handled command isn't defined anywhere in the project's message table — flag it; that's a Platform-side spec issue.
- The component package already exists with a different `componentId` in `.axoniq`.
- Compile fails after writing files.

## Boundaries

- Don't touch other components' packages.
- Don't redefine events/commands in `api/`; reference existing ones.
- Don't modify the per-package `.axoniq` of any component other than this one.
- Don't import from Axon Framework 4.
- Don't try to "implement" the external system call — it's a stub. The user owns the integration code.
