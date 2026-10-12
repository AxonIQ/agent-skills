# Refine spec

The spec (journeys, components, messages, notes) lives on the AxonIQ Platform. Two channels for change exist:

| Kind of change | Where it happens                                                                                  |
|---|---------------------------------------------------------------------------------------------------|
| **Journey content** — primary/alternative flows, step text | **Here, via MCP** — `chat_with_platform`. (Also editable in the Platform UI.)                     |
| **Component handlers / scenarios / exceptions** | **Here, via MCP** — `chat_with_platform`. (Also editable in the Platform UI.)                     |
| **Message shapes** (commands, events, queries) | **Here, via MCP** — `chat_with_platform`. (Also editable in the Platform UI.)                     |
| **Notes** — rationale, NFRs, scope decisions, open questions | **Here, via MCP** — `chat_with_platform`. (Also editable in the Platform UI.)                     |
| **Confirm Design** (Journey NEEDS_APPROVAL → APPROVED) | Platform UI; or, only if the user explicitly confirms, `approve_journey` via MCP, one at a time |
| **Component implementation lifecycle** (APPROVED → IMPLEMENTING → IMPLEMENTED) | Here, via `mark_component_implementing` / `mark_component_implemented`                            |

When the user asks for a change you can't make directly with the lifecycle MCP tools, use `chat_with_platform` — that pipes the request to the Platform's project AI, which can rewrite journeys, component handlers, message shapes, and notes. The Platform's AI applies the changes server-side; re-fetch with `get_project` after the call returns.

## How to ask `chat_with_platform`

Be specific. The Platform AI sees the full project graph but doesn't see your conversation history — it needs the change spelled out:

- Good: *"Add a `customerId: String` property to the `PlaceOrder` command, and reference it from the existing handler in `place-order`."*
- Bad: *"add what we just talked about"*

Pick `chat_with_platform` when the user has clearly asked for the change. Pick "just capture intent" (via the same tool, phrased as a note request) when the user is exploring rather than committing:

Example — committed change:

> *"Got it — asking the Platform AI to add a `customerId` property to `PlaceOrder`."*
> *(then `chat_with_platform(projectId, "Add customerId: String to PlaceOrder ...")`, then `get_project` to confirm)*

Example — exploratory thought:

> *"I've asked the Platform AI to capture 'should we charge on cancel?' as a question on the `cancel-order` journey. The Platform UI will surface it next time you open the project."*
> *(then `chat_with_platform(projectId, "Capture a question note on the cancel-order journey: ...")`)*

## Re-reading state

The Platform is the source of truth — never assume your in-context view of `get_project` is still valid across long-running tasks. Before:

- Marking a component implementing or implemented.
- Reporting status to the user.
- Starting a new implementation.

…re-call `get_project(projectId)` (or the focused `get_*_details` call) to refresh.
